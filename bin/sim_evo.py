import numpy as np, pandas as pd, sys, time
from pathlib import Path
outdir = Path(sys.argv[1]) if len(sys.argv)>1 else Path("/opt/lumen-core/reports")
outdir.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)
families = ["straight","spiral","helix","brach"]
N=400
rows=[]
for i in range(N):
    fam = rng.choice(families, p=[0.25,0.35,0.25,0.15])
    # toy score: straight best when field flat; spiral/helix win in curvature
    base = dict(straight=0.2, spiral=0.5, helix=0.6, brach=0.4)[fam]
    noise = abs(rng.normal(0,0.08))
    score = max(0.0, base + noise - (0.28 if fam=="straight" and rng.random()<0.35 else 0))
    rows.append({"rank":i+1,"family":fam,"score":score})
df = pd.DataFrame(rows).sort_values("score").reset_index(drop=True)
csv = outdir/f"evo_leaderboard_{int(time.time())}.csv"
df.to_csv(csv, index=False)
print(str(csv))
