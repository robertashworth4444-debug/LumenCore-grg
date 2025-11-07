from flask import Flask, request, jsonify
import os, subprocess, time, datetime, pathlib, shutil, json

app = Flask(__name__)
RUN_TOKEN = os.environ.get("RUN_TOKEN","")

ROOT = "/opt/lumen-core"
VENV = os.path.join(ROOT, ".venv", "bin", "python3")
INDEXER = os.path.join(ROOT, "tools", "sim_indexer.py")

def ok(auth):
    return RUN_TOKEN and auth == RUN_TOKEN

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def ensure_dir(p):
    pathlib.Path(p).mkdir(parents=True, exist_ok=True)

@app.after_request
def cors(r):
    r.headers['Access-Control-Allow-Origin']  = '*'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Run-Token'
    r.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return r

@app.route("/api-run/reindex", methods=["POST","OPTIONS"])
def reindex():
    if request.method=="OPTIONS": return ('',204)
    if not ok(request.headers.get("X-Run-Token","")):
        return jsonify({"error":"unauthorized"}), 401
    p = run_cmd(f"{VENV} {INDEXER}")
    return jsonify({"ok": p.returncode==0, "stdout": p.stdout, "stderr": p.stderr})

@app.route("/api-run/spiral", methods=["POST","OPTIONS"])
def run_spiral():
    if request.method=="OPTIONS": return ('',204)
    if not ok(request.headers.get("X-Run-Token","")):
        return jsonify({"error":"unauthorized"}), 401
    stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    outdir = f"{ROOT}/reports/spiral/spiral_run_{stamp}"
    ensure_dir(outdir)
    # If you have an existing spiral_demo.py elsewhere, call it. Otherwise generate a quick demo plot.
    spiral_script = os.path.join(ROOT,"tools","spiral","run_spiral.py")
    if not os.path.exists(spiral_script):
        ensure_dir(os.path.dirname(spiral_script))
        with open(spiral_script,"w") as f:
            f.write('''
import numpy as np, matplotlib.pyplot as plt, os, json
from datetime import datetime
stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
out = os.environ.get("OUTDIR",".")
t = np.linspace(0,10,4000)
r = 0.5 + 0.5*np.sin(3*t)*np.exp(-t/6)
x = r*np.cos(4*t); y = r*np.sin(4*t)
plt.figure(figsize=(6,6)); plt.plot(x,y,'c'); plt.axis('off')
plt.title("Spiral Demo", color="#00ffd0"); plt.tight_layout()
plt.savefig(os.path.join(out,"spiral_demo.png"), dpi=220)
summ={"timestamp":stamp,"note":"spiral demo","files":["spiral_demo.png"]}
open(os.path.join(out,"spiral_demo_report.json"),"w").write(json.dumps(summ,indent=2))
''')
    p = run_cmd(f"OUTDIR='{outdir}' {VENV} {spiral_script}")
    # refresh index
    run_cmd(f"{VENV} {INDEXER}")
    # latest symlink
    ensure_dir(f"{ROOT}/reports/spiral")
    try:
        latest = os.path.join(ROOT,"reports","spiral","latest")
        if os.path.islink(latest) or os.path.exists(latest):
            os.unlink(latest)
        os.symlink(outdir, latest)
    except Exception: pass
    return jsonify({"ok": p.returncode==0, "stdout": p.stdout, "stderr": p.stderr, "outdir": outdir})

@app.route("/api-run/nova", methods=["POST","OPTIONS"])
def run_nova():
    if request.method=="OPTIONS": return ('',204)
    if not ok(request.headers.get("X-Run-Token","")):
        return jsonify({"error":"unauthorized"}), 401
    nova = os.path.join(ROOT,"tools","nova","run_nova.py")
    if not os.path.exists(nova):
        return jsonify({"error":"nova runner missing","path":nova}), 404
    p = run_cmd(f"{VENV} {nova}")
    # copy newest nova_run_* to /reports/nova/<dir> and set latest
    newest = run_cmd("cd /opt/lumen-core && ls -1td nova_run_* 2>/dev/null | head -n1").stdout.strip()
    if newest:
        target = f"{ROOT}/reports/nova/{newest}"
        ensure_dir(os.path.dirname(target))
        run_cmd(f"cp -r '/opt/lumen-core/{newest}' '{target}'")
        link = f"{ROOT}/reports/nova/latest"
        try:
            if os.path.islink(link) or os.path.exists(link): os.unlink(link)
            os.symlink(target, link)
        except Exception: pass
    run_cmd(f"{VENV} {INDEXER}")
    return jsonify({"ok": p.returncode==0, "stdout": p.stdout, "stderr": p.stderr, "newest": newest})

@app.route("/api-run/prestige", methods=["POST","OPTIONS"])
@app.route("/api-run/harvest", methods=["POST","OPTIONS"])
def run_harvest():
    if request.method=="OPTIONS": return ("",204)
    if not ok(request.headers.get("X-Run-Token","")):
        return jsonify({"error":"unauthorized"}),401
    p = run_cmd(f"{VENV} /opt/lumen-core/tools/sim_harvester.py")
    return jsonify({"ok":p.returncode==0,"stdout":p.stdout,"stderr":p.stderr})

def run_prestige():
    if request.method=="OPTIONS": return ('',204)
    if not ok(request.headers.get("X-Run-Token","")):
        return jsonify({"error":"unauthorized"}), 401
    # If your PRESTIGE wrapper exists (tools/prestige/run_prestige.py), run it
    pr = os.path.join(ROOT,"tools","prestige","run_prestige.py")
    if not os.path.exists(pr):
        return jsonify({"error":"prestige wrapper missing","path":pr}), 404
    p = run_cmd(f"{VENV} {pr}")
    run_cmd(f"{VENV} {INDEXER}")
    return jsonify({"ok": p.returncode==0, "stdout": p.stdout, "stderr": p.stderr})


from flask import Response, stream_with_context
import json

def stream_sse(cmd):
    def generate():
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1, universal_newlines=True, cwd=ROOT)
        try:
            for line in p.stdout:
                yield f"data: {line.rstrip()}\n\n"
        finally:
            rc = p.wait()
            yield f"event: done\ndata: {{\"returncode\": {rc}}}\n\n"
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route("/api-stream/<which>", methods=["GET"])
def sse_run(which):
    tok = request.args.get("token","")
    if not ok(tok):
        return jsonify({"error":"unauthorized"}), 401
    if which == "nova":
        nova = os.path.join(ROOT,"tools","nova","run_nova.py")
        if not os.path.exists(nova): return jsonify({"error":"nova runner missing","path":nova}), 404
        cmd = f"{VENV} {nova}"
        return stream_sse(cmd)
    elif which == "prestige":
        pr = os.path.join(ROOT,"tools","prestige","run_prestige.py")
        if not os.path.exists(pr): return jsonify({"error":"prestige runner missing","path":pr}), 404
        cmd = f"{VENV} {pr}"
        return stream_sse(cmd)
    elif which == "spiral":
        spiral_script = os.path.join(ROOT,"tools","spiral","run_spiral.py")
        if not os.path.exists(spiral_script):
            os.makedirs(os.path.dirname(spiral_script), exist_ok=True)
            open(spiral_script,"w").write('''
import numpy as np, matplotlib.pyplot as plt, os, json, time
from datetime import datetime
stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
out = os.environ.get("OUTDIR", os.path.join("/opt/lumen-core","reports","spiral","spiral_run_"+stamp))
os.makedirs(out, exist_ok=True)
print("Spiral run to:", out, flush=True)
t = np.linspace(0,12,5000)
r = 0.6 + 0.4*np.sin(2.7*t)*np.exp(-t/7)
x = r*np.cos(4.2*t); y = r*np.sin(4.2*t)
for k in range(5):
    time.sleep(0.5)
    print("progress", (k+1)*20, "%", flush=True)
plt.figure(figsize=(6,6)); plt.plot(x,y,'c'); plt.axis('off')
plt.title("Spiral Demo", color="#00ffd0"); plt.tight_layout()
plt.savefig(os.path.join(out,"spiral_demo.png"), dpi=220)
open(os.path.join(out,"spiral_demo_report.json"),"w").write(json.dumps({"timestamp":stamp,"outdir":out}, indent=2))
print("done", flush=True)
''')
        # OUTDIR for spiral
        stamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        outdir = os.path.join(ROOT,"reports","spiral", f"spiral_run_{stamp}")
        os.environ["OUTDIR"] = outdir
        cmd = f"{VENV} {spiral_script}"
        return stream_sse(cmd)
    else:
        return jsonify({"error":"unknown sim"}), 404

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5054)
