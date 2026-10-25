"""Build a 150-second, 15-scene LUMINEX film from ten animated shots."""
from pathlib import Path
import sys
_runtime=Path(__file__).resolve().parent/".runtime/pylibs"
if _runtime.exists():sys.path.insert(0,str(_runtime))
import subprocess,os,sys,json,time,concurrent.futures,shutil,argparse
from PIL import Image
import numpy as np
from composite import overlays,city_frame,W,H
P=Path(__file__).resolve().parent;ROOT=P;OUT=ROOT.parent/'output';FPS=24
MAPPING={1:1,2:2,3:3,4:4,5:5,6:5,7:7,8:8,9:3,10:10,11:10,12:12,13:13}
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
 dst=P/'clips'/f'{i:02}.mp4';metadata=json.loads((P/f'camera_{src:02}.json').read_text());retime=i in [6,11];read=['ffmpeg','-v','error','-threads','1','-i',str(P/'masters'/f'{src:02}.mp4')]
 if retime:
  start,rate=(2.5,.75) if i==6 else (1,.9);read+=['-filter_threads','1','-vf',f'trim=start={start},setpts=(PTS-STARTPTS)/{rate},fps=24,tpad=stop_mode=clone:stop_duration=0.2','-frames:v','240']
 read+=['-f','rawvideo','-pix_fmt','rgb24','-'];inp=subprocess.Popen(read,stdout=subprocess.PIPE);proc=encoder(dst);home=None
 if i==12:home=subprocess.Popen(['ffmpeg','-v','error','-threads','1','-i',str(P/'masters/10.mp4'),'-vf','scale=480:270','-threads','1','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
 for f in range(240):
  raw=inp.stdout.read(W*H*3);assert len(raw)==W*H*3,(i,f,len(raw));im=Image.frombytes('RGB',(W,H),raw);source_time=(2.5+.75*f/24) if i==6 else (1+.9*f/24) if i==11 else f/24;at=min(119,source_time*12);j=int(at);k=min(j+1,119);w=at-j;quad=np.array(metadata[j]['quad'])*(1-w)+np.array(metadata[k]['quad'])*w;hands=np.array(metadata[j]['hands'])*(1-w)+np.array(metadata[k]['hands'])*w;home_frame=None
  if home:
   hraw=home.stdout.read(480*270*3);assert len(hraw)==480*270*3;home_frame=Image.frombytes('RGB',(480,270),hraw)
  im=overlays(im,i,f/24,quad,occluders=hands.tolist(),home_frame=home_frame);proc.stdin.write(im.tobytes())
  if f in [24,48,96,120,168,192,216]:im.save(P/f'proof_{i:02}_{f:03}.jpg',quality=95)
 proc.stdin.close();assert proc.wait()==0;inp.stdout.close();assert inp.wait()==0
 if home:home.stdout.close();assert home.wait()==0
 print('CLIP_DONE',i,'source',src,flush=True)
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
   if (P/f'camera_{src:02}.json').exists() and len(list((P/'frames'/f'{src:02}').glob('*.png')))==120:
    if not (P/'masters'/f'{src:02}.mp4').exists():master(src)
    for i,s in MAPPING.items():
     if i==12 and not (P/'masters/10.mp4').exists():continue
     if s==src and not (P/'clips'/f'{i:02}.mp4').exists():assemble(i,src)
    if all((P/'clips'/f'{i:02}.mp4').exists() for i,s in MAPPING.items() if s==src):waiting.remove(src)
  log=(P/'render_all.log').read_text()
  if 'Traceback' in log:raise RuntimeError(log)
  if waiting:time.sleep(5)
 finish()
def render():
 def one(i):
  env=os.environ.copy();env['LP_NUM_THREADS']='1';env['MESA_SHADER_CACHE_DIR']=str(P/'cache');env['OPENBLAS_NUM_THREADS']='1';env['LUMINEX_PYTHON']=sys.executable
  with (P/f'render_{i:02}.log').open('w') as f:subprocess.run(['blender','-b','-t','1','--factory-startup','--python-exit-code','1','--python',str(P/'scene.py'),'--','--scene',str(i),'--frames','120','--width','1280','--samples',str(6 if i in [12,13] else 4)],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(one,sorted(set(MAPPING.values()))))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--watch',action='store_true');args=parser.parse_args()
 if args.watch:watch()
 else:
  render();make_city(0);make_city(14)
  for src in [5,4,8,10,12,7,13,2,3,1]:
   master(src)
   for i,s in MAPPING.items():
    if s==src:assemble(i,src)
  finish()
