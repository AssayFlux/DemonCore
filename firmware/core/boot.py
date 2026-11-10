"""MicroPython boot entry point. Run before main.py."""
from core.state import prepare_boot

BOOT_STATE = prepare_boot()
