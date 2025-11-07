import os, re, json, pathlib, datetime, hashlib

ROOT = "/opt/lumen-core"
REPORTS = os.path.join(ROOT, "reports")
CATALOG = os.path.join(REPORTS, "catalog")      # canonical symlink catalog
INDEX_JSON = os.path.join(REPORTS, "sim_harvest.json")
HTML_OUT   = os.path.join(ROOT, "site", "console", "sim-index.html")

# Families & heuristics
FAMILIES = {
    "prestige":   {"run_glob": "prestige_run_*", "name_keys": ["prestige"]},
    "nova":       {"run_glob": "nova_run_*",     "name_keys": ["nova"]},
    "spiral":     {"run_glob": "spiral_run_*",   "name_keys": ["spiral", "spiral_demo", "golden", "fibonacci"]},
    "mycelium":   {"run_glob": "mycelium_run_*", "name_keys": ["mycelium"]},
    "whitehole":  {"run_glob": "whitehole_run_*","name_keys": ["whitehole","white-hole"]},
    "flowform":   {"run_glob": "flowform_run_*", "name_keys": ["flowform","flow_form","flow-form"]},
    "etherframe": {"run_glob": "etherframe_run_*","name_keys": ["etherframe","ether_frame"]},
    "thermal":    {"run_glob": "thermal_run_*", "name_keys": ["thermal","curved","flat"]},
    "kpi":        {"run_glob": "kpi_run_*",      "name_keys": ["kpi_run_"]},
    "roi":        {"run_glob": "roi_run_*",      "name_keys": ["roi_run_"]},
    "evo":        {"run_glob": "evo_*",          "name_keys": ["evo_leaderboard","evo_"]},
    "proof":      {"run_glob": "",               "name_keys": ["LumenCore_Proof","Harmonic_Report","Prestige_Report","InvestorDeck"]},
}

ART_PAT = re.compile(r"\.(csv|png|jpg|jpeg|gif|pdf|txt)$", re.I)
RUN_PAT = re.compile(r"([a-zA-Z]+)_run_(\d{8}T\d{6}Z)")

def utcstamp(path):
    try:
        return pathlib.Path.fromtimestamp(path.stat().st_mtime).isoformat()+"Z"
    except Exception:
        return datetime.datetime.utcnow().isoformat()+"Z"

def mklink(src, family, stamp):
    """Make canonical symlink under /reports/catalog/<family>/<stamp>/<basename>"""
    fam_dir = pathlib.Path(CATALOG) / family / stamp
    fam_dir.mkdir(parents=True, exist_ok=True)
    dst = fam_dir / src.name
    try:
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        dst.symlink_to(src.resolve())
    except Exception:
        pass
    return str(dst)

def harvest():
    root = pathlib.Path(ROOT)
    items = []   # list of dicts {family, kind, stamp, src, link, artifacts, ts}
    # 1) Folder-based runs (prestige/nova/spiral/... *_run_*)
    for fam, spec in FAMILIES.items():
        run_glob = spec.get("run_glob")
        if run_glob:
            for p in root.rglob(run_glob):
                if not p.is_dir(): continue
                m = RUN_PAT.search(p.name)
                stamp = m.group(2) if m else utcstamp(p)
                rec = {"family": fam, "kind": "run", "stamp": stamp,
                       "src": str(p), "artifacts": [], "ts": utcstamp(p)}
                # link artifacts in this dir
                for f in p.rglob("*"):
                    if f.is_file() and ART_PAT.search(f.name):
                        link = mklink(f, fam, stamp)
                        rec["artifacts"].append(link)
                items.append(rec)

    # 2) Loose artifacts in /reports (kpi/roi/evo/thermal/proofs etc.)
    rep = pathlib.Path(REPORTS)
    if rep.exists():
        for f in rep.rglob("*"):
            if not f.is_file(): continue
            if not ART_PAT.search(f.name): continue
            # determine family by name heuristic
            family = None
            low = f.name.lower()
            for fam, spec in FAMILIES.items():
                if any(k.lower() in low for k in spec["name_keys"]):
                    family = fam; break
            if family is None:
                # fallback: keep as "misc"
                family = "misc"
            # stamp from name or mtime
            m = RUN_PAT.search(f.name)
            stamp = m.group(2) if m else utcstamp(f)
            link = mklink(f, family, stamp)
            rec = {"family": family, "kind": "artifact", "stamp": stamp,
                   "src": str(f), "link": link, "artifacts": [link], "ts": utcstamp(f)}
            items.append(rec)

    # Dedup by (src path)
    seen = set(); dedup=[]
    for it in sorted(items, key=lambda x: x.get("ts","")):
        if it["src"] in seen: continue
        seen.add(it["src"]); dedup.append(it)

    # write json
    pathlib.Path(REPORTS).mkdir(parents=True, exist_ok=True)
    with open(INDEX_JSON,"w") as f:
        json.dump({"generated_utc": datetime.datetime.utcnow().isoformat()+"Z",
                   "count": len(dedup), "items": dedup}, f, indent=2)
    return dedup

def make_html(items):
    html = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>LumenCore — Simulation Index</title>',
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700&display=swap" rel="stylesheet">',
            '<style>body{font-family:Inter,system-ui,Arial;background:#05070b;color:#e6eef7;margin:0}h1{margin:18px;text-align:center;background:linear-gradient(90deg,#00ffd0,#2d8cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.wrap{max-width:1180px;margin:0 auto;padding:16px}.card{background:#0b1524;border-radius:12px;padding:12px;margin:10px 0;box-shadow:0 0 14px rgba(0,255,208,.08)}.fam{font-weight:700}.badge{background:rgba(255,255,255,.08);padding:2px 8px;border-radius:999px;margin-left:6px}.small{color:#9fb1c7;font-size:.85rem}a{color:#00ffd0;text-decoration:none}a:hover{text-decoration:underline}</style></head><body>',
            '<h1>🧪 LumenCore — Simulation Catalog</h1><div class="wrap">']
    if not items:
        html.append("<p>No runs indexed yet.</p>")
    else:
        # group by family then reverse chronological
        fams = {}
        for it in items: fams.setdefault(it["family"], []).append(it)
        for fam in sorted(fams.keys()):
            html.append(f'<div class="card"><span class="fam">{fam.upper()}</span> <span class="badge">{len(fams[fam])} items</span>')
            for it in sorted(fams[fam], key=lambda x: x.get("ts",""), reverse=True):
                rel = os.path.relpath(it.get("src",""), ROOT)
                html.append(f'<div class="small">• {it["kind"].upper()} {it.get("stamp","")} — <code>{rel}</code></div>')
                arts = it.get("artifacts",[])
                if arts:
                    html.append('<div class="small" style="margin-left:10px">')
                    for a in arts:
                        relA = os.path.relpath(a, ROOT)
                        html.append(f' <a href="/{relA}" target="_blank">{os.path.basename(a)}</a>')
                    html.append('</div>')
            html.append('</div>')
    html.append(f'<div class="small">Index generated {datetime.datetime.utcnow().isoformat()}Z</div></div></body></html>')
    pathlib.Path(HTML_OUT).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(HTML_OUT).write_text("\n".join(html))
    return HTML_OUT

if __name__ == "__main__":
    items = harvest()
    out = make_html(items)
    print(f"✅ Harvested {len(items)} items")
    print(f"📄 JSON: {INDEX_JSON}")
    print(f"🌐 HTML: {out}")
