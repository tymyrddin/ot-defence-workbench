import sys
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient("10.0.2.10", port=502, timeout=2)
if not client.connect():
    print("ERROR: could not connect to asset")
    sys.exit(1)
result = client.read_holding_registers(0, 10)
client.close()
if result.isError():
    print("ERROR: read failed")
    sys.exit(1)
print(f"OK: {result.registers}")