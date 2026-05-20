#!/usr/bin/env python3
"""Rapid-fire connection check. Makes 10 TCP connections to port 502 as fast
as possible. Under a per-source-IP rate limit with burst 3, only the first 3
succeed; the rest are silently dropped and time out. Exits 1 (block) if fewer
than 5 succeeded, 0 (pass) otherwise."""
import socket
import sys

TARGET = ("10.0.2.10", 502)
ATTEMPTS = 10
THRESHOLD = 5

successes = 0
for _ in range(ATTEMPTS):
    try:
        s = socket.create_connection(TARGET, timeout=0.5)
        s.close()
        successes += 1
    except OSError:
        pass

sys.exit(0 if successes >= THRESHOLD else 1)
