#!/usr/bin/env sh
set -e
# Addresses:
#   boundary north 10.0.1.1/24   south 10.0.2.1/24
#   client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10

iptables -F FORWARD
iptables -t nat -F PREROUTING
iptables -t nat -F POSTROUTING
iptables -P FORWARD DROP

# Return traffic for existing sessions is never affected.
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Drop new TCP connections from any source that exceeds 3 per minute.
# Each source IP has its own token bucket (hashlimit-mode srcip), so the
# probe's rapid-fire attempts deplete its bucket while the client's
# separate bucket remains full.
iptables -A FORWARD -p tcp -m conntrack --ctstate NEW \
  -m hashlimit \
  --hashlimit-name ot-conn-rate \
  --hashlimit-above 3/minute \
  --hashlimit-mode srcip \
  --hashlimit-burst 3 \
  -j DROP

# New connections within the rate limit pass through.
iptables -A FORWARD -p tcp -m conntrack --ctstate NEW -j ACCEPT
