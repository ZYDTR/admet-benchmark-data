"""Independent fixed read-only release and input check, without starting CUDA."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'raw/final-fetch'
sys.path.insert(0,str(R/'source'));import transport
identities={}
for phase in ['cuda01','cuda02','train01']:
 for suffix in ['dispatch','supervisor','launch']:
  d=json.loads((F/'raw'/f'{phase}-{suffix}.json').read_text());identities[str(d['pid'])]=d['start_stat'].rsplit(')',1)[1].split()[19]
 for line in (F/'raw'/f'{phase}-observations.jsonl').read_text().splitlines():
  for d in json.loads(line)['processes']:identities[str(d['pid'])]=d['start_stat'].rsplit(')',1)[1].split()[19]
source=r'''import json,os,socket,subprocess,hashlib,datetime,shutil,email.parser
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-follow-20261031')
OLD=ROOT.parent/'hainan-skill-pilot-20261030'
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012 and os.getgid()==1012 and ROOT.resolve(strict=True)==ROOT
identities=IDENTITIES
checks=[]
for pid,start in identities.items():
 p=Path('/proc')/pid/'stat'
 if not p.exists():checks.append({'pid':int(pid),'status':'gone'});continue
 parts=p.read_text().rsplit(')',1)[1].split()
 checks.append({'pid':int(pid),'status':'pid_reused' if parts[19]!=start else ('exited_zombie' if parts[0]=='Z' else 'STILL_RUNNING')})
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'hostname':socket.gethostname(),'uid':os.getuid(),'gid':os.getgid(),'own_processes':checks,'input_hashes':{},'source_hashes':{},'environment':{},'changes':[]}
def digest(p):
 assert p.resolve(strict=True)==p and p.stat().st_nlink==1
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for sub in ['input/train.csv','input/valid.csv','input/test.csv','assets/chemeleon_mp.pt']:
 result['input_hashes'][sub]=digest(ROOT/sub)
result['original_checkpoint_sha256']=digest(OLD/'assets/chemeleon_mp.pt')
for p in (ROOT/'source').iterdir():
 if p.is_file():result['source_hashes'][p.name]=digest(p)
for k,args in [('gpu_health',['nvidia-smi','-i','<REGISTERED_GPU>','-q','-x']),('apps',['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'])]:
 p=subprocess.run(args,capture_output=True,text=True,timeout=12);assert p.returncode==0,p.stderr;result[k]=p.stdout
v=OLD/'venv';result['environment']={'path':str(v),'python_sha256':digest(v/'bin/python3'),'pyvenv_config':(v/'pyvenv.cfg').read_text(),'packages':[]}
for p in sorted((v/'lib/python3.12/site-packages').glob('*.dist-info/METADATA')):
 msg=email.parser.Parser().parsestr(p.read_text());result['environment']['packages'].append({'name':msg.get('Name'),'version':msg.get('Version'),'metadata_sha256':digest(p)})
result['scheduler_commands']={x:shutil.which(x) for x in ['squeue','sinfo','qstat']}
print(json.dumps(result))
'''.replace('IDENTITIES',repr(identities))
(R/'source/postcheck_remote.py').write_text(source)
v=json.loads(transport.remote(source,'postcheck01',timeout=60));(R/'acceptance/postcheck.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({'own_processes':v['own_processes'],'packages':len(v['environment']['packages']),'scheduler_commands':v['scheduler_commands']}))
