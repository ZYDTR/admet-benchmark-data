"""Local admission checks only; not a remote execution or isolation mechanism."""
import csv
import hashlib
from pathlib import Path

ENCODER_SHA = 'c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def regular_inside(path, root):
    path, root = Path(path), Path(root).resolve(strict=True)
    resolved = path.resolve(strict=True)
    resolved.relative_to(root)
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError(f'linked input: {path}')
        if current.parent == current:
            raise ValueError(f'non-canonical input: {path}')
        current = current.parent
    if not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError(f'input must be a single-link regular file: {path}')
    return path


def check(plan, baseline_root, policy_path, skill_path):
    # Explicitly authorized runs only. A new name alone does not grant compute scope.
    admitted_runs = {'hainan-skill-pilot-20261030', 'hainan-frozen-training-20261031',
                     'hainan-skill-follow-20261031', 'hainan-index-cycle-20261031',
                     'hainan-mae-monitor-20261101'}
    if plan.get('run_id') not in admitted_runs:
        raise ValueError('unregistered run')
    required = {
        'schema_version': 1,
        'pretrained_backbone_frozen': True, 'training_labels': 'official_train_only',
        'validation_labels_allowed': False, 'external_labels_allowed': False,
        'test_fitting_allowed': False, 'new_cleaning_allowed': False,
        'official_upload_allowed': False, 'device': 'cuda',
        'max_concurrent_jobs': 1, 'task': 'caco2_wang',
        'remote_directory': '<AUTHORIZED_PROJECT_ROOT>/admet/' + plan['run_id'],
    }
    for key, expected in required.items():
        if type(plan.get(key)) is not type(expected) or plan[key] != expected:
            raise ValueError(f'contract mismatch: {key}')
    if plan.get('resource_budget', {}).get('gpu_count') != 1:
        raise ValueError('pilot requires one GPU')
    if plan['policy_sha256'] != digest(policy_path):
        raise ValueError('policy changed')
    if plan['hainan_skill_sha256'] != digest(skill_path):
        raise ValueError('skill changed; review and version the plan')
    asset = regular_inside(plan['pretrained_backbone_path'], baseline_root)
    if plan['pretrained_backbone_sha256'] != ENCODER_SHA or digest(asset) != ENCODER_SHA:
        raise ValueError('pretrained asset mismatch')
    files = plan['inputs']
    if len(files) != 3 or {f['role'] for f in files} != {'train', 'validation', 'test'}:
        raise ValueError('expected exactly three data roles')
    counts = {}
    expected_rows = {'train': 637, 'validation': 91, 'test': 182}
    for entry in files:
        role = entry['role']
        if entry['task'] != plan['task']:
            raise ValueError('task mismatch')
        path = regular_inside(entry['path'], baseline_root / 'execution' / 'data')
        if digest(path) != entry['sha256']:
            raise ValueError(f'input digest mismatch: {role}')
        with path.open(newline='', encoding='utf-8-sig') as stream:
            reader = csv.DictReader(stream)
            expected = ['Drug_ID', 'Drug', 'Y'] if role == 'train' else ['Drug_ID', 'Drug']
            if reader.fieldnames != expected:
                raise ValueError(f'input columns mismatch: {role}')
            count = sum(1 for _ in reader)
        if count != entry['rows'] or count != expected_rows[role]:
            raise ValueError(f'row count mismatch: {role}')
        counts[role] = count
    return {'passed': True, 'run_id': plan['run_id'], 'rows': counts,
            'checks': ['fixed_scope', 'frozen_policy', 'policy_and_skill_identity',
                       'asset_identity', 'input_identity', 'label_separation'],
            'not_proven': ['remote_identity', 'resource_availability', 'runtime_freeze',
                           'gpu_training', 'write_scope', 'other_job_noninterference']}
