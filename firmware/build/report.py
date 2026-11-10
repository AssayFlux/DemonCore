#!/usr/bin/env python3
"""Generate a size/hash/partition report for the DemonCore ESP32 image."""
import argparse
import csv
import hashlib
from pathlib import Path

EXPECTED = {
    "nvs": (0x9000, 0x4000, "data", "nvs"),
    "otadata": (0xD000, 0x2000, "data", "ota"),
    "phy_init": (0xF000, 0x1000, "data", "phy"),
    "ota_0": (0x10000, 0x190000, "app", "ota_0"),
    "ota_1": (0x1A0000, 0x190000, "app", "ota_1"),
    "vfs": (0x330000, 0xD0000, "data", "fat"),
}
OPTIONAL_DISABLED = (
    "CONFIG_LOG_MAXIMUM_LEVEL_INFO",
    "CONFIG_ETH_USE_SPI_ETHERNET",
    "CONFIG_ETH_SPI_ETHERNET_W5500",
    "CONFIG_ETH_SPI_ETHERNET_KSZ8851SNL",
    "CONFIG_ETH_SPI_ETHERNET_DM9051",
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_partitions(path):
    partitions = {}
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.reader(line for line in stream if not line.lstrip().startswith("#")):
            if not row or len(row) < 5:
                continue
            name, kind, subtype, offset, size = [item.strip() for item in row[:5]]
            partitions[name] = (int(offset, 0), int(size, 0), kind, subtype)
    return partitions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", required=True)
    parser.add_argument("--partition-csv", required=True)
    parser.add_argument("--merged", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--idf-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    build_dir = Path(args.build_dir)
    partition_csv = Path(args.partition_csv)
    merged = Path(args.merged)
    app = build_dir / "micropython.bin"
    bootloader = build_dir / "bootloader" / "bootloader.bin"
    partition_bin = build_dir / "partition_table" / "partition-table.bin"
    for path in (app, bootloader, partition_bin, merged):
        if not path.is_file():
            raise SystemExit("Missing build output: " + str(path))

    actual = parse_partitions(partition_csv)
    if actual != EXPECTED:
        raise SystemExit("Profile A partition layout mismatch: " + repr(actual))

    slot_size = actual["ota_0"][1]
    app_size = app.stat().st_size
    headroom = slot_size - app_size
    headroom_percent = 100.0 * headroom / slot_size
    passes = headroom >= slot_size * 0.10
    fs_size = actual["vfs"][1]
    merged_size = merged.stat().st_size
    sdkconfig = build_dir / "sdkconfig"
    if not sdkconfig.is_file():
        raise SystemExit("Missing ESP-IDF sdkconfig; cannot verify build configuration")
    sdkconfig_text = sdkconfig.read_text(encoding="utf-8")
    if "CONFIG_COMPILER_OPTIMIZATION_SIZE=y" not in sdkconfig_text:
        raise SystemExit("ESP-IDF build is not using size optimization (-Os)")
    if "CONFIG_COMPILER_OPTIMIZATION_PERF=y" in sdkconfig_text:
        raise SystemExit("ESP-IDF performance optimization (-O2) is still enabled")
    enabled_optional = [name for name in OPTIONAL_DISABLED if name + "=y" in sdkconfig_text]
    if enabled_optional:
        raise SystemExit("Optional ESP-IDF features unexpectedly enabled: " + ", ".join(enabled_optional))

    lines = [
        "# DemonCore ESP32 build report", "",
        "- Target: ESP-WROOM-32 / ESP32_GENERIC, 4 MiB flash, no PSRAM",
        "- MicroPython: v1.29.0, commit `" + args.source_commit + "`",
        "- MicroPython source archive SHA-256: `" + args.source_sha256 + "`",
        "- ESP-IDF: v5.5.2, commit `" + args.idf_commit + "`",
        "- Compiler optimization: ESP-IDF size mode (`-Os`), verified from generated sdkconfig",
        "- Optional features disabled: SPI Ethernet PHYs (W5500/KSZ8851SNL/DM9051), runtime INFO-level ESP logging",
        "- Frozen manifest: `firmware/manifest.py` (core package, boot.py, main.py, asyncio)",
        "- Merged image: `" + merged.name + "`",
        "- Merged image flash offset: `0x1000`",
        "- Merged image size: %d bytes" % merged_size,
        "- Merged image SHA-256: `" + sha256(merged) + "`",
        "- Bootloader size: %d bytes" % bootloader.stat().st_size,
        "- Partition table binary size: %d bytes" % partition_bin.stat().st_size,
        "- Application image size: %d bytes" % app_size,
        "- OTA application slot size: %d bytes" % slot_size,
        "- OTA slot headroom: %d bytes (%.2f%%)" % (headroom, headroom_percent),
        "- 10%% spare requirement: %s" % ("PASS" if passes else "FAIL"),
        "- Filesystem partition: %d bytes" % fs_size,
        "- Filesystem free space after initial format: 100%% expected; actual runtime free space not measured",
        "- Post-boot free heap: NOT MEASURED — requires a physical ESP32 boot",
        "- GC headroom with one active transport: NOT MEASURED — requires hardware runtime profiling",
        "", "## Partition layout", "", "| Name | Offset | Size |", "|---|---:|---:|",
    ]
    for name, values in actual.items():
        lines.append("| %s | 0x%06x | %d |" % (name, values[0], values[1]))
    Path(args.output).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("APP_IMAGE_BYTES", app_size)
    print("OTA_SLOT_BYTES", slot_size)
    print("OTA_HEADROOM_BYTES", headroom)
    print("OTA_HEADROOM_PERCENT", "%.2f" % headroom_percent)
    print("MERGED_IMAGE_BYTES", merged_size)
    print("MERGED_IMAGE_SHA256", sha256(merged))
    print("MICROPYTHON_SOURCE_ARCHIVE_SHA256", args.source_sha256)
    print("PROFILE_A_LAYOUT", "PASS")
    print("SIZE_OPTIMIZATION", "PASS")
    print("OPTIONAL_FEATURES_DISABLED", "PASS")
    print("OTA_SPARE_10_PERCENT", "PASS" if passes else "FAIL")
    if not passes:
        raise SystemExit("Firmware does not fit the OTA slot with 10% spare")


if __name__ == "__main__":
    main()
