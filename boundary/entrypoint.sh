#!/usr/bin/env sh
set -e

_wait() {
    local iface="$1" i=0
    while ! ip link show "$iface" > /dev/null 2>&1; do
        i=$((i+1))
        [ $i -ge 60 ] && { echo "timeout waiting for $iface" >&2; exit 1; }
        sleep 0.5
    done
}

_wait eth1
_wait eth2

ip addr add 10.0.1.1/24 dev eth1
ip addr add 10.0.2.1/24 dev eth2
ip link set eth1 up
ip link set eth2 up

echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -P FORWARD ACCEPT

exec "$@"