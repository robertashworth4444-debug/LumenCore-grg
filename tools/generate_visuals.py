import numpy as np, matplotlib.pyplot as plt, imageio.v2 as imageio, os, math, moviepy.editor as mpy
from PIL import Image, ImageDraw, ImageFilter

ASSETS="docs/assets"; os.makedirs(ASSETS, exist_ok=True)

# 1) genesis_grid.png — honeycomb/spiral node lattice
def genesis_grid():
    w,h=1600,600
    img=Image.new("RGBA",(w,h),(5,8,12,255))
    draw=ImageDraw.Draw(img)
    # hex-ish grid with spiral intensity
    for r in np.linspace(40,260,22):
        for t in np.linspace(0,2*np.pi,int(18+r/30)):
            x=int(w/2 + r*np.cos(t) + 30*np.cos(6*t))
            y=int(h/2 + r*np.sin(t) + 30*np.sin(6*t))
            rad=int(3+2*np.sin(3*t+r/25))
            glow=Image.new("RGBA",(rad*8,rad*8),(0,0,0,0))
            gdraw=ImageDraw.Draw(glow)
            gdraw.ellipse((0,0,rad*8,rad*8), fill=(0,255,200,18))
            img.alpha_composite(glow, (x-rad*4, y-rad*4))
            draw.ellipse((x-rad,y-rad,x+rad,y+rad), fill=(180,255,240,230))
    title=Image.new("RGBA",(w,120),(0,0,0,0))
    tdraw=ImageDraw.Draw(title)
    # simple bar highlight
    tdraw.rectangle((0,90,w,120), fill=(0,255,200,25))
    img.alpha_composite(title,(0,0))
    img.filter(ImageFilter.GaussianBlur(0.5)).save(f"{ASSETS}/genesis_grid.png")

# 2) flowform_vortex.gif — Fibonacci spiral particles
def flowform_vortex():
    frames=[]
    W,H=720,480
    N=900
    theta=np.linspace(0,24*np.pi,N)
    r=6*np.sqrt(np.linspace(0,1,N))*H/2.6
    x0=W/2 + r*np.cos(theta)
    y0=H/2 + r*np.sin(theta)
    for k in range(40):
        fig=plt.figure(figsize=(W/100,H/100),dpi=100)
        ax=plt.axes([0,0,1,1]); ax.set_axis_off()
        plt.scatter(x0+6*np.cos(theta+k/4), y0+6*np.sin(theta+k/4), s=1.2, alpha=0.9)
        ax.set_facecolor((0.02,0.03,0.06))
        frames.append(mpy.ImageClip(fig.canvas.buffer_rgba(), with_mask=False).get_frame(0))
        plt.close(fig)
    imageio.mimsave(f"{ASSETS}/flowform_vortex.gif", frames, duration=0.06)

# 3) etherframe_assembly.png — “exploded” curved PCB petals
def etherframe_assembly():
    w,h=1400,700
    img=Image.new("RGBA",(w,h),(6,8,12,255))
    draw=ImageDraw.Draw(img)
    cx,cy=w//2,h//2
    for i,a in enumerate(np.linspace(0,2*np.pi,11,endpoint=False)):
        R=210+i*12
        bbox=[cx-R, cy-R*0.55, cx+R, cy+R*0.55]
        draw.arc(bbox, start=math.degrees(a*0.6), end=math.degrees(a*0.6+210), fill=(0,230,180,240), width=6)
        # copper pads
        for t in np.linspace(0.1,1.6,8):
            x=int(cx+R*np.cos(a+t)/1.1); y=int(cy+R*0.55*np.sin(a+t)/1.1)
            draw.rectangle((x-8,y-3,x+8,y+3), fill=(255,180,0,220))
    img.save(f"{ASSETS}/etherframe_assembly.png")

# 4) aetherreach_console.mp4 — UI signal threads animation
def aetherreach_console():
    W,H=900,540
    def make_frame(t):
        import numpy as np
        img=np.zeros((H,W,3),dtype=np.uint8); img[:]=[5,7,12]
        cx,cy=W//2,H//2
        for k in range(6):
            tt=t+k*0.3
            for u in np.linspace(0,1,800):
                x=int(cx+280*np.cos(2*np.pi*u+tt)+60*np.cos(tt*1.4+k))
                y=int(cy+160*np.sin(2*np.pi*u+tt)+40*np.sin(tt*1.1-k))
                if 0<=x<W and 0<=y<H: img[y,x]=[0,220,190]
        return img
    clip=mpy.VideoClip(make_frame, duration=6)
    clip.write_videofile(f"{ASSETS}/aetherreach_console.mp4", fps=25, codec="libx264", audio=False, verbose=False, logger=None)

# 5) novacore_reactor.gif — heat dispersion self-cooling
def novacore_reactor():
    frames=[]; W,H=720,720
    yy,xx=np.mgrid[-1:1:720j,-1:1:720j]
    rr=np.sqrt(xx**2+yy**2)
    for t in np.linspace(0,2*np.pi,40,endpoint=False):
        field=np.sin(10*rr - t)*np.exp(-3*(rr-0.5)**2)
        field+=0.4*np.sin(16*np.arctan2(yy,xx)+t)
        field=(field-field.min())/(field.max()-field.min()+1e-9)
        img=(plt.cm.inferno(field)*255).astype(np.uint8)
        frames.append(img)
    imageio.mimsave(f"{ASSETS}/novacore_reactor.gif", frames, duration=0.07)

# Simple banner from grid
def banner():
    base=Image.open(f"{ASSETS}/genesis_grid.png").convert("RGBA")
    base=base.resize((1600,400))
    draw=ImageDraw.Draw(base)
    draw.rectangle((0,300,1600,400), fill=(0,0,0,80))
    base.save(f"{ASSETS}/banner.png")

genesis_grid(); flowform_vortex(); etherframe_assembly(); aetherreach_console(); novacore_reactor(); banner()
print("✔ visuals written to docs/assets")
