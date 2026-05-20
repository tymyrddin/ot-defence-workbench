# OT Defence Workbench — Developer Guide

How to extend the workbench. For design decisions and the reasoning behind them,
see [DESIGN.md](DESIGN.md).

## Project layout

```
topology.clab.yml               containerlab topology (four nodes, two bridges)
asset/                          asset container image
  server.py                     Modbus/TCP server (port 502, PID 1)
  iec104-server.py              IEC 60870-5-104 server (port 2404)
  iec104frame.py                shared IEC 104 APDU framing primitives
  mosquitto.conf                MQTT broker config (port 1883)
  Dockerfile
  entrypoint.sh                 starts background services, then exec's Modbus server
boundary/                       boundary container image (Debian 12, iptables only)
client/
  checks/                       check scripts run from the client container
  Dockerfile
probe/
  checks/                       check scripts run from the probe container
  custom/                       participant-written probes, organised by protocol
  Dockerfile
components/<name>/
  apply.sh                      iptables rules pushed to the boundary on activation
  remove.sh                     flush script called on deactivation
  description.txt               one-line description shown in the UI
briefs/<nn>-<slug>.toml         brief definition: requirement, links, checks, expectations
web/
  app.py                        Flask application
  templates/index.html
  static/
lab                             CLI: up / down / check / brief / build / remove
DESIGN.md                       design decisions and architectural notes
requirements.txt                web app dependencies (Flask only)
```

## Adding a protocol

A protocol needs: a server process on the asset, check scripts for the probe and
client, and a brief. The web app picks up any protocol that appears in a brief's
`protocol =` field — no web app changes needed.

### 1. Asset server

Write `asset/<proto>-server.py`. Start it in `asset/entrypoint.sh` as a background
process before the final `exec`:

```sh
python3 /app/<proto>-server.py &
exec python3 /app/server.py
```

Add the COPY to `asset/Dockerfile`:

```dockerfile
COPY <proto>-server.py /app/<proto>-server.py
```

If the protocol needs a shared framing module (as IEC 104 does), add that too.

For Layer 2 protocols (EtherType-based, no IP header), the boundary also needs a relay
daemon. Add `boundary/<proto>-relay.py`, copy it in `boundary/Dockerfile`, and start it
from `boundary/entrypoint.sh`. See `boundary/goose-relay.py` for the pattern: two
AF_PACKET sockets bridging eth1↔eth2, with a block-file read on each frame.

### 2. Library dependencies

If the probe or client need a library, add it to their Dockerfiles:

```dockerfile
RUN pip install --no-cache-dir "paho-mqtt>=1.6,<2.0"
```

Prefer pure-Python or Alpine-native packages. See DESIGN.md for the rationale.

### 3. Check scripts

Add scripts to `probe/checks/` and `client/checks/`. Exit 0 = reached/succeeded
(pass), exit 1 = blocked/failed (block). Follow the existing numbering sequence.

The probe scripts run inside the probe container. The client scripts run inside the
client container. Both can reach the asset at `10.0.2.10`.

### 4. Brief

Add `briefs/<nn>-<slug>.toml`. Each `[[checks]]` entry references a script path
and an expected outcome:

```toml
[[checks]]
runner = "probe"          # "probe" or "client"
name = "my-check"
script = "/checks/07-my-check.py"
expect = "block"          # "block" or "pass"
protocol = "my-protocol"  # determines which UI tab it appears under
```

Links follow the pattern `https://blue.tymyrddin.dev/docs/ot/protocols/<slug>`.

### 5. Rebuild

After any change to `asset/`, `probe/`, or `client/`:

```sh
./lab down && ./lab up
```

`./lab up` rebuilds all four images before deploying.

---

## Adding a brief

Create `briefs/<nn>-<slug>.toml`. The number must be unique and determines its
position in the ladder. Reference existing check scripts where possible — a new
brief does not require new scripts if the existing battery covers the scenario.

Expectations (`expect = "pass"` or `expect = "block"`) define what SHOULD happen
when the correct defence is applied, not what happens on a transparent boundary.

---

## Adding a component

Create `components/<name>/apply.sh`, `remove.sh`, and optionally `description.txt`.

`apply.sh` runs inside the boundary container. It has full iptables access. Always
start with `iptables -F FORWARD` to flush the previous state.

If the component needs to configure the asset container (e.g. enabling a server-side
authentication mode), also create `asset.sh` and `asset-remove.sh`. The web app
copies these to the asset container and runs them via `docker exec` on activation and
deactivation respectively. See `components/iec104-sa-asset/` for the pattern.

IP reference (also in the comment block at the top of every built-in `apply.sh`):

```
boundary north eth1  10.0.1.1/24
boundary south eth2  10.0.2.1/24
client               10.0.1.10
probe                10.0.1.20
asset                10.0.2.10
```

`remove.sh` is called on deactivation. The standard flush:

```sh
#!/usr/bin/env sh
set -e
iptables -F FORWARD
iptables -P FORWARD ACCEPT
```

**Rule ordering note:** Any u32 or protocol-aware DROP/REJECT rules must come
before the `ESTABLISHED,RELATED -j ACCEPT` rule. By the time a probe sends a
command, its TCP session is already ESTABLISHED; conntrack will accept the packet
before u32 can inspect it if the ACCEPT rule comes first.

---

## Adding check scripts

Scripts receive no arguments and communicate only via exit code:

- `sys.exit(0)` — reached / succeeded (result: **pass**)
- `sys.exit(1)` — blocked / failed (result: **block**)

Probe scripts target `10.0.2.10` directly (routed through the boundary).
Client scripts target `10.0.2.10` directly (same path, different source IP).

Use `socket.create_connection(host, port, timeout=N)` for TCP checks. For
protocol-level checks that need to detect a TCP RST, set a socket timeout after
connect and use `recv()` to wait for either a response or an `OSError`.
