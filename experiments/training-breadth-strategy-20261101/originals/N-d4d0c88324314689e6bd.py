"""主控独立复核六配置，封存干净执行件；不训练、不评分。"""
import copy
import csv
import datetime
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

C = Path(__file__).resolve().parents[1]
R = C.parents[1]
A = Path(__file__).resolve().parent
F = C / 'monitor/acceptance-continuation-01'
O = F / 'frozen/output'
I = C / 'preparation/input'
DEST = C / 'preparation/host-admitted-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not DEST.exists(), 'Do not overwrite admitted artifacts'
    freeze = json.loads((F / 'freeze-manifest.json').read_text())
    for rel, expected in freeze['output_files'].items():
        assert sha(F / 'frozen' / rel) == expected, rel
    assert freeze['registered_input_mismatches'] == []
    for name in ('training_science.py', 'train_remote_v4.py', 'encoder.py'):
        assert sha(O / name) == sha(I / 'reference' / name)
    sys.path.insert(0, str(O))
    import train_remote_v4 as production
    import training_science as science
    import numpy
    base = json.loads((I / 'base_config.json').read_text())
    req = json.loads((I / 'batch_request.json').read_text())
    expected = {(m, s) for m in science.ALLOWED_MONITORS for s in (44, 45, 46)}
    actual = set()
    assert len(list((O / 'configs').glob('*.json'))) == 6
    manifests = json.loads((O / 'batch-manifest.json').read_text())
    for entry in req['runs']:
        path = O / 'configs' / (entry['run_id'] + '.json')
        cfg = production.validate_config(json.loads(path.read_text()))
        want = copy.deepcopy(base)
        want['run_id'] = entry['run_id']; want['monitor'] = entry['monitor']
        want['head_config']['seed'] = entry['model_seed']
        assert cfg == want and cfg['split_config']['seed'] == 43
        assert next(x for x in manifests['runs'] if x['run_id'] == cfg['run_id'])['config_sha256'] == sha(path)
        actual.add((cfg['monitor'], cfg['head_config']['seed']))
    assert actual == expected
    tables, hashes, audits = science.load_input_tables(base, I, lambda p, existing: p, sha)
    assert [len(tables[k]) for k in ['train', 'valid', 'test']] == [637, 91, 182]
    assert all('Y' not in row for k in ['valid', 'test'] for row in tables[k])
    for split in tables:
        with (I / 'data' / (split + '.csv')).open(encoding='utf-8-sig', newline='') as stream:
            assert tables[split] == list(csv.DictReader(stream))
    synthetic = [{'Drug_ID': 'same', 'Drug': 'CC', 'Y': '1'},
                 {'Drug_ID': 'same', 'Drug': 'CC', 'Y': '1'},
                 {'Drug_ID': '', 'Drug': 'CCC', 'Y': '2'}]
    science.check_rows_identity(synthetic, require_y=True, label='train')
    split = science.split_train_stop_groups(synthetic, 43, .1)
    assert sorted(split['fit_row_indices'] + split['stop_row_indices']) == [0, 1, 2]
    test = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s',
                           str(R / 'tests'), '-p', 'test_prediction_table.py', '-v'],
                          capture_output=True, text=True)
    (A / 'prediction-consumer.stdout').write_text(test.stdout)
    (A / 'prediction-consumer.stderr').write_text(test.stderr)
    assert test.returncode == 0, test.stderr
    old = R / 'runs/hainan-mae-monitor-20261101/raw/execution-04/remote-snapshot/artifacts/predictions.csv'
    check = subprocess.run([sys.executable, '-B', str(R / 'scripts/check_prediction_table.py'),
                            '--predictions', str(old), '--valid', str(I / 'data/valid.csv'),
                            '--test', str(I / 'data/test.csv')], capture_output=True, text=True)
    (A / 'historical-prediction-consumer.stdout').write_text(check.stdout)
    (A / 'historical-prediction-consumer.stderr').write_text(check.stderr)
    assert check.returncode == 0, check.stderr
    DEST.mkdir()
    files = []
    for rel in ['training_science.py', 'train_remote_v4.py', 'encoder.py', 'batch-manifest.json'] + [
            str(p.relative_to(O)) for p in sorted((O / 'configs').glob('*.json'))]:
        dest = DEST / rel; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(O / rel, dest)
        assert not dest.is_symlink() and dest.stat().st_nlink == 1 and sha(dest) == sha(O / rel)
        files.append({'path': rel, 'sha256': sha(dest), 'source': str((O / rel).relative_to(C))})
    (DEST / 'MANIFEST.json').write_text(json.dumps({'files': files,
        'self_excluded': True, 'source_outputs_untouched': True}, indent=2) + '\n')
    result = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'science_configs_admitted': True, 'preparation_skill_behavior_passed': False,
        'training_execution_admitted': False, 'runtime_review_pending': True,
        'frozen_outputs_verified': len(freeze['output_files']), 'grid': sorted(actual),
        'numpy_version': numpy.__version__, 'training_steps': 0, 'private_valid_access': False,
        'prediction_consumer_synthetic_exit': test.returncode,
        'historical_273_prediction_consumer_exit': check.returncode,
        'preserved_failures': ['input pycache writes in original round',
            'self-referential/still-changing output manifest', 'tail exit mislabeled as suite exit',
            'complete-row-key negative case not actually constructed'],
        'upstream_contract_issue': 'Preparation was not given the actual host prediction consumer; loader attributes and exported composite keys were conflated in the task. Main supplied and tested the real consumer separately; original verdict is not rewritten.',
        'admitted_manifest_sha256': sha(DEST / 'MANIFEST.json')}
    (A / 'preparation-result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
