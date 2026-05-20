#!/usr/bin/env python3
import asyncio
import sys

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256


async def run():
    client = Client("opc.tcp://10.0.2.10:4840/", timeout=5)
    client.application_uri = "urn:ot-workbench:client"
    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate="/app/pki/client.pem",
        private_key="/app/pki/client-key.pem",
        mode=ua.MessageSecurityMode.Sign,
    )
    try:
        async with client:
            await client.nodes.root.get_children()
            return 0
    except Exception:
        return 1


sys.exit(asyncio.run(run()))
