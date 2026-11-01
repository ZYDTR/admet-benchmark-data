import json,os,socket,subprocess,sys
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
sys.path.insert(0,str(ROOT/'source'))
from common_remote import safe,environment,now
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
safe(ROOT,True)
with safe(ROOT/'state/setup03.launch_requested').open('x') as f:f.write(now())
with safe(ROOT/'raw/setup03-supervisor.log').open('xb') as f:
    p=subprocess.Popen(['/usr/bin/python3','-I','-B','-u',str(ROOT/'source/supervisor_setup03.py'),'setup03'],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,env=environment(),start_new_session=True)
print(json.dumps({'phase':'setup03','supervisor_pid':p.pid,'launch_requested_at':now(),'start_stat':Path(f'/proc/{p.pid}/stat').read_text()}))
