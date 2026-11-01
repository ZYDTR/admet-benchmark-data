"""Stage-one supervisor: only real local fake subprocesses can be launched.

The reusable core propagates terminal status to its caller via SystemExit.
Scientific execution is deliberately unavailable until a later reviewed binding.
No shell, SSH, GPU command, scientific import, or old runtime is executed here.
"""
import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time
import traceback
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_guarded import environment, now, prepare_environment_dirs, safe, write_json

RUN_ROOT = Path(__file__).resolve().parents[2]
EXIT_TIMEOUT = 124
EXIT_CHECK_FAILED = 125
EXIT_UNKNOWN = 126
EXIT_EVIDENCE_FAILED = 70
EXIT_DUPLICATE = 73
EXIT_GATE_CLOSED = 78


def shell_exit(returncode):
    return 128-returncode if returncode < 0 else returncode


def identity(pid):
    value = {'pid': pid, 'pgid': os.getpgid(pid), 'observed_at': now()}
    proc_stat = Path('/proc')/str(pid)/'stat'
    if proc_stat.exists():
        value['start_stat'] = proc_stat.read_text()
        # The comm field can contain spaces/parentheses; fields after last ')'.
        value['start_ticks'] = value['start_stat'].rsplit(')', 1)[1].split()[19]
    return value


def stop_own_child(child, launched_identity):
    """Only the exact Popen session we created, while leader identity matches."""
    if child.poll() is not None:
        return {'signalled': False, 'child_returncode': child.returncode}
    current = identity(child.pid)
    if current['pgid'] != child.pid:
        raise RuntimeError('own process-group identity mismatch; stop refused')
    if current.get('start_ticks') != launched_identity.get('start_ticks'):
        raise RuntimeError('own process start identity mismatch; stop refused')
    os.killpg(child.pid, signal.SIGTERM)
    escalated = False
    try:
        child.wait(timeout=1)
    except subprocess.TimeoutExpired:
        # Leader is still alive; revalidate before escalation.
        if identity(child.pid).get('start_ticks') != launched_identity.get('start_ticks'):
            raise RuntimeError('own process identity changed; escalation refused')
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=2)
        escalated = True
    return {'signalled': True, 'escalated': escalated,
            'child_returncode': child.returncode}


def supervise(attempt, command_factory, precheck, monitor, verify_completion,
              timeout_seconds, cancelled):
    """Every known terminal branch writes its actual outer exit before return.

    Evidence persistence failure returns 70 and emits a stderr diagnostic;
    it cannot promise a status file when storage itself has failed.
    """
    safe(RUN_ROOT, attempt, True)
    token = uuid.uuid4().hex
    started = time.monotonic()
    status = {'schema_version': 1, 'run_id': RUN_ROOT.name, 'offline_fake_task': True,
              'training_started': False, 'token': token, 'started_at': now(),
              'state': 'prechecking', 'success': False, 'verification': 'unknown',
              'supervisor_exit_code': None, 'child_returncode': None,
              'child_identity': None, 'completion_verified': False,
              'cleanup': None, 'reason': None}
    child, launched = None, None

    def event(kind, **fields):
        path = safe(RUN_ROOT, attempt/'events.jsonl')
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'at': now(), 'kind': kind, **fields})+'\n')
            stream.flush()
            os.fsync(stream.fileno())

    exit_code, state, verification = EXIT_CHECK_FAILED, 'check_failed', 'failed'
    try:
        write_json(RUN_ROOT, attempt/'status.json', status)
        event('precheck_started')
        precheck()
        event('precheck_passed')
        if cancelled['signal'] is not None:
            raise InterruptedError('cancelled before launch')
        env = environment(attempt, sys.executable, cpu_threads=2)
        prepare_environment_dirs(attempt, env)
        command = command_factory(token)
        with safe(RUN_ROOT, attempt/'child.log').open('xb') as log:
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log,
                                     stderr=subprocess.STDOUT, cwd=attempt, env=env,
                                     start_new_session=True)
            launched = identity(child.pid)
            status.update(state='running', child_identity=launched, command=command)
            write_json(RUN_ROOT, attempt/'status.json', status)
            event('launched', **launched)
            while True:
                if cancelled['signal'] is not None:
                    exit_code = 128+cancelled['signal']
                    state, verification = 'cancelled', 'failed'
                    status['reason'] = 'supervisor received signal'
                    break
                # Monitoring failure remains a failure even if child concurrently exits 0.
                observation = monitor(child)
                event('observed', **observation)
                # A delayed observation cannot turn an over-budget child into success.
                if time.monotonic()-started >= timeout_seconds:
                    exit_code, state, verification = EXIT_TIMEOUT, 'timed_out', 'failed'
                    status['reason'] = 'wall timeout'
                    break
                returncode = child.poll()
                if returncode is not None:
                    if returncode != 0:
                        exit_code, state = shell_exit(returncode), 'child_failed'
                        verification = 'failed'
                        status['reason'] = 'nonzero child returncode'
                    else:
                        exit_code, state, verification = EXIT_UNKNOWN, 'unknown', 'unknown'
                        try:
                            verify_completion(token, child.pid)
                        except (OSError, ValueError, KeyError, TypeError) as error:
                            status['reason'] = 'completion unverified: '+str(error)
                        else:
                            status['completion_verified'] = True
                            exit_code, state, verification = 0, 'succeeded', 'passed'
                    break
                time.sleep(0.03)
    except Exception as error:
        state = 'precheck_failed' if child is None else 'monitor_or_launch_failed'
        exit_code, verification = EXIT_CHECK_FAILED, 'failed'
        if isinstance(error, InterruptedError) and cancelled['signal'] is not None:
            exit_code, state = 128+cancelled['signal'], 'cancelled'
        status['reason'] = type(error).__name__+': '+str(error)
        status['exception'] = traceback.format_exc()
    finally:
        try:
            if child is not None:
                status['cleanup'] = stop_own_child(child, launched)
                status['child_returncode'] = child.wait(timeout=2)
            status.update(state=state, verification=verification,
                          supervisor_exit_code=exit_code,
                          success=(exit_code == 0 and status['completion_verified']),
                          finished_at=now(), elapsed_seconds=time.monotonic()-started)
            event('terminal', state=state, supervisor_exit_code=exit_code,
                  child_returncode=status['child_returncode'], success=status['success'])
            write_json(RUN_ROOT, attempt/'status.json', status)
        except Exception as error:
            # Best effort diagnostic; never publish stale running status as success.
            exit_code = EXIT_EVIDENCE_FAILED
            status.update(state='evidence_or_cleanup_failed', success=False,
                          verification='unknown', supervisor_exit_code=exit_code,
                          reason=type(error).__name__+': '+str(error))
            print(json.dumps(status), file=sys.stderr, flush=True)
            try:
                write_json(RUN_ROOT, attempt/'status.json', status)
            except Exception:
                pass
    print(json.dumps(status), flush=True)
    return exit_code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('offline', 'scientific'))
    parser.add_argument('--attempt', type=Path, required=True)
    parser.add_argument('--case', default='success', choices=(
        'success', 'exit7', 'exception', 'timeout', 'missing_receipt',
        'wrong_token', 'malformed_receipt', 'precheck_failure',
        'monitor_failure', 'signal_child', 'slow_success'))
    parser.add_argument('--timeout', type=float, default=3)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 10:
        parser.error('offline timeout must be finite and within (0,10] seconds')
    attempt = safe(RUN_ROOT, args.attempt)
    allowed_root = RUN_ROOT/'raw/local-runtime-checks'
    if allowed_root not in attempt.parents:
        raise ValueError('stage one writes only inside raw/local-runtime-checks')
    # mkdir(exist_ok=False) is the exclusive launch lock; never reclaim it here.
    try:
        attempt.mkdir()
    except FileExistsError:
        print(json.dumps({'state': 'existing_attempt_query_original',
                          'supervisor_exit_code': EXIT_DUPLICATE,
                          'attempt': str(attempt), 'success': False}), flush=True)
        return EXIT_DUPLICATE
    write_json(RUN_ROOT, attempt/'launch-lock.json',
               {'at': now(), 'run_id': RUN_ROOT.name, 'supervisor': identity(os.getpid()),
                'stage': args.stage, 'case': args.case})
    if args.stage == 'scientific':
        # Deliberately no code path that reads/launches a scientific delivery.
        value = {'state': 'stage_one_gate_closed', 'success': False,
                 'verification': 'not_authorized_in_stage_one',
                 'supervisor_exit_code': EXIT_GATE_CLOSED, 'child_returncode': None,
                 'training_started': False, 'remote_operations_performed': False,
                 'reason': 'requires separate main acceptance, manifest binding and formal dispatch'}
        write_json(RUN_ROOT, attempt/'status.json', value)
        print(json.dumps(value), flush=True)
        return EXIT_GATE_CLOSED

    cancelled = {'signal': None}
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda signum, frame: cancelled.update(signal=signum))
    profile_path = RUN_ROOT/'source/runtime/runtime-profile.json'

    def precheck():
        profile = json.loads(profile_path.read_text())
        if (profile['run_id'] != RUN_ROOT.name
                or profile['stage'] != 'local_preparation_only'
                or profile['remote_operations_enabled'] is not False
                or profile['training_enabled'] is not False):
            raise ValueError('stage-one profile identity/gate mismatch')
        if args.case == 'precheck_failure':
            raise RuntimeError('injected environment check failed')

    def monitor(child):
        if args.case == 'monitor_failure':
            raise RuntimeError('injected observation unavailable')
        return {'child_pid': child.pid, 'gpu_observed': False,
                'resource_enforcement_verified': False}

    def verify_completion(token, pid):
        value = json.loads(safe(RUN_ROOT, attempt/'completion.json', True).read_text())
        if (value.get('token') != token or value.get('pid') != pid
                or value.get('run_id') != RUN_ROOT.name
                or value.get('status') != 'success'
                or value.get('offline_fake_task') is not True):
            raise ValueError('receipt identity/status mismatch')

    def command_factory(token):
        worker = safe(RUN_ROOT, RUN_ROOT/'tests/fake_worker.py', True)
        return [sys.executable, '-I', '-B', '-u', str(worker), args.case,
                str(attempt), token, RUN_ROOT.name]

    return supervise(attempt, command_factory, precheck, monitor, verify_completion,
                     args.timeout, cancelled)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise SystemExit(EXIT_EVIDENCE_FAILED)
