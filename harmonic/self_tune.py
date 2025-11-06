import random
def perf(k): x,y=k; return -(x-5)**2-(y-5)**2+100
k=[random.uniform(0,10) for _ in range(2)]
p=perf(k)
print(f"start {k}  perf={p:.1f}")
for s in range(50):
    prop=[max(0,min(10,v+random.uniform(-1,1))) for v in k]
    np=perf(prop)
    if np>p: k,p=prop,np; print(f"step{s:02d}  perf={p:.1f}  {k}")
