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
Changed: added purpose READMEs for all required project folders and firmware subfolders; added `.github/workflows/ci.yml` using `git diff --check HEAD^ HEAD`; tightened `.gitignore` for generated firmware artifacts and local secrets; clarified this task's scope and main-only verification in `TASKS.md`.
Baseline: no pre-existing test suite or CI workflow was present, so there were no baseline tests to run.
Verified: pending push-triggered GitHub Actions result.
Blocker: repository already contains a full Apache-2.0 LICENSE, not a placeholder. Preserved it. Owner must confirm whether Apache-2.0 is intentional or specify the desired licence before T-101 can be marked done.
Memory: no firmware code or binaries changed; image size and heap not measured.
Next: check the CI run on `main`; ask owner to confirm the licence; only then close T-101 and proceed to T-102.
