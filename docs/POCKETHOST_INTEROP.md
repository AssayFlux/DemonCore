# Pocket Host 0.1.0 — DemonCore Edge Integration

**Product relationship:** interoperable, independently operated systems  
**Mobile owner interface:** Pocket Host Android and iOS command-center applications  
**DemonCore role:** microcontroller firmware, board safety and constrained device fleet

## 1. Responsibility boundary

Pocket Host manages the user's fleet from a mobile phone and operates general-purpose host nodes, websites, application components, runtimes, ingress and backups.

DemonCore manages MCU firmware, board profiles, safe GPIO/peripheral operations, device identity/provisioning, DCP messaging, embedded transports and MCU fleet lifecycle.

The repositories remain independently buildable and deployable. Neither project is required for the other to operate its own supported workloads.

## 2. Interconnected topology

```
Pocket Host Android / iOS command center
                  |
        authenticated fleet API
                  |
        Pocket Host host agents
                  |
       Pocket Host edge gateway
                  |
       authenticated DCP adapter
                  |
        DemonCore hub / gateway
                  |
       MQTT / BLE / Wi-Fi / ESP-NOW
                  |
        claimed MCU and sensor nodes
```

The mobile command center may pair, inspect, approve, configure and revoke edge devices through Pocket Host's edge gateway. It does not connect to unauthenticated MCU administration endpoints or send arbitrary DCP/GPIO commands.

A capable Linux SBC may run the Pocket Host host agent and DemonCore gateway as separate supervised components. They use separate service identities, storage, resource limits, credentials, health checks and update paths.

## 3. Device capability model

- ESP32-class MCUs: telemetry, sensor/actuator APIs, bounded local control, MQTT/DCP endpoint and protocol bridge where board profile supports it.
- Smaller MCUs: constrained measurements, event production and actuator operations.
- Raspberry Pi and other SBCs: general-purpose Linux host/gateway when the exact model and OS profile passes Pocket Host host acceptance. They are not microcontrollers.
- No MCU is assumed to run the Pocket Host Rust website engine, arbitrary Python/Node applications or general-purpose customer workloads.

## 4. Trust and protocol boundary

- DCP message format is not authentication.
- Device identity and claim must be completed before remote control.
- Cross-network DCP requires authenticated/encrypted transport, replay protection, authorization, key rotation and revocation.
- Every operation is allow-listed and scoped to the exact node, board profile and owner policy.
- GPIO access must pass board-specific safe pin rules and explicit confirmation for sensitive pins.
- Public website ingress never forwards to DCP administration, firmware update or GPIO operations.
- Firmware and OTA metadata are signed and rollback policy is enforced.
- Device secrets are distinct from Pocket Host owner credentials and host-agent keys.
- A compromised MCU cannot obtain SBC host-agent privileges or another node's credentials.

## 5. Failure containment

- Pocket Host mobile app unavailable: enrolled hosts and MCU gateway continue their last authorized local policy.
- Pocket Host control plane unavailable: local gateway and existing device operation continue within bounded authorization leases.
- DemonCore hub unavailable: unrelated Pocket Host websites and hosts continue; MCU-dependent components report degraded.
- One MCU offline or compromised: other nodes and host services remain isolated.
- Edge adapter failure: website ingress, runtime cells and other tunnel providers remain available.
- Firmware update failure: MCU returns to its last known-good image where the board bootloader/update design supports rollback.

## 6. Integration prerequisites

1. Physical board profile and pin mapping accepted for each target board.
2. Firmware boot, memory/GC, watchdog and filesystem limits measured on real hardware.
3. Device identity, secure claim, owner approval and revocation implemented.
4. Authenticated/encrypted DCP transport, replay protection and bounded parsing verified.
5. Signed OTA, rollback and interrupted-update recovery accepted.
6. Hub/gateway deployment, resource limits and fault recovery accepted.
7. Versioned edge capability catalogue and Pocket Host adapter implemented.
8. End-to-end mobile pairing, authorization, telemetry, device operation and revocation tested on real hardware.

Simulator and CI tests do not replace physical hardware acceptance.

## 7. Protocol compatibility

DCP has its own protocol version and compatibility lifecycle, independent of the Pocket Host product release version 0.1.0. Pocket Host adapter declares supported DCP version ranges and rejects unknown or unsafe operations. Breaking protocol changes require negotiated compatibility and staged rollout.

## 8. Non-goals

- No repository merge.
- No shared fleet-wide secret.
- No public MCU management endpoint.
- No arbitrary remote shell or unrestricted GPIO API.
- No promise of general-purpose web runtime execution on microcontrollers.
- No dependency from Pocket Host website serving on DemonCore availability.
