"""Shared real-process supervision for preflight and train; no shell or transport."""
import json
import os
import signal
import subprocess
import time
import traceback

from adapter_common import generic, process_identity, write
from completion import verify_receipt


def stop_own(child, original):
    if child.poll() is not None:
        return {'signalled': False, 'leader_reaped': True}
    current = process_identity(child.pid)
    if current['pgid'] != child.pid or current.get('start_ticks') != original.get('start_ticks'):
        raise RuntimeError('own child identity drift; signal refused')
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=1)
    except subprocess.TimeoutExpired:
        current = process_identity(child.pid)
        if current.get('start_ticks') != original.get('start_ticks'):
            raise RuntimeError('own child identity drift before escalation')
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=2)
    return {'signalled': True, 'leader_reaped': True}


def run_phase(context, phase, token, command, precheck, monitor, timeout, cancelled):
    root = context['root']
    attempt = context['attempt_root']/phase
    generic.safe(root, attempt).mkdir()
    started = time.monotonic()
    status = {'run_id': context['run_id'], 'phase': phase, 'token': token,
              'offline_fixture': context['offline'], 'state': 'prechecking',
              'success': False, 'child_returncode': None, 'supervisor_exit_code': None,
              'child_identity': None, 'receipt_verified': False, 'at': generic.now()}
    child, original, rc, state = None, None, 125, 'precheck_failed'
    def event(kind, **fields):
        with generic.safe(root, attempt/'events.jsonl').open('a') as stream:
            stream.write(json.dumps({'at': generic.now(), 'kind': kind, **fields})+'\n')
            stream.flush()
            os.fsync(stream.fileno())
    try:
        write(root, attempt/'status.json', status)
        precheck()
        event('precheck_passed')
        if cancelled['signal'] is not None:
            raise InterruptedError('cancelled before child launch')
        with generic.safe(root, attempt/'child.log').open('xb') as log:
            child = subprocess.Popen(command, cwd=root, env=context['environment'],
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                     start_new_session=True)
            original = process_identity(child.pid)
            status.update(state='running', child_identity=original, command=command)
            write(root, attempt/'status.json', status)
            event('launched', **original)
            while True:
                if cancelled['signal'] is not None:
                    rc, state = 128+cancelled['signal'], 'cancelled'
                    break
                observation = monitor(child)
                event('observed', **observation)
                if time.monotonic()-started >= timeout:
                    rc, state = 124, 'timed_out'
                    break
                code = child.poll()
                if code is not None:
                    if code != 0:
                        rc, state = (128-code if code < 0 else code), 'child_failed'
                    else:
                        rc, state = 126, 'completion_unknown'
                        try:
                            receipt = verify_receipt(root, attempt, phase, context['run_id'],
                                                     token, child.pid, context['manifest_sha256'],
                                                     context['gpu_uuid'], context['offline'])
                            if (not context['offline'] and context['observed_workers'].get(phase)
                                    != receipt['worker_identity']):
                                raise ValueError('production worker was not independently observed alive')
                        except (OSError, ValueError, KeyError, TypeError) as error:
                            status['reason'] = str(error)
                        else:
                            status['receipt_verified'] = True
                            status['worker_identity'] = receipt['worker_identity']
                            status['receipt_sha256'] = generic.sha(attempt/'adapter-complete.json')
                            rc, state = 0, 'succeeded'
                    break
                time.sleep(0.02)
    except Exception as error:
        rc, state = 125, ('precheck_failed' if child is None else 'monitor_or_launch_failed')
        if cancelled['signal'] is not None:
            rc, state = 128+cancelled['signal'], 'cancelled'
        status['reason'] = type(error).__name__+': '+str(error)
        status['exception'] = traceback.format_exc()
    finally:
        try:
            if child is not None:
                status['cleanup'] = stop_own(child, original)
                status['child_returncode'] = child.wait(timeout=2)
            status.update(state=state, supervisor_exit_code=rc, success=(rc == 0),
                          finished_at=generic.now(), elapsed_seconds=time.monotonic()-started)
            event('terminal', exit_code=rc, child_returncode=status['child_returncode'], state=state)
            write(root, attempt/'status.json', status)
        except Exception as error:
            rc = 70
            status.update(state='evidence_or_cleanup_failed', supervisor_exit_code=rc,
                          success=False, reason=type(error).__name__+': '+str(error))
            try:
                write(root, attempt/'status.json', status)
            except Exception:
                pass
    return rc, status
