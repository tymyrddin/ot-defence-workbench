#!/usr/bin/env sh
set -e
# Addresses:
#   boundary north 10.0.1.1/24   south 10.0.2.1/24
#   client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10

iptables -F FORWARD
iptables -t nat -F PREROUTING
iptables -t nat -F POSTROUTING
iptables -P FORWARD ACCEPT

# Discover probe MAC: send a UDP datagram to trigger kernel ARP resolution,
# then read the neighbour table from /proc/net/arp. Retried up to 5 times.
PROBE_MAC=$(python3 - <<'PYEOF'
import socket, time, sys

for _ in range(5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('10.0.1.20', 9))
        s.send(b'\x00')
        s.close()
    except Exception:
        pass
    time.sleep(0.4)
    try:
        with open('/proc/net/arp') as f:
            for line in f:
                parts = line.split()
                if (len(parts) >= 4 and parts[0] == '10.0.1.20'
                        and parts[3] != '00:00:00:00:00:00'):
                    print(parts[3])
                    sys.exit(0)
    except Exception:
        pass

sys.exit(1)
PYEOF
)

if [ -z "$PROBE_MAC" ]; then
    echo "goose-block-probe: could not resolve probe MAC, block not set" >&2
    exit 1
fi
echo "$PROBE_MAC" > /tmp/goose-blocked
