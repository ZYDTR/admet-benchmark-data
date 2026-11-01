"""Actual finite waiter OS exit propagation; only fixed toy subprocesses."""
import datetime
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

ADAPTER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADAPTER))
from adapter_common import RUN, generic, strict_json


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def main():
    suite = ADAPTER/'checks'/('waiter-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    suite.mkdir()
    results = []
    for name, case, expected, cancel in (('success', 'success', 0, False),
                                        ('child_exit7', 'train_exit7', 7, False),
                                        ('timeout', 'train_timeout', 124, False),
                                        ('precheck', 'preflight_check_failure', 125, False),
                                        ('missing_receipt', 'missing_adapter_receipt', 126, False),
                                        ('cancel', 'train_timeout', 143, True)):
        root = suite/name
        (root/'source').mkdir(parents=True)
        save(root/'source/config.json', {'run_id': RUN.name, 'fixture_case': case,
                                         'monitor': 'internal_validation_raw_mae'})
        env = generic.environment(root, sys.executable)
        generic.prepare_environment_dirs(root, env)
        command = [sys.executable, '-I', '-B', str(ADAPTER/'job_waiter.py'), 'offline',
                   '--root', str(root), '--case', case]
        process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if cancel:
            deadline = time.monotonic()+3
            while time.monotonic() < deadline:
                status = root/'raw/attempt-01/train/status.json'
                if status.exists() and strict_json(status).get('child_identity'):
                    process.send_signal(signal.SIGTERM)
                    break
                if process.poll() is not None:
                    raise AssertionError('waiter ended before cancellation')
                time.sleep(.01)
            else:
                process.terminate()
                raise AssertionError('fixture train did not launch for cancellation')
        stdout, stderr = process.communicate(timeout=10)
        save(root/'outer-process.json', {'command': command, 'returncode': process.returncode,
                                          'stdout': stdout, 'stderr': stderr})
        assert process.returncode == expected, (name, process.returncode, stdout, stderr)
        wait = strict_json(root/'raw/job-wait-exit.json')
        pipeline = strict_json(root/'raw/attempt-01/pipeline-exit.json')
        assert wait['actual_os_exit_code'] == pipeline['supervisor_exit_code'] == expected
        assert pipeline['training_started'] is False and pipeline['training_completed'] is False
        for phase in pipeline['phases'].values():
            if phase.get('child_identity'):
                try:
                    os.kill(phase['child_identity']['pid'], 0)
                except ProcessLookupError:
                    pass
                else:
                    raise AssertionError('fixture child not reaped')
        if name == 'success':
            before = generic.sha(root/'raw/job-wait-exit.json')
            replay = subprocess.run(command, env=env, capture_output=True, text=True, timeout=5)
            assert replay.returncode == 73 and generic.sha(root/'raw/job-wait-exit.json') == before
            save(root/'replay.json', {'returncode': replay.returncode, 'exit_evidence_unchanged': True})
        results.append({'case': name, 'passed': True, 'actual_os_exit_code': expected})
    closed = subprocess.run([sys.executable, '-I', '-B', str(ADAPTER/'job_waiter.py'), 'production'],
                            capture_output=True, text=True, timeout=5)
    assert closed.returncode == 78
    save(suite/'closed-production.json', {'returncode': closed.returncode, 'stdout': closed.stdout})
    report = {'passed': True, 'checks': 8, 'six_actual_waiter_cases': results,
              'replay_lock': True, 'production_disabled_exit': 78,
              'actual_scientific_main_called': False, 'parameter_updates': 0, 'remote_operations': False}
    save(suite/'result.json', report)
    print(json.dumps({'passed': True, 'evidence': str(suite/'result.json'), 'checks': report['checks']}))


if __name__ == '__main__':
    main()
