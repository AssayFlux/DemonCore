"""Self-contained tests runnable with CPython or the MicroPython unix port."""
import os
import json
import gc

from core.config import load_config
from core.log import LogRing
from core.scheduler import Scheduler, asyncio
from core.state import load_state, mark_stable, prepare_boot

class FakeWatchdog:
    def __init__(self):
        self.feeds = 0
    def feed(self):
        self.feeds += 1

def remove_if_present(path):
    try:
        os.remove(path)
    except OSError:
        pass

def test_config_defaults():
    path = "/tmp/demoncore-config-test.json"
    remove_if_present(path)
    config = load_config(path)
    assert config["schema_version"] == 1
    assert config["transports"]["wifi"] is False
    assert config["log_capacity"] > 0

def test_config_overrides():
    path = "/tmp/demoncore-config-test.json"
    with open(path, "w") as stream:
        json.dump({"schema_version": 1, "transports": {"wifi": True}}, stream)
    config = load_config(path)
    assert config["transports"]["wifi"] is True
    assert config["transports"]["ble"] is False
    remove_if_present(path)

def test_log_ring():
    ring = LogRing(2)
    ring.add("INFO", "one")
    ring.add("WARN", "two")
    ring.add("ERROR", "three")
    assert ring.snapshot() == [("WARN", "two"), ("ERROR", "three")]
    bounded = LogRing(1, 4)
    bounded.add("INFO", "123456")
    assert bounded.snapshot()[0][1] == "1234"

def test_crash_counter_and_safe_mode():
    path = "/tmp/demoncore-state-test.json"
    remove_if_present(path)
    assert prepare_boot(path)["consecutive_crashes"] == 1
    assert prepare_boot(path)["safe_mode"] is False
    third = prepare_boot(path)
    assert third["consecutive_crashes"] == 3
    assert third["safe_mode"] is True
    stable = mark_stable(path)
    assert stable["consecutive_crashes"] == 0
    assert load_state(path)["safe_mode"] is False
    remove_if_present(path)

def test_corrupt_state_fails_safe():
    path = "/tmp/demoncore-state-test.json"
    with open(path, "w") as stream:
        stream.write("{broken")
    assert load_state(path)["safe_mode"] is True
    remove_if_present(path)

def test_watchdog_feed_is_in_scheduler_loop():
    watchdog = FakeWatchdog()
    scheduler = Scheduler(interval_ms=1, stable_ticks=2)
    stable = []
    async def run_test():
        await scheduler.run(watchdog, lambda: stable.append(True), max_ticks=3)
    asyncio.run(run_test())
    assert watchdog.feeds == 3
    assert stable == [True]

def test_dcp_shared_vectors():
    global dcp
    gc.collect()
    heap_before = gc.mem_free() if hasattr(gc, "mem_free") else None
    from core import dcp
    gc.collect()
    heap_after = gc.mem_free() if hasattr(gc, "mem_free") else None
    if heap_before is not None and heap_after is not None:
        print("DCP_MODULE_HEAP_BYTES", heap_before - heap_after)
    with open("protocol/vectors/valid.json", "r") as stream:
        valid = json.load(stream)
    with open("protocol/vectors/invalid.json", "r") as stream:
        invalid = json.load(stream)
    for vector in valid:
        message = dcp.decode(json.dumps(vector["message"]).encode("utf-8"))
        assert message == vector["message"]
        assert dcp.decode(dcp.encode(message)) == message
    gc.collect()
    heap_before_roundtrip = gc.mem_free() if hasattr(gc, "mem_free") else None
    probe = {"v": "1.0", "id": "0000000000000001", "src": "node:1",
             "dst": "node:2", "t": "req", "op": "sys.ping", "args": {}}
    dcp.decode(dcp.encode(probe))
    gc.collect()
    heap_after_roundtrip = gc.mem_free() if hasattr(gc, "mem_free") else None
    if heap_before_roundtrip is not None and heap_after_roundtrip is not None:
        print("DCP_ROUNDTRIP_RETAINED_BYTES", heap_before_roundtrip - heap_after_roundtrip)
    for vector in invalid:
        rejected = False
        try:
            dcp.decode(json.dumps(vector["message"]).encode("utf-8"))
        except dcp.DCPError:
            rejected = True
        assert rejected, vector["name"]
    assert len(valid) >= 20 and len(invalid) >= 10

def test_dcp_strict_json_and_limits():
    base = '{"v":"1.0","id":"0000000000000001","src":"node:1","dst":"*","t":"req","op":"sys.ping","args":{}}'
    try:
        dcp.decode(b'{"v":"1.0","v":"1.0","id":"0000000000000001","src":"node:1","dst":"*","t":"req","op":"sys.ping","args":{}}')
        assert False
    except dcp.DCPError:
        pass
    try:
        dcp.decode(b'{"v":"1.0","id":"0000000000000001","src":"node:1","dst":"*","t":"req","op":"sys.ping","args":{},"x":NaN}')
        assert False
    except dcp.DCPError:
        pass
    try:
        dcp.decode(b'\xff')
        assert False
    except dcp.DCPError:
        pass
    try:
        dcp.decode(b' ' * (dcp.MAX_MESSAGE_BYTES + 1))
        assert False
    except dcp.DCPError as error:
        assert error.code == "E_TOO_LARGE"

def test_dcp_routing_and_error_reply():
    request = {"v": "1.0", "id": "0000000000000001", "src": "node:7",
               "dst": "group:lab", "t": "req", "op": "sys.ping", "args": {}}
    assert dcp.route(request, 8, groups=("lab",))
    assert not dcp.route(request, 8, groups=("other",))
    assert dcp.matches_destination("*", 99)
    reply = dcp.make_error_reply(request, "E_NOT_FOUND", "missing", responder="node:8")
    assert reply["src"] == "node:8" and reply["dst"] == "node:7"
    assert reply["id"] == request["id"] and reply["op"] == request["op"]
    assert dcp.decode(dcp.encode(reply)) == reply

def run():
    tests = [test_config_defaults, test_config_overrides, test_log_ring,
             test_crash_counter_and_safe_mode, test_corrupt_state_fails_safe,
             test_watchdog_feed_is_in_scheduler_loop, test_dcp_shared_vectors,
             test_dcp_strict_json_and_limits, test_dcp_routing_and_error_reply]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print("PASS: %d firmware core tests" % len(tests))

if __name__ == "__main__":
    run()
