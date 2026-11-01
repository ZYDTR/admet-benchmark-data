"""Unprivileged Landlock ABI>=3 write restriction for this child and future descendants.
Allow task tree file writes and existing NVIDIA/null character devices. Reads remain available.
ABI4 does not cover chmod/chown/xattr/utime or device ioctls; reviewed code plus trace still required.
Source: Linux userspace-api/landlock and actual target kernel UAPI header, recorded in raw/guard-support.stdout.
"""
import ctypes,json,os,runpy,stat,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common_guarded import ROOT,environment,now,safe,write_json
phase=sys.argv[1];assert phase in ['import_check','compile03','train03']
safe(ROOT,True);os.chdir(ROOT);os.environ.clear();os.environ.update(environment())
assert len(list(Path('/proc/self/task').iterdir()))==1, 'Apply restriction before library-created threads'
libc=ctypes.CDLL(None,use_errno=True);libc.syscall.restype=ctypes.c_long

def check(rc,name):
    if rc<0:raise OSError(ctypes.get_errno(),name+': '+os.strerror(ctypes.get_errno()))
    return rc
abi=check(libc.syscall(444,0,0,1),'landlock ABI query');assert abi>=3 and os.uname().machine=='x86_64'
class Ruleset(ctypes.Structure):_fields_=[('handled_access_fs',ctypes.c_uint64)]
class Beneath(ctypes.Structure):
    _pack_=1
    _fields_=[('allowed_access',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
rights=sum(1<<i for i in [1,4,5,6,7,8,9,10,11,12,13,14]);attr=Ruleset(rights)
rs=check(libc.syscall(444,ctypes.byref(attr),ctypes.sizeof(attr),0),'create write ruleset')
rules=[]
def add(path,allowed):
    fd=os.open(path,os.O_PATH|os.O_CLOEXEC)
    try:
        rule=Beneath(allowed,fd);check(libc.syscall(445,rs,1,ctypes.byref(rule),0),'add path rule')
    finally:os.close(fd)
    rules.append({'path':str(path),'allowed_access':allowed})
add(ROOT,rights)
devs=[Path('/dev/null')]+[p for p in Path('/dev').iterdir() if p.name.startswith('nvidia') and stat.S_ISCHR(p.lstat().st_mode)]
caps=Path('/dev/nvidia-caps')
if caps.is_dir():devs.extend(p for p in caps.iterdir() if stat.S_ISCHR(p.lstat().st_mode))
for p in devs:
    assert stat.S_ISCHR(p.lstat().st_mode) and p.resolve()==p
    add(p,1<<1)
check(libc.prctl(38,1,0,0,0),'PR_SET_NO_NEW_PRIVS')
check(libc.syscall(446,rs,0),'restrict self');os.close(rs)
receipt={'at':now(),'phase':phase,'pid':os.getpid(),'abi':abi,'handled_access_fs':rights,'rules':rules,'no_new_privs':True,'restrict_self_return_code':0,'applied_before_threads':True,'joblib_multiprocessing':os.environ['JOBLIB_MULTIPROCESSING'],'limitations':['Filesystem write/create/unlink/rename/truncate restrictions only. No read isolation, device partitioning, chmod/chown/xattr/utime/ioctl restriction, system-wide audit or SSH daemon isolation.','No outside-directory denial probe was attempted. Kernel syscall success and complete execution trace are retained.']}
write_json(ROOT/'raw'/f'guard-{phase}.json',receipt)
if phase=='import_check':
    import torch,chemprop,rdkit,numpy
    import joblib._multiprocessing_helpers as helper
    assert helper.mp is None
    write_json(ROOT/'raw/import-check-complete.json',{'at':now(),'status':'success','joblib_multiprocessing_disabled':helper.mp is None,'torch':torch.__version__,'chemprop':chemprop.__version__,'numpy':numpy.__version__,'rdkit':rdkit.__version__})
    print(json.dumps({'phase':phase,'status':'success','joblib_mp':None}),flush=True)
elif phase=='compile03':
    import shutil,subprocess
    cc=shutil.which('cc');assert cc, 'Existing system C compiler required; no global installation'
    args=[cc,'-shared','-fPIC','-O2','-pthread',str(ROOT/'source/avoid_thread_name.c'),'-o',str(ROOT/'artifacts/avoid_thread_name.so')]
    subprocess.run(args,check=True,env=environment(),cwd=ROOT)
    write_json(ROOT/'raw/compile03-complete.json',{'at':now(),'status':'success','command':args})
else:runpy.run_path(str(ROOT/'source/train_remote_v3.py'),run_name='__main__')
