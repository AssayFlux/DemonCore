# DemonCore Android app builder

**Workspace:** `app/`  
**Product:** Flutter Android control app  
**Shared contract:** [DCP](../protocol/README.md)

This is the app-builder directory. All Flutter/Dart source, UI, app assets, transport adapters and app tests belong here. Do not put ESP32 MicroPython code here.

## Planned responsibilities

- Provisioning and BLE discovery/claim.
- Fleet list and node detail.
- GPIO/pin-board control with safety confirmations.
- Console and redacted logs.
- Jobs, rules, OTA rollout, roles and audit.
- 3D board, replay and fleet heat map.

All UI communication must use the shared `NodeLink` interface. BLE, WebSocket and MQTT are adapters behind that interface; widgets must not call transports directly.

## Current state

This directory is currently a documentation placeholder: there is no `pubspec.yaml`, Dart source tree or Android project yet. T-113 is blocked until a Flutter/Dart-capable build environment is available. Do not claim an APK can be built until the app scaffold and `flutter analyze` / `flutter test` checks exist.

See [T-113](../TASKS.md#t-113-app-skeleton) and [NORTH_STAR.md](../NORTH_STAR.md).
