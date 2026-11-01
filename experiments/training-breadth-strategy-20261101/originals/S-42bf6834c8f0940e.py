import os,socket,json,subprocess,datetime,stat
from pathlib import Path
root=Path('<AUTHORIZED_PROJECT_ROOT>')
assert socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012 and os.getgid()==1012
assert root.resolve(strict=True)==root and stat.S_ISDIR(root.lstat().st_mode)
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':socket.gethostname(),'uid':os.getuid(),'root':str(root),'loadavg':os.getloadavg(),'memory':Path('/proc/meminfo').read_text(),'disk_available':os.statvfs(root).f_bavail*os.statvfs(root).f_frsize}
for k,args in [('gpus',['nvidia-smi','-q','-x']),('apps',['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'])]:
 p=subprocess.run(args,capture_output=True,text=True,timeout=20);assert p.returncode==0,(k,p.stderr);result[k]=p.stdout
old=root/'admet/hainan-skill-pilot-20261030'
result['own_env']=[{'path':str(p),'realpath':str(p.resolve()),'exists':p.exists()} for p in [old/'venv/bin/python3',old/'assets/chemeleon_mp.pt',old/'artifacts/avoid_thread_name.so']]
print(json.dumps(result))
