# Developer tools

Command-line utilities for flashing, provisioning, OTA, simulation and development workflows belong here. Never print or commit credentials, keys or tokens.

## DCP simulator

Install the host-only dependencies with `python -m pip install -r tools/requirements.txt`, then run `python tools/sim_node.py --count 100`. The simulator listens on `ws://127.0.0.1:8765` by default and assigns consecutive node IDs starting at 1. Use `--base-id` to change the first ID and `--wifi-active` to enforce ADC2 unavailability. Run its integration tests with `python -m unittest discover -s tests -v`.

The WebSocket and JSON Schema packages are host tooling only; they add no ESP32 firmware flash or RAM cost.


## Manufacturing provisioning

Provision one node per CSV row. The CSV must contain a unique decimal `node_id`; optional `name` and `cell` columns are metadata only. The 32-byte domain key must be supplied from a file outside this repository, either as 32 raw bytes or 64 hexadecimal characters. The tool derives the device secret as HMAC-SHA256(domain key, ASCII decimal node ID) and derives a distinct per-node cell key with the domain label `demoncore:cell:v1:`. The domain key and derived secrets are never included in labels or registry exports.

Install host dependencies with `python -m pip install -r tools/requirements.txt`. Find the ESP-IDF NVS generator under `$IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py`. Example:

```sh
python tools/provision.py \
  --nodes nodes.csv \
  --domain-key-file /secure/path/domain.key \
  --output-dir /secure/path/provisioned \
  --nvs-generator "$IDF_PATH/components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py"
```

The output directory must be outside the repository and is created with private permissions. Each node gets a 16 KiB NVS image and an SVG label whose QR encodes only `node:<id>`; a registry JSON export contains metadata, never credentials. The NVS images contain plaintext device credentials: protect the output directory and transfer media accordingly. This workflow does not enable NVS encryption or flash encryption.

To flash one node, supply `--port` plus the split bootloader, partition-table, PHY-init and application binaries. The tool writes them at Profile A offsets (0x1000, 0x8000, 0xf000 and 0x10000) and writes that node's NVS image at 0x9000. It deliberately does not flash the merged image at 0x1000: a contiguous merged image may cover the NVS address range and erase the provisioned credentials. Flashing is optional in the host workflow and must be done one physical board at a time.
