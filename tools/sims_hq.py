import os, time, json, numpy as np, pandas as pd, matplotlib.pyplot as plt
from joblib import Parallel, delayed
import numexpr as ne

os.makedirs('reports', exist_ok=True)
results=[]

def mc_chunk(n):
    a=np.random.rand(n); b=np.random.rand(n)
    return np.sum(ne.evaluate('sqrt(a*a + b*b) < 1.0'))

def flowform_v4(total=12_000_000, workers=4):
    n=total//workers
    # baseline
    tB=time.time(); s=0; ch=200_000
    for _ in range(total//ch):
        a=np.random.rand(ch); b=np.random.rand(ch)
        s+=np.sum(np.hypot(a,b)<1.0)
    tB2=time.time()
    # vectorized parallel
    tV=time.time()
    parts=Parallel(n_jobs=workers, prefer='threads')(delayed(mc_chunk)(n) for _ in range(workers))
    tV2=time.time()
    return {'name':'flowform_v4','baseline_s':tB2-tB,'vectorized_s':tV2-tV,'speedup':(tB2-tB)/(tV2-tV+1e-9)}

def thermal_diff(size=900, steps=260):
    grid=np.zeros((size,size)); grid[size//2,size//2]=1000
    kflat, kcurved = 0.18, 0.29
    def run(k):
        A=grid.copy(); t0=time.time()
        for _ in range(steps):
            A[1:-1,1:-1]=A[1:-1,1:-1]+k*(A[:-2,1:-1]+A[2:,1:-1]+A[1:-1,:-2]+A[1:-1,2:]-4*A[1:-1,1:-1])
        return A, time.time()-t0
    flat,tf=run(kflat); curved,tc=run(kcurved)
    eff=(flat.max()-curved.max())/max(flat.max(),1e-9)
    plt.figure(figsize=(5,4)); plt.imshow(flat, cmap='inferno'); plt.axis('off'); plt.title('Flat Frame Peak'); plt.tight_layout(); plt.savefig('reports/thermal_flat.png', dpi=160); plt.close()
    plt.figure(figsize=(5,4)); plt.imshow(curved, cmap='inferno'); plt.axis('off'); plt.title('Curved Frame Peak'); plt.tight_layout(); plt.savefig('reports/thermal_curved.png', dpi=160); plt.close()
    return {'name':'thermal_diff','flat_time_s':tf,'curved_time_s':tc,'efficiency_gain_pct':round(eff*100,2),'speedup':tf/(tc+1e-9)}

def whitehole_latency(N=4_000_000):
    t0=time.time()
    x=np.sin(np.linspace(0,100*np.pi,N))
    noisy=np.convolve(x, np.ones(160)/160, mode='same')
    t1=time.time()
    t2=time.time()
    y=np.sin(np.linspace(0,100*np.pi,N))
    f=np.fft.rfft(y); f[9000:]=0; clean=np.fft.irfft(f, n=y.size)
    t3=time.time()
    return {'name':'whitehole_latency','baseline_s':t1-t0,'harmonic_s':t3-t2,'speedup':(t1-t0)/(t3-t2+1e-9)}

r1=flowform_v4(); r2=thermal_diff(); r3=whitehole_latency()
import pandas as pd
df=pd.DataFrame([r1,r2,r3]); df.to_csv('reports/sim_results_hq.csv',index=False)

plt.figure(figsize=(7,4)); plt.bar(df['name'], df['speedup'])
plt.ylabel('Speedup (×)'); plt.title('Lumen/NovaCore Speedups (HQ)'); plt.tight_layout()
plt.savefig('reports/sim_speedups_hq.png', dpi=170)

summary={'total_tests':int(df.shape[0]),
         'avg_speedup':float(df['speedup'].mean()),
         'max_speedup':float(df['speedup'].max()),
         'thermal_gain_pct': float([x['efficiency_gain_pct'] for x in [r1,r2,r3] if x['name']=="thermal_diff"][0])}
open('reports/sim_summary_hq.json','w').write(__import__("json").dumps(summary,indent=2))
print("DONE")
