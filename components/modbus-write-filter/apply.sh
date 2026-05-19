#!/usr/bin/env sh
set -e
# Addresses:
#   boundary north 10.0.1.1/24   south 10.0.2.1/24
#   client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10:502

iptables -F FORWARD
iptables -P FORWARD DROP

# Block Modbus write function codes before any ACCEPT rule.
# The u32 expression resolves the variable-length IP and TCP headers,
# then reads the function code byte at Modbus MBAP offset 7.
#   FC05 = write single coil
#   FC06 = write single register
#   FC15 = write multiple coils
#   FC16 = write multiple registers
for fc in 5 6 0x0F 0x10; do
    iptables -A FORWARD -p tcp --dport 502 \
        -m u32 --u32 "0>>22&0x3C@12>>26&0x3C@7>>24&0xFF=$fc" -j DROP
done

iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Redirect all north-side port 502 connections to the asset
iptables -t nat -F PREROUTING
iptables -t nat -F POSTROUTING
iptables -t nat -A PREROUTING -i eth1 -p tcp --dport 502 -j DNAT --to-destination 10.0.2.10:502
iptables -t nat -A POSTROUTING -o eth2 -j MASQUERADE

# Allow DNAT'd traffic (originally addressed to the boundary)
iptables -A FORWARD -i eth1 -o eth2 -p tcp --dport 502 -m conntrack --ctorigdst 10.0.1.1 -j ACCEPT
