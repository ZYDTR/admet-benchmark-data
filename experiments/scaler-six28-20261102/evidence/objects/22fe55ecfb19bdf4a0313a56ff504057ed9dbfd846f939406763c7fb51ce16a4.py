import hashlib,io,json,zipfile
from pathlib import Path
import hainan
P=Path(__file__).resolve().parent
SOURCE="\nimport hashlib,io,json,os,sys,zipfile\nfrom pathlib import Path\nos.nice(19);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])\nR=Path('task-storage://admet/scaler-six28-20261102')\nassert os.getuid()==1012 and R.resolve(strict=True)==R\nassert json.loads((R/'raw/cpu-check02-exit.json').read_text())['actual_strace_wait_exit']==0\nassert json.loads((R/'raw/independent-CPU-verification.json').read_text())['verified_runs']==28\nfiles=[]\nfor name in ['raw','runtime','src','support']:\n files.extend(f for f in (R/name).rglob('*') if f.is_file())\nfiles.extend(R/n for n in ['deployment-manifest.json','deployment-manifest-staged01.json','input/INPUT_MANIFEST.json','input/TASK.json','input/task-metrics.json'])\nentries={};buf=io.BytesIO()\nwith zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:\n for f in sorted(files):\n  assert not f.is_symlink() and f.stat().st_nlink==1\n  data=f.read_bytes();name=str(f.relative_to(R));entries[name]={'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'downloaded':True,'remote_path':str(f)};z.writestr(name,data)\n cache=Path('task-storage://admet/breadth-six24-20261102/cache/chemeleon_mp')\n for f in sorted(cache.glob('*/*')):\n  if not f.is_file():continue\n  assert not f.is_symlink()\n  data=f.read_bytes();name='original-cache/'+str(f.relative_to(cache));downloaded=f.name.endswith('.meta.json');entries[name]={'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'downloaded':downloaded,'remote_path':str(f)}\n  if downloaded:z.writestr(name,data)\n z.writestr('_fetch-manifest.json',json.dumps(entries,indent=2)+'\\n')\nsys.stdout.buffer.write(buf.getvalue())\n"
data=hainan.read(SOURCE,'fetch-global01',timeout=240)
(P/'global-evidence.zip').write_bytes(data)
z=zipfile.ZipFile(io.BytesIO(data));m=json.loads(z.read('_fetch-manifest.json'))
assert set(z.namelist())=={n for n,e in m.items() if e['downloaded']}|{'_fetch-manifest.json'}
root=P/'global-evidence';root.mkdir(exist_ok=False)
for name in z.namelist():
 rel=Path(name);assert not rel.is_absolute() and '..' not in rel.parts
 content=z.read(name)
 if name!='_fetch-manifest.json':assert len(content)==m[name]['size'] and hashlib.sha256(content).hexdigest()==m[name]['sha256']
 f=root/rel;f.parent.mkdir(exist_ok=True,parents=True)
 with f.open('xb') as out:out.write(content)
print(json.dumps({'downloaded':len(z.namelist())-1,'remote_reference_only':sum(not e['downloaded'] for e in m.values()),'archive_bytes':len(data),'archive_sha256':hashlib.sha256(data).hexdigest()}))
