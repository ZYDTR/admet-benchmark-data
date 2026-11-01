"""Finite sequential six-run owner. Lifetime lock and conservative reservations."""
import argparse
import datetime
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapter_common import ADAPTER, RUN, generic, process_identity, strict_json, write
from admission import GateClosed, require_production
from process_state import signal_exact


def query(root, run_specs=None):
    result = {'state': 'reconcile_existing_no_start', 'root': str(root), 'runs': [], 'liveness': []}
    state = root/'state/batch-state.json'
    if state.exists():
        result['batch'] = strict_json(generic.safe(root, state, True))
        for record in result['batch'].get('runs', []):
            prior = record.get('identity')
            if prior is None:
                result['liveness'].append({'run_id': record['run_id'], 'state': 'launch_identity_unknown_no_restart'})
                continue
            try:
                current = process_identity(prior['pid'])
            except (ProcessLookupError, FileNotFoundError):
                item = {'pid': prior['pid'], 'state': 'absent_now_not_historical_exit_proof'}
            except OSError as error:
                item = {'pid': prior['pid'], 'state': 'unknown', 'error': repr(error)}
            else:
                item = {'pid': prior['pid'], 'expected': prior, 'current': current,
                        'state': 'matching_identity' if prior['start_ticks'] == current['start_ticks']
                                 and prior['pgid'] == current['pgid'] else 'identity_mismatch_no_admission'}
            result['liveness'].append(item)
    run_specs = run_specs or strict_json(ADAPTER/'batch-registration.json')['runs']
    for run_id in run_specs:
        child = Path(run_id['root']) if 'root' in run_id else root/'runs'/run_id['run_id']
        if not child.exists():
            continue
        record = {'run_id': run_id['run_id'], 'locks': sorted(p.name for p in (child/'state').glob('*.lock'))}
        for name in ('raw/job-wait-exit.json', 'raw/attempt-01/pipeline-exit.json'):
            p = child/name
            if p.exists():
                record[name] = strict_json(generic.safe(child, p, True))
        result['runs'].append(record)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('offline', 'production', 'query'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--dispatch', type=Path)
    parser.add_argument('--offline-budget-seconds', type=float, default=5400)
    parser.add_argument('--offline-case', default='success', choices=('success', 'train_exit7', 'preflight_timeout'))
    args = parser.parse_args()
    root = args.root
    registration = strict_json(ADAPTER/'batch-registration.json')
    offline = args.mode == 'offline' or (args.mode == 'query' and RUN/'raw/offline' in root.parents)
    if offline:
        if RUN/'raw/offline' not in root.parents:
            raise GateClosed('offline/query root outside current runtime fixtures')
        budget = args.offline_budget_seconds
        deadline = time.time()+budget
    else:
        if args.dispatch is None:
            raise GateClosed('main batch execution dispatch absent')
        dispatch = strict_json(args.dispatch)
        if (dispatch.get('execution_enabled') is not True or dispatch.get('cycle_id') != registration['cycle_id']
                or dispatch.get('batch_root') != str(root) or dispatch.get('max_learning_starts') != 6
                or dispatch.get('max_concurrent_jobs') != 1 or not dispatch.get('message_id')
                or dispatch.get('origin_thread_id') != 'private-role-298cc5edc25e'):
            raise GateClosed('exact main batch dispatch required')
        if not str(root).startswith('<AUTHORIZED_PROJECT_ROOT>/admet/') or root.resolve(strict=True) != root:
            raise GateClosed('batch root identity outside approved target')
        if sys.platform != 'linux' or os.uname().nodename != 'private-compute' or os.getuid() != 1012:
            raise GateClosed('target identity mismatch')
        budget, deadline = 5400, float(dispatch['deadline_epoch_seconds'])
        if not time.time() < deadline <= datetime.datetime.fromisoformat('2026-11-01T14:50:04.502622+00:00').timestamp():
            raise GateClosed('original cycle deadline expired or extended')
        runtime_spec = dispatch['runtime_source_manifest']
        runtime_path = generic.safe(root, root/runtime_spec['path'], True)
        if generic.sha(runtime_path) != runtime_spec['sha256']:
            raise GateClosed('batch runtime source manifest drift')
        runtime = strict_json(runtime_path)
        if runtime['cycle_id'] != registration['cycle_id']:
            raise GateClosed('batch source cycle mismatch')
        for item in runtime['files']:
            p = generic.safe(root, root/item['path'], True)
            if generic.sha(p) != item['sha256'] or p.stat().st_size != item['size']:
                raise GateClosed('batch runtime code drift: '+item['path'])
        if [x['run_id'] for x in dispatch['runs']] != [x['run_id'] for x in registration['runs']]:
            raise GateClosed('batch order/identity mismatch')
        for item in dispatch['runs']:
            child = Path(item['root'])
            if child.name != item['run_id'] or child.parent != Path('<AUTHORIZED_PROJECT_ROOT>/admet'):
                raise GateClosed('per-run root mismatch')
            profile_path = generic.safe(child, child/item['profile'], True)
            if generic.sha(profile_path) != item['profile_sha256']:
                raise GateClosed('per-run profile drift')
            require_production(strict_json(profile_path), child)
    if not 0 < budget <= 5400:
        raise GateClosed('batch budget outside fixed total')
    if args.mode == 'query':
        print(json.dumps(query(root, None if offline else dispatch['runs'])))
        return 0
    generic.safe(root, root, True)
    state_root = generic.safe(root, root/'state')
    state_root.mkdir(exist_ok=True)
    lock = generic.safe(root, state_root/'batch-lifetime.lock')
    try:
        with lock.open('x') as stream:
            json.dump({'at': generic.now(), 'identity': process_identity(os.getpid()), 'cycle_id': registration['cycle_id']}, stream)
    except FileExistsError:
        print(json.dumps(query(root, None if offline else dispatch['runs'])))
        return 73
    ledger = {'cycle_id': registration['cycle_id'], 'offline_fixture': args.mode == 'offline',
              'state': 'running', 'spent_seconds': 0., 'active_reservation_seconds': 0., 'runs': []}
    write(root, state_root/'batch-state.json', ledger)
    exit_code = 0
    for index, item in enumerate(registration['runs']):
        remaining = min(budget-ledger['spent_seconds'], deadline-time.time())
        if remaining <= 5:
            exit_code, ledger['state'] = 124, 'budget_expired'
            break
        allocation = min(965, remaining)
        child_root = root/'runs'/item['run_id'] if args.mode == 'offline' else Path(dispatch['runs'][index]['root'])
        if args.mode == 'offline':
            generic.safe(root, child_root).mkdir(parents=True, exist_ok=True)
            (child_root/'source').mkdir()
            (child_root/'source/config.json').write_text(json.dumps({'run_id': item['run_id'], 'monitor': item['monitor'],
                 'model_seed': item['model_seed'], 'split_seed': 43, 'fixture_case': args.offline_case})+'\n')
            command = [sys.executable, '-I', '-B', str(ADAPTER/'job_waiter.py'), 'offline',
                       '--root', str(child_root), '--case', args.offline_case]
            python, gpu = sys.executable, None
        else:
            spec = dispatch['runs'][index]
            profile_path = child_root/spec['profile']
            profile = strict_json(profile_path)
            python, gpu = profile['python'], profile['gpu_uuid']
            command = [python, '-I', '-B', str(child_root/'source/production-adapter-v2/job_waiter.py'),
                       'production', '--profile', str(profile_path)]
        command += ['--remaining-budget-seconds', str(min(960, allocation-5))]
        record = {'run_id': item['run_id'], 'state': 'launching_unknown_until_recorded', 'at': generic.now(),
                  'root': str(child_root), 'allocation_seconds': allocation}
        ledger['runs'].append(record)
        ledger['active_reservation_seconds'] = allocation
        write(root, state_root/'batch-state.json', ledger)
        env = generic.environment(child_root, python, gpu_uuid=gpu)
        generic.prepare_environment_dirs(child_root, env)
        started = time.monotonic()
        with generic.safe(child_root, child_root/'batch-child.log').open('xb') as log:
            process = subprocess.Popen(command, env=env, cwd=child_root, stdout=log,
                                       stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
            identity = process_identity(process.pid)
            record.update(state='running', identity=identity)
            write(root, state_root/'batch-state.json', ledger)
            def cancel(signum, frame):
                if process.poll() is None:
                    signal_exact(identity, signum, direct_child=process)
            for signum in (signal.SIGTERM, signal.SIGINT):
                signal.signal(signum, cancel)
            try:
                code = process.wait(timeout=allocation-2)
            except subprocess.TimeoutExpired:
                # Signal only the held exact waiter; it cooperatively cancels its
                # own pipeline. No shared UID/group/process-name cleanup.
                signal_exact(identity, signal.SIGTERM, direct_child=process)
                process.wait(timeout=2)
                code = 124
        elapsed = time.monotonic()-started
        ledger['spent_seconds'] += elapsed
        ledger['active_reservation_seconds'] = 0.
        record.update(state='completed' if code == 0 else 'failed', actual_OS_exit=code,
                      elapsed_seconds=elapsed, finished_at=generic.now())
        write(root, state_root/'batch-state.json', ledger)
        if code != 0:
            exit_code, ledger['state'] = (128-code if code < 0 else code), 'failed_needs_main'
            break
    if exit_code == 0:
        ledger['state'] = 'completed'
    ledger['actual_OS_exit'] = exit_code
    ledger['finished_at'] = generic.now()
    write(root, state_root/'batch-state.json', ledger)
    print(json.dumps(ledger))
    return exit_code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except GateClosed as error:
        print(json.dumps({'state': 'production_gate_closed', 'reason': str(error)}))
        raise SystemExit(78)
