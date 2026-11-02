import os,json,datetime
from pathlib import Path
R=Path('task-storage://admet/scaler-six28-20261102')
assert os.getuid()==1012 and R.resolve(strict=True)==R
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
for n in ['job-start01.json','worker-identity.json','study-progress.json','study-complete.json','science-error.json','job-exit01.json','observation-attention.json']:
 f=R/'raw'/n
 if f.exists():out[n]=json.loads(f.read_text())
f=R/'raw/worker01.stderr'
if f.exists():out['stderr_tail']=f.read_text()[-4000:]
f=R/'raw/resource01.jsonl'
if f.exists():
 v=json.loads(f.read_text().splitlines()[-1]);q=v.pop('query');out['last_resource']={**v,'query':{k:x for k,x in q.items() if k not in ['stdout','stderr']}}
started=[]
for e in json.loads((R/'input/TASK.json').read_text())['runs']:
 f=R/e['run_id']/'raw/learning-started.json'
 if f.exists():
  pr=R/e['run_id']/'raw/progress.json';started.append({'run_id':e['run_id'],'progress':json.loads(pr.read_text()) if pr.exists() else None})
out['learning_runs']=started
print(json.dumps(out))
