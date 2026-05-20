#!/usr/bin/env sh
set -e
# Addresses:
#   boundary north 10.0.1.1/24   south 10.0.2.1/24
#   client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10:2404

iptables -F FORWARD
iptables -P FORWARD DROP

# No source restriction: the boundary passes all IEC 104 traffic.
# The defence is at the asset (SA MAC validation), not at the boundary.
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -d 10.0.2.10 -p tcp --dport 2404 -j ACCEPT
