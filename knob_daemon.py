import json, os, time, signal, sys, random
LIVE = os.path.join(os.path.dirname(__file__), "knobs", "live.json")
RUN = True
def stop(*_): 
    global RUN; RUN=False
signal.signal(signal.SIGINT, stop); signal.signal(signal.SIGTERM, stop)
os.makedirs(os.path.dirname(LIVE), exist_ok=True)
if not os.path.exists(LIVE):
    with open(LIVE,"w") as f: json.dump({"ENTRY_TH":0.004,"EXIT_TH":0.018,"TAKE_PROFIT_PCT":0.014,"STOP_LOSS_PCT":0.01}, f, indent=2)
print("[knobs] daemon online; writing heartbeats to knobs/live.json")
while RUN:
    try:
        with open(LIVE) as f: k=json.load(f)
        k["last_heartbeat"]=int(time.time())
        for fld in ("ENTRY_TH","EXIT_TH","TAKE_PROFIT_PCT","STOP_LOSS_PCT"):
            if fld in k: k[fld]=round(float(k[fld])*(1+random.uniform(-5e-4,5e-4)),6)
        with open(LIVE,"w") as f: json.dump(k,f,indent=2)
    except Exception as e:
        print("[knobs] error:",e, file=sys.stderr)
    time.sleep(5)
print("[knobs] shutdown")
