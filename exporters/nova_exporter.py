#!/usr/bin/env python3
import json, sqlite3, time, requests, re
from fastapi import FastAPI, Response
import uvicorn

DB = "/opt/lumen-core/incidents.db"
NATS_VARZ = "http://127.0.0.1:8222/varz"

app = FastAPI(title="NovaCore Exporter", version="0.2")

def prom_kv(name, value, labels=None):
    if labels:
        label_str = ",".join([f'{k}="{v}"' for k,v in labels.items()])
        return f'{name}{{{label_str}}} {value}\n'
    return f"{name} {value}\n"

def parse_slo_latency_ms(s):
    # Accept "latency-p95<500ms" style if provided; default 500
    if not isinstance(s, str): return 500
    m = re.search(r'latency-p95<(\d+)ms', s)
    return int(m.group(1)) if m else 500

@app.get("/metrics")
def metrics():
    lines = []
    now = int(time.time())

    # --- NATS /varz ---
    try:
        v = requests.get(NATS_VARZ, timeout=2).json()
        lines.append(prom_kv("nats_connections", v.get("connections",0)))
        lines.append(prom_kv("nats_routes", v.get("routes",0)))
        lines.append(prom_kv("nats_mem_bytes", v.get("mem",0)))
        lines.append(prom_kv("nats_cpu_pct", v.get("cpu",0)))
        js = v.get("jetstream",{})
        mem = js.get("memory",0)
        store = js.get("store",0)
        if isinstance(mem,str): 
            try: mem = float(mem.split()[0])
            except: mem = 0
        if isinstance(store,str):
            try: store = float(store.split()[0])
            except: store = 0
        lines.append(prom_kv("nats_jetstream_mem_bytes", mem))
        lines.append(prom_kv("nats_jetstream_store_bytes", store))
    except Exception:
        lines.append(prom_kv("nats_scrape_error", 1))

    # --- WhiteHole incidents from SQLite ---
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        # Totals and severity
        cur.execute("SELECT COUNT(*) FROM incidents"); total = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM incidents WHERE severity='high'"); high = cur.fetchone()[0] or 0
        lines.append(prom_kv("whitehole_incidents_total", total))
        lines.append(prom_kv("whitehole_incidents_high_total", high))

        # Action success/fail + avg durations
        cur.execute("""
          WITH r AS (
            SELECT json_each.value AS res
            FROM incidents, json_each(json_extract(outcome_json, '$.results'))
          )
          SELECT 
            COALESCE(json_extract(res,'$.action'),'none') AS action,
            SUM(CASE COALESCE(json_extract(res,'$.ok'),0) WHEN 1 THEN 1 ELSE 0 END) AS ok,
            SUM(CASE COALESCE(json_extract(res,'$.ok'),0) WHEN 0 THEN 1 ELSE 0 END) AS fail,
            AVG(COALESCE(json_extract(res,'$.duration_ms'),0)) AS avg_ms
          FROM r
          GROUP BY action
        """)
        for action, ok, fail, avg_ms in cur.fetchall():
            lines.append(prom_kv("whitehole_actions_ok_total", ok or 0, {"action": action}))
            lines.append(prom_kv("whitehole_actions_fail_total", fail or 0, {"action": action}))
            lines.append(prom_kv("whitehole_actions_avg_duration_ms", round(avg_ms or 0, 2), {"action": action}))

        # SLO breaches (simple heuristics)
        # latency breach: metrics.latency_p95_ms > threshold (from context.slo or default 500ms)
        cur.execute("""
          SELECT 
            COALESCE(service,'default') AS svc,
            SUM(CASE 
                WHEN CAST(json_extract(event_json,'$.metrics.latency_p95_ms') AS INTEGER) >
                     (CASE 
                        WHEN json_extract(event_json,'$.context.slo') IS NOT NULL 
                        THEN 0  -- parse in Python later if needed
                        ELSE 500 
                      END)
                THEN 1 ELSE 0 END) AS latency_breach,
            SUM(CASE 
                WHEN CAST(1000*json_extract(event_json,'$.metrics.cpu') AS INTEGER) >= 900 
                THEN 1 ELSE 0 END) AS cpu_breach
          FROM incidents
          GROUP BY svc
        """)
        rows = cur.fetchall()
        for svc, lb, cb in rows:
            lines.append(prom_kv("whitehole_latency_breaches_total", lb or 0, {"service": svc}))
            lines.append(prom_kv("whitehole_cpu_breaches_total", cb or 0, {"service": svc}))

        conn.close()
    except Exception:
        lines.append(prom_kv("whitehole_incident_scrape_error", 1))

    lines.append(prom_kv("nova_exporter_timestamp", now))
    return Response(content="".join(lines), media_type="text/plain; version=0.0.4")

if __name__ == "__main__":
    uvicorn.run("nova_exporter:app", host="0.0.0.0", port=9105)
