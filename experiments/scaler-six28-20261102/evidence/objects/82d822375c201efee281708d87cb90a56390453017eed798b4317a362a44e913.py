"""One actual 28-fit command, with narrow resource sampling and own-PID controls."""
import datetime,hashlib,json,os,socket,stat,subprocess,time,signal,xml.etree.ElementTree as ET
from pathlib import Path
R=Path('task-storage://admet/scaler-six28-20261102');M=R.parents[1]
assert socket.gethostname().split('.')[0]=='h100' and os.getuid()==os.getgid()==1012
assert R.resolve(strict=True)==R and R.stat().st_dev==M.stat().st_dev
for f in R.rglob('*'):
 assert not f.is_symlink() and (not f.is_file() or f.stat().st_nlink==1)
manifest=json.loads((R/'deployment-manifest.json').read_text())
for name,e in manifest.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==e['sha256'],name
def at():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name,obj):(R/'raw'/name).write_text(json.dumps(obj,indent=2)+'\n')
def query(uuid):
 began=time.time()
 try:
  cp=subprocess.run(['nvidia-smi','-i',uuid,'-q','-x'],capture_output=True,text=True,timeout=5)
  q={'at':at(),'started_epoch':began,'exit':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr}
  if cp.returncode:return q,None
  tree=ET.fromstring(cp.stdout);g=tree.find('gpu');assert g.findtext('uuid')==uuid
  health={p:g.findtext(p) for p in ['gpu_recovery_action','compute_mode','ecc_errors/volatile/sram_uncorrectable_parity','ecc_errors/volatile/sram_uncorrectable_secded','ecc_errors/volatile/dram_uncorrectable','remapped_rows/remapped_row_pending','remapped_rows/remapped_row_failure']}
  healthy=health=={'gpu_recovery_action':'None','compute_mode':'Default','ecc_errors/volatile/sram_uncorrectable_parity':'0','ecc_errors/volatile/sram_uncorrectable_secded':'0','ecc_errors/volatile/dram_uncorrectable':'0','remapped_rows/remapped_row_pending':'No','remapped_rows/remapped_row_failure':'No'}
  value={'uuid':uuid,'health':health,'healthy':healthy,'used_mib':int(g.findtext('fb_memory_usage/used').split()[0]),'free_mib':int(g.findtext('fb_memory_usage/free').split()[0]),'util_percent':int(g.findtext('utilization/gpu_util').split()[0]),'pids':[int(x.findtext('pid')) for x in g.findall('processes/process_info')],'index':int(g.findtext('minor_number'))}
  q['parsed']=value;return q,value
 except BaseException as error:
  q={'at':at(),'started_epoch':began,'exit':None,'error_type':type(error).__name__,'error':str(error)}
  if isinstance(error,subprocess.TimeoutExpired):q.update(stdout=(error.stdout or b'').decode(),stderr=(error.stderr or b'').decode())
  return q,None
chosen=None;pre=[]
for uuid in ['GPU-b9fbba0f-b366-d145-720a-37b369c234a0','GPU-908d18d1-2508-abe3-3fec-b3906dbab791']:
 q,v=query(uuid);pre.append(q)
 if v and v['healthy'] and not v['pids'] and v['used_mib']<64 and v['util_percent']==0:chosen=v;break
write('prelaunch01.json',{'at':at(),'queries':pre,'selected':chosen})
assert chosen is not None,'No currently qualified idle candidate; no CUDA worker launched'
with (R/'raw/launch01.lock').open('x') as f:f.write(at())
def tick():return {x.split()[0]:list(map(int,x.split()[1:9])) for x in Path('/proc/stat').read_text().splitlines() if x.startswith('cpu') and x.split()[0]!='cpu'}
a=tick();time.sleep(.3);b=tick();allowed=os.sched_getaffinity(0)
busy={int(k[3:]):1-(v[3]+v[4]-a[k][3]-a[k][4])/(sum(v)-sum(a[k])) if sum(v)!=sum(a[k]) else 0 for k,v in b.items() if int(k[3:]) in allowed}
cpus=sorted(busy,key=busy.get)[:2]
env=dict(os.environ)
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',JOBLIB_MULTIPROCESSING='0',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2',CUDA_VISIBLE_DEVICES=chosen['uuid'],CUBLAS_WORKSPACE_CONFIG=':4096:8',CUDA_MODULE_LOADING='LAZY',TMPDIR=str(R/'private/tmp'),TMP=str(R/'private/tmp'),TEMP=str(R/'private/tmp'),XDG_CACHE_HOME=str(R/'private/cache'),TORCH_HOME=str(R/'private/torch'),MPLCONFIGDIR=str(R/'private/mpl'),TORCHINDUCTOR_CACHE_DIR=str(R/'private/inductor'),TRITON_CACHE_DIR=str(R/'private/triton'),HF_HOME=str(R/'private/cache/hf'),HF_HUB_OFFLINE='1',WANDB_MODE='disabled',LD_PRELOAD=str(R/'support/thread-names-v2.so'))
cmd=['strace','-f','-qq','-ttt','-s','1024','-yy','-e','trace=%file,write,writev,pwrite64,ftruncate,mmap,msync','-o',str(R/'raw/write01.strace'),'task-storage://admet/hainan-skill-pilot-20261030/venv/bin/python','-I','-B',str(R/'runtime/guard.py')]
os.sched_setaffinity(0,cpus)
start_wall=time.time();start=time.monotonic()
with (R/'raw/worker01.stdout').open('x') as stdout,(R/'raw/worker01.stderr').open('x') as stderr:
 child=subprocess.Popen(cmd,cwd=R,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
 def ident(pid):
  try:
   v=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();return {'pid':pid,'state':v[0],'ppid':int(v[1]),'start_ticks':int(v[19])}
  except FileNotFoundError:return None
 parent_identity=ident(os.getpid());trace_identity=ident(child.pid)
 write('job-start01.json',{'at':at(),'start_epoch':start_wall,'parent_identity':parent_identity,'strace_identity':trace_identity,'argv':cmd,'environment_overrides':{k:env[k] for k in ['CUDA_VISIBLE_DEVICES','CUBLAS_WORKSPACE_CONFIG','LD_PRELOAD','TMPDIR','XDG_CACHE_HOME','JOBLIB_MULTIPROCESSING']},'CPU_affinity':cpus,'GPU':chosen,'GPU_job_budget_seconds':7200})
 peak_device=0;peak_rss=0;unknown_count=0;stop_reason=None;last_health=time.monotonic();rounds=0
 while child.poll() is None:
  wi=json.loads((R/'raw/worker-identity.json').read_text()) if (R/'raw/worker-identity.json').exists() else None
  current=ident(wi['pid']) if wi else None
  rss=None
  if current and current['start_ticks']==wi['start_ticks']:
   status=Path(f"/proc/{wi['pid']}/status").read_text().splitlines();rss={x.split(':')[0]:int(x.split()[1])*1024 for x in status if x.startswith(('VmRSS:','VmHWM:'))};peak_rss=max(peak_rss,rss.get('VmHWM',0))
  q,v=query(chosen['uuid']);rounds+=1
  if v:
   last_health=time.monotonic();peak_device=max(peak_device,v['used_mib'])
   foreign=set(v['pids'])-{child.pid,wi['pid'] if wi else -1}
   if foreign:stop_reason='New foreign selected-card PID; shared suitability not established'
   if not v['healthy']:stop_reason='Selected GPU health became nonqualified'
   if v['used_mib']>4096:stop_reason='Selected-card memory exceeded this task target'
  else:unknown_count+=1
  if rss and rss.get('VmRSS',0)>8*1024**3:stop_reason='Own worker RSS exceeded8GiB target'
  if time.monotonic()-start>7190:stop_reason='Approaching7200GPU-job-second budget'
  # One query failure preserves an unknown sample. Own process and checkpoint
  # progress remain observable; Agent can inspect while bounded sampling retries.
  if time.monotonic()-last_health>30:stop_reason='Selected-card health unavailable for30s; own work paused for Agent review'
  item={'at':at(),'query':q,'worker_identity':current,'own_memory':rss,'peak_device_mib':peak_device,'peak_RSS_bytes':peak_rss,'science_complete_file':(R/'raw/study-complete.json').exists(),'stop_reason':stop_reason}
  with (R/'raw/resource01.jsonl').open('a') as f:f.write(json.dumps(item)+'\n')
  if stop_reason and child.poll() is None:
   # Only recorded lifetimes are controlled; never shared UID or device-wide.
   if wi and current and current['start_ticks']==wi['start_ticks']:
    pfd=os.pidfd_open(wi['pid']);signal.pidfd_send_signal(pfd,signal.SIGSTOP if 'paused' in stop_reason else signal.SIGTERM);os.close(pfd)
   if 'paused' in stop_reason:
    write('observation-attention.json',item)
    # Return control with the original job explicitly paused, never relaunch.
    print(json.dumps({'state':'paused_for_observation','worker':wi,'strace':trace_identity}),flush=True)
    raise SystemExit(71)
   try:child.wait(timeout=10)
   except subprocess.TimeoutExpired:
    if wi and ident(wi['pid']) and ident(wi['pid'])['start_ticks']==wi['start_ticks']:
     pfd=os.pidfd_open(wi['pid']);signal.pidfd_send_signal(pfd,signal.SIGKILL);os.close(pfd)
    child.wait(timeout=10)
   break
  if child.poll() is not None:break
  time.sleep(2)
 result={'at':at(),'actual_strace_wait_exit':child.wait(),'elapsed_gpu_job_seconds':time.monotonic()-start,'started_epoch':start_wall,'finished_epoch':time.time(),'resource_rounds':rounds,'unknown_query_samples':unknown_count,'peak_device_MiB':peak_device,'peak_sampled_RSS_bytes':peak_rss,'stop_reason':stop_reason,'science_complete_file':(R/'raw/study-complete.json').exists(),'parent_identity':parent_identity,'strace_identity':trace_identity,'worker_identity':json.loads((R/'raw/worker-identity.json').read_text()) if (R/'raw/worker-identity.json').exists() else None}
 write('job-exit01.json',result);print(json.dumps(result),flush=True)
