import os, json, time, glob
from prometheus_client import start_http_server, Gauge
from collections import deque
BASE="/opt/lumen-core"; STORAGE=f"{BASE}/storage"; PORT=int(os.environ.get("METRICS_PORT","9108"))
g_trials_total=Gauge("lumencore_trials_total","Total trials observed",["colony"])
g_trials_rate=Gauge("lumencore_trials_rate","Trials/sec (recent)",["colony"])
g_champions_total=Gauge("lumencore_champions_total","Promotions detected",["colony"])
g_path_ok_ratio=Gauge("lumencore_path_ok_ratio","Share of trials with path_ok==true",["colony"])
g_last_heartbeat=Gauge("lumencore_last_heartbeat","Unix ts of last trial",["colony"])
g_colonies_up=Gauge("lumencore_colonies_up","How many colonies appear healthy (>=1 trial seen)")
def iter_trials(p):
    try:
        with open(p,"r",errors="ignore") as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try: yield json.loads(line)
                except: pass
    except FileNotFoundError: return
def scan_colony(cdir):
    tfile=os.path.join(cdir,"trials.log")
    total=champs=ok=last_ts=0; recent=deque(maxlen=200)
    for rec in iter_trials(tfile) or []:
        total+=1
        if rec.get("path_ok"): ok+=1
        if "promoted" in json.dumps(rec).lower(): champs+=1
        last_ts=int(rec.get("ts",0)); recent.append(last_ts)
    rate=0.0
    if len(recent)>2:
        dt=(recent[-1]-recent[0])
        if dt>0: rate=(len(recent)-1)/dt
    ratio=(ok/total) if total else 0.0
    return dict(total=total,champs=champs,ratio=ratio,last_ts=last_ts,rate=rate)
def main():
    start_http_server(PORT)
    while True:
        up=0
        for cdir in sorted(glob.glob(f"{STORAGE}/colony-*")):
            colony=os.path.basename(cdir).split("-")[-1]
            s=scan_colony(cdir)
            if not s: continue
            up += 1 if s["total"]>0 else 0
            g_trials_total.labels(colony).set(s["total"])
            g_trials_rate.labels(colony).set(s["rate"])
            g_champions_total.labels(colony).set(s["champs"])
            g_path_ok_ratio.labels(colony).set(s["ratio"])
            g_last_heartbeat.labels(colony).set(s["last_ts"])
        g_colonies_up.set(up)
        time.sleep(5)
if __name__=="__main__": main()
