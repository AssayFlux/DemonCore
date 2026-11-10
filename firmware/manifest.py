# DemonCore MicroPython frozen-module manifest.
freeze("$(PORT_DIR)/modules")
include("$(MPY_DIR)/extmod/asyncio")
module("boot.py", base_path="core")
module("main.py", base_path="core")
freeze("core")
