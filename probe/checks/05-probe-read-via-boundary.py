#!/usr/bin/env python3
"""Probe reads from the boundary proxy using its own source address."""
import sys
from pymodbus.client import ModbusTcpClient

c = ModbusTcpClient("10.0.1.1", port=502, timeout=2)
if not c.connect():
    sys.exit(1)
try:
    r = c.read_holding_registers(0, 1)
    sys.exit(0 if not r.isError() else 1)
finally:
    c.close()
