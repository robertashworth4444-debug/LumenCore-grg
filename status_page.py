#!/usr/bin/env python3
import json, subprocess, os, time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
app = FastAPI()

def get_health():
    try:
        r = subprocess.run(["curl","-s","http://127.0.0.1:9110/health"],capture_output=True,text=True,timeout=3)
        return json.loads(r.stdout)
    except: return {}

def sysinfo():
    out = subprocess.getoutput("uptime").strip()
    load = out.split("load average:")[-1].strip() if "load average" in out else out
    disk = subprocess.getoutput("df -h / | awk 'NR==2{print $5}'").strip()
    mem = subprocess.getoutput("free -m | awk '/Mem/{printf(\"%s/%s MB\",$3,$2)}'").strip()
    return dict(load=load,disk=disk,mem=mem)

@app.get("/status", response_class=HTMLResponse)
def status_html():
    h = get_health(); s = sysinfo()
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    body = f"""
    <style>
      body{{font-family:system-ui;background:#0b132b;color:#fff;text-align:center;padding:40px}}
      .box{{background:#1c2541;margin:auto;max-width:800px;padding:30px;border-radius:14px;box-shadow:0 0 30px #0005}}
      h1{{color:#ffd166}}
      table{{margin:auto;color:#cbd5e1;font-size:1rem}}
      td,th{{padding:6px 12px}}
    </style>
    <div class="box">
      <h1>LumenCore Live Status</h1>
      <p><b>Last Proof:</b> {h.get('date_file','—')}</p>
      <p><b>Champions:</b> {h.get('totals',{}).get('champions','—')}</p>
      <table>
        <tr><th>System Load</th><td>{s['load']}</td></tr>
        <tr><th>Disk Usage</th><td>{s['disk']}</td></tr>
        <tr><th>Memory</th><td>{s['mem']}</td></tr>
        <tr><th>Generated</th><td>{ts}</td></tr>
      </table>
      <p><a href="/reports/latest_proof.pdf" style="color:#ffd166;text-decoration:none;">Download Latest Proof</a></p>
    </div>
    """
    return HTMLResponse(body)

@app.get("/status/json", response_class=JSONResponse)
def status_json():
    return {"system":sysinfo(),"health":get_health(),"timestamp":time.time()}
