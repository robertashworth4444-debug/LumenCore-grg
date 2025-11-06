import math
phi = (1+5**0.5)/2
def score(x,y):
    r = x/y if y else 0
    return math.exp(-((r-phi)**2)*2)
best=(-1,None)
for x in range(1,50,2):
    for y in range(1,50,2):
        s=score(x,y)
        if s>best[0]: best=(s,(x,y))
print(f"Optimal X,Y={best[1]}  harmony={best[0]:.3f}")
