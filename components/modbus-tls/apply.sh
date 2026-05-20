#!/usr/bin/env sh
set -e
# boundary north eth1  10.0.1.1/24   south eth2  10.0.2.1/24
# client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10

iptables -F FORWARD
iptables -t nat -F PREROUTING
iptables -t nat -F POSTROUTING
iptables -P FORWARD DROP

# Only the client may reach Modbus/TLS on port 802
iptables -A FORWARD -s 10.0.1.10 -d 10.0.2.10 -p tcp --dport 802 -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
