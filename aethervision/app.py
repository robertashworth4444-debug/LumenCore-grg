#!/usr/bin/env python3
import requests, time, re
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

POLICY_URL   = "http://127.0.0.1:8000/policy"
EXPORTER_URL = "http://127.0.0.1:9105/metrics"
NATS_VARZ    = "http://127.0.0.1:8222/varz"

app = FastAPI(title="AetherVision", version="0.1")

@app.get("/scene")
def scene():
    now = int(time.time())
    policy = {}
    metrics = {}
    varz = {}
    try:
        policy = requests.get(POLICY_URL, timeout=2).json()
    except: policy = {}
    try:
        txt = requests.get(EXPORTER_URL, timeout=2).text
        def getm(name, default=0.0):
            for line in txt.splitlines():
                if line.startswith(name+" " ) or line.startswith(name+"{"):
                    m = re.search(r'([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)$', line)
                    if m: return float(m.group(1))
            return default
        metrics = {
            "inc_total": getm("whitehole_incidents_total"),
            "inc_high":  getm("whitehole_incidents_high_total"),
            "nats_conn": getm("nats_connections"),
            "nats_mem":  getm("nats_mem_bytes"),
            "nats_cpu":  getm("nats_cpu_pct")
        }
    except: metrics = {}
    try:
        varz = requests.get(NATS_VARZ, timeout=2).json()
    except: varz = {}

    return {
        "ts": now,
        "policy": policy,
        "metrics": metrics,
        "varz": {k: varz.get(k) for k in ("connections","routes","mem","cpu","jetstream")}
    }

INDEX_HTML = """<!doctype html><html><head>
<meta charset="utf-8"/><title>AetherVision</title>
<style>html,body{margin:0;height:100%;background:#0a0f1a;color:#eee;font-family:Inter,system-ui}
#hud{position:fixed;top:10px;left:10px;background:rgba(0,0,0,.35);padding:8px 12px;border-radius:10px}
canvas{display:block}</style>
</head><body>
<div id="hud">AetherVision • <span id="stat">loading…</span></div>
<script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
<script>
const W=window.innerWidth,H=window.innerHeight;
const scene=new THREE.Scene(); scene.background=new THREE.Color(0x0a0f1a);
const camera=new THREE.PerspectiveCamera(65,W/H,0.1,1000); camera.position.set(0,6,18);
const renderer=new THREE.WebGLRenderer({antialias:true}); renderer.setSize(W,H); document.body.appendChild(renderer.domElement);
const light=new THREE.PointLight(0xffffff,1.2); light.position.set(10,12,10); scene.add(light);
const ambient=new THREE.AmbientLight(0x6688aa,0.4); scene.add(ambient);

const nodes={}, rings=[];
function colorFor(score, cooldown){
  if(cooldown>0) return 0x555555;
  if(score>=0.85) return 0x00ff9c;
  if(score>=0.7)  return 0x4dd2ff;
  if(score>=0.55) return 0xffd24d;
  return 0xff5c5c;
}
function pulseRing(x,y,z,color){
  const g=new THREE.RingGeometry(0.3,0.33,32);
  const m=new THREE.MeshBasicMaterial({color,transparent:true,opacity:0.9,side:THREE.DoubleSide});
  const r=new THREE.Mesh(g,m); r.position.set(x,y,z); r.rotation.x=-Math.PI/2; r.userData.v=0.02;
  rings.push(r); scene.add(r);
}
function upsertNode(key,x,z,score,cd,ok,fail){
  if(!nodes[key]){
    const geo=new THREE.SphereGeometry(0.6,32,32);
    const mat=new THREE.MeshStandardMaterial({color:0x2194ff,emissive:0x111111,metalness:0.3,roughness:0.4});
    const mesh=new THREE.Mesh(geo,mat); mesh.position.set(x,0,z); scene.add(mesh);
    nodes[key]={mesh};
  }
  const n=nodes[key]; n.mesh.material.color.setHex(colorFor(score, cd));
  n.mesh.scale.setScalar(1+Math.min(0.6, ok/(fail+1)));
}
function layout(actions){
  const R=8, step=(Math.PI*2)/Math.max(1,actions.length);
  let i=0; for(const a of actions){
    const ang=i*step, x=Math.cos(ang)*R, z=Math.sin(ang)*R;
    upsertNode(a.service+"::"+a.action, x,z, a.score_est??a.score??0.6, a.cooldown_left??0, a.ok_recent||0, a.fail_recent||0);
    i++;
  }
}
async function tick(){
  try{
    const r=await fetch('/scene'); const j=await r.json();
    const acts=j.policy?.actions||[];
    layout(acts);
    document.getElementById('stat').textContent=`incidents:${j.metrics?.inc_total||0} high:${j.metrics?.inc_high||0} nats:${j.metrics?.nats_conn||0}`;
    // pulse rings when high incidents
    if((j.metrics?.inc_high||0)>0){ pulseRing(0,0,0,0xff5c5c); }
  }catch(e){ document.getElementById('stat').textContent='offline'; }
}
setInterval(tick,3000); tick();

function animate(){ requestAnimationFrame(animate);
  for(const k in nodes){ nodes[k].mesh.rotation.y+=0.005; }
  for(let i=rings.length-1;i>=0;i--){ const r=rings[i]; r.scale.x+=0.03; r.scale.y+=0.03; r.material.opacity-=0.015; if(r.material.opacity<=0){ scene.remove(r); rings.splice(i,1); } }
  renderer.render(scene,camera);
} animate();
window.addEventListener('resize',()=>{ const w=innerWidth,h=innerHeight; camera.aspect=w/h; camera.updateProjectionMatrix(); renderer.setSize(w,h);});
</script>
<div id="speech" style="position:fixed;bottom:18px;left:18px;background:rgba(0,0,0,.45);padding:10px 14px;border-radius:12px;font:14px/1.4 system-ui,Inter;max-width:60%;display:none"></div>
<script>
 const hud=document.getElementById("speech");
 const sock=new WebSocket("ws://"+location.hostname+":9010/ws");
 sock.onmessage=(e)=>{ try{ const j=JSON.parse(e.data);
   if(j.type==="asr"||j.type==="luma"){ hud.style.display="block"; hud.innerText=j.text }
 }catch(_){ } };
</script>
</body></html>
"""
@app.get("/", response_class=HTMLResponse)
def index(): return HTMLResponse(INDEX_HTML)

app.mount("/static", StaticFiles(directory="/opt/lumen-core/aethervision/static"), name="static")
