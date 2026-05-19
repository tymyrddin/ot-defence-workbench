#!/usr/bin/env sh
set -e
# Addresses:
#   boundary north 10.0.1.1/24   south 10.0.2.1/24
#   client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10:502

# Block all direct north-to-south forwarding
iptables -F FORWARD
iptables -P FORWARD DROP
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# DNAT only connections from the client's address to the asset
iptables -t nat -F PREROUTING
iptables -t nat -F POSTROUTING
iptables -t nat -A PREROUTING -i eth1 -s 10.0.1.10 -p tcp --dport 502 -j DNAT --to-destination 10.0.2.10:502
iptables -t nat -A POSTROUTING -o eth2 -j MASQUERADE

# Allow only DNAT'd traffic (originally addressed to the boundary from the client)
iptables -A FORWARD -i eth1 -o eth2 -p tcp --dport 502 -m conntrack --ctorigdst 10.0.1.1 -j ACCEPT
