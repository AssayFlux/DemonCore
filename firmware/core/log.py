"""Fixed-capacity in-memory log ring; messages are truncated and never persisted."""
class LogRing:
    LEVELS = ("DEBUG", "INFO", "WARN", "ERROR")

    def __init__(self, capacity=32, message_limit=96):
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._items = [None] * capacity
        self._next = 0
        self._count = 0
        self._message_limit = message_limit

    def add(self, level, message):
        if level not in self.LEVELS:
            level = "INFO"
        text = str(message)
        if len(text) > self._message_limit:
            text = text[:self._message_limit]
        self._items[self._next] = (level, text)
        self._next = (self._next + 1) % len(self._items)
        if self._count < len(self._items):
            self._count += 1

    def snapshot(self):
        start = (self._next - self._count) % len(self._items)
        result = []
        for offset in range(self._count):
            item = self._items[(start + offset) % len(self._items)]
            if item is not None:
                result.append(item)
        return result
