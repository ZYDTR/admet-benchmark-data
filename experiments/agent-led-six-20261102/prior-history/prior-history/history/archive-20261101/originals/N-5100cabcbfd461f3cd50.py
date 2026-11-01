"""Future local binding derivation; does not connect, deploy or authorize launch."""
import hashlib,json,re,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
MAX_REMAINING=5363.641942024231
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
def build(observation,remaining,output):
    assert observation['passed'] is True and 0<remaining<=MAX_REMAINING
    gpu=observation['selected'];assert re.fullmatch(r'GPU-[0-9a-fA-F-]+',gpu['gpu_uuid']) and type(gpu['gpu_index']) is int
    assert output.parent==HERE and not output.exists();output.mkdir()
    original=HERE.parent;task=json.loads((original.parent/'TASK.json').read_text())
    runs=json.loads((original.parent/'RUNS.json').read_text());specs=[]
    for run in runs:
        profile=json.loads(Path(run['base_profile']).read_text())
        profile.update(gpu,execution_enabled=True,stage='main_recovery_01_current_GPU_bound')
        relative='operator/recovery-01/execution-profile.json';path=output/run['run_id']/relative
        write(path,profile);specs.append({'run_id':run['run_id'],'root':run['root'],'profile':relative,'profile_sha256':sha(path)})
    target=output/Path(task['target_batch_root']).name/'operator/recovery-01';target.mkdir(parents=True)
    for name in ('outer.py','watch.py'):shutil.copyfile(HERE/name,target/name)
    old=original/'fault-01-snapshot/contract-follow-e2e-20261101'
    dispatch=json.loads((original/'batch-package/batch-dispatch.json').read_text())
    dispatch.pop('runs');dispatch.pop('deadline_epoch_seconds')
    binding={'request_id':'admet-contract-follow-transport-recovery-20261101-001','remaining_seconds':remaining,
             **gpu,'profile_specs':specs,'batch_template':dispatch,
             'old_identity':json.loads((old/'raw/launch-receipt.json').read_text())['host_waiter_identity'],
             'old_launch_receipt_sha256':sha(old/'raw/launch-receipt.json'),
             'old_request_lock_sha256':sha(old/'state/host-start-request.lock')}
    write(target/'binding.json',binding)
    # batch-dispatch.json is created exclusively by outer after successful prelaunch;
    # its deadline uses actual recovery start + remaining, less cleanup reserve.
    return binding
if __name__=='__main__':
    raise SystemExit('Library-only candidate. Main admission and fresh observation required; no production CLI.')
