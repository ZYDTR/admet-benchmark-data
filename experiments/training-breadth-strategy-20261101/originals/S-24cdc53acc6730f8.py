"""Raw-SMILES exposure diagnostic for validation, using approved local inputs only."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
snapshot = BASE / 'data-snapshot'
audit = json.loads((BASE / 'data-audit/dataset-audit.json').read_text())
folders = {p.name: p for p in (snapshot / 'data_benchmark').iterdir() if p.is_dir()}
train_smiles = {}
hashes = {}
for task, folder in folders.items():
    path = folder / 'train.csv'
    hashes[str(path.relative_to(snapshot))] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding='utf-8-sig', newline='') as handle:
        train_smiles[task] = {row['Drug'] for row in csv.DictReader(handle)}

tasks = {}
for task, folder in sorted(folders.items()):
    other_train = set().union(*(smiles for other, smiles in train_smiles.items() if other != task))
    path = folder / 'valid.csv'
    hashes[str(path.relative_to(snapshot))] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding='utf-8-sig', newline='') as handle:
        rows = [{'smiles': r['Drug'], 'y': r['Y']} for r in csv.DictReader(handle)]
    groups = {
        'exposed_to_other_task_train': [r for r in rows if r['smiles'] in other_train],
        'unexposed_to_other_task_train': [r for r in rows if r['smiles'] not in other_train],
    }
    metric = audit['tasks'][task]['metric'][0]
    entry = {'metric': metric, 'valid_rows': len(rows), 'groups': {}}
    for group, selected in groups.items():
        info = {'rows': len(selected), 'unique_raw_smiles': len({r['smiles'] for r in selected})}
        if metric in ('AUPRC', 'AUROC'):
            labels = Counter(float(r['y']) for r in selected)
            info.update({'positive_rows': labels[1.0], 'negative_rows': labels[0.0], 'both_classes_present': labels[1.0] > 0 and labels[0.0] > 0})
        entry['groups'][group] = info
    assert len(groups['exposed_to_other_task_train']) == audit['tasks'][task]['cross_task_overlap']['valid_rows_with_raw_smiles_in_another_tasks_train']
    tasks[task] = entry

result = {
    'commit': '0275588ac7a5d3df032ec7dc0794cab21dfcfeeb',
    'scope': 'Read-only reaggregation of train molecular strings and validation labels. No test data or labels read.',
    'definition': 'Validation row exposure means exact raw SMILES is present in at least one other task original train.csv. This is not proof of forbidden leakage; it describes an estimand boundary for multi-task learning.',
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'source_sha256': hashes,
    'tasks': tasks,
}
output = BASE / 'validation/mtl-exposure-review.json'
output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'output': str(output), 'tasks': len(tasks), 'all_exposure_counts_match_original_audit': True}))
