import subprocess, os
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET = os.environ.get("DEPLOY_TOKEN","")

@app.after_request
def cors(r):
    r.headers['Access-Control-Allow-Origin']  = '*'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Deploy-Token'
    r.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return r

@app.route("/api/deploy", methods=["POST", "OPTIONS"])
def deploy():
    if request.method == "OPTIONS":
        return ('', 204)
    tok = request.headers.get("X-Deploy-Token","")
    if not SECRET or tok != SECRET:
        return jsonify({"error":"unauthorized"}), 401
    try:
        out = subprocess.check_output(
            ["/bin/bash","-lc",
             "cd /opt/lumen-core && "
             "git fetch origin main && git reset --hard origin/main && "
             "sudo systemctl restart lumencore-api && "
             "sudo systemctl restart lumencore-api-staging && "
             "sudo nginx -t && sudo systemctl reload nginx && "
             "echo 'REV='$(git rev-parse --short HEAD)"],
            stderr=subprocess.STDOUT, text=True)
    # run harvester after deploy
    try:
        subprocess.check_call(["/opt/lumen-core/.venv/bin/python3","/opt/lumen-core/tools/sim_harvester.py"])
    except Exception as _e:
        pass

        return jsonify({"ok":True, "log":out})
    except subprocess.CalledProcessError as e:
        return jsonify({"ok":False,"log":e.output}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5052)
