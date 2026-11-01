import hashlib,json,os,sys,tarfile
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
assert ROOT.resolve(strict=True)==ROOT
expected=json.loads('{"source/setup_remote05.py": {"sha256": "a44157e5f9a84c01642236fcb4f9c9aa02f6bb9a4508d853068b9dcc799c0010", "size": 5242}, "source/supervisor_setup05.py": {"sha256": "e19cc12412a287a519a438432a88e39fde37890663104b5a687f19f8cced441a", "size": 5717}, "source/wheels-linux.lock.json": {"sha256": "59dd6c64e5bd282b25529c3c719523c6d7593f83dc04040d00073be8fab6f3df", "size": 65208}, "source/requirements-linux.lock": {"sha256": "92ac086b9faa3d37ca07529c2d614f6a89c360553f774259b85e8a599357b95d", "size": 7568}, "source/train_remote_v2.py": {"sha256": "e9216bb29bf74857886af4aa886a83f421c5c96ea6544a349e0678fe534c837b", "size": 12622}, "source/supervisor_train.py": {"sha256": "633771565e05090dfb6b01d93fb99b8222d1d86d0cab2b4be2b24efa089396b3", "size": 5481}}')
dirs=json.loads('["attempts/setup05", "attempts/setup05/wheels"]')
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
