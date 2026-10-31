"""Unprivileged Landlock ABI>=3 write restriction for this child and future descendants.
Allow task tree file writes and existing NVIDIA/null character devices. Reads remain available.
ABI4 does not cover chmod/chown/xattr/utime or device ioctls; reviewed code plus trace still required.
Source: Linux userspace-api/landlock and actual target kernel UAPI header, recorded in raw/guard-support.stdout.
"""
import ctypes,json,os,runpy,stat,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common_guarded import ROOT,environment,now,safe,write_json
phase=sys.argv[1];assert phase in ['cuda01','train01']
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
if phase=='cuda01':
    import torch,chemprop,rdkit,numpy,joblib._multiprocessing_helpers as helper
    assert helper.mp is None
    assert torch.cuda.is_available() and torch.cuda.device_count()==1
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.cuda.set_device(0);props=torch.cuda.get_device_properties(0)
    torch.cuda.set_per_process_memory_fraction(4096*1024**2/props.total_memory,0)
    a=torch.ones((64,64),device='cuda:0');b=a@a;torch.cuda.synchronize()
    assert b.device.type=='cuda' and bool(torch.all(b==64))
    write_json(ROOT/'raw/cuda01-complete.json',{'at':now(),'status':'success','pid':os.getpid(),'gpu_uuid':os.environ['CUDA_VISIBLE_DEVICES'],'actual_cuda_matmul':True,'torch':torch.__version__,'chemprop':chemprop.__version__,'rdkit':rdkit.__version__,'numpy':numpy.__version__,'joblib_mp':None,'allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved()})
    print('CUDA preflight success',flush=True)
else:runpy.run_path(str(ROOT/'source/train_remote_v3.py'),run_name='__main__')
