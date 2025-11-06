#!/usr/bin/env python3
import argparse, math, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def log_spiral(theta, a=1.0, k=0.15):
    r = a * np.exp(k * theta); x = r*np.cos(theta); y = r*np.sin(theta); return x,y

def path_length(x,y):
    dx=np.diff(x); dy=np.diff(y); return float(np.sum(np.hypot(dx,dy)))

def curvature_penalty(x,y):
    dx=np.diff(x); dy=np.diff(y); h=np.arctan2(dy,dx)
    d=np.diff(h); d=(d+np.pi)%(2*np.pi)-np.pi
    return float(np.sum(np.abs(d)))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--n",type=int,default=600)
    p.add_argument("--radius",type=float,default=10.0)
    p.add_argument("--k",type=float,default=0.15)
    p.add_argument("--noise",type=float,default=0.04)
    p.add_argument("--alpha",type=float,default=1.0)
    p.add_argument("--beta",type=float,default=0.05)
    p.add_argument("--harm",type=float,default=0.20)
    p.add_argument("--png",default="/opt/lumen-core/reports/spiral_demo.png")
    p.add_argument("--csv",default="/opt/lumen-core/reports/spiral_demo_report.csv")
    a=p.parse_args()

    # straight baseline
    sx=np.linspace(a.radius,0,200); sy=np.zeros_like(sx)
    if a.noise>0: sy+=np.random.normal(0,a.noise,sy.size)
    Ls=path_length(sx,sy); Ks=curvature_penalty(sx,sy); Es=a.alpha*Ls+a.beta*Ks

    # spiral
    tmax=math.log(max(a.radius,1e-6))/max(a.k,1e-6)
    th=np.linspace(0,tmax,a.n); x,y=log_spiral(th,1.0,a.k)
    r_end=np.hypot(x[-1],y[-1]); scale=a.radius/(r_end if r_end>0 else 1.0)
    x*=scale; y*=scale
    if a.noise>0:
        x+=np.random.normal(0,a.noise,x.size); y+=np.random.normal(0,a.noise,y.size)
    Lp=path_length(x,y); Kp=curvature_penalty(x,y)
    Ep=a.alpha*(1.0-a.harm)*Lp + a.beta*Kp

    # plot
    plt.figure(figsize=(8,6))
    plt.plot(sx,sy,lw=3,label=f"Straight  L={Ls:.2f}")
    plt.plot(x,y,lw=3,label=f"Spiral    L={Lp:.2f}")
    plt.scatter([0],[0],s=50,label="Origin"); plt.scatter([a.radius],[0],s=50,label="Target")
    plt.axis("equal"); plt.grid(True,alpha=.3); plt.title("LumenSpiral: Spiral vs Straight Routing")
    plt.legend(); plt.tight_layout(); plt.savefig(a.png,dpi=160)

    import pandas as pd
    pd.DataFrame([{
        "radius":a.radius,"k":a.k,"noise":a.noise,"alpha":a.alpha,"beta":a.beta,"harm_gain":a.harm,
        "L_straight":Ls,"K_straight":Ks,"E_straight":Es,"L_spiral":Lp,"K_spiral":Kp,"E_spiral":Ep,
        "savings_distance_%":(Ls-Lp)/Ls*100.0, "savings_energy_%":(Es-Ep)/Es*100.0
    }]).to_csv(a.csv,index=False)

    print(f"\nSaved: {a.png}\nSaved: {a.csv}\n")

if __name__=="__main__": main()
