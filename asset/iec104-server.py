#!/usr/bin/env python3
import hashlib
import hmac
import os
import socket
import sys
import threading

sys.path.insert(0, os.path.dirname(__file__))
from iec104frame import (
    read_apdu, is_iframe, make_s_frame,
    STARTDT_ACT, STARTDT_CON,
    TESTFR_ACT, TESTFR_CON,
)

SA_FLAG = "/app/sa-mode"
SA_KEY = b"ot-workbench-iec104-sa"
SA_MAC_LEN = 4


def _sa_mode():
    return os.path.exists(SA_FLAG)


def handle(conn):
    with conn:
        recv_sn = 0
        while True:
            apdu = read_apdu(conn)
            if apdu is None:
                break
            if apdu == STARTDT_ACT:
                conn.sendall(STARTDT_CON)
            elif apdu == TESTFR_ACT:
                conn.sendall(TESTFR_CON)
            elif is_iframe(apdu):
                if _sa_mode():
                    asdu_and_mac = apdu[6:]
                    if len(asdu_and_mac) <= SA_MAC_LEN:
                        return
                    asdu = asdu_and_mac[:-SA_MAC_LEN]
                    mac_recv = asdu_and_mac[-SA_MAC_LEN:]
                    mac_expected = hmac.new(SA_KEY, asdu, hashlib.sha256).digest()[:SA_MAC_LEN]
                    if not hmac.compare_digest(mac_recv, mac_expected):
                        return
                ssn = (apdu[2] >> 1) | (apdu[3] << 7)
                recv_sn = ssn + 1
                conn.sendall(make_s_frame(recv_sn))


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", 2404))
        s.listen()
        while True:
            conn, _ = s.accept()
            threading.Thread(target=handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
