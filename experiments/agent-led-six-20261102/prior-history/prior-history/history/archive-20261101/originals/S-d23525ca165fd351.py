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
        ('learning_lock_exists', 125, 'succeeded', 'precheck_failed'),
    )
    for name, expected, pre_state, train_state in scenarios:
        root = suite/name
        root.mkdir()
        (root/'source').mkdir()
        save(root/'source/config.json', {'run_id': RUN.name, 'fixture_case': name,
                                        'monitor': 'internal_validation_raw_mae'})
        command = [sys.executable, '-I', '-B', str(ADAPTER/'pipeline.py'), 'offline',
                   '--root', str(root), '--case', name]
        process = subprocess.run(command, capture_output=True, text=True, env=env, timeout=15)
        save(root/'outer-process.json', {'command': command, 'returncode': process.returncode,
                                         'stdout': process.stdout, 'stderr': process.stderr})
        status = json.loads((root/'raw/attempt-01/pipeline-exit.json').read_text())
        assert process.returncode == expected, (name, process.returncode, process.stdout, process.stderr)
        assert status['supervisor_exit_code'] == process.returncode, name
        assert status['success'] is (expected == 0), name
        assert status['training_started'] is False, name
        assert status['phases']['preflight']['state'] == pre_state, name
        assert status['phases']['train']['state'] == train_state, name
        if train_state == 'skipped_failed_preflight':
            assert not (root/'raw/attempt-01/train').exists(), name
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
                actual = json.loads((root/'raw/attempt-01'/phase/'status.json').read_text())
                assert actual['supervisor_exit_code'] == value['supervisor_exit_code']
        if name == 'success':
            for phase in ('preflight', 'train'):
                receipt = json.loads((root/'raw/attempt-01'/phase/'adapter-complete.json').read_text())
                assert receipt['worker_identity']['pid'] == status['phases'][phase]['child_identity']['pid']
                assert receipt['run_id'] == RUN.name
                assert receipt['offline_fixture'] is True
                assert receipt['protection']['landlock_applied'] is False
            assert len(list((root/'raw').glob('import-order-*.json'))) == 2
            before = generic.sha(root/'raw/attempt-01/pipeline-exit.json')
            replay = subprocess.run(command, capture_output=True, text=True, env=env, timeout=5)
            assert replay.returncode == 73
            assert generic.sha(root/'raw/attempt-01/pipeline-exit.json') == before
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

    # Actual four-file/frozen-input admission is tested with real approved bytes
    # by check_science_interfaces.py; toy subprocess tests do not certify science.
    root = suite/'runtime-artifact-contract'
    root.mkdir()
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
