import csv
import hashlib
import hmac
import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.provision import (
    REPO_ROOT, derive_credentials, load_domain_key, load_nodes,
    nvs_csv_text, generate_nvs_image, write_label, _private_output_dir,
)


class ProvisioningTests(unittest.TestCase):
    def test_derivation_matches_hmac_and_separates_cell_key(self):
        key = bytes(range(32))
        device, cell = derive_credentials(key, 42, "lab")
        self.assertEqual(device, hmac.new(key, b"42", hashlib.sha256).digest())
        self.assertEqual(cell, hmac.new(key, b"demoncore:cell:v1:lab", hashlib.sha256).digest())
        other_node, same_cell = derive_credentials(key, 43, "lab")
        _, other_cell = derive_credentials(key, 42, "field")
        self.assertEqual(cell, same_cell)
        self.assertNotEqual(device, other_node)
        self.assertNotEqual(cell, other_cell)
        self.assertEqual(len(device), 32)
        self.assertEqual(len(cell), 32)
        self.assertNotEqual(device, cell)

    def test_key_file_raw_and_hex_and_repository_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "domain.key"
            raw.write_bytes(b"k" * 32)
            self.assertEqual(load_domain_key(raw), b"k" * 32)
            raw.write_text((b"k" * 32).hex(), encoding="ascii")
            self.assertEqual(load_domain_key(raw), b"k" * 32)
        with tempfile.TemporaryDirectory(dir=str(REPO_ROOT)) as tmp:
            key_file = Path(tmp) / "domain.key"
            key_file.write_bytes(b"k" * 32)
            with self.assertRaises(ValueError):
                load_domain_key(key_file)

    def test_csv_validates_unique_uint64_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nodes.csv"
            path.write_text("node_id,name,cell\n7,Desk,lab\n8,Sensor,lab\n", encoding="utf-8")
            nodes = load_nodes(path)
            self.assertEqual([x["node_id"] for x in nodes], [7, 8])
            self.assertEqual(nodes[0]["cell"], "lab")
            path.write_text("node_id\\n9\\n", encoding="utf-8")
            self.assertEqual(load_nodes(path)[0]["cell"], "default")
            path.write_text("node_id,cell\\n10,INVALID CELL\\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_nodes(path)
            path.write_text("node_id\n7\n7\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_nodes(path)
            path.write_text("node_id\n0\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_nodes(path)

    def test_nvs_csv_matches_identity_store_blob_layout(self):
        text = nvs_csv_text(0x0102030405060708, b"d" * 32, b"c" * 32)
        self.assertIn("demoncore,namespace,,", text)
        self.assertIn("node_id,data,hex2bin,0102030405060708", text)
        self.assertIn("dev_secret,data,hex2bin," + (b"d" * 32).hex(), text)
        self.assertIn("cell_key,data,hex2bin," + (b"c" * 32).hex(), text)
        self.assertIn("claimed,data,i32,1", text)

    def test_nvs_generation_removes_secret_csv_and_locks_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generator = root / "fake_nvs_gen.py"
            generator.write_text(
                "import pathlib,sys\n"
                "pathlib.Path(sys.argv[3]).write_bytes(b'\\xff'*0x4000)\n",
                encoding="utf-8",
            )
            output = root / "out"
            output.mkdir(mode=0o700)
            image = generate_nvs_image({"node_id": 17}, b"k" * 32, generator, output)
            self.assertEqual(image.stat().st_size, 0x4000)
            self.assertEqual(image.stat().st_mode & 0o777, 0o600)
            self.assertFalse(list(output.glob(".demoncore-nvs-*.csv")))

    def test_label_contains_visible_node_id_and_svg_qr(self):
        with tempfile.TemporaryDirectory() as tmp:
            label = write_label({"node_id": 314}, Path(tmp))
            content = label.read_text(encoding="utf-8")
            self.assertIn("Node ID: 314", content)
            self.assertIn("<svg", content)

    def test_output_directory_cannot_be_inside_repo(self):
        with self.assertRaises(ValueError):
            _private_output_dir(REPO_ROOT / "tools" / "unsafe-test-output")


if __name__ == "__main__":
    unittest.main()
