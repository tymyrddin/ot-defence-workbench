#!/usr/bin/env python3
# <name>: describe what this probe checks.
# Exit 0 = reached / succeeded  →  result: pass
# Exit 1 = blocked  / failed    →  result: block
#
# Files whose names start with _ are not run by lab check.
# Copy this file, give it a real name, then edit the check.
import sys
from pymodbus.client import ModbusTcpClient

TARGET = "10.0.2.10"
PORT = 502

client = ModbusTcpClient(TARGET, port=PORT, timeout=2)
if not client.connect():
    sys.exit(1)

# Replace with the operation you want to test.
result = client.read_holding_registers(0, 1)
client.close()

sys.exit(0 if not result.isError() else 1)