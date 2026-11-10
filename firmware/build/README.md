# Firmware build output

Run `firmware/build/build.sh` after installing the pinned ESP-IDF toolchain and
cloning MicroPython at the commits in `firmware/vendor/micropython.lock`.
Set `IDF_PATH` and `MPYTHON_DIR`. The script freezes the core, applies Profile
A partitions, and emits `Demoncore ESP32 Master Firmware.bin` at flash offset
`0x1000`.

The upstream ESP32 board configuration defaults to performance optimization
(`-O2`). The build script changes that pinned configuration to size
optimization (`-Os`) because Profile A is fixed and the application must leave
at least 10% of each OTA slot unused. The script fails closed if the expected
upstream setting changes, and the report verifies the generated sdkconfig.
This trades some execution speed for flash headroom; benchmark timing on the
physical target remains part of hardware validation.

The report checks the exact Profile A layout and at least 10% OTA-slot spare,
and records source/image hashes. Generated binaries and intermediate build
products are CI artifacts, not committed. Post-boot heap, GC headroom and
runtime filesystem free space require a physical ESP32 measurement.
