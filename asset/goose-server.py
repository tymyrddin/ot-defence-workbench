#!/usr/bin/env python3
"""GOOSE subscriber: receives EtherType 0x88B8 frames and echoes a reply
to the sender's unicast MAC. The echo gives check scripts a positive signal
that the frame got through; without it GOOSE is fire-and-forget and checks
have no way to distinguish pass from silent drop.
"""
import socket
import struct

GOOSE_ETHERTYPE = 0x88B8
IFACE = "eth1"


def get_mac(iface):
    return bytes(
        int(b, 16) for b in
        open(f"/sys/class/net/{iface}/address").read().strip().split(":")
    )


def main():
    my_mac = get_mac(IFACE)
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(GOOSE_ETHERTYPE))
    s.bind((IFACE, 0))
    while True:
        frame, _ = s.recvfrom(65535)
        sender = frame[6:12]
        if sender == my_mac:
            continue
        reply = sender + my_mac + struct.pack("!H", GOOSE_ETHERTYPE) + frame[14:]
        s.send(reply)


if __name__ == "__main__":
    main()
