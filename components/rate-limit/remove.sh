#!/usr/bin/env sh
set -e
iptables -F FORWARD
iptables -t nat -F PREROUTING
iptables -t nat -F POSTROUTING
iptables -P FORWARD ACCEPT
