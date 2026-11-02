import json,os,sys,socket,hashlib,subprocess,time,datetime
from pathlib import Path
R=Path('task-storage://admet/scaler-six28-20261102')
assert socket.gethostname().split('.')[0]=='h100' and os.getuid()==1012 and R.resolve(strict=True)==R
expected={'cpu_guard02.py': '4058721c577cc412b73fb02a9403f91c9f9cc7007d6357a61037c90d745779c2', 'verify_cpu02.py': 'a08cd9bd6929717c87cd11ffebe0dad768b4ffd943670887947179df42bd4176'}
for name,digest in expected.items():assert hashlib.sha256((R/'runtime'/name).read_bytes()).hexdigest()==digest
for name in ['cpu-check02.stdout','cpu-check02.stderr','cpu-check02.strace','cpu-check02-exit.json','cpu-check02-identity.json']:assert not (R/'raw'/name).exists(),name
env=dict(os.environ);env.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',JOBLIB_MULTIPROCESSING='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',TMPDIR=str(R/'private/tmp'),XDG_CACHE_HOME=str(R/'private/cache'),TORCH_HOME=str(R/'private/torch'),MPLCONFIGDIR=str(R/'private/mpl'),TORCHINDUCTOR_CACHE_DIR=str(R/'private/inductor'),TRITON_CACHE_DIR=str(R/'private/triton'))
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
cmd=['strace','-f','-qq','-ttt','-s','1024','-yy','-e','trace=%file,write,writev,pwrite64,ftruncate,mmap,msync','-o',str(R/'raw/cpu-check02.strace'),'task-storage://admet/hainan-skill-pilot-20261030/venv/bin/python','-I','-B',str(R/'runtime/cpu_guard02.py')]
began=time.monotonic()
with (R/'raw/cpu-check02.stdout').open('x') as out,(R/'raw/cpu-check02.stderr').open('x') as err:
 child=subprocess.Popen(cmd,cwd=R,env=env,stdout=out,stderr=err);code=child.wait(timeout=240)
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_strace_wait_exit':code,'elapsed_CPU_program_seconds':time.monotonic()-began,'strace_pid':child.pid,'argv':cmd,'source_sha256':expected,'CUDA_visible_devices':'','parent_pid':os.getpid(),'CPU_affinity':list(os.sched_getaffinity(0))}
(R/'raw/cpu-check02-exit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));sys.exit(code)
