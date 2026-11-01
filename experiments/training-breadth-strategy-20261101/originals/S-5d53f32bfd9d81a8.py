import datetime,json,os,signal,socket
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030');assert ROOT.resolve(strict=True)==ROOT and socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012
launch=json.loads((ROOT/'raw/setup02-launch.json').read_text());pid=launch['pid'];proc=Path(f'/proc/{pid}')
if (ROOT/'raw/setup02-exit.json').exists():print(json.dumps({'already_exited':json.loads((ROOT/'raw/setup02-exit.json').read_text())}))
else:
    current=(proc/'stat').read_text();start=current.split(') ',1)[1].split()[19];expected=launch['start_stat'].split(') ',1)[1].split()[19]
    assert start==expected and os.getpgid(pid)==launch['pgid'] and proc.stat().st_uid==1012
    cmd=(proc/'cmdline').read_bytes().split(b'\0');assert str(ROOT/'raw/setup02.strace').encode() in cmd
    os.killpg(launch['pgid'],signal.SIGTERM)
    print(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'signalled_own_pgid':launch['pgid'],'start_ticks':start,'reason':'Correct per-file dependency limit before large wheel; preserve attempt02 logs and partial files.'}))
