#!/usr/bin/env sh
set -e
pkill mosquitto || true
sleep 0.3
mosquitto -c /app/mosquitto.conf &
