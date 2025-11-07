#!/usr/bin/env python3
# LumenCore–NovaCore Harmonic Simulation (Nobel+ Auto-Tune Edition)
# Robert Ashworth – 2025
import os, json, time, math, zipfile, io, random
from datetime import datetime
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from tqdm import tqdm

RNG_SEED = 42
BASE_SAMPLES = 4000
REFINE_SAMPLES = 12000
DURATION = 60.0
NOISES   = [0.01, 0.02, 0.03]
F0S      = [2.8, 3.0, 3.1415, 3.3]
DFS      = [0.003, 0.005, 0.008]
GAINCS   = [0.08, 0.1, 0.12]
W_SI  = 1.0
W_ERR = 0.35

def set_seed(seed=RNG_SEED):
    random.seed(seed); np.random.seed(seed)

def simulate(N, T, f0, df, noise_sigma, gain_c, seed=None):
    if seed is not None: np.random.seed(seed)
    t = np.linspace(0.0, T, N)
    energy = np.zeros(N); stability=np.zeros(N); err=np.zeros(N)
    for i in range(N):
        drift = np.sin(f0*t[i]) * np.exp(-df*(i/N))
        correction = np.cos((f0*t[i])/2.0) * gain_c
        noise = np.random.normal(0.0, noise_sigma)
        energy[i]  = drift + correction + noise
        stability[i] = 1.0/(1.0+abs(energy[i]))
        err[i] = 0.5*(energy[i]**2)
    return t, energy, stability, err

def metrics(stability, t, err):
    si_med = float(np.median(stability))
    int_err = float(np.trapz(err, t))
    return si_med, int_err

def composite_score(si_med, int_err):
    return float(W_SI*si_med - W_ERR*math.log1p(int_err))

def bootstrap_ci(x, iters=300, alpha=0.05):
    n=len(x); meds=[]; idx=np.arange(n)
    for _ in range(iters):
        samp=x[np.random.choice(idx, size=n, replace=True)]
        meds.append(np.median(samp))
    lo=np.quantile(meds,alpha/2.0); hi=np.quantile(meds,1.0-alpha/2.0)
    return float(lo),float(hi)

def psd(energy, fs):
    freqs=np.fft.rfftfreq(len(energy), d=1.0/fs)
    mag=np.abs(np.fft.rfft(energy))**2
    return freqs,mag

def spectral_coherence_metric(freqs,mag):
    peak=float(mag.max()+1e-9); med=float(np.median(mag)+1e-9)
    return float(peak/med)

def ensure_dir(d): os.makedirs(d, exist_ok=True)

def main():
    set_seed()
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    outdir = f"nova_run_{stamp}"
    ensure_dir(outdir)

    # Grid search (coarse)
    recs=[]; total=len(F0S)*len(DFS)*len(NOISES)*len(GAINCS)
    pbar=tqdm(total=total, desc="Grid search (coarse)")
    for f0 in F0S:
        for df in DFS:
            for ns in NOISES:
                for gc in GAINCS:
                    t,e,s,er=simulate(BASE_SAMPLES, DURATION, f0, df, ns, gc)
                    si,ie=metrics(s,t,er); comp=composite_score(si,ie)
                    recs.append({"f0":f0,"df":df,"noise":ns,"gain_c":gc,
                                 "SI_med":si,"int_err":ie,"score":comp})
                    pbar.update(1)
    pbar.close()
    grid_df=pd.DataFrame(recs).sort_values("score", ascending=False)
    grid_df.to_csv(os.path.join(outdir,"grid_results.csv"), index=False)

    # Refine best
    best=grid_df.iloc[0].to_dict()
    t,e,s,er=simulate(REFINE_SAMPLES, DURATION, best["f0"], best["df"], best["noise"], best["gain_c"], seed=RNG_SEED+999)
    si,ie=metrics(s,t,er); si_lo,si_hi=bootstrap_ci(s, iters=300)
    fs=REFINE_SAMPLES/DURATION; freqs,mag=psd(e,fs); coh= spectral_coherence_metric(freqs,mag)

    best_df=pd.DataFrame({"t":t,"energy":e,"stability":s,"error":er})
    best_df.to_csv(os.path.join(outdir,"best_timeseries.csv"), index=False)

    # Plots
    plt.figure(figsize=(11,6))
    plt.subplot(2,1,1); plt.plot(t,e,'g'); plt.title('Energy Flow (Best Tuned)')
    plt.subplot(2,1,2); plt.plot(t,s,'b'); plt.title('Stability Index (Best Tuned)')
    plt.tight_layout(); plt.savefig(os.path.join(outdir,"plot_timeseries.png"), dpi=300)

    plt.figure(figsize=(8,5))
    plt.semilogy(freqs,mag+1e-12); plt.xlabel("Hz"); plt.ylabel("PSD")
    plt.title("Energy Spectrum (Best Tuned)"); plt.tight_layout()
    plt.savefig(os.path.join(outdir,"plot_psd.png"), dpi=300)

    pivot=grid_df[(grid_df["noise"]==best["noise"]) & (grid_df["gain_c"]==best["gain_c"])]
    if len(pivot)>0:
        pvt=pivot.pivot_table(index="f0", columns="df", values="score", aggfunc="max")
        plt.figure(figsize=(7,5))
        plt.imshow(pvt.values,aspect='auto',origin='lower',
                   extent=[pvt.columns.min(), pvt.columns.max(), pvt.index.min(), pvt.index.max()])
        plt.colorbar(label="Composite Score")
        plt.xlabel("df"); plt.ylabel("f0"); plt.title("Score Heatmap @ best noise/gain")
        plt.tight_layout(); plt.savefig(os.path.join(outdir,"plot_heatmap.png"), dpi=300)

    summary={
        "timestamp": stamp,
        "best_config":{"f0":best["f0"],"df":best["df"],"noise":best["noise"],"gain_c":best["gain_c"]},
        "refined_metrics":{"median_SI":round(si,6),"median_SI_CI95":[round(si_lo,6),round(si_hi,6)],
                           "integrated_error_energy":round(ie,6),"spectral_coherence_ratio":round(coh,6)},
        "composite_score": round((1.0*si - 0.35*math.log1p(ie)),6),
        "files":["best_timeseries.csv","plot_timeseries.png","plot_psd.png","grid_results.csv","plot_heatmap.png"]
    }
    with open(os.path.join(outdir,"summary.json"),"w") as f: json.dump(summary,f,indent=2)

    # Report
    report_txt=os.path.join(outdir,"Harmonic_Report.txt")
    with open(report_txt,"w") as f:
        f.write("LumenCore/NovaCore – Harmonic Auto-Tune Report\n")
        f.write(f"UTC: {stamp}\n\nBest Config:\n{json.dumps(summary['best_config'],indent=2)}\n\n")
        f.write(f"Refined Metrics:\n{json.dumps(summary['refined_metrics'],indent=2)}\n")
        f.write(f"\nComposite Score: {summary['composite_score']}\n")
    try:
        from fpdf import FPDF
        pdf=FPDF(); pdf.add_page(); pdf.set_font("Helvetica","B",16)
        pdf.cell(0,10,"LumenCore / NovaCore – Harmonic Auto-Tune Report",ln=1)
        pdf.set_font("Helvetica","",11)
        pdf.multi_cell(0,6, f"UTC: {stamp}\n\nBest Config: {summary['best_config']}\n\n"
                            f"Refined Metrics: {summary['refined_metrics']}\n\n"
                            f"Composite Score: {summary['composite_score']}")
        for img in ["plot_timeseries.png","plot_psd.png","plot_heatmap.png"]:
            p=os.path.join(outdir,img)
            if os.path.exists(p): pdf.add_page(); pdf.image(p, x=10, y=20, w=190)
        pdf.output(os.path.join(outdir,"Harmonic_Report.pdf"))
    except Exception: pass

    zipname=f"{outdir}.zip"
    with zipfile.ZipFile(zipname,'w',zipfile.ZIP_DEFLATED) as z:
        for fn in os.listdir(outdir):
            z.write(os.path.join(outdir,fn), arcname=os.path.join(outdir,fn))

    print("\n=== Nova Harmonics Summary ===")
    print("Best config:", summary['best_config'])
    print("Median SI:", summary['refined_metrics']['median_SI'], "CI:", tuple(summary['refined_metrics']['median_SI_CI95']))
    print("Int. Err Energy:", summary['refined_metrics']['integrated_error_energy'])
    print("Coherence:", summary['refined_metrics']['spectral_coherence_ratio'])
    print("Artifacts:", zipname)
    print("Outputs:", outdir + "/")

if __name__=="__main__": main()
