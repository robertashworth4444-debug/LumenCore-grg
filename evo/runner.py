import os, json, time, argparse, random, numpy as np
from flow.fields import make_scalar_field
from flow.optimize import astar_3d
from sim.inverter_mc import monte_evo

ap=argparse.ArgumentParser()
ap.add_argument("--safe", default="1")
ap.add_argument("--tph", default="30")
ap.add_argument("--out", default="/opt/lumen-core/storage")
args=ap.parse_args()
os.makedirs(args.out, exist_ok=True)

def read_knobs(path="/opt/lumen-core/knobs/live.json"):
    try:
        with open(path) as f: return json.load(f)
    except: return {"ENTRY_TH":0.0042,"EXIT_TH":0.018,"TAKE_PROFIT_PCT":0.014,"STOP_LOSS_PCT":0.01}

def score_trial():
    k=read_knobs()
    # Build a synthetic field: hotspots scale with TAKE_PROFIT_PCT; walls from EXIT_TH
    shape=(40,40,20)
    hot = [((20,20,10),  3.0*k["TAKE_PROFIT_PCT"]/0.014, 6.0)]
    cold= [((10,30,5),   1.0, 5.0)]
    walls=np.zeros(shape); 
    if k["EXIT_TH"]>0.017: walls[5:8, :, :] = 1  # example constraint plane
    field = make_scalar_field(shape, hot_spots=hot, cold_spots=cold, wall_mask=walls)

    # Path from inlet to outlet with gradient & smoothness penalties
    res = astar_3d(field, start=(0,0,0), goal=(39,39,19), lam_grad=0.25, lam_smooth=0.1)
    path_cost = 1e3 if not res["ok"] else res["cost"]
    path_len  = 0 if not res["ok"] else len(res["path"])

    # Inverter Monte-Carlo + Evolution
    inv = monte_evo(n_samples=48, elite=8, gens=4, seed=random.randint(1,1_000_000))
    inv_score = inv["score"]

    # Composite objective (lower path cost, higher inv_score)
    score = float( 0.5*(-path_cost) + 1.0*(inv_score) + 0.1*path_len )
    return {
        "score": score,
        "path_ok": bool(res["ok"]),
        "path_cost": float(path_cost),
        "path_len": int(path_len),
        "inv": inv["best"]
    }

print(f"[evo] runner online SAFE={args.safe} TPH={args.tph} out={args.out}")
i=0
while True:
    i+=1
    res = score_trial()
    rec={"trial": i, "ts": int(time.time())} ; rec.update(res)
    with open(os.path.join(args.out,"trials.log"),"a") as f: f.write(json.dumps(rec)+"\n")

    # Occasionally promote knobs (simple example: nudge thresholds if path failed or inv_score low)
    try:
        knobs_path="/opt/lumen-core/knobs/live.json"
        with open(knobs_path) as f: k=json.load(f)
    except: k={"ENTRY_TH":0.0042,"EXIT_TH":0.018,"TAKE_PROFIT_PCT":0.014,"STOP_LOSS_PCT":0.01}

    if (i%20)==0:
        if not res["path_ok"]:
            k["EXIT_TH"]=max(0.010, k["EXIT_TH"]-0.0005)   # ease obstacle plane
        if res["inv"]["fsw_khz"]>110:
            k["TAKE_PROFIT_PCT"]=max(0.005, k["TAKE_PROFIT_PCT"]-0.0005) # keep thermals tame
        with open(knobs_path,"w") as f: json.dump(k,f,indent=2)
        print("[evo] promoted champion -> knobs/live.json")

    time.sleep(max(1, 3600/int(args.tph)))
