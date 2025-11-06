#!/usr/bin/env python3
import os, time, random, json, requests

URL = os.getenv("WHITEHOLE_URL","http://127.0.0.1:9001/event")
SERVICES = ["genesis-node","alpha-api","beta-worker"]
PODS = ["api-7f9","api-8c2","wrk-1a2"]

def send(cpu, lat, svc, pod):
    payload = {
        "type":"metric.alert",
        "source":"chaos_driver",
        "service": svc,
        "severity":"high" if cpu>0.92 or lat>1500 else "warn",
        "labels":{"pod":pod,"route":"/api"},
        "metrics":{"cpu":round(cpu,3),"latency_p95_ms":int(lat)}
    }
    r = requests.post(URL, json=payload, timeout=3)
    print(f"{svc}:{pod} cpu={cpu} lat={lat} -> {r.status_code}")

if __name__=="__main__":
    while True:
        svc = random.choice(SERVICES)
        pod = random.choice(PODS)
        cpu = random.uniform(0.75, 0.99)
        lat = random.uniform(400, 2500)
        # spike probability
        if random.random() < 0.35: cpu = random.uniform(0.92,0.99)
        if random.random() < 0.35: lat = random.uniform(1200,2500)
        send(cpu, lat, svc, pod)
        time.sleep(random.uniform(0.6, 1.8))
