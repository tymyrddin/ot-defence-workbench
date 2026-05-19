#!/usr/bin/env python3
import sys
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("10.0.2.10", port=502, timeout=2)
if not client.connect():
    sys.exit(1)
result = client.read_holding_registers(0, 1)
client.close()
sys.exit(0 if not result.isError() else 1)