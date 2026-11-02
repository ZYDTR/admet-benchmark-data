
import io,json,zipfile,hashlib,os,socket,stat,sys,datetime
from pathlib import Path
M=Path('task-storage:/');R=M/'admet/scaler-six28-20261102'
assert socket.gethostname().split('.')[0]=='h100' and os.getuid()==os.getgid()==1012
for p in [M,M/'admet']:
 assert p.resolve(strict=True)==p and p.stat().st_uid==1012 and p.stat().st_dev==M.stat().st_dev
assert not R.exists(),'Existing remote task must be reconciled before mutation'
archive=sys.stdin.buffer.read();z=zipfile.ZipFile(io.BytesIO(archive));names=z.namelist()
assert len(names)==len(set(names))
for e in z.infolist():
 p=Path(e.filename);mode=e.external_attr>>16
 assert not p.is_absolute() and '..' not in p.parts and stat.S_IFMT(mode) in (0,stat.S_IFREG)
manifest=json.loads(z.read('deployment-manifest.json'))
assert set(names)==set(manifest)|{'deployment-manifest.json'}
for name,e in manifest.items():
 data=z.read(name);assert len(data)==e['size'] and hashlib.sha256(data).hexdigest()==e['sha256'],name
R.mkdir(mode=0o700)
for name in names:
 p=R/name;p.parent.mkdir(parents=True,exist_ok=True)
 assert p.parent.resolve(strict=True).is_relative_to(R)
 with p.open('xb') as f:f.write(z.read(name))
for name,e in manifest.items():
 p=R/name;assert p.stat().st_nlink==1 and hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256']
for name in ['raw','private/tmp','private/cache','private/torch','private/mpl','private/inductor','private/triton']:(R/name).mkdir(parents=True,exist_ok=True)
print(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root':str(R),'root_realpath':str(R.resolve()),'uid':os.getuid(),'files':len(names),'archive_sha256':hashlib.sha256(archive).hexdigest(),'files_sha_verified':len(manifest),'no_links_or_special_members':True,'outside_requested_writes':[]}))
