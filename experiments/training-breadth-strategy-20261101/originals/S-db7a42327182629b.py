"""Parent read-only post-check via the reviewed fixed Hainan transport."""
import hashlib, importlib.util, json
from pathlib import Path

RUN=Path(__file__).resolve().parents[1]
FETCH=RUN/'raw/final-fetch'
identities={}
for path in (FETCH/'raw').glob('*-observations.jsonl'):
    for line in path.open():
        for item in json.loads(line).get('processes',[]):
            identities[item['pid']]=item['start_stat'].split(') ',1)[1].split()[19]
for pattern in ('*-supervisor.json','*-launch.json'):
    for path in (FETCH/'raw').glob(pattern):
        item=json.loads(path.read_text())
        identities[item['pid']]=item['start_stat'].split(') ',1)[1].split()[19]

source="""
import csv,datetime,hashlib,io,json,os,socket,stat,subprocess
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012 and os.getgid()==1012
assert ROOT.resolve(strict=True)==ROOT
recorded=RECORDED
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':socket.gethostname(),'uid':os.getuid(),'gid':os.getgid(),'root':str(ROOT),'changes':[],'processes':[],'files':[]}
for pid,ticks in recorded.items():
    p=Path('/proc')/str(pid)/'stat'
    try:text=p.read_text()
    except FileNotFoundError:text=None
    fields=text.split(') ',1)[1].split() if text else None
    r['processes'].append({'pid':int(pid),'expected_ticks':ticks,'current_stat':text,'same_live_process':bool(fields and fields[19]==ticks and fields[0]!='Z')})
for rel in ['input/train.csv','input/valid.csv','input/test.csv','assets/chemeleon_mp.pt']:
    p=ROOT/rel;assert p.resolve()==p and p.stat().st_nlink==1
    r['files'].append({'path':rel,'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
r['artifact_names']=[p.name for p in (ROOT/'artifacts').iterdir()]
r['expected_sem_names_present']={str(p):p.exists() for p in [Path('/dev/shm/sem.kK3d5M'),Path('/dev/shm/sem.joblib-2187947-jg6d0uzx')]}
for key,args in [('selected_gpu',['nvidia-smi','-i','<REGISTERED_GPU>','-q']),('compute_apps',['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'])]:
    p=subprocess.run(args,capture_output=True,text=True,timeout=12)
    r[key]={'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
print(json.dumps(r))
""".replace('RECORDED',repr(identities))
out=RUN/'acceptance/parent-remote'
(out/'raw/local-tmp').mkdir(parents=True,exist_ok=True)
(out/'read_only_source.py').write_text(source)
spec=importlib.util.spec_from_file_location('reviewed_transport',RUN/'source/transport.py')
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
transport.RUN=out
result=json.loads(transport.remote(source,'read-only-postcheck',timeout=50))
print(json.dumps({'processes_checked':len(result['processes']),'same_live_processes':[x['pid'] for x in result['processes'] if x['same_live_process']],'file_hashes':result['files'],'artifact_names':result['artifact_names'],'sem_names_present':result['expected_sem_names_present'],'selected_gpu_returncode':result['selected_gpu']['returncode'],'recovery_reset':'GPU Recovery Action                   : Reset' in result['selected_gpu']['stdout']},ensure_ascii=False))
