#!/usr/bin/env python3
import socket, sys

STARTDT_ACT = bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00])
STARTDT_CON = bytes([0x68, 0x04, 0x0B, 0x00, 0x00, 0x00])

try:
    s = socket.create_connection(("10.0.2.10", 2404), timeout=3)
    s.sendall(STARTDT_ACT)
    resp = s.recv(6)
    s.close()
    sys.exit(0 if resp == STARTDT_CON else 1)
except OSError:
    sys.exit(1)