#!/usr/bin/env sh
set -e
# Addresses:
#   boundary north 10.0.1.1/24   south 10.0.2.1/24
#   client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10:2404

iptables -F FORWARD
iptables -P FORWARD DROP

# Reject C_SC_NA_1 (type ID 0x2D) before ESTABLISHED,RELATED.
# The u32 expression navigates the IP and TCP headers then reads byte 6 of the
# TCP payload — the ASDU type ID. This rule must precede ESTABLISHED,RELATED
# so commands on already-established sessions (post-STARTDT) are still caught.
iptables -A FORWARD -p tcp --dport 2404 \
    -m u32 --u32 "0>>22&0x3C@12>>26&0x3C@6>>24&0xFF=0x2D" \
    -j REJECT --reject-with tcp-reset

iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -d 10.0.2.10 -p tcp --dport 2404 -j ACCEPT
