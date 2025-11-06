#!/usr/bin/env python3
import time, requests, os, sys

CHECKS = {
    "exporter": "http://127.0.0.1:9105/metrics",
    "grafana":  "http://127.0.0.1:3000/api/health"
}
WINDOW = os.getenv("MAINT_WINDOW","02:45-03:15")
INTERVAL = 30
FLAG = "/opt/lumen-core/.guardrail_pause"

def in_window():
    h, m = time.strftime("%H"), time.strftime("%M")
    now = int(h)*60+int(m)
    start,end=[sum(int(x)*60**i for i,x in enumerate(reversed(t.split(':')))) for t in WINDOW.split('-')]
    return start<=now<=end

while True:
    pause=False
    # maintenance window
    if in_window(): pause=True
    # exporter health
    for name,url in CHECKS.items():
        try:
            r=requests.get(url,timeout=3)
            if r.status_code!=200: pause=True
        except: pause=True
    if pause and not os.path.exists(FLAG):
        open(FLAG,"w").close()
        print("🔒 GuardRail: Paused heals")
    elif not pause and os.path.exists(FLAG):
        os.remove(FLAG)
        print("✅ GuardRail: Unpaused heals")
    time.sleep(INTERVAL)
