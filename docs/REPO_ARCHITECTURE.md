# DemonCore modular monorepo architecture

## Decision

DemonCore remains one Git repository, but each product/tool is an independently buildable workspace. Shared contracts and governance stay at the repository root. This is a modular monorepo, not a set of nested Git repositories or submodules.

## Target layout

```text
DemonCore/
├── firmware/                 # ESP32 MicroPython product
│   ├── src/                  # runtime and device-side modules (migration target)
│   ├── boards/               # board profiles
│   ├── build/                # pinned build and merged BIN pipeline
│   ├── tests/                # firmware/unit/resource tests
│   ├── vendor/               # pinned upstream source/lock
│   ├── plugins/
│   └── README.md
├── app/                      # Flutter Android product
│   ├── lib/
│   ├── android/
│   ├── assets/
│   ├── test/
│   └── README.md
├── hub/                      # self-hosted control-plane product
│   ├── src/
│   ├── services/
│   ├── config/
│   ├── deploy/
│   ├── tests/
│   └── README.md
├── tools/                    # host-side developer tools
│   ├── simulator/
│   ├── pin-validator/
│   ├── flash/
│   ├── provisioning/
│   ├── tests/
│   └── README.md
├── protocol/                 # shared DCP contract; remains root-level
├── Assets/                   # owner-supplied source models/images
├── docs/                     # cross-project architecture and guides
├── .github/                  # repository-wide CI
├── NORTH_STAR.md
├── AGENTS.md
├── TASKS.md
├── PROGRESS.md
├── README.md
└── LICENSE
```

Empty future directories should be created only when the corresponding task introduces real code; do not add empty placeholder trees merely to make the diagram look complete.

## Current-to-target path map

| Current path | Target path / disposition |
|---|---|
| `firmware/core/**` | `firmware/src/core/**` (preserve package/import semantics; choose exact package root after checking MicroPython frozen-module and import paths) |
| `firmware/boards/**` | Stay in `firmware/boards/**` |
| `firmware/build/**` | Stay in `firmware/build/**` |
| `firmware/tests/**` | Stay in `firmware/tests/**` |
| `firmware/vendor/**` | Stay in `firmware/vendor/**` |
| `firmware/manifest.py`, `firmware/partitions.csv`, `firmware/boot.py`, `firmware/main.py` (where present) | Stay under `firmware/`; builder and freeze manifest paths must be updated atomically if any path moves |
| `tools/sim_node.py` | `tools/simulator/sim_node.py` |
| `tools/validate_pins.py` | `tools/pin-validator/validate_pins.py` |
| `tools/tests/**` | `tools/pin-validator/tests/**` or the owning tool's own test directory, after test ownership is classified |
| `tools/requirements.txt` | Split into per-tool requirements files; keep a root tools requirements file only if shared dependencies remain |
| root `tests/test_sim_node.py` | `tools/simulator/tests/test_sim_node.py` |
| `web-flasher/**` | `tools/web-flasher/**` (update docs/workflows and hosting paths) |
| `protocol/**` | Stay at root as the shared versioned contract consumed by firmware, app and hub |
| `docs/**`, `Assets/**` | Stay at root as cross-project documentation and supplied source assets |
| `.github/**`, `AGENTS.md`, `NORTH_STAR.md`, `TASKS.md`, `PROGRESS.md`, `README.md`, `LICENSE` | Stay at root as repository governance/shared CI/legal files |
| `app/**`, `hub/**` | Already separate workspace roots; introduce their own source/dependency/test/build files within those roots |

This map is a plan, not permission to move all paths in one blind filesystem operation. Before each move, inspect exact tree paths, references, import semantics and workflow assumptions.

## Workspace independence contract

- **Firmware:** its own pinned MicroPython/ESP-IDF build, manifest, partition profile, tests and flashable merged image. No dependency on Flutter or hub source.
- **App:** its own Flutter package, Android project, UI, tests and APK/AAB build. It consumes DCP schemas/vectors, not firmware Python modules.
- **Hub:** its own service/deployment configuration, APIs, broker integration, tests and container build. It consumes DCP schemas/vectors, not firmware internals.
- **Tools:** host-side simulator, validator, flashing and provisioning utilities, each with explicit dependencies and entry-point documentation.
- **Protocol:** the only shared wire-level contract. Version changes follow the protocol change order in `AGENTS.md`.
- **CI:** path-filtered jobs may optimise execution later, but a root-level integration workflow must still validate shared protocol compatibility and cross-workspace contracts.

## Migration sequence and safety gates

1. **Inventory and freeze baseline:** capture current tree, all imports, path literals, build/freeze manifests, CI workflow references, docs links and test commands. Record baseline passing jobs.
2. **Tools extraction:** move simulator, pin validator and simulator tests into tool-owned subdirectories; split dependencies and update entry points.
3. **Firmware source boundary:** establish the chosen `firmware/src` package layout only after verifying frozen-module/import behaviour; update manifest/build scripts atomically.
4. **Standalone app and hub workspaces:** create actual Flutter and hub project metadata only when their implementation tasks are active; do not fabricate SDK versions or placeholder source.
5. **CI and docs:** add per-workspace build/test jobs and root integration checks; update every path reference and workspace README.

For every step:
- Use git moves so file history is retained; do not rewrite file contents unnecessarily.
- Keep the Apache-2.0 `LICENSE` unchanged.
- Preserve binary asset blobs and the four agreed asset names.
- Search the entire repository for old paths after each move.
- Run all affected unit tests, protocol vectors, lint, firmware build/report, and the relevant app/hub checks when those workspaces exist.
- Verify the merged firmware image hash and partition layout after firmware path changes.
- Commit directly to `main` with the task ID; no branch or PR.
- Never report a workspace as independently buildable until its actual toolchain build succeeds.

## Explicit non-goals

- Do not split into multiple repositories or git submodules.
- Do not duplicate DCP schemas/vectors across projects; consume the root protocol contract.
- Do not move root governance, licence, shared docs or supplied Assets into one product.
- Do not create a fake Flutter APK or hub service merely to populate folders.
