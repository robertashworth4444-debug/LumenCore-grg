#!/usr/bin/env python3
import os, time, queue, threading, tempfile, json, requests, wave, re
import sounddevice as sd, webrtcvad, numpy as np, yaml, simpleaudio
from openwakeword import Model
import openai

# ====== CONFIG ======
openai.api_key = os.getenv("OPENAI_API_KEY","")
FS = 16000
BLOCK = 16000//10
NATS_ENDPOINT = "http://127.0.0.1:9001/event"
HUD_PUSH = "http://127.0.0.1:9010/push"
VOICE_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"
VOICE_TTS_KEY = os.getenv("ELEVEN_KEY","")
COMMAND_FILE = "/opt/lumen-core/commands.yml"

# ====== UTIL ======
q_in = queue.Queue()
def hud(t, kind="luma"):
    try: requests.post(HUD_PUSH,json={"type":kind,"text":t},timeout=1)
    except: pass
def tts(text):
    if not VOICE_TTS_KEY: print("LUMA:",text); return
    try:
        r=requests.post(VOICE_TTS_URL,headers={"xi-api-key":VOICE_TTS_KEY},
                        json={"text":text,"voice_settings":{"stability":0.6,"similarity_boost":0.7}},timeout=15)
        if not r.ok: print("LUMA:",text); return
        tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".wav"); tmp.write(r.content); tmp.close()
        simpleaudio.WaveObject.from_wave_file(tmp.name).play()
    except Exception: print("LUMA:",text)

def audio_cb(indata, frames, time_info, status): q_in.put(bytes(indata))
def write_wav(samples: bytes, path: str):
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(FS); wf.writeframes(samples)

def record_phrase(max_sec=6):
    vad=webrtcvad.Vad(2); tail=0; buf=b''; start=time.time()
    while True:
        try: chunk=q_in.get(timeout=2)
        except: break
        if time.time()-start>max_sec: break
        buf+=chunk
        tail = 0 if vad.is_speech(chunk,FS) else tail+1
        if tail>=8 and len(buf)>FS//2: break
    path=tempfile.NamedTemporaryFile(delete=False,suffix=".wav").name
    write_wav(buf,path); return path

def transcribe(path):
    try:
        with open(path,"rb") as f:
            r=openai.Audio.transcriptions.create(model="whisper-1", file=f)
        return (r.text or "").strip()
    except Exception: return ""

# ====== COMMAND ROUTING ======
def load_mappings():
    try:
        with open(COMMAND_FILE,"r") as f: return yaml.safe_load(f) or []
    except Exception: return []

def tmpl(s, **kw): 
    out=s
    for k,v in kw.items(): out=out.replace("{{"+k+"}}", str(v))
    return out

def try_route(cmd: str) -> bool:
    maps=load_mappings()
    for m in maps:
        pat=re.compile(m["pattern"], re.IGNORECASE)
        z=pat.search(cmd)
        if z:
            vars=z.groupdict()
            payload={}
            for k,v in m["payload"].items():
                payload[k]=tmpl(v, **vars) if isinstance(v,str) else v
            event={
                "type": payload.get("type","command"),
                "source":"luma",
                "service": payload.get("service","luma"),
                "severity":"info",
                "labels":{},
                "metrics":{},
                "context":{},
            }
            # merge rest of payload fields
            for k,v in payload.items():
                if k not in ("type","service"): event[k]=v
            try:
                requests.post(NATS_ENDPOINT,json=event,timeout=3)
                hud(f"↪ {m['name']} → {payload}", "luma")
                tts("Done.")
            except Exception:
                hud("Failed to send command.","luma")
                tts("I could not reach the command gateway.")
            return True
    return False

# ====== MAIN LOOP with wakeword ======
def main():
    sd.RawInputStream(samplerate=FS, blocksize=BLOCK, dtype='int16', channels=1, callback=audio_cb).__enter__()
    oww=Model(wakeword_models=None)
    threshold=0.8; last=0
    tts("Luma is listening for Hey Luma.")
    while True:
        buf=b''.join(q_in.get() for _ in range(10))
        scores=oww.predict(np.frombuffer(buf,dtype=np.int16), FS)
        _,score=max(scores.items(), key=lambda kv: kv[1])
        if score>=threshold and (time.time()-last)>1.5:
            last=time.time(); hud("🔵 Listening…","luma"); tts("Yes?")
            wav=record_phrase(7); text=transcribe(wav)
            if text:
                hud("“"+text+"”","asr")
                if not try_route(text):
                    # fallback → send raw command
                    try:
                        requests.post(NATS_ENDPOINT,json={"type":"command","source":"luma","service":"luma","message":text},timeout=3)
                        tts("Sent.")
                    except Exception: tts("Gateway not reachable.")
            else:
                hud("…(no speech detected)","luma")

if __name__=="__main__": main()
