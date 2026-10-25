"""Check that both downloadable files are real, identical, decodable MP4s."""
from pathlib import Path
import argparse,hashlib,json,subprocess

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def verify(folder):
 movie=folder/'LUMINEX_Pohang_2035.mp4';compat=folder/'AI_Smart_Window_Pohang.mp4'
 for path in [movie,compat]:
  assert path.is_file() and path.stat().st_size>5_000_000,path
  with path.open('rb') as f:assert f.read(12)[4:8]==b'ftyp',path
 checksum=digest(movie);assert checksum==digest(compat),'The two MP4 files differ'
 data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(movie)]));video=next(s for s in data['streams'] if s['codec_type']=='video');audio=next(s for s in data['streams'] if s['codec_type']=='audio')
 assert video['codec_name']=='h264' and (video['width'],video['height'])==(1920,1080)
 assert video['r_frame_rate']=='24/1' and int(video['nb_frames'])==3600
 assert abs(float(data['format']['duration'])-150)<.05
 assert audio['codec_name']=='aac' and audio['channels']==2
 subprocess.run(['ffmpeg','-v','error','-threads','1','-i',str(movie),'-f','null','-'],check=True)
 return {'product':'LUMINEX','files':[movie.name,compat.name],'identical':True,'duration_seconds':float(data['format']['duration']),'resolution':[video['width'],video['height']],'frames':int(video['nb_frames']),'size_bytes':movie.stat().st_size,'sha256':checksum,'full_decode':'passed'}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('output',type=Path,nargs='?',default=Path(__file__).resolve().parent.parent/'output');args=parser.parse_args();print(json.dumps(verify(args.output),ensure_ascii=False,indent=2))
