#!/usr/bin/env sh
rm -f /app/opcua-sec-policy-mode
pkill -f "opcua-server.py" || true
sleep 0.3
python3 /app/opcua-server.py &
