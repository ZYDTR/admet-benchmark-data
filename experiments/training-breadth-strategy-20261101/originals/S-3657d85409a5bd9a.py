from pathlib import Path
import sys,json,hashlib,tarfile,io
sys.path.insert(0,str(Path(__file__).resolve().parent));import transport
R=Path(__file__).resolve().parents[1];tag=sys.argv[1];assert tag in ['preflight-fetch','preflight02-fetch','final-fetch']
source=r'''import sys,json,hashlib,os,socket,stat,tarfile,io
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-follow-20261031')
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012 and ROOT.resolve(strict=True)==ROOT
manifest={};files=[];total=0
for sub in ['raw','source','artifacts','state','input']:
 for p in sorted((ROOT/sub).rglob('*')):
  assert not p.is_symlink() and p.resolve()==p
  if p.is_dir():continue
  st=p.stat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1
  n=str(p.relative_to(ROOT));total+=st.st_size;assert total<=1024**3
  with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  manifest[n]={'size':st.st_size,'sha256':h};files.append((n,p))
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as tar:
 for n,p in files:
  with p.open('rb') as f:data=f.read()
  assert hashlib.sha256(data).hexdigest()==manifest[n]['sha256'],'File still changing; wait for terminal'
  m=tarfile.TarInfo(n);m.size=len(data);tar.addfile(m,io.BytesIO(data))
 data=json.dumps(manifest,indent=2).encode();m=tarfile.TarInfo('fetch-manifest.json');m.size=len(data);tar.addfile(m,io.BytesIO(data))
'''
(R/'source/collect_remote.py').write_text(source)
assert not (R/'raw'/tag).exists()
data=transport.remote(source,tag,timeout=90);target=R/'raw'/tag;target.mkdir()
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
 for m in tar:
  assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
  p=target/m.name;assert target in p.parents;p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:f.write(tar.extractfile(m).read())
manifest=json.loads((target/'fetch-manifest.json').read_text())
for n,v in manifest.items():
 p=target/n;assert p.stat().st_size==v['size'] and hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']
print(json.dumps({'files':len(manifest),'bytes':sum(x['size'] for x in manifest.values()),'hashes_verified':True,'path':str(target)}))
