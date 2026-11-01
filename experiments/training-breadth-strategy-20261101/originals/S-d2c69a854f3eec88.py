"""Review-only stdlib parsing. Does not import or execute any archived program."""
from pathlib import Path
import collections
import csv
import hashlib
import io
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'agent-reviews'
manifest = json.loads((ROOT / 'manifest.json').read_text())
manifest_by_path = {v['path']: v for v in manifest['payload_files']}
files = {}

def record(path, coverage):
    path = Path(path)
    b = path.read_bytes()
    rel = str(path.relative_to(ROOT))
    t = b.decode('utf-8-sig')
    actual_sha = hashlib.sha256(b).hexdigest()
    expected = manifest_by_path.get(rel)
    entry = {'path': rel, 'bytes': len(b), 'lines': len(t.splitlines()),
             'sha256': actual_sha, 'coverage': coverage,
             'manifest_match': None if expected is None else actual_sha == expected['sha256'] and len(b) == expected['bytes']}
    if path.suffix == '.json':
        value = json.loads(t)
        entry['parsed_type'] = type(value).__name__
        if isinstance(value, list):
            entry['records'] = len(value)
        if isinstance(value, dict) and isinstance(value.get('entries'), list):
            entry['records'] = len(value['entries'])
    elif path.suffix == '.jsonl':
        rows = [json.loads(x) for x in t.splitlines() if x.strip()]
        entry['records'] = len(rows)
    files[rel] = entry
    return t

for rel in ['START_HERE.md', 'manifest.json', 'source-map.json',
            'environment/ENVIRONMENT.md', 'environment/pyvenv.cfg', 'environment/packages.json',
            'research/current-research-context.md', 'research/evidence/rule-source-metadata.json']:
    record(ROOT / rel, 'full_text_or_all_structured_records; inspected applicable fields')
for folder in ['evidence', 'rules']:
    for path in sorted((ROOT / folder).iterdir()):
        if path.is_file():
            record(path, 'full_text_or_all_structured_records')
record(ROOT / 'research/evidence/chemistry-audit.json', 'parsed_all; inspected rdkit_version and chemistry provenance only, not all task statistics')
record(ROOT / 'agent-reviews/rules-data.md', 'independent cross-check of F1, historical audit pending and unpublished evidence coverage; reviewer artifact not packet payload')

run_summaries = {}
for run_id in ['hainan-frozen-training-20261031', 'hainan-skill-follow-20261031']:
    r = ROOT / 'runs' / run_id
    for name in ['PLAN.json', 'audit-summary.json', 'historical-acceptance.md', 'native-adapter-reference.json']:
        record(r / name, 'full_text_or_all_structured_records')
    for name in ['common_remote.py', 'common_guarded.py', 'guard_exec_v3.py', 'supervisor.py', 'avoid_thread_name.c', 'guard_exec_cuda02.py', 'supervisor_attempt02.py']:
        path = r / 'source' / name
        if path.exists():
            record(path, 'full_text static review only; not executed')
    record(r / 'source/train_remote_v3.py', 'full_text read; targeted static inspection of optimizer, seeds, recording, checkpoint and reload code; not executed')
    te = json.loads(record(r / 'artifacts/training-evidence.json', 'all JSON records parsed; epoch chronology, counters, timing and peak resource fields inspected'))
    raw_counts = collections.Counter()
    for path in sorted((r / 'raw').iterdir()):
        if path.suffix in ['.json', '.jsonl', '.log']:
            text = record(path, 'all JSON/JSONL records parsed or full log text read; runtime/exit/guard/phase fields inspected')
            raw_counts[path.suffix] += 1
            if path.suffix == '.log':
                events = []
                for i, line in enumerate(text.splitlines(), 1):
                    try:
                        events.append((i, json.loads(line)))
                    except json.JSONDecodeError:
                        pass
                files[str(path.relative_to(ROOT))]['json_event_rows'] = [i for i, _ in events]
    phases = []
    for path in sorted((r / 'raw').glob('*-exit.json')):
        phase = path.name.removesuffix('-exit.json')
        exit_record = json.loads(path.read_text())
        ob_path = r / 'raw' / (phase + '-observations.jsonl')
        observations = [json.loads(s) for s in ob_path.read_text().splitlines() if s.strip()]
        gpu = []
        for index, ob in enumerate(observations, 1):
            for row in csv.reader(io.StringIO(ob.get('gpu', ''))):
                if len(row) == 3:
                    gpu.append({'record': index, 'memory_mib': int(row[1].strip()), 'utilization_percent': int(row[2].strip())})
        phases.append({'phase': phase, 'exit': exit_record,
                       'observation_count': len(observations),
                       'peak_tree_rss_computed_from_all_observations': max(x.get('rss_bytes', 0) for x in observations),
                       'peak_selected_device_memory_mib': max(x['memory_mib'] for x in gpu),
                       'peak_selected_device_memory_records': [x['record'] for x in gpu if x['memory_mib'] == max(g['memory_mib'] for g in gpu)],
                       'warning': 'Selected-device memory includes CUDA context and any other process; it is not own-process GPU memory or a continuous peak.'})
    train_log = (r / 'raw/train01.log').read_text().splitlines()
    epoch_events = []
    for i, line in enumerate(train_log, 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get('phase') == 'head_training':
            epoch_events.append((i, event))
    matching_history = all({k: v for k, v in ev.items() if k != 'phase'} == h
                           for (_, ev), h in zip(epoch_events, te['history'])) and len(epoch_events) == len(te['history'])
    run_summaries[run_id] = {'raw_file_counts': dict(raw_counts), 'phases': phases,
                            'epoch_count': te['epochs_run'], 'optimizer_steps': te['optimizer_steps'],
                            'best_epoch_1_based': te['best_epoch_1_based'],
                            'train_log_epoch_line_numbers': [i for i, _ in epoch_events],
                            'log_epochs_equal_training_evidence_history': matching_history,
                            'model_elapsed_seconds': te['elapsed_seconds'],
                            'cuda_peak_allocated_bytes': te['cuda_peak_allocated_bytes'],
                            'cuda_peak_reserved_bytes': te['cuda_peak_reserved_bytes'],
                            'runtime': json.loads((r / 'raw/train-runtime.json').read_text())}

critical = ['chemprop-2.2.1', 'torch-2.6.0', 'rdkit-2024.9.6', 'numpy-1.26.4', 'joblib-1.6.0', 'pytorch_lightning-2.5.1', 'scikit_learn-1.6.1']
env_summary = []
for dist in critical:
    d = ROOT / 'environment/lib/python3.12/site-packages' / (dist + '.dist-info')
    metadata = record(d / 'METADATA', 'entire bytes read; headers and all Requires-Dist fields inspected, long description not scientifically audited')
    wheel = record(d / 'WHEEL', 'all wheel fields inspected')
    record_text = record(d / 'RECORD', 'all CSV records parsed; package file list/hash declarations inspected; implementation bytes unavailable')
    rows = list(csv.reader(io.StringIO(record_text)))
    header = {}
    for line in metadata.splitlines():
        if line.startswith(('Name:', 'Version:', 'Requires-Python:')):
            k, v = line.split(':', 1)
            header[k] = v.strip()
    env_summary.append({'distribution': dist, 'headers': header, 'wheel': wheel.strip().splitlines(),
                        'record_rows': len(rows), 'all_rows_have_three_columns': all(len(r) == 3 for r in rows),
                        'hashless_record_rows': sum(not r[1] for r in rows),
                        'requires_dist_count': sum(l.startswith('Requires-Dist:') for l in metadata.splitlines())})

receipt = {'schema_version': '1.0', 'reviewer_perspective': 'reproducibility-process-records',
           'request_id': 'admet-public-repo-pro-20261031-001', 'round_id': 'public-repo-round001',
           'fixed_commit': 'eaec280cf142839597fe75ce748cd2b9a8a897d4',
           'manifest_sha256_expected': 'dbdec244caa8ddb106721877cf93625c1957b9184985c07b1cf751eed5d70505',
           'manifest_sha256_actual': hashlib.sha256((ROOT / 'manifest.json').read_bytes()).hexdigest(),
           'method': 'Only local Python standard-library text/JSON/CSV parsing. No archive imports, pickle/model/native execution, package install, remote server access, training, inference or scoring.',
           'files': list(files.values()),
           'manifest_match_failures': [v['path'] for v in files.values() if v['manifest_match'] is False],
           'raw_record_inspection': run_summaries,
           'environment': {'index_distribution_count': len(json.loads((ROOT / 'environment/packages.json').read_text())), 'critical_distribution_details': env_summary,
                           'coverage_limit': 'All 78 package version entries read, 7 critical METADATA/WHEEL/RECORD sets deeply inspected. Other dependency implementation or metadata prose not audited by this perspective. No package import or file-byte verification using RECORD installed paths.'},
           'not_read_or_not_available': ['Original full strace', 'Native adapter .so', 'External CheMeleon checkpoint bytes', 'Full installed dependency implementations and interpreter bytes', 'Excluded original parent control/transport/acceptance artifacts', 'Private valid/test labels or labeled scoring workfiles', 'Global historical experiments/failures/issues/disproved-hypotheses ledger', 'Full original official API response', 'Original F1 command transcript and fault-injection report as standalone public artifacts'],
           'alignment': 'This perspective verified phase/config/source provenance and epoch log alignment; independent CSV task/split/row_index checks are owned by rules/statistics/root routes. It does not independently claim to have rechecked prediction rows.'}
OUT.mkdir(exist_ok=True)
(OUT / 'repro-records-read-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'read_files': len(files), 'manifest_match_failures': receipt['manifest_match_failures'], 'run_epoch_matches': {k:v['log_epochs_equal_training_evidence_history'] for k,v in run_summaries.items()}, 'critical_environment_distributions': env_summary}, ensure_ascii=False, indent=2))
