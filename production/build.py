"""Build a 150-second, 15-scene LUMINEX film from nine animated shots."""
from pathlib import Path
import subprocess,os,sys,json,time,concurrent.futures,shutil,argparse
from PIL import Image
import numpy as np
from composite import overlays,city_frame,W,H
P=Path(__file__).resolve().parent;ROOT=Path('/workspace/ai-video-project/production') if str(P).startswith('/workspace/work') else P;OUT=ROOT.parent/'output';FPS=24
MAPPING={1:1,2:2,3:3,4:4,5:5,6:5,7:10,8:8,9:3,10:10,11:10,12:12,13:13}
P.joinpath('clips').mkdir(exist_ok=True);P.joinpath('masters').mkdir(exist_ok=True)
def encoder(path):return subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-maxrate','4M','-bufsize','8M','-threads','1','-pix_fmt','yuv420p',str(path)],stdin=subprocess.PIPE)
def make_city(i):
 dst=P/'clips'/f'{i:02}.mp4';proc=encoder(dst)
 for f in range(240):proc.stdin.write(city_frame(i,f/24).tobytes())
 proc.stdin.close();assert proc.wait()==0;print('CLIP_DONE',i,'city',flush=True)
def master(src):
 dst=P/'masters'/f'{src:02}.mp4'
 vf='tpad=stop_mode=clone:stop_duration=0.3,minterpolate=fps=24:mi_mode=mci:mc_mode=obmc:me_mode=bidir:me=epzs:vsbmc=0,scale=1920:1080:flags=lanczos'
 subprocess.run(['ffmpeg','-y','-v','error','-threads','1','-filter_threads','1','-framerate','12','-start_number','1','-i',str(P/'frames'/f'{src:02}'/'%04d.png'),'-vf',vf,'-frames:v','240','-an','-c:v','libx264','-preset','veryfast','-crf','16','-threads','1','-pix_fmt','yuv420p',str(dst)],check=True)
 print('MASTER_DONE',src,flush=True)
def assemble(i,src):
 dst=P/'clips'/f'{i:02}.mp4';quads=np.array(json.loads((P/f'projection_{src:02}.json').read_text()));inp=subprocess.Popen(['ffmpeg','-v','error','-threads','1','-i',str(P/'masters'/f'{src:02}.mp4'),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE);proc=encoder(dst)
 for f in range(240):
  raw=inp.stdout.read(W*H*3);assert len(raw)==W*H*3,(i,f,len(raw));im=Image.frombytes('RGB',(W,H),raw);at=f/2;j=int(at);k=min(j+1,119);quad=quads[j]*(1-(at-j))+quads[k]*(at-j);im=overlays(im,i,f/24,quad);proc.stdin.write(im.tobytes())
  if f in [48,120,192]:im.save(P/f'proof_{i:02}_{f:03}.jpg',quality=95)
 proc.stdin.close();assert proc.wait()==0;inp.stdout.close();assert inp.wait()==0;print('CLIP_DONE',i,'source',src,flush=True)
def finish():
 cmd=['ffmpeg','-y','-v','error','-filter_complex_threads','1']
 for i in range(15):cmd+=['-threads','1','-i',str(P/'clips'/f'{i:02}.mp4')]
 cmd+=['-i',str(ROOT/'assets'/'soundtrack.m4a')];filters=[]
 for i in range(15):filters.append(f'[{i}:v]null'+(',tpad=stop_mode=clone:stop_duration=0.166667' if i<14 else '')+f',fps=24[v{i}]')
 prev='v0'
 for i in range(1,15):label=f'x{i}';filters.append(f'[{prev}][v{i}]xfade=transition=fade:duration=0.166667:offset={i*10}[{label}]');prev=label
 filters.append(f'[{prev}]fade=t=in:st=0:d=0.25,fade=t=out:st=149.6:d=0.4[final]')
 cmd+=['-filter_complex',';'.join(filters),'-map','[final]','-map','15:a:0','-c:v','libx264','-preset','fast','-crf','18','-maxrate','4M','-bufsize','8M','-threads','2','-pix_fmt','yuv420p','-r','24','-c:a','copy','-t','150','-metadata','title=LUMINEX — Pohang 2035','-metadata','comment=Textured rigged 3D animation; Microsoft Rocketbox MIT; Wayfair / Eric Chadwick CC BY 4.0 and CC0','-movflags','+faststart',str(OUT/'AI_Smart_Window_Pohang.mp4')]
 subprocess.run(cmd,check=True);shutil.copy2(OUT/'AI_Smart_Window_Pohang.mp4',OUT/'LUMINEX_Pohang_2035.mp4');print('FULL_MP4_WRITTEN',flush=True)
def watch():
 
 for i in [0,14]:
  if not (P/'clips'/f'{i:02}.mp4').exists():make_city(i)
 waiting=set(MAPPING.values())
 while waiting:
  for src in list(waiting):
   if (P/f'projection_{src:02}.json').exists() and len(list((P/'frames'/f'{src:02}').glob('*.png')))==120:
    if not (P/'masters'/f'{src:02}.mp4').exists():master(src)
    for i,s in MAPPING.items():
     if s==src and not (P/'clips'/f'{i:02}.mp4').exists():assemble(i,src)
    waiting.remove(src)
  log=(P/'render_all.log').read_text()
  if 'Traceback' in log:raise RuntimeError(log)
  if waiting:time.sleep(5)
 finish()
def render():
 def one(i):
  env=os.environ.copy();env['LP_NUM_THREADS']='1';env['MESA_SHADER_CACHE_DIR']=str(P/'cache')
  with (P/f'render_{i:02}.log').open('w') as f:subprocess.run(['blender','-b','-t','1','--factory-startup','--python',str(P/'scene.py'),'--','--scene',str(i),'--frames','120','--width','1280'],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(one,sorted(set(MAPPING.values()))))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');args=parser.parse_args()
 if args.watch:watch()
 else:
  render();make_city(0);make_city(14)
  for src in sorted(set(MAPPING.values())):
   master(src)
   for i,s in MAPPING.items():
    if s==src:assemble(i,src)
  finish()
