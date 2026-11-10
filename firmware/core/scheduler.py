"""Cooperative asyncio scheduler with watchdog feed confined to its main loop."""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

async def _sleep_ms(milliseconds):
    sleep_ms = getattr(asyncio, "sleep_ms", None)
    if sleep_ms is not None:
        await sleep_ms(milliseconds)
    else:
        await asyncio.sleep(milliseconds / 1000.0)

class Scheduler:
    def __init__(self, interval_ms=100, stable_ticks=300):
        self.interval_ms = interval_ms
        self.stable_ticks = stable_ticks
        self._callbacks = []

    def add(self, callback):
        self._callbacks.append(callback)

    async def run(self, watchdog=None, on_stable=None, max_ticks=None):
        ticks = 0
        stable_called = False
        while max_ticks is None or ticks < max_ticks:
            for callback in self._callbacks:
                result = callback()
                if hasattr(result, "__await__"):
                    await result
            ticks += 1
            if not stable_called and on_stable is not None and ticks >= self.stable_ticks:
                on_stable()
                stable_called = True
            if watchdog is not None:
                watchdog.feed()
            await _sleep_ms(self.interval_ms)
