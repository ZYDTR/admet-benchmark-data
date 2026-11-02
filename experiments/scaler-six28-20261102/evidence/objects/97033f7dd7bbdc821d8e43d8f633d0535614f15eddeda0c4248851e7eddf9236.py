
import hashlib,io,json,os,stat,sys,zipfile
from pathlib import Path
os.nice(19)
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
R=Path('task-storage://admet/scaler-six28-20261102');run=R/'hainan-scaler-ld50_zhu-h0-s46-20261102'
assert os.getuid()==1012 and run.resolve(strict=True)==run
assert (run/'raw/train-complete.json').is_file()
entries={};data=io.BytesIO()
with zipfile.ZipFile(data,'w',compression=zipfile.ZIP_DEFLATED) as z:
 for f in sorted(run.rglob('*')):
  assert not f.is_symlink()
  if not f.is_file():continue
  assert f.stat().st_nlink==1
  name=str(f.relative_to(run));content=f.read_bytes()
  downloaded=name!='artifacts/progress.pt' and not name.endswith('.tmp')
  entries[name]={'sha256':hashlib.sha256(content).hexdigest(),'size':len(content),'downloaded':downloaded,'remote_path':str(f)}
  if downloaded:z.writestr(name,content)
 z.writestr('_fetch-manifest.json',json.dumps(entries,indent=2)+'\n')
sys.stdout.buffer.write(data.getvalue())
