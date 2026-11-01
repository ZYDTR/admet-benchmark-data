"""Real outer-supervisor/inner-child checks. All evidence remains inside this run.

Run with python3 -I -B <this file>; no pytest, network, GPU or science imports.
Each invocation has a new suite directory. No old attempts are overwritten.
"""
import datetime
import json
import os
import signal
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path

RUN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN_ROOT/'source/runtime'))
from common_guarded import environment, prepare_environment_dirs, safe, sha, write_json
from readonly_recovery import TransientConnectionError, recover_read_only
from resource_checks import enforce_observation, validate_idle_gpu
from linux_boundary import trace_command

SUITE = RUN_ROOT/'raw/local-runtime-checks'/('suite-' + datetime.datetime.now(
    datetime.timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
SUPERVISOR = RUN_ROOT/'source/runtime/supervisor.py'


class RuntimeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SUITE.mkdir()
        cls.results = []
        cls.env_root = SUITE/'outer-environment'
        cls.env_root.mkdir()
        cls.env = environment(cls.env_root, sys.executable)
        prepare_environment_dirs(cls.env_root, cls.env)

    def argv(self, name, case='success', timeout=3, stage='offline'):
        return [sys.executable, '-I', '-B', '-u', str(SUPERVISOR), stage,
                '--attempt', str(SUITE/name), '--case', case, '--timeout', str(timeout)]

    def check_case(self, name, case, expected_code, expected_state, timeout=3, stage='offline'):
        started = time.monotonic()
        process = subprocess.run(self.argv(name, case, timeout, stage),
                                 capture_output=True, text=True, env=self.env,
                                 cwd=RUN_ROOT, timeout=15)
        evidence = {'command': self.argv(name, case, timeout, stage),
                    'outer_returncode': process.returncode,
                    'stdout': process.stdout, 'stderr': process.stderr,
                    'elapsed_seconds': time.monotonic()-started}
        write_json(RUN_ROOT, SUITE/(name+'-outer-result.json'), evidence)
        self.assertEqual(process.returncode, expected_code, evidence)
        status = json.loads((SUITE/name/'status.json').read_text())
        self.assertEqual(status['supervisor_exit_code'], process.returncode)
        self.assertEqual(status['state'], expected_state)
        self.assertEqual(status['success'], expected_code == 0)
        self.assertIs(status['training_started'], False)
        self.results.append({'case': name, 'passed': True,
                             'outer_returncode': process.returncode,
                             'state': status['state'],
                             'status_path': str((SUITE/name/'status.json').relative_to(RUN_ROOT))})
        return status

    def assert_child_gone(self, status):
        pid = status['child_identity']['pid']
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_success_has_matching_fresh_receipt(self):
        value = self.check_case('success', 'success', 0, 'succeeded')
        self.assertEqual(value['child_returncode'], 0)
        self.assertIs(value['completion_verified'], True)
        self.assert_child_gone(value)

    def test_nonzero_child_propagates(self):
        value = self.check_case('exit7', 'exit7', 7, 'child_failed')
        self.assertEqual(value['child_returncode'], 7)
        self.assertIs(value['completion_verified'], False)

    def test_child_exception_propagates(self):
        value = self.check_case('exception', 'exception', 1, 'child_failed')
        self.assertEqual(value['child_returncode'], 1)
        self.assertIn('intentional toy-child failure', (SUITE/'exception/child.log').read_text())

    def test_timeout_propagates_and_reaps_own_child(self):
        value = self.check_case('timeout', 'timeout', 124, 'timed_out', timeout=0.4)
        self.assertIs(value['cleanup']['signalled'], True)
        self.assertNotEqual(value['child_returncode'], 0)
        self.assert_child_gone(value)

    def test_zero_child_without_receipt_is_unknown(self):
        value = self.check_case('missing', 'missing_receipt', 126, 'unknown')
        self.assertEqual(value['child_returncode'], 0)
        self.assertEqual(value['verification'], 'unknown')

    def test_zero_child_with_wrong_receipt_is_unknown(self):
        self.check_case('wrong-token', 'wrong_token', 126, 'unknown')

    def test_zero_child_with_malformed_receipt_is_unknown(self):
        self.check_case('malformed', 'malformed_receipt', 126, 'unknown')

    def test_precheck_failure_never_launches_child(self):
        value = self.check_case('precheck', 'precheck_failure', 125, 'precheck_failed')
        self.assertIsNone(value['child_identity'])
        self.assertIsNone(value['child_returncode'])
        self.assertFalse((SUITE/'precheck/child-started.json').exists())
        self.assertFalse((SUITE/'precheck/child.log').exists())

    def test_monitor_failure_propagates_and_reaps(self):
        value = self.check_case('monitor', 'monitor_failure', 125, 'monitor_or_launch_failed')
        self.assertIs(value['cleanup']['signalled'], True)
        self.assert_child_gone(value)

    def test_child_signal_preserves_raw_and_shell_codes(self):
        value = self.check_case('signal-child', 'signal_child', 143, 'child_failed')
        self.assertEqual(value['child_returncode'], -signal.SIGTERM)

    def test_supervisor_signal_is_nonzero_and_reaps(self):
        name = 'signal-supervisor'
        process = subprocess.Popen(self.argv(name, 'timeout'), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, env=self.env, cwd=RUN_ROOT)
        try:
            deadline = time.monotonic()+5
            while not (SUITE/name/'child-started.json').exists():
                self.assertIsNone(process.poll())
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.02)
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=5)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)
        write_json(RUN_ROOT, SUITE/(name+'-outer-result.json'),
                   {'outer_returncode': process.returncode, 'stdout': stdout, 'stderr': stderr})
        value = json.loads((SUITE/name/'status.json').read_text())
        self.assertEqual(process.returncode, 143)
        self.assertEqual(value['supervisor_exit_code'], 143)
        self.assertEqual(value['state'], 'cancelled')
        self.assertIs(value['success'], False)
        self.assert_child_gone(value)
        self.results.append({'case': name, 'passed': True, 'outer_returncode': 143,
                             'status_path': str((SUITE/name/'status.json').relative_to(RUN_ROOT))})

    def test_duplicate_lock_keeps_original_and_never_replays(self):
        self.check_case('duplicate', 'success', 0, 'succeeded')
        before = {p.name: sha(p) for p in (SUITE/'duplicate').iterdir() if p.is_file()}
        duplicate = subprocess.run(self.argv('duplicate'), capture_output=True,
                                   text=True, env=self.env, cwd=RUN_ROOT, timeout=5)
        write_json(RUN_ROOT, SUITE/'duplicate-replay-result.json',
                   {'outer_returncode': duplicate.returncode, 'stdout': duplicate.stdout,
                    'stderr': duplicate.stderr})
        self.assertEqual(duplicate.returncode, 73)
        self.assertEqual(json.loads(duplicate.stdout)['state'], 'existing_attempt_query_original')
        self.assertEqual(before, {p.name: sha(p) for p in (SUITE/'duplicate').iterdir() if p.is_file()})

    def test_scientific_launch_stays_closed(self):
        value = self.check_case('science-gate', 'success', 78, 'stage_one_gate_closed', stage='scientific')
        self.assertIsNone(value['child_returncode'])
        self.assertFalse((SUITE/'science-gate/child.log').exists())

    def test_active_attempt_cannot_be_resubmitted(self):
        name = 'active-duplicate'
        process = subprocess.Popen(self.argv(name, 'slow_success'), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, env=self.env, cwd=RUN_ROOT)
        try:
            deadline = time.monotonic()+5
            while not (SUITE/name/'child-started.json').exists():
                self.assertIsNone(process.poll())
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.01)
            lock_hash = sha(SUITE/name/'launch-lock.json')
            duplicate = subprocess.run(self.argv(name), capture_output=True,
                                       text=True, env=self.env, cwd=RUN_ROOT, timeout=5)
            self.assertEqual(duplicate.returncode, 73)
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0)
            value = json.loads((SUITE/name/'status.json').read_text())
            self.assertEqual(value['supervisor_exit_code'], 0)
            self.assertIs(value['success'], True)
            self.assertEqual(lock_hash, sha(SUITE/name/'launch-lock.json'))
            events = [json.loads(line) for line in (SUITE/name/'events.jsonl').read_text().splitlines()]
            self.assertEqual(sum(event['kind'] == 'launched' for event in events), 1)
            write_json(RUN_ROOT, SUITE/(name+'-outer-result.json'),
                       {'outer_returncode': process.returncode, 'stdout': stdout, 'stderr': stderr,
                        'duplicate_returncode': duplicate.returncode,
                        'duplicate_stdout': duplicate.stdout})
            self.results.append({'case': name, 'passed': True, 'outer_returncode': 0,
                                 'duplicate_returncode': 73,
                                 'status_path': str((SUITE/name/'status.json').relative_to(RUN_ROOT))})
        finally:
            if process.poll() is None:
                process.terminate()
                process.communicate(timeout=5)

    def test_readonly_transient_recovery_requires_validation(self):
        calls, waits, events, validations = [], [], [], []
        def query(action):
            calls.append(action)
            if len(calls) < 3:
                raise TransientConnectionError('connection_reset', 255)
            return {'identity': 'fixture'}
        def validate(value):
            validations.append(value)
        value = recover_read_only('identity', query, validate, waits.append,
                                  events.append, {'run_id': RUN_ROOT.name, 'stage': 'identity'})
        self.assertEqual(calls, ['identity']*3)
        self.assertEqual(waits, [2, 5])
        self.assertEqual(len(validations), 1)
        self.assertEqual([e['status'] for e in events], ['connection_failed']*2+['checks_passed'])
        self.assertEqual(value['state'], 'ready')
        write_json(RUN_ROOT, SUITE/'recovery-success.json', value)

    def test_readonly_exhaustion_preserves_waiting_context(self):
        waits, events, calls = [], [], []
        def query(action):
            calls.append(action)
            raise TransientConnectionError('registered_ssh_auth_once', 255)
        context = {'run_id': RUN_ROOT.name, 'stage': 'resources', 'original_job': None}
        value = recover_read_only('resources', query, lambda x: self.fail('no success'),
                                  waits.append, events.append, context)
        self.assertEqual(len(calls), 4)
        self.assertEqual(waits, [2, 5, 10])
        self.assertEqual(value['state'], 'waiting_for_connection')
        self.assertEqual(value['context'], context)
        self.assertIs(value['checks_passed'], False)
        self.assertIs(value['automatic_wakeup_created'], False)
        write_json(RUN_ROOT, SUITE/'recovery-exhausted.json', value)

    def test_hard_check_failure_blocks_downstream_without_retry(self):
        calls, waits, events, downstream = [], [], [], []
        def query(action):
            calls.append(action)
            return {'identity': 'wrong-host'}
        def validate(value):
            raise ValueError('host identity mismatch')
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            result = recover_read_only('identity', query, validate, waits.append,
                                       events.append, {'stage': 'identity'})
            downstream.append(result)
        self.assertEqual(calls, ['identity'])
        self.assertEqual(waits, [])
        self.assertEqual(downstream, [])
        self.assertEqual(events[-1]['status'], 'checks_failed')
        write_json(RUN_ROOT, SUITE/'recovery-hard-failure.json', {'events': events})

    def test_mutation_never_enters_generic_retries(self):
        calls = []
        for action in ('upload', 'deploy', 'start', 'training', 'arbitrary_shell'):
            with self.subTest(action=action), self.assertRaises(ValueError):
                recover_read_only(action, calls.append, calls.append, calls.append,
                                  calls.append, {'stage': 'offline'})
        self.assertEqual(calls, [])
        for reason in ('remote_file_permission', 'host_key_changed', 'account_locked'):
            with self.subTest(reason=reason), self.assertRaises(ValueError):
                raise TransientConnectionError(reason, 255)

    def test_environment_and_path_contracts(self):
        env = environment(self.env_root, sys.executable)
        self.assertEqual(env['JOBLIB_MULTIPROCESSING'], '0')
        self.assertEqual(env['CUDA_VISIBLE_DEVICES'], '')
        self.assertEqual(env['OMP_NUM_THREADS'], '2')
        self.assertNotIn('SSH_AUTH_SOCK', env)
        self.assertNotIn('PYTHONPATH', env)
        self.assertEqual(env['JOBLIB_TEMP_FOLDER'], str(self.env_root/'tmp/joblib'))
        with self.assertRaises(ValueError):
            safe(RUN_ROOT, RUN_ROOT.parent/'hainan-index-cycle-20261031-escape')
        linked = SUITE/'linked'
        linked.symlink_to(self.env_root)
        with self.assertRaises(ValueError):
            safe(RUN_ROOT, linked/'new-file')
        original = SUITE/'hardlink-original'
        original.write_text('fixture')
        os.link(original, SUITE/'hardlink-second')
        with self.assertRaises(ValueError):
            safe(RUN_ROOT, original, True)
        # Deliberate rejection fixtures remain inside suite evidence.

    def test_resource_unknown_health_and_occupancy_block(self):
        xml = '''<nvidia_smi_log><gpu><uuid>GPU-fixture</uuid><minor_number>99</minor_number>
        <gpu_recovery_action>None</gpu_recovery_action><compute_mode>Default</compute_mode>
        <mig_mode><current_mig>Disabled</current_mig></mig_mode>
        <remapped_rows><remapped_row_pending>No</remapped_row_pending><remapped_row_failure>No</remapped_row_failure></remapped_rows>
        <fb_memory_usage><used>0 MiB</used></fb_memory_usage><utilization><gpu_util>0 %</gpu_util></utilization>
        <ecc_errors><volatile><double_bit_uncorrectable>0</double_bit_uncorrectable></volatile></ecc_errors>
        </gpu></nvidia_smi_log>'''
        self.assertTrue(validate_idle_gpu(xml, '', 'GPU-fixture', 99)['healthy'])
        for bad in (xml.replace('<gpu_recovery_action>None</gpu_recovery_action>', ''),
                    xml.replace('>None<', '>Reset<'), xml.replace('>0 MiB<', '>1 MiB<')):
            with self.subTest(xml=bad), self.assertRaises(ValueError):
                validate_idle_gpu(bad, '', 'GPU-fixture', 99)
        with self.assertRaises(ValueError):
            validate_idle_gpu(xml, 'GPU-fixture,42,100\n', 'GPU-fixture', 99)
        budget = json.loads((RUN_ROOT/'source/runtime/runtime-profile.json').read_text())['resource_budget']
        obs = {'tree_rss_bytes': 1, 'result_bytes': 1, 'apps_csv': 'GPU-fixture,42,20\n'}
        self.assertTrue(enforce_observation(obs, budget, 'GPU-fixture', [42])['observation_passed'])
        with self.assertRaises(RuntimeError):
            enforce_observation(obs, budget, 'GPU-fixture', [43])
        with self.assertRaises(KeyError):
            enforce_observation({}, budget, 'GPU-fixture', [42])
        with self.assertRaises(RuntimeError):
            enforce_observation({**obs, 'tree_rss_bytes': 9*1024**3}, budget, 'GPU-fixture', [42])
        command = trace_command('/fixture/python', '/fixture/guard.py', '/fixture/trace', ['phase'])
        self.assertIn('-I', command)
        self.assertIn('-B', command)
        self.assertTrue(any('landlock_restrict_self' in x for x in command))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        'schema_version': 1, 'run_id': RUN_ROOT.name, 'suite_path': str(SUITE.relative_to(RUN_ROOT)),
        'passed': result.wasSuccessful(), 'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors),
        'test_ids': [case.id() for case in unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeChecks)],
        'subprocess_cases': getattr(RuntimeChecks, 'results', []),
        'no_gpu_no_training': True, 'remote_operations_performed': False,
        'linux_guard_executed': False, 'real_target_resource_state_verified': False,
    }
    write_json(RUN_ROOT, SUITE/'offline-validation.json', report)
    print(json.dumps(report), flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
