#!/usr/bin/env python3
"""Probe adopts the client's source address and attempts direct reach to the asset."""
import subprocess, socket, sys

subprocess.run(["ip", "addr", "add", "10.0.1.10/32", "dev", "eth1"],
               capture_output=True)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("10.0.1.10", 0))
    s.settimeout(2)
    s.connect(("10.0.2.10", 502))
    s.close()
    sys.exit(0)
except OSError:
    sys.exit(1)
finally:
    subprocess.run(["ip", "addr", "del", "10.0.1.10/32", "dev", "eth1"],
                   capture_output=True)
