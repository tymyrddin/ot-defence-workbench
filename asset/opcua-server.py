#!/usr/bin/env python3
import asyncio
import os

from asyncua import Server, ua
from asyncua.server.user_managers import UserManager, User, UserRole

AUTH_FLAG = "/app/opcua-auth-mode"
SEC_POLICY_FLAG = "/app/opcua-sec-policy-mode"
CRED_USER = "ot-client"
CRED_PASS = "ot-workbench-opcua-pass"


class ConditionalAuth(UserManager):
    def get_user(self, iserver, username=None, password=None, certificate=None):
        if os.path.exists(AUTH_FLAG):
            if username == CRED_USER and password in (CRED_PASS, CRED_PASS.encode()):
                return User(role=UserRole.User)
            return None
        return User(role=UserRole.User)


async def main():
    server = Server(user_manager=ConditionalAuth())
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/")

    if os.path.exists(SEC_POLICY_FLAG):
        server.set_security_policy([ua.SecurityPolicyType.Basic256Sha256_Sign])
        await server.load_certificate("/app/tls/server.crt", format="pem")
        await server.load_private_key("/app/tls/server.key", format="pem")
    else:
        server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    idx = await server.register_namespace("urn:ot-workbench:asset")
    obj = await server.nodes.objects.add_object(idx, "Plant")
    var = await obj.add_variable(idx, "Temperature", 100.0)
    await var.set_writable()

    async with server:
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
