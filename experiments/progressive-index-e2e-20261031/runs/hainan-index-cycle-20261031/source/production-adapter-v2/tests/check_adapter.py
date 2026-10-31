"""Fixed no-GPU subprocess checks, all writes within production-adapter-v1/checks."""
import copy
import datetime
import hashlib
import json
import os
import subprocess
import sys
import types
import uuid
from pathlib import Path

ADAPTER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADAPTER))
from adapter_common import RUN, establish_environment, generic, legacy_module
from admission import GateClosed, require_production, runtime_preload


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    suite = ADAPTER/'checks'/('suite-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    suite.mkdir()
    results = []
    outer_env_root = suite/'outer-env'
    outer_env_root.mkdir()
    env = generic.environment(outer_env_root, sys.executable)
    generic.prepare_environment_dirs(outer_env_root, env)
    scenarios = (
        ('success', 0, 'succeeded', 'succeeded'),
        ('preflight_exit7', 7, 'child_failed', 'skipped_failed_preflight'),
        ('train_exit7', 7, 'succeeded', 'child_failed'),
        ('preflight_timeout', 124, 'timed_out', 'skipped_failed_preflight'),
        ('train_timeout', 124, 'succeeded', 'timed_out'),
        ('preflight_check_failure', 125, 'precheck_failed', 'skipped_failed_preflight'),
        ('preflight_missing_receipt', 126, 'completion_unknown', 'skipped_failed_preflight'),
        ('train_check_failure', 125, 'succeeded', 'precheck_failed'),
        ('monitor_failure', 125, 'monitor_or_launch_failed', 'skipped_failed_preflight'),
        ('legacy_success_only', 1, 'succeeded', 'child_failed'),
        ('missing_adapter_receipt', 126, 'succeeded', 'completion_unknown'),
        ('wrong_token', 126, 'succeeded', 'completion_unknown'),
        ('wrong_pid', 126, 'succeeded', 'completion_unknown'),
        ('wrong_manifest', 126, 'succeeded', 'completion_unknown'),
        ('artifact_tamper', 126, 'succeeded', 'completion_unknown'),
        ('stale_legacy_complete', 125, 'succeeded', 'precheck_failed'),
        ('prior_learning_record', 125, 'succeeded', 'precheck_failed'),
        ('learning_lock_exists', 125, 'succeeded', 'precheck_failed'),
    )
    for name, expected, pre_state, train_state in scenarios:
        root = suite/name
        root.mkdir()
        (root/'source').mkdir()
        save(root/'source/config.json', {'run_id': RUN.name, 'fixture_case': name})
        command = [sys.executable, '-I', '-B', str(ADAPTER/'pipeline.py'), 'offline',
                   '--root', str(root), '--case', name]
        process = subprocess.run(command, capture_output=True, text=True, env=env, timeout=15)
        save(root/'outer-process.json', {'command': command, 'returncode': process.returncode,
                                         'stdout': process.stdout, 'stderr': process.stderr})
        status = json.loads((root/'raw/attempt-v2/pipeline-exit.json').read_text())
        assert process.returncode == expected, (name, process.returncode, process.stdout, process.stderr)
        assert status['supervisor_exit_code'] == process.returncode, name
        assert status['success'] is (expected == 0), name
        assert status['training_started'] is False, name
        assert status['phases']['preflight']['state'] == pre_state, name
        assert status['phases']['train']['state'] == train_state, name
        if train_state == 'skipped_failed_preflight':
            assert not (root/'raw/attempt-v2/train').exists(), name
            assert not (root/'raw/fake-train-called.json').exists(), name
        if name in ('train_check_failure', 'stale_legacy_complete'):
            assert not (root/'raw/fake-train-called.json').exists(), name
        for phase in ('preflight', 'train'):
            value = status['phases'][phase]
            if value.get('child_identity'):
                pid = value['child_identity']['pid']
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    pass
                else:
                    raise AssertionError((name, phase, 'child not reaped'))
                actual = json.loads((root/'raw/attempt-v2'/phase/'status.json').read_text())
                assert actual['supervisor_exit_code'] == value['supervisor_exit_code']
        if name == 'success':
            for phase in ('preflight', 'train'):
                receipt = json.loads((root/'raw/attempt-v2'/phase/'adapter-complete.json').read_text())
                assert receipt['worker_identity']['pid'] == status['phases'][phase]['child_identity']['pid']
                assert receipt['run_id'] == RUN.name
                assert receipt['offline_fixture'] is True
                assert receipt['protection']['landlock_applied'] is False
            assert len(list((root/'raw').glob('import-order-*.json'))) == 2
            before = generic.sha(root/'raw/attempt-v2/pipeline-exit.json')
            replay = subprocess.run(command, capture_output=True, text=True, env=env, timeout=5)
            assert replay.returncode == 73
            assert generic.sha(root/'raw/attempt-v2/pipeline-exit.json') == before
            save(root/'duplicate-process.json', {'returncode': replay.returncode, 'stdout': replay.stdout})
        results.append({'case': name, 'passed': True, 'outer_exit': expected,
                        'preflight_state': pre_state, 'train_state': train_state,
                        'evidence': str(root.relative_to(ADAPTER))})
        print('PASS '+name, flush=True)

    # Production CLI must exit before root creation, nvidia-smi or science import.
    process = subprocess.run([sys.executable, '-I', '-B', str(ADAPTER/'pipeline.py'), 'production'],
                             capture_output=True, text=True, env=env, timeout=5)
    assert process.returncode == 78, (process.stdout, process.stderr)
    save(suite/'production-gate.json', {'returncode': process.returncode, 'stdout': process.stdout})
    results.append({'case': 'production_gate_closed', 'passed': True, 'outer_exit': 78})

    # Validate every legacy signature directly, including positional existing.
    root = suite/'legacy-signatures'
    root.mkdir()
    legacy = legacy_module(root, sys.executable, 'GPU-fixture')
    legacy.write_json(root/'sample.json', {'test': True})
    assert legacy.safe(root/'sample.json', True) == root/'sample.json'
    assert legacy.safe(root/'sample.json', existing=True) == root/'sample.json'
    assert legacy.sha(root/'sample.json') == generic.sha(root/'sample.json')
    assert legacy.environment()['CUDA_VISIBLE_DEVICES'] == 'GPU-fixture'
    # An already-loaded scientific module must block protective bootstrap.
    sys.modules['numpy'] = types.ModuleType('numpy')
    try:
        try:
            establish_environment(root, sys.executable, 'GPU-fixture')
        except RuntimeError:
            pass
        else:
            raise AssertionError('early scientific import accepted')
    finally:
        sys.modules.pop('numpy')
    results.append({'case': 'legacy_api_and_early_import_gate', 'passed': True})

    # Synthetic documents exercise normalized admission only, never production().
    root = suite/RUN.name
    root.mkdir()
    (root/'source').mkdir()
    for name in ('PLAN.json', 'source/config.json', 'encoder.py', 'source/training_science.py', 'source/science.py'):
        (root/name).write_text('{}\n' if name.endswith('.json') else '# stdlib inert fixture\n')
    manifest = {'files': [{'path': name, 'sha256': generic.sha(root/name)} for name in
                          ('source/config.json', 'encoder.py', 'source/training_science.py', 'source/science.py')]}
    save(root/'manifest.json', manifest)
    manifest_sha, plan_sha = generic.sha(root/'manifest.json'), generic.sha(root/'PLAN.json')
    acceptance = {'passed': True, 'run_id': RUN.name, 'accepted_source_manifest_sha256': manifest_sha}
    dispatch = {'action': 'execute_one_frozen_run', 'run_id': RUN.name,
                'accepted_source_manifest_sha256': manifest_sha, 'plan_sha256': plan_sha,
                'max_training_jobs': 1, 'message_id': 'synthetic-fixture-only',
                'origin_thread_id': '<PRIVATE_ROLE_REF_298cc5edc2>'}
    save(root/'acceptance.json', acceptance)
    save(root/'dispatch.json', dispatch)
    binding = {'plan_sha256': plan_sha,
               **{key: {'path': name, 'sha256': generic.sha(root/name)} for key, name in
                  (('acceptance', 'acceptance.json'), ('manifest', 'manifest.json'),
                   ('formal_dispatch', 'dispatch.json'))}}
    save(root/'binding.json', binding)
    profile = {'execution_enabled': True, 'run_id': RUN.name, 'remote_root': str(root),
               'gpu_uuid': 'GPU-12345678-abcd', 'gpu_index': 99, 'plan_sha256': plan_sha,
               'admission_binding': 'binding.json', 'science_entry': 'source/science.py',
               'accepted_manifest': {'sha256': manifest_sha},
               'main_scientific_acceptance': {'sha256': generic.sha(root/'acceptance.json')},
               'formal_execution_message': {'message_id': dispatch['message_id'],
                                            'origin_thread_id': dispatch['origin_thread_id']}}
    assert require_production(profile, root)['manifest_sha256'] == manifest_sha
    rejected = []
    for key, value in (('execution_enabled', False), ('gpu_uuid', None), ('plan_sha256', '0'*64),
                       ('science_entry', 'source/unaccepted.py'), ('admission_binding', None),
                       ('formal_execution_message', None)):
        bad = {**profile, key: value}
        try:
            require_production(bad, root)
        except (GateClosed, ValueError):
            rejected.append(key)
        else:
            raise AssertionError('bad admission passed: '+key)
    # File drift and approval/dispatch drift both reject.
    (root/'source/science.py').write_text('# changed after acceptance\n')
    try:
        require_production(profile, root)
    except GateClosed:
        rejected.append('source_drift')
    else:
        raise AssertionError('source drift accepted')
    (root/'source/science.py').write_text('# stdlib inert fixture\n')
    for name in ('acceptance.json', 'dispatch.json'):
        original = (root/name).read_text()
        (root/name).write_text('{}\n')
        try:
            require_production(profile, root)
        except GateClosed:
            rejected.append(name+'_drift')
        else:
            raise AssertionError(name+' drift accepted')
        (root/name).write_text(original)
    save(suite/'admission-contract.json', {'positive_fixture_passed': True, 'rejected': rejected,
                                         'production_execution_attempted': False})
    results.append({'case': 'admission_normalized_contract', 'passed': True,
                    'negative_cases': rejected})
    # Runtime compatibility objects are bound separately, never appended to the
    # already accepted four-file scientific manifest. No test byte is loaded.
    (root/'shim-fixture.bin').write_text('inert fixture; never loaded')
    runtime_manifest = {'files': [{'path': 'shim-fixture.bin',
                                   'sha256': generic.sha(root/'shim-fixture.bin')}]}
    save(root/'runtime-artifacts.json', runtime_manifest)
    runtime_hash = generic.sha(root/'runtime-artifacts.json')
    preload_profile = {'compatibility_preload': runtime_manifest['files'][0],
                       'runtime_artifacts_manifest': {'path': 'runtime-artifacts.json', 'sha256': runtime_hash}}
    admitted = {'documents': {'formal_dispatch': {'runtime_artifacts_manifest_sha256': runtime_hash}}}
    assert runtime_preload(preload_profile, admitted, root) == root/'shim-fixture.bin'
    try:
        runtime_preload(preload_profile, {'documents': {'formal_dispatch': {}}}, root)
    except GateClosed:
        pass
    else:
        raise AssertionError('unbound runtime preload passed')
    results.append({'case': 'separate_runtime_artifact_binding', 'passed': True,
                    'binary_loaded': False})
    report = {'run_id': RUN.name, 'passed': True, 'checks': len(results),
              'subprocess_pipeline_cases': len(scenarios), 'results': results,
              'suite': str(suite.relative_to(ADAPTER)), 'actual_gpu_or_training': False,
              'parameter_updates': 0, 'remote_operations': False,
              'real_scientific_runner_executed': False, 'linux_boundary_executed': False}
    save(suite/'result.json', report)
    print(json.dumps(report), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
