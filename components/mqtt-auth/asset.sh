#!/usr/bin/env sh
set -e
mosquitto_passwd -c -b /tmp/mqtt.passwd ot-client ot-workbench-mqtt-pass
chmod 644 /tmp/mqtt.passwd
printf 'listener 1883\nallow_anonymous false\npassword_file /tmp/mqtt.passwd\n' \
    > /tmp/mosquitto-auth.conf
pkill mosquitto || true
sleep 0.3
mosquitto -c /tmp/mosquitto-auth.conf &
