"""Accepted source interface probe. Stops before late scientific imports/updates.

numpy is an inert ModuleType only for importing helper definitions; no numpy,
torch, encoder, model construction, dataset loading or CUDA code is executed.
"""
import ast
import importlib.abc
import json
import os
import sys
import types
from pathlib import Path

ADAPTER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADAPTER))
from adapter_common import RUN, establish_environment, generic, strict_json, write
from admission import require_production
from guarded_worker import load_science


def main():
    root = Path(sys.argv[1])
    if ADAPTER/'checks' not in root.parents:
        raise ValueError('probe root outside adapter checks')
    root.mkdir()
    binding = strict_json(ADAPTER/'accepted-science-binding.json')
    manifest_path = Path(binding['accepted_manifest'])
    assert generic.sha(manifest_path) == binding['accepted_manifest_sha256']
    for item in binding['files']:
        assert generic.sha(Path(item['local_source'])) == item['sha256']
    entry = next(Path(item['local_source']) for item in binding['files']
                 if item['deploy_path'] == binding['science_entry'])
    cfg_path = next(Path(item['local_source']) for item in binding['files']
                    if item['deploy_path'] == 'source/config.json')
    source_ast = ast.parse(entry.read_text())
    required = {'ROOT', 'GPU_UUID', 'environment', 'now', 'safe', 'sha', 'write_json'}
    imported = {alias.name for node in ast.walk(source_ast)
                if isinstance(node, ast.ImportFrom) and node.module == 'common_guarded'
                for alias in node.names}
    assert required <= imported
    legacy = establish_environment(root, sys.executable, 'GPU-interface-fixture')
    write(root, root/'protection-before-import.json',
          {'environment_prepared': True, 'linux_guard_executed': False})
    # The helper's numpy annotations/definitions import through this inert stub.
    # All numerical calls and real scientific modules remain forbidden.
    sys.modules['numpy'] = types.ModuleType('numpy')
    class ForbidScientificImport(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {'torch', 'encoder', 'chemprop', 'rdkit', 'joblib'}:
                raise RuntimeError('forbidden scientific import during interface probe: '+fullname)
    sys.meta_path.insert(0, ForbidScientificImport())
    module = load_science(entry, root)
    assert callable(module.main) and callable(module._load_late)
    config = strict_json(cfg_path)
    assert module.validate_config(config) == config
    plan = strict_json(RUN/'PLAN.json')
    assert {k: v for k, v in config['head_config'].items() if k != 'optimizer'} == plan['head_config']
    assert config['head_config']['optimizer'] == 'AdamW'
    assert config['split_config'] == plan['split_config']
    assert [(i['role'], i['sha256'], i['rows']) for i in config['inputs']] == [
        (i['role'], i['sha256'], i['rows']) for i in plan['inputs']]
    reached = []
    class StopBeforeScientificLoad(Exception):
        pass
    def stop_before_late():
        assert sys.modules['common_guarded'] is legacy
        assert legacy.ROOT == root and os.getcwd() == str(root)
        assert os.environ == legacy.environment()
        assert os.environ['JOBLIB_MULTIPROCESSING'] == '0'
        assert not any(name in sys.modules for name in ('torch', 'encoder', 'chemprop', 'rdkit'))
        reached.append('main_env_then_load_late')
        raise StopBeforeScientificLoad()
    module._load_late = stop_before_late
    try:
        module.main()
    except StopBeforeScientificLoad:
        pass
    else:
        raise AssertionError('actual science main did not stop at late-load boundary')
    assert reached == ['main_env_then_load_late']

    # Exact original manifest with deploy_path is validated in an inert local
    # deployment fixture. No file from this fixture is executed.
    deployed = root/'host-admission'/RUN.name
    deployed.mkdir(parents=True)
    (deployed/'source').mkdir()
    (deployed/'PLAN.json').write_bytes((RUN/'PLAN.json').read_bytes())
    for item in binding['files']:
        (deployed/item['deploy_path']).write_bytes(Path(item['local_source']).read_bytes())
    (deployed/'manifest.json').write_bytes(manifest_path.read_bytes())
    (deployed/'acceptance.json').write_bytes(Path(binding['main_acceptance']).read_bytes())
    manifest_sha = generic.sha(deployed/'manifest.json')
    plan_sha = generic.sha(deployed/'PLAN.json')
    dispatch = {'action': 'execute_one_frozen_run', 'run_id': RUN.name,
                'accepted_source_manifest_sha256': manifest_sha, 'plan_sha256': plan_sha,
                'max_training_jobs': 1, 'message_id': 'SYNTHETIC_NOT_A_FORMAL_EXECUTION_MESSAGE',
                'origin_thread_id': '<PRIVATE_ROLE_REF_298cc5edc2>'}
    write(root, deployed/'dispatch.json', dispatch)
    normalized = {'plan_sha256': plan_sha,
                  **{key: {'path': name, 'sha256': generic.sha(deployed/name)} for key, name in
                     (('acceptance', 'acceptance.json'), ('manifest', 'manifest.json'),
                      ('formal_dispatch', 'dispatch.json'))}}
    write(root, deployed/'binding.json', normalized)
    profile = {'execution_enabled': True, 'run_id': RUN.name, 'remote_root': str(deployed),
               'gpu_uuid': 'GPU-12345678-abcd', 'gpu_index': 99, 'plan_sha256': plan_sha,
               'admission_binding': 'binding.json', 'science_entry': 'source/train_remote_v4.py',
               'accepted_manifest': {'sha256': manifest_sha},
               'main_scientific_acceptance': {'sha256': generic.sha(deployed/'acceptance.json')},
               'formal_execution_message': {'message_id': dispatch['message_id'],
                                            'origin_thread_id': dispatch['origin_thread_id']}}
    admitted = require_production(profile, deployed)
    assert admitted['manifest_sha256'] == binding['accepted_manifest_sha256']
    for item in binding['files']:
        assert generic.sha(Path(item['local_source'])) == item['sha256']
    result = {'passed': True, 'run_id': RUN.name,
              'accepted_manifest_sha256': binding['accepted_manifest_sha256'],
              'exact_source_files_verified': 4, 'legacy_names': sorted(required),
              'accepted_main_entered_then_stopped_before_load_late': True,
              'protection_precedes_source_import': True, 'actual_deploy_path_contract_passed': True,
              'real_scientific_library_imports': False, 'numpy_stub_only': True,
              'data_loaded': False, 'parameter_updates': 0, 'cuda_executed': False,
              'original_scientific_files_unchanged': True,
              'synthetic_dispatch_is_not_real_authorization': True}
    write(root, root/'result.json', result)
    print(json.dumps(result), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
