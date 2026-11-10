# DemonCore

**One platform. Three parts. One protocol.** Secure ESP32 firmware, a Flutter control app and a self-hosted fleet hub, connected by the DemonCore Protocol (DCP).

> **Status — 10 November 2026:** Foundation work is underway. The CI-built ESP32 image meets the OTA-slot margin (12.57%), but Phase 1 is **not hardware-accepted**. Physical boot/resource checks, board pinout confirmation, app implementation and device identity/claim remain outstanding.

## Start here — choose your workspace

| Work area | Enter this directory | What belongs there |
|---|---|---|
| **ESP32 firmware builder** | [`firmware/`](firmware/README.md) | MicroPython core, board profile, plugins, partitions and build |
| **Build the flashable firmware BIN** | [`firmware/build/`](firmware/build/README.md) | Pinned builder, merged image and OTA-size report |
| **Android control app builder** | [`app/`](app/README.md) | Flutter UI, `NodeLink`, BLE/WebSocket/MQTT adapters and tests |
| **Self-hosted fleet hub** | [`hub/`](hub/README.md) | Broker, registry, APIs, scheduler, OTA and deployment |
| **Shared device/app protocol** | [`protocol/`](protocol/README.md) | DCP spec, schema, operations and vectors |
| **Simulator and developer tools** | [`tools/`](tools/README.md) | Host simulator, pin validator and developer utilities |
| **Project documentation** | [`docs/`](docs/README.md) | Architecture, setup, hardware and audit |
| **3D board/source assets** | [`Assets/`](Assets/) | Supplied models and images; see the asset audit |

**Directory rule:** `app/` is the Flutter app-builder workspace; `firmware/` is the ESP32 firmware workspace. They are separate products. At this commit, `app/` is documentation-only—there is no Flutter `pubspec.yaml` or Dart app yet, so no APK can be built from it.

## Project action cards

These cards reflect the task backlog, not aspirational percentages.

| Phase | Status | Progress / next action |
|---|---|---|
| **1 — Foundation** | **BLOCKED** | 5/13 tasks marked done. Confirm board labels, complete hardware acceptance and unblock app/identity work. [Phase 1](TASKS.md#phase-1--foundation) |
| **2 — Secure control** | **QUEUED** | 0/9 started. Begins only after Gate 1 passes. [Phase 2](TASKS.md#phase-2--core-control-and-security) |
| **3 — Fleet platform** | **QUEUED** | 0/11 started: hub, MQTT, ESP-NOW, mesh, rules, file OTA and 3D. [Phase 3](TASKS.md#phase-3--fleet-mesh-hub-and-first-3d-view) |
| **4 — Jobs and extensions** | **QUEUED** | 0/11 started: jobs, distribution, scheduler, image OTA, plugins, roles and SDK. [Phase 4](TASKS.md#phase-4--jobs-image-ota-plugins-and-developer-tools) |
| **5 — Release hardening** | **QUEUED** | 0/6 started: security, integrations, final docs and release pipeline. [Phase 5](TASKS.md#phase-5--hardening-and-release) |

## Five-step completion pathway

1. **Foundation:** DCP, board safety, firmware baseline, identity/provisioning, reproducible build/flash, simulator and app shell.
2. **Secure control:** claim, BLE/Wi-Fi, authentication/encryption, GPIO/peripherals, app controls and recovery.
3. **Fleet platform:** hub/MQTT, ESP-NOW cells/mesh, selectors, telemetry, rules, file OTA and live 3D board.
4. **Jobs and extensions:** authorised jobs, chunked distribution, canary/wave scheduling, map-reduce, image OTA, plugins, roles and SDK.
5. **Release hardening:** key lifecycle, owner-approved hardware security decisions, integrations, release documentation and full CI/hardware acceptance.

Each step has a gate. Do not skip a blocked gate or count simulator/CI evidence as physical hardware evidence.

## Current verified build

- Target: ESP-WROOM-32, 38-pin, 4 MiB flash, no PSRAM.
- Latest recorded merged image: 1,493,872 bytes.
- OTA slot: 1,638,400 bytes; spare: 205,968 bytes (**12.57%**, above the 10% minimum).
- Latest recorded CI: lint, MicroPython unix-port build, 9 core tests, ESP32 merged build and Profile A checks passed.
- Flash offset: `0x1000`.
- **Not yet verified:** physical boot, free heap (>60 KiB target), GC headroom (>=20 KiB), filesystem free space (>=25%) and live transport operation.

See [firmware build status](firmware/build/README.md) before flashing. A CI-built binary is not a hardware-accepted release.

## Source of truth

1. [North Star](NORTH_STAR.md)
2. [Working rules](AGENTS.md)
3. [Task backlog](TASKS.md)
4. [Progress log](PROGRESS.md)
5. [Architecture plan](docs/PLAN.md)
6. [Repository audit](docs/REPO_AUDIT.md)

## Licence

Apache-2.0. Preserve the existing [LICENSE](LICENSE). Do not add third-party models, libraries or assets without recording their licences.
