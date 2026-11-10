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

### T-109 Simulator node (2026-11-10) status: done
Goal: implement a host-side WebSocket simulator that runs multiple distinct DCP nodes and enforces the shared protocol and board pin policy.
Done when: simulator supports `sys.info`, `sys.ping`, `gpio.mode`, `gpio.read`, `gpio.write`; `--count N` creates N distinct node IDs; shared vectors validate; integration test starts 100 nodes and queries each.
Files: `tools/sim_node.py`, `tools/requirements.txt`, `tests/` only.

Changed: added `tools/sim_node.py` with WebSocket serving, schema/operation validation, 1..N distinct node IDs, node/group/tag/cell/wildcard routing, `sys.info`, `sys.ping`, GPIO mode/read/write and board-profile enforcement. Added host-only dependencies (`websockets>=13.0`, `jsonschema>=4.0`) and documented setup/run/test commands in `tools/README.md`. These dependencies do not enter firmware.
Verified: local integration run using the installed WebSocket 16.0 and JSON Schema 4.26.0 libraries: 6 tests passed. Shared valid/invalid vectors accepted/rejected; blocked and warned pins return DCP errors; GPIO mode/write/read round-trip passed; 100 simulated nodes were started behind a WebSocket server and all 100 returned distinct `sys.info` replies; wildcard routing returned all nodes. GitHub Actions run for commit `43f008c1bc0b03201b22190a48a3ea7455879abe` passed its configured `git diff --check` job.
Memory: simulator is host-only; no firmware flash/RAM impact.
Next: T-113 App skeleton is the next eligible task (depends on T-109 only), but the current environment has no Flutter or Dart executable; check availability before implementation and block if the required analyze/test verification cannot run.

### T-113 App skeleton (2026-11-10) status: blocked
Goal: create the Flutter fleet app shell with the NodeLink abstraction and WebSocket adapter, then connect it to the simulator.
Done when: Flutter project builds; NodeLink and WebSocket adapter exist; fleet lists simulator nodes; node detail displays sys.info; `flutter analyze` and `flutter test` pass.
Files: `app/` only.
Blocker: neither `flutter` nor `dart` is installed in the execution environment. Creating a project without the actual SDK would require guessing the SDK constraints/package metadata, and the required analyze/test verification could not run. No app files were changed.
Next: owner must provide a Flutter/Dart-capable runner or enable the SDK in the build environment. Gate 1 remains blocked.


### T-104 Firmware core skeleton — CI verification work (2026-11-10) status: doing
Goal: add a reproducible MicroPython unix-port test job so the existing firmware core is verified by the actual target Python runtime in CI.
Done when: the pinned unix port builds in CI; all six core tests pass under that runtime; the exact Verify output is recorded; task status is updated.
Files: `firmware/core/`, `firmware/tests/`, and `.github/workflows/ci.yml` (CI verification only; owner authorised changes needed to complete the project).
Changed: adding a CI job that builds the official MicroPython v1.29.0 unix port from its tagged source and runs `firmware/tests/test_core.py`; no firmware logic or hardware assumptions changed.
Verified: pending GitHub Actions run.
Memory: no ESP32 image built; device heap and flash budgets remain unmeasured.
Next: inspect the unix-port CI result; fix only T-104 failures, then continue to the next eligible backlog task.


### T-104 Firmware core skeleton — unix-port import-path correction (2026-11-10) status: doing
Goal: correct the CI invocation so the firmware package is discoverable by the MicroPython unix runtime.
Done when: the pinned unix port builds; all six core tests pass under MicroPython; exact output is recorded; task status is updated.
Files: `.github/workflows/ci.yml`, `PROGRESS.md`.
Changed: the first unix-port CI run successfully built MicroPython v1.29.0 but failed before tests because the `core` package was not on MicroPython's module search path (`ImportError: no module named 'core'`). Set `MICROPYPATH=firmware` for the test invocation; no firmware source changes.
Verified: pending rerun.
Memory: no ESP32 image built; device heap and flash budgets remain unmeasured.
Next: rerun T-104 CI and record the six-test result; only then select the next eligible backlog task.

### T-104 Firmware core skeleton — preserve frozen modules in unix-port test path (2026-11-10) status: doing
Goal: retain MicroPython's frozen standard-library search path while adding the repository firmware package to the unix-port test environment.
Done when: the pinned unix port builds; all six core tests pass under MicroPython; exact output is recorded; task status is updated.
Files: `.github/workflows/ci.yml`, `PROGRESS.md`.
Changed: the previous run built MicroPython v1.29.0 successfully but failed importing asyncio. The CI job set `MICROPYPATH=firmware`, which replaced the unix port's frozen-module search entry. Restored the frozen search entry explicitly with `MICROPYPATH=.frozen:firmware`; no firmware logic changed.
Verified: pending rerun.
Memory: no ESP32 image built; device heap and flash budgets remain unmeasured.
Next: rerun T-104 unix-port CI and record the six-test result; then select the next eligible backlog task.

### T-104 Firmware core skeleton — MicroPython unix-port verification (2026-11-10) status: done
Goal: close the MicroPython core task after the pinned v1.29.0 unix-port build and all six tests pass.
Done when: asyncio scheduler, JSON config defaults, bounded log ring, main-loop watchdog, three-crash safe mode and unix-port compatibility are verified; exact output is recorded; backlog status is updated.
Files: `firmware/core/`, `firmware/tests/`, `.github/workflows/ci.yml` (CI verification only); `TASKS.md` and `PROGRESS.md` for status.
Changed: added CI that builds the official MicroPython v1.29.0 unix port and runs the core test script. The final invocation preserves frozen modules and adds the repository package path with `MICROPYPATH=.frozen:firmware`.
Verified: GitHub Actions run 42764956525, commit `7af3475de10f039b3fe0b364424109fab79d8f22`: lint job PASS; pinned MicroPython unix build PASS; tests PASS — `PASS test_config_defaults`, `PASS test_config_overrides`, `PASS test_log_ring`, `PASS test_crash_counter_and_safe_mode`, `PASS test_corrupt_state_fails_safe`, `PASS test_watchdog_feed_is_in_scheduler_loop`, `PASS: 6 firmware core tests`. Exit code 0.
Memory: ESP32 image size and physical-device free heap not yet measured; those are part of T-107 build report and hardware validation. Unix executable size is not an ESP32 firmware measurement.
Next: T-105 DCP codec in firmware is now eligible (depends on T-102 and T-104). T-103 remains blocked until owner confirms physical board header labels.

### T-102 protocol-vector consistency correction (2026-11-10) status: done
Goal: align every valid DCP vector's version field with the normative v1.0 string contract before firmware codec conformance testing.
Done when: all valid vectors use the exact string `"1.0"`; invalid vectors remain unchanged; the correction is committed and the protocol validator is rerun by the codec CI verification.
Files: `protocol/vectors/valid.json`, `PROGRESS.md`.
Changed: replaced numeric `v: 1` values in valid vectors with the specified string `v: "1.0"`. Invalid vectors were not modified.
Verified: parsed the edited JSON and confirmed all valid vectors use `"1.0"`; 23 valid vectors retained. Full schema/operation validation will be exercised by the T-105 CI vector job.
Memory: no firmware changes.
Next: T-105 DCP codec in firmware.

### T-105 DCP codec in firmware (2026-11-10) status: doing
Goal: implement the MicroPython-compatible DCP v1 encoder, strict decoder, destination matching and standard error replies.
Done when: encode/decode/routing/error replies work; all shared valid and invalid vectors pass; RAM measurement script reports codec heap cost; exact MicroPython unix-port CI output and RAM result are recorded.
Files: `firmware/core/dcp.py`, `firmware/tests/test_core.py`, `firmware/tests/measure_dcp_ram.py`; `TASKS.md` and `PROGRESS.md` for task status.

### T-105 DCP codec in firmware (2026-11-10) status: done
Goal: implement the MicroPython-compatible DCP v1 encoder, strict decoder, destination matching and standard error replies.
Done when: encode/decode/routing/error replies work; all shared valid and invalid vectors pass; RAM measurement script reports codec heap cost; exact MicroPython unix-port CI output and RAM result are recorded.
Files: `firmware/core/dcp.py`, `firmware/tests/test_core.py`, `firmware/tests/measure_dcp_ram.py`; `TASKS.md` and `PROGRESS.md` for task status.
Changed: added bounded UTF-8 encode/decode (4,096-byte cap), duplicate-key and malformed JSON rejection, args nesting/member limits, finite-number checks, v1 envelope and operation validation, selector routing, and DCP error replies. Added shared-vector tests and a standalone gc.mem_free measurement script.
Verified: GitHub Actions run 42766278144 on commit `8c4bee3a6f46014ed3bf59502eb96a6b0b15c058` passed lint, built the pinned MicroPython v1.29.0 unix port, and passed all 9 core tests: `PASS test_config_defaults`, `PASS test_config_overrides`, `PASS test_log_ring`, `PASS test_crash_counter_and_safe_mode`, `PASS test_corrupt_state_fails_safe`, `PASS test_watchdog_feed_is_in_scheduler_loop`, `PASS test_dcp_shared_vectors`, `PASS test_dcp_strict_json_and_limits`, `PASS test_dcp_routing_and_error_reply`, `PASS: 9 firmware core tests`. Shared vectors: 23 valid accepted/round-tripped and 12 invalid rejected. Unix-port heap measurement: DCP module import `14,368 bytes`; sample round-trip retained `352 bytes`. These are unix-port measurements, not ESP32 heap measurements.
Memory: ESP32 target heap and flash costs remain unmeasured until T-107 ESP32 build and hardware boot; do not treat unix-port heap as ESP32 RAM.
Next: T-107 Build pipeline and memory report is now the first eligible firmware build task (T-106 depends on blocked T-103 physical pin-map confirmation). T-103 still requires owner photo/silkscreen verification.

### T-107 Build pipeline and memory report (2026-11-10) status: doing
Goal: create a reproducible ESP32_GENERIC build of MicroPython with the DemonCore core frozen into the image and Profile A flash partitions.
Done when: MicroPython source/version/SHA256 and ESP-IDF are pinned; the core is frozen; Profile A partition table is validated; build emits the single merged `Demoncore ESP32 Master Firmware.bin`; report records image size, 10% OTA-slot headroom and post-boot free heap; exact build verification is logged.
Files: `firmware/vendor/`, `firmware/manifest.py`, `firmware/partitions.csv`, `firmware/build/`, `.github/workflows/ci.yml`; `TASKS.md` and `PROGRESS.md` for status.


### T-107 ESP32 build pipeline — frozen-module manifest correction (2026-11-10) status: doing
Goal: produce the pinned ESP32_GENERIC OTA firmware image with DemonCore core frozen into MicroPython.
Done when: pinned source/version/hash are recorded; core manifest freezes required modules once; Profile A partitions build; the build emits a real merged image and report with OTA headroom; post-boot heap remains explicitly hardware-pending until measured.
Files: `firmware/vendor/`, `firmware/manifest.py`, `firmware/partitions.csv`, `firmware/build/`, CI.
Changed: removed the explicit `module()` declarations for `boot.py` and `main.py` because `freeze("core")` already freezes both files. The duplicate declarations generated duplicate C symbols (`frozen_module_boot` and `frozen_module_main`) and stopped the ESP32 compile.
Verified: previous run #52 (commit `26ff3c2d4bd24da08e91df9e10a72121322d3a09`) — lint PASS; MicroPython unix-port core tests PASS; ESP32 build FAIL at C compilation with redefinition errors for frozen boot/main modules. No artifact was produced. Official MicroPython ESP32 build documentation confirms `firmware.bin` is the combined bootloader, partition table and application image, suitable as the single-image output when the build succeeds.
Blocker: corrected manifest is committed next; rebuild and inspect report/artifact before marking done. Physical-board boot and runtime heap/GC measurements remain [HUMAN].
Memory: no verified ESP32 image yet; image size and post-boot heap remain unmeasured.
Next: rerun CI on main, validate merged image size/OTA headroom and SHA-256, then provide the binary only after artifact verification.

### T-107 OTA headroom remediation — size-optimized ESP-IDF build (2026-11-10) status: doing
Goal: meet the mandatory 10% OTA-slot spare while preserving the exact Profile A partition geometry and the existing MicroPython/ESP-IDF pins.
Done when: the reproducible ESP32 build uses verified size optimization; the application image leaves at least 10% of each OTA slot unused; all CI firmware tests pass; image and source hashes are recorded; physical boot, free heap, GC headroom and filesystem free space are measured or explicitly remain [HUMAN]-blocked.
Files: `firmware/build/build.sh`, `firmware/build/report.py`, `firmware/build/README.md`, `TASKS.md`, `PROGRESS.md`.

Changed: owner authorized solving the OTA shortfall. The previous application was 1,482,080 bytes in a 1,638,400-byte slot (9.54% spare), 7,520 bytes above the strict 90%-of-slot maximum. Preserve Profile A exactly; switch the pinned ESP-IDF configuration from its upstream performance mode (`-O2`) to size mode (`-Os`), fail closed if the expected upstream setting changes, and verify the generated sdkconfig in the report. This is a measured-build change, not a partition-layout workaround.

Verified: pending CI build and artifact inspection. The prior run 42768800978 passed lint and all 9 MicroPython unix-port core tests, but the ESP32 build failed only the strict OTA headroom check. Real-board boot, execution-speed impact, free heap, GC headroom and filesystem usage require the owner's ESP-WROOM-32 hardware and remain [HUMAN].

Next: inspect the size-optimized build report and SHA-256; if OTA headroom is at least 10%, provide the verified image while retaining the physical hardware checks as outstanding.

### T-107 build pipeline — restore executable build-script mode (2026-11-10) status: doing
Goal: rerun the pinned ESP32 build after the OTA-size optimization change.
Done when: the build script executes in CI, the image meets the strict 10% OTA-slot headroom requirement, and the artifact is hash-verified.
Files: `firmware/build/build.sh` file mode; `PROGRESS.md`.

Changed: the first run after the optimization commit passed lint and all 9 MicroPython unix-port core tests, but the ESP32 job stopped before invoking the build because the Git tree recorded `firmware/build/build.sh` as non-executable. Restore its executable bit (100755); no firmware source or partition change.

Verified: CI run 42770564358 — lint PASS; MicroPython unix-port build and all 9 tests PASS; ESP32 build did not start (exit 126, permission denied). No new firmware artifact was produced.

Next: rerun CI and inspect the actual size-optimized ESP32 build, OTA headroom, merged image and checksum. Physical hardware checks remain [HUMAN].

### T-107 build script quoting correction (2026-11-10) status: doing
Goal: restore a valid shell script and rerun the pinned ESP32 build.
Done when: `bash -n firmware/build/build.sh` passes; the script performs the pinned size-optimized build; the report verifies at least 10% OTA headroom.
Files: `firmware/build/build.sh`, `PROGRESS.md`.

Changed: CI run 42770796267 passed lint and all 9 MicroPython unix-port tests, but the ESP32 job exited before compiling because the generated script had a malformed shell quote from the initial automated edit. Replaced the script body cleanly and checked its shell syntax locally with `bash -n` (PASS). Restored executable mode 100755.

Verified: shell syntax check PASS. The previous ESP32 run produced no artifact; no OTA size result yet. Real-board boot and runtime resource checks remain [HUMAN].

Next: rerun CI; inspect the ESP32 build report and merged image before distributing any firmware.

### T-107 OTA image-size follow-up — optional ESP-IDF feature trimming (2026-11-10) status: doing
Goal: reduce the application image below the strict 90%-of-slot limit while preserving Profile A, Wi-Fi, BLE, TLS and the frozen DemonCore core.
Done when: the build deterministically uses `-Os`, disables only optional features outside the current board plan, verifies those settings from generated sdkconfig, and produces at least 10% OTA headroom; lint and all MicroPython core tests pass.
Files: `firmware/build/build.sh`, `firmware/build/report.py`, `firmware/build/README.md`, `TASKS.md`, `PROGRESS.md`.

Changed: CI run 42771051878 built successfully with `-Os`, but the application remained exactly 1,482,080 bytes and OTA spare remained 156,320 bytes (9.54%). Therefore compiler size mode alone does not meet the contract. The next bounded optimization disables optional SPI Ethernet PHY drivers (W5500/KSZ8851SNL/DM9051), ULP coprocessor and runtime INFO-level ESP logging. Wi-Fi, BLE, TLS and DCP remain enabled. The report will fail if any excluded feature is still enabled or if OTA spare is below 10%.

Verified: run 42771051878 — lint PASS; MicroPython unix-port build PASS; all 9 firmware core tests PASS; ESP32 compilation PASS; Profile A layout PASS; OTA 10% FAIL (9.54%). Artifact SHA-256 from report: `b1730de54bd68af5e54432633d73589ecb1dbb41ffcdf798f45f7ad91fef92ca`; this image is not an accepted release. No physical hardware tests were performed.

Next: run CI on the feature-trimmed configuration; verify the image size, OTA margin, hash and merged image. Hardware boot, free heap, GC headroom and runtime filesystem space remain [HUMAN].


### T-107 OTA trim correction — retain mandatory ULP headers (2026-11-10) status: doing
Goal: remove only optional ESP-IDF features that can be disabled without breaking the pinned MicroPython ESP32 port.
Done when: the pinned build compiles, Profile A is unchanged, at least 10% OTA-slot headroom is measured, unix-port tests pass, and image/source hashes are recorded.
Files: `firmware/build/build.sh`, `firmware/build/report.py`, `firmware/build/README.md`, `PROGRESS.md`.

Changed: run 42771740065 confirmed that disabling `CONFIG_ULP_COPROC_ENABLED` is not safe for this pinned MicroPython source: `ports/esp32/esp32_ulp.c` is compiled unconditionally and requires the ESP-IDF `esp32/ulp.h` header. Reverted only that ULP exclusion and removed it from the report's disabled-feature assertions. SPI Ethernet PHY drivers and runtime INFO-level ESP logging remain excluded; Wi-Fi, BLE, TLS and ULP support remain enabled. Profile A partition geometry is untouched.

Verified: run 42771740065 — lint PASS; MicroPython unix-port build and all 9 tests PASS; ESP32 compile FAIL at `esp32_ulp.c:32` with missing `esp32/ulp.h`, caused by the unsupported ULP Kconfig exclusion. No firmware artifact was produced. The next CI run must confirm that retaining ULP restores compilation and whether the remaining supported trims meet the OTA threshold.

Memory: no physical ESP32 boot; free heap, GC headroom and runtime filesystem space remain [HUMAN].
Next: rerun pinned CI, inspect the measured OTA report, then iterate only on source-verified optional features if the 10% threshold still fails.
