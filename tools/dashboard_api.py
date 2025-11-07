from flask import Flask, jsonify, request
import datetime, re

app = Flask(__name__)

@app.route("/api/metrics", methods=["GET"])
def metrics():
    return jsonify({
        "status": "online",
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

def persona_prelude(mode):
    mode=(mode or "").lower()
    if "invest" in mode:
        return ("Speak to investors. Be concise, ROI-oriented, highlight 10× advantages, "
                "market, moat, team, traction, and clear asks.")
    if "engineer" in mode:
        return ("Speak to engineers. Be detailed, specific, cover architecture trade-offs, "
                "interfaces, performance and failure modes.")
    if "vision" in mode or "visionary" in mode:
        return ("Speak visionary. Connect technology to systems-level impact, societal scale, "
                "and the LumenCore roadmap.")
    return ("Speak balanced and clear, suitable for a broad audience.")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    mode= data.get("mode","")
    if not msg:
        return jsonify({"reply":"Ask me anything about LumenCore, metrics, architecture, or roadmap.","source":"local"})
    pre = persona_prelude(mode)

    # lightweight answerer: detect topics
    lower=msg.lower()
    parts=[]
    if any(k in lower for k in ["10x","advantage","why","better"]):
        parts.append("**10× Advantage:** adaptive FlowForm harmonics, EtherFrame curved conduction, and self-healing nodes reduce thermal + latency while increasing throughput.")
    if any(k in lower for k in ["arch","architecture","how it works","layers"]):
        parts.append("**Architecture:** FlowForm (biomimetic data/energy), EtherFrame (curved modular hardware), LumenShell (energy-harmonic physical layer), AetherReach (human-AI), WhiteHole (synchronization/repair).")
    if any(k in lower for k in ["market","monet","business","revenue","moat"]):
        parts.append("**Monetization:** open-core licensing, enterprise node subscriptions, ops SLAs, and reference designs for OEMs; moat via integrated hardware+AI harmonics + ops tooling.")
    if any(k in lower for k in ["thermal","cool","efficiency"]):
        parts.append("**Thermal:** curved frames + harmonic routing → significant cooling efficiency gains vs flat boards; lower throttling, more consistent clocks.")
    if any(k in lower for k in ["latency","speed","perf","throughput"]):
        parts.append("**Performance:** reduced cross-node hop count, harmonic routing, auto-evolving schedulers; target multi-× speedups under load.")
    if not parts:
        parts.append("LumenCore fuses AI, geometry, and energy harmonics into modular, self-healing nodes—from edge devices to smart-city scale.")

    reply = f"{pre}\n\n" + "\n".join("• "+p for p in parts)
    return jsonify({"reply": reply, "source": "local"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050)
