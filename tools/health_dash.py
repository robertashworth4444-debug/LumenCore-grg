from flask import Flask, jsonify
import psutil, time, platform, requests, re

app = Flask(__name__)

@app.route('/api/health')
def health():
    return jsonify({
        "system": platform.node(),
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "mem_used_mb": round(psutil.virtual_memory().used/1e6,1),
        "mem_total_mb": round(psutil.virtual_memory().total/1e6,1),
        "uptime_sec": round(time.time()-psutil.boot_time(),1),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    })

@app.route('/api/nginx')
def nginx():
    # read nginx stub_status locally
    try:
        r = requests.get("http://127.0.0.1/nginx_status", timeout=1)
        t = r.text
        active = int(re.search(r'Active connections:\s+(\d+)', t).group(1))
        accepts, handled, requests = map(int, re.findall(r'\n\s*(\d+)\s+(\d+)\s+(\d+)\n', t)[0])
        reading = int(re.search(r'Reading:\s+(\d+)', t).group(1))
        writing = int(re.search(r'Writing:\s+(\d+)', t).group(1))
        waiting = int(re.search(r'Waiting:\s+(\d+)', t).group(1))
        return jsonify({"active":active,"accepts":accepts,"handled":handled,"requests":requests,
                        "reading":reading,"writing":writing,"waiting":waiting,"timestamp":time.time()})
    except Exception as e:
        return jsonify({"error":str(e)}), 502

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5060)
