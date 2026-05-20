#!/usr/bin/env python3
import socket, sys
import paho.mqtt.client as mqtt

socket.setdefaulttimeout(3)
published = [False]

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.publish("commands/valve", "OPEN", qos=1)
    else:
        client.disconnect()

def on_publish(client, userdata, mid):
    published[0] = True
    client.disconnect()

c = mqtt.Client()
c.on_connect = on_connect
c.on_publish = on_publish
try:
    c.connect("10.0.2.10", 1883, keepalive=5)
    c.loop_forever()
    sys.exit(0 if published[0] else 1)
except Exception:
    sys.exit(1)