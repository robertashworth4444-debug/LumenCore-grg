#!/usr/bin/env python3
import asyncio, json, requests, simpleaudio, tempfile, os
from nats.aio.client import Client as NATS

NATS_URL = "nats://whitehole:lumenpower@127.0.0.1:4222"
VOICE_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"
VOICE_TTS_KEY = os.getenv("ELEVEN_KEY","")

async def speak(txt):
    if not VOICE_TTS_KEY:
        print("LUMA:", txt); return
    try:
        r=requests.post(VOICE_TTS_URL,
                        headers={"xi-api-key":VOICE_TTS_KEY},
                        json={"text":txt,"voice_settings":{"stability":0.6,"similarity_boost":0.7}},
                        timeout=10)
        if r.ok:
            tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".wav")
            tmp.write(r.content); tmp.close()
            simpleaudio.WaveObject.from_wave_file(tmp.name).play()
        else:
            print("LUMA:", txt)
    except Exception as e:
        print("LUMA:", txt, "error:", e)

async def main():
    nc=NATS()
    await nc.connect(servers=[NATS_URL])
    async def cb(msg):
        data=json.loads(msg.data.decode())
        out=data.get("message","")
        await speak(out)
    await nc.subscribe("whitehole.skill.out", cb=cb)
    await asyncio.Event().wait()

asyncio.run(main())
