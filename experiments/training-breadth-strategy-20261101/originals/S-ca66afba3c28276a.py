from pathlib import Path
import sys,json,hashlib,tarfile,io
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'source'));from transport import remote
files=['source/guard_exec_cuda02.py','source/supervisor_attempt02.py']
expected={n:{'sha256':hashlib.sha256((R/n).read_bytes()).hexdigest(),'size':(R/n).stat().st_size} for n in files}
b=io.BytesIO()
with tarfile.open(fileobj=b,mode='w:gz') as tar:
 for n in files:
  data=(R/n).read_bytes();m=tarfile.TarInfo(n);m.size=len(data);m.mode=0o600;tar.addfile(m,io.BytesIO(data))
source='''import sys,os,socket,hashlib,json,tarfile
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-follow-20261031')
assert ROOT.resolve(strict=True)==ROOT and socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
sys.path.insert(0,str(ROOT/'source'));from common_guarded import safe
expected=EXPECTED
seen=set()
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz') as tar:
 for m in tar:
  assert m.name in expected and m.name not in seen and m.isfile() and m.size==expected[m.name]['size'] and m.size<100000
  p=safe(ROOT/m.name);data=tar.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==expected[m.name]['sha256']
  with os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600),'wb') as f:f.write(data)
  seen.add(m.name)
assert seen==set(expected)
print(json.dumps({'added_sources':expected,'previous_sources_preserved':True}))
'''.replace('EXPECTED',repr(expected))
(R/'source/upload_retry_remote.py').write_text(source)
print(remote(source,'upload-retry02',payload=b.getvalue(),timeout=60).decode())
initial=R/'raw/upload-manifest.json';copy=R/'raw/upload-manifest-initial.json'
assert not copy.exists();copy.write_bytes(initial.read_bytes());merged=json.loads(initial.read_text());merged.update(expected);initial.write_text(json.dumps(merged,indent=2)+'\n')
(R/'raw/upload-retry02-manifest.json').write_text(json.dumps(expected,indent=2)+'\n')
