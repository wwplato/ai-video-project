from pathlib import Path
from functools import lru_cache
import json,math,sys,os,subprocess,random
from PIL import Image,ImageDraw,ImageFont,ImageEnhance
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P
ASSETS=ROOT/'assets';TEX=ROOT/'textures';W,H=1920,1080;FPS=24
STORY=json.loads((ROOT/'storyboard.json').read_text());SPEECH=json.loads((ROOT/'speech_segments.json').read_text())
TEAL='#a2e4d5';WHITE='#f5f8f5';MUTED='#d5dfdf'
@lru_cache(None)
def font(size,bold=False):return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',size)
def text(d,pos,s,size=32,fill=WHITE,bold=False,anchor=None):d.text(pos,s,font=font(size,bold),fill=fill,anchor=anchor,stroke_width=0)
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
@lru_cache(None)
def gradient():
 im=Image.new('RGBA',(W,H),(0,0,0,0));a=np.zeros((H,W,4),dtype=np.uint8);a[:,:,:3]=[2,14,24]
 y=np.arange(H);bottom=np.clip((y-750)/310,0,1)**.8*.88;top=np.clip((210-y)/210,0,1)*.55;a[:,:,3]=np.maximum(bottom,top)[:,None]*255;return Image.fromarray(a)
from hud import render as render_hud
def project_ui(im,quad,i,t,occluders=None):
 points=np.array(quad,dtype=np.float64)*[W,H];width=max(128,int(max(np.linalg.norm(points[1]-points[0]),np.linalg.norm(points[2]-points[3]))/32+1)*32);height=round(width*850/1400);src=np.array([[0,height],[width,height],[width,0],[0,0]],dtype=np.float64);A=[];B=[]
 for (x,y),(u,v) in zip(points,src):A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);B.extend([u,v])
 coeff=np.linalg.solve(np.array(A),np.array(B));source=render_hud(i,t).resize((width,height),Image.Resampling.LANCZOS)
 if i==2:source.putalpha(source.getchannel('A').point(lambda value:round(value*ease((t-2.7)/.7))))
 tile=source.transform((W,H),Image.Transform.PERSPECTIVE,coeff,resample=Image.Resampling.BICUBIC)
 if occluders:
  mask=Image.new('L',(W,H),255);d=ImageDraw.Draw(mask)
  for points in occluders:
   p=[(x*W,y*H) for x,y in points];d.line(p,fill=0,width=10)
   for x,y in p:d.ellipse((x-5,y-5,x+5,y+5),fill=0)
  from PIL import ImageChops
  tile.putalpha(ImageChops.multiply(tile.getchannel('A'),mask))
 im.paste(tile,(0,0),tile)
def overlays(im,i,t,quad=None,window=None,occluders=None,home_frame=None,weather_panes=None,weather_mask=None):
 im=im.convert('RGB')
 if i==8:im=Image.blend(im,Image.new('RGB',im.size,'#b67942'),.025)
 if i in [1,10,11] and weather_mask is not None:
  from rain import apply as apply_rain
  im=apply_rain(im,i,t,[] if weather_panes is None else weather_panes,weather_mask)
 if quad is not None and i not in [1,9,12] and not(i==2 and t<2.7):project_ui(im,quad,i,t,occluders)
 if i==12:
  card=Image.new('RGBA',(520,405),(0,0,0,0));cd=ImageDraw.Draw(card);cd.rounded_rectangle((0,0,519,404),radius=18,fill=(5,31,39,157),outline=(159,229,219,180),width=2);text(cd,(21,13),'우리 집 창문  ·  LIVE',23,TEAL,True)
  if home_frame is not None:
   home_frame=home_frame.resize((480,270),Image.Resampling.LANCZOS)
   # The geometry mask keeps foreground furniture clear as the glass darkens.
   strength=ease((t-6)/1.2)
   if strength:
    mask=blackout_coverage().point(lambda value:round(value*strength));home_frame=Image.composite(Image.new('RGB',(480,270),'#03070a'),home_frame,mask)
   card.paste(home_frame,(20,59))
  status='원격 연결됨' if t<3.8 else '창문 닫는 중…' if t<6 else '닫힘 · 안전 잠금' if t<7.2 else '닫힘 · 암흑 모드';text(cd,(23,348),status,25,WHITE,True);im.paste(card,(1340,150),card)
 if i==7 and t>5:
  # Show the exterior finish while the articulated resident remains in view.
  k=ease((t-5)/.35);panel=Image.new('RGBA',(510,337),(0,0,0,0));pd=ImageDraw.Draw(panel);pd.rounded_rectangle((1,1,508,335),radius=19,fill=(5,24,33,245),outline=(123,182,184,230),width=2);pd.text((22,12),'OUTSIDE VIEW  ·  프라이버시 썬팅',font=font(19),fill=TEAL);picture=exterior().resize((472,266),Image.Resampling.LANCZOS);panel.paste(picture,(19,51));panel.putalpha(panel.getchannel('A').point(lambda a:round(a*k)));im.paste(panel,(1370+round((1-k)*36),156),panel)
 layer=gradient()
 if i==5 and t<3.1:
  layer=layer.copy();alpha=np.asarray(layer.getchannel('A')).copy();y=np.arange(H);top=np.clip((470-y)/470,0,1)**.55*.82;bottom=np.clip((y-750)/310,0,1)**.8*.88*ease((t-2.65)/.45);alpha[:]=np.maximum(top,bottom)[:,None]*255;layer.putalpha(Image.fromarray(alpha))
 im.paste(layer,(0,0),layer);d=ImageDraw.Draw(im)
 # Geometric window mark and restrained wordmark.
 x,y=84,61;d.rounded_rectangle((x,y,x+23,y+32),radius=3,outline=TEAL,width=2);d.line((x+12,y+1,x+12,y+31),fill=TEAL,width=2);d.line((x+1,y+16,x+22,y+16),fill=TEAL,width=2)
 text(d,(125,53),'LUMINEX',29,WHITE,True);text(d,(1834,62),f'POHANG 2035   /   {i+1:02d}',22,MUTED,anchor='ra')
 active=next((s for s in SPEECH if s['scene']==i+1 and s['start']<=i*10+t<s['end']),None)
 if active and active['role']=='window':
  d.rounded_rectangle((84,116,321,162),radius=20,fill='#163b43',outline='#587e83',width=1);text(d,(104,119),'LUMINEX VOICE',21,TEAL)
  for j in range(10):
   h=4+12*abs(math.sin(t*8+j*.7));xx=345+j*7;d.line((xx,139-h/2,xx,139+h/2),fill=TEAL,width=2)
 caption=Image.new('RGBA',(W,H));d=ImageDraw.Draw(caption);upper=i==5 and t<2.8;headline_y=182 if upper else 844;subtitle_y=headline_y+109
 title=STORY[i]['headline'];text(d,(96,headline_y+round(12*(1-ease(t/.25)))),title,48,WHITE,True)
 d.line((96,headline_y+85,167,headline_y+85),fill=TEAL,width=3)
 cap=active['text'] if active else STORY[i]['narration'];words=cap.split();lines=[];current=''
 for word in words:
  attempt=(current+' '+word).strip()
  if d.textlength(attempt,font=font(30))>(1100 if upper else 1710):lines.append(current);current=word
  else:current=attempt
 if current:lines.append(current)
 if upper and len(lines)>1:
  pairs=[(' '.join(words[:k]),' '.join(words[k:])) for k in range(1,len(words))];pairs=[pair for pair in pairs if all(d.textlength(part,font=font(30))<=1100 for part in pair)]
  if pairs:lines=list(min(pairs,key=lambda pair:abs(d.textlength(pair[0],font=font(30))-d.textlength(pair[1],font=font(30)))))
 for j,line in enumerate(lines[:2]):text(d,(97,subtitle_y+j*43),line,30,MUTED)
 if i==5:
  opacity=ease((2.8-t)/.15) if upper else ease((t-2.8)/.15);caption.putalpha(caption.getchannel('A').point(lambda value:round(value*opacity)))
 im.paste(caption,(0,0),caption);d=ImageDraw.Draw(im)
 if i==14:
  # Source attribution remains legible and travels with the exported film.
  text(d,(1827,1037),'3D: Microsoft Rocketbox (MIT) · Wayfair / Eric Chadwick (CC BY 4.0, CC0)',17,'#afc5c7',anchor='ra')
 return im
@lru_cache(None)
def blackout_coverage():return Image.open(ASSETS/'home_blackout_mask.png').convert('L').point(lambda value:255 if value>180 else 0)
@lru_cache(None)
def exterior():return Image.open(ASSETS/'privacy.png').convert('RGB')
@lru_cache(None)
def city_image():return Image.open(ASSETS/'city.png').convert('RGB')
def city_frame(i,t):
 src=city_image();sw,sh=src.size;z=1.015+.025*t/10;cw=sw/z;ch=cw*9/16;cx=sw*.51+15*math.sin(t*.12);cy=sh*.51;im=src.crop((round(cx-cw/2),round(cy-ch/2),round(cx+cw/2),round(cy+ch/2))).resize((W,H),Image.Resampling.LANCZOS)
 if i==0:
  scr=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(scr);d.rounded_rectangle((105,240,660,700),radius=26,fill=(4,24,33,142),outline=(167,222,220,90),width=2);text(d,(153,278),'POHANG',40,TEAL,True);text(d,(140,335),'2035',181,WHITE,True);text(d,(154,612),'포항의 내일을 여는 창',34,WHITE);im.paste(scr,(0,0),scr)
 else:
  im=ImageEnhance.Brightness(im).enhance(.5);d=ImageDraw.Draw(im);cx=960;cy=290;w=76;d.rounded_rectangle((cx-w/2,cy-57,cx+w/2,cy+57),radius=8,outline=TEAL,width=4);d.line((cx,cy-54,cx,cy+54),fill=TEAL,width=3);d.line((cx-w/2+3,cy,cx+w/2-3,cy),fill=TEAL,width=3)
  text(d,(960,387),'LUMINEX',148,WHITE,True,'mt');text(d,(960,588),'창문을 넘어, 미래를 열다.',49,TEAL,True,'mt');text(d,(960,691),'AI SMART WINDOW  ·  POHANG 2035',25,MUTED,anchor='mt')
 return overlays(im,i,t)
