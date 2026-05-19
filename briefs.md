# Briefs

## 1 · block-probe
**The network is the only control surface.**

Modbus carries no authentication. Anyone who reaches port 502 can read or write any register. The boundary starts as a transparent bridge. Setting FORWARD DROP and adding a single permit rule for the client is enough to separate the probe from the asset. Several architectures satisfy the brief; only the outcome is tested.

---

## 2 · write-one-setpoint
**Source allowlisting: the first and weakest identity check.**

The client needs to write a setpoint; the probe must still be blocked. The only distinction available at L3/L4 is source address. A permit rule scoped to 10.0.1.10 works, and introduces the assumption that brief 4 will break.

---

## 3 · jump-host
**Topology is a control. Remove the direct path entirely.**

Brief 2 permitted the client to reach the asset directly. Brief 3 closes that path for everyone. The boundary DNAT-proxies all port 502 connections: no packet travels directly between north and south. Lateral movement to the asset requires going through the single visible gate.

---

## 4 · spoof-proof
**The jump-host defence does not inspect source addresses, so spoofing one changes nothing.**

The probe adopts the client's address (10.0.1.10) and attempts a direct connection. The jump-host FORWARD DROP blocks it regardless, because the rule is topological, not address-based. A source-allowlist defence fails this check; the jump-host holds.

---

## 5 · source-restricted-proxy
**The proxy itself needs a gatekeeper.**

The jump-host DNAT rule had no source restriction: any host on the north segment could use it. Adding `-s 10.0.1.10` to the PREROUTING rule means only the client's connections are forwarded. The probe's connections find no matching DNAT entry and hit the DROP policy.

---

## 6 · modbus-write-filter
**Protocol-layer enforcement is independent of source address.**

The iptables u32 module navigates IP and TCP headers and reads the Modbus function code byte. Write FCs (05, 06, 15, 16) are dropped before any ACCEPT rule sees them, regardless of who sent the packet. The client's writes are also blocked; the asset becomes read-only. Source address is irrelevant to this control.

---

## 7 · graduated-access
**Access can be tiered: reads open, writes gated.**

Brief 6's read-only posture is too strict when the client must write setpoints. Adding a source exception to the FC filter restores that: write FCs are dropped for all sources except 10.0.1.10. The proxy is open to everyone for reads; writes require the authorised address. The probe can read but cannot write.

---

## 8 · layered-defence
**Defence in depth: two independent controls must both fail.**

The DNAT source restriction (brief 5) and the function code filter (brief 6/7) are combined. Each control independently denies a different attack surface. Bypassing the source restriction still leaves the FC filter; bypassing the FC filter still leaves the source restriction. The probe can neither read nor write via the boundary. The client retains full access.
