import json,os,socket,subprocess,sys
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
sys.path.insert(0,str(ROOT/'source'))
from common_guarded import safe,environment,now
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
safe(ROOT,True)

assert json.loads((ROOT/'raw/setup05-exit.json').read_text())['exit_code']==0
assert json.loads((ROOT/'raw/import-check-exit.json').read_text())['exit_code']==0
assert json.loads((ROOT/'raw/import-check-complete.json').read_text())['joblib_multiprocessing_disabled']
assert json.loads((ROOT/'raw/guard-import_check.json').read_text())['restrict_self_return_code']==0
expected=json.loads('{"source/common_remote.py": {"sha256": "cccfd63105767e5e62480c24f83ad362b5be3c2e47dc1185b2d4e65295b7d9db", "size": 2497}, "source/setup_remote.py": {"sha256": "6102b6f9e67fd0348571a3dd58faf43d0745473198b466cea607fe114a5af91f", "size": 4302}, "source/supervisor_remote.py": {"sha256": "f81d0d38b4c62c13b72d8ffcdb72973e65f5f8e73fd92d84b31a8c6791cc4e35", "size": 5457}, "source/requirements.in": {"sha256": "ffb06f600b21ae77543354bef2cafa0862bd578651877f996e752da97f9f47e7", "size": 188}, "input/train.csv": {"sha256": "3061c58d3601d081e5459a2de03dc1d189243c4b5683d1b7288577a29fed4d6f", "size": 53598}, "input/valid.csv": {"sha256": "41370e87d89a96a7481425dae1bf7c45184bd116b353e96719b2afcd0a8a5ca3", "size": 6982}, "input/test.csv": {"sha256": "d87dac944bedcefb216bce57ba5a8de93d3781172c66653b937e5065b9c2579c", "size": 16063}, "assets/chemeleon_mp.pt": {"sha256": "c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651", "size": 34859448}, "source/config.json": {"sha256": "a97b004d084aa944f51c206974eae5a9cbbc500985e08dd8e512ca061ac3a5b4", "size": 1371}, "source/train_remote.py": {"sha256": "7bfc5ac5a3232c839572485e1bd3c09af54d4bc800494df3d36975c00a28d7cf", "size": 12512}, "source/encoder.py": {"sha256": "3adfea2d761e416f4aedcd42d36587e1b6961fbf57efb76995cfd99890942712", "size": 5289}, "source/setup_remote05.py": {"sha256": "a44157e5f9a84c01642236fcb4f9c9aa02f6bb9a4508d853068b9dcc799c0010", "size": 5242}, "source/supervisor_setup05.py": {"sha256": "e19cc12412a287a519a438432a88e39fde37890663104b5a687f19f8cced441a", "size": 5717}, "source/wheels-linux.lock.json": {"sha256": "59dd6c64e5bd282b25529c3c719523c6d7593f83dc04040d00073be8fab6f3df", "size": 65208}, "source/requirements-linux.lock": {"sha256": "92ac086b9faa3d37ca07529c2d614f6a89c360553f774259b85e8a599357b95d", "size": 7568}, "source/train_remote_v2.py": {"sha256": "e9216bb29bf74857886af4aa886a83f421c5c96ea6544a349e0678fe534c837b", "size": 12622}, "source/supervisor_train.py": {"sha256": "633771565e05090dfb6b01d93fb99b8222d1d86d0cab2b4be2b24efa089396b3", "size": 5481}, "source/common_guarded.py": {"sha256": "d4c5bbba379b194eb9744de8e45af95625f75e0122b07cfeb952b034de17d241", "size": 379}, "source/guard_exec.py": {"sha256": "72503f354953a3b959bfe9eb0020ab851caab1c96f6c4d3b569eecdb61fba276", "size": 3438}, "source/train_remote_v3.py": {"sha256": "1dd9ba6a6da7828849bdc208341cc9618ed71a704dc1db531efa3758179e471d", "size": 12623}, "source/supervisor_train_guarded.py": {"sha256": "139691979e02c05a85d4f3370461c9f0715a6a1f394c6262703929d1a3b3c92f", "size": 5556}}')
import hashlib
for rel,meta in expected.items():
    p=safe(ROOT/rel,True)
    assert p.is_file() and p.stat().st_nlink==1 and p.stat().st_size==meta['size']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']

with safe(ROOT/'state/train.launch_requested').open('x') as f:f.write(now())
with safe(ROOT/'raw/train-supervisor.log').open('xb') as f:
    p=subprocess.Popen(['/usr/bin/python3','-I','-B','-u',str(ROOT/'source/supervisor_train_guarded.py'),'train'],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,env=environment(),start_new_session=True)
print(json.dumps({'phase':'train','supervisor_pid':p.pid,'launch_requested_at':now(),'start_stat':Path(f'/proc/{p.pid}/stat').read_text()}))
