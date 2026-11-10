#!/usr/bin/env python3
"""Validate DCP v1 shared vectors against the envelope and request schemas."""
import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    raise SystemExit("Install host test dependency: python -m pip install jsonschema")

ROOT = Path(__file__).resolve().parent

def load(path):
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)

def main():
    envelope = Draft202012Validator(load(ROOT / "schema" / "message.schema.json"))
    operations = load(ROOT / "ops.json")["operations"]
    valid = load(ROOT / "vectors" / "valid.json")
    invalid = load(ROOT / "vectors" / "invalid.json")
    failures = []

    for vector in valid:
        message = vector["message"]
        errors = list(envelope.iter_errors(message))
        if message.get("op") in operations and message.get("t") in ("req", "res"):
            contract = operations[message["op"]]["request" if message["t"] == "req" else "response"]
            errors.extend(Draft202012Validator(contract).iter_errors(message.get("args")))
        if errors:
            failures.append("valid %s rejected: %s" % (vector["name"], "; ".join(e.message for e in errors)))

    for vector in invalid:
        if not list(envelope.iter_errors(vector["message"])):
            failures.append("invalid %s unexpectedly accepted" % vector["name"])

    if failures:
        print("\n".join(failures))
        return 1
    print("PASS: %d valid vectors accepted; %d invalid vectors rejected; %d operation schemas loaded." %
          (len(valid), len(invalid), len(operations)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
