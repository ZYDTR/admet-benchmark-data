import hashlib,json,os,sys,tarfile
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
expected=json.loads('{"source/setup_remote02.py": {"sha256": "0b24441838c8052ea8c9218c756aad8360adf56ad4e7381cde3e5d2cd697c52e", "size": 4903}, "source/supervisor_setup02.py": {"sha256": "14f3f4e54da0d94613036538deedd8cbd9e05cb3991450c3a4ca421b225847af", "size": 5582}, "attempts/setup02/pip-25.3-py3-none-any.whl": {"sha256": "9655943313a94722b7774661c21049070f6bbb0a1516bf02f7c8d5d9201514cd", "size": 1778622}}')
(ROOT/'attempts').mkdir();(ROOT/'attempts/setup02').mkdir()
seen=[]
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz') as tar:
    for m in tar:
        assert m.name in expected and m.isfile() and m.name not in seen
        p=ROOT/m.name;assert p.resolve()==p and ROOT in p.parents
        assert m.size==expected[m.name]['size'] and m.size<3000000
        data=tar.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==expected[m.name]['sha256']
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
        with os.fdopen(fd,'wb') as f:f.write(data)
        seen.append(m.name)
assert set(seen)==set(expected)
print(json.dumps({'uploaded':expected}))
