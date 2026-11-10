# DemonCore — North Star

**Purpose:** build one secure, resource-bounded platform for provisioning, controlling, programming and operating ESP32 devices as a coordinated fleet.

This file defines the destination, not a claim that every feature already exists. Implementation status and acceptance evidence live in [TASKS.md](TASKS.md) and [PROGRESS.md](PROGRESS.md).

## The product

DemonCore is three cooperating products joined by the versioned **DemonCore Protocol (DCP)**:

1. **ESP32 device firmware** — MicroPython firmware for the ESP-WROOM-32 38-pin board, 4 MB flash and no PSRAM. It boots a small asyncio runtime, enforces pin safety, stores identity, authenticates commands, runs authorised jobs and supports recoverable updates. Delivery target: one merged flashable `.bin`.
2. **DemonCore control app** — Flutter Android app for provisioning/claiming, fleet and device views, GPIO, logs, rules/jobs and OTA. All device communication goes through one `NodeLink` interface with transport adapters.
3. **DemonCore Hub** — self-hosted control plane providing MQTT, device registry, REST/WebSocket APIs, job scheduling, OTA hosting, roles and audit records.

A simulator supports development, integration and scale tests. It is not a substitute for physical-board acceptance.

## North-star experience

The owner flashes a new ESP32 over USB, discovers and claims it in the app, assigns its unique numeric identity, and sees it in the fleet. The owner safely inspects/controls GPIO, groups devices into sites/cells, runs authorised jobs across selected nodes, monitors live state and updates firmware with staged rollout and rollback. Device rules and authorised jobs continue when the app is closed; the hub coordinates fleet work and records actions.

## Non-negotiable constraints

- **Hardware:** ESP-WROOM-32, 38-pin board, 4 MiB flash, no PSRAM. Never assume an unverified board revision or physical pin mapping.
- **Flash layout:** Profile A is two 1,600 KiB OTA slots, 16 KiB NVS and 832 KiB filesystem. Preserve at least 10% OTA-slot spare.
- **Runtime:** more than 60 KiB free heap after boot with one transport active; at least 20 KiB GC headroom; at least 25% filesystem free. Measure on real hardware.
- **Pin safety:** GPIO 6–11 blocked; strapping pins warned; GPIO 1/3 reserved for console; GPIO 34/35/36/39 input-only; ADC2 unavailable while Wi-Fi is active. The board profile is authoritative.
- **Identity:** unique numeric node ID and per-device secret. Domain key remains outside the repository and never reaches a node.
- **Trust:** unclaimed nodes expose no normal operations. Claimed nodes reject unauthenticated messages. Use established crypto libraries; never invent cryptography or add debug bypasses.
- **Protocol:** firmware, app, hub and simulator share versioned DCP definitions, schemas and test vectors.
- **Safety:** staged OTA, integrity checks and rollback. No irreversible hardware security action without explicit owner approval.
- **Licensing:** preserve the existing Apache-2.0 licence. Third-party code and 3D assets need documented redistribution rights before release.

## Required capabilities at completion

- BLE claim/local control; Wi-Fi station reconnect and setup AP; WebSocket/HTTP DCP; LAN discovery.
- MQTT hub connectivity and ESP-NOW cells with authentication, bounded peers, fragmentation and relay limits.
- Safe GPIO/peripheral HAL, watchdog, recovery/safe mode, resource accounting and optional on-demand plugins.
- Timed claim and owner-controlled release/transfer; HMAC authentication with counters, replay/tamper/wrong-key rejection and lockout.
- AES-CTR + HMAC encrypted frames with documented nonce and directional-key rules.
- Node/group/tag/site/cell selectors; bounded mesh relay and cell leader election.
- Snapshot/delta telemetry with subscription-based delivery and rate limits.
- On-device rules and authorised jobs with resource caps, timeouts, cancellation and results.
- Hub canary/wave scheduling, per-node progress, stop/retry and audit history.
- App provisioning, fleet, node detail, GPIO board, console/logs, jobs/rules, OTA, roles/audit, 3D board, replay and fleet heat map.
- One documented setup path for app, firmware build/flash and self-hosted hub.

## Five-step completion pathway

| Step | Destination | Exit gate |
|---|---|---|
| 1. Foundation | Repository, DCP, board safety, firmware core, identity, build/flash, simulator and app skeleton | Real board boots; memory report; app talks to simulator and board; three-board provisioning |
| 2. Secure control | BLE/Wi-Fi, claim, authentication/encryption, safe GPIO/peripherals, app control and recovery | Real encrypted pin control; unsafe writes blocked; replay/tamper rejected |
| 3. Fleet platform | MQTT, hub, ESP-NOW cells/mesh, selectors, telemetry, rules, file OTA and 3D v1 | Cell works without app; hub manages fleet; file OTA rollback and live 3D proven |
| 4. Jobs and extensions | Job runtime/distribution/scheduler, map-reduce, image OTA, plugins, roles, builders and SDK | Fleet jobs; bad update rolls back; plugin budgets and roles enforced |
| 5. Release hardening | Key lifecycle, hardware-lock decision, optional signatures, integrations, docs and release CI | Release candidate passes security, protocol, scale, rollback and hardware acceptance |

A step is not complete because code compiles. Its documented exit gate must pass, including all `[HUMAN]` checks. Stop at each gate and report evidence before moving on.

## Current reality (2026-11-10)

- DCP v1 contract, firmware core baseline, codec, simulator and CI-built merged ESP32 image exist.
- Latest recorded CI image has 12.57% OTA-slot spare and passes configured build/test checks.
- Physical ESP32 boot, post-boot heap, GC headroom and filesystem measurements remain unverified.
- Exact physical 38-pin header mapping is not owner-confirmed.
- DemonCore BLE/Wi-Fi adapters, identity/claim, GPIO HAL, Flutter app and hub implementations are not complete. Platform BLE/Wi-Fi support in MicroPython is not the same as working DemonCore transports.
- **Phase 1 is not accepted**; later phases remain gated.

## Document hierarchy

- `NORTH_STAR.md` — destination and non-negotiable constraints.
- `AGENTS.md` — contributor/agent workflow and safety rules.
- `TASKS.md` — ordered implementation backlog and acceptance criteria.
- `PROGRESS.md` — dated evidence, blockers and next hand-off.
- `docs/PLAN.md` — detailed architecture.

If documents conflict, stop, reconcile them and record the decision. Never convert an assumption into a requirement or a planned feature into a completed feature.
