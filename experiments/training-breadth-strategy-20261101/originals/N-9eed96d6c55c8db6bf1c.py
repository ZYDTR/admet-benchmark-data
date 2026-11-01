"""Append-only recovery-01 outer; production has no fixture mode or query override."""
import datetime,hashlib,json,os,resource,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/contract-follow-e2e-20261101')
MAX_REMAINING=5363.641942024231
OVERALL=1793544604.502622
REQUEST='admet-contract-follow-transport-recovery-20261101-001'

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run_outer(context):
    """The shared actual workflow; fixtures exist only in a separate test entry."""
    started=time.monotonic();wall=time.time()
    outcome={'request_id':REQUEST,'started_at':now(),'batch_invocation_attempted':False,
             'actual_batch_OS_exit':None,'release_verified':None,'returncode':70}
    child=None
    try:
        context.record('outer-start.json',{'at':now(),'identity':context.identity()})
        remaining=context.prepare()
        if not 0<remaining<=MAX_REMAINING:raise ValueError('remaining budget outside original allowance')
        outcome['starting_remaining_seconds']=remaining
        records=[]
        for index,command in enumerate(context.commands()):
            begin=now();clock=time.monotonic()
            try:
                process=context.query(command)
                raw={'argv':command,'started_at':begin,'finished_at':now(),
                     'elapsed_seconds':time.monotonic()-clock,'actual_OS_exit':process.returncode,
                     'stdout':process.stdout,'stderr':process.stderr}
            except Exception as error:
                raw={'argv':command,'started_at':begin,'finished_at':now(),
                     'elapsed_seconds':time.monotonic()-clock,'actual_OS_exit':None,'error':repr(error),
                     'stdout':getattr(error,'stdout',None),'stderr':getattr(error,'stderr',None)}
                # Decode timed-out query bytes without losing their content.
                for field in ('stdout','stderr'):
                    if isinstance(raw[field],bytes):raw[field]=raw[field].decode('utf-8','replace')
                context.record('query-%02d.json'%index,raw)
                raise
            context.record('query-%02d.json'%index,raw) # durable before parsing/refusal
            records.append(raw)
            if raw['actual_OS_exit']!=0:raise ValueError('system query failed')
        context.validate(records)
        context.reconcile() # immediately before exclusive global start
        elapsed=time.monotonic()-started
        if remaining-elapsed<=5:
            outcome.update(returncode=124,state='budget_expired_before_batch');return 124
        # Reserve five seconds for actual wait/outcome finalization, never reset5400.
        deadline=min(OVERALL,wall+remaining-5)
        outcome.update(deadline_epoch_seconds=deadline,prelaunch_seconds=elapsed,
                       batch_invocation_attempted=True)
        child=context.start_batch(deadline)
        outcome['batch_identity']=context.identity(child.pid)
        context.record('batch-start.json',dict(outcome,at=now()))
        code=child.wait(timeout=max(.001,remaining-(time.monotonic()-started)))
        outcome.update(state='actual_batch_exit_verified',actual_batch_OS_exit=code,
                       release_verified=True,returncode=128-code if code<0 else code)
        return outcome['returncode']
    except (ValueError,AssertionError) as error:
        outcome.update(state='prelaunch_refused' if child is None else 'batch_state_failed',
                       error=repr(error),returncode=78 if child is None else 70)
        return outcome['returncode']
    except Exception as error:
        outcome.update(state='outer_failed_or_release_unknown',error=repr(error),returncode=70)
        return 70
    finally:
        elapsed=time.monotonic()-started
        outcome.update(finished_at=now(),elapsed_seconds=elapsed,
                       remaining_after_seconds=max(0,outcome['starting_remaining_seconds']-elapsed) if 'starting_remaining_seconds' in outcome else None,
                       additional_failed_start_debit_seconds=elapsed if child is None else 0,
                       actual_batch_OS_exit=child.poll() if child is not None else None)
        if child is None and not outcome['batch_invocation_attempted']:outcome['release_verified']=True
        context.record('outer-outcome.json',outcome)

class Production:
    def __init__(self):
        assert sys.platform=='linux' and socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==os.getgid()==1012
        assert ROOT.resolve(strict=True)==ROOT
        sys.path.insert(0,str(ROOT/'source/production-adapter-v2'))
        from adapter_common import generic,process_identity,load_runtime
        self.generic,self.identity,self.load_runtime=generic,process_identity,load_runtime
        self.raw=generic.safe(ROOT,ROOT/'raw/recovery-01');self.raw.mkdir(exist_ok=True)
    def record(self,name,value):
        path=self.generic.safe(ROOT,self.raw/name)
        with path.open('x') as stream:
            json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    def prepare(self):
        path=self.generic.safe(ROOT,ROOT/'operator/recovery-01/binding.json',True)
        self.binding=json.loads(path.read_text())
        expected={'request_id','remaining_seconds','gpu_uuid','gpu_index','profile_specs',
                  'batch_template','old_identity','old_launch_receipt_sha256','old_request_lock_sha256'}
        assert set(self.binding)==expected and self.binding['request_id']==REQUEST
        self.record('binding-used.json',{'path':str(path),'sha256':sha(path),'binding':self.binding})
        assert sha(ROOT/'raw/launch-receipt.json')==self.binding['old_launch_receipt_sha256']
        assert self.binding['old_identity']==json.loads((ROOT/'raw/launch-receipt.json').read_text())['host_waiter_identity']
        assert sha(ROOT/'state/host-start-request.lock')==self.binding['old_request_lock_sha256']
        self.reconcile()
        from admission import require_production,runtime_preload
        for name in [x['run_id'] for x in self.binding['profile_specs']]+[ROOT.name]:
            original=ROOT.parent/name
            for item in json.loads((original/'raw/deployment.json').read_text())['files']:
                old=self.generic.safe(original,original/item['path'],True)
                assert old.stat().st_size==item['size'] and sha(old)==item['sha256']
        registration=json.loads((ROOT/'source/production-adapter-v2/batch-registration.json').read_text())
        assert [x['run_id'] for x in self.binding['profile_specs']]==[x['run_id'] for x in registration['runs']]
        profiles=[]
        for spec in self.binding['profile_specs']:
            root=ROOT.parent/spec['run_id'];assert str(root)==spec['root']
            assert spec['profile']=='operator/recovery-01/execution-profile.json'
            profile_path=self.generic.safe(root,root/spec['profile'],True)
            assert sha(profile_path)==spec['profile_sha256']
            profile=json.loads(profile_path.read_text());base=json.loads((root/'admission/execution-profile.base.json').read_text())
            allowed={'gpu_uuid','gpu_index','execution_enabled','stage'}
            assert {k:v for k,v in profile.items() if k not in allowed}=={k:v for k,v in base.items() if k not in allowed}
            assert profile['gpu_uuid']==self.binding['gpu_uuid'] and profile['gpu_index']==self.binding['gpu_index']
            admitted=require_production(profile,root);runtime_preload(profile,admitted,root)
            profiles.append(profile)
        self.profile=profiles[0]
        self.env=self.generic.environment(ROOT,self.profile['python'],gpu_uuid=self.profile['gpu_uuid'])
        self.generic.prepare_environment_dirs(ROOT,self.env)
        assert os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize>4*1024**3
        mem={x.split(':')[0]:int(x.split(':')[1].split()[0])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')}
        assert mem['MemAvailable']>16*1024**3 and max(os.getloadavg())<os.cpu_count()/2
        return self.binding['remaining_seconds']
    def commands(self):
        return [['/usr/bin/nvidia-smi','-i',self.binding['gpu_uuid'],'-q','-x'],
                ['/usr/bin/nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits']]
    def query(self,command):
        return subprocess.run(command,capture_output=True,text=True,timeout=15,env=self.env,cwd=ROOT)
    def validate(self,records):
        self.load_runtime('resource_checks').validate_idle_gpu(records[0]['stdout'],records[1]['stdout'],
            self.binding['gpu_uuid'],self.binding['gpu_index'])
    def reconcile(self):
        prior=self.binding['old_identity']
        try:current=self.identity(prior['pid'])
        except (FileNotFoundError,ProcessLookupError):current=None
        else:assert current['start_ticks']!=prior['start_ticks'], 'original lifetime still present; no restart'
        for name in ('host-batch-start.lock','batch-lifetime.lock','batch-state.json'):
            assert not (ROOT/'state'/name).exists(),'original batch exists; reconcile only'
        registration=json.loads((ROOT/'source/production-adapter-v2/batch-registration.json').read_text())
        for item in registration['runs']:
            root=ROOT.parent/item['run_id'];self.generic.safe(root,root,True)
            assert not any((root/'state').glob('*.lock'))
            assert not (root/'raw/attempt-01').exists() and not (root/'artifacts').exists()
    def start_batch(self,deadline):
        from batch import registered_scope,execution_allowance
        dispatch=dict(self.binding['batch_template']);dispatch.update(deadline_epoch_seconds=deadline,runs=self.binding['profile_specs'])
        original=json.loads((ROOT/'batch-dispatch.json').read_text())
        assert {k:v for k,v in dispatch.items() if k not in ('runs','deadline_epoch_seconds')}=={k:v for k,v in original.items() if k not in ('runs','deadline_epoch_seconds')}
        registration=json.loads((ROOT/'source/production-adapter-v2/batch-registration.json').read_text())
        registered_scope(dispatch,ROOT,registration);execution_allowance(dispatch)
        assert dispatch['runtime_source_manifest']['sha256']=='1a04c54229935de62fc5614605736753f79d4f8dc74c1c76a78d56a5c7d29182'
        dispatch_path=self.generic.safe(ROOT,ROOT/'operator/recovery-01/batch-dispatch.json')
        with dispatch_path.open('x') as stream:json.dump(dispatch,stream,indent=2);stream.write('\n')
        self.record('dispatch-used.json',{'path':str(dispatch_path),'sha256':sha(dispatch_path),'deadline':deadline})
        with self.generic.safe(ROOT,ROOT/'state/host-batch-start.lock').open('x') as stream:
            json.dump({'at':now(),'identity':self.identity(),'request_id':REQUEST},stream)
        affinity=sorted(os.sched_getaffinity(0))[:2];assert len(affinity)==2
        def limits():
            os.sched_setaffinity(0,affinity);resource.setrlimit(resource.RLIMIT_CORE,(0,0))
            resource.setrlimit(resource.RLIMIT_FSIZE,(450*1024**2,450*1024**2))
        command=[self.profile['python'],'-I','-B','-u',str(ROOT/'source/production-adapter-v2/batch.py'),
                 'production','--root',str(ROOT),'--dispatch',str(dispatch_path)]
        self.record('batch-argv.json',{'argv':command,'affinity':affinity})
        with self.generic.safe(ROOT,self.raw/'batch.log').open('xb') as log:
            return subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                env=self.env,cwd=ROOT,start_new_session=True,preexec_fn=limits)

def main():
    if len(sys.argv)!=1:raise SystemExit(78) # fixture/command/target injection rejected
    return run_outer(Production())

if __name__=='__main__':raise SystemExit(main())
