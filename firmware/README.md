# DemonCore ESP32 firmware workspace

**Workspace:** `firmware/`
**Target:** ESP-WROOM-32, 38-pin, 4 MiB flash, no PSRAM
**Runtime:** pinned MicroPython ESP32_GENERIC build

This is the firmware-builder directory. ESP32 MicroPython source, board profiles, core runtime, optional plugins, partition layout, frozen-module manifest and tests belong here. Do not put Flutter/Dart app code here.

## Where to enter

| Work | Directory |
|---|---|
| Core runtime and DCP codec | [`core/`](core/README.md) |
| Board profile and GPIO safety | [`boards/`](boards/README.md) |
| Optional peripheral integrations | [`plugins/`](plugins/README.md) |
| Build the merged flashable BIN | [`build/`](build/README.md) |
| Firmware tests | [`tests/`](tests/README.md) |
| Pinned upstream dependencies | [`vendor/`](vendor/README.md) |

Run the builder from the repository root:

```bash
firmware/build/build.sh
```

The current recorded CI image has 12.57% OTA-slot spare, above the 10% minimum. See [build status](build/README.md).

## Acceptance still pending

CI does not replace physical ESP32 verification. Boot log, free heap (>60 KiB), GC headroom (>=20 KiB), filesystem free space (>=25%) and live connectivity must be measured on the owner's board. Exact physical 38-pin header mapping remains owner-unverified.

See [AGENTS.md](../AGENTS.md), [TASKS.md](../TASKS.md) and [NORTH_STAR.md](../NORTH_STAR.md).
