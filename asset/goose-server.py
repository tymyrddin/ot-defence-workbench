#!/usr/bin/env python3
"""GOOSE subscriber: receives EtherType 0x88B8 frames and echoes a reply
to the sender's unicast MAC. The echo gives check scripts a positive signal
that the frame got through; without it GOOSE is fire-and-forget and checks
have no way to distinguish pass from silent drop.

SA mode (IEC 62351-6 simplified): when /app/goose-sa-mode exists, the server
expects a 4-byte HMAC-SHA256 MAC appended after the GOOSE PDU. Frames with
no MAC or an invalid MAC are silently dropped (no echo).
"""
import hashlib
import hmac
import os
import socket
import struct

GOOSE_ETHERTYPE = 0x88B8
IFACE = "eth1"
SA_FLAG = "/app/goose-sa-mode"
SA_KEY = b"ot-workbench-goose-sa"
SA_MAC_LEN = 4


def get_mac(iface):
    return bytes(
        int(b, 16) for b in
        open(f"/sys/class/net/{iface}/address").read().strip().split(":")
    )


def validate_mac(frame):
    """Check HMAC appended after the GOOSE PDU.

    The GOOSE Length field (frame[16:18]) covers the 8-byte header plus PDU.
    A signed frame is exactly Length+14+SA_MAC_LEN bytes long.
    Returns (valid: bool, clean_frame: bytes without the appended MAC).
    """
    goose_len = struct.unpack("!H", frame[16:18])[0]
    expected_total = 14 + goose_len
    if len(frame) != expected_total + SA_MAC_LEN:
        return False, frame
    pdu = frame[22:expected_total]
    mac_recv = frame[expected_total:]
    mac_exp = hmac.new(SA_KEY, pdu, hashlib.sha256).digest()[:SA_MAC_LEN]
    return hmac.compare_digest(mac_recv, mac_exp), frame[:expected_total]


def main():
    my_mac = get_mac(IFACE)
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(GOOSE_ETHERTYPE))
    s.bind((IFACE, 0))
    while True:
        frame, _ = s.recvfrom(65535)
        sender = frame[6:12]
        if sender == my_mac:
            continue
        if os.path.exists(SA_FLAG):
            valid, frame = validate_mac(frame)
            if not valid:
                continue
        reply = sender + my_mac + struct.pack("!H", GOOSE_ETHERTYPE) + frame[14:]
        s.send(reply)


if __name__ == "__main__":
    main()
