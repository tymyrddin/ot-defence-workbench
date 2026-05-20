#!/usr/bin/env python3
# Client sends C_SC_NA_1 authenticated with a truncated HMAC-SHA256 MAC.
# The asset accepts it when SA mode is active; the probe's unauthenticated
# send (check 12) is rejected. Same port, same command, different key.
import hashlib, hmac, socket, sys

STARTDT_ACT = bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00])
STARTDT_CON = bytes([0x68, 0x04, 0x0B, 0x00, 0x00, 0x00])

SA_KEY = b"ot-workbench-iec104-sa"
SA_MAC_LEN = 4

# ASDU: C_SC_NA_1 (type 45), 1 object, COT activation, CA 1, IOA 1, SCO ON
ASDU = bytes([0x2D, 0x01, 0x06, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x01])
mac4 = hmac.new(SA_KEY, ASDU, hashlib.sha256).digest()[:SA_MAC_LEN]

# APDU length = CF(4) + ASDU(10) + MAC(4) = 18 = 0x12
SA_TRIP_CMD = bytes([0x68, 0x12, 0x00, 0x00, 0x00, 0x00]) + ASDU + mac4

try:
    s = socket.create_connection(("10.0.2.10", 2404), timeout=3)
    s.sendall(STARTDT_ACT)
    resp = s.recv(6)
    if resp != STARTDT_CON:
        s.close()
        sys.exit(1)
    s.settimeout(3)
    s.sendall(SA_TRIP_CMD)
    try:
        ack = s.recv(6)
        s.close()
        sys.exit(0 if (ack and ack[0] == 0x68) else 1)
    except OSError:
        sys.exit(1)
except OSError:
    sys.exit(1)
