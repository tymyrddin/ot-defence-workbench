#!/usr/bin/env sh
set -e
iptables -F FORWARD
iptables -P FORWARD ACCEPT
rm -f /tmp/goose-trip-filter
