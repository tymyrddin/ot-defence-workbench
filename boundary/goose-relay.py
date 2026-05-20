#!/usr/bin/env python3
"""GOOSE Layer 2 relay between eth1 (north) and eth2 (south).

GOOSE (EtherType 0x88B8) is a multicast protocol with no IP header.
It cannot be routed; this relay bridges it explicitly between segments.
/tmp/goose-blocked lists source MACs (one per line) to drop silently.
"""
import socket
import threading

GOOSE_ETHERTYPE = 0x88B8
BLOCK_FILE = "/tmp/goose-blocked"


def blocked_macs():
    try:
        return {m.strip().lower() for m in open(BLOCK_FILE) if m.strip()}
    except FileNotFoundError:
        return set()


def src_mac(frame):
    return ':'.join(f'{b:02x}' for b in frame[6:12])


def relay(src_iface, dst_iface):
    rx = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(GOOSE_ETHERTYPE))
    rx.bind((src_iface, 0))
    tx = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(GOOSE_ETHERTYPE))
    tx.bind((dst_iface, 0))
    while True:
        frame, _ = rx.recvfrom(65535)
        if src_mac(frame) not in blocked_macs():
            try:
                tx.send(frame)
            except OSError:
                pass


threading.Thread(target=relay, args=("eth1", "eth2"), daemon=True).start()
relay("eth2", "eth1")
