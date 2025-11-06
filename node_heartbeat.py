#!/usr/bin/env python3
import asyncio, socket, time, json
from nats.aio.client import Client as NATS

async def main():
    nc = NATS(); await nc.connect(servers=["nats://whitehole:lumenpower@127.0.0.1:4222"])
    host = socket.gethostname()
    while True:
        msg = {
            "ts": int(time.time()),
            "node": host,
            "cpu":  round(float(open("/proc/loadavg").read().split()[0]),2),
            "mem":  float(open("/proc/meminfo").read().split()[1])/1e6,
            "uptime": int(float(open("/proc/uptime").read().split()[0]))
        }
        await nc.publish(f"whitehole.node.{host}.heartbeat", json.dumps(msg).encode())
        await asyncio.sleep(10)

asyncio.run(main())
