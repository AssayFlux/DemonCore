import json
import os
import tempfile
import unittest

from core.config import load_config
from core.log import LogRing
from core.scheduler import Scheduler, asyncio
from core.state import load_state, mark_stable, prepare_boot

class FakeWatchdog:
    def __init__(self):
        self.feeds = 0
    def feed(self):
        self.feeds += 1

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temp.name, "state.json")
    def tearDown(self):
        self.temp.cleanup()

    def test_config_defaults_without_file(self):
        config = load_config(os.path.join(self.temp.name, "missing.json"))
        self.assertEqual(config["schema_version"], 1)
        self.assertFalse(config["transports"]["wifi"])
        self.assertGreater(config["log_capacity"], 0)

    def test_config_loads_valid_transport_overrides(self):
        path = os.path.join(self.temp.name, "config.json")
        with open(path, "w") as stream:
            json.dump({"schema_version": 1, "transports": {"wifi": True}}, stream)
        config = load_config(path)
        self.assertTrue(config["transports"]["wifi"])
        self.assertFalse(config["transports"]["ble"])

    def test_log_ring_wraps_at_capacity(self):
        ring = LogRing(2)
        ring.add("INFO", "one")
        ring.add("WARN", "two")
        ring.add("ERROR", "three")
        self.assertEqual(ring.snapshot(), [("WARN", "two"), ("ERROR", "three")])

    def test_log_message_is_bounded(self):
        ring = LogRing(1, 4)
        ring.add("INFO", "123456")
        self.assertEqual(ring.snapshot()[0][1], "1234")

    def test_safe_mode_after_three_consecutive_boots(self):
        self.assertEqual(prepare_boot(self.path)["consecutive_crashes"], 1)
        self.assertFalse(prepare_boot(self.path)["safe_mode"])
        third = prepare_boot(self.path)
        self.assertTrue(third["safe_mode"])
        self.assertEqual(third["consecutive_crashes"], 3)

    def test_stable_boot_clears_crash_counter(self):
        prepare_boot(self.path)
        self.assertEqual(mark_stable(self.path)["consecutive_crashes"], 0)
        self.assertFalse(load_state(self.path)["safe_mode"])

    def test_corrupt_state_fails_safe(self):
        with open(self.path, "w") as stream:
            stream.write("{broken")
        self.assertTrue(load_state(self.path)["safe_mode"])

    def test_watchdog_is_fed_by_scheduler_main_loop(self):
        watchdog = FakeWatchdog()
        scheduler = Scheduler(interval_ms=1, stable_ticks=2)
        stable = []
        async def run_test():
            await scheduler.run(watchdog, lambda: stable.append(True), max_ticks=3)
        asyncio.run(run_test())
        self.assertEqual(watchdog.feeds, 3)
        self.assertEqual(stable, [True])

if __name__ == "__main__":
    unittest.main()
