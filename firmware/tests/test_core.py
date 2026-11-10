"""Self-contained tests runnable with CPython or the MicroPython unix port."""
import os
import json
import gc

from core.config import load_config
from core.log import LogRing
from core.identity import IdentityStore
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


class FakeNVS:
    def __init__(self):
        self.values = {}
        self.commits = 0
    def set_blob(self, key, value):
        self.values[key] = bytes(value)
    def get_blob(self, key, buffer):
        if key not in self.values or not isinstance(self.values[key], bytes):
            raise OSError("not found")
        value = self.values[key]
        if len(value) > len(buffer):
            raise OSError("buffer too small")
        buffer[:len(value)] = value
        return len(value)
    def set_i32(self, key, value):
        self.values[key] = int(value)
    def get_i32(self, key):
        if key not in self.values or not isinstance(self.values[key], int):
            raise OSError("not found")
        return self.values[key]
    def erase_key(self, key):
        if key not in self.values:
            raise OSError("not found")
        del self.values[key]
    def commit(self):
        self.commits += 1


def test_identity_store_roundtrip_and_claim_state():
    nvs = FakeNVS()
    store = IdentityStore(nvs)
    secret = bytes(range(32))
    cell_key = bytes(range(32, 64))
    assert store.load() is None
    store.store(123456789, secret, cell_key, 17, 23, True)
    loaded = store.load()
    assert loaded["node_id"] == 123456789
    assert loaded["device_secret"] == secret
    assert loaded["cell_key"] == cell_key
    assert loaded["tx_counter"] == 17 and loaded["rx_counter"] == 23
    assert loaded["claimed"] is True
    assert nvs.commits == 1
    store.store(123456789, secret, cell_key, 18, 24, False)
    assert store.load()["claimed"] is False
    assert store.load()["tx_counter"] == 18


def test_identity_store_tamper_and_validation():
    nvs = FakeNVS()
    store = IdentityStore(nvs)
    secret = b"s" * 32
    store.store(7, secret, b"k" * 32)
    nvs.values["dev_secret"] = b"tampered"
    rejected = False
    try:
        store.load()
    except ValueError:
        rejected = True
    assert rejected
    for bad_id in (0, -1, True, 1 << 64):
        rejected = False
        try:
            store.store(bad_id, secret, b"k" * 32)
        except ValueError:
            rejected = True
        assert rejected
    for bad_secret in (b"", b"x" * 31, "not-bytes"):
        rejected = False
        try:
            store.store(8, bad_secret, b"k" * 32)
        except ValueError:
            rejected = True
        assert rejected


def test_identity_store_wipe_and_no_secret_logging():
    nvs = FakeNVS()
    store = IdentityStore(nvs)
    secret = b"secret-value-not-for-logs-000000"
    assert len(secret) == 32
    store.store(9, secret, b"c" * 32, claimed=True)
    ring = LogRing(8)
    ring.add("INFO", "identity persisted")
    log_text = repr(ring.snapshot())
    assert secret.hex() not in log_text
    assert str(secret) not in log_text
    store.wipe()
    assert store.load() is None
    assert nvs.commits == 2


def run():
    tests = [test_config_defaults, test_config_overrides, test_log_ring,
             test_identity_store_roundtrip_and_claim_state,
             test_identity_store_tamper_and_validation,
             test_identity_store_wipe_and_no_secret_logging,
             test_crash_counter_and_safe_mode, test_corrupt_state_fails_safe,
             test_watchdog_feed_is_in_scheduler_loop, test_dcp_shared_vectors,
             test_dcp_strict_json_and_limits, test_dcp_routing_and_error_reply]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print("PASS: %d firmware core tests" % len(tests))

if __name__ == "__main__":
    run()
