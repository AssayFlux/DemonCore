# DemonCore — Task Backlog

Follow the rules in `AGENTS.md`. Work strictly top to bottom: select the first `todo` task whose dependencies are all `done`. One task at a time. `[HUMAN]` means a person with the required board/phone must perform or confirm the step; write exact steps and wait.

Statuses: `todo`, `doing`, `done`, `blocked`.

## Phase 1 — Foundation

Goal: repository, protocol, pin safety, firmware core, identity, build/flash pipeline, simulator and app skeleton.

### T-101 Repo skeleton and CI
- Status: done | Size: S | Depends: none
- Touch: repo root, `.github/workflows/`, `docs/`, `firmware/`, `app/`, `hub/`, `protocol/`, `tools/`, `web-flasher/`
- Done when: required folders from AGENTS.md exist with short READMEs; `.gitignore` covers build output and secrets; CI runs a lint check on every push; the existing Apache-2.0 LICENSE is preserved until the owner confirms whether it is intentional; `docs/PLAN.md` contains the master plan.
- Verify: push directly to `main` and observe CI pass.

### T-102 DCP v1 specification
- Status: done | Size: M | Depends: T-101
- Touch: `protocol/`
- Done when: `dcp.md` defines fields `v,id,src,dst,t,op,args`, types `req,res,evt`, errors, node/group/tag/cell/`*` addressing, size limits and fragmentation; JSON schema validates messages; `ops.json` defines `sys.info,sys.ping,gpio.mode,gpio.read,gpio.write` with types/ranges/units; at least 20 valid and 10 invalid vectors exist.
- Verify: tool validates every vector against schema and fails on mismatch.

### T-103 Board profile and pin validator
- Status: blocked | Size: S | Depends: T-101
- Touch: `firmware/boards/`, `tools/`
- Done when: `esp32-wroom-38pin.json` encodes blocked, strapping, console, input-only, ADC1, ADC2, DAC and general classes; validator returns allow/warn/block with reason for mode/write/pwm/adc; tests cover each class.
- Verify: unit tests; [HUMAN] owner checks pin labels against real board photo/silkscreen and records differences.

### T-104 Firmware core skeleton
- Status: blocked | Size: M | Depends: T-101
- Touch: `firmware/core/`, `firmware/tests/`
- Done when: `boot.py` and `main.py` start an asyncio scheduler; JSON config defaults; log ring buffer; main-loop-only watchdog; crash counter enters safe mode after 3 consecutive crashes; unix-port compatible.
- Verify: unix-port unit tests in CI.

### T-105 DCP codec in firmware
- Status: todo | Size: M | Depends: T-102, T-104
- Touch: `firmware/core/dcp.py`, `firmware/tests/`
- Done when: encode/decode/routing/error replies work; all protocol vectors pass; RAM measurement script reports codec cost.
- Verify: CI vector tests; record RAM in PROGRESS.md.

### T-106 HAL for GPIO with pin enforcement
- Status: todo | Size: M | Depends: T-103, T-105
- Touch: `firmware/core/hal/`, `firmware/tests/`
- Done when: `gpio.mode/read/write` work through DCP; all calls pass pin validator; blocked pins error; warned pins require `confirm`.
- Verify: fake-machine unit tests; [HUMAN] toggle LED pin on real board over USB serial.

### T-107 Build pipeline and memory report
- Status: todo | Size: L | Depends: T-104
- Touch: `firmware/vendor/`, `firmware/manifest.py`, `firmware/partitions.csv`, `firmware/build/`, CI
- Done when: pinned MicroPython ESP32_GENERIC source/binary, version and SHA256 recorded; manifest freezes core; partitions implement Profile A (two 1,600 KB slots, 16 KB NVS, 832 KB filesystem); build emits merged `demoncore-esp32-merged.bin` and `build/report.md` with image size, slot headroom and post-boot free heap. If image misses 10% spare, report actual sizes and stop.
- Verify: CI/documented-container build and report; [HUMAN] boot real board (see T-108).

### T-108 Flash tools
- Status: todo | Size: M | Depends: T-107
- Touch: `tools/flash.py`, `web-flasher/`, `docs/`
- Done when: CLI flashes merged image with esptool and checks result; web flasher flashes same image from Chrome/Edge; docs give both paths and exact offset.
- Verify: [HUMAN] flash real ESP-WROOM-32 by both paths, open serial console, confirm boot log and `sys.info` reply.

### T-109 Simulator node
- Status: todo | Size: M | Depends: T-102
- Touch: `tools/sim_node.py`, `tests/`
- Done when: simulator speaks DCP over WebSocket and implements sys.info, sys.ping, gpio.* with same pin rules; `--count N` starts distinct-ID nodes.
- Verify: vectors pass against simulator; start 100 nodes and query all.

### T-110 Identity storage
- Status: todo | Size: M | Depends: T-104
- Touch: `firmware/core/identity.py`, `firmware/tests/`
- Done when: node ID, device secret, cell key and counters stored in NVS; secrets never logged/printed; claimed flag controls behaviour; tests cover read/write/tamper/wipe.
- Verify: fake-NVS tests and assertion that no secret appears in log buffer.

### T-111 Claim state machine
- Status: todo | Size: L | Depends: T-110, T-105
- Touch: `firmware/core/claim.py`, `firmware/core/transport/ble.py`, `firmware/tests/`
- Done when: unclaimed/claim_window/claimed follow plan §14; BOOT opens timed window; BLE pairing-code claim stores ID, secret, cell key, name and reboots; unclaimed node answers nothing else; claimed node cannot reopen window without owner-signed release.
- Verify: transition/timeout tests; [HUMAN] claim real board from phone client and verify persistence over reboot.

### T-112 Provisioning tool
- Status: todo | Size: M | Depends: T-110
- Touch: `tools/provision.py`, `tools/tests/`
- Done when: CSV node IDs; device secret derived as HMAC-SHA256(domain key, node ID); NVS image built; flashed with firmware; label file (ID, QR) and registry export written; domain key read from outside repo and never printed.
- Verify: fake-domain-key tests; [HUMAN] provision 3 boards and confirm unique claimed IDs.

### T-113 App skeleton
- Status: todo | Size: M | Depends: T-109
- Touch: `app/`
- Done when: Flutter project builds; NodeLink interface and WebSocket adapter; Fleet lists simulator nodes and detail view shows sys.info.
- Verify: flutter analyze/test and app against 100 simulated nodes without lag.

**Gate 1:** merged image boots on real board; app talks to simulator and one real board; provisioning works on 3 boards; memory report committed. Stop and report to owner before Phase 2.

## Phase 2 — Core control and security

Goal: authenticated/encrypted pin operations over BLE and Wi-Fi and app control screens.

### T-201 BLE transport
- Status: todo | Size: L | Depends: Gate 1
- Touch: `firmware/core/transport/ble.py`, `tests/`
- Done when: GATT command/response/event characteristics; chunking to negotiated MTU; timeout reassembly; BLE configurable off to save RAM.
- Verify: chunk tests; [HUMAN] phone sends 2 KB message.

### T-202 Wi-Fi transport
- Status: todo | Size: L | Depends: Gate 1
- Touch: `firmware/core/transport/wifi.py`, `tests/`
- Done when: station reconnect/backoff; fallback setup AP; WebSocket/HTTP DCP endpoints; mDNS if supported, otherwise UDP announce.
- Verify: unit tests and real-network app integration.

### T-203 Authentication layer
- Status: todo | Size: L | Depends: T-110, T-105
- Touch: `firmware/core/auth.py`, `app/lib/security/`, `protocol/`
- Done when: every post-claim message has HMAC-SHA256 tag and counter; replay/bad tags dropped; repeated failures lock source out with growing delay; shared app/firmware vectors.
- Verify: valid/replay/tampered/wrong-key vectors pass both sides.

### T-204 Encrypted frames
- Status: todo | Size: M | Depends: T-203
- Touch: `firmware/core/crypto.py`, `app/lib/security/`
- Done when: AES-CTR plus HMAC for all transports; nonce rules documented; no directional key reuse.
- Verify: cross-implementation vectors; identical plaintexts yield different ciphertexts.

### T-205 Peripheral ops
- Status: todo | Size: L | Depends: T-106
- Touch: `firmware/core/hal/`, `protocol/ops.json`
- Done when: pwm.set, adc.read, dac.write, touch.read, i2c.scan/read/write, spi.xfer, uart.open/read/write exist with pin validation and argument ranges.
- Verify: fake-based tests; [HUMAN] PWM LED, read ADC1 and scan I2C.

### T-206 App BLE link and claim screen
- Status: todo | Size: L | Depends: T-111, T-113
- Touch: `app/`
- Done when: scan/unclaimed list, button/pairing guidance, ID assignment, secret derivation, claim send, node appears in fleet.
- Verify: [HUMAN] end-to-end real-board claim.

### T-207 Device screen with pin board
- Status: todo | Size: M | Depends: T-205, T-113
- Touch: `app/`
- Done when: 38-pin layout shows mode/level; tap reads/sets; unsafe actions confirm using node manifest pin map.
- Verify: widget tests and simulator.

### T-208 Console and logs
- Status: todo | Size: M | Depends: T-202, T-113
- Touch: `firmware/core/sys/log.py`, `app/`
- Done when: streamed logs with level filter, subscribe/unsubscribe, no secrets.
- Verify: grep stream for secret patterns; none found.

### T-209 Recovery and safe mode
- Status: todo | Size: M | Depends: T-104
- Touch: `firmware/core/`
- Done when: BOOT held 5 seconds enters safe mode (transports/OTA only, user code off); keys/identity preserved; reset reason in sys.info.
- Verify: [HUMAN] induce crash loop and verify recovery.

**Gate 2:** real hardware pin ops work encrypted; unsafe writes blocked; replay/tamper rejected; app claims and controls a real board. Report to owner.

## Phase 3 — Fleet, mesh, hub and first 3D view

Goal: cells, ESP-NOW, MQTT, hub, rules, file OTA and 3D board v1.

### T-301 MQTT transport
- Status: todo | Size: M | Depends: Gate 2
- Touch: `firmware/core/transport/mqtt.py`
- Done when: broker connection with TLS when configured; per-node topics; last-will; reconnect/backoff.
- Verify: tests against hub broker in CI.

### T-302 Hub first version
- Status: todo | Size: L | Depends: T-301
- Touch: `hub/`
- Done when: docker compose starts broker, registry, REST/WS API; registry stores node ID/hardware/claim/cell/tags/last-seen; keys encrypted; exact README setup.
- Verify: 100-node simulator integration.

### T-303 ESP-NOW transport and peer table
- Status: todo | Size: L | Depends: Gate 2
- Touch: `firmware/core/transport/espnow.py`
- Done when: DCP frames up to 250 bytes, fragmentation/reassembly, bounded peer table, configured fixed channel, cell-key authentication.
- Verify: [HUMAN] two boards exchange commands without router.

### T-304 Relay with TTL and dedup
- Status: todo | Size: M | Depends: T-303
- Touch: `firmware/core/mesh.py`
- Done when: hop count, message-ID duplicate cache, hop limit 3, random delay to avoid storms.
- Verify: simulator proves no loops and bounded traffic.

### T-305 Cell leader election and gateway
- Status: todo | Size: L | Depends: T-304, T-202
- Touch: `firmware/core/cell.py`
- Done when: lowest-ID live node leads; failure triggers re-election; leader bridges ESP-NOW to Wi-Fi/MQTT and reports membership.
- Verify: leader-failure simulator; [HUMAN] three boards.

### T-306 Groups, tags and selectors
- Status: todo | Size: M | Depends: T-302
- Touch: `hub/`, `app/`, `protocol/`
- Done when: selectors (e.g. site/tag/firmware predicates) resolve nodes; bulk commands preview then run in waves with stop.
- Verify: 1,000-node tests.

### T-307 Telemetry and pin events
- Status: todo | Size: M | Depends: T-205, T-302
- Touch: `firmware/core/`, `hub/`, `protocol/`
- Done when: pin.snapshot on subscribe, pin.delta on change, max 10/sec/node; stop when no subscribers; hub caches latest state.
- Verify: rate-limit/unsubscribe tests.

### T-308 On-device rules engine
- Status: todo | Size: L | Depends: T-307
- Touch: `firmware/core/rules/`
- Done when: JSON rules for pin change, threshold, timer, message and boot; run without app; RAM within budget.
- Verify: unit tests, memory report; [HUMAN] button on A switches relay on B.

### T-309 File OTA with rollback
- Status: todo | Size: L | Depends: T-203
- Touch: `firmware/core/ota/`, `tools/ota_push.py`, `hub/`
- Done when: signed file packages (device-secret tag over package hash); stage/verify/swap; retain old file; interrupted update leaves node working.
- Verify: simulator cuts power/connection at every step.

### T-310 3D board view v1
- Status: todo | Size: L | Depends: T-307, T-207
- Touch: `app/`, `app/assets/`
- Done when: licensed/owner-made glTF 38-pin board, named part per pin, live pin.delta colour/glow, tap action, subscribe only to open node; licence recorded.
- Verify: smooth frame rate on owner's phone [HUMAN].

### T-311 Scale test with simulated cells
- Status: todo | Size: M | Depends: T-305, T-302
- Touch: `tools/`, `tests/`
- Done when: 500 simulated nodes in 10+ leader cells connect; leader failure/rejoin tested; hub CPU/RAM recorded.
- Verify: report in `docs/scale-test.md`.

**Gate 3:** real nodes control each other over ESP-NOW without app; hub manages simulated fleet; file OTA rollback proven; live 3D view. Report to owner.

## Phase 4 — Jobs, image OTA, plugins and developer tools

Goal: shared jobs, safe code delivery and extensibility.

### T-401 Job package format and signer
- Status: todo | Size: M | Depends: Gate 3
- Touch: `protocol/`, `tools/`, `hub/`
- Done when: manifest schema (ID/version/selector/resources/schedule/timeout/retry), mpy-cross build, content hash and per-node authorisation tag.
- Verify: schema and tests.

### T-402 Job runtime on node
- Status: todo | Size: L | Depends: T-401, T-308
- Touch: `firmware/core/jobs/`
- Done when: asyncio jobs with RAM cap/time slice/stop; manifest-scoped pins/plugins; failures reported without crashing node; API dc.gpio/send/on/result.
- Verify: memory-leaking, infinite-loop and blocked-pin job tests.

### T-403 Chunked distribution
- Status: todo | Size: L | Depends: T-402, T-304
- Touch: `firmware/core/jobs/dist.py`, `hub/`
- Done when: leader fetches once, distributes numbered chunks; nodes request missing chunks/pull from neighbours; hash/tag verified before content-addressed storage.
- Verify: 500 nodes, 10% packet loss, all verified.

### T-404 Scheduler with waves and canary
- Status: todo | Size: L | Depends: T-403
- Touch: `hub/`
- Done when: selector, canary, waves, stop, retry/reassign on missed heartbeats; per-node ready/running/finished/failed/reason.
- Verify: failure-injected integration test.

### T-405 Map and reduce
- Status: todo | Size: L | Depends: T-404
- Touch: `firmware/core/jobs/`, `hub/`
- Done when: leaders combine partial results; results include job/node/version/sequence; duplicates and gaps detected.
- Verify: 500-node sum with lost/repeated messages equals expected.

### T-406 Image OTA with auto-rollback
- Status: todo | Size: L | Depends: T-309, T-107
- Touch: `firmware/core/ota/image.py`, `hub/`
- Done when: stream to inactive slot, hash check, switch slot, confirm boot or rollback; staged hub rollout.
- Verify: [HUMAN] real update and deliberately broken image rollback.

### T-407 Plugin registry
- Status: todo | Size: M | Depends: T-309
- Touch: `firmware/plugins/`, `hub/`, `app/`
- Done when: manifest lists ops/pins/flash/RAM/licence; app install/remove; refuse if resource budget fails; first plugins NeoPixel, DHT, DS18B20, SSD1306, servo.
- Verify: fit tests; [HUMAN] one real sensor.

### T-408 Roles and audit log
- Status: todo | Size: M | Depends: T-302
- Touch: `hub/`, `app/`
- Done when: owner/admin/developer/operator/viewer roles scoped by site/tag; raw code/files/REPL admin-only; jobs/key changes/updates logged with actor/time.
- Verify: permission tests per role.

### T-409 Dashboard and rule builders
- Status: todo | Size: L | Depends: T-308, T-306
- Touch: `app/`
- Done when: JSON switch/slider/gauge/chart/log widgets bind to ops; visual rule builder emits T-308 JSON and supports test.
- Verify: widget tests and export/import round trip.

### T-410 SDK and dcctl
- Status: todo | Size: M | Depends: T-404
- Touch: `tools/dcctl/`, `tools/sdk/`
- Done when: Python SDK and CLI list nodes, run job, watch progress and push update via hub API.
- Verify: simulator/hub tests.

### T-411 3D replay and fleet heat map
- Status: todo | Size: M | Depends: T-310
- Touch: `app/`, `hub/`
- Done when: time slider replays recent pin activity; fleet view colours nodes by signal; only visible nodes subscribed.
- Verify: 1,000-node tests.

**Gate 4:** job across real cell and large simulated fleet; bad update auto-rolls back; plugin fit checks; roles enforced. Report to owner.

## Phase 5 — Hardening and release

### T-501 Key rotation, release and transfer
- Status: todo | Size: L | Depends: Gate 4
- Touch: `firmware/core/`, `hub/`, `app/`
- Done when: cell-key rotation without node loss; owner-signed release to unclaimed; owner transfer; lost-key behaviour documented.
- Verify: simulator and [HUMAN] real board.

### T-502 Hardware lock decision [HUMAN]
- Status: todo | Size: S | Depends: Gate 4
- Touch: `docs/hardware-lock.md`
- Done when: explain flash encryption, secure boot, download disable, effects on owner's wired reflashing, irreversible fuses, and tested procedure on sacrificial board. Agent writes document then stops; owner decides. Agent must never burn eFuses.
- Verify: owner approval recorded in PROGRESS.md.

### T-503 Optional asymmetric signatures
- Status: todo | Size: L | Depends: Gate 4
- Touch: `firmware/native/`, `hub/`
- Done when: native mbedtls ECDSA P-256 verification; packages signed without per-node tags; flash/RAM costs recorded.
- Verify: cross-vectors and build report.

### T-504 Other board profiles
- Status: todo | Size: M | Depends: Gate 4
- Touch: `firmware/boards/`
- Done when: profile format supports other ESP32 chips; add one profile only after owner confirms board.
- Verify: validator tests.

### T-505 Integrations
- Status: todo | Size: M | Depends: T-302
- Touch: `hub/`, `docs/`
- Done when: MQTT topics/webhooks documented; Home Assistant and Node-RED examples.
- Verify: example flows run against simulator.

### T-506 Docs and release pipeline
- Status: todo | Size: M | Depends: T-501
- Touch: `docs/`, `.github/workflows/`
- Done when: setup/pin/plugin/security guides; CI builds merged image, OTA packages and app and attaches checksums to GitHub Release; nodes report firmware/app/protocol versions.
- Verify: tagged release on test branch.

**Gate 5:** release candidate passes protocol vectors, scale, rollback and security tests. Report to owner.

## Ideas parked

- None yet.

## Open questions for the owner

- Re-claiming: hold-button wipe or owner-signed release only?
- Hub hosting: PC/Raspberry Pi or cloud?
- First fleet size/layout: one building, one site or multiple places?
- Who may deploy code besides the owner?
- Hardware locking decision (T-502).
