from __future__ import annotations
import heapq, numpy as np
from .fields import grad

# 6-neighborhood steps (axis-aligned) + diagonals optional
STEPS = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]

def heuristic(a,b):  # Manhattan works fine on grids
    return sum(abs(int(ai)-int(bi)) for ai,bi in zip(a,b))

def astar_3d(cost: np.ndarray, start, goal, lam_grad=0.2, lam_smooth=0.1):
    """A* through 3D field with composite cost:
       base = cost[x] + lam_grad*|∇cost| + lam_smooth*direction_change_penalty
    """
    gx,gy,gz = np.gradient(cost)
    gradmag = np.sqrt(gx*gx+gy*gy+gz*gz)
    sx,sy,sz = cost.shape
    start,goal = tuple(start),tuple(goal)

    openq = []
    heapq.heappush(openq,(0,start,None))
    came, gscore = {}, {start: 0.0}
    prev_dir = {start:(0,0,0)}

    while openq:
        _, cur, _ = heapq.heappop(openq)
        if cur==goal: break
        for dx,dy,dz in STEPS:
            nx,ny,nz = cur[0]+dx,cur[1]+dy,cur[2]+dz
            if not (0<=nx<sx and 0<=ny<sy and 0<=nz<sz): continue
            if not np.isfinite(cost[nx,ny,nz]): continue
            base = cost[nx,ny,nz] + lam_grad*gradmag[nx,ny,nz]
            # smoothness: penalize turning vs previous step
            pd = prev_dir.get(cur,(0,0,0))
            turn = (abs(pd[0]-dx)+abs(pd[1]-dy)+abs(pd[2]-dz))>0
            cand = gscore[cur] + base + (lam_smooth if turn else 0.0)
            n = (nx,ny,nz)
            if cand < gscore.get(n, 1e18):
                gscore[n]=cand
                came[n]=cur
                prev_dir[n]=(dx,dy,dz)
                fscore = cand + heuristic(n,goal)
                heapq.heappush(openq,(fscore,n,cur))

    # reconstruct
    path=[goal]
    while path[-1]!=start and path[-1] in came:
        path.append(came[path[-1]])
    path.reverse()
    valid = path and path[0]==start
    total_cost = gscore.get(goal, np.inf)
    return {"ok": valid, "path": path, "cost": float(total_cost)}
