import json,os,socket,subprocess,sys
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
sys.path.insert(0,str(ROOT/'source'))
from common_remote import safe,environment,now
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
safe(ROOT,True)
assert json.loads((ROOT/'raw/setup-complete.json').read_text())['status']=='success'
assert json.loads((ROOT/'raw/setup05-exit.json').read_text())['exit_code']==0
with safe(ROOT/'state/train.launch_requested').open('x') as f:f.write(now())
with safe(ROOT/'raw/train-supervisor.log').open('xb') as f:
    p=subprocess.Popen(['/usr/bin/python3','-I','-B','-u',str(ROOT/'source/supervisor_train.py'),'train'],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,cwd=ROOT,env=environment(),start_new_session=True)
print(json.dumps({'phase':'train','supervisor_pid':p.pid,'launch_requested_at':now(),'start_stat':Path(f'/proc/{p.pid}/stat').read_text()}))
