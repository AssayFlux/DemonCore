# DemonCore — Agent Working Rules

This file is the working contract for every contributor and AI session. Read it at the start of every session, then read the last five entries of `PROGRESS.md` and all of `TASKS.md`. If this file conflicts with `docs/PLAN.md`, stop and ask the owner.

## Product

DemonCore is three cooperating products sharing the DemonCore Protocol (DCP): ESP-WROOM-32 firmware (4 MB flash, no PSRAM), a Flutter Android control app, and a self-hosted fleet hub. The simulator is host-side development/test tooling, not a fourth product. The firmware ships as one merged MicroPython `.bin` with the core frozen in. Target scale is 10,000 nodes. Core priorities: owner-issued numeric identity and password; owner-key-authenticated communication after claim; authorised code jobs to nodes/groups/cells; OTA after initial USB flash; live 3D pin board; fit within 4 MB flash and approximately 100 KB free RAM.

The master plan is `docs/PLAN.md`. The ordered implementation backlog is `TASKS.md`.

## Workflow — mandatory

1. Work on exactly one task at a time. Select the first `todo` task whose dependencies are all `done`. Do not start another until the current task is `done` or `blocked`.
2. Before coding, write a three-line restatement at the top of the work log entry: goal, complete “Done when” list, and files to touch.
3. Touch only paths named by that task's `Touch` line. Park unrelated ideas under `## Ideas parked` in `TASKS.md`; do not implement them.
4. Make the smallest change that satisfies the task. No unrelated features or refactors.
5. A task is `done` only when every acceptance item is met and the exact `Verify` step has run with output recorded in `PROGRESS.md`. If verification cannot run, mark `blocked`.
6. Log every task using the template in `PROGRESS.md`; commit task work as `T-123: short title`.
7. Stop and ask the owner when hardware facts are unknown; a task requires a physical board, USB cable or phone ([HUMAN]); a security/key/protocol decision is undocumented; an action is irreversible; or work exceeds its size estimate by more than 2x.
8. Never invent pin numbers, APIs, ESP-IDF options, package names or versions. Verify against repository code or authoritative documentation, or ask.
9. Record durable findings in `PROGRESS.md` for the next session.

## Hardware invariants

Target: ESP-WROOM-32 38-pin board.
- GPIO 6–11 are flash pins: never expose or drive.
- GPIO 0, 2, 5, 12, 15 are strapping pins: warn before use; GPIO 12 must be low at boot.
- GPIO 1 and 3 are USB console: reserved.
- GPIO 34, 35, 36, 39 are input-only: no output and no pull-up.
- ADC2 is unavailable while Wi-Fi is active; prefer ADC1 (GPIO 32–39).
- Pin classifications must be read from `firmware/boards/esp32-wroom-38pin.json`; do not hard-code pin lists.

## Resource budgets

Measure using `gc.mem_free()` and the build report.
- Free heap after boot with one transport active: greater than 60 KB.
- Garbage-collection headroom: at least 20 KB.
- Firmware image must fit its OTA slot with 10% spare.
- Filesystem must retain at least 25% free space.
- Each module needs a header comment stating flash/RAM cost and a test measuring it.
- No new dependency without its flash/RAM cost in the PR or commit message.

## Security invariants

- Never commit, log or print secrets, keys, passwords or tokens. Test vectors use clearly fake keys.
- No home-made cryptography. Firmware uses `cryptolib`, `hashlib`, `hmac`; app/hub use established libraries.
- A claimed node drops every message without a valid authentication tag. No debug bypasses, even temporarily.
- The domain key never goes onto a node.
- Never burn eFuses, enable flash encryption or secure boot. These are owner decisions tracked by T-502.

## Protocol change order

For every new operation: (1) update `protocol/ops.json` and `protocol/dcp.md`; (2) add vectors; (3) implement firmware; (4) implement app or hub; (5) make both implementations pass the same vectors. DCP messages carry a version. Never change an existing field's meaning; add a field and bump the minor version.

## Repository layout

```
firmware/   ESP32 MicroPython firmware; enter firmware/build/ to build the merged BIN
app/        Flutter Android app builder; all app source, UI and tests live here
hub/        self-hosted control plane: broker, registry, APIs, scheduler and OTA
protocol/   shared DCP spec, schemas, operations and vectors
tools/      host-side simulator, pin validator and developer/flash/provision tools
Assets/     supplied board models/images; inspect content and licence before use
web-flasher/ browser-based firmware flasher
docs/       North Star references, architecture, setup, pin and release guides
```

Each top-level project folder and meaningful subfolder gets a short README explaining its purpose once created.

## Firmware rules (MicroPython)

- Use `asyncio`; no blocking sleep or busy loops in the main task.
- Preallocate buffers (`bytearray`, `memoryview`); avoid large temporary strings/lists in loops; use `micropython.const`.
- Call `gc.collect()` at defined lifecycle points (after plugin load and job completion), not arbitrarily.
- Handle all I/O errors. Transport failure must not crash the node; reconnect with backoff.
- Feed the watchdog only from the main loop.
- Batch flash writes; never write a file for every event.
- Load plugins on demand and release them when idle.

## App and hub rules

- App has one `NodeLink` interface with BLE, WebSocket and MQTT adapters. UI never talks to transports directly.
- Virtualise node lists; subscribe only to live data for nodes on screen.
- Hub configuration is code (Docker Compose); README must eliminate undocumented manual setup.
- Every network call has a timeout and a visible error state.

## Required checks

| Layer | Check |
|---|---|
| Protocol | Schema validates vectors; firmware and app pass the same vectors |
| Firmware logic | MicroPython unix-port unit tests in CI |
| Firmware hardware | Checklist in `firmware/TESTING.md` ([HUMAN]) |
| App | `flutter analyze` and `flutter test` |
| Hub | Integration test against simulator |
| Scale | Hundreds of fake nodes for mesh, jobs or OTA changes |
| Memory | Build report: image size, slot headroom, post-boot free heap |

If a check cannot run in the current environment, state why in `PROGRESS.md` and mark the task `blocked`.

## Definition of done

- Every task acceptance item is true.
- Its Verify step ran and output is recorded in `PROGRESS.md`.
- Tests are added/updated; lint and tests pass.
- Firmware memory report is updated when firmware changes.
- Docs are updated for behaviour, protocol or setup changes.
- No secrets, debug bypasses or out-of-scope files.
- `TASKS.md` status updated, progress logged and commit made.

## Session start

1. Read this file, the last five `PROGRESS.md` entries, and `TASKS.md`.
2. Run the baseline test suite. If red, treat fixing it as task zero.
3. Select the first eligible task and restate it in the work log.
4. Work, verify, log and commit.
5. Leave `PROGRESS.md` ready for the next session.


## Workspace navigation and asset handling

- Firmware work belongs under `firmware/`; the merged ESP32 image builder is `firmware/build/build.sh`.
- Flutter app work belongs under `app/`. Do not put app code under `firmware/` or host utilities under the app.
- Hub work belongs under `hub/`; shared wire contracts belong under `protocol/`.
- Before renaming or deleting any asset, inspect its actual contents, identify every reference, and verify its licence. A filename or extension alone is not enough evidence.
- The root `NORTH_STAR.md` defines the destination; `TASKS.md` defines the implementation order.
