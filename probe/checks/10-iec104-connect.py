#!/usr/bin/env python3
import socket, sys

try:
    s = socket.create_connection(("10.0.2.10", 2404), timeout=2)
    s.close()
    sys.exit(0)
except OSError:
    sys.exit(1)