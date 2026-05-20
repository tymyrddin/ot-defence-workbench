#!/usr/bin/env python3
import asyncio, sys
from asyncua import Client

CRED_USER = "ot-client"
CRED_PASS = "ot-workbench-opcua-pass"


async def run():
    client = Client("opc.tcp://10.0.2.10:4840/", timeout=3)
    client.set_user(CRED_USER)
    client.set_password(CRED_PASS)
    try:
        async with client:
            await client.nodes.root.get_children()
            return 0
    except Exception:
        return 1


sys.exit(asyncio.run(run()))
