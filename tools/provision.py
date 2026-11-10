#!/usr/bin/env python3
"""Generate per-node ESP32 NVS images, QR labels and a secret-free registry export."""
import argparse
import csv
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[1]
NVS_SIZE = 0x4000
NVS_OFFSET = 0x9000
APP_OFFSET = 0x10000
APP_SLOT_SIZE = 0x190000
DEVICE_SECRET_BYTES = 32
MAX_NODE_ID = (1 << 64) - 1


def load_domain_key(path):
    """Read a 32-byte key from outside the repository; never print its contents."""
    key_path = Path(path).expanduser().resolve(strict=True)
    try:
        key_path.relative_to(REPO_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("domain key file must be outside the repository")
    raw = key_path.read_bytes()
    if len(raw) == DEVICE_SECRET_BYTES:
        return raw
    try:
        text = raw.decode("ascii").strip()
        if re.fullmatch(r"[0-9a-fA-F]{64}", text):
            return bytes.fromhex(text)
    except UnicodeDecodeError:
        pass
    raise ValueError("domain key must contain 32 raw bytes or 64 hexadecimal characters")


def derive_credentials(domain_key, node_id):
    if not isinstance(domain_key, bytes) or len(domain_key) != DEVICE_SECRET_BYTES:
        raise ValueError("domain key must be exactly 32 bytes")
    if isinstance(node_id, bool) or not isinstance(node_id, int) or not 1 <= node_id <= MAX_NODE_ID:
        raise ValueError("node_id must be a positive uint64")
    identity = str(node_id).encode("ascii")
    device_secret = hmac.new(domain_key, identity, hashlib.sha256).digest()
    cell_key = hmac.new(domain_key, b"demoncore:cell:v1:" + identity, hashlib.sha256).digest()
    return device_secret, cell_key


def load_nodes(csv_path):
    rows = []
    seen = set()
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "node_id" not in reader.fieldnames:
            raise ValueError("CSV must have a node_id column")
        if set(reader.fieldnames) - {"node_id", "name", "cell"}:
            raise ValueError("CSV may contain only node_id, name and cell columns")
        for line, row in enumerate(reader, start=2):
            raw_id = (row.get("node_id") or "").strip()
            if not re.fullmatch(r"[1-9][0-9]{0,19}", raw_id):
                raise ValueError("invalid node_id on CSV line %d" % line)
            node_id = int(raw_id)
            if node_id > MAX_NODE_ID or node_id in seen:
                raise ValueError("duplicate or out-of-range node_id on CSV line %d" % line)
            seen.add(node_id)
            name = (row.get("name") or "").strip()
            cell = (row.get("cell") or "").strip()
            if len(name) > 64 or len(cell) > 32:
                raise ValueError("name or cell metadata too long on CSV line %d" % line)
            rows.append({"node_id": node_id, "name": name, "cell": cell})
    if not rows:
        raise ValueError("CSV contains no nodes")
    return rows


def nvs_csv_text(node_id, device_secret, cell_key):
    """Build the exact namespace/key layout consumed by firmware/core/identity.py."""
    rows = [
        ["key", "type", "encoding", "value"],
        ["demoncore", "namespace", "", ""],
        ["node_id", "data", "hex2bin", node_id.to_bytes(8, "big").hex()],
        ["dev_secret", "data", "hex2bin", device_secret.hex()],
        ["cell_key", "data", "hex2bin", cell_key.hex()],
        ["tx_count", "data", "hex2bin", "0000000000000000"],
        ["rx_count", "data", "hex2bin", "0000000000000000"],
        ["claimed", "data", "i32", "1"],
    ]
    from io import StringIO
    output = StringIO()
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue()


def _private_output_dir(path):
    output = Path(path).expanduser().resolve()
    try:
        output.relative_to(REPO_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("output directory must be outside the repository")
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        output.chmod(0o700)
    except OSError:
        pass
    return output


def generate_nvs_image(node, domain_key, generator, output_dir):
    device_secret, cell_key = derive_credentials(domain_key, node["node_id"])
    fd, csv_name = tempfile.mkstemp(prefix=".demoncore-nvs-", suffix=".csv", dir=str(output_dir))
    os.chmod(csv_name, 0o600)
    image_path = output_dir / ("node-%d.nvs.bin" % node["node_id"])
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(nvs_csv_text(node["node_id"], device_secret, cell_key))
        subprocess.run(
            [sys.executable, str(generator), "generate", csv_name, str(image_path),
             hex(NVS_SIZE), "--version", "2"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
    finally:
        try:
            os.unlink(csv_name)
        except FileNotFoundError:
            pass
    if not image_path.is_file() or image_path.stat().st_size != NVS_SIZE:
        raise RuntimeError("NVS generator did not produce an exact 16 KiB image")
    image_path.chmod(0o600)
    return image_path


def write_label(node, output_dir):
    import qrcode
    import qrcode.image.svg
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=8, border=4)
    qr.add_data("node:%d" % node["node_id"])
    qr.make(fit=True)
    image = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
    path = output_dir / ("node-%d-label.svg" % node["node_id"])
    image.save(str(path))
    path.chmod(0o600)
    return path


def flash_node(port, node, nvs_image, bootloader, partition_table, phy_init, app_image):
    """Flash split images only; a merged image can overwrite the NVS partition."""
    required = [bootloader, partition_table, phy_init, app_image]
    if any(not Path(item).is_file() for item in required):
        raise ValueError("all split firmware image paths must exist")
    if Path(app_image).stat().st_size > APP_SLOT_SIZE:
        raise ValueError("application image exceeds the 1,600 KiB OTA slot")
    import shutil
    if shutil.which("esptool") is None:
        raise RuntimeError("esptool executable not found; install tools/requirements.txt")
    command = [
        "esptool", "--chip", "esp32", "--port", port, "--baud", "460800",
        "write-flash", "0x1000", str(bootloader), "0x8000", str(partition_table),
        "0x9000", str(nvs_image), "0xf000", str(phy_init),
        "0x10000", str(app_image),
    ]
    subprocess.run(command, check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", required=True, help="CSV with node_id and optional name,cell")
    parser.add_argument("--domain-key-file", required=True, help="32-byte raw or 64-hex key file outside repo")
    parser.add_argument("--output-dir", default=str(Path.home() / ".local/share/demoncore/provisioned"))
    parser.add_argument("--nvs-generator", default=None, help="ESP-IDF nvs_partition_gen.py path")
    parser.add_argument("--port", help="flash each generated node image to this serial port")
    parser.add_argument("--bootloader")
    parser.add_argument("--partition-table")
    parser.add_argument("--phy-init")
    parser.add_argument("--app-image", help="unmerged application binary for ota_0")
    args = parser.parse_args(argv)

    key = load_domain_key(args.domain_key_file)
    nodes = load_nodes(args.nodes)
    output_dir = _private_output_dir(args.output_dir)
    generator = args.nvs_generator
    if not generator:
        idf = os.environ.get("IDF_PATH")
        if idf:
            generator = str(Path(idf) / "components/nvs_flash/nvs_partition_generator/nvs_partition_gen.py")
    if not generator or not Path(generator).is_file():
        parser.error("provide --nvs-generator or set IDF_PATH to the pinned ESP-IDF checkout")
    if args.port and not all((args.bootloader, args.partition_table, args.phy_init, args.app_image)):
        parser.error("--port requires --bootloader, --partition-table, --phy-init and --app-image")

    registry = []
    for node in nodes:
        image = generate_nvs_image(node, key, generator, output_dir)
        label = write_label(node, output_dir)
        registry.append({
            "node_id": node["node_id"], "name": node["name"], "cell": node["cell"],
            "hardware": "ESP-WROOM-32", "claimed": True,
            "credential_profile": "hmac-sha256-domain-separated-v1",
            "label_file": label.name,
        })
        if args.port:
            flash_node(args.port, node, image, args.bootloader, args.partition_table,
                       args.phy_init, args.app_image)
        print("Prepared node %d: %s%s" % (
            node["node_id"], image.name, " (flashed)" if args.port else ""
        ))

    registry_path = output_dir / "registry-export.json"
    registry_path.write_text(json.dumps({"schema": "demoncore-provisioning-v1",
                                         "nodes": registry}, indent=2) + "\n",
                             encoding="utf-8")
    registry_path.chmod(0o600)
    print("Registry export: %s" % registry_path)
    print("No credential values were written to labels or registry export.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print("Provisioning failed: %s" % error, file=sys.stderr)
        raise SystemExit(2)
