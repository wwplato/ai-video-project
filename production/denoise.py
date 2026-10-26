"""CPU path-tracing denoiser with albedo/normal guidance and Blender AgX colors."""
from pathlib import Path
import os,sys,ctypes as C,argparse,time
P=Path(__file__).resolve().parent
for d in [P/'pylibs',P/'.runtime/pylibs']:
 if d.exists():sys.path.insert(0,str(d))
import numpy as np,OpenEXR,PyOpenColorIO as OCIO
from PIL import Image
class Denoiser:
 def __init__(self,w,h):
  candidates=[os.environ.get('LUMINEX_OIDN_LIBRARY',''),str(P/'oidn-2.5.1.x86_64.linux/lib/libOpenImageDenoise.so.2'),str(P/'.runtime/oidn-2.5.1.x86_64.linux/lib/libOpenImageDenoise.so.2')];lib=next((x for x in candidates if x and Path(x).exists()),None)
  if not lib:raise RuntimeError('Install Open Image Denoise 2.5.1 or set LUMINEX_OIDN_LIBRARY')
  self.lib=l=C.CDLL(lib);ptr=C.c_void_p;s=C.c_size_t;i=C.c_int;ch=C.c_char_p
  definitions={'oidnNewDevice':([i],ptr),'oidnSetDeviceInt':([ptr,ch,i],None),'oidnCommitDevice':([ptr],None),'oidnNewFilter':([ptr,ch],ptr),'oidnSetSharedFilterImage':([ptr,ch,ptr,i,s,s,s,s,s],None),'oidnSetFilterBool':([ptr,ch,C.c_bool],None),'oidnSetFilterInt':([ptr,ch,i],None),'oidnCommitFilter':([ptr],None),'oidnExecuteFilter':([ptr],None),'oidnGetDeviceError':([ptr,C.POINTER(ch)],i)}
  for name,(args,ret) in definitions.items():f=getattr(l,name);f.argtypes=args;f.restype=ret
  self.device=l.oidnNewDevice(1);l.oidnSetDeviceInt(self.device,b'numThreads',1);l.oidnCommitDevice(self.device);self.filter=l.oidnNewFilter(self.device,b'RT');self.buffers={name:np.empty((h,w,3),dtype=np.float32) for name in ['color','albedo','normal','output']}
  for name,a in self.buffers.items():l.oidnSetSharedFilterImage(self.filter,name.encode(),a.ctypes.data,3,w,h,0,12,w*12)
  l.oidnSetFilterBool(self.filter,b'hdr',True);l.oidnSetFilterBool(self.filter,b'cleanAux',False);l.oidnSetFilterInt(self.filter,b'quality',6);l.oidnCommitFilter(self.filter);self.check()
 def check(self):
  message=C.c_char_p();code=self.lib.oidnGetDeviceError(self.device,C.byref(message))
  if code:raise RuntimeError(f'OIDN {code}: {message.value.decode()}')
 def run(self,color,albedo,normal):
  self.buffers['color'][:]=np.nan_to_num(color);self.buffers['albedo'][:]=np.nan_to_num(albedo);self.buffers['normal'][:]=np.nan_to_num(normal);self.lib.oidnExecuteFilter(self.filter);self.check();return self.buffers['output'].copy()
def channels(ch,prefix,letters='RGB'):return np.stack([ch[prefix+'.'+c].pixels for c in letters],axis=-1).astype(np.float32)
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path);p.add_argument('--output',type=Path);p.add_argument('--folder',type=Path);p.add_argument('--outdir',type=Path);p.add_argument('--ocio',default='/usr/share/blender/datafiles/colormanagement/config.ocio');p.add_argument('--keep-raw',action='store_true');p.add_argument('--background',type=Path);p.add_argument('--mask-outdir',type=Path);a=p.parse_args();jobs=[(a.input,a.output)] if a.input else [(x,a.outdir/(x.stem+'.png')) for x in sorted(a.folder.glob('*.exr'))]
 cfg=OCIO.Config.CreateFromFile(a.ocio or "/usr/share/blender/datafiles/colormanagement/config.ocio");space=cfg.getRoleColorSpace('scene_linear');look=OCIO.LookTransform(src=space,dst=space,looks='AgX - Medium High Contrast');view=OCIO.DisplayViewTransform(src=space,display='sRGB',view='AgX');proc=cfg.getProcessor(OCIO.GroupTransform([look,view])).getDefaultCPUProcessor();denoiser=None;start=time.monotonic()
 for k,(src,dst) in enumerate(jobs):
  file=OpenEXR.File(str(src),separate_channels=True);ch=file.channels();prefix=next(x[:-2] for x in ch if x.endswith('.Combined.R'));color=channels(ch,prefix);layer=prefix.rsplit('.',1)[0];alb=channels(ch,layer+'.Denoising Albedo') if layer+'.Denoising Albedo.R' in ch else channels(ch,layer+'.DiffCol');nrm=channels(ch,layer+'.Denoising Normal','XYZ') if layer+'.Denoising Normal.X' in ch else channels(ch,layer+'.Normal','XYZ')
  if a.mask_outdir:
   key=next(k for k in ch if '.IndexOB' in k);mask=np.uint8(np.clip(ch[key].pixels/2,0,1)*255+.5);a.mask_outdir.mkdir(parents=True,exist_ok=True);Image.fromarray(mask).save(a.mask_outdir/(dst.stem+'.png'))
  if a.background:color=color/np.maximum(ch[prefix+'.A'].pixels[...,None],.02)
  if denoiser is None:denoiser=Denoiser(color.shape[1],color.shape[0])
  result=denoiser.run(color,alb,nrm);proc.applyRGB(result);rgb=np.uint8(np.clip(result,0,1)*255+.5)
  if a.background:
   foreground=Image.fromarray(rgb).convert('RGBA');foreground.putalpha(Image.fromarray(np.uint8(np.clip(ch[prefix+'.A'].pixels,0,1)*255+.5)));foreground=foreground.resize((1920,1080),Image.Resampling.LANCZOS)
   if a.outdir:
    foreground_dir=a.outdir.parent.parent/'foreground'/a.outdir.name;foreground_dir.mkdir(parents=True,exist_ok=True);foreground.save(foreground_dir/dst.name,compress_level=1)
   bg=Image.open(a.background).convert('RGB').resize((1920,1080),Image.Resampling.LANCZOS);bg.paste(foreground,(0,0),foreground);image=bg
  else:image=Image.fromarray(rgb)
  dst.parent.mkdir(parents=True,exist_ok=True);image.save(dst,compress_level=0)
  if a.folder and not a.keep_raw:src.unlink()
  if k==0 or (k+1)%24==0:print('DENOISED',k+1,'of',len(jobs),'seconds',round(time.monotonic()-start,2),flush=True)
if __name__=='__main__':main()
