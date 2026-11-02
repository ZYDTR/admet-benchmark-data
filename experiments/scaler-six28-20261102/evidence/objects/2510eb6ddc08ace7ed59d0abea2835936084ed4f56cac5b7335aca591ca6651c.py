
import hashlib,io,json,os,sys,zipfile
from pathlib import Path
os.nice(19);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
R=Path('task-storage://admet/scaler-six28-20261102')
assert os.getuid()==1012 and R.resolve(strict=True)==R
assert json.loads((R/'raw/cpu-check02-exit.json').read_text())['actual_strace_wait_exit']==0
assert json.loads((R/'raw/independent-CPU-verification.json').read_text())['verified_runs']==28
files=[]
for name in ['raw','runtime','src','support']:
 files.extend(f for f in (R/name).rglob('*') if f.is_file())
files.extend(R/n for n in ['deployment-manifest.json','deployment-manifest-staged01.json','input/INPUT_MANIFEST.json','input/TASK.json','input/task-metrics.json'])
entries={};buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in sorted(files):
  assert not f.is_symlink() and f.stat().st_nlink==1
  data=f.read_bytes();name=str(f.relative_to(R));entries[name]={'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'downloaded':True,'remote_path':str(f)};z.writestr(name,data)
 cache=Path('task-storage://admet/breadth-six24-20261102/cache/chemeleon_mp')
 for f in sorted(cache.glob('*/*')):
  if not f.is_file():continue
  assert not f.is_symlink()
  data=f.read_bytes();name='original-cache/'+str(f.relative_to(cache));downloaded=f.name.endswith('.meta.json');entries[name]={'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'downloaded':downloaded,'remote_path':str(f)}
  if downloaded:z.writestr(name,data)
 z.writestr('_fetch-manifest.json',json.dumps(entries,indent=2)+'\n')
sys.stdout.buffer.write(buf.getvalue())
