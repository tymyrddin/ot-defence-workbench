import asyncio
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext


def build_context():
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [17] * 100)
    )
    return ModbusServerContext(slaves=store, single=True)


async def main():
    await StartAsyncTcpServer(
        context=build_context(),
        address=("0.0.0.0", 502),
    )


if __name__ == "__main__":
    asyncio.run(main())