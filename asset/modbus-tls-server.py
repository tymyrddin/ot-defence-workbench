#!/usr/bin/env python3
import asyncio
from pymodbus.server import StartAsyncTlsServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext


def build_context():
    store = ModbusSlaveContext(hr=ModbusSequentialDataBlock(0, [17] * 100))
    return ModbusServerContext(slaves=store, single=True)


async def main():
    await StartAsyncTlsServer(
        context=build_context(),
        certfile="/app/tls/server.crt",
        keyfile="/app/tls/server.key",
        address=("0.0.0.0", 802),
    )


if __name__ == "__main__":
    asyncio.run(main())
