#!/usr/bin/env sh
set -e
iptables -F FORWARD
iptables -P FORWARD ACCEPT
iptables -t nat -F PREROUTING
iptables -t nat -F POSTROUTING
