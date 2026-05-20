#!/usr/bin/env sh
set -e

i=0
while ! ip link show eth1 > /dev/null 2>&1; do
    i=$((i+1))
    [ $i -ge 60 ] && { echo "timeout waiting for eth1" >&2; exit 1; }
    sleep 0.5
done

ip addr add 10.0.2.10/24 dev eth1
ip link set eth1 up
ip route add default via 10.0.2.1

mosquitto -c /app/mosquitto.conf &
python3 /app/goose-server.py &
python3 /app/iec104-server.py &
python3 /app/modbus-tls-server.py &
exec python3 /app/server.py