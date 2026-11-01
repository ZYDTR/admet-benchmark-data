import json,os,socket
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030');assert ROOT.resolve(strict=True)==ROOT and socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
r={}
for file in ['setup.strace','setup-observations.jsonl','setup.log']:
    p=ROOT/'raw'/file
    if p.exists():
        with p.open('rb') as f:f.seek(max(0,p.stat().st_size-11000));r[file]={'size':p.stat().st_size,'tail':f.read().decode(errors='replace')}
print(json.dumps(r))
