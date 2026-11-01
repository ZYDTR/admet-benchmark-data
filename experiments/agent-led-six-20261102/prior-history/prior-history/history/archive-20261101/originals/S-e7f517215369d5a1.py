"""Real admitted pure definitions only; never import/call scientific main.

No NumPy/Torch dependency is installed. Checkpoint save_head is exercised with
an explicitly metadata-only serializer, which does not certify Tensor storage.
Admission uses real approved bytes and a synthetic local dispatch, never a CLI.
"""
import ast
import copy
import csv
import datetime
import importlib.util
import hashlib
import json
import math
import random
import shutil
import sys
import types
import uuid
from pathlib import Path

ADAPTER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ADAPTER))
from adapter_common import RUN, generic, legacy_module, strict_json
from admission import GateClosed, SCIENCE_PATHS, RUNTIME_REQUIRED, require_production
from state_contract import history_selection, verify_metadata


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def rejects(call):
    try:
        call()
    except (ValueError, RuntimeError):
        return
    raise AssertionError('invalid interface input accepted')


def extracted_helper(path):
    source = path.read_text()
    tree = ast.parse(source)
    definitions = {'PreparationError', '_is_number', 'validate_config',
                   'check_rows_identity', 'build_drug_groups', 'load_input_tables',
                   'sha256_hex', 'canonical_json_bytes', 'assign_internal_stop',
                   'select_stop_groups', 'total', 'split_train_stop_groups',
                   'monitor_metric_key', 'select_monitor_value',
                   'validate_epoch_history', 'checkpoint_identity'}
    constants = {'SCHEMA_VERSION', 'MONITOR_STANDARDIZED_MSE', 'MONITOR_RAW_MAE',
                 'ALLOWED_MONITORS', 'MIN_DELTA', '_REQUIRED_TOP_KEYS',
                 '_REQUIRED_HEAD_KEYS', '_REQUIRED_SPLIT_KEYS', '_INPUT_ROLES',
                 '_EPOCH_REQUIRED_KEYS'}
    constants.add('SHUFFLE_ALGORITHM')
    selected = []
    names = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in definitions:
            selected.append(node)
            names.append(node.name)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets):
            selected.append(node)
    assert set(names) == definitions
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    unit = ast.fix_missing_locations(ast.Module(body=[future, *selected], type_ignores=[]))
    scope = {'csv': csv, 'math': math, 'random': random, 'hashlib': hashlib, 'json': json}
    exec(compile(unit, str(path), 'exec'), scope)
    return scope, names


class MetadataValue:
    """Never represents a Tensor. Only covers detach/cpu metadata plumbing."""
    def detach(self):
        return self

    def cpu(self):
        return 'METADATA_ONLY_NO_TENSOR'


class MetadataArray:
    def __init__(self, value):
        self.value = value

    def tolist(self):
        return self.value


def check_metadata(helper, suite, cfg, runner_path):
    tree = ast.parse(runner_path.read_text())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    node = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'save_head')
    # This is the exact nested production definition; main itself is never compiled/executed.
    unit = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    call_names = [ast.unparse(n.func) for n in ast.walk(main) if isinstance(n, ast.Call)]
    assert 'nn.MSELoss' in call_names and 'select_monitor_value' in call_names
    assert 'checkpoint_identity' in call_names
    assert any(isinstance(n, ast.Compare) and ast.unparse(n) == 'monitor_value < best - MIN_DELTA' for n in ast.walk(main))
    results = []
    for monitor, expected_epoch in (('internal_validation_raw_mae', 3), ('internal_validation_standardized_mse', 2)):
        local_cfg = copy.deepcopy(cfg)
        local_cfg['monitor'] = monitor
        helper['validate_config'](local_cfg)
        root = suite/monitor
        (root/'artifacts').mkdir(parents=True)
        config_path = root/'config.json'
        save(config_path, local_cfg)
        config_sha = generic.sha(config_path)
        history = []
        for i, (mse, mae) in enumerate(zip((.2, .1, .3, .4), (.4, .5, .2, .3))):
            value = helper['select_monitor_value'](monitor, mse, {'mae': mae, 'mse': 99.})
            history.append({'epoch': i+1, 'steps': 5*(i+1),
                            'internal_validation_standardized_mse': mse,
                            'internal_validation_raw_mae': mae,
                            'monitor': monitor, 'monitor_key': helper['monitor_metric_key'](monitor),
                            'monitor_value': value})
        selected = history_selection(local_cfg, history)
        assert selected+1 == expected_epoch
        def metadata_save(payload, path):
            save(path, {'metadata_only_serializer': True, 'payload': payload})
        scope = {'cfg': local_cfg, 'hc': local_cfg['head_config'], 'sc': local_cfg['split_config'],
                 'cfg_source_sha256': config_sha, 'enc': types.SimpleNamespace(feature_dim=2),
                 'mu': MetadataArray([0., 0.]), 'sd': MetadataArray([1., 1.]),
                 'ym': 0., 'ys': 1., 'tr': [0, 1], 'va': [2],
                 'split_record': {'split_record_sha256': 'a'*64}, 'ROOT': root,
                 'torch': types.SimpleNamespace(save=metadata_save)}
        exec(compile(unit, str(runner_path), 'exec'), scope)
        records = {}
        for tag, index in (('best', selected), ('last', len(history)-1)):
            identity = helper['checkpoint_identity'](history, index)
            payload, path = scope['save_head']({'metadata_placeholder': MetadataValue()}, tag, identity)
            records[tag] = payload
            assert payload['best_internal_validation_standardized_mse'] == .1
            assert payload['internal_validation_standardized_mse_at_checkpoint'] == history[index]['internal_validation_standardized_mse']
            assert payload['best_monitor_value'] == (.2 if monitor.endswith('raw_mae') else .1)
            results.append({'monitor': monitor, 'tag': tag, 'epoch': payload['epoch_1_based'],
                            'steps': payload['optimizer_steps'], 'legacy_best_mse': .1,
                            'current_mse': payload['internal_validation_standardized_mse_at_checkpoint'],
                            'serializer': 'metadata_only_stub_actual_tensor_storage_UNVERIFIED'})
        state = {'run_id': local_cfg['run_id'], 'config': local_cfg, 'config_sha256': config_sha,
                 'which': 'last', 'head_tag': 'last', 'epoch_1_based': 4, 'optimizer_steps': 20,
                 'last_head_sha256': generic.sha(root/'artifacts/caco2_wang-head-last.pt'),
                 'split_record_sha256': 'a'*64}
        def validate(best, last, st=state):
            return verify_metadata(local_cfg, history, best, last, st, config_sha,
                                   generic.sha(root/'artifacts/caco2_wang-head-last.pt'))
        validate(records['best'], records['last'])
        for tag, field, wrong in (('best', 'best_internal_validation_standardized_mse', .2),
                                  ('last', 'internal_validation_standardized_mse_at_checkpoint', .1),
                                  ('best', 'optimizer_steps', 999), ('last', 'monitor', 'wrong'),
                                  ('best', 'config_sha256', '0'*64)):
            bad = copy.deepcopy(records)
            bad[tag][field] = wrong
            rejects(lambda: validate(bad['best'], bad['last']))
        invalid = copy.deepcopy(history)
        invalid[0]['monitor_value'] = 123
        rejects(lambda: helper['validate_epoch_history'](invalid))
        rejects(lambda: helper['select_monitor_value'](monitor, float('nan'), {'mae': float('nan')}))
    rejects(lambda: helper['monitor_metric_key']('unknown'))
    return results


def main():
    suite = ADAPTER/'checks'/('interfaces-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8])
    root = suite/RUN.name
    root.mkdir(parents=True)
    profile = strict_json(ADAPTER/'adapter-profile.json')
    plan = strict_json(RUN/'PLAN.json')
    for name, target in SCIENCE_PATHS.items():
        (root/target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RUN/'source/science'/name, root/target)
    for path in ('PLAN.json', 'inputs-manifest.json', *(i['path'] for i in strict_json(RUN/'inputs-manifest.json'))):
        (root/path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RUN/path, root/path)
    for item in plan['inputs']:
        target = {'train': 'data/train.csv', 'validation': 'data/valid.csv', 'test': 'data/test.csv'}[item['role']]
        (root/target).parent.mkdir(exist_ok=True)
        shutil.copyfile(item['path'], root/target)
    (root/'assets').mkdir()
    shutil.copyfile(plan['pretrained_backbone_path'], root/'assets/chemeleon_mp.pt')
    (root/'admission').mkdir()
    authority = Path(profile['accepted_manifest']['authority_path'])
    shutil.copyfile(authority, root/'admission/science-manifest.json')
    shutil.copyfile(Path(plan['scientific_code_admission']), root/'admission/MAIN_ACCEPTANCE.json')
    runtime_files = []
    for relative in sorted(RUNTIME_REQUIRED):
        (root/relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RUN/relative, root/relative)
        runtime_files.append({'path': relative, 'sha256': generic.sha(root/relative),
                              'size': (root/relative).stat().st_size})
    save(root/'admission/runtime-source-manifest.json', {'run_id': RUN.name, 'files': runtime_files})
    runtime_sha = generic.sha(root/'admission/runtime-source-manifest.json')
    dispatch = {'action': 'execute_one_frozen_run', 'run_id': RUN.name,
                'accepted_source_manifest_sha256': generic.sha(authority),
                'scientific_acceptance_sha256': profile['main_scientific_acceptance']['sha256'],
                'plan_sha256': profile['plan_sha256'], 'max_training_jobs': 1,
                'frozen_inputs_manifest_sha256': profile['frozen_inputs_manifest']['sha256'],
                'runtime_source_manifest_sha256': runtime_sha,
                'message_id': 'SYNTHETIC_LOCAL_INTERFACE_ONLY_NEVER_EXECUTE',
                'origin_thread_id': 'private-role-298cc5edc25e'}
    save(root/'admission/synthetic-dispatch.json', dispatch)
    binding = {'plan_sha256': profile['plan_sha256']}
    for key, name in (('acceptance', 'MAIN_ACCEPTANCE.json'), ('manifest', 'science-manifest.json'),
                      ('formal_dispatch', 'synthetic-dispatch.json')):
        binding[key] = {'path': 'admission/'+name, 'sha256': generic.sha(root/'admission'/name)}
    save(root/'admission/binding.json', binding)
    profile.update(execution_enabled=True, remote_root=str(root), gpu_uuid='<REGISTERED_GPU>',
                   gpu_index=0, admission_binding='admission/binding.json',
                   runtime_source_manifest={'path': 'admission/runtime-source-manifest.json', 'sha256': runtime_sha},
                   formal_execution_message={k: dispatch[k] for k in ('message_id', 'origin_thread_id')})
    admitted = require_production(profile, root)  # data/hash validation only, never launches anything
    assert admitted['entry'] == root/'source/train_remote_v4.py'
    rejected = []
    for key, wrong in (('run_id', 'wrong'), ('remote_root', '/wrong'), ('monitor', 'internal_validation_standardized_mse'),
                        ('plan_sha256', '0'*64), ('formal_execution_message', None)):
        bad = copy.deepcopy(profile)
        bad[key] = wrong
        rejects(lambda: require_production(bad, root))
        rejected.append(key)
    # Tamper copies only; approved originals and frozen inputs never change.
    for relative in ('source/training_science.py', 'inputs/project/policy.json',
                     'inputs-manifest.json', 'data/valid.csv', 'assets/chemeleon_mp.pt',
                     'source/runtime-v1/resource_checks.py',
                     'admission/runtime-source-manifest.json',
                     'admission/synthetic-dispatch.json'):
        path = root/relative
        original = path.read_bytes()
        try:
            path.write_bytes(original+b'\nTAMPER')
            rejects(lambda: require_production(profile, root))
            rejected.append(relative)
        finally:
            path.write_bytes(original)
    require_production(profile, root)
    helper_path = RUN/'source/science/training_science.py'
    helper, names = extracted_helper(helper_path)
    cfg = admitted['config']
    helper['validate_config'](cfg)
    legacy = legacy_module(root, sys.executable, 'GPU-interface-fixture')
    rows, hashes, audits = helper['load_input_tables'](cfg, root, legacy.safe, legacy.sha)
    assert {k: len(v) for k, v in rows.items()} == {'train': 637, 'valid': 91, 'test': 182}
    split = helper['split_train_stop_groups'](rows['train'], cfg['split_config']['seed'], cfg['split_config']['validation_fraction'])
    assert split == helper['split_train_stop_groups'](rows['train'], cfg['split_config']['seed'], cfg['split_config']['validation_fraction'])
    assert sorted(split['fit_row_indices']+split['stop_row_indices']) == list(range(637))
    assert not ({rows['train'][i]['Drug'] for i in split['fit_row_indices']}
                & {rows['train'][i]['Drug'] for i in split['stop_row_indices']})
    encoder_spec = importlib.util.spec_from_file_location('_read_only_encoder_interface', RUN/'source/science/encoder.py')
    encoder = importlib.util.module_from_spec(encoder_spec)
    encoder_spec.loader.exec_module(encoder)  # stdlib only; no embedder construction
    checkpoint = encoder.verify_checkpoint(root/'assets/chemeleon_mp.pt')
    assert checkpoint['size'] == 34859448
    # Original row identity allows blank/repeated IDs and preserves raw SMILES strings.
    fixture = [{'Drug_ID': '', 'Drug': ' C '}, {'Drug_ID': '', 'Drug': 'C'}]
    assert helper['check_rows_identity'](fixture, require_y=False, label='fixture')['blank_drug_id_rows'] == [0, 1]
    assert len(helper['build_drug_groups'](fixture)) == 2
    rejects(lambda: helper['check_rows_identity']([dict(fixture[0], Y='0')], require_y=False, label='fixture'))
    rejects(lambda: helper['check_rows_identity']([dict(fixture[0], Y='nan')], require_y=True, label='fixture'))
    legacy.write_json(root/'legacy-signature.json', {'checked': True})
    assert legacy.safe(root/'legacy-signature.json', True) == root/'legacy-signature.json'
    rejects(lambda: legacy.safe(root.parent/'outside.json'))
    link = root/'linked.json'
    link.symlink_to(root/'legacy-signature.json')
    rejects(lambda: legacy.safe(link, True))
    metadata = check_metadata(helper, suite, cfg, RUN/'source/science/train_remote_v4.py')
    report = {'passed': True, 'run_id': RUN.name, 'real_approved_bytes_admission': True,
              'synthetic_dispatch_used_only_in_pure_function': True, 'negative_admission_cases': rejected,
              'actual_source_functions': names+['main.<locals>.save_head'],
              'actual_encoder_function': 'verify_checkpoint',
              'helper_sha256': generic.sha(helper_path),
              'runner_sha256': generic.sha(RUN/'source/science/train_remote_v4.py'),
              'csv_rows': {k: len(v) for k, v in rows.items()}, 'csv_hashes': hashes,
              'identity_audits': audits, 'checkpoint_metadata_four_cases': metadata,
              'split': {k: split[k] for k in ('fit_rows', 'stop_rows', 'split_record_sha256')},
              'checkpoint_bytes_identity': checkpoint,
              'actual_helper_full_module_import': False, 'actual_runner_full_module_import': False,
              'actual_encoder_stdlib_module_import': True, 'actual_tensor_serialization_checked': False,
              'dependencies_present': {k: importlib.util.find_spec(k) is not None for k in ('numpy', 'torch')},
              'unverified': ['NumPy numeric interfaces', 'real Tensor/optimizer/RNG serialization', 'CUDA', 'Linux boundary'],
              'scientific_main_called': False, 'model_inference': False, 'parameter_updates': 0,
              'remote_operations': False, 'private_valid_truth_or_scores_read': False}
    save(suite/'result.json', report)
    print(json.dumps({'passed': True, 'evidence': str(suite/'result.json'), 'metadata_cases': len(metadata),
                      'admission_negatives': len(rejected), 'tensor_storage_verified': False}))


if __name__ == '__main__':
    main()
