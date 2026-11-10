"""DemonCore asyncio runtime entry point."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from core.config import load_config
from core.log import LogRing
from core.scheduler import Scheduler
from core.state import load_state, mark_stable
from core.watchdog import create_watchdog

def build_runtime(config_path="demoncore_config.json", state_path="demoncore_state.json"):
    config = load_config(config_path)
    state = load_state(state_path)
    logs = LogRing(config["log_capacity"])
    if state["safe_mode"]:
        logs.add("WARN", "safe mode active after repeated boot failures")
    scheduler = Scheduler(
        interval_ms=config["loop_interval_ms"],
        stable_ticks=max(1, config["stable_boot_ms"] // config["loop_interval_ms"]),
    )
    watchdog = create_watchdog(config["watchdog_timeout_ms"])
    return config, state, logs, scheduler, watchdog

async def run(config_path="demoncore_config.json", state_path="demoncore_state.json"):
    config, state, logs, scheduler, watchdog = build_runtime(config_path, state_path)
    if state["safe_mode"]:
        logs.add("WARN", "user tasks remain disabled in safe mode")
    await scheduler.run(watchdog, lambda: mark_stable(state_path))

def main():
    asyncio.run(run())

if __name__ == "__main__":
    main()
