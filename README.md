# OT Defence Workbench

A containerlab environment for practising OT network defence. Four containers, two
segments, one asset to protect, one adversary that probes. Each brief states what
outcome must hold; the workbench tells you whether it does.

## What it is not

A green scoreboard means the probe found no path through. It does not mean secure. The probe battery is finite, the asset is a simulation, and the
workbench teaches the shape of a decision rather than the specifics of any particular
vendor's appliance. That distinction is worth carrying from the start.

## The estate

```
north segment 10.0.1.0/24          south segment 10.0.2.0/24
  client  10.0.1.10                   asset  10.0.2.10:502
  probe   10.0.1.20
                    boundary  north 10.0.1.1 / south 10.0.2.1
```

- client: the legitimate consumer of the asset.
- asset: a Modbus/TCP server. Holds a register map the client reads and writes.
- boundary: the node the learner builds out. Starts as a transparent bridge.
- probe: the adversary. Sits on the north segment alongside the client and runs a
  battery of attempts against the asset.

The asset is only reachable through the boundary. Nothing on the north segment has a
direct route to the south segment.

## Running it

Prerequisites: Docker, [containerlab](https://containerlab.dev/install/), Python 3.11+.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./lab up
python web/app.py
```

Open `http://localhost:5000`.

When a brief requires a new container image (a new check script is added to
`probe/checks/` or `client/checks/`), restart the lab:

```
./lab down && ./lab up
```

Only needed when adding new material.

## The web UI

The web interface is the working surface. It has three sections.

Probe Battery: the checks the probe and client will run. Brief checks come from
the active brief's TOML file and show the source script. Custom probes can be written
and saved directly in the browser under any supported protocol tab.

Firewall Rules: the components available on the boundary. Select one to view or
edit its `apply.sh`, then activate it. Only one component is active at a time.
Activating a new one flushes the previous. The Save button saves changes to disk
without activating.

Results: the outcome of the last run. Each check shows whether the result matched
the brief's expectation. The headline HELD or OPEN reflects whether all brief checks
passed their expected outcomes. Custom probe results are shown separately and do not
affect the headline.

Use Next brief and Prev brief to move through the ladder. Navigation resets the
boundary rules and clears results.

## The briefs

Eight briefs form a ladder. Each introduces a new condition or attack vector and asks
for a defence that holds.

| # | Slug                    | Teaches                                                                                                       |
|---|-------------------------|---------------------------------------------------------------------------------------------------------------|
| 1 | block-probe             | Basic network segmentation: FORWARD DROP with a permit for the client.                                        |
| 2 | write-one-setpoint      | Source allowlisting: permit by IP, introducing the assumption that breaks in brief 4.                         |
| 3 | jump-host               | Topology control: close the direct path, proxy all connections through the boundary via DNAT.                 |
| 4 | spoof-proof             | IP spoofing: the jump-host holds because it does not inspect source addresses.                                |
| 5 | source-restricted-proxy | Tighten the proxy: restrict the DNAT rule to the authorised source so the probe cannot use the proxy at all.  |
| 6 | modbus-write-filter     | Protocol-layer enforcement: iptables u32 drops write function codes regardless of source.                     |
| 7 | graduated-access        | Graduated access: reads open to all, writes gated to the authorised host.                                     |
| 8 | layered-defence         | Defence in depth: source restriction and function code filter are independent; both must fail simultaneously. |

## The components

Each component lives in `components/<name>/apply.sh`. Activating a component copies
the script to the boundary container and executes it. `remove.sh` is called when the
component is flushed.

| Component                 | What it does                                                                        |
|---------------------------|-------------------------------------------------------------------------------------|
| `packet-filter`           | FORWARD DROP with commented permit rules to fill in.                                |
| `client-allowlist`        | Permits the client's IP through, drops everything else.                             |
| `jump-host`               | DNAT proxy: redirects port 502 to the asset, no source restriction.                 |
| `source-restricted-proxy` | DNAT proxy restricted to the client's source address.                               |
| `modbus-write-filter`     | Jump-host base with u32 rules blocking all Modbus write FCs.                        |
| `graduated-access`        | Open DNAT proxy with write FCs blocked for all sources except the client.           |
| `layered-defence`         | Source-restricted DNAT combined with write FC filter as a second independent layer. |

## Custom probes

Write a probe script in the New probe section of the UI, assign it a protocol and
name, and save. It appears in the protocol tab alongside brief checks. Custom probes
run when selected and their results appear in the CUSTOM PROBES section of the results
table. They do not affect the HELD/OPEN headline.

Saved probes live in `probe/custom/<protocol>/<name>.py`. The template at
`probe/custom/_template.py` is the starting point.

## Project layout

```
topology.clab.yml
asset/                          Modbus/TCP server image
boundary/                       boundary node image
client/
  checks/                       check scripts run from the client container
probe/
  checks/                       check scripts run from the probe container
  custom/                       participant-written probes, organised by protocol
components/<name>/
  apply.sh                      iptables rules applied to the boundary
  remove.sh                     flush script
briefs/<nn>-<slug>.toml         brief definition: requirement, links, expected checks
web/
  app.py                        Flask application
  templates/index.html
  static/
lab                             CLI: up / down
requirements.txt
```

## How it sits with the rest of the site

The [blue documentation](https://blue.tymyrddin.dev/docs/ot/) covers the per-protocol
security recipes and the architecture patterns. The workbench makes those decisions
executable: each brief links to a relevant doc page, and each component is the
iptables translation of a pattern described there.
