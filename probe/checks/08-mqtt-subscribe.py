#!/usr/bin/env python3
import socket, sys
import paho.mqtt.client as mqtt

socket.setdefaulttimeout(3)
connected = [False]

def on_connect(client, userdata, flags, rc):
    connected[0] = (rc == 0)
    client.disconnect()

c = mqtt.Client()
c.on_connect = on_connect
try:
    c.connect("10.0.2.10", 1883, keepalive=5)
    c.loop_forever()
    sys.exit(0 if connected[0] else 1)
except Exception:
    sys.exit(1)