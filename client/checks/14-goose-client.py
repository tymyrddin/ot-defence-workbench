#!/usr/bin/env python3
# Client sends an IEC 61850 GOOSE frame and waits for the asset's echo.
# The client's source MAC is not in the relay block list; this check
# confirms the authorised sender can still reach the asset.
import socket, struct, sys, time

GOOSE_ETHERTYPE = 0x88B8
GOOSE_DST = bytes([0x01, 0x0C, 0xCD, 0x01, 0x00, 0x01])


def iface_mac(iface):
    return bytes(
        int(b, 16) for b in
        open(f"/sys/class/net/{iface}/address").read().strip().split(":")
    )


def goose_frame(src_mac):
    eth = GOOSE_DST + src_mac + struct.pack("!H", GOOSE_ETHERTYPE)
    asdu = bytes([
        0x61, 0x0E,
        0x85, 0x01, 0x01,
        0x86, 0x01, 0x00,
        0x8A, 0x01, 0x01,
        0xAB, 0x03, 0x83, 0x01, 0x01,
    ])
    hdr = struct.pack("!HH4x", 0x0000, 8 + len(asdu))
    return eth + hdr + asdu


try:
    src = iface_mac("eth1")
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(GOOSE_ETHERTYPE))
    s.bind(("eth1", 0))
    s.settimeout(3)
    s.send(goose_frame(src))
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        try:
            reply, _ = s.recvfrom(65535)
            if reply[0:6] == src and reply[6:12] != src:
                sys.exit(0)
        except socket.timeout:
            break
    sys.exit(1)
except OSError:
    sys.exit(1)
