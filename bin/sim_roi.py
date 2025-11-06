import sys, json, numpy as np, pandas as pd, time
from pathlib import Path
outdir = Path(sys.argv[1]) if len(sys.argv)>1 else Path("/opt/lumen-core/reports")
outdir.mkdir(parents=True, exist_ok=True)
sites = int(sys.argv[2]) if len(sys.argv)>2 else 20
rng = np.random.default_rng(7)
# Baseline from your prior snapshot
down_savings_site = 180000.0
maint_savings_site = 3120.0
capex_site = 120000.0
opex_site = 18000.0
events_per_site = 4
baseline_trip = 0.08
novacore_trip = 0.02
rows=[]
for s in range(sites):
    # add  +/- 10% noise to reflect site variability
    ds = down_savings_site*(1+rng.normal(0,0.08))
    ms = maint_savings_site*(1+rng.normal(0,0.1))
    total = ds+ms
    rows.append({"site":s+1,"downtime_sav":ds,"maint_sav":ms,"total_sav":total})
df = pd.DataFrame(rows)
tot_sav = df["total_sav"].sum()
year1_cost = sites*(capex_site) + sites*(opex_site)
roi = (tot_sav-year1_cost)/year1_cost if year1_cost>0 else 0
out = {"sites":sites,"events_site":events_per_site,"baseline_trip":baseline_trip,
       "novacore_trip":novacore_trip,"total_savings_all":tot_sav,
       "year1_cost_all":year1_cost,"year1_roi":roi}
csv = outdir/f"roi_run_{int(time.time())}.csv"; df.to_csv(csv,index=False)
print(json.dumps(out))
