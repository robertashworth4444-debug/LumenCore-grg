#!/usr/bin/env python3
import time, requests, os, re

EXPORTER="http://127.0.0.1:9105/metrics"
CONF_FILE="/etc/systemd/system/whitehole.service"

def extract(name):
    try:
        txt=requests.get(EXPORTER,timeout=3).text
        for line in txt.splitlines():
            if line.startswith(name): return float(re.findall(r"[-+]?[0-9]*\.?[0-9]+", line)[0])
    except: pass
    return 0.0

while True:
    ok=extract("whitehole_actions_ok_total")
    fail=extract("whitehole_actions_fail_total")
    rate = (fail/(ok+fail+1e-9))
    score = round(max(0.4, min(0.9, 0.9-rate*0.5)),2)
    os.system(f"sed -i 's|WH_MIN_SCORE=.*|WH_MIN_SCORE={score}|' {CONF_FILE}")
    print(f"[AutoTuner] Updated WH_MIN_SCORE -> {score}")
    os.system("systemctl daemon-reload && systemctl restart whitehole")
    time.sleep(600)
