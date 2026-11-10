#!/usr/bin/env python3
"""Data-driven GPIO safety checks for the ESP-WROOM-32 board profile."""
import argparse
import json
from pathlib import Path

DEFAULT_PROFILE = Path(__file__).resolve().parents[1] / "firmware" / "boards" / "esp32-wroom-38pin.json"
ACTIONS = ("mode", "write", "pwm", "adc", "dac")

def load_profile(path=DEFAULT_PROFILE):
    with Path(path).open("r", encoding="utf-8") as stream:
        profile = json.load(stream)
    required = {"blocked", "strapping", "console", "input_only", "adc1", "adc2", "dac", "general"}
    if not required.issubset(profile.get("classes", {})):
        raise ValueError("board profile is missing required GPIO classes")
    return profile

def evaluate(profile, pin, action, mode=None, confirm=False, wifi_active=False):
    classes = profile["classes"]
    memberships = {name for name, pins in classes.items() if pin in pins}
    def result(status, reason):
        return {"status": status, "reason": reason, "pin": pin, "action": action}

    if action not in ACTIONS:
        return result("block", "unsupported pin action")
    if not isinstance(pin, int) or isinstance(pin, bool):
        return result("block", "GPIO identifier must be an integer")
    if "blocked" in memberships:
        return result("block", profile["rules"]["blocked"])
    if pin not in profile["available_gpio"]:
        return result("block", "GPIO is not available on this ESP32 profile")
    if "console" in memberships:
        return result("block", profile["rules"]["console"])

    if action == "mode":
        if mode not in ("input", "input_pullup", "input_pulldown", "output"):
            return result("block", "unsupported digital mode")
        if "input_only" in memberships and mode != "input":
            return result("block", profile["rules"]["input_only"])
        if not ({"general", "strapping", "input_only"} & memberships):
            return result("block", "GPIO has no digital mode capability in this profile")
    elif action in ("write", "pwm") and "input_only" in memberships:
        return result("block", profile["rules"]["input_only"])
    elif action == "adc":
        if "adc1" not in memberships and "adc2" not in memberships:
            return result("block", "GPIO has no ADC capability")
        if "adc2" in memberships and wifi_active and "adc1" not in memberships:
            return result("block", profile["rules"]["adc2"])
    elif action == "dac" and "dac" not in memberships:
        return result("block", "GPIO has no DAC capability")

    if "strapping" in memberships:
        if not confirm:
            return result("warn", profile["rules"]["strapping"])
        return result("allow", "explicit confirmation supplied; ensure GPIO12 is low at boot")
    return result("allow", "allowed by board profile")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pin", type=int, required=True)
    parser.add_argument("--action", choices=ACTIONS, required=True)
    parser.add_argument("--mode", choices=("input", "input_pullup", "input_pulldown", "output"))
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--wifi-active", action="store_true")
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    args = parser.parse_args()
    decision = evaluate(load_profile(args.profile), args.pin, args.action, args.mode, args.confirm, args.wifi_active)
    print(json.dumps(decision, sort_keys=True))
    return 2 if decision["status"] == "block" else 0

if __name__ == "__main__":
    raise SystemExit(main())
