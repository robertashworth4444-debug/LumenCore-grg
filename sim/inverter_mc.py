from __future__ import annotations
import numpy as np, random

# A toy inverter model score: higher is better
def score_inverter(cfg, demand_profile):
    # penalties: ripple, thermal, inefficiency; rewards: tracking, stability
    fsw   = cfg["fsw_khz"]*1e3
    dead  = cfg["dead_ns"]*1e-9
    duty  = cfg["duty_scale"]
    L, C  = cfg["L_mH"]*1e-3, cfg["C_uF"]*1e-6
    track = -np.mean((demand_profile*duty - demand_profile)**2)
    ripple = (1/(L*C+1e-9)) * 1e-6
    therm  = 1e-6*fsw + 5e-3*dead
    eff    = 0.98 - 1e-3*(fsw/100e3) - 2e-3*max(0, duty-1.0)
    return float(5*track - 10*ripple - 2*therm + 50*eff)

def random_cfg(rng=random):
    return {
      "fsw_khz": rng.uniform(30, 120),   # switching frequency
      "dead_ns": rng.uniform(50, 300),   # dead time
      "duty_scale": rng.uniform(0.9,1.1),
      "L_mH": rng.uniform(0.1, 1.0),
      "C_uF": rng.uniform(50, 500)
    }

def monte_evo(n_samples=64, elite=8, gens=5, seed=44):
    rng = random.Random(seed)
    demand = np.sin(np.linspace(0, 2*np.pi, 512)) * rng.uniform(0.6, 1.2)
    pop=[random_cfg(rng) for _ in range(n_samples)]
    scores=[score_inverter(p, demand) for p in pop]
    for _ in range(gens):
        idx=np.argsort(scores)[::-1][:elite]
        elites=[pop[i].copy() for i in idx]
        children=[]
        for e in elites:
            for _ in range((n_samples//elite)-1):
                c=e.copy()
                for k in c:
                    if rng.random()<0.5:
                        c[k]*=rng.uniform(0.95,1.05)
                children.append(c)
        pop = elites + children
        pop = pop[:n_samples]
        scores=[score_inverter(p, demand) for p in pop]
    best_i=int(np.argmax(scores))
    return {"best": pop[best_i], "score": float(scores[best_i])}
