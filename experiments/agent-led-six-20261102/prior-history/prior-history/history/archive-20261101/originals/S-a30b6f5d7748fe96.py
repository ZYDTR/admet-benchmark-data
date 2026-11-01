import hashlib,json,os,sys,tarfile
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
assert ROOT.resolve(strict=True)==ROOT
expected=json.loads('{"source/supervisor_setup04.py": {"sha256": "72a5bf28481e4ad91df18e57ca71ab96f3affdb7248a67646ff833a1df9ee5fa", "size": 5717}}')
dirs=json.loads('[]')
for d in dirs:
    p=ROOT/d;assert p.resolve()==p and ROOT in p.parents and not p.exists();p.mkdir()
seen=[]
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz') as tar:
    for m in tar:
        assert m.name in expected and m.isfile() and m.name not in seen
        p=ROOT/m.name;assert p.resolve()==p and ROOT in p.parents
        assert m.size==expected[m.name]['size'] and m.size<50000000
        data=tar.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==expected[m.name]['sha256']
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
        with os.fdopen(fd,'wb') as f:f.write(data)
        seen.append(m.name)
assert set(seen)==set(expected)
print(json.dumps({'uploaded':expected,'dirs_created':dirs}))
