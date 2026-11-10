# Developer tools

Command-line utilities for flashing, provisioning, OTA, simulation and development workflows belong here. Never print or commit credentials, keys or tokens.

## DCP simulator

Install the host-only dependencies with `python -m pip install -r tools/requirements.txt`, then run `python tools/sim_node.py --count 100`. The simulator listens on `ws://127.0.0.1:8765` by default and assigns consecutive node IDs starting at 1. Use `--base-id` to change the first ID and `--wifi-active` to enforce ADC2 unavailability. Run its integration tests with `python -m unittest discover -s tests -v`.

The WebSocket and JSON Schema packages are host tooling only; they add no ESP32 firmware flash or RAM cost.
