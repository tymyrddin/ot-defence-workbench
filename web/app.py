#!/usr/bin/env python3
import glob
import json
import shutil
import subprocess
import tomllib
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "ot-workbench-dev"

LAB_DIR = Path(__file__).resolve().parent.parent
LAB_NAME = "ot-defence-workbench"
BOUNDARY = f"clab-{LAB_NAME}-boundary"
PROBE = f"clab-{LAB_NAME}-probe"
CLIENT = f"clab-{LAB_NAME}-client"
ASSET = f"clab-{LAB_NAME}-asset"
RUNNER_CONTAINER = {"probe": PROBE, "client": CLIENT}
RUNNER_DIR = {"probe": LAB_DIR / "probe", "client": LAB_DIR / "client"}

BRIEF_FILE = LAB_DIR / ".current-brief"
APPLIED_FILE = LAB_DIR / ".applied-components"
RESULTS_FILE = LAB_DIR / ".last-results.json"

PROTOCOLS = [
    "modbus", "dnp3", "opc-ua", "iec-61850", "ethernet-ip",
    "profinet", "bacnet", "mqtt", "iec-60870-5-104", "opc-da",
    "iccp", "hart-ip",
]

DEFAULT_REMOVE = """\
#!/usr/bin/env sh
set -e
iptables -F FORWARD
iptables -P FORWARD ACCEPT
"""

DEFAULT_APPLY = """\
#!/usr/bin/env sh
set -e
# Addresses:
#   boundary north 10.0.1.1/24   south 10.0.2.1/24
#   client 10.0.1.10   probe 10.0.1.20   asset 10.0.2.10:502

iptables -F FORWARD
iptables -P FORWARD DROP
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
# iptables -A FORWARD -s 10.0.1.10 -d 10.0.2.10 -p tcp --dport 502 -j ACCEPT
"""


def current_brief_num():
    try:
        return int(BRIEF_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 1


def load_brief(n=None):
    if n is None:
        n = current_brief_num()
    matches = sorted(glob.glob(str(LAB_DIR / "briefs" / f"{n:02d}-*.toml")))
    if not matches:
        return None
    with open(matches[0], "rb") as f:
        return tomllib.load(f)


def get_components():
    comps = []
    for d in sorted((LAB_DIR / "components").iterdir()):
        if not d.is_dir() or not (d / "apply.sh").exists():
            continue
        desc_file = d / "description.txt"
        comps.append({
            "name": d.name,
            "description": desc_file.read_text().strip() if desc_file.exists() else "",
            "apply": (d / "apply.sh").read_text(),
            "remove": (d / "remove.sh").read_text() if (d / "remove.sh").exists() else DEFAULT_REMOVE,
        })
    return comps


def get_applied():
    if not APPLIED_FILE.exists():
        return set()
    return {l.strip() for l in APPLIED_FILE.read_text().splitlines() if l.strip()}


def get_probe_checks(brief):
    if not brief:
        return []
    checks = []
    for check in brief.get("checks", []):
        runner = check["runner"]
        script_name = Path(check["script"]).name
        src = RUNNER_DIR.get(runner, LAB_DIR) / "checks" / script_name
        checks.append({
            "name": check["name"],
            "runner": runner,
            "script": check["script"],
            "expect": check["expect"],
            "protocol": check.get("protocol", "modbus"),
            "source": src.read_text() if src.exists() else "(source not found)",
        })
    return checks


def get_custom_probes():
    """Return custom probes grouped by protocol subdirectory."""
    custom_dir = LAB_DIR / "probe" / "custom"
    if not custom_dir.exists():
        return {}
    by_protocol = {}
    for protocol_dir in sorted(custom_dir.iterdir()):
        if not protocol_dir.is_dir() or protocol_dir.name.startswith("_"):
            continue
        probes = []
        for p in sorted(protocol_dir.iterdir()):
            if p.suffix in (".py", ".sh") and not p.name.startswith("_"):
                probes.append({"name": p.stem, "filename": p.name,
                               "source": p.read_text(), "protocol": protocol_dir.name})
        if probes:
            by_protocol[protocol_dir.name] = probes
    return by_protocol


def get_probe_template():
    t = LAB_DIR / "probe" / "custom" / "_template.py"
    return t.read_text() if t.exists() else "#!/usr/bin/env python3\nimport sys\nsys.exit(1)\n"


def docker_exec_rc(container, cmd):
    return subprocess.run(
        ["docker", "exec", container] + cmd, capture_output=True
    ).returncode


def load_results():
    if not RESULTS_FILE.exists():
        return None
    with open(RESULTS_FILE) as f:
        return json.load(f)


def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f)


def compute_headline(results):
    brief_checks = [r for r in results if not r.get("custom")]
    return "HELD" if brief_checks and all(r["held"] for r in brief_checks) else "OPEN"


@app.route("/")
def index():
    brief = load_brief()
    checks = get_probe_checks(brief)
    custom_probes = get_custom_probes()
    components = get_components()
    applied = get_applied()
    results = load_results()
    headline = compute_headline(results) if results else None

    # Group brief checks by protocol
    checks_by_protocol = {}
    for chk in checks:
        proto = chk["protocol"]
        checks_by_protocol.setdefault(proto, []).append(chk)

    # Protocols that have content (brief checks or custom probes)
    active_protocols = sorted(
        set(list(checks_by_protocol.keys()) + list(custom_probes.keys()))
    )

    applied_names = applied
    # Which editor to show: URL param > applied > first component
    show_comp = (
        request.args.get("comp")
        or next(iter(applied_names), None)
        or (components[0]["name"] if components else None)
    )

    brief_num = current_brief_num()
    has_next = bool(glob.glob(str(LAB_DIR / "briefs" / f"{brief_num+1:02d}-*.toml")))

    return render_template(
        "index.html",
        brief=brief,
        brief_num=brief_num,
        has_next=has_next,
        checks_by_protocol=checks_by_protocol,
        custom_probes=custom_probes,
        active_protocols=active_protocols,
        all_protocols=PROTOCOLS,
        components=components,
        applied=applied_names,
        show_comp=show_comp,
        results=results,
        headline=headline,
        probe_template=get_probe_template(),
        default_apply=DEFAULT_APPLY,
    )


@app.route("/check", methods=["POST"])
def check():
    brief = load_brief()
    selected_brief = set(request.form.getlist("brief_probes"))
    selected_custom = set(request.form.getlist("custom_probes"))
    results = []

    for chk in (brief or {}).get("checks", []):
        if chk["name"] not in selected_brief:
            continue
        container = RUNNER_CONTAINER.get(chk["runner"])
        if not container:
            continue
        rc = docker_exec_rc(container, ["python3", chk["script"]])
        actual = "pass" if rc == 0 else "block"
        results.append({
            "name": chk["name"], "runner": chk["runner"],
            "protocol": chk.get("protocol", ""),
            "expect": chk["expect"], "actual": actual,
            "held": actual == chk["expect"], "custom": False,
        })

    custom_dir = LAB_DIR / "probe" / "custom"
    for proto_dir in sorted(custom_dir.iterdir()) if custom_dir.exists() else []:
        if not proto_dir.is_dir() or proto_dir.name.startswith("_"):
            continue
        for script in sorted(proto_dir.iterdir()):
            if script.suffix not in (".py", ".sh") or script.name.startswith("_"):
                continue
            key = f"{proto_dir.name}/{script.stem}"
            if key not in selected_custom:
                continue
            dest = f"/tmp/custom-{proto_dir.name}-{script.name}"
            subprocess.run(
                ["docker", "cp", str(script), f"{PROBE}:{dest}"], capture_output=True
            )
            cmd = ["python3", dest] if script.suffix == ".py" else ["/bin/sh", dest]
            rc = docker_exec_rc(PROBE, cmd)
            results.append({
                "name": script.stem, "runner": "probe", "protocol": proto_dir.name,
                "expect": None, "actual": "pass" if rc == 0 else "block",
                "held": True, "custom": True,
            })

    save_results(results)
    return redirect(url_for("index"))


def _flush_applied():
    for name in list(get_applied()):
        comp_dir = LAB_DIR / "components" / name
        asset_remove = comp_dir / "asset-remove.sh"
        if asset_remove.exists():
            subprocess.run(
                ["docker", "cp", str(asset_remove), f"{ASSET}:/tmp/asset-remove.sh"],
                capture_output=True,
            )
            subprocess.run(
                ["docker", "exec", ASSET, "/bin/sh", "/tmp/asset-remove.sh"],
                capture_output=True,
            )
        remove_sh = comp_dir / "remove.sh"
        if remove_sh.exists():
            subprocess.run(
                ["docker", "cp", str(remove_sh), f"{BOUNDARY}:/tmp/component-remove.sh"],
                capture_output=True,
            )
            subprocess.run(["docker", "exec", BOUNDARY, "/bin/sh", "/tmp/component-remove.sh"])
    APPLIED_FILE.write_text("")


def _write_script(path, code):
    """Write shell script with Unix line endings."""
    path.write_text(code.replace('\r\n', '\n').replace('\r', '\n'))
    path.chmod(0o755)


def _apply_component_scripts(name):
    """Copy and run apply.sh on boundary, and asset.sh on asset if present."""
    comp_dir = LAB_DIR / "components" / name
    apply_sh = comp_dir / "apply.sh"
    subprocess.run(
        ["docker", "cp", str(apply_sh), f"{BOUNDARY}:/tmp/component-apply.sh"], check=True
    )
    subprocess.run(["docker", "exec", BOUNDARY, "/bin/sh", "/tmp/component-apply.sh"])
    asset_sh = comp_dir / "asset.sh"
    if asset_sh.exists():
        subprocess.run(
            ["docker", "cp", str(asset_sh), f"{ASSET}:/tmp/asset-apply.sh"], check=True
        )
        subprocess.run(["docker", "exec", ASSET, "/bin/sh", "/tmp/asset-apply.sh"])


@app.route("/apply-component/<name>", methods=["POST"])
def apply_component(name):
    """Apply a saved component by name, flushing whatever is current."""
    apply_sh = LAB_DIR / "components" / name / "apply.sh"
    if not apply_sh.exists():
        flash(f"No apply.sh for: {name}")
        return redirect(url_for("index"))
    _flush_applied()
    _apply_component_scripts(name)
    APPLIED_FILE.write_text(name)
    return redirect(url_for("index"))


@app.route("/build-and-apply", methods=["POST"])
def build_and_apply():
    name = request.form.get("name", "").strip()
    apply_code = request.form.get("apply_code", "")
    if not name:
        flash("Give the defence a name.")
        return redirect(url_for("index"))
    comp_dir = LAB_DIR / "components" / name
    comp_dir.mkdir(exist_ok=True)
    apply_sh = comp_dir / "apply.sh"
    _write_script(apply_sh, apply_code)
    remove_sh = comp_dir / "remove.sh"
    if not remove_sh.exists():
        _write_script(remove_sh, DEFAULT_REMOVE)
    _flush_applied()
    _apply_component_scripts(name)
    APPLIED_FILE.write_text(name)
    return redirect(url_for("index"))


@app.route("/build", methods=["POST"])
def build():
    component = request.form.get("component", "").strip()
    if not component:
        flash("Select a component first.")
        return redirect(url_for("index"))
    if not (LAB_DIR / "components" / component / "apply.sh").exists():
        flash(f"No apply.sh for: {component}")
        return redirect(url_for("index"))
    _flush_applied()
    _apply_component_scripts(component)
    APPLIED_FILE.write_text(component)
    return redirect(url_for("index"))


@app.route("/remove/<name>", methods=["POST"])
def remove(name):
    comp_dir = LAB_DIR / "components" / name
    asset_remove = comp_dir / "asset-remove.sh"
    if asset_remove.exists():
        subprocess.run(
            ["docker", "cp", str(asset_remove), f"{ASSET}:/tmp/asset-remove.sh"],
            capture_output=True,
        )
        subprocess.run(
            ["docker", "exec", ASSET, "/bin/sh", "/tmp/asset-remove.sh"],
            capture_output=True,
        )
    remove_sh = comp_dir / "remove.sh"
    if remove_sh.exists():
        subprocess.run(
            ["docker", "cp", str(remove_sh), f"{BOUNDARY}:/tmp/component-remove.sh"], check=True
        )
        subprocess.run(["docker", "exec", BOUNDARY, "/bin/sh", "/tmp/component-remove.sh"])
    applied = get_applied()
    applied.discard(name)
    APPLIED_FILE.write_text("\n".join(sorted(applied)))
    return redirect(url_for("index", comp=name))


@app.route("/reset", methods=["POST"])
def reset():
    _flush_applied()
    r = subprocess.run(
        ["docker", "exec", BOUNDARY, "/bin/sh", "-c",
         "iptables -F FORWARD && iptables -P FORWARD ACCEPT && iptables -t nat -F PREROUTING && iptables -t nat -F POSTROUTING"],
        capture_output=True,
    )
    if r.returncode != 0:
        flash(f"Reset failed (is the lab running?): {r.stderr.decode().strip()}")
    RESULTS_FILE.unlink(missing_ok=True)
    BRIEF_FILE.write_text("1")
    return redirect(url_for("index"))


def _nav_reset():
    """Flush applied components (including asset state) and reset all iptables."""
    _flush_applied()
    RESULTS_FILE.unlink(missing_ok=True)
    subprocess.run(
        ["docker", "exec", BOUNDARY, "/bin/sh", "-c",
         "iptables -F FORWARD && iptables -P FORWARD ACCEPT && iptables -t nat -F PREROUTING && iptables -t nat -F POSTROUTING"]
    )


@app.route("/prev", methods=["POST"])
def prev_brief():
    n = current_brief_num()
    if n <= 1:
        flash("Already at the first brief.")
        return redirect(url_for("index"))
    _nav_reset()
    BRIEF_FILE.write_text(str(n - 1))
    return redirect(url_for("index"))


@app.route("/next", methods=["POST"])
def next_brief():
    n = current_brief_num()
    if not glob.glob(str(LAB_DIR / "briefs" / f"{n+1:02d}-*.toml")):
        flash("End of ladder.")
        return redirect(url_for("index"))
    _nav_reset()
    BRIEF_FILE.write_text(str(n + 1))
    return redirect(url_for("index"))


@app.route("/probe/save", methods=["POST"])
def save_probe():
    name = request.form.get("name", "").strip()
    protocol = request.form.get("protocol", "modbus").strip()
    code = request.form.get("code", "")
    if not name:
        flash("Probe needs a name.")
        return redirect(url_for("index"))
    dest_dir = LAB_DIR / "probe" / "custom" / protocol
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{name}.py"
    dest.write_text(code)
    dest.chmod(0o755)
    return redirect(url_for("index"))


@app.route("/probe/delete/<protocol>/<name>", methods=["POST"])
def delete_probe(protocol, name):
    (LAB_DIR / "probe" / "custom" / protocol / f"{name}.py").unlink(missing_ok=True)
    return redirect(url_for("index"))


@app.route("/defence/save", methods=["POST"])
def save_defence():
    name = request.form.get("name", "").strip()
    apply_code = request.form.get("apply_code", "")
    if not name:
        flash("Defence needs a name.")
        return redirect(url_for("index"))
    comp_dir = LAB_DIR / "components" / name
    comp_dir.mkdir(exist_ok=True)
    _write_script(comp_dir / "apply.sh", apply_code)
    _write_script(comp_dir / "remove.sh", DEFAULT_REMOVE)
    return redirect(url_for("index", comp=name))


@app.route("/defence/delete/<name>", methods=["POST"])
def delete_defence(name):
    comp_dir = LAB_DIR / "components" / name
    if comp_dir.exists():
        shutil.rmtree(comp_dir)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
