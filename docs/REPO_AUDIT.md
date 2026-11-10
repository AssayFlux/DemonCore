# Repository audit — 2026-11-10

## Executive result

The tracked repository is small and purpose-built, with separate top-level workspaces for firmware, app, hub, protocol and host tools. The root README was only `# DemonCore`; this audit adds a clear project map and five-step pathway.

**No tracked file was deleted in this pass.** The inventory did not establish any source file as dead or safe to remove. Binary assets must be inspected before being renamed or removed; the repository interface returned metadata but not binary contents.

## Directory map

| Path | Purpose | Current assessment |
|---|---|---|
| `.github/workflows/` | CI | Keep; build/test automation is required |
| `Assets/` | Supplied 3D/image source assets | Keep pending content and licence inspection |
| `app/` | Flutter Android control app | Placeholder README only; no Flutter project files yet |
| `docs/` | Architecture and project documentation | Keep; North Star and audit references added |
| `firmware/` | ESP32 MicroPython firmware | Active implementation area |
| `firmware/boards/` | Board profile and pin policy | Keep; physical header mapping remains unverified |
| `firmware/build/` | Reproducible merged-image builder/report | Keep; CI image passes OTA margin, hardware checks pending |
| `firmware/core/` | Async runtime, DCP codec, state/log/scheduler/watchdog | Active foundation |
| `firmware/tests/` | Firmware core tests and RAM measurement helper | Keep; acceptance evidence |
| `firmware/vendor/` | Pinned upstream dependency lock | Keep for reproducible build |
| `hub/` | Self-hosted fleet control plane | Placeholder README only |
| `protocol/` | DCP specification/schema/ops/vectors | Active shared contract; keep |
| `tests/` | Simulator integration tests | Keep |
| `tools/` | Simulator, pin validator and host tooling | Active developer utilities |
| `web-flasher/` | Browser flashing workspace | Placeholder README only |

## Asset inventory and disposition

| Existing file | Established metadata | Action |
|---|---|---|
| `Assets/ESP32_NodeMCU_Professional.stl` | STL; 7,099,284 bytes | Keep name; inspect mesh and licence before use |
| `Assets/ESP32_NodeMCU_Professional.3mf` | 3MF; 1,746,388 bytes | Keep name; inspect package metadata/model and licence |
| `Assets/ESP32_NodeMCU_Professional_Package.zip` | ZIP; 6,562,109 bytes | Keep; inspect archive manifest before deciding if contents duplicate standalone files |
| `Assets/file_00000000049482118b4e6dd1685eb63f.png` | PNG; 2,396,063 bytes | Do not guess its subject; rename only after visual inspection |

The binary contents could not be read through the connected repository interface during this audit. Consequently, no asset rename, deletion, deduplication or licence assertion is made. Before T-310, identify the model's exact board revision, verify geometry against the owner's physical board, and record redistribution rights.

## Findings and blockers

1. **Phase 1 is not complete.** T-103 is blocked on owner confirmation of physical pin labels; T-107 is blocked on physical boot and runtime resource measurements; T-113 is blocked because Flutter/Dart tooling was unavailable in the prior implementation environment. T-106 depends on T-103.
2. **App and hub are not implemented yet.** Their directories currently contain only README files. They are not buildable projects.
3. **Platform support is not a DemonCore transport.** MicroPython Wi-Fi/BLE support does not mean DemonCore BLE/Wi-Fi DCP adapters or claim are implemented.
4. **No unnecessary tracked source was proven.** Keep CI, schemas, vectors, tests, build scripts, pin profile and dependency lock.
5. **Potential asset duplication is unresolved.** The ZIP may contain the standalone STL/3MF, but its manifest was not inspectable; do not delete it based on a guess.

## Safe next actions

- Owner: provide a clear photo of both sides of the exact ESP-WROOM-32 38-pin board (or exact-revision pinout) to close T-103.
- Owner: flash the CI-built image, return boot serial log and run the read-only heap/GC/filesystem diagnostic for T-107.
- Build environment: provide Flutter/Dart SDK to implement and verify T-113.
- Asset review: expose PNG and ZIP/model contents for visual/archive inspection; then rename content-based and update references.
- Continue in `TASKS.md` order. Do not bypass dependencies or Phase 1 gate.
