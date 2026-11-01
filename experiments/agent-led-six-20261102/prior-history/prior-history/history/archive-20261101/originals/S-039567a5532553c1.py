"""Add new reviewed files only, under a uniquely named attempt with a unique trace."""
import base64,json,os,socket,subprocess,sys
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')
assert ROOT.resolve(strict=True)==ROOT and socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
child=base64.b64decode('__CHILD_SOURCE__').decode()
p=subprocess.run(['/usr/bin/strace','-f','-qq','-yy','-s','160','-e','trace=%file,write,writev,pwrite64,ftruncate','-o',str(ROOT/'raw/upload-setup02.strace'),'/usr/bin/python3','-I','-B','-c',child],stdin=sys.stdin.buffer,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT,env={'PATH':'/usr/bin:/bin','HOME':str(ROOT/'home'),'TMPDIR':str(ROOT/'tmp')})
print(json.dumps({'exit_code':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()}));assert p.returncode==0
