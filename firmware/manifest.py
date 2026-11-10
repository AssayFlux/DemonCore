# DemonCore MicroPython frozen-module manifest.
freeze("$(PORT_DIR)/modules")
include("$(MPY_DIR)/extmod/asyncio")
freeze("core")
