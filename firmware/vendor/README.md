# Vendored firmware dependencies

The reproducible ESP32 build fetches upstream MicroPython and ESP-IDF at the
exact commits in `micropython.lock`. Source archive SHA-256 values are
calculated and recorded in the generated build report. Upstream source is not
patched in Git; the build overlays only DemonCore's partition CSV into the
temporary MicroPython checkout.

MicroPython is MIT-licensed. The repository's Apache-2.0 licence is preserved.
