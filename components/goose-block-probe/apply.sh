#!/usr/bin/env sh
set -e
# Addresses:
#   boundary north 10.0.1.1/24   south 10.0.2.1/24
#   client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10

iptables -F FORWARD
iptables -P FORWARD ACCEPT

# Block probe's GOOSE at the Layer 2 relay.
# GOOSE has no IP header; filtering is MAC-based. Discover the probe's
# MAC via ARP (ping to populate the neighbour table first).
ping -c 2 -W 1 10.0.1.20 >/dev/null 2>&1 || true
PROBE_MAC=$(ip neigh show 10.0.1.20 | awk 'NR==1{print $5}')
echo "${PROBE_MAC:-aa:c1:ab:fc:51:6b}" > /tmp/goose-blocked
