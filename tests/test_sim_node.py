import asyncio
import json
import unittest
from pathlib import Path

from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from tools.sim_node import Simulator

ROOT = Path(__file__).resolve().parents[1]

class SimulatorTests(unittest.TestCase):
    def test_all_shared_vectors(self):
        sim = Simulator(2)
        valid = json.loads((ROOT / "protocol" / "vectors" / "valid.json").read_text())
        invalid = json.loads((ROOT / "protocol" / "vectors" / "invalid.json").read_text())
        for vector in valid:
            ok, _, _ = sim.validate(vector["message"])
            self.assertTrue(ok, vector["name"])
        for vector in invalid:
            ok, _, _ = sim.validate(vector["message"])
            self.assertFalse(ok, vector["name"])

    def test_gpio_policy_is_enforced(self):
        sim = Simulator(1)
        request = {"v":"1.0","id":"0000000000000001","src":"node:1","dst":"node:1","t":"req","op":"gpio.mode","args":{"pin":6,"mode":"output"}}
        reply = sim.handle_message(request)[0]
        self.assertEqual(reply["args"]["error"]["code"], "E_PIN_BLOCKED")
        request["id"] = "0000000000000002"
        request["args"] = {"pin":5,"mode":"output"}
        reply = sim.handle_message(request)[0]
        self.assertEqual(reply["args"]["error"]["code"], "E_CONFIRM_REQUIRED")
        request["id"] = "0000000000000003"
        request["args"] = {"pin":5,"mode":"output","confirm":True}
        self.assertEqual(sim.handle_message(request)[0]["args"]["mode"], "output")

    def test_100_nodes_over_websocket(self):
        async def exercise():
            sim = Simulator(100)
            async with serve(sim.websocket_handler, "127.0.0.1", 0, max_size=4096, compression=None) as server:
                port = server.sockets[0].getsockname()[1]
                async with connect("ws://127.0.0.1:%d" % port, max_size=4096, compression=None) as ws:
                    seen = set()
                    for node_id in range(1, 101):
                        request = {"v":"1.0","id":"%016x" % node_id,"src":"node:100","dst":"node:%d" % node_id,"t":"req","op":"sys.info","args":{}}
                        await ws.send(json.dumps(request))
                        response = json.loads(await ws.recv())
                        self.assertEqual(response["src"], "node:%d" % node_id)
                        self.assertEqual(response["args"]["hardware"], "ESP32")
                        seen.add(response["src"])
                    self.assertEqual(len(seen), 100)
        asyncio.run(exercise())

    def test_wildcard_resolves_all_nodes(self):
        sim = Simulator(5)
        request = {"v":"1.0","id":"0000000000000001","src":"node:1","dst":"*","t":"req","op":"sys.ping","args":{}}
        self.assertEqual(len(sim.handle_message(request)), 5)

if __name__ == "__main__":
    unittest.main()
