# Future briefs

Possible directions. Grouped by what they teach and what they require.

The ladder currently ends at brief 20 (opcua-sec-policy).

---

## OPC-UA

OPC-UA (port 4840) is the dominant data exchange protocol in European manufacturing
and process industry. It has three security modes (None, Sign, SignAndEncrypt) and
three authentication methods (anonymous, username, certificate). A small ladder:

~~**Brief 18: OPC-UA port block**~~ — implemented.

~~**Brief 19: OPC-UA anonymous block**~~ — implemented.

~~**Brief 20: OPC-UA security policy**~~ — implemented.

**Library:** `asyncua` installs cleanly on Alpine via musllinux_1_2 wheels — no
source builds needed. Its two C-extension dependencies (`cryptography>=48,<49`
and `cffi 2.0`) both ship musllinux wheels. Total wheel weight ~8 MB (mostly
`cryptography`). Pin `cryptography>=48,<49` to avoid a surprise if a future
major bump lands without a musllinux wheel on day one.

`asyncua` is pure Python on top; the compiled layer is only `cryptography`/`cffi`.
This is the case where the minimal-protocol-implementation policy correctly admits
a library: OPC-UA Binary (NodeIds, ExtensionObjects, variant types) is
disproportionately complex to hand-roll for what the briefs teach. Use `asyncua`
on both asset and probe/client so the shared-primitive property holds through the
library itself. Add it to asset, probe, and client Dockerfiles alongside the
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

OPC-UA is the natural next track — Alpine compatibility confirmed, no glibc
divergence, no compile step. Rate limiting is protocol-agnostic and can be
inserted anywhere.

All briefs involving `asset.sh` state (OPC-UA auth, etc.) share the rebuild
caveat: re-activate the component after `./lab down && ./lab up`.
