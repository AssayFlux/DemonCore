# DemonCore — Master Plan

**Status:** Planning baseline, derived from the owner's project brief and task backlog. This document records agreed goals and constraints; it does not silently decide unresolved security, hardware, hosting or licensing questions. Where a detail is not specified, implementation must stop and ask rather than guess.

## 1. Product vision

DemonCore is two products sharing one versioned protocol, DCP:

1. **Device firmware:** MicroPython for the ESP-WROOM-32 38-pin board (4 MB flash, no PSRAM), distributed as one merged `.bin` with the DemonCore core frozen into the image.
2. **Control plane:** Flutter app plus self-hosted hub. The hub comprises an MQTT broker, node registry, job scheduler and OTA server. The target fleet is up to 10,000 nodes.

The system must issue each node a unique numeric ID and password; ensure a claimed node communicates only with apps/nodes proving owner-key possession; allow authorised users to deploy one job to a node, group or cell; support OTA after the first USB flash; provide a live 3D board/pin view; and fit the constrained flash/RAM budget.

Priority order is: identity and ownership; authenticated communication; multi-node jobs; OTA; live 3D visibility; resource fit.

## 2. System boundaries and responsibilities

### Firmware node

- Boots into a small asyncio-based core.
- Stores identity, device secret, cell key and counters in NVS.
- Enforces board pin policy through a data-driven board profile.
- Exposes DCP operations through transport adapters.
- Runs authorised jobs and on-device rules within resource/time limits.
- Supports safe mode, recovery and staged OTA/rollback.
- Loads optional plugins on demand and accounts for their flash/RAM cost.

### Flutter app

- Owns user-facing provisioning, claiming, fleet, device, pin, logs, jobs and OTA workflows.
- Talks through one `NodeLink` abstraction; BLE, WebSocket and MQTT are adapters.
- Never binds UI directly to a transport implementation.
- Virtualises fleet lists and subscribes only to visible/open nodes.
- Presents confirmation for risky pin actions and clear errors/timeouts for network calls.

### Self-hosted hub

- Runs as declared configuration (Docker Compose).
- Provides MQTT broker, registry, REST/WebSocket APIs, job scheduling and OTA hosting.
- Stores node metadata and encrypted key material.
- Resolves selectors, executes canary/wave deployments and records progress/audit events.
- Supports simulator-based integration and scale tests.

### Protocol

- DCP is the shared contract across firmware, app, simulator and hub.
- Message versioning, schemas, operation definitions and shared test vectors are authoritative.
- New operations follow the protocol-first sequence in AGENTS.md.

## 3. Hardware profile and pin safety

Initial target is exactly ESP-WROOM-32 on a 38-pin board, 4 MB flash, no PSRAM. Pin policy is data in `firmware/boards/esp32-wroom-38pin.json`, not duplicated in code.

| Pin class | Rule |
|---|---|
| GPIO 6–11 | Flash pins; never expose or drive |
| GPIO 0, 2, 5, 12, 15 | Strapping pins; warn before use |
| GPIO 12 | Must be low at boot |
| GPIO 1, 3 | USB console; reserved |
| GPIO 34, 35, 36, 39 | Input-only; no output or pull-up |
| ADC2 | Not usable while Wi-Fi is active |
| ADC1 | Prefer GPIO 32–39 |

Unknown board markings, voltage assumptions, pin mappings or hardware behaviours are owner questions, not implementation guesses.

## 4. Firmware resource model

Hard targets:
- Post-boot free heap with one active transport: greater than 60 KB.
- GC headroom: at least 20 KB.
- Image fits OTA slot with 10% spare.
- Filesystem retains at least 25% free.
- Measure heap using `gc.mem_free()`; report image/slot sizes in build report.
- Each module documents flash and RAM cost and has a measurement test.
- Dependencies require explicit flash/RAM cost disclosure.

Partition Profile A from the owner brief is two 1,600 KB firmware slots, 16 KB NVS and 832 KB filesystem. Validate actual partition-table/tool constraints during T-107; do not assume a build fits.

## 5. Identity, claim and trust model

- App issues each node its unique numeric identity and credentials.
- Provisioning derives per-device secret as HMAC-SHA256(domain key, node ID); domain key remains outside repository and never reaches a node.
- Node claim lifecycle is unclaimed → timed claim window → claimed.
- Unclaimed nodes answer no normal operations.
- Claimed nodes reject every message lacking a valid authentication tag.
- Authentication includes HMAC-SHA256 and counters; replay, tamper and wrong-key cases have shared vectors.
- Repeated authentication failures cause increasing lockout delay.
- AES-CTR plus HMAC is the specified encrypted-frame direction; nonce and directional key rules must be documented and tested before implementation.
- No custom cryptography, debug authentication bypass, secret logging or secret commits.

Unresolved: precise re-claim/release behaviour, key-loss policy, and any hardware security fuses/secure boot. These require owner decisions. Never burn eFuses or enable hardware locks as an autonomous action.

## 6. DCP protocol contract

Every DCP message is versioned and carries fields `v, id, src, dst, t, op, args`. Message types are request, response and event (`req,res,evt`). Addressing supports node, group, tag, cell and wildcard `*`. Error codes, size limits, fragmentation, schema and vectors are defined in Phase 1 T-102.

Initial operations: `sys.info`, `sys.ping`, `gpio.mode`, `gpio.read`, `gpio.write`.

Never change the meaning of an existing field. Add fields and increment the minor protocol version. Protocol changes begin with docs/ops/schema/vectors, then firmware, then app/hub, followed by cross-implementation vector tests.

## 7. Transports and connectivity

Planned adapters:
- BLE for initial claim and local control, with negotiated-MTU chunking and bounded reassembly.
- Wi-Fi station mode with reconnect/backoff, setup AP, WebSocket and HTTP DCP endpoints, and LAN discovery (mDNS if supported, otherwise UDP announce).
- MQTT to the hub, with per-node topics, optional TLS, last-will and reconnect/backoff.
- ESP-NOW for local cell communication, authenticated with cell key, bounded peer table, fragmentation and configured channel.

A transport failure must not crash the node. Transport enablement is configurable where RAM savings are important. Exact library/API availability must be checked against the pinned MicroPython/ESP-IDF version before use.

## 8. Fleet, cells and telemetry

- Nodes may be grouped by group, tag, site and cell selectors.
- ESP-NOW mesh relay uses TTL/hop count, duplicate suppression and hop limit 3.
- Cell leader is the live node with the lowest ID; loss triggers re-election.
- Leader bridges cell traffic to Wi-Fi/MQTT and reports membership.
- Pin state uses snapshot on subscribe and delta on change, capped at 10 events/sec/node.
- Nodes stop telemetry when no client subscribes; hub caches latest state.
- Scale verification grows through 100, 500 and 1,000 simulated nodes, with 10,000 as product target.

## 9. Rules, jobs and plugins

On-device rules are JSON-defined and trigger on pin change, threshold, timer, message or boot. They must run without the app and fit the RAM budget.

Jobs are signed/authorised packages with manifest for ID, version, selector, resources, schedule, timeout and retry. Runtime is asyncio-based, RAM-capped, time-sliced, stoppable and restricted to declared pins/plugins. Job API: `dc.gpio`, `dc.send`, `dc.on`, `dc.result`. Failures are reported without crashing the node.

Distribution uses content hashes, per-node authorisation tags and chunked cell delivery with retry/missing-chunk recovery. Hub scheduler supports canary, waves, stop, retry/reassignment and per-node progress. Map/reduce results include job ID, node ID, version and sequence number.

Plugins declare operations, pins, flash/RAM cost and licence. The initial set is NeoPixel, DHT, DS18B20, SSD1306 and servo. Refuse installation when resource budgets do not fit.

## 10. OTA and recovery

- File OTA packages are signed with a tag derived from the node device secret over package hash.
- Stage, verify, swap and retain old file for rollback.
- Interrupted transfers must leave the node operational.
- Image OTA streams to inactive slot, verifies hash, switches slot and requires boot confirmation; otherwise revert to prior slot.
- Rollouts are staged through hub scheduler.
- Safe mode is entered by holding BOOT for 5 seconds: transports and OTA remain, user code is disabled; identity/keys persist.
- Crash loop safe mode after 3 consecutive crashes; watchdog is fed only by main loop.

All destructive/irreversible operations require explicit owner approval.

## 11. App experience

Planned progression:
1. Fleet list and simulator-backed node details.
2. BLE discovery, claim flow and provisioning.
3. 38-pin device view with pin mode/level and safe read/write controls.
4. Console/log stream with level filters and secret redaction.
5. Job/rule builders, rollout progress, roles and audit log.
6. Live 3D 38-pin board with one named glTF part per pin; only open node subscribed.
7. Replay timeline and fleet heat map.

3D asset must be owner-created or licensed for redistribution; record the licence. Smoothness must be checked on owner's phone.

## 12. Hub, roles and audit

Hub is self-hosted with Docker Compose and documented one-command startup. Registry includes node ID, hardware, claim state, cell, tags and last-seen. Keys are encrypted at rest. Selector expressions resolve nodes. Scheduler supports canary and waves with stop/retry. Roles: owner, admin, developer, operator, viewer, scoped by site/tag. Raw code, files and REPL require admin. Job deployments, key changes and updates are auditable with actor and time.

Hosting location (PC, Raspberry Pi or cloud) remains an owner decision.

## 13. Build, test and release strategy

- Pin MicroPython ESP32_GENERIC source/binary with version and SHA256.
- Freeze firmware core through manifest and produce one merged image.
- Maintain reproducible documented build environment and memory report.
- CLI and browser flashers use same image and documented offset.
- Protocol vectors run across schema, firmware and app.
- Firmware logic tests run on MicroPython unix port.
- App runs flutter analyze/test.
- Hub integration tests use simulator.
- Mesh/jobs/OTA changes include scale simulation.
- Hardware acceptance steps are marked [HUMAN] and wait for owner.
- Release CI builds firmware image, OTA packages and app; publishes checksums and version information.

## 14. Delivery phases and gates

The detailed task-level acceptance criteria and dependencies live in `TASKS.md`.

| Phase | Outcome | Gate |
|---|---|---|
| 1 Foundation | Repo, DCP, pin validator, core, identity, build, flash, simulator, app skeleton | Real board boots; app talks to simulator and board; 3-board provisioning; memory report |
| 2 Control/security | BLE/Wi-Fi, auth/encryption, peripherals, app control, recovery | Real pin ops encrypted; unsafe writes blocked; replay/tamper rejected; app claims/controls board |
| 3 Fleet/mesh/hub/3D | MQTT, hub, ESP-NOW, cells, selectors, telemetry, rules, file OTA, 3D | Real cell works without app; hub manages simulator; OTA rollback and live 3D proven |
| 4 Jobs/extensions | Job runtime/distribution/scheduler, map-reduce, image OTA, plugins, roles, builders, SDK | Real and simulated fleet jobs; rollback; plugin resource checks; roles |
| 5 Hardening/release | Key rotation/transfer, hardware-lock decision, optional signatures, integrations, release docs/CI | Release candidate passes vectors, scale, rollback and security tests |

Stop at each gate and report to the owner before proceeding to the next phase.

## 15. Explicit owner decisions

Do not infer answers to these:
- Licence: repository currently has Apache-2.0 text; confirm whether intentional.
- Re-claiming: physical hold-button wipe or owner-signed release only?
- Hub hosting: PC, Raspberry Pi or cloud?
- First fleet geography and size.
- Who can deploy code besides owner.
- Whether to pursue hardware locking (T-502).
- Any unknown board-specific facts or irreversible security choices.

## 16. Source of truth and change control

The owner's original project brief establishes hard constraints and priorities. `AGENTS.md` defines working rules; `TASKS.md` defines task order, scope, dependencies and acceptance; this plan explains intended architecture. If these documents conflict or a new decision is needed, stop and ask the owner. Record approved decisions in the plan and progress log before implementing them.
