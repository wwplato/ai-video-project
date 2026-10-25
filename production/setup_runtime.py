"""Install the Linux x86-64 denoiser dependencies beside the source, not in Git."""
from pathlib import Path
import hashlib,subprocess,sys,tarfile,urllib.request
P=Path(__file__).resolve().parent/'.runtime';P.mkdir(exist_ok=True)
subprocess.run([sys.executable,'-m','pip','install','--target',str(P/'pylibs'),'numpy','Pillow','OpenEXR','opencolorio'],check=True)
archive=P/'oidn.tar.gz'
url='https://github.com/RenderKit/oidn/releases/download/v2.5.1/oidn-2.5.1.x86_64.linux.tar.gz'
with urllib.request.urlopen(url,timeout=60) as src,archive.open('wb') as dst:
 while block:=src.read(1024*1024):dst.write(block)
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6','OIDN checksum mismatch'
with tarfile.open(archive) as package:package.extractall(P,filter='data')
archive.unlink();print('Runtime ready:',P)
