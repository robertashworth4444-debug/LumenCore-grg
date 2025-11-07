# wrapper: runs prestige and copies artifacts to /opt/lumen-core/reports/prestige/latest
import os, shutil, glob, subprocess, sys, time
from datetime import datetime, timezone

def run():
    t0=time.time()
    # Save user script as prestige_paper.py for clarity
    with open("tools/prestige/prestige_paper.py","w") as f:
        f.write("""""")
    # ^ We will replace the marker below with your code in the next command.

    # Run the prestige analysis
    subprocess.check_call([sys.executable, "tools/prestige/prestige_paper.py"])

    # Find the newest prestige_run_* folder
    runs = sorted(glob.glob("prestige_run_*"), key=os.path.getmtime)
    if not runs:
        print("No prestige_run_* found"); return
    newest = runs[-1]

    # Stage to /opt/lumen-core/reports/prestige/latest
    dest = "/opt/lumen-core/reports/prestige/latest"
    os.makedirs(dest, exist_ok=True)
    # clear old
    for p in glob.glob(dest+"/*"): 
        try: os.remove(p)
        except: pass
    for fn in glob.glob(newest+"/*"):
        shutil.copy(fn, dest)
    print("Staged:", dest, "Elapsed:", round(time.time()-t0,1), "s")

if __name__=="__main__":
    run()
