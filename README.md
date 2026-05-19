# OT defence workbench

A containerlab environment for practising OT network defence. Four containers, two
segments, one asset to protect, one adversary that probes. The skill being practised
is deciding what may cross a boundary and proving the decision held.

This is a workbench rather than a facility. A simulation lab earns its keep by feeling
real; a practice environment for defence needs a trust boundary, two sides, an asset,
and a verdict. Lore would only add weight.

## What it is not

A green scoreboard reports that nothing the probe knows how to attempt got through. It
does not report secure. The probe battery is finite. The asset is a toy. The workbench
teaches the shape of a decision, not the specifics of any particular vendor's appliance.
That distinction is worth carrying from the start.

## The estate

Four containers at rest:

- `client` — the legitimate consumer of the asset, on the north segment.
- `asset` — the protected service, on the south segment. Version 1 runs a Modbus/TCP
  server.
- `boundary` — the node the learner builds out. Starts as a transparent bridge that
  forwards everything.
- `probe` — the adversary. Sits on the north segment, models an attacker who already
  holds a foothold on the IT side, and runs a battery of attempts against the asset.

Two networks, north and south, joined only through `boundary`. Nothing reaches `asset`
except through that node.

Modbus/TCP is the first asset protocol because it has a clean split: read function
codes against write function codes. "Permit reads, refuse writes" is a crisp,
demonstrable constraint. Later versions can swap the asset to MQTT or OPC UA.

## The component tray

A defence is built by instantiating a component. Each component is a pre-built container
image with a wiring recipe. The skill being practised is placement and composition: where
the component sits, what it connects to, what path it replaces.

Version 1 components:

- `packet-filter` — an L3/L4 allowlist. Default deny, permits named flows.
- `jump-host` — a bastion. Once placed it becomes the only node permitted to originate
  connections to the asset, and it records sessions.
- `protocol-filter` — a Modbus-aware proxy. Permits read function codes, refuses writes
  from a configured source. No equivalent in a plain firewall recipe.
- `read-replica` — a one-way mirror of the asset's register map. The client reads the
  replica and never opens a socket to the asset.
- `log-sink` — a collector. Components send events here, giving the learner a visibility
  plane rather than only a preventive one.

## The control surface

```
lab up / lab down        start and stop the bench
lab brief                print the current requirement
lab build <component>    instantiate and wire a component
lab remove <component>   reverse it
lab check                run the probe battery and print the scoreboard
lab next                 advance to the next brief
lab reset                return the bench to flat
```

## Scoring

The probe runs a battery of attempts. Each one is an assertion. `lab check` compares
outcomes to what the current brief expects and prints a scoreboard.

Two points are fixed:

The legitimate flow is scored alongside the attacks. A defence that blocks the probe
but also breaks the client's reads has not passed. A brief is met only when every
adversary check is blocked and every legitimate check still succeeds.

Bypass detection needs no special mechanism. Every brief includes a direct-path check.
A `jump-host` built while the direct route is still open leaves that check failing and
the headline still shows reach. A defence counts only when the path it was meant to
replace is shut.

## The briefs

Briefs are constraints, not instructions. Each one states what the outcome must be;
several architectures may satisfy it. The point is the decision, not the component.

A first ladder:

1. The probe cannot reach the asset. The client's reads still succeed.
2. The client needs to write one setpoint. That write succeeds; all other writes from
   the north segment do not.
3. An engineer needs occasional interactive access to the asset. No direct path from
   the north segment to the asset is permitted.
4. The probe now holds the client's address. Source allowlisting alone no longer
   separates them. The brief still holds.
5. A second client appears, read-only, from a different segment. Both clients succeed;
   the probe does not.
6. The asset is readable from the north without the north segment opening a socket to
   the asset.
7. Every cross-boundary access is logged. An unexpected one raises an event.
8. An estate is handed to the learner with a defence already built and the scoreboard
   still red. Find what gets through and close it.

Briefs are cumulative by default. `lab reset` is available, and a brief can ask for a
clean slate where it needs one. Brief 8 is inverted: instead of building, the learner
is finding. That is a different muscle, and it is the lab teaching its central lesson
directly rather than as a side effect of a build step.

## Two axes

Briefs and adversary tiers are separate.

**Briefs** evolve what you protect: the constraint, the asset protocol, the topology.

**Adversary tiers** evolve what you protect against. Version 1 ships tier zero: a
network-external probe that attempts unauthenticated access. Later tiers step inward.
The first worth adding is an authenticated-but-overprivileged actor, a legitimate
identity doing something it should not. That is the only adversary a network control
cannot touch.

The same brief replays under a stronger adversary and fails differently. The estate
stays at four containers throughout; the difficulty lives in the tier, not the size.

## Project layout

```
topology.clab.yml              base four-node bench
asset/                         Modbus/TCP server image
client/                        legitimate consumer image and checks
probe/checks/                  adversary image and check scripts
boundary/                      boundary node image
components/<name>/             one directory per component: image and apply/remove scripts
briefs/<nn>-<slug>.toml        one file per brief: requirement text and expected check outcomes
lab                            CLI
README.md
```

containerlab handles the two-segment topology cleanly. Plain Docker Compose is a
workable fallback if containerlab adds friction for the component-injection step.

## Running it

**Prerequisites:** Docker, [containerlab](https://containerlab.dev/install/), Python 3.11+.

```
./lab up                   build images and start the bench
./lab check                run the probe battery and print the scoreboard
./lab brief                print the current requirement
./lab build <component>    instantiate and wire a component
./lab remove <component>   reverse it
./lab next                 advance to the next brief
./lab reset                return the bench to flat
./lab down                 stop and remove all containers
```

Add the project directory to `PATH` to drop the `./` prefix.

## The smallest first slice

- `lab up` with the four nodes and the Modbus asset.
- One component: `packet-filter`.
- One brief: brief 1 from the ladder.
- A probe with four checks: direct port reachable, anonymous read, write attempt, and
  the client's legitimate read.

`lab up`, then `lab check` showing the bench owned, then `lab build packet-filter`,
then `lab check` showing it held. Every later component, brief, and tier is that
skeleton repeated.

## How it sits with the rest of the site

The [blue documentation](https://blue.tymyrddin.dev) covers the per-protocol recipes
and the architecture patterns. Prose cannot verify an implementation. The workbench
makes those decisions verifiable and surfaces what was left open rather than only what
was configured.

Each component links back to the relevant protocol page. Each brief links to an incident
in the incidents section, since a brief tends to be an incident's antidote made
practisable. The topology is the Purdue model from the architecture pages in executable
form.
