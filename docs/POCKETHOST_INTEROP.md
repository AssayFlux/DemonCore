# Pocket Host interoperability boundary

**Status:** proposed integration contract; no Pocket Host bridge is implemented by this document.  
**Related project:** [AssayFlux/PocketHost](https://github.com/AssayFlux/PocketHost).  
**DemonCore authority:** `NORTH_STAR.md`, `docs/PLAN.md`, `TASKS.md`, `AGENTS.md` and the DCP specifications remain authoritative for DemonCore implementation.

## 1. Purpose

Pocket Host is evolving into a cross-platform website/service hosting and device-management ecosystem. DemonCore is a specialised microcontroller and edge-device fleet project. They should interoperate without merging repositories, duplicating firmware internals or making either product mandatory for the other.

## 2. Responsibility boundary

**Pocket Host owns**
- General-purpose host nodes: Android, Linux, Windows, macOS, VPS/server and capable SBC.
- Website ingress, static hosting, supported language runtimes and multi-component service deployments.
- Host-node registration, service placement, operator UX and public website connectivity.
- The policy decision about which edge capabilities a website/service may consume.

**DemonCore owns**
- MCU firmware, board profiles, pin/peripheral safety and MicroPython resource budgets.
- DCP device protocol, device identity/claim, provisioning and MCU-specific authentication.
- BLE/Wi-Fi/ESP-NOW/MQTT device transports, mesh/fleet operations and firmware OTA.
- The allow-listed set of device capabilities exposed by each board profile.

An ESP32 is not presumed to be a general-purpose Pocket Host host. It may provide telemetry, sensor/actuator operations, a bounded local API, MQTT/DCP endpoint or protocol bridge only when the exact board/firmware profile passes its own resource, security and hardware acceptance.

## 3. Target topology

```
Pocket Host operator / optional control plane
                   |
       Pocket Host edge-fleet adapter
                   |
       DemonCore hub / authenticated DCP gateway
                   |
       MQTT / BLE / Wi-Fi / ESP-NOW
                   |
          Claimed MCU / edge nodes
```

The DemonCore hub is a future integration point, not an implemented dependency. A Raspberry Pi or other capable Linux SBC may eventually host both a Pocket Host Linux node and the DemonCore hub if each workspace becomes independently deployable and passes its own security and resource tests.

## 4. Protocol and security prerequisites

- DCP v1.0's envelope is not authentication. The normative `protocol/dcp.md` explicitly states this.
- The current DCP message and reassembly limit is 4,096 bytes. Gateways must enforce the limit and never partially execute an oversized message.
- Only operations explicitly present in the versioned operation catalogue and granted by owner policy may be exposed.
- Complete claim, authenticated/encrypted transport, key lifecycle, replay protection, revocation and OTA authorization before cross-network Pocket Host integration.
- Do not forward arbitrary public HTTP requests into DCP, GPIO or firmware administration.
- Do not reuse device secrets as Pocket Host owner/account credentials.
- A compromised MCU must not gain host filesystem, runtime secret, management API or unrelated device access.
- Public website ingress and device-management ingress remain separate.
- Preserve board pin validation and owner confirmation rules for dangerous hardware operations.

## 5. Integration sequence

1. Complete DemonCore Phase 1 hardware acceptance: verify exact board pinout, physical boot, memory/GC/filesystem margins and live transport.
2. Complete device identity/claim and provisioning on real hardware.
3. Complete authenticated/encrypted transport, authorization, key rotation and revocation.
4. Complete OTA signature/rollback and fleet-hub acceptance.
5. Freeze a versioned DCP gateway API and capability catalogue suitable for remote consumption.
6. Implement the Pocket Host adapter with explicit enrollment, scoped capabilities, rate limits, audit and health state.
7. Test simulator and real boards, network interruption, malicious/compromised node behaviour and revocation end-to-end.

Do not skip a blocked human hardware task. CI/simulator evidence does not substitute for a physical board.

## 6. Current repository status snapshot (2026-11-17)

The current root README records:
- ESP-WROOM-32 38-pin, 4 MiB flash, no PSRAM target with pinned MicroPython.
- Phase 1 is not hardware-accepted; physical boot/resource checks and board pinout confirmation remain open.
- `app/` is documentation-only and has no Flutter `pubspec.yaml` or Dart application.
- `hub/` is not implemented.
- DCP v1.0, simulator and firmware foundations exist, but DCP v1 itself does not authenticate traffic.
- Claim/provisioning, transports, fleet, mesh, OTA and job work remain gated by `TASKS.md`.

Recheck the live backlog, exact commit and CI before claiming any prerequisite is complete. This snapshot is not a substitute for the current task ledger.

## 7. Non-goals

- No repository merge, git submodule or copied firmware implementation.
- No Pocket Host website engine or Python/Node runtime on ESP32 by default.
- No unauthenticated DCP bridge or public GPIO/control endpoint.
- No claims of fleet scale, mesh reliability, hardware compatibility or production readiness without physical and adversarial evidence.
