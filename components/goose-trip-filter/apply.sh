#!/usr/bin/env sh
set -e
# boundary north eth1  10.0.1.1/24   south eth2  10.0.2.1/24
# client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10
# Boundary transparent — trip filtering is done by the relay daemon.

iptables -F FORWARD
iptables -t nat -F PREROUTING
iptables -t nat -F POSTROUTING
iptables -P FORWARD ACCEPT

# Signal the relay to filter GOOSE frames whose allData is BOOLEAN TRUE.
touch /tmp/goose-trip-filter
