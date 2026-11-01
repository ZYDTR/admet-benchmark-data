import ctypes,json,os,socket,subprocess
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030');assert ROOT.resolve(strict=True)==ROOT and socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
p=ROOT/'venv/lib/python3.12/site-packages/joblib/_multiprocessing_helpers.py'
libc=ctypes.CDLL(None,use_errno=True);abi=libc.syscall(444,0,0,1)
r={'landlock_abi':abi,'errno':ctypes.get_errno(),'kernel':os.uname().release,'machine':os.uname().machine,'joblib_source_path':str(p),'joblib_source':p.read_text()}
h=Path('/usr/include/linux/landlock.h')
if h.exists():r['landlock_header']=h.read_text()
print(json.dumps(r))
