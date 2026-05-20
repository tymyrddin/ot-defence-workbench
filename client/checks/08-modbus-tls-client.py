#!/usr/bin/env python3
import asyncio, ssl, sys
from pymodbus.client import AsyncModbusTlsClient


async def run():
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    client = AsyncModbusTlsClient("10.0.2.10", port=802, sslctx=ctx)
    connected = await client.connect()
    if not connected:
        return 1
    result = await client.read_holding_registers(0, count=1, slave=1)
    client.close()
    return 0 if not result.isError() else 1


sys.exit(asyncio.run(run()))
