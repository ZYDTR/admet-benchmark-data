"""One exact owned finite batch launch and actual OS wait, no transport."""
import datetime,json,os,resource,socket,subprocess,sys,time
from pathlib import Path

PARAMETERS = {'dispatch_sha256': 'b71b881e37a4d725d8614f473fee3e518cc0a46718675f44f6d5e08ff7505e5c'}
ROOT = Path('<AUTHORIZED_PROJECT_ROOT>/admet/contract-follow-e2e-20261101')


def main():
    assert socket.gethostname().split('.')[0] == 'private-compute' and os.getuid() == os.getgid() == 1012
    assert ROOT.resolve(strict=True) == ROOT
    sys.path.insert(0,str(ROOT/'source/production-adapter-v2'))
    from adapter_common import generic,load_runtime,process_identity,strict_json,write
    from admission import require_production,runtime_preload
    dispatch_path = generic.safe(ROOT,ROOT/'batch-dispatch.json',True)
    assert generic.sha(dispatch_path) == PARAMETERS['dispatch_sha256']
    dispatch = strict_json(dispatch_path)
    for spec in dispatch['runs']:
        root = Path(spec['root']);profile_path = generic.safe(root,root/spec['profile'],True)
        assert generic.sha(profile_path) == spec['profile_sha256']
        profile = strict_json(profile_path);admitted = require_production(profile,root);runtime_preload(profile,admitted,root)
        receipt = strict_json(generic.safe(root,root/'raw/deployment.json',True))
        for item in receipt['files']:
            path = generic.safe(root,root/item['path'],True)
            assert path.stat().st_size == item['size'] and generic.sha(path) == item['sha256']
    profile = strict_json(Path(dispatch['runs'][0]['root'])/dispatch['runs'][0]['profile'])
    env = generic.environment(ROOT,profile['python'],gpu_uuid=profile['gpu_uuid']);generic.prepare_environment_dirs(ROOT,env)
    def query(command):
        return subprocess.run(command,capture_output=True,text=True,timeout=15,check=True,env=env,cwd=ROOT).stdout
    xml = query(['nvidia-smi','-i',profile['gpu_uuid'],'-q','-x'])
    apps = query(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'])
    load_runtime('resource_checks').validate_idle_gpu(xml,apps,profile['gpu_uuid'],profile['gpu_index'])
    memory = {line.split(':')[0]:int(line.split(':')[1].split()[0])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemAvailable:','MemTotal:'))}
    disk = os.statvfs(ROOT);affinity = sorted(os.sched_getaffinity(0))[:2]
    assert memory['MemAvailable']>16*1024**3 and disk.f_bavail*disk.f_frsize>4*1024**3
    assert len(affinity)==2 and max(os.getloadavg())<os.cpu_count()/2
    assert time.time()<dispatch['deadline_epoch_seconds']
    write(ROOT,ROOT/'raw/host-immediate-prelaunch.json',{'at':generic.now(),'xml':xml,'apps_csv':apps,
          'memory':memory,'disk_available_bytes':disk.f_bavail*disk.f_frsize,'loadavg':os.getloadavg(),
          'selected_affinity':affinity,'gpu_uuid':profile['gpu_uuid'],'gpu_index':profile['gpu_index'],'shared_use':False})
    with generic.safe(ROOT,ROOT/'state/host-batch-start.lock').open('x') as stream:
        json.dump({'at':generic.now(),'identity':process_identity(os.getpid()),'message_id':dispatch['message_id']},stream)
    def limits():
        os.sched_setaffinity(0,affinity);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        resource.setrlimit(resource.RLIMIT_FSIZE,(450*1024**2,450*1024**2))
    command = [profile['python'],'-I','-B','-u',str(ROOT/'source/production-adapter-v2/batch.py'),
               'production','--root',str(ROOT),'--dispatch',str(dispatch_path)]
    child = None;identity = None;exit_record = None;started = time.monotonic()
    try:
        with generic.safe(ROOT,ROOT/'raw/batch.log').open('xb') as log:
            child = subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                                     env=env,cwd=ROOT,start_new_session=True,preexec_fn=limits)
        identity = process_identity(child.pid)
        receipt = {'at':generic.now(),'host_identity':process_identity(os.getpid()),'batch_identity':identity,
                   'command':command,'gpu_uuid':profile['gpu_uuid'],'gpu_index':profile['gpu_index'],
                   'formal_message_id':dispatch['message_id'],'dispatch_sha256':generic.sha(dispatch_path)}
        write(ROOT,ROOT/'raw/host-dispatch.json',receipt)
        code = child.wait(timeout=min(5500,dispatch['deadline_epoch_seconds']-time.time()+10))
        exit_record = {'state':'actual_batch_exit_verified','actual_OS_exit':code,'batch_identity':identity,
                       'host_identity':process_identity(os.getpid()),'actual_wait_verified':True}
        return code if code>=0 else 128-code
    finally:
        if exit_record is None:
            exit_record = {'state':'batch_release_unknown','actual_OS_exit':child.poll() if child else None,
                           'batch_identity':identity,'pid':child.pid if child else None,'actual_wait_verified':False}
        exit_record.update(at=generic.now(),elapsed_seconds=time.monotonic()-started)
        write(ROOT,ROOT/'raw/host-wait-exit.json',exit_record)


if __name__ == '__main__':
    raise SystemExit(main())
