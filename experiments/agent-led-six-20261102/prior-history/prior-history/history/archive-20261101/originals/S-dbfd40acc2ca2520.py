"""Task-specific sequential phase supervisor; yields only its own child on conflict."""
import csv,io,json,os,signal,subprocess,sys,time,resource,traceback,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common_guarded import ROOT,GPU_UUID,now,safe,environment,write_json
from common_remote import VENV
phase=sys.argv[1];assert phase in ['cuda01','train01'];safe(ROOT,True);os.chdir(ROOT)
os.environ.clear();os.environ.update(environment())
affinity=sorted(os.sched_getaffinity(0))[:2];os.sched_setaffinity(0,affinity)
resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(450*1024**2,450*1024**2))
with (ROOT/'state'/f'{phase}.started').open('x') as f:f.write(now())
write_json(ROOT/'raw'/f'{phase}-supervisor.json',{'pid':os.getpid(),'pgid':os.getpgid(0),'start_stat':Path('/proc/self/stat').read_text(),'started_at':now(),'cpu_affinity':affinity,'environment':environment()})
def query(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=10);assert p.returncode==0,p.stderr;return p.stdout
def health():
 xml=query(['nvidia-smi','-i',GPU_UUID,'-q','-x']);g=ET.fromstring(xml).find('gpu')
 assert g.findtext('uuid')==GPU_UUID and g.findtext('minor_number')=='3'
 assert g.findtext('gpu_recovery_action')=='None','GPU not healthy'
 assert g.findtext('compute_mode')=='Default' and g.findtext('mig_mode/current_mig')=='Disabled'
 assert g.findtext('remapped_rows/remapped_row_pending')=='No' and g.findtext('remapped_rows/remapped_row_failure')=='No'
 for v in g.findall('ecc_errors/volatile/*'):
  if 'uncorrectable' in v.tag:assert v.text=='0','uncorrectable ECC'
 return xml,g
started=time.monotonic();p=None;reason=None;ids=[];peak_rss=0;rc=1
try:
 if phase=='train01':assert (ROOT/'raw/cuda01-complete.json').exists()
 obs=[]
 for i in range(3):
  xml,g=health();apps=query(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'])
  obs.append({'at':now(),'health_xml':xml,'apps':apps,'loadavg':os.getloadavg()});write_json(ROOT/'raw'/f'{phase}-prelaunch.json',obs)
  assert g.findtext('fb_memory_usage/used')=='0 MiB' and g.findtext('utilization/gpu_util')=='0 %','GPU no longer idle'
  assert not any(r[0].strip()==GPU_UUID for r in csv.reader(io.StringIO(apps)))
  if i<2:time.sleep(2)
 args=['/usr/bin/strace','-f','-qq','-yy','-s','160','-e','trace=%file,write,writev,pwrite64,ftruncate,mmap,msync,close,dup,dup2,dup3,fchdir,fchmod,fchown,fsetxattr,fremovexattr,fallocate,copy_file_range,sendfile,landlock_create_ruleset,landlock_add_rule,landlock_restrict_self,prctl','-o',str(ROOT/'raw'/f'{phase}.strace'),str(VENV/'bin/python3'),'-I','-B','-u',str(ROOT/'source/guard_exec_v3.py'),phase]
 env=environment();env['LD_PRELOAD']=str(ROOT/'artifacts/avoid_thread_name.so')
 with (ROOT/'raw'/f'{phase}.log').open('xb') as log:
  p=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT,env=env,start_new_session=True)
  write_json(ROOT/'raw'/f'{phase}-launch.json',{'at':now(),'pid':p.pid,'pgid':p.pid,'start_stat':Path(f'/proc/{p.pid}/stat').read_text(),'command':args,'timeout_seconds':900})
  def descendants(pid):
   found=[pid]
   for current in found:
    try:children=Path(f'/proc/{current}/task/{current}/children').read_text().split()
    except OSError:continue
    found.extend(int(x) for x in children if int(x) not in found)
   return found
  while p.poll() is None:
   ids=descendants(p.pid);rss=0;procs=[]
   for pid in ids:
    try:
     sm=dict(x.split(':',1) for x in Path(f'/proc/{pid}/status').read_text().splitlines());rss+=int(sm.get('VmRSS','0 kB').split()[0])*1024
     procs.append({'pid':pid,'rss_kib':sm.get('VmRSS'),'threads':sm.get('Threads'),'start_stat':Path(f'/proc/{pid}/stat').read_text()})
    except OSError:pass
   peak_rss=max(peak_rss,rss)
   ob={'at':now(),'elapsed_seconds':time.monotonic()-started,'rss_bytes':rss,'processes':procs,'loadavg':os.getloadavg()}
   ob['apps']=query(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'])
   ob['gpu']=query(['nvidia-smi','-i',GPU_UUID,'--query-gpu=uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
   if any(r[0].strip()==GPU_UUID and int(r[1]) not in ids for r in csv.reader(io.StringIO(ob['apps']))):reason='Other process appeared; yield own job'
   if rss>8*1024**3:reason='RAM budget exceeded'
   if time.monotonic()-started>900:reason='Wall timeout'
   if sum(f.stat().st_size for d in ['raw','artifacts'] for f in (ROOT/d).rglob('*') if f.is_file())>1024**3:reason='Result budget exceeded'
   with (ROOT/'raw'/f'{phase}-observations.jsonl').open('a') as f:f.write(json.dumps(ob)+'\n')
   if reason:break
   time.sleep(1)
except Exception as e:
 reason=type(e).__name__+': '+str(e);traceback.print_exc()
finally:
 if p is not None:
  if p.poll() is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=5)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  rc=p.wait()
 if reason:rc=1
 write_json(ROOT/'raw'/f'{phase}-exit.json',{'at':now(),'exit_code':rc,'reason':reason,'elapsed_seconds':time.monotonic()-started,'peak_observed_tree_rss_bytes':peak_rss,'pids_last_observed':ids,'cpu_affinity':affinity})
print(json.dumps({'phase':phase,'exit_code':rc,'reason':reason}),flush=True)
