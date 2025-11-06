import os, csv, json, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
BASE="/opt/lumen-core"; OUT=f"{BASE}/reports"; HOST="0.0.0.0"; PORT=int(os.environ.get("HEALTH_PORT","9110"))
def latest_summary():
    if not os.path.isdir(OUT): return None
    files=sorted([f for f in os.listdir(OUT) if f.endswith("_summary.csv")])
    if not files: return None
    path=os.path.join(OUT,files[-1]); T=0; OKw=0.0; CH=0; rows=[]
    with open(path,newline="") as f:
        r=csv.DictReader(f)
        for row in r:
            try:
                t=int(row["trials"]); rr=float(row["ok_ratio"]); ch=int(row["champions"])
                T+=t; OKw+=t*rr; CH+=ch; rows.append(row)
            except: pass
    return {
      "date_file": os.path.basename(path).split("_summary.csv")[0],
      "summary_csv": os.path.basename(path),
      "totals": {"trials":T,"avg_ok_ratio": (OKw/T if T else 0.0),"champions":CH},
      "colonies": rows, "generated_at": int(time.time())
    }
class H(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/health":
            snap=latest_summary() or {"message":"No summary yet.","generated_at":int(time.time())}
            b=json.dumps(snap).encode(); self.send_response(200)
            self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b)))
            self.end_headers(); self.wfile.write(b); return
        if self.path=="/":
            html='''<!doctype html><meta charset="utf-8"><title>LumenCore Cockpit</title>
<style>body{font-family:system-ui;margin:24px} .card{border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0}</style>
<h1>🔭 LumenCore — Read-Only Cockpit</h1>
<div class=card><div id=top>Loading…</div></div>
<div class=card><h3>Colonies (yesterday)</h3><div id=cols></div></div>
<div class=card><h3>CSV Archive</h3><a href="/reports/">/reports/</a></div>
<script>
(async()=>{
 const r=await fetch('/health'); const j=await r.json();
 const ts=new Date((j.generated_at||Date.now()/1000)*1000).toLocaleString();
 if(j.totals){ document.getElementById('top').innerHTML=
   `<b>Date file:</b> ${j.date_file} • <b>Trials:</b> ${j.totals.trials.toLocaleString()} • <b>Avg ok:</b> ${(100*j.totals.avg_ok_ratio).toFixed(2)}% • <b>Champions:</b> ${j.totals.champions} • <span style="color:#666">Updated ${ts}</span>`;}
 else { document.getElementById('top').innerText=j.message||'No data'; }
 const root=document.getElementById('cols'); (j.colonies||[]).forEach(r=>{
   const d=document.createElement('div'); d.className='card';
   d.innerHTML=`<b>${r.colony}</b> — ${r.date}<br>Trials: <b>${r.trials}</b> • OK: <b>${(100*parseFloat(r.ok_ratio)).toFixed(2)}%</b> • Champions: <b>${r.champions}</b> • Window: ${r.window_s}s`;
   root.appendChild(d);
 });
})();
</script>'''
            b=html.encode(); self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(b)))
            self.end_headers(); self.wfile.write(b); return
        self.directory=BASE
        return super().do_GET()
def main():
    os.chdir(BASE)
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
if __name__=="__main__": main()

# --- static file handler for /reports/ (added by Luma) ---
import mimetypes
from urllib.parse import unquote
class FileHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/reports/"):
            path = Path(BASE) / unquote(self.path.lstrip("/"))
            if path.is_file():
                mime, _ = mimetypes.guess_type(path)
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", str(path.stat().st_size))
                self.end_headers()
                with open(path, "rb") as f: self.wfile.write(f.read())
                return
        return super().do_GET()
Handler = FileHandler
