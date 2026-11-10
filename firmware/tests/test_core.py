"""Self-contained tests runnable with CPython or the MicroPython unix port."""
import os
import json

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

def run():
    tests = [test_config_defaults, test_config_overrides, test_log_ring,
             test_crash_counter_and_safe_mode, test_corrupt_state_fails_safe,
             test_watchdog_feed_is_in_scheduler_loop]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print("PASS: %d firmware core tests" % len(tests))

if __name__ == "__main__":
    run()
