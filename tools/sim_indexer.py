import os, re, json, time, pathlib
from datetime import datetime

ROOT = "/opt/lumen-core"
REPORTS = os.path.join(ROOT, "reports")
SITE = os.path.join(ROOT, "site", "console")
INDEX_JSON = os.path.join(REPORTS, "sim_index.json")
PRESTIGE_LATEST_LINK = os.path.join(REPORTS, "prestige", "latest")

def find_prestige_runs():
def find_nova_runs():
    runs=[]
    for p in pathlib.Path(ROOT).rglob("nova_run_*"):
        if p.is_dir():
            entry={"type":"nova","path":str(p),"timestamp":None,"artifacts":[]}
            m=re.search(r'nova_run_(\d{8}T\d{6}Z)', p.name)
            if m: entry["timestamp"]=m.group(1)
            else: entry["timestamp"]=datetime.datetime.utcfromtimestamp(p.stat().st_mtime).isoformat()+"Z"
            s=p/"summary.json"
            if s.exists():
                try: entry["summary"]=json.loads(s.read_text())
                except Exception: pass
            for fn in ["grid_results.csv","best_timeseries.csv","plot_timeseries.png","plot_psd.png","plot_heatmap.png","Harmonic_Report.pdf"]:
                fp=p/fn
                if fp.exists(): entry["artifacts"].append(str(fp))
            runs.append(entry)
    return runs

    runs=[]
    # any dir anywhere under ROOT named prestige_run_*
    for p in pathlib.Path(ROOT).rglob("prestige_run_*"):
        if p.is_dir():
            summary = p / "summary.json"
            entry = {"type":"prestige","path":str(p),"timestamp":None,"best":None,"artifacts":[]}
            # timestamp from folder name or mtime
            m = re.search(r'prestige_run_(\d{8}T\d{6}Z)', p.name)
            if m:
                entry["timestamp"] = m.group(1)
            else:
                entry["timestamp"] = datetime.utcfromtimestamp(p.stat().st_mtime).isoformat()+"Z"
            # summary
            if summary.exists():
                try:
                    js = json.loads(summary.read_text())
                    entry["summary"] = js
                    entry["best"] = js.get("best_config")
                except Exception:
                    pass
            # common artifacts
            for fn in ["coarse_grid.csv","best_timeseries.csv","heatmap_score.png",
                       "surface_score3D.png","plot_timeseries.png","plot_psd.png","Prestige_Report.pdf"]:
                fp = p / fn
                if fp.exists(): entry["artifacts"].append(str(fp))
            runs.append(entry)
    return runs

def find_reports():
    items=[]
    if not os.path.isdir(REPORTS):
        return items
    for f in pathlib.Path(REPORTS).glob("*"):
        name=f.name
        if f.is_file() and re.search(r"(sim_results|sim_summary|sim_speedups|thermal_.*|LumenCore_.*Deck\.pdf)$", name):
            items.append({
                "type":"report",
                "path":str(f),
                "name":name,
                "timestamp":datetime.utcfromtimestamp(f.stat().st_mtime).isoformat()+"Z"
            })
    return items

def ensure_latest_link(runs):
    # newest prestige by timestamp (string or iso)
    if not runs: return None
    def ts(r):
        # normalize into sortable number
        t=r.get("timestamp","")
        try:
            if "T" in t and t.endswith("Z") and len(t)>=16:  # 20250101T010203Z
                return t
            return datetime.fromisoformat(t.replace("Z","")).isoformat()
        except Exception:
            return ""
    newest = sorted(runs, key=lambda r: ts(r), reverse=True)[0]
    linkdir = pathlib.Path(PRESTIGE_LATEST_LINK)
    linkdir.parent.mkdir(parents=True, exist_ok=True)
    try:
        if linkdir.exists() or linkdir.is_symlink():
            linkdir.unlink()
        linkdir.symlink_to(newest["path"], target_is_directory=True)
    except Exception:
        pass
    return newest

def write_index(all_items):
    pathlib.Path(REPORTS).mkdir(parents=True, exist_ok=True)
    idx = {
        "generated_utc": datetime.utcnow().isoformat()+"Z",
        "count": len(all_items),
        "items": all_items
    }
    with open(INDEX_JSON,"w") as f:
        json.dump(idx,f,indent=2)
    return INDEX_JSON

def write_html(all_items):
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>LumenCore — Simulation Index</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700&display=swap" rel="stylesheet">
<style>
body{font-family:Inter,system-ui,Arial;background:#05070b;color:#e6eef7;margin:0}
h1{margin:18px;text-align:center;background:linear-gradient(90deg,#00ffd0,#2d8cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.wrapper{max-width:1100px;margin:0 auto;padding:16px}
.card{background:#0b1524;border-radius:12px;padding:12px;margin:10px 0;box-shadow:0 0 14px rgba(0,255,208,.08)}
.badge{background:rgba(255,255,255,.08);padding:3px 8px;border-radius:999px;margin-left:8px}
a{color:#00ffd0;text-decoration:none}
a:hover{text-decoration:underline}
.small{color:#9fb1c7;font-size:.85rem}
</style></head><body>
<h1>🧪 LumenCore Simulation Index</h1>
<div class="wrapper">
"""
    if not all_items:
        html += "<p>No runs found yet. When PRESTIGE or other sims produce results, they will appear here.</p>"
    else:
        for it in all_items:
            if it["type"]=="prestige":
                html += f'<div class="card"><b>PRESTIGE Run</b><span class="badge">{it.get("timestamp","")}</span><br>'
                html += f'<span class="small">Path: {it["path"]}</span><br>'
                if it.get("best"):
                    b=it["best"]
                    html += f'<div class="small">Best: f0={b.get("f0")}, df={b.get("df")}, noise={b.get("noise")}, gain_c={b.get("gain_c")}</div>'
                if it.get("artifacts"):
                    html += '<div class="small">Artifacts: '
                    html += " • ".join([f'<a href="{a.replace(ROOT,"")}" target="_blank">{os.path.basename(a)}</a>' for a in it["artifacts"]])
                    html += '</div>'
                html += "</div>"
            else:
                rel = it["path"].replace(ROOT,"")
                html += f'<div class="card"><b>Report</b><span class="badge">{it.get("timestamp","")}</span><br>'
                html += f'<a href="{rel}" target="_blank">{os.path.basename(it["path"])}</a></div>'
    html += f"""
<div class="small">Index generated {datetime.utcnow().isoformat()}Z</div>
</div></body></html>
"""
    out = os.path.join(SITE, "sim-index.html")
    pathlib.Path(SITE).mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.write(html)
    return out

def main():
    prestige = find_prestige_runs()
    nova  = find_nova_runs()
    reports  = find_reports()
    newest = ensure_latest_link(prestige)
    items = sorted(prestige + nova + reports, key=lambda x: x.get("timestamp",""), reverse=True)
    jpath = write_index(items)
    hpath = write_html(items)
    print("✅ Indexed items:", len(items))
    if newest: print("✅ Latest PRESTIGE:", newest.get("timestamp",""), "->", newest["path"])
    print("📄 JSON:", jpath)
    print("🌐 HTML:", hpath)

if __name__ == "__main__":
    main()
