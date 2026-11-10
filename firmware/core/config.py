"""JSON configuration defaults and loading; no secrets are logged or emitted."""
try:
    import ujson as json
except ImportError:
    import json

CONFIG_PATH = "demoncore_config.json"

def defaults():
    return {
        "schema_version": 1,
        "device_name": "DemonCore",
        "log_capacity": 32,
        "loop_interval_ms": 100,
        "stable_boot_ms": 30000,
        "watchdog_timeout_ms": 5000,
        "transports": {"ble": False, "wifi": False, "mqtt": False, "espnow": False},
    }

def load_config(path=CONFIG_PATH):
    config = defaults()
    try:
        with open(path, "r") as stream:
            stored = json.load(stream)
    except OSError:
        return config
    except (ValueError, TypeError):
        return config
    if not isinstance(stored, dict) or stored.get("schema_version") != 1:
        return config
    transports = stored.get("transports", {})
    if not isinstance(transports, dict):
        transports = {}
    config.update({key: value for key, value in stored.items() if key in config and key != "transports"})
    for key in config["transports"]:
        if isinstance(transports.get(key), bool):
            config["transports"][key] = transports[key]
    if not isinstance(config["log_capacity"], int) or config["log_capacity"] < 1:
        config["log_capacity"] = 32
    if not isinstance(config["loop_interval_ms"], int) or config["loop_interval_ms"] < 10:
        config["loop_interval_ms"] = 100
    if not isinstance(config["stable_boot_ms"], int) or config["stable_boot_ms"] < 1000:
        config["stable_boot_ms"] = 30000
    if not isinstance(config["watchdog_timeout_ms"], int) or config["watchdog_timeout_ms"] < 1000:
        config["watchdog_timeout_ms"] = 5000
    return config
