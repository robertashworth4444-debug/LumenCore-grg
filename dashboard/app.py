import os, time, json, subprocess, psutil, pathlib
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE="/opt/lumen-core"; WEB="/var/www/lumen-core"; RPT=f"{BASE}/reports"
env = Environment(loader=FileSystemLoader(f"{BASE}/dashboard/templates"),
                  autoescape=select_autoescape())
app = FastAPI()
app.mount("/static", StaticFiles(directory=f"{BASE}/dashboard/static"), name="static")

def read_health():
    try:
        out = subprocess.run(["curl","-s","http://127.0.0.1:9110/health"],
                             capture_output=True,text=True,timeout=3)
        return json.loads(out.stdout or "{}")
    except Exception:
        return {}

def proof_info():
    try:
        p = sorted(pathlib.Path(RPT).glob("*_summary.csv"))[-1]
    except Exception:
        p = None
    dt = None
    if p:
        try:
            ts = p.stat().st_mtime
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception: pass
    return dict(file=str(p) if p else None,
                age_min=( (datetime.now(timezone.utc)-dt).total_seconds()/60 if dt else None),
                display=dt.strftime("%Y-%m-%d %H:%M UTC") if dt else "—")

def sys_metrics():
    cpu = psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else psutil.cpu_percent()
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return dict(cpu_1m=round(cpu,2),
                mem_pct=round(mem.percent,1),
                disk_pct=round(disk.percent,1))

SPARK=[]
def point():
    h = read_health()
    s = sys_metrics()
    pi = proof_info()
    SPARK.append({"t": int(time.time()), "cpu": s["cpu_1m"], "mem": s["mem_pct"]})
    if len(SPARK) > 200: SPARK.pop(0)
    return dict(now=int(time.time()), sys=s, proof=pi, health=h, spark=SPARK)

@app.get("/api/summary", response_class=JSONResponse)
def api_summary(): return point()

@app.get("/", response_class=HTMLResponse)
def ui(request: Request, mode: str|None=None):
    tpl = env.get_template("pitch.html" if (mode=="pitch") else "dashboard.html")
    return tpl.render()

