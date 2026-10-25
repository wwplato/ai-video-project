"""Transparent animated window graphics, composited in the plane of the glass."""
import math
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from functools import lru_cache
W,H=1400,850
@lru_cache(None)
def font(n,b=False):return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if b else 'Regular')+'.ttc',n)
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
WHITE=(245,255,254,240);TEAL=(153,252,227,225);DIM=(228,251,247,205)
def text(d,pos,s,n=36,color=WHITE,b=False):
 x,y=pos;d.text((x+2,y+2),s,font=font(n,b),fill=(3,30,38,145));d.text((x,y),s,font=font(n,b),fill=color)
def today(t,rainy=False):
 im=Image.new('RGBA',(W,620));d=ImageDraw.Draw(im);text(d,(55,25),('포항 · 비' if rainy else '포항 · 맑음'),42,TEAL);text(d,(48,96),('20°' if rainy else '22°'),178,WHITE,True);text(d,(58,330),('빗방울 감지 · 자동 닫힘' if rainy else '바깥 공기 좋음'),44);text(d,(58,409),'실내 23°C   ·   습도 46%',35,DIM)
 for j,(label,value) in enumerate([('강수 확률','95%' if rainy else '10%'),('미세먼지','좋음')]):
  x=650+j*310;d.line((x,120,x+220,120),fill=TEAL,width=2);text(d,(x,150),label,32,DIM);text(d,(x,218),value,53,WHITE,True)
 return im
def week(t):
 im=Image.new('RGBA',(W,620));d=ImageDraw.Draw(im);text(d,(55,20),'주간 날씨',48,TEAL,True);text(d,(55,98),'터치 한 번으로, 이번 주를 한눈에',32,DIM)
 data=[22,23,25,24,21,22,24];points=[(80+j*175,385-(temp-20)*33) for j,temp in enumerate(data)]
 for y in [250,350,450]:d.line((65,y,1180,y),fill=(211,248,243,65),width=1)
 for j,(x,y) in enumerate(points):text(d,(x-18,477),['월','화','수','목','금','토','일'][j],29,DIM);text(d,(x-25,y-64),str(data[j])+'°',31)
 reveal=ease((t-4.6)/1.0);poly=[]
 for k in range(121):
  at=k/120*6;j=min(5,int(at));a=at-j;x=points[j][0]*(1-a)+points[j+1][0]*a;y=points[j][1]*(1-a)+points[j+1][1]*a
  if k<=120*reveal:poly.append((x,y))
 if len(poly)>1:d.line(poly,fill=TEAL,width=7)
 cursor=6*ease((t-5.0)/2.8);j=min(5,int(cursor));a=cursor-j;x=points[j][0]*(1-a)+points[j+1][0]*a;y=points[j][1]*(1-a)+points[j+1][1]*a;d.line((x,190,x,454),fill=(199,255,245,110),width=2);d.ellipse((x-11,y-11,x+11,y+11),fill=WHITE)
 return im
def render(i,t):
 im=Image.new('RGBA',(W,H),(6,37,46,31));d=ImageDraw.Draw(im);d.line((35,25,1365,25),fill=(166,255,238,120),width=2);d.line((35,825,1365,825),fill=(166,255,238,90),width=2);text(d,(55,50),'LUMINEX',46,WHITE,True);text(d,(1020,64),'POHANG 2035',27,TEAL)
 if i in [2,4,5,10]:
  sub=today(t,i==10 and t>3.8)
  if i in [2,5]:
   u=ease((t-4.1)/1);container=Image.new('RGBA',(W,610));container.alpha_composite(sub,(0,-round(u*630)));container.alpha_composite(week(t),(0,round((1-u)*630)));sub=container
  im.alpha_composite(sub,(0,170))
 elif i==6:
  text(d,(55,180),'오늘의 일정',50,TEAL,True);scroll=110*ease((t-1.5)/2);rows=Image.new('RGBA',(W,530));r=ImageDraw.Draw(rows)
  for j,(time,label) in enumerate([('09:00','과학 수업'),('11:00','프로젝트 발표'),('13:00','창의 활동'),('15:00','비 예보 · 우산을 챙기세요')]):
   y=35+j*122-scroll;active=j==3;fill=(255,215,143,245) if active else WHITE;text(r,(55,y),time,40,fill,True);text(r,(300,y),label,40,fill);r.line((55,y+92,1200,y+92),fill=(216,250,245,80),width=1)
  im.alpha_composite(rows,(0,270))
 elif i==3:
  text(d,(55,230),'06:59' if t<1.4 else '07:00',151,WHITE,True);text(d,(60,460),'편안한 수면' if t<1.4 else '좋은 아침을 준비해요',45,TEAL);text(d,(60,560),'기상 감지  ·  나만의 아침 루틴',32,DIM)
 elif i==7:
  text(d,(55,205),'PRIVACY',105,WHITE,True);text(d,(60,370),'보이는 풍경, 지켜지는 일상',42,TEAL);text(d,(60,480),'실내 전망 유지',37);text(d,(60,570),'외부의 시선은 줄이고',37)
 elif i==8:
  text(d,(55,205),'SOFT LIGHT',95,WHITE,True);text(d,(60,380),'빛은 부드럽게, 시선은 흐리게',40,TEAL);text(d,(60,490),'풍경의 색과 빛을 머금은 반투명',35);text(d,(60,588),'저녁 모드 전환',35,DIM)
 elif i==11:
  orange=(255,210,163,245);text(d,(55,195),'태풍 경보',94,orange,True);text(d,(60,360),'창문을 닫고 안전 잠금',42);text(d,(60,480),'닫는 중…' if t<2.6 else '안전 잠금 완료',43,TEAL);text(d,(60,600),'가족에게 알림 전송',34,DIM)
 elif i==13:
  text(d,(55,200),'SMART CARE',95,WHITE,True);text(d,(60,380),'누구나 편안한 우리 집',42,TEAL);text(d,(60,490),'공기에 맞춘 자동 환기',37);text(d,(60,590),'햇빛에 맞춘 에너지 관리',37)
 if i in [2,5,6]:
  x,y=1340,700;d=ImageDraw.Draw(im);r=51;d.ellipse((x-r,y-r,x+r,y+r),fill=(9,56,65,72),outline=TEAL,width=3);d.line((x,y-20,x,y+8),fill=WHITE,width=4);d.arc((x-24,y-24,x+24,y+24),25,335,fill=WHITE,width=3)
  if (3.5<t<7.4 and i!=6) or (.9<t<6 and i==6):
   r=65+18*(.5+.5*math.sin(t*5));d.ellipse((x-r,y-r,x+r,y+r),outline=(185,255,239,110),width=2)
 # Low-energy emission halo lets the lettering feel projected into the glass.
 glow=im.filter(ImageFilter.GaussianBlur(4));glow.putalpha(glow.getchannel('A').point(lambda a:round(a*.17)));return Image.alpha_composite(glow,im)
