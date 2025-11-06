import io,sys,os,re
p="/opt/lumen-core/aethervision/app.py"
with open(p,"r",encoding="utf-8") as f:
    s=f.read()
if "id=\"speech\"" in s:
    print("HUD already present"); sys.exit(0)
injection = r'''
<div id="speech" style="position:fixed;bottom:18px;left:18px;background:rgba(0,0,0,.45);padding:10px 14px;border-radius:12px;font:14px/1.4 system-ui,Inter;max-width:60%;display:none"></div>
<script>
 const hud=document.getElementById("speech");
 const sock=new WebSocket("ws://"+location.hostname+":9010/ws");
 sock.onmessage=(e)=>{ try{ const j=JSON.parse(e.data);
   if(j.type==="asr"||j.type==="luma"){ hud.style.display="block"; hud.innerText=j.text }
 }catch(_){ } };
</script>
</body>'''
s=re.sub(r'</body>', injection, s, count=1, flags=re.IGNORECASE)
with open(p,"w",encoding="utf-8") as f:
    f.write(s)
print("HUD injected into AetherVision")
