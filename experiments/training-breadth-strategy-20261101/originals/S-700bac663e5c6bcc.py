
import csv,datetime,hashlib,io,json,os,socket,stat,subprocess
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012 and os.getgid()==1012
assert ROOT.resolve(strict=True)==ROOT
recorded={2797587: '373671633', 2797593: '373671633', 2099578: '373508409', 2099583: '373508410', 2157014: '373521472', 2187109: '373528476', 2187947: '373528669', 1668753: '373411886', 1668756: '373411887', 1872696: '373456729', 1799124: '373441472', 1799129: '373441472', 1801443: '373441999', 1802104: '373442151', 2416259: '373580754', 2416264: '373580754', 2595295: '373623407', 2595300: '373623407', 1929112: '373469336', 1929116: '373469336', 1929222: '373469356', 1668709: '373411876', 2415132: '373580492', 1929073: '373469327', 1872661: '373456721', 2594243: '373623146', 2796514: '373671370', 1799083: '373441463', 2099536: '373508399'}
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
