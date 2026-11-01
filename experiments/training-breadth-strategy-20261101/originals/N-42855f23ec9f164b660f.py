"""Read only this exact seven-root batch and its registered process lifetimes."""
import datetime,json,os,socket
from pathlib import Path
PARENT = Path('<AUTHORIZED_PROJECT_ROOT>/admet')
NAMES = ['hainan-paired-mse-s44-20261101','hainan-paired-mae-s44-20261101',
         'hainan-paired-mse-s45-20261101','hainan-paired-mae-s45-20261101',
         'hainan-paired-mse-s46-20261101','hainan-paired-mae-s46-20261101','contract-follow-e2e-20261101']
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==os.getgid()==1012
out = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roots':[],'processes':[]}
registered = {}
def register(value):
    if isinstance(value,dict):
        if type(value.get('pid')) is int and ('start_stat' in value or 'start_ticks' in value):
            registered[value['pid']] = value
        if type(value.get('receiver_pid')) is int and 'receiver_start_stat' in value:
            registered[value['receiver_pid']] = {'pid':value['receiver_pid'],'start_stat':value['receiver_start_stat']}
        for item in value.values():register(item)
    elif isinstance(value,list):
        for item in value:register(item)
for name in NAMES:
    root = PARENT/name
    assert root.resolve(strict=True)==root
    entry = {'root':str(root),'json':{},'log_tail':{},'locks':[]}
    for directory in ('raw','state'):
        folder = root/directory
        if not folder.exists():continue
        files = list(folder.rglob('*.json'));assert len(files)<300
        for path in files:
            assert path.resolve(strict=True)==path and path.stat().st_nlink==1
            if path.stat().st_size>1024**2:continue
            try:value=json.loads(path.read_text())
            except (ValueError,FileNotFoundError):continue
            entry['json'][str(path.relative_to(root))]=value;register(value)
    for path in (root/'raw/host-waiter.log',root/'raw/batch.log',root/'batch-child.log',
                 root/'raw/attempt-01/preflight/worker.log',root/'raw/attempt-01/train/worker.log'):
        if path.exists():
            assert path.resolve(strict=True)==path
            with path.open('rb') as stream:
                stream.seek(max(0,path.stat().st_size-4000));entry['log_tail'][str(path.relative_to(root))]=stream.read(4000).decode('utf-8','replace')
    if (root/'state').exists():entry['locks']=sorted(x.name for x in (root/'state').glob('*.lock'))
    out['roots'].append(entry)
for pid,prior in sorted(registered.items()):
    item={'pid':pid,'expected':prior}
    try:raw=(Path('/proc')/str(pid)/'stat').read_text()
    except FileNotFoundError:item['state']='absent_now'
    except OSError as error:item.update(state='unknown',error=repr(error))
    else:
        fields=raw.rsplit(')',1)[1].split();expected=prior.get('start_ticks')
        if expected is None:expected=prior['start_stat'].rsplit(')',1)[1].split()[19]
        item.update(raw_stat=raw,state='pid_reused' if str(expected)!=fields[19] else 'terminal' if fields[0] in ('Z','X') else 'matching_live')
    out['processes'].append(item)


import hashlib,subprocess
out['deployed_identity']=[]
for name in NAMES:
 root=PARENT/name
 receipt=json.loads((root/'raw/deployment.json').read_text())
 checks=[]
 for item in receipt['files']:
  p=root/item['path'];assert p.resolve(strict=True)==p and p.stat().st_nlink==1
  digest=hashlib.sha256(p.read_bytes()).hexdigest()
  checks.append({'path':item['path'],'sha256':digest,'unchanged':digest==item['sha256'] and p.stat().st_size==item['size']})
 out['deployed_identity'].append({'root':str(root),'files':checks})
profile=json.loads((PARENT/NAMES[0]/'source/production-adapter-v2/execution-profile.json').read_text())
code="import sys,json,hashlib,importlib.metadata as m;from pathlib import Path;print(json.dumps({'interpreter_sha256':hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),'packages':sorted([{'name':d.metadata['Name'],'version':d.version,'metadata_sha256':hashlib.sha256((Path(d._path)/'METADATA').read_bytes()).hexdigest()} for d in m.distributions()],key=lambda x:x['name'].lower())}))"
env={'PATH':str(Path(profile['python']).parent)+':/usr/bin:/bin','HOME':str(PARENT/NAMES[0]/'home'),'TMPDIR':str(PARENT/NAMES[0]/'tmp'),'JOBLIB_MULTIPROCESSING':'0'}
out['environment']=json.loads(subprocess.run([profile['python'],'-I','-B','-c',code],capture_output=True,text=True,timeout=15,check=True,env=env).stdout)
out['old_own_weight_sha256']=hashlib.sha256((PARENT/'hainan-mae-monitor-20261101/assets/chemeleon_mp.pt').read_bytes()).hexdigest()


recovery=PARENT/'contract-follow-e2e-20261101'
new=json.loads((recovery/'raw/recovery-01/append-deployment.json').read_text())
out['recovery_files_identity']=[]
for name,item in new['files'].items():
 path=PARENT/name;assert path.resolve(strict=True)==path and path.stat().st_nlink==1
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 out['recovery_files_identity'].append({'path':name,'sha256':digest,'unchanged':digest==item['sha256'] and path.stat().st_size==item['size']})
binding=json.loads((recovery/'operator/recovery-01/binding.json').read_text())
out['actual_recovery_gpu_uuid']=binding['gpu_uuid'];out['actual_recovery_gpu_index']=binding['gpu_index']
out['gpu_health_xml']=subprocess.run(['/usr/bin/nvidia-smi','-i',binding['gpu_uuid'],'-q','-x'],capture_output=True,text=True,timeout=15,check=True).stdout
out['gpu_apps_csv']=subprocess.run(['/usr/bin/nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10,check=True).stdout
print(json.dumps(out))
