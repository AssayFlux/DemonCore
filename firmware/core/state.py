"""Small boot-state file; writes occur only at boot and after a stable boot window."""
try:
    import ujson as json
except ImportError:
    import json

STATE_PATH = "demoncore_state.json"
CRASH_LIMIT = 3

def load_state(path=STATE_PATH):
    try:
        with open(path, "r") as stream:
            state = json.load(stream)
    except OSError:
        return {"consecutive_crashes": 0, "safe_mode": False}
    except (ValueError, TypeError):
        return {"consecutive_crashes": CRASH_LIMIT, "safe_mode": True}
    if not isinstance(state, dict):
        return {"consecutive_crashes": CRASH_LIMIT, "safe_mode": True}
    count = state.get("consecutive_crashes", 0)
    if not isinstance(count, int) or count < 0:
        return {"consecutive_crashes": CRASH_LIMIT, "safe_mode": True}
    return {"consecutive_crashes": count, "safe_mode": count >= CRASH_LIMIT}

def _save_state(path, state):
    with open(path, "w") as stream:
        json.dump(state, stream)

def prepare_boot(path=STATE_PATH):
    state = load_state(path)
    count = state["consecutive_crashes"] + 1
    state = {"consecutive_crashes": count, "safe_mode": state["safe_mode"] or count >= CRASH_LIMIT}
    try:
        _save_state(path, state)
    except OSError:
        return {"consecutive_crashes": count, "safe_mode": True}
    return state

def mark_stable(path=STATE_PATH):
    state = {"consecutive_crashes": 0, "safe_mode": False}
    _save_state(path, state)
    return state
