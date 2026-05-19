#!/usr/bin/env python3
# Does the probe reach the asset on a non-Modbus port?
#
# A packet-filter that drops all forward traffic from the probe blocks this.
# A narrower rule that only blocks port 502 would not — the host stays reachable.
# This check surfaces that gap: port-specific rules are not the same as host-level blocks.
import socket
import sys

TARGET = "10.0.2.10"
PORT = 80

try:
    s = socket.create_connection((TARGET, PORT), timeout=2)
    s.close()
    sys.exit(0)
except ConnectionRefusedError:
    # Port closed but host answered — host is reachable, just no service on port 80.
    sys.exit(0)
except OSError:
    sys.exit(1)