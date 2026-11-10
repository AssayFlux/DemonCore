import unittest
from tools.validate_pins import evaluate, load_profile

class PinPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile()

    def check(self, pin, action, **kwargs):
        return evaluate(self.profile, pin, action, **kwargs)["status"]

    def test_blocked_flash_pin(self):
        self.assertEqual(self.check(6, "write"), "block")

    def test_unavailable_gpio(self):
        self.assertEqual(self.check(20, "mode", mode="input"), "block")

    def test_console_reserved(self):
        self.assertEqual(self.check(1, "mode", mode="input"), "block")

    def test_strapping_warns_without_confirmation(self):
        self.assertEqual(self.check(5, "write"), "warn")

    def test_strapping_allows_with_confirmation(self):
        self.assertEqual(self.check(5, "write", confirm=True), "allow")

    def test_input_only_accepts_plain_input(self):
        self.assertEqual(self.check(34, "mode", mode="input"), "allow")
        self.assertEqual(self.check(34, "mode", mode="input_pullup"), "block")
        self.assertEqual(self.check(34, "pwm"), "block")

    def test_adc1_works_with_wifi(self):
        self.assertEqual(self.check(32, "adc", wifi_active=True), "allow")

    def test_adc2_blocked_with_wifi(self):
        self.assertEqual(self.check(4, "adc", wifi_active=True), "block")

    def test_adc2_allowed_without_wifi(self):
        self.assertEqual(self.check(4, "adc", wifi_active=False), "allow")

    def test_dac_capability(self):
        self.assertEqual(self.check(25, "dac"), "allow")
        self.assertEqual(self.check(18, "dac"), "block")

    def test_general_gpio(self):
        self.assertEqual(self.check(18, "mode", mode="output"), "allow")

if __name__ == "__main__":
    unittest.main()
