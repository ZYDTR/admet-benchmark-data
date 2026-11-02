"""This task's narrow file-write restriction, applied before scientific imports."""
import ctypes, os, resource, sys,json,datetime
from pathlib import Path
R=Path('task-storage://admet/scaler-six28-20261102')
assert R.resolve(strict=True)==R
os.chdir(R)
rawstat=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()
(R/'raw/cpu-check02-identity.json').write_text(json.dumps({'pid':os.getpid(),'ppid':os.getppid(),'start_ticks':int(rawstat[19]),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
os.nice(19)
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
resource.setrlimit(resource.RLIMIT_FSIZE,(450*1024**2,450*1024**2))
libc=ctypes.CDLL(None,use_errno=True)
class Ruleset(ctypes.Structure): _fields_=[('handled',ctypes.c_uint64)]
class PathBeneath(ctypes.Structure): _pack_=1;_fields_=[('allowed',ctypes.c_uint64),('parent',ctypes.c_int32)]
abi=libc.syscall(444,0,0,1)
assert abi>=4,('Landlock ABI',abi)
# Filesystem mutation classes through TRUNCATE. Reads remain available.
access=sum(1<<i for i in [1,4,5,6,7,8,9,10,11,12,13,14])
rs=Ruleset(access); fd=libc.syscall(444,ctypes.byref(rs),ctypes.sizeof(rs),0)
assert fd>=0,ctypes.get_errno()
def allow(path,mask):
 p=os.open(path,os.O_PATH|os.O_CLOEXEC);rule=PathBeneath(mask,p)
 try: assert libc.syscall(445,fd,1,ctypes.byref(rule),0)==0,ctypes.get_errno()
 finally:os.close(p)
allow(str(R),access)
for device in ['/dev/null','/dev/tty','/dev/urandom','/dev/random','/dev/nvidiactl','/dev/nvidia-uvm','/dev/nvidia-uvm-tools',*[f'/dev/nvidia{i}' for i in range(8)]]:
 if Path(device).exists():allow(device,1<<1)
assert libc.prctl(38,1,0,0,0)==0,ctypes.get_errno()
assert libc.syscall(446,fd,0)==0,ctypes.get_errno()
os.close(fd)
sys.path.insert(0,str(R/'src'))
sys.path.insert(0,str(R/'runtime'))
import verify_cpu02
