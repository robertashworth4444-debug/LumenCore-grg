#!/usr/bin/env python3
import sqlite3, time, json, os
from fastapi import FastAPI, Response

DB = "/opt/lumen-core/incidents.db"
COOLDOWN = int(os.getenv("WH_COOLDOWN", "120"))
LOOKBACK = int(os.getenv("WH_LOOKBACK_SEC", "3600"))

def get_snapshot():
    now = int(time.time())
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
      WITH r AS (
        SELECT ts, json_each.value AS res, json_extract(event_json,'$.service') AS svc
        FROM incidents, json_each(json_extract(outcome_json,'$.results'))
      )
      SELECT svc,
             COALESCE(json_extract(res,'$.action'),'none') AS action,
             SUM(CASE WHEN COALESCE(json_extract(res,'$.ok'),0)=1 THEN 1 ELSE 0 END) AS ok,
             SUM(CASE WHEN COALESCE(json_extract(res,'$.ok'),0)=0 THEN 1 ELSE 0 END) AS fail,
             MAX(ts) AS last_ts
      FROM r
      GROUP BY svc,action
    """)
    rows = cur.fetchall()
    conn.close()
    data = []
    for svc, action, ok, fail, last_ts in rows:
        last_ts = int(last_ts or 0)
        cd_left = max(0, (last_ts + COOLDOWN) - now)
        score = round(min(1.0, (ok/(ok+fail+1e-9))*0.8 + 0.2),3)
        data.append({
            "service": svc, "action": action,
            "ok_recent": ok, "fail_recent": fail,
            "score_est": score, "cooldown_left": cd_left,
            "last_ts": last_ts
        })
    return {"ts": now, "lookback_sec": LOOKBACK, "cooldown_sec": COOLDOWN, "actions": data}

app = FastAPI(title="WhiteHole Policy View")

@app.get("/policy")
def policy():
    snap = get_snapshot()
    return Response(content=json.dumps(snap, indent=2), media_type="application/json")

from fastapi import Body
import sqlite3, time

@app.post("/policy/reset")
def policy_reset(payload: dict = Body(...)):
    """
    Reset cooldowns and/or history counters.
    payload:
      { "service":"genesis-node", "action":"cpu_relief" }
      { "all": true }
      { "service":"genesis-node" }  # all actions for service
    """
    target_service = payload.get("service")
    target_action  = payload.get("action")
    reset_all      = bool(payload.get("all", False))

    # Cooling off is tracked implicitly via last_ts in incidents.
    # We'll insert a synthetic "reset" record with ts = 0 to neutralize cooldown.
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS incidents (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts INTEGER, service TEXT, severity TEXT,
      event_json TEXT, outcome_json TEXT
    )""")

    if reset_all:
        cur.execute("DELETE FROM incidents")  # full reset
        conn.commit()
        return {"status":"ok","reset":"all"}

    # targeted delete for outcome results of a given (service, action)
    if target_service and target_action:
        cur.execute("""
          DELETE FROM incidents
          WHERE service=? AND outcome_json LIKE '%' || ? || '%'
        """, (target_service, target_action))
        conn.commit()
        return {"status":"ok","reset":{"service":target_service,"action":target_action}}

    if target_service:
        cur.execute("DELETE FROM incidents WHERE service=?", (target_service,))
        conn.commit()
        return {"status":"ok","reset":{"service":target_service}}

    return {"status":"noop","msg":"nothing matched"}
