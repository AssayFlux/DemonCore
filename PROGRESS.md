# DemonCore — Progress Log

This file is the durable hand-off between sessions. Read the last five entries at session start. Do not mark a task done without running its Verify command and recording the key output.

## Task log

### Planning bootstrap (2026-11-10) status: done
Goal: establish the project instructions, ordered backlog and master plan from the owner's supplied DemonCore specification before implementation begins.
Changed: `AGENTS.md` (working rules and invariants), `TASKS.md` (phased backlog and acceptance criteria), `docs/PLAN.md` (product and architecture plan), and this `PROGRESS.md` (session hand-off).
Verified: GitHub file creation responses confirmed all four documents were committed to branch `docs/project-charter-and-plan`. No code tests were run; this bootstrap changes documentation only.
Memory: no firmware changed; image size and heap not measured.
Open issues: T-101 implementation has not started. Repository currently contains only a minimal README, a generic Python `.gitignore`, and an Apache-2.0 LICENSE. Owner confirmation is needed before changing the licence. No repository test suite exists yet, so baseline test status is unknown.
Next: T-101 Repo skeleton and CI (first backlog task; dependencies clear). Before coding, restate goal, full Done-when list and Touch paths here. Run baseline checks once the repository skeleton and CI files exist; do not claim CI passes until a branch push produces a passing run.

### T-101 Repo skeleton and CI (2026-11-10) status: blocked
Goal: create the required DemonCore repository skeleton and a push-triggered CI lint check.
Done when: required folders have short READMEs; `.gitignore` covers build output and secrets; CI lints every push; licence disposition is confirmed without changing legal text without approval; `docs/PLAN.md` remains the master plan.
Files: repository root, `.github/workflows/`, `docs/`, `firmware/`, `app/`, `hub/`, `protocol/`, `tools/`, `web-flasher/`.
Changed: added purpose READMEs for all required project folders and firmware subfolders; added `.github/workflows/ci.yml` using `git diff --check HEAD^ HEAD`; extended the original `.gitignore` without removing its existing rules, covering generated firmware artifacts and local secrets; clarified this task's scope and main-only verification in `TASKS.md`.
Baseline: no pre-existing test suite or CI workflow was present, so there were no baseline tests to run.
Verified: both pushes to `main` triggered CI. Run #1 for `0d84a4d93e081783064595bc49217471e3c57238` passed; run #2 for `81be1c4fab074d00026ed5cdb6c06c4e0bc86337` passed. The `Lint changed files` job completed successfully, including `git diff --check HEAD^ HEAD`. Repository tree confirms all requested skeleton READMEs and `.github/workflows/ci.yml` are present.
Blocker: repository already contains a full Apache-2.0 LICENSE, not a placeholder. Preserved it. Owner must confirm whether Apache-2.0 is intentional or specify the desired licence before T-101 can be marked done.
Memory: no firmware code or binaries changed; image size and heap not measured.
Next: ask owner to confirm the licence; once confirmed, close T-101 and proceed to T-102.


### T-101 licence confirmation and closure (2026-11-10) status: done
Goal: close repository foundation after the owner confirms the existing licence.
Done when: required folder READMEs exist; ignore rules cover generated artifacts and secrets; push CI lint passes; Apache-2.0 is explicitly approved and preserved.
Files: `TASKS.md`, `PROGRESS.md`.
Changed: recorded the owner's explicit approval to keep Apache-2.0; changed T-101 from blocked to done. No licence text was altered.
Verified: prior direct-to-main CI runs #1 and #2 passed, including `git diff --check HEAD^ HEAD`; current main head before this closure was `5ffcb45b5798d09151adf2cf045b358f4ba652bb`. Baseline suite: no test suite existed at T-101 start; no additional baseline tests available. This closure is documentation-only.
Memory: no firmware changed; image size and heap not measured.
Next: T-102 DCP v1 specification is the first eligible task. Implement only under `protocol/`, then validate all vectors against the schema.

### T-102 DCP v1 specification (2026-11-10) status: done
Goal: define the shared DCP v1 envelope, addressing, operation contracts, limits, errors and reusable test vectors before any transport implementation.
Done when: `dcp.md` specifies fields `v,id,src,dst,t,op,args`, types `req,res,evt`, error responses, node/group/tag/cell/`*` addressing, limits and transport fragmentation; JSON Schema validates the envelope; `ops.json` defines `sys.info,sys.ping,gpio.mode,gpio.read,gpio.write` with argument/response types and ranges; at least 20 valid and 10 invalid vectors exist.
Files: `protocol/` only (specification, schema, operation catalogue, validator, vectors and README).
Changed: added the normative DCP v1.0 envelope and address grammar; defined 4,096-byte encoded-message and bounded-reassembly limits; documented standard error codes; added Draft 2020-12 JSON Schema, five operation request/response contracts, a host-side vector validator, 23 valid vectors and 12 invalid vectors. Version is represented as `"1.0"`; schema rejects unsupported major versions while allowing compatible v1 minor increments. GPIO argument schema does not replace board-profile pin enforcement.
Baseline: repository had no test suite before T-102; no baseline tests were available.
Verified: ran the validator logic against the committed protocol schema, operation catalogue and vectors in an isolated local mirror. Output: `PASS: 23 valid vectors accepted; 12 invalid vectors rejected; 5 operation schemas loaded.` Exit code: 0. Host test dependency `jsonschema` was present. The test caught and led to a fix rejecting unsupported major version `2.0`.
Memory: no firmware changed; image size and heap not measured.
Next: T-103 Board profile and pin validator is next by backlog order; T-104 Firmware core skeleton is also eligible but T-103 precedes it. T-105 depends on both T-102 and T-104.

### T-103 Board profile and pin validator (2026-11-10) status: blocked
Goal: encode the ESP-WROOM-32 38-pin GPIO safety classes in a data-driven profile and provide a validator that returns allow/warn/block with a reason.
Done when: profile represents blocked, strapping, console, input-only, ADC1, ADC2, DAC and general GPIO classes; validator covers mode/write/PWM/ADC decisions; tests cover each class; owner confirms the physical board labels against a board photo/silkscreen.
Files: `firmware/boards/`, `tools/` only.

Changed: added `firmware/boards/esp32-wroom-38pin.json` with available GPIO identifiers and blocked, strapping, console, input-only, ADC1, ADC2, DAC and general classes; added `tools/validate_pins.py` returning allow/warn/block with a reason for mode/write/PWM/ADC/DAC; added unit tests for each policy class. Profile explicitly distinguishes GPIO identifiers from physical header positions and marks physical mapping unverified.
Verified: ran `python -m unittest discover -s tools/tests -v` in an isolated local mirror of the committed files. Output: 11 tests passed, 0 failures. Covered flash/unavailable GPIO, console, strapping confirmation, input-only restrictions, ADC1 with Wi-Fi, ADC2 with/without Wi-Fi, DAC and general GPIO. No hardware was connected.
Blocker: acceptance requires owner verification of the physical board's 38-pin silkscreen/header mapping. The project context contains no board photo, so physical labels are not guessed. Please provide a clear photo of both sides of the exact ESP-WROOM-32 38-pin board (or a pinout image matching its exact revision) to complete this check.
Memory: no firmware changed; image size and heap not measured.
Next: T-104 Firmware core skeleton is the next eligible task because it depends only on T-101. T-103 remains blocked until the owner confirms the board labels.

### T-104 Firmware core skeleton (2026-11-10) status: blocked
Goal: add a MicroPython-compatible asyncio runtime skeleton with default JSON configuration, bounded log ring, main-loop-only watchdog feeding and a three-crash safe-mode threshold.
Done when: `boot.py` and `main.py` start the scheduler; configuration defaults load safely; logs use a fixed-size ring; only the main loop feeds the watchdog; three consecutive unsuccessful boots enter safe mode; modules run on the MicroPython unix port.
Files: `firmware/core/`, `firmware/tests/` only.

Changed: added `core/boot.py`, `main.py`, `config.py`, `state.py`, `scheduler.py`, `watchdog.py`, `log.py`; default JSON config, persistent consecutive-boot counter, three-failure safe-mode flag, 30-second stable-boot reset, fixed-capacity log ring and cooperative asyncio scheduler. Watchdog construction uses the documented ESP32 `machine.WDT(timeout=...)` API; the only `feed()` call is inside the scheduler's main loop. Tests avoid CPython-only unittest/tempfile dependencies and are written as a self-contained script.
Verified: CPython 3.13.5 mirror run of `firmware/tests/test_core.py`: 6 tests passed (defaults, config overrides, ring wrap/bounds, 3-crash safe mode, stable reset/corrupt-state fail-safe, main-loop watchdog feed). GitHub Actions run for commit `db58e1ae93ed663b2cc86c4d97811d2646f9ebc6` passed, but the existing workflow only runs `git diff --check`.
Blocker: no `micropython` executable (unix port) is installed in the environment, and CI does not yet run the unix-port tests. Therefore the required unix-port verification has not run. Per repo rules, this task remains blocked; no MicroPython runtime or hardware behaviour is claimed as verified. Module flash/RAM measurements also remain pending the pinned build task.
Memory: no ESP32 firmware image built; heap/image budgets not measured.
Next: T-109 Simulator node is the next eligible task (depends only on T-102); T-103 remains blocked pending physical board-label photo verification.

### T-109 Simulator node (2026-11-10) status: doing
Goal: implement a host-side WebSocket simulator that runs multiple distinct DCP nodes and enforces the shared protocol and board pin policy.
Done when: simulator supports `sys.info`, `sys.ping`, `gpio.mode`, `gpio.read`, `gpio.write`; `--count N` creates N distinct node IDs; shared vectors validate; integration test starts 100 nodes and queries each.
Files: `tools/sim_node.py`, `tools/requirements.txt`, `tests/` only.
