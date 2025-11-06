#!/usr/bin/env python3
import json, os, re, yaml, subprocess, requests
from flask import Flask, request, jsonify

app = Flask("LumaSkills")
RUNBOOK_DIR = "/opt/lumen-core/runbooks"
CONF = "/opt/lumen-core/commands.yml"
NATS = "http://127.0.0.1:9001/event"

def load_cmds():
    with open(CONF,"r") as f: return yaml.safe_load(f)

def fire_runbook(script, *args):
    path=os.path.join(RUNBOOK_DIR,script)
    if not os.path.exists(path): return f"runbook {script} missing"
    try:
        out=subprocess.check_output(["bash",path,*args],stderr=subprocess.STDOUT)
        return out.decode().strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode()

@app.post("/skill")
def skill():
    data=request.get_json(force=True)
    msg=data.get("message","")
    for m in load_cmds():
        r=re.search(m["pattern"], msg, re.I)
        if not r: continue
        v=r.groupdict()
        skill=m["name"]
        if skill=="scale_service":
            res=fire_runbook("scale_service.sh",v["service"],v["replicas"])
        elif skill=="restart_service":
            res=fire_runbook("restart_service.sh",v["service"])
        elif skill=="cache_purge":
            res=fire_runbook("cache_purge.sh",v["route"])
        else:
            res="no handler"
        payload={"type":"skill.out","service":"luma","message":res}
        requests.post(NATS,json=payload,timeout=2)
        return jsonify({"skill":skill,"result":res})
    return jsonify({"error":"no match"})
