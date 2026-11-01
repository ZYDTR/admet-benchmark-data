"""Read-only structural audit of the user-provided official ZIP and public template."""
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo
import zipfile

BASE = Path(__file__).resolve().parent
ZIP = Path('<LOCAL_PRIVATE_PATH>')
TEMPLATE = BASE.parent / 'parallel-review/rules-evidence/official-template.csv'
SCHEMA = BASE.parent / 'original/admet-agent-harness/competition/task_schema.json'
expected = {x['task']: x for x in json.loads(SCHEMA.read_text())['tasks']}
with TEMPLATE.open(encoding='utf-8-sig', newline='') as f:
    template_rows = list(csv.DictReader(f, strict=True))
template_by_task = defaultdict(list)
for row in template_rows:
    template_by_task[row['task']].append(row)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def quantile(values, p):
    v = sorted(values)
    pos = (len(v) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)


all_data = defaultdict(dict)
file_stats = []
issues = []
with zipfile.ZipFile(ZIP) as z:
    bad_crc = z.testzip()
    entries = z.infolist()
    names = [x.filename for x in entries]
    duplicate_archive_entries = [k for k, v in Counter(names).items() if v > 1]
    unsafe_names = [n for n in names if PurePosixPath(n).is_absolute() or '..' in PurePosixPath(n).parts]
    regular_names = [x.filename for x in entries if not x.is_dir()]
    for name in regular_names:
        parts = PurePosixPath(name).parts
        if len(parts) != 3 or parts[0] != 'data_benchmark' or parts[2] not in ('train.csv', 'valid.csv', 'test.csv'):
            issues.append({'file': name, 'issue': 'unexpected_file'})
            continue
        task, split = parts[1], parts[2][:-4]
        raw = z.read(name)
        parsed = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True))
        header, body = parsed[0], parsed[1:]
        desired = ['Drug_ID', 'Drug'] + ([] if split == 'test' else ['Y'])
        if header != desired:
            issues.append({'file': name, 'issue': 'unexpected_header', 'header': header})
        width_errors = [i for i, r in enumerate(body) if len(r) != len(header)]
        if width_errors:
            issues.append({'file': name, 'issue': 'row_width', 'sample_idxs': width_errors})
        rows = [dict(zip(header, r)) for r in body]
        all_data[task][split] = rows
        drug_counts = Counter(r.get('Drug', '') for r in rows)
        id_counts = Counter(r.get('Drug_ID', '') for r in rows)
        values, bad_labels = [], []
        for i, row in enumerate(rows):
            if split == 'test':
                continue
            try:
                value = float(row.get('Y', ''))
                if not math.isfinite(value):
                    raise ValueError('nonfinite')
                values.append(value)
            except ValueError:
                bad_labels.append({'sample_idx': i, 'value': row.get('Y')})
        label_stats = None
        if split != 'test':
            label_stats = {'nonfinite_or_nonnumeric': bad_labels, 'blank_count': sum(not r.get('Y', '').strip() for r in rows)}
            if values:
                label_stats.update({'min': min(values), 'max': max(values), 'q01': quantile(values, .01), 'median': quantile(values, .5), 'q99': quantile(values, .99), 'unique_values': len(set(values))})
            if expected.get(task, {}).get('kind') == 'classification':
                label_stats['class_counts'] = dict(Counter(str(v) for v in values))
                if not set(values) <= {0.0, 1.0}:
                    issues.append({'file': name, 'issue': 'non_binary_labels'})
        stats = {'file': name, 'task': task, 'split': split, 'bytes': len(raw), 'sha256': sha(raw), 'header': header,
                 'rows': len(rows), 'blank_smiles': sum(not r.get('Drug', '').strip() for r in rows),
                 'blank_ids': sum(r.get('Drug_ID', '') == '' for r in rows),
                 'duplicate_exact_smiles_keys': sum(v > 1 for v in drug_counts.values()),
                 'duplicate_exact_smiles_extra_rows': sum(v - 1 for v in drug_counts.values()),
                 'duplicate_id_keys': sum(v > 1 for v in id_counts.values()),
                 'duplicate_id_extra_rows': sum(v - 1 for v in id_counts.values()), 'label_stats': label_stats}
        file_stats.append(stats)

task_stats = []
template_mismatches = []
all_train_smiles = set()
all_valid_smiles = set()
all_test_smiles = set()
for splits in all_data.values():
    all_train_smiles.update(r['Drug'] for r in splits.get('train', []))
    all_valid_smiles.update(r['Drug'] for r in splits.get('valid', []))
    all_test_smiles.update(r['Drug'] for r in splits.get('test', []))

for task in sorted(set(expected) | set(all_data)):
    splits = all_data.get(task, {})
    absent = sorted({'train', 'valid', 'test'} - set(splits))
    if absent:
        issues.append({'task': task, 'issue': 'missing_splits', 'splits': absent})
    molecules = {s: {r['Drug'] for r in splits.get(s, [])} for s in ('train', 'valid', 'test')}
    overlap = {}
    for a, b in [('train', 'valid'), ('train', 'test'), ('valid', 'test')]:
        common = molecules[a] & molecules[b]
        overlap[a + '_' + b] = {'unique_exact_smiles': len(common),
            a + '_rows': sum(r['Drug'] in common for r in splits.get(a, [])),
            b + '_rows': sum(r['Drug'] in common for r in splits.get(b, []))}
    conflicting = []
    for split in ('train', 'valid', 'train+valid'):
        rws = splits.get(split, []) if split != 'train+valid' else splits.get('train', []) + splits.get('valid', [])
        labels = defaultdict(set)
        numeric_labels = defaultdict(set)
        for row in rws:
            labels[row['Drug']].add(row.get('Y', ''))
            try:
                value = float(row.get('Y', ''))
                if math.isfinite(value):
                    numeric_labels[row['Drug']].add(value)
            except ValueError:
                pass
        conflicts = {smiles: list(ys) for smiles, ys in labels.items() if len(ys) > 1}
        conflicting.append({'scope': split, 'exact_smiles_with_distinct_raw_labels': len(conflicts),
                            'exact_smiles_with_distinct_numeric_labels': sum(len(ys) > 1 for ys in numeric_labels.values())})
    trows = template_by_task.get(task, [])
    test = splits.get('test', [])
    if len(trows) != len(test):
        template_mismatches.append({'task': task, 'issue': 'row_count', 'template': len(trows), 'test': len(test)})
    for index, row in enumerate(trows):
        if index >= len(test):
            break
        actual = test[index]
        failures = []
        if row['sample_idx'] != str(index): failures.append('sample_idx_not_row_position')
        if row['drug_id'] != actual['Drug_ID']: failures.append('drug_id')
        if row['smiles'] != actual['Drug']: failures.append('smiles')
        if row['metric'] != expected.get(task, {}).get('metric'): failures.append('metric')
        if failures:
            template_mismatches.append({'task': task, 'sample_idx': index, 'mismatched_fields': failures})
    other_train = set().union(*(molecules_other for name, ss in all_data.items() if name != task
                              for molecules_other in [{r['Drug'] for r in ss.get('train', [])}]))
    cross_task = {split: {'unique_exact_smiles_seen_in_other_tasks_train': len(molecules[split] & other_train),
                          'rows_seen_in_other_tasks_train': sum(r['Drug'] in other_train for r in splits.get(split, []))}
                  for split in ('valid', 'test')}
    task_stats.append({'task': task, 'kind': expected.get(task, {}).get('kind'), 'metric': expected.get(task, {}).get('metric'),
                       'row_counts': {s: len(splits.get(s, [])) for s in ('train', 'valid', 'test')},
                       'within_task_exact_smiles_overlap': overlap, 'raw_label_conflicts': conflicting,
                       'cross_task_overlap': cross_task})

report = {'audited_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(), 'source_path': str(ZIP),
          'source_attestation': 'User confirmed in current conversation that ZIP was obtained from official registration/download page; authenticated download was not independently replayed.',
          'zip_bytes': ZIP.stat().st_size, 'zip_sha256': sha(ZIP.read_bytes()), 'crc_failure': bad_crc,
          'regular_file_count': len(regular_names), 'uncompressed_bytes': sum(f['bytes'] for f in file_stats),
          'duplicate_archive_entries': duplicate_archive_entries, 'unsafe_archive_paths': unsafe_names,
          'unexpected_tasks': sorted(set(all_data) - set(expected)), 'missing_tasks': sorted(set(expected) - set(all_data)),
          'total_rows': {s: sum(t['row_counts'][s] for t in task_stats) for s in ('train', 'valid', 'test')},
          'unique_exact_smiles': {'train': len(all_train_smiles), 'valid': len(all_valid_smiles), 'test': len(all_test_smiles),
                                  'all_splits': len(all_train_smiles | all_valid_smiles | all_test_smiles)},
          'cross_task_note': 'String equality only. Cross-task overlap is an observed property, not proof of cheating or same-endpoint label leakage. Molecular canonicalization/scaffold analysis not performed here.',
          'template_path': str(TEMPLATE), 'template_sha256': sha(TEMPLATE.read_bytes()),
          'template_rows': len(template_rows), 'template_mismatches': template_mismatches, 'structural_issues': issues,
          'files': file_stats, 'tasks': task_stats,
          'limits': ['No official explanatory README, units or positive-class definitions supplied in this ZIP.',
                     'No chemistry-aware SMILES validity or equivalence test performed by this script.',
                     'No model training, source approval update or original project edit.']}
(BASE / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
with (BASE / 'task-summary.csv').open('w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['task', 'kind', 'metric', 'train_rows', 'valid_rows', 'test_rows', 'train_valid_exact_smiles_overlap', 'train_test_exact_smiles_overlap', 'valid_test_exact_smiles_overlap', 'valid_rows_seen_in_other_tasks_train', 'test_rows_seen_in_other_tasks_train'])
    for task in task_stats:
        writer.writerow([task['task'], task['kind'], task['metric'], *task['row_counts'].values(),
                         *(task['within_task_exact_smiles_overlap'][key]['unique_exact_smiles'] for key in ('train_valid', 'train_test', 'valid_test')),
                         task['cross_task_overlap']['valid']['rows_seen_in_other_tasks_train'], task['cross_task_overlap']['test']['rows_seen_in_other_tasks_train']])
print(json.dumps({key: report[key] for key in ['zip_bytes', 'zip_sha256', 'crc_failure', 'regular_file_count', 'uncompressed_bytes', 'missing_tasks', 'unexpected_tasks', 'total_rows', 'unique_exact_smiles', 'template_mismatches', 'structural_issues']}, ensure_ascii=False, indent=2))
for task in task_stats:
    print(json.dumps(task, ensure_ascii=False))
for f in file_stats:
    if f['blank_ids'] or f['blank_smiles'] or (f['label_stats'] and (f['label_stats']['nonfinite_or_nonnumeric'] or f['label_stats']['blank_count'])):
        print('FIELD_WARNING', json.dumps(f, ensure_ascii=False))
