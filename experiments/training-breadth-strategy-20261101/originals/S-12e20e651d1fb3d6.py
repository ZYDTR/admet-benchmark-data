import hashlib,json,os,sys,tarfile
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
assert ROOT.resolve(strict=True)==ROOT
expected=json.loads('{"source/setup_remote03.py": {"sha256": "fac00f569c7ee84c91470360869daf3106d02277829d7c2af6ca8b58279a9f09", "size": 3321}, "source/supervisor_setup03.py": {"sha256": "666f30d2706a2db9643ed1dc80ac4d592aaeb3e3a052c182e8d03c1ffa5d854a", "size": 5717}}')
dirs=json.loads('["attempts/setup03", "attempts/setup03/wheels"]')
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
