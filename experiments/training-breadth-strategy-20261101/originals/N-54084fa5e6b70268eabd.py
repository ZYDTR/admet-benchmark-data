"""Fixed nine-file append receiver and one held-wait launcher; no core edits."""
import ast,datetime,hashlib,importlib.util,io,json,os,sys,time,uuid,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
P=Path(__file__).resolve().parent;OP=P.parent
sys.path.insert(0,str(OP));import transport
transport.EVIDENCE=P/'raw';transport.RUN=P
TASK=json.loads((OP.parent/'recovery-01/setup-continuation-02/EXECUTE_TASK.json').read_text())
START=float(sys.argv[1]);PRIOR=json.loads((P/'status.json').read_text())['setup_spent_seconds']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
observed=json.loads((P/'current-reconcile.json').read_text())
assert all(x['unchanged'] for r in observed['deployed_identity'] for x in r['files'])
assert not any(x['state'] in ('matching_live','unknown') for x in observed['processes'])
sys.path.insert(0,str(OP/'batch-package/source/production-adapter-v2'));from adapter_common import load_runtime
gate=load_runtime('resource_checks');candidates=None
for sample in observed['observations']:
 accepted=set()
 for gpu in ET.fromstring(sample['xml']).findall('gpu'):
  uid=gpu.findtext('uuid');idx=int(gpu.findtext('minor_number'));node=ET.Element('nvidia_smi_log');node.append(gpu)
  rows=[x.split() for x in sample['pmon'].splitlines() if x.strip() and not x.lstrip().startswith('#') and x.split()[0]==str(idx)]
  try:gate.validate_idle_gpu(ET.tostring(node,encoding='unicode'),sample['apps'],uid,idx);assert rows and all(x[1]=='-' for x in rows)
  except (ValueError,AssertionError):continue
  accepted.add((idx,uid))
 candidates=accepted if candidates is None else candidates&accepted
assert candidates,'No current candidate; preserve resource wait'
selected=sorted(candidates,key=lambda x:(x[0]!=5,x[0]))[0]
selection={'passed':True,'selected':{'gpu_index':selected[0],'gpu_uuid':selected[1]},'source':'current-reconcile.json'};write(P/'selection-current.json',selection)
source=Path(TASK['admitted_source_root']);manifest=json.loads(Path(TASK['admitted_source_manifest']).read_text())
for item in manifest['files']:assert sha(source/item['path'])==item['sha256']
spec=importlib.util.spec_from_file_location('_approved_binding',source/'make_binding.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
package=source/('package-'+uuid.uuid4().hex[:10]);builder.build(selection,TASK['budget']['execution_remaining_seconds'],package)
files={str(p.relative_to(package)):{'size':p.stat().st_size,'sha256':sha(p)} for p in package.rglob('*') if p.is_file()};assert len(files)==9
names=TASK['run_ids']+[TASK['run_id']]
assert all(name.split('/')[0] in names and '/operator/recovery-01/' in name for name in files)
buffer=io.BytesIO()
with zipfile.ZipFile(buffer,'w',zipfile.ZIP_STORED) as archive:
 for name in files:archive.write(package/name,name)
payload=buffer.getvalue();(P/'append-payload.zip').write_bytes(payload)
params={'files':files,'root_names':names,'size':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}
old=(OP/'receiver_template.py').read_text();canonical=old[old.index('def canonical('):old.index('def collect(')]
receiver='import datetime,hashlib,io,json,os,socket,stat,sys,zipfile\nfrom pathlib import Path\nPARAMETERS='+repr(params)+'\n'+canonical+'''
def collect(payload,parameters):
 assert len(payload)==parameters['size'] and hashlib.sha256(payload).hexdigest()==parameters['sha256']
 with zipfile.ZipFile(io.BytesIO(payload)) as archive:
  names=archive.namelist();assert len(names)==len(set(names)) and set(names)==set(parameters['files'])
  for item in archive.infolist():
   p=Path(item.filename);mode=item.external_attr>>16
   assert not p.is_absolute() and '..' not in p.parts and str(p)==item.filename
   assert not item.is_dir() and item.compress_type==zipfile.ZIP_STORED and not stat.S_ISLNK(mode)
   assert not stat.S_ISCHR(mode) and not stat.S_ISBLK(mode)
   assert item.file_size==parameters['files'][item.filename]['size'] and item.file_size<128*1024
  data={name:archive.read(name) for name in names}
 for name,item in parameters['files'].items():assert len(data[name])==item['size'] and hashlib.sha256(data[name]).hexdigest()==item['sha256']
 return data

def main():
 assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==os.getgid()==1012
 michael=Path('<AUTHORIZED_PROJECT_ROOT>');parent=michael/'admet';canonical(parent,michael)
 batch=parent/'contract-follow-e2e-20261101';canonical(batch,michael)
 start=Path('/proc/self/stat').read_text();print(json.dumps({'event':'append_receiver_started','pid':os.getpid(),'start_stat':start}),flush=True)
 data=collect(sys.stdin.buffer.read(PARAMETERS['size']),PARAMETERS)
 for rootname in PARAMETERS['root_names']:
  root=parent/rootname;canonical(root,michael)
  for item in json.loads((root/'raw/deployment.json').read_text())['files']:
   p=canonical(root/item['path'],root);assert p.stat().st_size==item['size'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']
 for lock in ('host-batch-start.lock','batch-lifetime.lock','host-start-recovery-01.lock'):assert not (batch/'state'/lock).exists()
 for rootname in PARAMETERS['root_names'][:6]:
  root=parent/rootname;assert not any((root/'state').glob('*.lock')) and not (root/'raw/attempt-01').exists() and not (root/'artifacts').exists()
 prior=json.loads((batch/'raw/launch-receipt.json').read_text())['host_waiter_identity'];proc=Path('/proc')/str(prior['pid'])/'stat'
 if proc.exists():assert proc.read_text().rsplit(')',1)[1].split()[19]!=str(prior['start_ticks'])
 for name in data:
  path=canonical(parent/name,parent,False);assert not path.exists() and not path.is_symlink()
 for name,content in data.items():
  path=parent/name;path.parent.mkdir(parents=True,exist_ok=True);canonical(path.parent,michael)
  with path.open('xb') as stream:stream.write(content)
  assert hashlib.sha256(path.read_bytes()).hexdigest()==PARAMETERS['files'][name]['sha256']
 raw=canonical(batch/'raw/recovery-01',batch,False);raw.mkdir(exist_ok=True)
 receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':PARAMETERS['files'],'payload_sha256':PARAMETERS['sha256'],'pid':os.getpid(),'start_stat':start,'original_files_unchanged':True,'learning_started':False}
 with (raw/'append-deployment.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\\n')
 print(json.dumps({'event':'append_deployment_complete','receipt':receipt}),flush=True)
if __name__=='__main__':main()
'''
(P/'append-receiver.py').write_text(receiver);compile(receiver,'append-receiver.py','exec')
ns={'__name__':'_frame_test'};exec(compile(receiver,'receiver','exec'),ns)
assert set(ns['collect'](payload,params))==set(files)
rejected=[]
for label,data in [('truncated',payload[:-1]),('tampered',bytes([payload[0]^1])+payload[1:])]:
 try:ns['collect'](data,params)
 except AssertionError:rejected.append(label)
 else:raise AssertionError(label)
for label,evilname,mode in [('escape','../escape',0),('absolute','/escape',0),('symlink',next(iter(files)),0o120777<<16)]:
 b=io.BytesIO()
 with zipfile.ZipFile(b,'w',zipfile.ZIP_STORED) as archive:
  if mode:
   for name in files:
    info=zipfile.ZipInfo(name);info.compress_type=zipfile.ZIP_STORED;info.external_attr=mode if name==evilname else 0o100600<<16;archive.writestr(info,(package/name).read_bytes())
  else:archive.writestr(evilname,b'x')
 bad=b.getvalue();changed=dict(params,size=len(bad),sha256=hashlib.sha256(bad).hexdigest())
 try:ns['collect'](bad,changed)
 except AssertionError:rejected.append(label)
 else:raise AssertionError(label)
write(P/'append-review.json',{'passed':True,'package':str(package),'files':files,'payload_sha256':params['sha256'],'receiver_sha256':sha(P/'append-receiver.py'),'negative_cases':rejected,'original_core_and_outer_bytes_unchanged':True,'no_test_binding':True,'fixed_nine_paths_only':True})
assert PRIOR+(time.time()-START)<550,'Setup allowance nearly spent; do not mutate'
deployed=transport.remote_once(receiver,'append-once',payload=payload,timeout=55,readonly=False)
records=[json.loads(x) for x in deployed.decode().splitlines()];assert records[-1]['event']=='append_deployment_complete';write(P/'append-receipt.json',records)
launcher='''import datetime,json,os,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/contract-follow-e2e-20261101')
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==os.getgid()==1012 and ROOT.resolve(strict=True)==ROOT
sys.path.insert(0,str(ROOT/'source/production-adapter-v2'))
from adapter_common import generic,process_identity,strict_json,write
watch=generic.safe(ROOT,ROOT/'operator/recovery-01/watch.py',True)
assert generic.sha(watch)==WATCH_SHA
raw=generic.safe(ROOT,ROOT/'raw/recovery-01',True)
for name,item in strict_json(raw/'append-deployment.json')['files'].items():
 p=ROOT.parent/name;generic.safe(ROOT.parent,p,True);assert generic.sha(p)==item['sha256'] and p.stat().st_size==item['size']
binding=strict_json(ROOT/'operator/recovery-01/binding.json')
with (raw/'launcher-request.json').open('x') as stream:json.dump({'at':generic.now(),'identity':process_identity(os.getpid())},stream)
python='<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030/venv/bin/python3'
env=generic.environment(ROOT,python,gpu_uuid=binding['gpu_uuid']);generic.prepare_environment_dirs(ROOT,env)
with (raw/'watcher.log').open('xb') as log:child=subprocess.Popen([python,'-I','-B','-u',str(watch)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env,cwd=ROOT,start_new_session=True)
identity=process_identity(child.pid);receipt={'at':generic.now(),'watcher_identity':identity,'launcher_identity':process_identity(os.getpid()),'source':str(watch)}
write(ROOT,raw/'launcher-receipt.json',receipt);print(json.dumps({'launched':receipt}),flush=True)
record={'watcher_identity':identity,'actual_watcher_OS_exit':None,'actual_wait_verified':False}
try:
 code=child.wait(timeout=binding['remaining_seconds']+10);record.update(actual_watcher_OS_exit=code,actual_wait_verified=True)
finally:
 record['at']=generic.now();write(ROOT,raw/'launcher-watch-exit.json',record);print(json.dumps({'completed':record}),flush=True)
raise SystemExit(code if code>=0 else 128-code)
'''
launcher='WATCH_SHA='+repr(files[TASK['run_id']+'/operator/recovery-01/watch.py']['sha256'])+'\n'+launcher
(P/'launch-once.py').write_text(launcher);compile(launcher,'launch-once.py','exec')
spent=PRIOR+time.time()-START;assert spent<570,'Setup allowance nearly spent; do not launch'
write(P/'resume-setup-cutover.json',{'resume_native_start_epoch':START,'setup_spent_before_launch':spent,'setup_remaining_before_launch':600-spent,'launch_sent_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'append_verified':True,'recovery_start_sent_once':True})
state=json.loads((P/'status.json').read_text());state.update(state='recovery_launch_sent_once',setup_spent_seconds=spent,setup_remaining_seconds=600-spent,recovery_starts=1,learning_starts=None,append_deployment=True);write(P/'status.json',state)
try:
 result=transport.remote_once(launcher,'recovery-launch-once',timeout=5385,readonly=False)
 write(P/'launch-and-wait.json',[json.loads(x) for x in result.decode().splitlines()]);print(json.dumps({'actual_launcher_transport_exit':0,'all_waits_returned':True}))
except transport.fixed.QueryError as error:
 write(P/'launch-query-required.json',error.detail);print(json.dumps({'actual_launch_transport_error':error.detail['exit_code'],'must_query_original':True}))
