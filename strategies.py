from typing import Dict, Any, List, Tuple
import subprocess, shlex, json, time, os, sqlite3

DB = "/opt/lumen-core/incidents.db"
MIN_SCORE = float(os.getenv("WH_MIN_SCORE", "0.6"))
COOLDOWN = int(os.getenv("WH_COOLDOWN", "120"))            # seconds
LOOKBACK = int(os.getenv("WH_LOOKBACK_SEC", "3600"))       # seconds

# ---------- helpers ----------
def _run_timed(cmd: str) -> Dict[str, Any]:
    t0 = time.time()
    try:
        out = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT, timeout=60)
        dt = int((time.time() - t0) * 1000)
        return {"ok": True, "out": out.decode().strip(), "duration_ms": dt}
    except Exception as e:
        dt = int((time.time() - t0) * 1000)
        return {"ok": False, "err": str(e), "duration_ms": dt}

def _connect():
    try:
        conn = sqlite3.connect(DB)
        return conn
    except Exception:
        return None

def _recent_action_stats(conn, action: str, service: str) -> Tuple[int,int,int]:
    """
    Returns (ok_count, fail_count, last_ts) within LOOKBACK for (action, service).
    """
    if conn is None:
        return (0,0,0)
    now = int(time.time())
    lb = now - LOOKBACK
    cur = conn.cursor()
    # successes/failures
    cur.execute("""
      WITH r AS (
        SELECT ts, json_each.value AS res, json_extract(event_json,'$.service') AS svc
        FROM incidents, json_each(json_extract(outcome_json,'$.results'))
        WHERE ts >= ?
      )
      SELECT
        SUM(CASE WHEN COALESCE(json_extract(res,'$.ok'),0)=1 AND svc=? AND COALESCE(json_extract(res,'$.action'),'')=? THEN 1 ELSE 0 END) AS ok,
        SUM(CASE WHEN COALESCE(json_extract(res,'$.ok'),0)=0 AND svc=? AND COALESCE(json_extract(res,'$.action'),'')=? THEN 1 ELSE 0 END) AS fail
      FROM r
    """, (lb, service, action, service, action))
    row = cur.fetchone() or (0,0)
    ok, fail = int(row[0] or 0), int(row[1] or 0)

    # last timestamp for this action+service
    cur.execute("""
      WITH r AS (
        SELECT ts, json_each.value AS res, json_extract(event_json,'$.service') AS svc
        FROM incidents, json_each(json_extract(outcome_json,'$.results'))
      )
      SELECT MAX(ts) FROM r
      WHERE svc=? AND COALESCE(json_extract(res,'$.action'),'')=?
    """, (service, action))
    last_ts = int(cur.fetchone()[0] or 0)
    return (ok, fail, last_ts)

def _metric_base_score(metrics: Dict[str, Any]) -> float:
    """
    Heuristic: scale base score from metric severities.
    """
    cpu = float(metrics.get("cpu", 0.0))
    lat = float(metrics.get("latency_p95_ms", 0.0))
    base = 0.0
    # CPU weight
    if cpu >= 0.95: base += 0.45
    elif cpu >= 0.90: base += 0.35
    elif cpu >= 0.80: base += 0.20
    # Latency weight
    if lat >= 2000: base += 0.45
    elif lat >= 1200: base += 0.35
    elif lat >= 800: base += 0.20
    return min(base, 0.9)

def _history_boost(ok: int, fail: int) -> float:
    total = ok + fail
    if total == 0:
        return 0.05  # tiny prior
    wr = ok / max(1, total)  # win rate
    # curve: 0.0..1.0 -> -0.2..+0.2 centered ~0.5
    return max(-0.2, min(0.2, (wr - 0.5) * 0.5 * 2.0))

def _cooldown_left(now: int, last_ts: int) -> int:
    if last_ts <= 0: return 0
    rem = (last_ts + COOLDOWN) - now
    return rem if rem > 0 else 0

# ---------- main policy ----------
def decide_and_act(ev: Dict[str, Any]) -> Dict[str, Any]:
    t = ev.get("type","")
    sev = ev.get("severity","info")
    svc = ev.get("service","default")
    labels = ev.get("labels",{}) or {}
    metrics = ev.get("metrics",{}) or {}

    # candidate actions
    actions: List[Dict[str,str]] = []
    if t=="metric.alert" and float(metrics.get("cpu",0)) >= 0.90:
        pod = labels.get("pod","unknown")
        actions.append({"name":"cpu_relief","cmd":f"/opt/lumen-core/runbooks/cpu_relief.sh {svc} {pod}"})
    if t=="metric.alert" and float(metrics.get("latency_p95_ms",0)) >= 1000:
        route = labels.get("route","/api")
        actions.append({"name":"latency_hotfix","cmd":f"/opt/lumen-core/runbooks/latency_hotfix.sh {svc} {route}"})

    policy_decisions = []
    results = []
    now = int(time.time())
    base = _metric_base_score(metrics)
    conn = _connect()

    for a in actions:
        name = a["name"]
        ok_c, fail_c, last_ts = _recent_action_stats(conn, name, svc)
        hist = _history_boost(ok_c, fail_c)
        score = max(0.0, min(1.0, base + hist))
        cd_left = _cooldown_left(now, last_ts)

        decision = {"action": name, "score": round(score,3), "cooldown_left": cd_left,
                    "ok_recent": ok_c, "fail_recent": fail_c, "base": round(base,3), "hist": round(hist,3)}

        if cd_left > 0:
            decision["decision"] = "skip_cooldown"
            policy_decisions.append(decision)
            continue
        if score < MIN_SCORE:
            decision["decision"] = "skip_low_confidence"
            policy_decisions.append(decision)
            continue

        # execute
        res = _run_timed(a["cmd"])
        res["action"] = name
        results.append(res)
        decision["decision"] = "execute"
        policy_decisions.append(decision)

    if conn: conn.close()

    return {
        "ts": now,
        "matched_actions": [a["name"] for a in actions],
        "policy": {
            "min_score": MIN_SCORE,
            "cooldown_sec": COOLDOWN,
            "lookback_sec": LOOKBACK,
            "decisions": policy_decisions
        },
        "results": results
    }
