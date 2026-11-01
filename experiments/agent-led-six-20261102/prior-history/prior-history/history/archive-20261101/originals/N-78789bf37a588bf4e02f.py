"""Preflight -> training fail-fast adapter. Production profile is closed by default.

No SSH/upload/network transport. Local tests launch only fixed toy_science.
The production branch is prepared source, pending main review and target tests.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapter_common import ADAPTER, RUN, generic, load_boundary, load_runtime, process_identity, strict_json, write
from admission import GateClosed, require_production, runtime_preload
from phase_supervisor import run_phase

CASES = ('success', 'preflight_exit7', 'train_exit7', 'preflight_timeout', 'train_timeout',
         'preflight_missing_receipt',
         'preflight_check_failure', 'train_check_failure', 'monitor_failure',
         'legacy_success_only', 'missing_adapter_receipt', 'wrong_token', 'wrong_pid',
         'wrong_manifest', 'artifact_tamper', 'stale_legacy_complete')
CASES = (*CASES, 'learning_lock_exists', 'terminal_missing_rss', 'live_missing_rss', 'unreadable_rss', 'identity_mismatch', 'final_safety_violation', 'oom', 'malformed_artifact', 'terminal_missing_receipt', 'terminal_malformed_artifact', 'train_final_safety_violation', 'some_zero_gradient_steps', 'zero_gradient_all')


def production_callbacks(context, profile, phase):
    """Deferred target-only callbacks; never used by offline test path."""
    resource = load_runtime('resource_checks')
    root, gpu_uuid = context['root'], context['gpu_uuid']
    def query(args):
        process = subprocess.run(args, capture_output=True, text=True, timeout=10,
                                 env=context['environment'], cwd=root, check=True)
        return process.stdout
    def precheck():
        observations = []
        for index in range(3):
            xml = query(['nvidia-smi', '-i', gpu_uuid, '-q', '-x'])
            apps = query(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_gpu_memory',
                          '--format=csv,noheader,nounits'])
            # Store failed raw observations too; never mask a check failure.
            observations.append({'at': generic.now(), 'health_xml': xml, 'apps_csv': apps})
            write(root, context['attempt_root']/phase/'prelaunch.json', observations)
            resource.validate_idle_gpu(xml, apps, gpu_uuid, profile['gpu_index'])
            if index < 2:
                import time
                time.sleep(2)
        # No intervening deployment or setup follows this final resource check.
    def monitor(child):
        start = context['attempt_root']/phase/'worker-start.json'
        if start.exists():
            worker = strict_json(generic.safe(root, start, True))['worker_identity']
            try:
                live = process_identity(worker['pid'])
            except OSError as error:
                from process_state import ObservationUnknown
                raise ObservationUnknown('worker identity temporarily unreadable',
                    [{'expected': worker, 'error': repr(error)}],
                    terminal_reconciliation_allowed=isinstance(error, (ProcessLookupError, FileNotFoundError))) from error
            if (worker['pgid'] != child.pid or live['pgid'] != child.pid
                    or worker['start_ticks'] != live['start_ticks'] or live.get('ppid') != child.pid):
                from process_state import IdentityMismatch
                raise IdentityMismatch('worker lifetime/parent mismatch', [worker, live])
            context['owned_processes'].setdefault(worker['pid'], worker)
            context['observed_workers'][phase] = worker
        observation = resource.own_process_observation(child.pid,
            expected=context['owned_processes'], audit=context['process_audit'])
        observation['apps_csv'] = query(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_gpu_memory',
                                         '--format=csv,noheader,nounits'])
        observation['gpu_raw'] = query(['nvidia-smi', '-i', gpu_uuid,
                                        '--query-gpu=uuid,memory.used,utilization.gpu',
                                        '--format=csv,noheader,nounits'])
        observation['result_bytes'] = resource.result_bytes(root)
        resource.enforce_observation(observation, profile['resource_budget'], gpu_uuid, observation['pids'])
        return observation
    def final_checks(receipt, proofs):
        observation = {'tree_rss_bytes': 0, 'terminal_memory_basis': proofs,
            'apps_csv': query(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_gpu_memory',
                              '--format=csv,noheader,nounits']),
            'result_bytes': resource.result_bytes(root)}
        if resource.parse_apps(observation['apps_csv']) and any(
                row['gpu_uuid'] == gpu_uuid for row in resource.parse_apps(observation['apps_csv'])):
            raise RuntimeError('selected GPU has active process after verified own exits')
        resource.enforce_observation(observation, profile['resource_budget'], gpu_uuid, [])
        from trace_contract import verify_trace
        trace = verify_trace(root, context['attempt_root']/phase/'write.strace')
        return {'resource': observation, 'trace_sha256': trace['sha256'], 'trace_checked': True}
    return precheck, monitor, final_checks


def run(context, profile, case=None):
    root, offline = context['root'], context['offline']
    for name in ('raw', 'state', 'artifacts'):
        generic.safe(root, root/name).mkdir(exist_ok=True)
    attempt_root = generic.safe(root, root/'raw/attempt-01')
    context['attempt_root'] = attempt_root
    lock = generic.safe(root, root/'state/production-adapter-v2-start.lock')
    try:
        with lock.open('x') as stream:
            json.dump({'run_id': context['run_id'], 'at': generic.now(),
                       'supervisor_identity': process_identity(os.getpid()),
                       'manifest_sha256': context['manifest_sha256'], 'offline_fixture': offline}, stream)
    except FileExistsError:
        return 73, {'state': 'existing_run_query_original', 'success': False,
                    'supervisor_exit_code': 73}
    attempt_root.mkdir()
    cancelled = {'signal': None}
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda signum, frame: cancelled.update(signal=signum))
    result = {'run_id': context['run_id'], 'offline_fixture': offline, 'phases': {},
              'success': False, 'training_started': False, 'supervisor_exit_code': None,
              'training_process_launched': False, 'training_completed': False,
              'learning_attempt_registered': False, 'preflight_outer_passed': False,
              'remote_transport_performed': False}
    exit_code = 125
    for phase in ('preflight', 'train'):
        token = uuid.uuid4().hex
        command = [profile['python'], '-I', '-B', '-u', str(ADAPTER/'guarded_worker.py'),
                   'offline' if offline else 'production', '--root', str(root),
                   '--attempt', str(context['attempt_root']/phase), '--phase', phase, '--token', token]
        if not offline:
            command += ['--profile', str(context['profile_path'])]
        if offline:
            def precheck(phase=phase):
                if case == phase+'_check_failure':
                    raise RuntimeError('injected '+phase+' environment check failure')
            def monitor(child, phase=phase):
                if case == 'monitor_failure':
                    raise RuntimeError('injected resource observation unavailable')
                if phase == 'train' and case in ('terminal_missing_rss', 'live_missing_rss', 'unreadable_rss', 'identity_mismatch', 'terminal_missing_receipt', 'terminal_malformed_artifact'):
                    from offline_faults import inject_process_observation
                    inject_process_observation(root, context, child, case)
                return {'pid': child.pid, 'gpu_observed': False}
            def final_checks(receipt, proofs):
                if case == 'final_safety_violation' or (case == 'train_final_safety_violation' and phase == 'train'):
                    raise RuntimeError('independent final boundary check failed despite exit0/receipt')
                return {'offline_only': True, 'actual_child_wait': True, 'proofs': proofs}
            context['final_checks'] = final_checks
            timeout = 0.4 if case == phase+'_timeout' else 4
        else:
            precheck, monitor, context['final_checks'] = production_callbacks(context, profile, phase)
            timeout = 60 if phase == 'preflight' else profile['resource_budget']['training_timeout_seconds']
            command = load_boundary().trace_command(profile['python'], ADAPTER/'guarded_worker.py',
                                                      context['attempt_root']/phase/'write.strace', command[5:])
        timeout = min(timeout, context.get('budget_deadline', float('inf'))-__import__('time').monotonic())
        phase_precheck = precheck
        def precheck(phase=phase, phase_precheck=phase_precheck):
            phase_precheck()
            if __import__('time').monotonic() >= context.get('budget_deadline', float('inf')):
                raise TimeoutError('shared batch budget expired before learning lock')
            if phase == 'train':
                from completion import require_fresh_training_outputs
                require_fresh_training_outputs(root)
                learning = generic.safe(root, root/'state/learning-started.lock')
                with learning.open('x') as stream:
                    json.dump({'at': generic.now(), 'run_id': context['run_id'],
                               'attempt': '01', 'token': token, 'offline': offline}, stream)
        exit_code, status = run_phase(context, phase, token, command, precheck, monitor, timeout, cancelled)
        result['phases'][phase] = status
        if phase == 'preflight':
            result['preflight_outer_passed'] = exit_code == 0 and status['receipt_verified']
        if phase == 'train':
            launched = not offline and status['child_identity'] is not None
            result['training_process_launched'] = launched
            result['learning_attempt_registered'] = not offline and (root/'state/learning-started.lock').exists()
            # Launch/lock is not proof that an optimizer step happened. Unknown
            # interrupted learning stays unknown and the exclusive lock remains.
            result['training_started'] = (True if launched and exit_code == 0 and status['receipt_verified']
                                          else None if launched else False)
        # This branch is the only route to train; raw train-complete isn't read here.
        if exit_code != 0 or not status['receipt_verified']:
            break
    if 'train' not in result['phases']:
        result['phases']['train'] = {'state': 'skipped_failed_preflight', 'child_identity': None,
                                     'success': False, 'supervisor_exit_code': None}
    result.update(success=(exit_code == 0 and result['phases']['train'].get('receipt_verified') is True),
                  training_completed=(not offline and exit_code == 0 and result['phases']['train'].get('receipt_verified') is True),
                  supervisor_exit_code=exit_code, state='succeeded' if exit_code == 0 else 'failed',
                  finished_at=generic.now())
    write(root, attempt_root/'pipeline-exit.json', result)
    return exit_code, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('offline', 'production'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--case', choices=CASES, default='success')
    parser.add_argument('--profile', type=Path, default=ADAPTER/'adapter-profile.json')
    parser.add_argument('--remaining-budget-seconds', type=float, default=5400)
    args = parser.parse_args()
    if not 0 < args.remaining_budget_seconds <= 5400:
        raise GateClosed('batch remaining budget invalid')
    offline = args.mode == 'offline'
    if offline:
        root = args.root
        if root is None or RUN/'raw/offline' not in root.parents:
            raise GateClosed('offline root outside adapter checks')
        cfg = strict_json(root/'source/config.json')
        profile = {'python': sys.executable, 'gpu_uuid': 'GPU-offline-fixture', 'run_id': cfg['run_id']}
        manifest_sha = generic.sha(RUN/'tests/toy_science.py')
    else:
        root = RUN
        profile = strict_json(generic.safe(root, args.profile, True))
        admitted = require_production(profile, root)
        if sys.platform != 'linux' or os.uname().nodename != 'private-compute' or os.getuid() != 1012:
            raise GateClosed('target Linux private-compute UID identity mismatch')
        manifest_sha = admitted['manifest_sha256']
    env = generic.environment(root, profile['python'], gpu_uuid=profile['gpu_uuid'])
    generic.prepare_environment_dirs(root, env)
    # Optional shim has a separate runtime artifact manifest and formal binding;
    # the fixed four-file scientific manifest remains unchanged.
    if not offline and profile.get('compatibility_preload'):
        path = runtime_preload(profile, admitted, root)
        env['LD_PRELOAD'] = str(path)
    context = {'root': root, 'run_id': profile['run_id'], 'offline': offline, 'environment': env,
               'gpu_uuid': profile['gpu_uuid'], 'manifest_sha256': manifest_sha,
               'observed_workers': {}, 'profile_path': args.profile,
               'budget_deadline': __import__('time').monotonic()+args.remaining_budget_seconds}
    code, result = run(context, profile, args.case if offline else None)
    print(json.dumps(result), flush=True)
    return code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except GateClosed as error:
        print(json.dumps({'state': 'production_gate_closed', 'success': False,
                          'supervisor_exit_code': 78, 'reason': str(error)}), flush=True)
        raise SystemExit(78)
    except Exception as error:
        print(json.dumps({'state': 'adapter_error', 'success': False,
                          'supervisor_exit_code': 70, 'reason': type(error).__name__+': '+str(error)}), flush=True)
        raise SystemExit(70)
