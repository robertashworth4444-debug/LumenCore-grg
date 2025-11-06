#!/usr/bin/env python3
import asyncio, json, os, sqlite3, time, socket
from nats.aio.client import Client as NATS

SELF = socket.gethostname()
DB = "/opt/lumen-core/incidents.db"
NATS_URL = "nats://whitehole:lumenpower@127.0.0.1:4222"
STATS = {}

def local_success_rate():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
      WITH r AS (
        SELECT json_each.value AS res FROM incidents, json_each(json_extract(outcome_json,'$.results'))
      )
      SELECT SUM(CASE json_extract(res,'$.ok') WHEN 1 THEN 1 ELSE 0 END) AS ok,
             COUNT(*) AS total FROM r
    """)
    ok,total = cur.fetchone() or (0,0)
    conn.close()
    if total == 0: return 0.5
    return round(ok/total,3)

async def consensus():
    nc = NATS()
    await nc.connect(servers=[NATS_URL])
    async def cb(msg):
        data=json.loads(msg.data.decode())
        STATS[data["node"]]=data["success_rate"]
    await nc.subscribe("whitehole.node.*.consensus", cb=cb)

    while True:
        # broadcast our current success rate
        rate = local_success_rate()
        await nc.publish(f"whitehole.node.{SELF}.consensus",
                         json.dumps({"node":SELF,"success_rate":rate,"ts":int(time.time())}).encode())
        # compute cluster average
        all_rates=[rate]+[v for k,v in STATS.items()]
        avg=round(sum(all_rates)/len(all_rates),3)
        await nc.publish("whitehole.mesh.consensus",
                         json.dumps({"cluster_rate":avg,"nodes":len(all_rates),"ts":int(time.time())}).encode())
        await asyncio.sleep(120)

asyncio.run(consensus())
