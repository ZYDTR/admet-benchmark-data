import hashlib,json,os,sys,tarfile
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
assert ROOT.resolve(strict=True)==ROOT
expected=json.loads('{"source/common_guarded.py": {"sha256": "d4c5bbba379b194eb9744de8e45af95625f75e0122b07cfeb952b034de17d241", "size": 379}, "source/guard_exec.py": {"sha256": "72503f354953a3b959bfe9eb0020ab851caab1c96f6c4d3b569eecdb61fba276", "size": 3438}, "source/train_remote_v3.py": {"sha256": "1dd9ba6a6da7828849bdc208341cc9618ed71a704dc1db531efa3758179e471d", "size": 12623}, "source/supervisor_train_guarded.py": {"sha256": "139691979e02c05a85d4f3370461c9f0715a6a1f394c6262703929d1a3b3c92f", "size": 5556}}')
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
