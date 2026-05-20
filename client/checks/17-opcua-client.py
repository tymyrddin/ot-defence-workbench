#!/usr/bin/env python3
import asyncio, sys
from asyncua import Client


async def run():
    try:
        async with Client("opc.tcp://10.0.2.10:4840/", timeout=3) as client:
            await client.nodes.root.get_children()
            return 0
    except Exception:
        return 1


sys.exit(asyncio.run(run()))
