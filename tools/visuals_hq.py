import os, math, numpy as np, imageio.v2 as imageio, matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFilter
import moviepy.editor as mpy

AS="docs/assets"; os.makedirs(AS, exist_ok=True)

def genesis_grid():
    w,h=2560,960
    img=Image.new("RGBA",(w,h),(4,6,10,255)); d=ImageDraw.Draw(img)
    for r in np.linspace(40,420,28):
        for t in np.linspace(0,2*np.pi,int(18+r/24)):
            x=int(w/2 + r*np.cos(t) + 32*np.cos(6*t))
            y=int(h/2 + r*np.sin(t) + 32*np.sin(6*t))
            d.ellipse((x-2,y-2,x+2,y+2), fill=(175,255,240,230))
    d.rectangle((0,h-140,w,h), fill=(0,0,0,85))
    img.filter(ImageFilter.GaussianBlur(0.6)).save(f"{AS}/genesis_grid_4k.png")

def flowform_vortex():
    W,H=1280,720; frames=[]
    N=1600; th=np.linspace(0,30*np.pi,N)
    r=7*np.sqrt(np.linspace(0,1,N))*H/2.2
    x0=W/2 + r*np.cos(th); y0=H/2 + r*np.sin(th)
    for k in range(48):
        fig=plt.figure(figsize=(W/100,H/100),dpi=100)
        ax=plt.axes([0,0,1,1]); ax.set_axis_off(); ax.set_facecolor((0.015,0.02,0.05))
        plt.scatter(x0+7*np.cos(th+k/6), y0+7*np.sin(th+k/6), s=0.9, alpha=0.95)
        fig.canvas.draw(); frames.append(np.asarray(fig.canvas.buffer_rgba())); plt.close(fig)
    imageio.mimsave(f"{AS}/flowform_vortex_1080.gif", frames, duration=0.06)

def etherframe_assembly():
    w,h=2560,1440; img=Image.new("RGBA",(w,h),(6,8,12,255))
    d=ImageDraw.Draw(img); cx,cy=w//2,h//2
    for i,a in enumerate(np.linspace(0,2*np.pi,12,endpoint=False)):
        R=260+i*18; bbox=[cx-R, cy-R*0.52, cx+R, cy+R*0.52]
        d.arc(bbox, start=math.degrees(a*0.6), end=math.degrees(a*0.6+220), fill=(0,230,190,240), width=8)
        for t in np.linspace(0.18,1.55,10):
            x=int(cx+R*np.cos(a+t)/1.1); y=int(cy+R*0.52*np.sin(a+t)/1.1)
            d.rectangle((x-10,y-4,x+10,y+4), fill=(255,180,0,225))
    img.save(f"{AS}/etherframe_assembly_4k.png")

def aetherreach_console():
    W,H=1280,720
    def make_frame(t):
        import numpy as np
        img=np.zeros((H,W,3),dtype=np.uint8); img[:]=[5,7,12]
        cx,cy=W//2,H//2
        for k in range(7):
            tt=t+k*0.25
            for u in np.linspace(0,1,900):
                x=int(cx+320*np.cos(2*np.pi*u+tt)+70*np.cos(tt*1.4+k))
                y=int(cy+190*np.sin(2*np.pi*u+tt)+50*np.sin(tt*1.1-k))
                if 0<=x<W and 0<=y<H: img[y,x]=[0,220,190]
        return img
    clip=mpy.VideoClip(make_frame, duration=8)
    clip.write_videofile(f"{AS}/aetherreach_console_1080.mp4", fps=30, codec='libx264', audio=False, preset='medium', bitrate='3M', verbose=False, logger=None)

def novacore_reactor():
    W,H=1080,1080
    yy,xx=np.mgrid[-1:1:H*1j,-1:1:W*1j]; rr=np.sqrt(xx**2+yy**2); frames=[]
    for t in np.linspace(0,2*np.pi,48,endpoint=False):
        field=np.sin(10*rr - t)*np.exp(-3*(rr-0.52)**2)
        field+=0.45*np.sin(18*np.arctan2(yy,xx)+t)
        field=(field-field.min())/(field.max()-field.min()+1e-9)
        frames.append((plt.cm.plasma(field)*255).astype(np.uint8))
    imageio.mimsave(f"{AS}/novacore_reactor_1080.gif", frames, duration=0.06)

def banner():
    base=Image.open(f"{AS}/genesis_grid_4k.png").convert("RGBA").resize((1600,400))
    ImageDraw.Draw(base).rectangle((0,300,1600,400), fill=(0,0,0,80))
    base.save(f"{AS}/banner.png")

genesis_grid(); flowform_vortex(); etherframe_assembly(); aetherreach_console(); novacore_reactor(); banner()
print("DONE")
