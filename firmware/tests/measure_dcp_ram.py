"""Measure MicroPython heap cost of importing and exercising the DCP codec.
Run from the repository root: micropython firmware/tests/measure_dcp_ram.py
"""
import gc
try:
    import micropython
except ImportError:
    micropython = None

gc.collect()
before = gc.mem_free() if hasattr(gc, "mem_free") else None
from core import dcp
gc.collect()
after_import = gc.mem_free() if hasattr(gc, "mem_free") else None

sample = {
    "v": "1.0", "id": "0000000000000001", "src": "node:1",
    "dst": "node:2", "t": "req", "op": "sys.ping",
    "args": {"token": "ram-measure"},
}
payload = dcp.encode(sample)
decoded = dcp.decode(payload)
gc.collect()
after_roundtrip = gc.mem_free() if hasattr(gc, "mem_free") else None

if before is not None and after_import is not None:
    print("DCP_MODULE_HEAP_BYTES", before - after_import)
    print("DCP_ROUNDTRIP_RETAINED_BYTES", after_import - after_roundtrip)
else:
    print("DCP_HEAP_MEASUREMENT_UNAVAILABLE: runtime has no gc.mem_free()")
print("DCP_SAMPLE_ENCODED_BYTES", len(payload))
print("DCP_ROUNDTRIP_OK", decoded == sample)
