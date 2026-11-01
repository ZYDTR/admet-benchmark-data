import hashlib,json,os,stat,sys,tarfile
from pathlib import Path
TASK=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
assert TASK.resolve(strict=True)==TASK
EXPECTED=json.loads('{"source/common_remote.py":{"sha256":"cccfd63105767e5e62480c24f83ad362b5be3c2e47dc1185b2d4e65295b7d9db","size":2497},"source/setup_remote.py":{"sha256":"6102b6f9e67fd0348571a3dd58faf43d0745473198b466cea607fe114a5af91f","size":4302},"source/supervisor_remote.py":{"sha256":"f81d0d38b4c62c13b72d8ffcdb72973e65f5f8e73fd92d84b31a8c6791cc4e35","size":5457},"source/requirements.in":{"sha256":"ffb06f600b21ae77543354bef2cafa0862bd578651877f996e752da97f9f47e7","size":188},"input/train.csv":{"sha256":"3061c58d3601d081e5459a2de03dc1d189243c4b5683d1b7288577a29fed4d6f","size":53598},"input/valid.csv":{"sha256":"41370e87d89a96a7481425dae1bf7c45184bd116b353e96719b2afcd0a8a5ca3","size":6982},"input/test.csv":{"sha256":"d87dac944bedcefb216bce57ba5a8de93d3781172c66653b937e5065b9c2579c","size":16063},"assets/chemeleon_mp.pt":{"sha256":"c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651","size":34859448},"source/config.json":{"sha256":"a97b004d084aa944f51c206974eae5a9cbbc500985e08dd8e512ca061ac3a5b4","size":1371}}')
for d in ['source','input','assets','home','tmp','cache','config','datahome','state','artifacts','wheels']:
    p=TASK/d;assert not p.exists();p.mkdir()
seen=[]
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz') as tar:
    for m in tar:
        assert m.name in EXPECTED and m.isfile() and m.name not in seen
        p=TASK/m.name;assert p.resolve()==p and TASK in p.parents
        assert m.size==EXPECTED[m.name]['size'] and m.size<=40*1024**2
        data=tar.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==EXPECTED[m.name]['sha256']
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
        with os.fdopen(fd,'wb') as f:f.write(data)
        seen.append(m.name)
assert set(seen)==set(EXPECTED)
print(json.dumps({'uploaded':EXPECTED,'directories_created':['source','input','assets','home','tmp','cache','config','datahome','state','artifacts','wheels']}))
