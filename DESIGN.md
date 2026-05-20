# Design notes

Working decisions that are not obvious from the code or README.

## Asset-slot model

The asset container runs one background process per protocol, each on its
canonical port, alongside the primary Modbus server. Entrypoint order:

```
mosquitto  -c /app/mosquitto.conf &   # MQTT  :1883
python3 /app/iec104-server.py &       # IEC 104 :2404
exec python3 /app/server.py           # Modbus  :502  (PID 1)
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

The shared framing primitive for IEC 104 lives in `asset/iec104frame.py`. When
a protocol-aware boundary filter arrives for IEC 104, copy or symlink that
module into the boundary build context so the filter can parse ASDU type and
cause of transmission without duplicating the framing logic.

## IEC 62351-5 three-layer ladder

`12-iec104-command.py` sends `C_SC_NA_1` (type 45, single command) — the exact
ASDU that IEC 62351-5 was designed to authenticate. The probe's payload is
therefore a stable fixture: same brief, same check, same trip command across
three defence generations.

Brief 10 teaches network-layer control: block the probe at the boundary (port).
Brief 11 teaches protocol-layer control: the probe may connect and STARTDT,
but its C_SC_NA_1 is rejected at the boundary by a u32 rule on the ASDU type
byte. Brief 12 teaches application-layer control: the boundary is transparent,
and the asset validates a MAC on every I-frame. The three briefs show the same
trip command stopped at three different layers: port (10), type ID (11), MAC (12).

In brief 12, the probe connects to port 2404, completes the STARTDT handshake,
and sends the same trip command. The command reaches the asset. The asset checks
for a valid HMAC-SHA256 MAC appended to the I-frame, finds none, and closes the
connection. The probe's `recv()` raises `ConnectionResetError`. The authorised
client sends the same command with a correct MAC and receives an S-frame ACK.

The cross-brief comparison (brief 10 vs brief 12) demonstrates that network
segmentation and application-layer authentication are complementary controls,
not alternatives. Both produce a HELD headline; the enforcement point is at
opposite ends of the path.

## IEC 62351-5 asset toggle: asset.sh

Brief 12 requires the asset's IEC 104 server to validate MACs when active and
accept unauthenticated I-frames for briefs 10 and 11 (so the probe's command
gets through in those briefs' open state). A flag file (`/app/sa-mode`) controls
the behaviour at runtime; the server checks `os.path.exists(SA_FLAG)` on each
incoming I-frame.

The web app was extended to support an optional `asset.sh` alongside each
component's `apply.sh`. When a component is activated, `apply.sh` runs on the
boundary container (as before) and `asset.sh`, if present, is copied to and run
on the asset container via `docker exec`. Deactivation calls `asset-remove.sh`
on the asset. Navigation (prev/next brief) and reset go through `_flush_applied`,
which runs both `remove.sh` and `asset-remove.sh` before clearing state.

**State after `./lab down && ./lab up`:** container filesystems are wiped on
restart. Any flag file written by `asset.sh` (e.g. `/app/sa-mode`) does not
survive. The host-side `.applied-components` file persists, so the UI may show a
component as active while the container carries none of its state. Always
re-activate the component after a rebuild to re-run both `apply.sh` and
`asset.sh` on the fresh containers.

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
`/tmp/goose-blocked` for source MACs to drop before forwarding, checked
dynamically on each frame.

The component writes the probe's MAC to that file (discovered via ARP
on the boundary). Frames from the probe are dropped silently; frames
from the client are passed. The asset's `goose-server.py` echoes a
unicast GOOSE reply to the sender's MAC, giving check scripts a
positive signal that the frame arrived — without this echo, GOOSE is
fire-and-forget and there is no way to distinguish pass from silent drop.

Python3 was added to the boundary Dockerfile for the relay daemon. The
boundary previously needed only iptables and iproute2; brief 13 is the
first brief that requires logic on the boundary beyond shell + iptables.

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