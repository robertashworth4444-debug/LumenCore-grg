#!/usr/bin/env python3
import asyncio, json, sqlite3
from nats.aio.client import Client as NATS

DB = "/opt/lumen-core/incidents.db"
SCHEMA = """CREATE TABLE IF NOT EXISTS incidents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER,
  service TEXT,
  severity TEXT,
  event_json TEXT,
  outcome_json TEXT
);"""

async def main():
    nc = NATS()
    await nc.connect(servers=["nats://whitehole:lumenpower@127.0.0.1:4222"])
    conn = sqlite3.connect(DB, isolation_level=None, check_same_thread=False)
    conn.execute(SCHEMA)

    async def handler(msg):
        inc = json.loads(msg.data.decode())
        e, o = inc.get("event", {}), inc.get("outcome", {})
        conn.execute(
            "INSERT INTO incidents(ts,service,severity,event_json,outcome_json) VALUES (?,?,?,?,?)",
            (o.get("ts",0), e.get("service"), e.get("severity"), json.dumps(e), json.dumps(o))
        )
        print(f"[INCIDENT] {e.get('service')} {e.get('severity')} -> {o.get('matched_actions')}")

    await nc.subscribe("whitehole.incidents", cb=handler)
    print("✅ Incident consumer online; waiting for messages...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
