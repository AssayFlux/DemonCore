"""DemonCore identity storage backed by the ESP32 NVS namespace.

Secrets are stored as fixed-size NVS blobs and are never logged or printed.
This module does not enable flash encryption; physical flash-at-rest protection
remains an owner-controlled hardware/security decision.
Flash/RAM: six small NVS values; temporary buffers are at most 32 bytes.
RAM measurement: exercise load/store with the MicroPython ESP32 runtime.
"""
NVS_NAMESPACE = "demoncore"
NODE_ID_BYTES = 8
SECRET_BYTES = 32
COUNTER_BYTES = 8
MAX_U64 = (1 << 64) - 1

_KEYS = ("node_id", "dev_secret", "cell_key", "tx_count", "rx_count", "claimed")


def _uint_bytes(value, width):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("value must be a non-negative integer")
    if value >= (1 << (width * 8)):
        raise ValueError("integer is out of range")
    result = bytearray(width)
    index = width - 1
    while index >= 0:
        result[index] = value & 255
        value >>= 8
        index -= 1
    return bytes(result)


def _bytes_uint(value):
    result = 0
    for byte in value:
        result = (result << 8) | byte
    return result


def _secret(value, name):
    if not isinstance(value, (bytes, bytearray)) or len(value) != SECRET_BYTES:
        raise ValueError(name + " must be exactly 32 bytes")
    return bytes(value)


class IdentityStore:
    """Read/write one device identity; pass an NVS-compatible object for tests."""

    def __init__(self, nvs=None):
        if nvs is None:
            from esp32 import NVS
            nvs = NVS(NVS_NAMESPACE)
        self._nvs = nvs

    def _read_blob(self, key, size):
        buffer = bytearray(size)
        try:
            length = self._nvs.get_blob(key, buffer)
        except OSError:
            return None
        if length != size:
            raise ValueError("Corrupt identity field: " + key)
        return bytes(buffer)

    def _read_i32(self, key):
        try:
            value = self._nvs.get_i32(key)
        except OSError:
            return None
        if value not in (0, 1):
            raise ValueError("Corrupt identity field: " + key)
        return value

    def load(self):
        node_id = self._read_blob("node_id", NODE_ID_BYTES)
        device_secret = self._read_blob("dev_secret", SECRET_BYTES)
        cell_key = self._read_blob("cell_key", SECRET_BYTES)
        tx_counter = self._read_blob("tx_count", COUNTER_BYTES)
        rx_counter = self._read_blob("rx_count", COUNTER_BYTES)
        claimed = self._read_i32("claimed")
        fields = (node_id, device_secret, cell_key, tx_counter, rx_counter, claimed)
        if all(value is None for value in fields):
            return None
        if any(value is None for value in fields):
            raise ValueError("Incomplete device identity in NVS")
        numeric_id = _bytes_uint(node_id)
        if numeric_id == 0:
            raise ValueError("Corrupt device node ID")
        return {
            "node_id": numeric_id,
            "device_secret": device_secret,
            "cell_key": cell_key,
            "tx_counter": _bytes_uint(tx_counter),
            "rx_counter": _bytes_uint(rx_counter),
            "claimed": bool(claimed),
        }

    def store(self, node_id, device_secret, cell_key,
              tx_counter=0, rx_counter=0, claimed=False):
        if isinstance(node_id, bool) or not isinstance(node_id, int) or not 1 <= node_id <= MAX_U64:
            raise ValueError("node_id must be an integer in the uint64 range")
        device_secret = _secret(device_secret, "device_secret")
        cell_key = _secret(cell_key, "cell_key")
        if not isinstance(claimed, bool):
            raise ValueError("claimed must be a boolean")
        values = (
            ("node_id", _uint_bytes(node_id, NODE_ID_BYTES)),
            ("dev_secret", device_secret),
            ("cell_key", cell_key),
            ("tx_count", _uint_bytes(tx_counter, COUNTER_BYTES)),
            ("rx_count", _uint_bytes(rx_counter, COUNTER_BYTES)),
        )
        for key, value in values:
            self._nvs.set_blob(key, value)
        self._nvs.set_i32("claimed", 1 if claimed else 0)
        self._nvs.commit()

    def wipe(self):
        for key in _KEYS:
            try:
                self._nvs.erase_key(key)
            except OSError:
                pass
        self._nvs.commit()
