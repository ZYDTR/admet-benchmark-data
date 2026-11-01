import json,os,socket,subprocess,sys
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
sys.path.insert(0,str(ROOT/'source'))
from common_guarded import safe,environment,now,write_json
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
safe(ROOT,True);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
with safe(ROOT/'state/compile.started').open('x') as f:f.write(now())
args=['/usr/bin/strace','-f','-qq','-yy','-s','160','-e','trace=%file,write,writev,pwrite64,ftruncate,mmap,msync,close,dup,dup2,dup3,fchdir,fchmod,fchown,fsetxattr,fremovexattr,fallocate,copy_file_range,sendfile,landlock_create_ruleset,landlock_add_rule,landlock_restrict_self,prctl','-o',str(ROOT/'raw/compile.strace'),str(ROOT/'venv/bin/python3'),'-I','-B','-u',str(ROOT/'source/guard_exec_v2.py'),'compile']
with safe(ROOT/'raw/compile.log').open('xb') as log:
    p=subprocess.run(args,cwd=ROOT,env=environment(),stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,timeout=120)
write_json(ROOT/'raw/compile-exit.json',{'at':now(),'exit_code':p.returncode,'command':args})
print(json.dumps({'exit_code':p.returncode,'log':(ROOT/'raw/compile.log').read_text()[-1000:]}));assert p.returncode==0
