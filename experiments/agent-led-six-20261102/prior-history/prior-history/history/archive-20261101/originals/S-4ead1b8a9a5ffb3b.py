from pathlib import Path
import subprocess,json,uuid,shlex,tarfile,hashlib
A=Path(__file__).resolve().parent
rid='ds-coldstart-probe-'+uuid.uuid4().hex[:10]; evidence=A/rid; evidence.mkdir()
remote='<LOCAL_PRIVATE_PATH>'+rid
def cmd(args,**kw): return subprocess.run(args,text=True,capture_output=True,check=True,**kw)
cmd(['ssh','<PREPARATION_HOST_ALIAS>','mkdir -p '+shlex.quote(remote)+'/candidate '+shlex.quote(remote)+'/evidence'])
archive=evidence/'candidate.tar.gz'
with tarfile.open(archive,'w:gz') as tf:
    tf.add(A.parent/'originals/model/output',arcname='candidate',filter=lambda ti: None if '__pycache__' in ti.name else ti)
cmd(['scp',str(archive),str(A/'model_probe.py'),'<PREPARATION_HOST_ALIAS>:'+remote+'/'])
cmd(['ssh','<PREPARATION_HOST_ALIAS>','tar -xzf '+shlex.quote(remote+'/candidate.tar.gz')+' -C '+shlex.quote(remote)+' && chmod -R u+w '+shlex.quote(remote+'/candidate')])
docker=['docker','--context','<PREPARATION_HOST_ALIAS>']; image='python@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93'
args=[*docker,'run','--name',rid,'--network','none','--read-only','--cpus','2','--memory','4g','--pids-limit','128','--tmpfs','/tmp:rw,size=128m']
for v in ('codex.test=true','codex.run_id='+rid,'codex.cleanup=required','codex.owner=admet-deepseek-acceptance'): args+=['--label',v]
for v in ('PYTHONPATH=/deps','PYTHONDONTWRITEBYTECODE=1','OMP_NUM_THREADS=2','OPENBLAS_NUM_THREADS=2','MPLCONFIGDIR=/evidence/mpl','HOME=/evidence'):args+=['-e',v]
for v in (remote+'/candidate:/candidate',remote+'/evidence:/evidence',remote+'/model_probe.py:/probe.py:ro','<LOCAL_PRIVATE_PATH>','<LOCAL_PRIVATE_PATH>','<LOCAL_PRIVATE_PATH>'):args+=['-v',v]
args+=[image,'python','/probe.py']
try:
    p=subprocess.run(args,text=True,capture_output=True,timeout=180)
    (evidence/'docker.log').write_text(p.stdout+'\nSTDERR\n'+p.stderr)
    (evidence/'execution.json').write_text(json.dumps(dict(run_id=rid,args=args,exit_code=p.returncode),indent=2))
    cmd(['scp','-r','<PREPARATION_HOST_ALIAS>:'+remote+'/evidence/.',str(evidence)])
finally:
    c=subprocess.run([*docker,'rm','-f',rid],text=True,capture_output=True)
    left=cmd([*docker,'ps','-aq','--filter','label=codex.run_id='+rid]).stdout.strip()
    (evidence/'cleanup.json').write_text(json.dumps(dict(run_id=rid,remove_exit=c.returncode,containers_remaining=left),indent=2))
print(str(evidence))
print((evidence/'docker.log').read_text()[-16000:])
