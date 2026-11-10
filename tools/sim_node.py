#!/usr/bin/env python3
"""Run a local WebSocket fleet of DCP simulator nodes."""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator
from websockets.asyncio.server import serve
from tools.validate_pins import evaluate, load_profile

PROTOCOL_DIR = ROOT / "protocol"
MAX_MESSAGE_BYTES = 4096
CAPABILITIES = ["sys.info", "sys.ping", "gpio.mode", "gpio.read", "gpio.write"]

class SimNode:
    def __init__(self, node_id, profile, wifi_active=False):
        self.node_id = node_id
        self.address = "node:%d" % node_id
        self.group = "sim"
        self.tags = ("sim",)
        self.cell = "sim-cell"
        self.profile = profile
        self.wifi_active = wifi_active
        self.started = time.monotonic()
        self.pin_modes = {}
        self.pin_values = {}

    def error(self, request, code, message):
        return {
            "v": "1.0", "id": request["id"], "src": self.address,
            "dst": request["src"], "t": "res", "op": request["op"],
            "args": {"error": {"code": code, "message": message, "details": {}}},
        }

    def _pin_decision(self, pin, action, mode=None, confirm=False):
        decision = evaluate(self.profile, pin, action, mode=mode,
                            confirm=confirm, wifi_active=self.wifi_active)
        if decision["status"] == "block":
            return "E_PIN_BLOCKED", decision["reason"]
        if decision["status"] == "warn":
            return "E_CONFIRM_REQUIRED", decision["reason"]
        return None

    def handle(self, request):
        op = request["op"]
        args = request["args"]
        if op == "sys.info":
            response = {"firmware": "simulator-1.0", "hardware": "ESP32",
                        "capabilities": CAPABILITIES}
        elif op == "sys.ping":
            response = {"uptime_ms": int((time.monotonic() - self.started) * 1000)}
            if "token" in args:
                response["token"] = args["token"]
        elif op == "gpio.mode":
            pin, mode = args["pin"], args["mode"]
            error = self._pin_decision(pin, "mode", mode, args.get("confirm", False))
            if error:
                return self.error(request, error[0], error[1])
            self.pin_modes[pin] = mode
            response = {"pin": pin, "mode": mode}
        elif op == "gpio.read":
            pin = args["pin"]
            mode = self.pin_modes.get(pin, "input")
            error = self._pin_decision(pin, "mode", mode)
            if error:
                return self.error(request, error[0], error[1])
            response = {"pin": pin, "value": self.pin_values.get(pin, 0)}
        elif op == "gpio.write":
            pin, value = args["pin"], args["value"]
            error = self._pin_decision(pin, "write", confirm=args.get("confirm", False))
            if error:
                return self.error(request, error[0], error[1])
            if self.pin_modes.get(pin) != "output":
                return self.error(request, "E_INVALID_ARG", "pin must be configured as output before writing")
            self.pin_values[pin] = value
            response = {"pin": pin, "value": value}
        else:
            return self.error(request, "E_UNSUPPORTED", "operation is not implemented by simulator")
        return {"v": "1.0", "id": request["id"], "src": self.address,
                "dst": request["src"], "t": "res", "op": op, "args": response}

class Simulator:
    def __init__(self, count=1, base_id=1, wifi_active=False):
        if count < 1:
            raise ValueError("count must be at least 1")
        self.profile = load_profile()
        self.nodes = {
            node_id: SimNode(node_id, self.profile, wifi_active)
            for node_id in range(base_id, base_id + count)
        }
        self.envelope_validator = Draft202012Validator(
            json.loads((PROTOCOL_DIR / "schema" / "message.schema.json").read_text(encoding="utf-8"))
        )
        self.operations = json.loads((PROTOCOL_DIR / "ops.json").read_text(encoding="utf-8"))["operations"]
        self.request_validators = {
            name: Draft202012Validator(spec["request"])
            for name, spec in self.operations.items()
        }

    def validate(self, message):
        errors = list(self.envelope_validator.iter_errors(message))
        if errors:
            return False, "E_BAD_MESSAGE", errors[0].message
        if message["t"] != "req":
            return False, "E_BAD_MESSAGE", "simulator accepts request messages only"
        operation = self.request_validators.get(message["op"])
        if operation is None:
            return False, "E_UNSUPPORTED", "unknown operation"
        errors = list(operation.iter_errors(message["args"]))
        if errors:
            return False, "E_INVALID_ARG", errors[0].message
        return True, None, None

    def validate_vector(self, message):
        errors = list(self.envelope_validator.iter_errors(message))
        if errors:
            return False, errors[0].message
        operation = self.operations.get(message["op"])
        if operation is None:
            return False, "unknown operation"
        if message["t"] == "req":
            contract = operation["request"]
        elif message["t"] == "res" and "error" not in message["args"]:
            contract = operation["response"]
        elif message["t"] in ("res", "evt"):
            return True, None
        else:
            return False, "unsupported message type"
        errors = list(Draft202012Validator(contract).iter_errors(message["args"]))
        return (False, errors[0].message) if errors else (True, None)

    def resolve(self, destination):
        if destination == "*":
            return list(self.nodes.values())
        if destination.startswith("node:"):
            try:
                node = self.nodes.get(int(destination[5:]))
            except ValueError:
                node = None
            return [node] if node is not None else []
        if destination == "group:sim":
            return [node for node in self.nodes.values() if node.group == "sim"]
        if destination == "tag:sim":
            return [node for node in self.nodes.values() if "sim" in node.tags]
        if destination == "cell:sim-cell":
            return [node for node in self.nodes.values() if node.cell == "sim-cell"]
        return []

    def handle_message(self, message):
        valid, code, reason = self.validate(message)
        if not valid:
            return []
        targets = self.resolve(message["dst"])
        if not targets:
            # The first simulated node acts as the local router for selector errors.
            router = next(iter(self.nodes.values()))
            return [router.error(message, "E_NOT_FOUND", "destination did not resolve to a simulated node")]
        return [node.handle(message) for node in targets]

    async def websocket_handler(self, websocket):
        async for raw in websocket:
            try:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                if len(raw.encode("utf-8")) > MAX_MESSAGE_BYTES:
                    await websocket.close(code=1009, reason="DCP message exceeds 4096 bytes")
                    return
                message = json.loads(raw)
            except (UnicodeError, ValueError, TypeError):
                await websocket.close(code=1003, reason="invalid DCP JSON")
                return
            valid, code, reason = self.validate(message) if isinstance(message, dict) else (False, "E_BAD_MESSAGE", "message must be an object")
            if not valid:
                await websocket.close(code=1008, reason=reason[:120])
                return
            for response in self.handle_message(message):
                await websocket.send(json.dumps(response, separators=(",", ":")))

async def run_server(count=1, host="127.0.0.1", port=8765, base_id=1, wifi_active=False):
    simulator = Simulator(count, base_id, wifi_active)
    async with serve(simulator.websocket_handler, host, port, max_size=MAX_MESSAGE_BYTES,
                     compression=None, ping_interval=20, ping_timeout=20, close_timeout=5):
        print("Started %d simulated nodes at ws://%s:%d" % (count, host, port))
        await asyncio.Future()

def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=positive_int, default=1, help="number of simulated nodes")
    parser.add_argument("--base-id", type=positive_int, default=1, help="first numeric node ID")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--wifi-active", action="store_true", help="make ADC2 unavailable")
    args = parser.parse_args()
    asyncio.run(run_server(args.count, args.host, args.port, args.base_id, args.wifi_active))

if __name__ == "__main__":
    main()
