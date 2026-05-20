# Design notes

Working decisions that are not obvious from the code or README.

## Asset-slot model

The asset container runs one background process per protocol, each on its
canonical port, alongside the primary Modbus server. Entrypoint order:

```
mosquitto  -c /app/mosquitto.conf &       # MQTT     :1883
python3 /app/goose-server.py &            # GOOSE    EtherType 0x88B8
python3 /app/iec104-server.py &           # IEC 104  :2404
python3 /app/modbus-tls-server.py &       # Modbus/TLS :802
python3 /app/opcua-server.py &            # OPC-UA   :4840
exec python3 /app/server.py               # Modbus   :502  (PID 1)
```

`exec` on the last process makes the Modbus server PID 1 so Docker stop/kill
signals reach it directly. The background processes are daemons of PID 1 and
are reaped when the container exits.

Adding a protocol means: add a server script, start it in the background before
the `exec` line, copy it in the Dockerfile. The topology and web app need no
changes.

## Minimal-protocol-implementation policy

Protocol libraries that require compiled C extensions (e.g. `c104`) do not
produce manylinux-compatible wheels for Alpine (musl libc). Rather than switch
base images or bloat the build with gcc/cmake/musl-dev, prefer a pure-Python or
Alpine-native implementation for any protocol the lab adds.

IEC 60870-5-104 framing is simple enough to implement in ~60 lines. MQTT uses
the Alpine `mosquitto` package. Modbus uses `pymodbus`, which is pure Python.
Each implementation is a small, auditable file with no transitive dependencies.

**Exception — OPC-UA:** The OPC-UA Binary protocol stack includes multi-layer
security (X.509 certs, asymmetric key exchange, symmetric session encryption)
that cannot be hand-rolled in a few hundred lines. `asyncua` is used instead.
It ships `musllinux` wheels and installs cleanly on Alpine without a compiler.
The `cryptography` package is pinned to `>=48,<49` because asyncua's cert
handling calls APIs introduced in cryptography 48 and may break on 49.x.

## IEC 62351-5 three-layer ladder

`12-iec104-command.py` sends `C_SC_NA_1` (type 45, single command) — the exact
ASDU that IEC 62351-5 was designed to authenticate. The probe's payload is
therefore a stable fixture: same brief, same check, same trip command across
three defence generations.

Brief 12 teaches network-layer control: block the probe at the boundary (port).
Brief 13 teaches protocol-layer control: the probe may connect and STARTDT,
but its C_SC_NA_1 is rejected at the boundary by a u32 rule on the ASDU type
byte. Brief 14 teaches application-layer control: the boundary is transparent,
and the asset validates a MAC on every I-frame. The three briefs show the same
trip command stopped at three different layers: port (12), type ID (13), MAC (14).

In brief 14, the probe connects to port 2404, completes the STARTDT handshake,
and sends the same trip command. The command reaches the asset. The asset checks
for a valid HMAC-SHA256 MAC appended to the I-frame, finds none, and closes the
connection. The probe's `recv()` raises `ConnectionResetError`. The authorised
client sends the same command with a correct MAC and receives an S-frame ACK.

The cross-brief comparison (brief 12 vs brief 14) demonstrates that network
segmentation and application-layer authentication are complementary controls,
not alternatives. Both produce a HELD headline; the enforcement point is at
opposite ends of the path.

## Asset.sh toggle pattern

Several briefs require the asset itself to change behaviour when a component is
activated (as opposed to the boundary). A flag file controls the behaviour at
runtime; the server checks `os.path.exists(FLAG)` on each relevant event.

| Brief                 | Flag file                                   | Effect                                                    |
|-----------------------|---------------------------------------------|-----------------------------------------------------------|
| 11 (mqtt-auth)        | `/tmp/mqtt.passwd` + live mosquitto restart | Broker rejects anonymous CONNECT (rc=5)                   |
| 14 (iec104-sa)        | `/app/sa-mode`                              | IEC 104 server validates HMAC-SHA256 MAC on every I-frame |
| 19 (opcua-auth)       | `/app/opcua-auth-mode`                      | OPC-UA server requires username+password                  |
| 20 (opcua-sec-policy) | `/app/opcua-sec-policy-mode`                | OPC-UA server requires Basic256Sha256_Sign                |

The web app supports an optional `asset.sh` alongside each component's `apply.sh`.
When a component is activated, `apply.sh` runs on the boundary container (as
before) and `asset.sh`, if present, is copied to and run on the asset container
via `docker exec`. Deactivation calls `asset-remove.sh` on the asset.
Navigation (prev/next brief) and reset go through `_flush_applied`, which runs
both `remove.sh` and `asset-remove.sh` before clearing state.

**State after `./lab down && ./lab up`:** container filesystems are wiped on
restart. Any flag file written by `asset.sh` does not survive. The host-side
`.applied-components` file persists, so the UI may show a component as active
while the container carries none of its state. Always re-activate the component
after a rebuild to re-run both `apply.sh` and `asset.sh` on the fresh containers.

## Modbus/TLS (brief 9)

The asset runs two Modbus listeners: the original plain-TCP server on 502 (PID 1
via `exec`) and a TLS server on 802 (`modbus-tls-server.py` background process).
The TLS cert is a self-signed RSA-2048 cert generated at image build time and
stored at `/app/tls/server.crt` and `/app/tls/server.key`.

The client connects with `ssl.CERT_NONE` (no CA validation), which is appropriate
for a lab with a self-signed cert. The component blocks port 502 from all sources
and permits only the client's IP on port 802. The probe can reach neither port.

`pymodbus.client.AsyncModbusTlsClient` is used. Its `close()` is a coroutine and
must be awaited; calling it without `await` silently does nothing and leaves the
connection open.

## MQTT password authentication (brief 11)

`mosquitto_passwd` creates a password file. The file must be world-readable
(`chmod 644`) before mosquitto opens it, or the daemon silently ignores the file
and continues accepting anonymous connections. The `asset.sh` for `mqtt-auth`
runs `chmod 644 /tmp/mqtt.passwd` immediately after `mosquitto_passwd`.

mosquitto is restarted (pkill + sleep 0.3 + re-launch) rather than reloaded
because the Alpine mosquitto package does not ship with `mosquitto_ctrl` or a
clean reload signal handler.

## IEC 61850 GOOSE relay

GOOSE (EtherType 0x88B8) carries no IP header and cannot be routed.
The boundary container has two Ethernet interfaces (eth1 north, eth2
south) with no bridge between them; GOOSE multicast from the north
segment stops at eth1 without explicit forwarding.

The boundary runs `goose-relay.py` as a background daemon that reads
raw GOOSE frames from each interface and forwards them to the other.
This is the realistic model: GOOSE cannot cross an IP router without an
explicit relay, and real substation vendors implement exactly this for
inter-zone GOOSE. The relay is also the control point: it reads
`/tmp/goose-blocked` for source MACs to drop before forwarding, and
`/tmp/goose-trip-filter` to enable allData content inspection.

Python3 was added to the boundary Dockerfile for the relay daemon. The
boundary previously needed only iptables and iproute2; brief 15 is the
first brief that requires logic on the boundary beyond shell + iptables.

The asset's `goose-server.py` echoes a unicast GOOSE reply to the sender's
MAC, giving check scripts a positive signal that the frame arrived. Without
this echo, GOOSE is fire-and-forget and there is no way to distinguish pass
from silent drop.

## GOOSE MAC discovery via UDP ARP (brief 15)

`goose-block-probe/apply.sh` must write the probe's MAC to `/tmp/goose-blocked`
before the relay can filter its frames. The boundary cannot use `ping` (not in
the `debian:12-slim` image). Instead, the script uses Python:

1. Open a UDP socket and `connect()` to `10.0.1.20:9`. The kernel resolves the
   ARP entry without sending any application data.
2. Read `/proc/net/arp` and find the line for `10.0.1.20` with a non-zero MAC.
3. Retry up to 5 times with 0.4 s sleep; fail loudly if unresolved.

This works reliably because the boundary (10.0.1.1) and probe (10.0.1.20) are
on the same L2 subnet. A shell heredoc inside the container-side shell script is
used to pass the Python source; `docker exec` without `-i` does not forward
heredoc stdin, but scripts that already run inside the container handle heredocs
normally.

## GOOSE trip filter (brief 16)

The relay's allData content filter is activated by the presence of
`/tmp/goose-trip-filter`. When the flag exists, `goose-relay.py` parses the
allData BER TLV in each forwarded GOOSE PDU and drops frames whose first
allData entry is a BOOLEAN TRUE (0xff). BOOLEAN FALSE (cancel) and all
non-boolean entries pass.

The BER parsing is minimal: walk the TLV chain to find the allData tag (0xa2),
then inspect the first value byte of the first child entry. This is enough to
distinguish trip from cancel without a full IEC 61850 schema library.

## GOOSE IEC 62351-6 SA (brief 17)

The asset's `goose-server.py` checks `os.path.exists("/app/goose-sa-mode")` on
each received frame. When active, it rejects frames that do not carry a valid
HMAC-SHA256 signature appended after the GOOSE PDU. Unsigned frames are silently
dropped; the sender receives no echo and the check exits 1 (block). The client
generates the correct HMAC using the shared key before sending.

## OPC-UA asyncua 1.1.8 API notes

asyncua 1.1.8 has changed several APIs relative to older versions:

**Import path:** `User` and `UserRole` live in `asyncua.server.user_managers`,
not a separate `asyncua.server.users` module.
```python
from asyncua.server.user_managers import UserManager, User, UserRole
```

**Certificate format:** `server.load_certificate()` and `server.load_private_key()`
default to DER format. Files with a `.crt` or `.key` extension (PEM content)
must be loaded with `format="pem"` explicitly:
```python
await server.load_certificate("/app/tls/server.crt", format="pem")
await server.load_private_key("/app/tls/server.key", format="pem")
```

**Password type:** `decrypt_user_token` always returns a `str` (UTF-8 decoded).
Compare the received password to a `str` constant, not `bytes`.

**Endpoint discovery for security:** `client.set_security(..., server_certificate=None)`
auto-fetches the server cert via a temporary None-security `GetEndpoints` call.
This works even when the server only advertises `Basic256Sha256_Sign` — the
GetEndpoints channel is always available regardless of the server's security policy
list. No manual certificate exchange is needed.

**Client certificate validation:** `certificate_validator = None` (the default)
means the server does NOT validate client certificates against a trust list.
The client must supply a cert+key pair (to sign its own messages) but does not
need to be enrolled in the server's PKI.

## OPC-UA client certificate generation

The client needs a self-signed cert with the application URI as a Subject
Alternative Name (URI SAN: `urn:ot-workbench:client`). The standard `openssl`
CLI cannot add URI SANs without a config file, so the cert is generated at image
build time by `gen-opcua-cert.py` using the `cryptography` Python library.
The cert and key are written to `/app/pki/client.pem` and `/app/pki/client-key.pem`.

Files use the `.pem` extension so asyncua's `load_certificate` and
`load_private_key` default to PEM format without an explicit `format=` argument.

## OPC-UA security policy: server restart (brief 20)

Changing the security policy requires restarting the OPC-UA server process
(the policy list is fixed at startup). The `opcua-sec-policy/asset.sh`:

1. Touches `/app/opcua-sec-policy-mode`.
2. `pkill -f opcua-server.py` to stop the running instance.
3. Sleeps 0.5 s.
4. Re-launches `python3 /app/opcua-server.py &`.

On startup, `opcua-server.py` reads the flag and passes
`[ua.SecurityPolicyType.Basic256Sha256_Sign]` to `set_security_policy`.
Without the flag, it uses `[ua.SecurityPolicyType.NoSecurity]`.

## IEC 61850 GOOSE relay — relay flag files

The relay uses two flag files, checked dynamically on each frame:

| File                     | Effect                                          |
|--------------------------|-------------------------------------------------|
| `/tmp/goose-blocked`     | Source MACs (one per line) to silently drop     |
| `/tmp/goose-trip-filter` | Presence enables allData BOOLEAN TRUE filtering |

Both files may be absent (relay passes all frames). Either or both may be active
simultaneously. `remove.sh` for each component deletes its flag file; the relay
continues running throughout.

## IEC 104 command-filter: rule ordering

The u32 REJECT rule must precede ESTABLISHED,RELATED in the FORWARD chain. The
probe sends its C_SC_NA_1 command on an already-established TCP session (the
STARTDT handshake established it). Without this ordering, conntrack accepts the
command as part of an established session before u32 can inspect the payload.
This is the same constraint as modbus-write-filter.

## IEC 104 S-frame ACKs in the asset server

The asset's IEC 104 server was extended to send S-frame acknowledgements for
received I-frames (correct IEC 104 behaviour). This gives the probe check a
positive signal when the command is not filtered: receipt of a 6-byte frame
starting with 0x68 means the command got through (exit 0). A TCP RST from the
boundary means it was rejected (ConnectionResetError → exit 1). Without
S-frames, the check had no way to distinguish pass from silent ignore.

## Rate limiting: hashlimit token-bucket design (brief 21)

`iptables hashlimit` maintains a per-key token bucket. The component uses
`--hashlimit-mode srcip` so each source IP has an independent bucket. The probe
and the client do not share a bucket; the probe exhausting its quota does not
affect the client.

Rule order matters:
1. ESTABLISHED,RELATED — return traffic for existing sessions is never affected.
2. hashlimit DROP — new connections above the rate are silently dropped.
3. NEW ACCEPT — new connections within the rate pass.

`--hashlimit-above 3/minute --hashlimit-burst 3` means: a bucket holds 3 tokens;
each new connection consumes one token; tokens refill at 3/minute. The probe
makes 10 rapid connections. The first 3 consume the initial burst and succeed.
Subsequent connections find an empty bucket and are dropped (SYN silently dropped
by iptables — no RST, so the probe waits for its 0.5 s timeout on each).

The probe check (`16-rate-hammer.py`) exits 1 (block) if fewer than 5 of 10
attempts succeed. Without the rate limit, all 10 succeed (exit 0, pass). With the
rate limit, only 3 succeed (exit 1, block).

The failure mode worth knowing: this control is per source IP, not per host
identity. A NAT gateway routing both authorised and unauthorised traffic from the
same public IP shares one bucket.
