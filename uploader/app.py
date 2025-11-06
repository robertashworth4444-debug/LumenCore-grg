from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os, shutil, pathlib, datetime
SAVE_DIR="/var/www/lumen-core/docs"
app=FastAPI()
app.mount("/docs", StaticFiles(directory=SAVE_DIR), name="docs")
HTML="""<!doctype html><meta charset=utf-8>
<title>LumenCore — Upload</title>
<style>body{background:#0d1117;color:#e6edf3;font-family:system-ui;margin:0}
.wrap{max-width:900px;margin:0 auto;padding:32px}
h1{color:#00e0ff}.panel{background:#121a33;border:1px solid #1f2a44;border-radius:14px;padding:18px}
input[type=file]{padding:12px;background:#0f1731;color:#e6edf3;border:1px solid #223;border-radius:10px;width:100%}
.btn{margin-top:12px;padding:10px 14px;background:#ffd166;color:#111;font-weight:700;border-radius:10px;border:0}
small{color:#94a3b8}</style>
<div class=wrap>
<h1>📤 LumenCore Upload</h1>
<div class=panel>
<form method=post enctype=multipart/form-data>
<input type=file name=files multiple>
<button class=btn type=submit>Upload</button>
</form>
<p><small>Files save to <code>/docs</code> and appear at <a href="/docs/" target=_blank>/docs/</a>.</small></p>
</div>
</div>"""
@app.get("/", response_class=HTMLResponse)
def form(): return HTML
@app.post("/", response_class=HTMLResponse)
async def upload(files:list[UploadFile]=File(...)):
    os.makedirs(SAVE_DIR, exist_ok=True)
    for f in files:
        dest=os.path.join(SAVE_DIR, pathlib.Path(f.filename).name)
        with open(dest,"wb") as out: shutil.copyfileobj(f.file,out)
    return RedirectResponse(url="/", status_code=303)
