"""Await the identified CUDA phase, verify its trace, then submit one fixed training phase."""
from pathlib import Path
import json,subprocess,sys,time
R=Path(__file__).resolve().parents[1]
def action(script,*args):
 p=subprocess.run(['python3','-B',str(R/'source'/script),*args],capture_output=True,text=True,check=True)
 return p.stdout
for i in range(12):
 v=json.loads(action('operate02.py','status'))['cuda02']
 if 'exit.json' in v:
  exit=json.loads(v['exit.json']);assert exit['exit_code']==0,exit
  assert json.loads(v['complete.json'])['actual_cuda_matmul'] is True
  print('CUDA02 complete',json.dumps(exit),flush=True);break
 time.sleep(3)
else:raise RuntimeError('CUDA02 still pending; query original phase; never resubmit unknown state')
print(action('collect.py','preflight02-fetch'),flush=True)
print(action('audit_raw.py','preflight02-fetch'),flush=True)
a=json.loads((R/'acceptance/audit-preflight02-fetch.json').read_text())
assert not a['manifest_mismatches'] and len(a['traces'])==2
assert all(not t['outside_mutation_evidence'] and not t['unresolved_count'] and not t['pending_at_eof'] for t in a['traces'])
ref=json.loads((R/'raw/environment-before02.stdout').read_text());assert len(ref['packages'])==78
p=subprocess.run(['python3','-B','scripts/check_plan.py','runs/hainan-skill-follow-20261031/PLAN.json'],cwd=R.parents[1],capture_output=True,text=True,check=True)
(R/'raw/check-plan-pretrain.json').write_text(p.stdout)
print(action('operate02.py','launch-train01'),flush=True)
s=json.loads((R/'status.json').read_text());s.update({'phase':'training_running','cuda_preflight_completed':True,'preflight_write_audit_verified':True,'training_completed':False});(R/'status.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
