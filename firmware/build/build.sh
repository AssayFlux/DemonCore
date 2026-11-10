#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
: "${MPYTHON_DIR:?Set MPYTHON_DIR to the pinned MicroPython v1.29.0 checkout}"
: "${IDF_PATH:?Set IDF_PATH to the pinned ESP-IDF v5.5.2 checkout}"

MPYTHON_COMMIT="0fd6c573ea815774668bbb16b8e197c8822368b2"
IDF_COMMIT="30aaf64524299d3bde422ca9a2848090d1bc5d0f"
ACTUAL_MPYTHON_COMMIT="$(git -C "$MPYTHON_DIR" rev-parse HEAD)"
ACTUAL_IDF_COMMIT="$(git -C "$IDF_PATH" rev-parse HEAD)"
test "$ACTUAL_MPYTHON_COMMIT" = "$MPYTHON_COMMIT" || { echo "Unexpected MicroPython commit: $ACTUAL_MPYTHON_COMMIT" >&2; exit 2; }
test "$ACTUAL_IDF_COMMIT" = "$IDF_COMMIT" || { echo "Unexpected ESP-IDF commit: $ACTUAL_IDF_COMMIT" >&2; exit 2; }

OUT_DIR="$ROOT/firmware/build"
BUILD_DIR="$MPYTHON_DIR/ports/esp32/build-ESP32_GENERIC-OTA"
SDKCONFIG_BASE="$MPYTHON_DIR/ports/esp32/boards/sdkconfig.base"
mkdir -p "$OUT_DIR"

# The upstream ESP32 profile selects -O2 for speed. DemonCore's fixed Profile A
# OTA slots require a smaller image, so deterministically select ESP-IDF -Os.
# Fail closed if the pinned upstream configuration changes unexpectedly.
if [[ "$(grep -c '^CONFIG_COMPILER_OPTIMIZATION_PERF=y
SOURCE_SHA256="$(git -C "$MPYTHON_DIR" archive --format=tar "$MPYTHON_COMMIT" | gzip -n | sha256sum | awk '{print $1}')"
cp "$ROOT/firmware/partitions.csv" "$MPYTHON_DIR/ports/esp32/partitions-4MiB-ota.csv"

make -C "$MPYTHON_DIR/mpy-cross" -j2
make -C "$MPYTHON_DIR/ports/esp32" BOARD=ESP32_GENERIC BOARD_VARIANT=OTA FROZEN_MANIFEST="$ROOT/firmware/manifest.py" submodules
make -C "$MPYTHON_DIR/ports/esp32" -j2 BOARD=ESP32_GENERIC BOARD_VARIANT=OTA FROZEN_MANIFEST="$ROOT/firmware/manifest.py" all

MERGED="$OUT_DIR/Demoncore ESP32 Master Firmware.bin"
cp "$BUILD_DIR/firmware.bin" "$MERGED"
python3 "$ROOT/firmware/build/report.py" --build-dir "$BUILD_DIR" --partition-csv "$ROOT/firmware/partitions.csv" --merged "$MERGED" --source-commit "$ACTUAL_MPYTHON_COMMIT" --source-sha256 "$SOURCE_SHA256" --idf-commit "$ACTUAL_IDF_COMMIT" --output "$OUT_DIR/report.md"
sha256sum "$MERGED" > "$OUT_DIR/firmware.sha256"
cp "$ROOT/firmware/partitions.csv" "$OUT_DIR/partitions.csv"
echo "Built: $MERGED"
 "$SDKCONFIG_BASE")" != "1" ]]; then
    echo "Expected exactly one upstream performance-optimization setting in $SDKCONFIG_BASE" >&2
    exit 2
fi
sed -i 's/^CONFIG_COMPILER_OPTIMIZATION_PERF=y$/CONFIG_COMPILER_OPTIMIZATION_SIZE=y/' "$SDKCONFIG_BASE"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

SOURCE_SHA256="$(git -C "$MPYTHON_DIR" archive --format=tar "$MPYTHON_COMMIT" | gzip -n | sha256sum | awk '{print $1}')"
cp "$ROOT/firmware/partitions.csv" "$MPYTHON_DIR/ports/esp32/partitions-4MiB-ota.csv"

make -C "$MPYTHON_DIR/mpy-cross" -j2
make -C "$MPYTHON_DIR/ports/esp32" BOARD=ESP32_GENERIC BOARD_VARIANT=OTA FROZEN_MANIFEST="$ROOT/firmware/manifest.py" submodules
make -C "$MPYTHON_DIR/ports/esp32" -j2 BOARD=ESP32_GENERIC BOARD_VARIANT=OTA FROZEN_MANIFEST="$ROOT/firmware/manifest.py" all

MERGED="$OUT_DIR/Demoncore ESP32 Master Firmware.bin"
cp "$BUILD_DIR/firmware.bin" "$MERGED"
python3 "$ROOT/firmware/build/report.py" --build-dir "$BUILD_DIR" --partition-csv "$ROOT/firmware/partitions.csv" --merged "$MERGED" --source-commit "$ACTUAL_MPYTHON_COMMIT" --source-sha256 "$SOURCE_SHA256" --idf-commit "$ACTUAL_IDF_COMMIT" --output "$OUT_DIR/report.md"
sha256sum "$MERGED" > "$OUT_DIR/firmware.sha256"
cp "$ROOT/firmware/partitions.csv" "$OUT_DIR/partitions.csv"
echo "Built: $MERGED"
