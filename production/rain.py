"""Lens-like water beads on moving glass and depth-masked exterior rainfall."""
from functools import lru_cache
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops

def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
@lru_cache(None)
def seeds(pane):
 rng=np.random.default_rng(735+pane);return rng.random((225,7))
@lru_cache(None)
def falling():return np.random.default_rng(2035).random((820,6))
def homography(quad):
 target=np.array(quad,dtype=float);source=[(0,1),(1,1),(1,0),(0,0)];a=[];b=[]
 for (u,v),(x,y) in zip(source,target):a.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*y,-v*y]]);b.extend([x,y])
 return np.append(np.linalg.solve(np.array(a),np.array(b)),1).reshape(3,3)
def apply(im,i,t,panes,visibility):
 intensity=1 if i==11 else .74*ease((t-3.25)/1.15) if i==10 else .70 if i==1 and t<5 else 0
 if not intensity or visibility is None:return im
 w,h=im.size;visible=visibility.resize((w,h),Image.Resampling.NEAREST).convert('L');outside=visible.point(lambda x:255 if x>50 else 0);glass=visible.point(lambda x:255 if x>190 else 0);glass_array=np.asarray(glass,dtype=np.float32)/255
 # Several exposure depths, lengths and opacities, with a short shutter trail.
 layer=Image.new('RGBA',(w,h));d=ImageDraw.Draw(layer)
 for j,(sx,sy,speed,depth,alpha,shift) in enumerate(falling()):
  x=((sx-(.035+.045*depth)*t)%1)*w;y=((sy+(.43+.57*speed)*t)%1)*h;length=5+18*depth;dx=length*(.22 if i!=11 else .62);opacity=round((10+38*alpha)*intensity)
  d.line([(x+dx,y-length),(x,y)],fill=(182,207,217,opacity),width=1 if depth<.83 else 2)
  if depth>.85:d.line([(x+dx+2,y-length),(x+2,y)],fill=(194,214,225,opacity//4),width=2)
 layer=Image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(.55)),layer);layer.putalpha(ImageChops.multiply(layer.getchannel('A'),outside));im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
 # Trails are deliberately faint: beads bend the scenery instead of looking
 # like painted white capsules. Their coordinates belong to each sliding sash.
 paths=Image.new('RGBA',(w,h));d=ImageDraw.Draw(paths);beads=[]
 for k,quad in enumerate(panes):
  q=np.array(quad)*[w,h];matrix=homography(q);scale=max(.45,min(1.3,np.linalg.norm(q[1]-q[0])/700))
  for j,(u,v,size,speed,age,wiggle,branch) in enumerate(seeds(k)):
   v=(v+(.002+.014*size**2)*t)%1;u+=.0018*math.sin(t*.7+wiggle*12);p=matrix@np.array([u,v,1]);x,y=p[:2]/p[2];r=(1.4+4.8*size**3)*scale
   if j<12:r=(5.5+5*size)*scale
   if x<-r or x>w+r or y<-r or y>h+r:continue
   if j<38 and r>2:
    length=(13+28*size)*scale;points=[(x+math.sin(a*.7+wiggle*7)*1.3*scale,y-length+a*length/7) for a in range(8)];d.line(points,fill=(229,244,247,round(27*intensity)),width=1);d.line([(a+1,b) for a,b in points],fill=(5,22,28,round(19*intensity)),width=1)
   beads.append((x,y,r))
 paths.putalpha(ImageChops.multiply(paths.getchannel('A'),glass));im=Image.alpha_composite(im.convert('RGBA'),paths).convert('RGB');base=np.asarray(im).copy();result=base.copy()
 for x,y,r in beads:
  x0=max(0,int(x-r-1));x1=min(w,int(x+r+2));y0=max(0,int(y-r-1));y1=min(h,int(y+r+2))
  if x1<=x0 or y1<=y0:continue
  yy,xx=np.mgrid[y0:y1,x0:x1];nx=(xx-x)/r;ny=(yy-y)/r;radius=nx*nx+ny*ny;circle=radius<1;coverage=circle*glass_array[y0:y1,x0:x1]
  if not np.any(coverage):continue
  sx=np.clip(np.rint(x+(xx-x)*1.32+r*.18),0,w-1).astype(int);sy=np.clip(np.rint(y+(yy-y)*1.17-r*.23),0,h-1).astype(int);lens=base[sy,sx].astype(np.float32)
  highlight=np.exp(-((nx+.34)**2+(ny+.43)**2)/.026)*90;rim=np.clip((radius-.68)/.32,0,1)*13;shade=highlight-rim+5*(ny-nx);lens=np.clip(lens+shade[...,None],0,255);alpha=coverage*np.clip((1-radius)*4,0,1)*(.48+.16*intensity)
  patch=result[y0:y1,x0:x1].astype(np.float32);result[y0:y1,x0:x1]=np.uint8(patch*(1-alpha[...,None])+lens*alpha[...,None])
 return Image.fromarray(result)
