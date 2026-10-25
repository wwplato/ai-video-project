from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent/'textures';P.mkdir(exist_ok=True)
reg='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def font(n,b=False):return ImageFont.truetype(bold if b else reg,n)
items={'weather':('오늘의 포항','22°','맑음 · 바깥 공기 좋음',['강수 확률 10%','미세먼지 좋음','실내 23°C · 습도 46%']), 'schedule':('오늘의 일정','15:00','오후부터 비가 예상돼요',['09:00  과학 수업','13:00  창의 프로젝트','우산을 챙겨 주세요']), 'alarm':('나에게 맞춘 아침','07:00','좋은 아침을 준비하고 있어요',['수면 중 · 빛 차단','기상 감지 준비','개인 맞춤 기상 루틴']), 'privacy':('보이는 풍경, 지켜지는 일상','PRIVACY','낮 시간 프라이버시 썬팅',['실내 전망 유지','외부 시선 줄이기','빛에 맞춘 투과율']), 'frost':('편안한 저녁','SOFT LIGHT','부드러운 빛과 사생활 보호',['자동 반투명 전환','실내 조도 조절','나만의 저녁 모드']), 'blackout':('깊이 쉬는 시간','22:00','커튼 없는 완전 차광',['BLACKOUT MODE','외부 빛 차단','취침 루틴 실행']), 'warning':('포항 · 태풍 경보','SAFE LOCK','창문을 닫고 안전 잠금 실행',['폭우 · 강풍 감지','창문 잠금 완료','가족에게 알림 전송']), 'energy':('모두를 위한 기술','ECO','햇빛에 맞춰 실내 환경 조절',['자동 환기','아이와 어르신을 위한 편의','햇빛에 맞춘 실내 환경']), 'phone':('우리 집 LUMINEX','연결됨','창문 상태를 확인해 보세요',['닫힘  ·  안전 잠금','차광 모드  ON','원격 제어 완료'])}
for name,(heading,big,sub,lines) in items.items():
 im=Image.new('RGBA',(1400,1000),(5,22,32,238));d=ImageDraw.Draw(im);teal='#91e5d3';white='#f4faf8';red='#ffad96' if name=='warning' else teal
 d.rounded_rectangle((3,3,1397,997),radius=35,outline='#476770',width=3)
 d.text((65,45),'LUMINEX',font=font(52,True),fill=white);d.text((1335,60),'POHANG 2035',font=font(26),fill=teal,anchor='ra')
 d.line((65,130,1335,130),fill='#39535d',width=2);d.text((65,180),heading,font=font(43),fill=white)
 d.text((65,285),big,font=font(124 if len(big)<8 else 86,True),fill=red)
 d.text((65,465),sub,font=font(40),fill=teal)
 for j,line in enumerate(lines):
  y=590+j*105;d.ellipse((72,y+15,88,y+31),fill=red);d.text((115,y),line,font=font(34),fill=white)
 im.save(P/(name+'.png'))
