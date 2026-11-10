# Firmware build output

Run `firmware/build/build.sh` after installing the pinned ESP-IDF toolchain and
cloning MicroPython at the commits in `firmware/vendor/micropython.lock`.
Set `IDF_PATH` and `MPYTHON_DIR`. The script freezes the core, applies Profile
A partitions, and emits `Demoncore ESP32 Master Firmware.bin` at flash offset
`0x1000`.

The upstream ESP32 board configuration defaults to performance optimization
(`-O2`). The build selects size optimization (`-Os`) and disables optional
features outside the current DemonCore board contract: SPI Ethernet PHY
drivers (W5500, KSZ8851SNL and DM9051), and runtime INFO-level ESP
logging. The ULP coprocessor remains enabled because the pinned MicroPython
ESP32 port compiles its ULP support source unconditionally. Wi-Fi, BLE, TLS, MicroPython networking and the frozen
DemonCore core remain enabled. The ESP-IDF `ETH_USE_SPI_ETHERNET` umbrella menu may still read enabled because
its pinned Kconfig default is `y`; that setting alone does not enable a PHY.
The report verifies that all three concrete PHY driver options are disabled.
The build fails closed if the pinned upstream base configuration changes, and
the report verifies the generated sdkconfig.
Disabling these optional facilities means this image does not provide SPI
Ethernet; it is not part of the current hardware plan.

The report checks the exact Profile A layout and at least 10% OTA-slot spare,
and records source/image hashes. Generated binaries and intermediate build
products are CI artifacts, not committed. Post-boot heap, GC headroom, runtime
filesystem free space and performance require physical ESP32 measurements.
