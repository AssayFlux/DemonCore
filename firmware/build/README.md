# Firmware build output

Run `firmware/build/build.sh` after installing the pinned ESP-IDF toolchain and
cloning MicroPython at the commits in `firmware/vendor/micropython.lock`.
Set `IDF_PATH` and `MPYTHON_DIR`. The script freezes the core, applies Profile
A partitions, and emits `Demoncore ESP32 Master Firmware.bin` at flash offset
`0x1000`.

The report checks for at least 10% OTA-slot spare and records source/image
hashes. Generated binaries and intermediate build products are CI artifacts,
not committed. Post-boot heap requires a physical ESP32 measurement.
