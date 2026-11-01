from pathlib import Path
import json,sys
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'source'))
from transport import remote
s=(RUN/'source/audit_traces.py').read_text().split("if __name__=='__main__':")[0]
s+="\na=audit(Path(ROOT)/'raw/compile03.strace');a.pop('successful_inside_paths',None);print(json.dumps(a))\n"
(RUN/'source/audit_compile03_remote.py').write_text(s)
a=json.loads(remote(s,'audit-compile03',timeout=60));assert a['verdict']=='pass_for_traced_file_effects' and not a['failed_outside_or_unknown_attempts'],a
expected={}
for mf in ['upload-initial-manifest.json','upload-training-manifest.json','upload-setup05-manifest.json','upload-guard-manifest.json','upload-threadname-fix-manifest.json','upload-threadname-redirect-manifest.json']:expected.update(json.loads((RUN/'raw'/mf).read_text()))
s=(RUN/'source/launch_setup.py').read_text().replace('from common_remote import','from common_guarded import').replace('setup.launch_requested','train03.launch_requested').replace('setup-supervisor.log','train03-supervisor.log').replace("'source/supervisor_remote.py'),'setup'","'source/supervisor_train03.py'),'train03'").replace("'phase':'setup'","'phase':'train03'")
insert='''
assert json.loads((ROOT/'raw/setup05-exit.json').read_text())['exit_code']==0
assert json.loads((ROOT/'raw/compile03-exit.json').read_text())['exit_code']==0
assert json.loads((ROOT/'raw/train02-exit.json').read_text())['exit_code']==1
import datetime
assert (datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(json.loads((ROOT/'raw/setup-launch.json').read_text())['started_at'])).total_seconds()<2700, 'Original setup budget exhausted'
assert not (ROOT/'raw/train-runtime.json').exists(), 'Previous attempt must not have passed CUDA init'
assert {p.name for p in (ROOT/'artifacts').iterdir()}=={'no_thread_name.so','avoid_thread_name.so'}, 'No earlier model/feature artifact allowed'
previous=json.loads((ROOT/'raw/train02-launch.json').read_text())
p=Path('/proc')/str(previous['pid'])/'stat'
if p.exists():assert p.read_text().split(') ',1)[1].split()[19]!=previous['start_stat'].split(') ',1)[1].split()[19]
expected=json.loads(EXPECTED_LITERAL)
import hashlib
for rel,meta in expected.items():
    p=safe(ROOT/rel,True)
    assert p.is_file() and p.stat().st_nlink==1 and p.stat().st_size==meta['size']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
p=safe(ROOT/'artifacts/avoid_thread_name.so',True)
write_json(ROOT/'raw/train03-code-inputs.json',{'at':now(),'files':expected,'thread_name_preload_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Optional thread naming calls only; no model or optimizer operation intercepted'})
'''.replace('EXPECTED_LITERAL',repr(json.dumps(expected)))
s=s.replace('from common_guarded import safe,environment,now','from common_guarded import safe,environment,now,write_json')
s=s.replace("with safe(ROOT/'state/train03.launch_requested').open('x')",insert+"\nwith safe(ROOT/'state/train03.launch_requested').open('x')")
(RUN/'source/launch_train03.py').write_text(s)
print(remote(s,'launch-train03',timeout=45).decode(),flush=True)
(RUN/'operator/status.json').write_text(json.dumps({'stage':'train03_running','training_completed':False,'training_attempt01':'CUDA init failure before encoder/head','strict_write_scope_overall':'failed_setup05_joblib_semaphore','corrections':['JOBLIB_MULTIPROCESSING=0','Landlock write restriction','Task-only optional thread comm writes redirected to null under unchanged Landlock'],'gpu_uuid':'<REGISTERED_GPU>','max_concurrent_gpu_jobs':1},indent=2)+'\n')
