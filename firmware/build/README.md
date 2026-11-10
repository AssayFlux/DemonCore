# DemonCore ESP32 build and current feature status

This directory documents the generated ESP32 firmware image and the checks that have actually run. It is intentionally explicit about the difference between a compiled platform capability and a working DemonCore feature.

## Target and image

- Board target: ESP-WROOM-32 / ESP32_GENERIC, 4 MiB flash, no PSRAM.
- MicroPython: v1.29.0, pinned commit `0fd6c573ea815774668bbb16b8e197c8822368b2`.
- ESP-IDF: v5.5.2, pinned commit `30aaf64524299d3bde422ca9a2848090d1bc5d0f`.
- Profile A: two 1,600 KiB OTA slots, 16 KiB NVS, 832 KiB filesystem.
- One merged image: `Demoncore ESP32 Master Firmware.bin`; flash at offset `0x1000`.
- Build uses `-Os`; optional SPI Ethernet PHY drivers and runtime INFO-level ESP logging are excluded. Wi-Fi, BLE, TLS and ULP support in the underlying MicroPython/ESP-IDF build are retained.

## Latest verified CI build (2026-11-10)

Workflow: [CI run 42797507810](https://github.com/AssayFlux/DemonCore/actions/runs/42797507810), commit `631566cfd603b0157a3669bf40e92faefb37ef4f).

| Check | Result |
|---|---|
| Lint | PASS |
| MicroPython v1.29.0 unix-port build | PASS |
| Firmware core tests | PASS — 9 tests |
| ESP32 merged firmware build | PASS |
| Profile A partition layout | PASS |
| Application image | 1,432,432 bytes |
| OTA slot | 1,638,400 bytes |
| OTA slot spare | 205,968 bytes / 12.57% — PASS (minimum 10%) |
| Merged image | 1,493,872 bytes |
| Merged image SHA-256 | `42e42960c3f87090138a1db491cd9bb64c252468386c09711995ed62dca45ce8` |

These are CI/build measurements, not physical-board measurements.

## BLE and Wi-Fi: what is and is not working

**Important:** BLE and Wi-Fi being retained in the ESP-IDF/MicroPython build means the platform has those underlying capabilities. It does **not** mean DemonCore already has working BLE or Wi-Fi DCP transports.

| Capability | Current condition |
|---|---|
| ESP-IDF / MicroPython Wi-Fi support | Included in build |
| ESP-IDF / MicroPython BLE support | Included in build |
| DemonCore BLE DCP adapter | NOT IMPLEMENTED |
| DemonCore Wi-Fi station/reconnect adapter | NOT IMPLEMENTED |
| Setup access point and WebSocket/HTTP DCP endpoints | NOT IMPLEMENTED |
| BLE pairing and owner claim flow | NOT IMPLEMENTED |
| App-to-device BLE/Wi-Fi control | NOT IMPLEMENTED |
| Config defaults | BLE=false, Wi-Fi=false |

The configuration defaults are deliberately off because the corresponding DemonCore transport and claim implementations are not complete. Changing those booleans alone would not make a usable connection and could consume RAM without providing a functional service.

The ordered backlog defines the work:
- T-111: claim state machine and BLE claim path.
- T-201: BLE GATT DCP transport, MTU chunking and phone test.
- T-202: Wi-Fi station reconnect, setup AP, WebSocket/HTTP DCP and discovery.

Do not advertise BLE/Wi-Fi as operational until those tasks and their hardware acceptance checks pass. No credentials or secrets should be placed in config files or logs.

## Hardware checks still required

The cloud CI runner cannot measure the physical ESP32. These checks remain pending and must be recorded after flashing a real board:

1. Confirm boot completes without reset loops or uncaught exceptions.
2. Record `gc.mem_free()` after boot; the target is greater than 60 KiB with one transport active.
3. Measure GC headroom; target is at least 20 KiB.
4. Record filesystem total/free bytes; target is at least 25% free.
5. Once BLE/Wi-Fi adapters exist, repeat memory checks with the relevant transport active and perform actual phone/network communication tests.

Until these checks are run, the binary is a CI-built firmware image, not a hardware-accepted release.

## Build locally

Install the exact pinned MicroPython and ESP-IDF revisions listed in `firmware/vendor/micropython.lock`. Set `MPYTHON_DIR` and `IDF_PATH`, then run:

```bash
firmware/build/build.sh
```

The script generates the merged image, `report.md`, `firmware.sha256` and a copy of `partitions.csv` under this directory. It fails if the Profile A layout or 10% OTA headroom requirement is not met.
