# Future briefs

Possible directions. Grouped by what they teach and what they require.

The ladder currently ends at brief 15 (goose-block-probe).

---

## Complete the GOOSE ladder

Brief 15 blocks the probe's GOOSE at the relay by source MAC — the port-level
analogue (compare brief 12). Two natural extensions follow the same three-layer
pattern already established for IEC 104.

**Brief 16: GOOSE trip filter**
The probe can send GOOSE frames; only trip commands are blocked. The relay
inspects the ASN.1 `allData` field: if the first entry is BOOLEAN TRUE (execute),
drop the frame; BOOLEAN FALSE (normal/cancel) passes. This is the GOOSE analogue
of brief 13 (IEC 104 type ID filter). Requires the relay to parse enough of the
GOOSE PDU to reach `allData` — about 20 lines of BER walking.

**Brief 17: GOOSE security authentication (IEC 62351-6)**
Boundary transparent; asset validates HMAC-SHA256 on received GOOSE frames.
Probe sends unsigned GOOSE → asset's `goose-server.py` finds no MAC, closes.
Client sends signed GOOSE → asset validates and echoes. Mechanically identical to
brief 14 (IEC 62351-5 SA for IEC 104): same `asset.sh` toggle pattern, same
shared-key HMAC approach. Completes the three-layer GOOSE story: relay MAC block
(15) → relay trip filter (16) → asset MAC validation (17).

---

## OPC-UA

OPC-UA (port 4840) is the dominant data exchange protocol in European manufacturing
and process industry. It has three security modes (None, Sign, SignAndEncrypt) and
three authentication methods (anonymous, username, certificate). A small ladder:

**Brief N: OPC-UA port block**
Direct analogue of brief 12. Block TCP 4840 from the probe; client connects.
Requires `asyncua` (pure Python) on asset, probe, and client. Check Alpine
wheel availability first — `asyncua` is pure Python and should be fine.

**Brief N+1: OPC-UA anonymous block**
Server requires at minimum username/password authentication. The probe's anonymous
session is rejected at the application layer; the client connects with credentials.
Boundary transparent. Same `asset.sh` toggle pattern as briefs 11 and 14.

**Brief N+2: OPC-UA security policy**
Server requires `Basic256Sha256` signing (rejects `None` policy). The probe
connects with security policy None → server rejects. Client connects with Sign →
server accepts. Teaches that OPC-UA's security policy is negotiated at session
establishment, not enforced at the network layer.

**Implementation note:** verify `asyncua` builds on Alpine before committing to
this track. If it does, add it to asset/probe/client Dockerfiles alongside the
existing dependencies.

---

## Rate limiting

**Brief N: Connection rate limit**
iptables `hashlimit` module limits the probe to N new connections per minute on
any asset port. Legitimate client traffic is unaffected (different source IP
bucket). Teaches that volumetric protection is a distinct class of control from
content filtering — and that it has a different failure mode (legitimate traffic
from a shared IP is also limited). No new protocol needed; works against existing
Modbus or IEC 104 checks.

---

## Notes on sequencing

The GOOSE extension (16–17) is the lowest-friction next step: the infrastructure
is in place and the pattern is established.
OPC-UA is the largest new addition — worth checking `asyncua` on Alpine first.
Rate limiting is protocol-agnostic and can be inserted anywhere in the ladder.

All briefs involving `asset.sh` state (GOOSE SA, OPC-UA auth) share
the rebuild caveat: re-activate the component after `./lab down && ./lab up`.
