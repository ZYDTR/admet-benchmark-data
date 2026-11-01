"""One detached supervisor per phase, identity records, exact-child timeout and sampled RSS guard.
No unrelated process is signalled. syscalls for worker descendants recorded with existing strace.
"""
import csv,io,json,os,signal,subprocess,sys,time,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common_remote import ROOT,GPU_UUID,now,safe,environment,write_json
phase=sys.argv[1];assert phase in ['train'];safe(ROOT,True);os.chdir(ROOT)
os.environ.clear();os.environ.update(environment())
affinity=sorted(os.sched_getaffinity(0))[:2];os.sched_setaffinity(0,affinity)
resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_FSIZE,(450*1024**2,450*1024**2))
base=ROOT/'raw'/phase
lock=ROOT/'state'/f'{phase}.started'
with lock.open('x') as f:f.write(now())
write_json(ROOT/'raw'/f'{phase}-supervisor.json',{'pid':os.getpid(),'pgid':os.getpgid(0),'start_stat':Path('/proc/self/stat').read_text(),'started_at':now(),'cpu_affinity':affinity,'environment':environment()})
if phase=='train':
    assert (ROOT/'raw/setup-complete.json').exists()
    obs=[]
    for i in range(2):
        gp=subprocess.run(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True)
        apps=subprocess.run(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True)
        rows=list(csv.reader(io.StringIO(gp.stdout)));sel=next(r for r in rows if r[1].strip()==GPU_UUID)
        obs.append({'at':now(),'gpu':gp.stdout,'apps':apps.stdout,'loadavg':os.getloadavg()})
        assert sel[0].strip()=='4' and int(sel[2])==0 and int(sel[3])==0,'Selected GPU no longer idle'
        assert not any(r[0].strip()==GPU_UUID for r in csv.reader(io.StringIO(apps.stdout)))
        if i==0:time.sleep(2)
    write_json(ROOT/'raw/prelaunch.json',obs)
script=ROOT/'source'/'train_remote_v2.py'
py='/usr/bin/python3' if phase=='setup' else str(ROOT/'venv/bin/python3')
args=['/usr/bin/strace','-f','-qq','-yy','-s','160','-e','trace=%file,write,writev,pwrite64,ftruncate,mmap,msync,close,dup,dup2,dup3,fchdir,fchmod,fchown,fsetxattr,fremovexattr,fallocate,copy_file_range,sendfile','-o',str(base)+'.strace',py,'-I','-B','-u',str(script)]
with (ROOT/'raw'/f'{phase}.log').open('xb') as log:
    p=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,cwd=ROOT,env=environment(),start_new_session=True)
    started=time.monotonic();observations=[];reason=None;peak_rss=0
    write_json(ROOT/'raw'/f'{phase}-launch.json',{'started_at':now(),'supervisor_pid':os.getpid(),'pid':p.pid,'pgid':p.pid,'start_stat':Path(f'/proc/{p.pid}/stat').read_text(),'command':args,'timeout_seconds':2700 if phase=='setup' else 900})
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
                st=Path(f'/proc/{pid}/status').read_text().splitlines();sm={x.split(':',1)[0]:x.split(':',1)[1].strip() for x in st}
                rss+=int(sm.get('VmRSS','0 kB').split()[0])*1024
                procs.append({'pid':pid,'name':sm.get('Name'),'rss_kib':sm.get('VmRSS'),'threads':sm.get('Threads'),'start_stat':Path(f'/proc/{pid}/stat').read_text()})
            except OSError:pass
        peak_rss=max(peak_rss,rss)
        ob={'at':now(),'elapsed_seconds':round(time.monotonic()-started,2),'rss_bytes':rss,'processes':procs,'loadavg':os.getloadavg()}
        if phase=='train':
            for key,cmd in [('gpu',['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits']),('apps',['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'])]:
                v=subprocess.run(cmd,capture_output=True,text=True,timeout=8);ob[key]={'exit_code':v.returncode,'stdout':v.stdout,'stderr':v.stderr}
            if ob['apps']['exit_code']!=0:reason='GPU query failed'
            else:
                other=[r for r in csv.reader(io.StringIO(ob['apps']['stdout'])) if r and r[0].strip()==GPU_UUID and int(r[1]) not in ids]
                if other:reason='Other process appeared on selected GPU; yield own job'
        with (ROOT/'raw'/f'{phase}-observations.jsonl').open('a') as f:f.write(json.dumps(ob)+'\n')
        if rss>8*1024**3:reason='Sampled RAM budget exceeded'
        if time.monotonic()-started>(2700 if phase=='setup' else 900):reason='Wall timeout'
        if reason:
            # Only a direct child group created above, still owned by this Popen instance.
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
            break
        time.sleep(1 if phase=='train' else 3)
    rc=p.wait()
write_json(ROOT/'raw'/f'{phase}-exit.json',{'completed_at':now(),'exit_code':rc,'reason':reason,'elapsed_seconds':time.monotonic()-started,'peak_observed_tree_rss_bytes':peak_rss,'pids_last_observed':ids,'cpu_affinity':affinity})
print(json.dumps({'phase':phase,'exit_code':rc,'reason':reason}),flush=True)
