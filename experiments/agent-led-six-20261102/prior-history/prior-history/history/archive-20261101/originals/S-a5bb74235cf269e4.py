from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,sys
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'source'))
from transport import remote
s=(RUN/'source/audit_traces.py').read_text().split("if __name__=='__main__':")[0]
s+='\nimport os\nos.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])\nr=[]\nfor p in sorted(Path(ROOT).joinpath("raw").glob("*.strace")):\n    a=audit(p);a.pop("successful_inside_paths",None);r.append(a)\nprint(json.dumps(r))\n'
(RUN/'source/audit_guarded_prelaunch_remote.py').write_text(s)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    a=pool.submit(remote,s,'audit-guarded-prelaunch',timeout=90)
    b=pool.submit(remote,RUN/'source/final_inventory_remote.py','inventory-prelaunch',timeout=150)
    audits=json.loads(a.result());inventory=json.loads(b.result())
(RUN/'operator/prelaunch-write-audit.json').write_text(json.dumps(audits,indent=2)+'\n')
assert not inventory['tree_identity_violations'],inventory['tree_identity_violations']
for a in audits:
    if Path(a['trace']).name=='setup05.strace':
        assert len(a['successful_outside_file_effects'])==7
        assert {x['path'] for x in a['successful_outside_file_effects']}=={'/dev/shm/sem.kK3d5M','/dev/shm/sem.joblib-2187947-jg6d0uzx'}
        assert not a['unknown_write_effects'] and not a['unfinished_at_eof']
    else:assert a['verdict']=='pass_for_traced_file_effects',a
imp=next(a for a in audits if Path(a['trace']).name=='import-check.strace')
assert not imp['failed_outside_or_unknown_attempts'] and not imp['outside_task_home_reads'],imp
print('Corrected complete import trace passes; previous setup05 violation explicitly retained. Tree has no outside symlink/hardlink/special-file violation.',flush=True)
res=subprocess.run(['python3','-B','scripts/check_plan.py','runs/hainan-skill-pilot-20261030/PLAN.json'],cwd=RUN.parents[1],capture_output=True,text=True)
(RUN/'raw/check-plan-prelaunch.json').write_text(res.stdout);assert res.returncode==0,res.stderr
expected={}
for mf in ['upload-initial-manifest.json','upload-training-manifest.json','upload-setup05-manifest.json','upload-guard-manifest.json']:expected.update(json.loads((RUN/'raw'/mf).read_text()))
s=(RUN/'source/launch_setup.py').read_text().replace('from common_remote import','from common_guarded import').replace('setup.launch_requested','train.launch_requested').replace('setup-supervisor.log','train-supervisor.log').replace("'source/supervisor_remote.py'),'setup'","'source/supervisor_train_guarded.py'),'train'").replace("'phase':'setup'","'phase':'train'")
insert='''
assert json.loads((ROOT/'raw/setup05-exit.json').read_text())['exit_code']==0
assert json.loads((ROOT/'raw/import-check-exit.json').read_text())['exit_code']==0
assert json.loads((ROOT/'raw/import-check-complete.json').read_text())['joblib_multiprocessing_disabled']
assert json.loads((ROOT/'raw/guard-import_check.json').read_text())['restrict_self_return_code']==0
expected=json.loads(EXPECTED_LITERAL)
import hashlib
for rel,meta in expected.items():
    p=safe(ROOT/rel,True)
    assert p.is_file() and p.stat().st_nlink==1 and p.stat().st_size==meta['size']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
'''.replace('EXPECTED_LITERAL',repr(json.dumps(expected)))
s=s.replace("with safe(ROOT/'state/train.launch_requested').open('x')",insert+"\nwith safe(ROOT/'state/train.launch_requested').open('x')")
(RUN/'source/launch_train_guarded.py').write_text(s)
print(remote(s,'launch-train',timeout=45).decode(),flush=True)
(RUN/'operator/status.json').write_text(json.dumps({'stage':'training_running','training_started':True,'strict_write_scope_overall':'failed_during_setup05','corrected_import_write_audit':'pass_for_traced_file_effects','joblib_multiprocessing':0,'landlock':True,'gpu_uuid':'<REGISTERED_GPU>','max_concurrent_gpu_jobs':1},indent=2)+'\n')
