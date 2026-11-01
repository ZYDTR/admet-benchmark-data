"""Fixed stdlib fixture with legacy runner API. No ML imports or parameter updates."""
import json
import os
import sys
import time
from pathlib import Path

from common_guarded import ROOT, GPU_UUID, environment, now, safe, sha, write_json

# These assertions execute at MODULE IMPORT, before preflight()/main().
assert ROOT == Path.cwd()
assert os.environ['HOME'] == str(ROOT/'home')
assert os.environ['TMPDIR'] == str(ROOT/'tmp')
assert os.environ['JOBLIB_MULTIPROCESSING'] == '0'
assert os.environ['CUDA_VISIBLE_DEVICES'] == GPU_UUID
assert GPU_UUID == 'GPU-offline-fixture'
assert not any(name.split('.')[0] in ('torch', 'numpy', 'chemprop', 'rdkit') for name in sys.modules)
assert safe(ROOT, True) == ROOT
assert safe(ROOT/'source/config.json', existing=True).is_file()
CFG = json.loads((ROOT/'source/config.json').read_text())
PROTECTION = []
for phase in ('preflight', 'train'):
    p = ROOT/'raw/attempt-01'/phase/'protection.json'
    if p.exists():
        record = json.loads(p.read_text())
        if record['worker_identity']['pid'] == os.getpid():
            PROTECTION.append(record)
assert len(PROTECTION) == 1
assert PROTECTION[0]['environment_before_scientific_import'] is True
assert PROTECTION[0]['offline_test_only'] is True
write_json(ROOT/'raw'/('import-order-'+str(os.getpid())+'.json'),
           {'pid': os.getpid(), 'at': now(), 'legacy_signature_works': True,
            'protection_marker_existed_before_import': True, 'heavy_imports': False})


def preflight(proof_path):
    case = CFG['fixture_case']
    if case == 'preflight_exit7':
        return 7
    if case == 'preflight_timeout':
        time.sleep(30)
    if case == 'stale_legacy_complete':
        write_json(ROOT/'raw/train-complete.json', {'status': 'success'})
    if case == 'learning_lock_exists':
        (ROOT/'state/learning-started.lock').write_text('inert fixture')
    write_json(proof_path, {'offline_fixture': True, 'actual_cuda': False,
                            'pid': os.getpid(), 'parameter_updates': 0})
    return 0


def main():
    case = CFG['fixture_case']
    write_json(ROOT/'raw/fake-train-called.json', {'pid': os.getpid(), 'parameter_updates': 0})
    # Reproduce the real runner's environment reset using the legacy no-arg API.
    os.environ.clear()
    os.environ.update(environment())
    assert os.environ['JOBLIB_MULTIPROCESSING'] == '0'
    if case == 'train_exit7':
        return 7
    if case == 'train_timeout':
        time.sleep(30)
    if case == 'legacy_success_only':
        write_json(ROOT/'raw/train-complete.json', {'status': 'success'})
        return 0
    # Byte fixtures only. These .pt/.npz files are never deserialized.
    names = ('head-initial.pt', 'caco2_wang-head-best.pt', 'caco2_wang-head-last.pt',
             'training-state-last.pt', 'preprocessing.npz', 'predictions.csv',
             'train-predictions.csv', 'features-train.npz', 'features-valid.npz',
             'features-test.npz', 'features-train-identity.json',
             'features-valid-identity.json', 'features-test-identity.json',
             'optimizer-separation.json', 'internal-split.json')
    for name in names:
        safe(ROOT/'artifacts'/name).write_text('fixed toy bytes; zero parameter updates\n')
    write_json(ROOT/'raw/train-runtime.json', {'pid': os.getpid(), 'run_id': CFG['run_id'],
               'visible_gpu_uuid': GPU_UUID, 'config_sha256': sha(ROOT/'source/config.json'),
               'monitor': CFG['monitor']})
    evidence = {'run_id': CFG['run_id'], 'gpu_uuid': GPU_UUID,
                'monitor': CFG['monitor'], 'monitor_key': CFG['monitor'],
                'config_sha256': sha(ROOT/'source/config.json'),
                'encoder_state_unchanged': True, 'encoder_gradients_none': True,
                'encoder_eval': True, 'encoder_parameters_frozen': True,
                'encoder_checkpoint_sha256_unchanged': True,
                'optimizer_separation': {'optimizer_exactly_head': True, 'optimizer_encoder_intersection': 0},
                'optimizer_steps': 1, 'nonzero_gradient_steps': 1,
                'head_initial_sha256': 'toy-initial', 'head_final_sha256': 'toy-final',
                'head_output_devices': ['cuda:0'], 'official_validation_scoring': False,
                'test_fitting': False, 'fixture_claims_only_actual_cuda': False}
    write_json(ROOT/'artifacts/training-evidence.json', evidence)
    for tag in ('before', 'after'):
        write_json(ROOT/'artifacts'/('encoder-'+tag+'.json'), {'toy_digest': 'unchanged'})
    write_json(ROOT/'artifacts/training-state-reload.json', {
        'weights_only_load': True, 'optimizer_roundtrip_exact': True,
        'restore_reproducible': True, 'restored_back_to_checkpoint_state': True,
        'restored_sources': ['python', 'numpy', 'torch_cpu', 'torch_cuda', 'sampler']})
    write_json(ROOT/'raw/train-complete.json', {'status': 'success', 'optimizer_steps': 1,
                                               'encoder_frozen': True})
    return 0
