#!/usr/bin/env sh
touch /app/opcua-sec-policy-mode
pkill -f "opcua-server.py" || true
sleep 0.3
python3 /app/opcua-server.py &
