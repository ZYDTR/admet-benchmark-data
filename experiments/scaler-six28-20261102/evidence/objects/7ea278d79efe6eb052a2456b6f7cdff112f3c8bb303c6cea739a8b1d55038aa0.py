"""Read a completed run once; verify every downloaded byte before extraction."""
import hashlib,io,json,sys,zipfile
from pathlib import Path
import hainan
P=Path(__file__).resolve().parent;TASK=json.loads((P.parent/'TASK.json').read_text())
i=int(sys.argv[1]);run_id=TASK['runs'][i]['run_id']
source="\nimport hashlib,io,json,os,stat,sys,zipfile\nfrom pathlib import Path\nos.nice(19)\nos.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])\nR=Path('task-storage://admet/scaler-six28-20261102');run=R/__RUN_ID__\nassert os.getuid()==1012 and run.resolve(strict=True)==run\nassert (run/'raw/train-complete.json').is_file()\nentries={};data=io.BytesIO()\nwith zipfile.ZipFile(data,'w',compression=zipfile.ZIP_DEFLATED) as z:\n for f in sorted(run.rglob('*')):\n  assert not f.is_symlink()\n  if not f.is_file():continue\n  assert f.stat().st_nlink==1\n  name=str(f.relative_to(run));content=f.read_bytes()\n  downloaded=name!='artifacts/progress.pt' and not name.endswith('.tmp')\n  entries[name]={'sha256':hashlib.sha256(content).hexdigest(),'size':len(content),'downloaded':downloaded,'remote_path':str(f)}\n  if downloaded:z.writestr(name,content)\n z.writestr('_fetch-manifest.json',json.dumps(entries,indent=2)+'\\n')\nsys.stdout.buffer.write(data.getvalue())\n".replace('__RUN_ID__',repr(run_id))
payload=hainan.read(source,f'fetch-{i:02}',timeout=240)
archive=P/'archives'/f'{run_id}.zip';archive.parent.mkdir(exist_ok=True)
with archive.open('xb') as f:f.write(payload)
z=zipfile.ZipFile(io.BytesIO(payload));manifest=json.loads(z.read('_fetch-manifest.json'))
assert set(z.namelist())=={n for n,e in manifest.items() if e['downloaded']}|{'_fetch-manifest.json'}
target=P/'snapshots'/run_id;target.mkdir(parents=True,exist_ok=False)
for name in z.namelist():
 path=Path(name);assert not path.is_absolute() and '..' not in path.parts
 content=z.read(name)
 if name!='_fetch-manifest.json':assert len(content)==manifest[name]['size'] and hashlib.sha256(content).hexdigest()==manifest[name]['sha256']
 dest=target/path;dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(content)
print(json.dumps({'index':i,'run_id':run_id,'downloaded_files':len(z.namelist())-1,'archive_bytes':len(payload),'archive_sha256':hashlib.sha256(payload).hexdigest()}))
