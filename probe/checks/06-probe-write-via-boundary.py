#!/usr/bin/env python3
"""Probe attempts a Modbus register write via the boundary proxy."""
import sys
from pymodbus.client import ModbusTcpClient

c = ModbusTcpClient("10.0.1.1", port=502, timeout=3)
if not c.connect():
    sys.exit(1)
try:
    r = c.write_register(0, 42)
    sys.exit(0 if not r.isError() else 1)
finally:
    c.close()
