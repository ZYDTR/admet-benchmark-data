import concurrent.futures,json,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
def fetch(i):
 r=subprocess.run([sys.executable,'-B',str(p/'fetch.py'),str(i)],capture_output=True,text=True,timeout=270)
 return {'index':i,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for result in pool.map(fetch,range(8,28)):
  results.append(result);print(json.dumps(result),flush=True)
(p/'fetch-remaining-results.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(x['exit']==0 for x in results), 'Some retrievals need reconciliation'
