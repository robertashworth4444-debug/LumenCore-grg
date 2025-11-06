#!/usr/bin/env python3
import asyncio, json
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Luma HUD")
clients = set()

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()  # we don't expect inbound data
    except Exception:
        pass
    finally:
        clients.discard(ws)

@app.post("/push")
async def push(payload: dict):
    msg = json.dumps(payload)
    to_drop=set()
    for c in list(clients):
        try:
            await c.send_text(msg)
        except Exception:
            to_drop.add(c)
    clients.difference_update(to_drop)
    return JSONResponse({"pushed": len(clients)})

if __name__ == "__main__":
    uvicorn.run("luma_hud:app", host="0.0.0.0", port=9010)
