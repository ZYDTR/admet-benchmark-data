"""Primary-operated fixed run actions. No arbitrary target or shell arguments."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent));import transport
R=Path(__file__).resolve().parents[1]
action=sys.argv[1];assert action in ['launch-cuda01','launch-train01','status']
base="""import os,sys,json,socket,subprocess,stat,datetime
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-follow-20261031')
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012 and os.getgid()==1012
assert ROOT.resolve(strict=True)==ROOT
sys.path.insert(0,str(ROOT/'source'))
from common_guarded import safe,environment,write_json,now
safe(ROOT,True)
"""
if action.startswith('launch-'):
 phase=action.removeprefix('launch-')
 code=base+f"phase={phase!r}\n"+"""lock=ROOT/'state'/f'{phase}.launch-request'
with lock.open('x') as f:f.write(now())
args=['/usr/bin/python3','-I','-B','-u',str(ROOT/'source/supervisor.py'),phase]
with (ROOT/'raw'/f'{phase}-supervisor.log').open('xb') as log:
 p=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=ROOT,env=environment())
record={'pid':p.pid,'start_stat':Path(f'/proc/{p.pid}/stat').read_text(),'at':now(),'phase':phase}
write_json(ROOT/'raw'/f'{phase}-dispatch.json',record);print(json.dumps(record))
"""
else:
 code=base+"""result={}
for phase in ['cuda01','train01']:
 v={}
 for suffix in ['dispatch.json','exit.json','complete.json','supervisor.log','log']:
  p=ROOT/'raw'/f'{phase}-{suffix}' if suffix not in ['log'] else ROOT/'raw'/f'{phase}.log'
  if p.exists():v[suffix]=p.read_text()[-12000:]
 result[phase]=v
print(json.dumps(result))
"""
(R/'source'/f'{action}_remote.py').write_text(code)
tag=action if action!='status' else 'status-'+__import__('datetime').datetime.now().strftime('%H%M%S')
print(transport.remote(code,tag,timeout=50).decode())
