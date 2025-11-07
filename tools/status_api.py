from flask import Flask, jsonify
import subprocess, datetime

app = Flask(__name__)

def check_service(name):
    try:
        out = subprocess.check_output(
            ["systemctl", "is-active", name], text=True
        ).strip()
        return "🟢" if out == "active" else "🔴"
    except:
        return "🔴"

@app.route("/api/status")
def status():
    return jsonify({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "health": check_service("lumencore-health"),
        "api": check_service("lumencore-api"),
        "deploy": check_service("lumencore-deploy"),
        "uptime": subprocess.getoutput("uptime -p"),
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9090)
