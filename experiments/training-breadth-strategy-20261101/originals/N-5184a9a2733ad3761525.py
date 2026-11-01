"""Held Popen actual OS wait covers all outer initialization/prelaunch failures."""
import hashlib,json,os,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/contract-follow-e2e-20261101')
EXPECTED_OUTER_SHA256='7b5bea679be187d9fb6032132737002b8a0e0a30fc72a32290f8cf388278a504'

def held_wait(command,record,cwd,env,timeout):
    child=None;started=time.monotonic()
    outcome={'actual_outer_OS_exit':None,'release_verified':None,'argv':command}
    try:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                               cwd=cwd,env=env,start_new_session=True)
        outcome['pid']=child.pid
        stat=Path('/proc')/str(child.pid)/'stat'
        if stat.exists():outcome['start_stat']=stat.read_text()
        record('watch-child-start.json',outcome)
        stdout,stderr=child.communicate(timeout=timeout)
        outcome.update(actual_outer_OS_exit=child.returncode,release_verified=True,
                       stdout=stdout.decode('utf-8','replace'),stderr=stderr.decode('utf-8','replace'))
        return child.returncode if child.returncode>=0 else 128-child.returncode
    except Exception as error:
        outcome.update(error=repr(error),actual_outer_OS_exit=child.poll() if child else None)
        return 70
    finally:
        outcome['elapsed_seconds']=time.monotonic()-started
        record('watch-actual-exit.json',outcome)

def main():
    if len(sys.argv)!=1:raise SystemExit(78)
    assert sys.platform=='linux' and socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==os.getgid()==1012
    assert ROOT.resolve(strict=True)==ROOT
    sys.path.insert(0,str(ROOT/'source/production-adapter-v2'))
    from adapter_common import generic,process_identity
    source=generic.safe(ROOT,ROOT/'operator/recovery-01/outer.py',True)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==EXPECTED_OUTER_SHA256
    binding=json.loads(generic.safe(ROOT,ROOT/'operator/recovery-01/binding.json',True).read_text())
    assert 0<binding['remaining_seconds']<=5363.641942024231
    with generic.safe(ROOT,ROOT/'state/host-start-recovery-01.lock').open('x') as stream:
        json.dump({'request_id':binding['request_id'],'identity':process_identity(os.getpid())},stream)
    raw=generic.safe(ROOT,ROOT/'raw/recovery-01');raw.mkdir(exist_ok=True)
    def record(name,value):
        with generic.safe(ROOT,raw/name).open('x') as stream:
            json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    python='<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030/venv/bin/python3'
    env=generic.environment(ROOT,python,gpu_uuid=binding['gpu_uuid']);generic.prepare_environment_dirs(ROOT,env)
    return held_wait([python,'-I','-B','-u',str(source)],record,ROOT,env,binding['remaining_seconds']+5)

if __name__=='__main__':raise SystemExit(main())
