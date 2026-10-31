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
CASES = (*CASES, 'prior_learning_record', 'learning_lock_exists')


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
        if child.poll() is not None:
            return {'leader_exited': True}
        try:
            observation = resource.own_process_observation(child.pid)
        except (FileNotFoundError, KeyError):
            if child.poll() is not None:
                return {'leader_exited': True}
            raise
        observation['apps_csv'] = query(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_gpu_memory',
                                         '--format=csv,noheader,nounits'])
        observation['gpu_raw'] = query(['nvidia-smi', '-i', gpu_uuid,
                                        '--query-gpu=uuid,memory.used,utilization.gpu',
                                        '--format=csv,noheader,nounits'])
        observation['result_bytes'] = resource.result_bytes(root)
        resource.enforce_observation(observation, profile['resource_budget'], gpu_uuid, observation['pids'])
        start = context['attempt_root']/phase/'worker-start.json'
        if start.exists():
            record = strict_json(generic.safe(root, start, True))
            worker = record['worker_identity']
            if worker['pgid'] != child.pid:
                raise ValueError('worker escaped launcher process group')
            try:
                live = process_identity(worker['pid'])
            except ProcessLookupError:
                live = None
            if live is not None:
                if live.get('start_ticks') != worker.get('start_ticks') or live['pgid'] != child.pid:
                    raise ValueError('live worker identity mismatch')
                context['observed_workers'][phase] = worker
        return observation
    return precheck, monitor


def run(context, profile, case=None):
    root, offline = context['root'], context['offline']
    for name in ('raw', 'state', 'artifacts'):
        generic.safe(root, root/name).mkdir(exist_ok=True)
    attempt_root = generic.safe(root, root/'raw/attempt-v2')
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
            def monitor(child):
                if case == 'monitor_failure':
                    raise RuntimeError('injected resource observation unavailable')
                return {'pid': child.pid, 'gpu_observed': False}
            timeout = 0.4 if case == phase+'_timeout' else 4
        else:
            precheck, monitor = production_callbacks(context, profile, phase)
            timeout = 60 if phase == 'preflight' else profile['resource_budget']['training_timeout_seconds']
            command = load_boundary().trace_command(profile['python'], ADAPTER/'guarded_worker.py',
                                                      context['attempt_root']/phase/'write.strace', command[5:])
        phase_precheck = precheck
        def precheck(phase=phase, phase_precheck=phase_precheck):
            phase_precheck()
            if phase == 'train':
                from completion import require_fresh_training_outputs
                require_fresh_training_outputs(root)
                old = root/'raw/pipeline-exit.json'
                if old.exists():
                    prior = strict_json(generic.safe(root, old, True))
                    if prior.get('training_started') is not False or prior['phases']['train'].get('child_identity') is not None:
                        raise ValueError('prior learning state not confirmed unstarted')
                learning = generic.safe(root, root/'state/learning-started.lock')
                with learning.open('x') as stream:
                    json.dump({'at': generic.now(), 'run_id': context['run_id'],
                               'attempt': 'v2', 'token': token, 'offline': offline}, stream)
        exit_code, status = run_phase(context, phase, token, command, precheck, monitor, timeout, cancelled)
        result['phases'][phase] = status
        if phase == 'train':
            result['training_started'] = (not offline and status['child_identity'] is not None)
        # This branch is the only route to train; raw train-complete isn't read here.
        if exit_code != 0 or not status['receipt_verified']:
            break
    if 'train' not in result['phases']:
        result['phases']['train'] = {'state': 'skipped_failed_preflight', 'child_identity': None,
                                     'success': False, 'supervisor_exit_code': None}
    result.update(success=(exit_code == 0 and result['phases']['train'].get('receipt_verified') is True),
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
    args = parser.parse_args()
    offline = args.mode == 'offline'
    if offline:
        root = args.root
        if root is None or ADAPTER/'checks' not in root.parents:
            raise GateClosed('offline root outside adapter checks')
        profile = {'python': sys.executable, 'gpu_uuid': 'GPU-offline-fixture'}
        manifest_sha = generic.sha(ADAPTER/'tests/toy_science.py')
    else:
        root = RUN
        profile = strict_json(generic.safe(root, args.profile, True))
        admitted = require_production(profile, root)
        if sys.platform != 'linux' or os.uname().nodename != '<COMPUTE_HOST>' or os.getuid() != 1012:
            raise GateClosed('target Linux <COMPUTE_HOST> UID identity mismatch')
        manifest_sha = admitted['manifest_sha256']
    env = generic.environment(root, profile['python'], gpu_uuid=profile['gpu_uuid'])
    generic.prepare_environment_dirs(root, env)
    # Optional shim has a separate runtime artifact manifest and formal binding;
    # the fixed four-file scientific manifest remains unchanged.
    if not offline and profile.get('compatibility_preload'):
        path = runtime_preload(profile, admitted, root)
        env['LD_PRELOAD'] = str(path)
    context = {'root': root, 'run_id': RUN.name, 'offline': offline, 'environment': env,
               'gpu_uuid': profile['gpu_uuid'], 'manifest_sha256': manifest_sha,
               'observed_workers': {}, 'profile_path': args.profile}
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
