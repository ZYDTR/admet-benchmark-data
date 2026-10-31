"""Protect first, install legacy API, import accepted science, issue new receipt.

Offline mode executes only the fixed tests/toy_science.py. Production remains
closed by adapter-profile.json plus main admission/dispatch and Linux identity.
"""
import argparse
import importlib.util
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapter_common import (ADAPTER, RUN, establish_environment, generic,
                            load_boundary, process_identity, strict_json, write)
from admission import GateClosed, require_production
from completion import (TRAIN_FILES, create_receipt, require_fresh_training_outputs,
                        training_claims)


def load_science(path, root):
    # common_guarded is already the adapter-owned compatibility module.
    sys.path[:0] = [str(path.parent), str(root), str(root/'source')]
    spec = importlib.util.spec_from_file_location('_accepted_science', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cuda_preflight(module, proof_path, root):
    module._load_late()
    import torch
    import chemprop
    import rdkit
    import numpy
    import joblib._multiprocessing_helpers as helper
    if helper.mp is not None or not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError('dependency/joblib/single CUDA preflight failed')
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.cuda.set_device(0)
    props = torch.cuda.get_device_properties(0)
    torch.cuda.set_per_process_memory_fraction(4096*1024**2/props.total_memory, 0)
    value = torch.ones((64, 64), device='cuda:0')
    result = value@value
    torch.cuda.synchronize()
    if result.device.type != 'cuda' or not bool(torch.all(result == 64)):
        raise RuntimeError('actual CUDA calculation failed')
    proof = {'pid': os.getpid(), 'actual_cuda_matmul': True,
             'single_cuda_device': True, 'full_imports': True, 'joblib_mp': None,
             'torch': torch.__version__, 'chemprop': chemprop.__version__,
             'rdkit': rdkit.__version__, 'numpy': numpy.__version__,
             'allocated_bytes': torch.cuda.max_memory_allocated(),
             'reserved_bytes': torch.cuda.max_memory_reserved()}
    write(root, proof_path, proof)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('offline', 'production'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--attempt', type=Path, required=True)
    parser.add_argument('--phase', choices=('preflight', 'train'), required=True)
    parser.add_argument('--token', required=True)
    parser.add_argument('--profile', type=Path, default=ADAPTER/'adapter-profile.json')
    args = parser.parse_args()
    root, attempt = args.root, args.attempt
    offline = args.mode == 'offline'
    if offline:
        if ADAPTER/'checks' not in root.parents:
            raise GateClosed('offline root must be inside this adapter checks directory')
        config = strict_json(generic.safe(root, root/'source/config.json', True))
        case = config['fixture_case']
        profile = {'python': sys.executable, 'gpu_uuid': 'GPU-offline-fixture'}
        entry = ADAPTER/'tests/toy_science.py'
        manifest_sha = generic.sha(entry)
    else:
        profile = strict_json(generic.safe(root, args.profile, True))
        admitted = require_production(profile, root)
        if sys.platform != 'linux' or os.uname().nodename != '<COMPUTE_HOST>' or os.getuid() != 1012:
            raise GateClosed('target Linux <COMPUTE_HOST> UID identity mismatch')
        entry, manifest_sha, case = admitted['entry'], admitted['manifest_sha256'], None
    generic.safe(root, attempt, True)
    worker_identity = process_identity(os.getpid())
    context = {'run_id': RUN.name, 'phase': args.phase, 'token': args.token,
               'worker_identity': worker_identity, 'accepted_manifest_sha256': manifest_sha,
               'gpu_uuid': profile['gpu_uuid'], 'offline_fixture': offline}
    write(root, attempt/'worker-start.json', context)
    # No scientific entry/helper/encoder or third-party library has been imported.
    legacy = establish_environment(root, profile['python'], profile['gpu_uuid'])
    boundary = load_boundary()
    if offline:
        protection = {'environment_before_scientific_import': True,
                      'landlock_applied': False, 'process_limits_applied': False,
                      'offline_test_only': True}
    else:
        limits = boundary.apply_process_limits(2)
        guard = boundary.apply_write_guard(root)
        protection = {'environment_before_scientific_import': True,
                      'landlock_applied': True, 'process_limits_applied': True,
                      'limits': limits, 'guard': guard, 'offline_test_only': False}
    write(root, attempt/'protection.json', {**context, **protection})
    if args.phase == 'train':
        require_fresh_training_outputs(root)
    module = load_science(entry, root)
    # Toy module is fixed and performs only file writes and integer return paths.
    proof_path = attempt/'preflight-proof.json'
    if args.phase == 'preflight':
        returncode = module.preflight(proof_path) if offline else cuda_preflight(module, proof_path, root)
        evidence_paths = [str(proof_path.relative_to(root))]
        claims = {'preflight_returned_zero': returncode == 0,
                  'actual_cuda_verified': not offline}
    else:
        returncode = module.main()
        evidence_paths = list(TRAIN_FILES)
        claims = None
    if type(returncode) is not int:
        raise ValueError('science main must explicitly return integer exit status')
    if returncode != 0:
        return returncode
    if args.phase == 'train':
        claims = training_claims(root, RUN.name, os.getpid(), profile['gpu_uuid'],
                                 legacy.sha(root/'source/config.json'))
    if offline and ((case == 'missing_adapter_receipt' and args.phase == 'train')
                    or (case == 'preflight_missing_receipt' and args.phase == 'preflight')):
        return 0  # Fixed fault injection: legacy success alone must be rejected.
    receipt = create_receipt(root, attempt, args.phase, RUN.name, args.token,
                             worker_identity, manifest_sha, profile['gpu_uuid'],
                             evidence_paths, offline, protection, claims)
    if offline and args.phase == 'train':
        if case == 'wrong_token':
            receipt['token'] = 'old-token'
        elif case == 'wrong_pid':
            receipt['worker_identity'] = {**worker_identity, 'pid': 1}
        elif case == 'wrong_manifest':
            receipt['accepted_manifest_sha256'] = '0'*64
        write(root, attempt/'adapter-complete.json', receipt)
        if case == 'artifact_tamper':
            (root/'artifacts/predictions.csv').write_text('tampered after receipt')
    print({'phase': args.phase, 'receipt_created': True}, flush=True)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except GateClosed as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(78)
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
