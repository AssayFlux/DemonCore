"""Watchdog construction. Feeding is deliberately owned by scheduler.run only."""
def create_watchdog(timeout_ms=5000):
    try:
        from machine import WDT
    except ImportError:
        return None
    return WDT(timeout=timeout_ms)
