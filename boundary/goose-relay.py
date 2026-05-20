#!/usr/bin/env python3
"""GOOSE Layer 2 relay between eth1 (north) and eth2 (south).

GOOSE (EtherType 0x88B8) is a multicast protocol with no IP header.
It cannot be routed; this relay bridges it explicitly between segments.

Two control files checked dynamically on each frame:
  /tmp/goose-blocked      — source MACs to drop (one per line)
  /tmp/goose-trip-filter  — if present, drop any frame whose allData first
                            entry is BOOLEAN TRUE (execute / trip command)
"""
import os
import socket
import struct
import threading

GOOSE_ETHERTYPE = 0x88B8
BLOCK_FILE = "/tmp/goose-blocked"
TRIP_FILTER_FILE = "/tmp/goose-trip-filter"


def blocked_macs():
    try:
        return {m.strip().lower() for m in open(BLOCK_FILE) if m.strip()}
    except FileNotFoundError:
        return set()


def src_mac(frame):
    return ':'.join(f'{b:02x}' for b in frame[6:12])


def is_trip_command(frame):
    """Return True if the GOOSE frame's allData first entry is BOOLEAN TRUE.

    Frame layout: Ethernet (14) + GOOSE header (8) + GOOSE PDU (BER).
    Walks the TLVs inside the GOOSE PDU looking for allData (tag 0xAB),
    then checks whether the first entry has value 0x01 (execute/trip).
    """
    if len(frame) < 38:
        return False
    pos = 22  # skip Ethernet header (14) + GOOSE app header (8)
    if frame[pos] != 0x61:  # GOOSE PDU tag
        return False
    pos += 1
    # Skip PDU length (BER short or long form)
    if pos >= len(frame):
        return False
    pdu_len_byte = frame[pos]
    pos += 1
    if pdu_len_byte & 0x80:
        pos += pdu_len_byte & 0x7F
    # Walk inner TLVs looking for allData (constructed context tag 11 = 0xAB)
    while pos + 2 <= len(frame):
        tag = frame[pos]; pos += 1
        tlen = frame[pos]; pos += 1
        if tlen & 0x80:
            n = tlen & 0x7F
            if pos + n > len(frame):
                return False
            tlen = int.from_bytes(frame[pos:pos + n], 'big')
            pos += n
        if tag == 0xAB:  # allData
            # First entry: tag 0x83 (BOOLEAN in GOOSE encoding), length 1, value
            return (pos + 3 <= len(frame)
                    and frame[pos] == 0x83
                    and frame[pos + 1] == 0x01
                    and frame[pos + 2] == 0x01)
        pos += tlen
    return False


def relay(src_iface, dst_iface):
    rx = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(GOOSE_ETHERTYPE))
    rx.bind((src_iface, 0))
    tx = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(GOOSE_ETHERTYPE))
    tx.bind((dst_iface, 0))
    while True:
        frame, _ = rx.recvfrom(65535)
        if src_mac(frame) in blocked_macs():
            continue
        if os.path.exists(TRIP_FILTER_FILE) and is_trip_command(frame):
            continue
        try:
            tx.send(frame)
        except OSError:
            pass


threading.Thread(target=relay, args=("eth1", "eth2"), daemon=True).start()
relay("eth2", "eth1")
