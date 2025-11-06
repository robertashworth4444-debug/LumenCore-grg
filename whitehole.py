#!/usr/bin/env python3
import asyncio, json, logging, os
from typing import Dict, Any
from fastapi import FastAPI, Request
from pydantic import BaseModel
from nats.aio.client import Client as NATS
import uvicorn
import strategies

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="WhiteHole Gateway", version="0.5-beast")

NATS_HOST = os.getenv("NATS_HOST","127.0.0.1")
NATS_URL = f"nats://whitehole:lumenpower@{NATS_HOST}:4222"
EVENT_SUBJECT = os.getenv("EVENT_SUBJECT","whitehole.events")
ACTION_SUBJECT = os.getenv("ACTION_SUBJECT","whitehole.actions")
INCIDENT_SUBJECT = os.getenv("INCIDENT_SUBJECT","whitehole.incidents")

class Event(BaseModel):
    type: str
    source: str | None = None
    service: str | None = None
    severity: str | None = "info"
    fingerprint: str | None = None
    labels: dict | None = {}
    metrics: dict | None = {}
    context: dict | None = {}

@app.on_event("startup")
async def startup_event():
    app.state.nc = NATS()
    await app.state.nc.connect(servers=[NATS_URL])
    logging.info(f"Connected to NATS at {NATS_URL}")

@app.get("/health")
async def health():
    return {"status":"whitehole_alive","nats":NATS_URL}

@app.post("/event")
async def receive_event(request: Request):
    payload = await request.json()
    try:
        ev = Event(**payload).model_dump()
    except Exception as e:
        return {"status":"error","error":str(e)}

    # 1) publish raw event
    await app.state.nc.publish(EVENT_SUBJECT, json.dumps(ev).encode())

    # 2) reason + act (inline for low-latency)
    outcome = strategies.decide_and_act(ev)

    # 3) publish incident record
    inc = {"event": ev, "outcome": outcome}
    await app.state.nc.publish(INCIDENT_SUBJECT, json.dumps(inc).encode())

    logging.info(f"Event processed sev={ev.get('severity')} type={ev.get('type')} results={outcome.get('matched_actions')}")
    return {"status":"ok","published":[EVENT_SUBJECT, INCIDENT_SUBJECT],"outcome":outcome}

if __name__ == "__main__":
    uvicorn.run("whitehole:app", host="0.0.0.0", port=9001)
