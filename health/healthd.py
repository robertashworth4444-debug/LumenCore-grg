#!/usr/bin/env python3
import os, time, requests, subprocess, json

PROM_URL = os.getenv("PROM_URL", "http://127.0.0.1:9090")
ALERT_WEBHOOK = os.getenv("ALERT_WEBHOOK")
CHECK_EVERY_SEC = int(os.getenv("CHECK_EVERY_SEC", "30"))

TARGETS = {
    "lumen-core.service": {"restart_cmd": "systemctl restart lumen-core"},
    "whitehole.service":  {"restart_cmd": "systemctl restart whitehole"},
}

def q(expr):
    try:
        r = requests.get(f"{PROM_URL}/api/v1/query", params={"query": expr}, timeout=5)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success": return 0.0
        res = data["data"]["result"]
        if not res: return 0.0
        return float(res[0]["value"][1])
    except Exception:
        return 0.0

def alert(msg):
    print("[HEALTHD]", msg, flush=True)
    if ALERT_WEBHOOK:
        try:
            requests.post(ALERT_WEBHOOK, json={"text": msg}, timeout=5)
        except Exception:
            pass

def sh(cmd):
    return subprocess.call(cmd, shell=True)

while True:
    try:
        cpu_temp = q('max_over_time(node_hwmon_temp_celsius[5m])')
        undervolt = q('max_over_time(lumen_rpi_undervolt[5m])')
        disk_err = q('increase(lumen_disk_errors_total[10m])')
        core_ok = q('avg_over_time(lumencore_tasks_ok[5m])')

        issues = []
        if cpu_temp and cpu_temp > 80:
            issues.append(f"High CPU temp {cpu_temp:.1f}°C")
        if undervolt and undervolt >= 1:
            issues.append("Undervolt/throttle flag set")
        if disk_err and disk_err > 0:
            issues.append(f"Disk errors in last 10m: {disk_err:.0f}")
        if core_ok < 0.5:
            issues.append("Core heartbeat degraded (<0.5)")

        if issues:
            msg = "🛠️ Auto-heal triggered: " + " | ".join(issues)
            alert(msg)
            for unit, spec in TARGETS.items():
                sh(spec["restart_cmd"])
            sh("/opt/lumen-core/health/recovery.sh || true")
        else:
            print("[HEALTHD] all green", flush=True)
    except Exception as e:
        alert(f"healthd exception: {e}")
    time.sleep(CHECK_EVERY_SEC)
