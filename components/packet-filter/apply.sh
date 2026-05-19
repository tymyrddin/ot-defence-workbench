#!/usr/bin/env sh
set -e
iptables -F FORWARD
iptables -P FORWARD DROP
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -s 10.0.1.10 -d 10.0.2.10 -p tcp --dport 502 -j ACCEPT