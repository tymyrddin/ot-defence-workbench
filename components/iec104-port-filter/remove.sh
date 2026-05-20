#!/usr/bin/env sh
set -e
iptables -F FORWARD
iptables -P FORWARD ACCEPT