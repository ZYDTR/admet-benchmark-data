"""Shared utilities and registered input expectations.

Registered expectations freeze the 2026-10-30 snapshot recorded in
research/data-profile.md and reference-harness/competition/{contract,task_schema}.json.
Live files remain the primary source; registered values are cross-checks only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import os
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = 'admet_eval'
TOOL_VERSION = '1.0.0'

TEMPLATE_COLUMNS = ['task', 'sample_idx', 'drug_id', 'smiles', 'y_pred', 'metric']
PRED_COLUMNS = ('task', 'split', 'row_index', 'y_pred')
SPLITS = ('train', 'valid', 'test')
SPLIT_SOURCES = {
    'train': ('data_benchmark', 'train.csv'),
    'test': ('data_benchmark', 'test.csv'),
    'valid': ('blind_validation', 'valid.csv'),
}
OFFICIAL_LABEL_COLUMNS = ['Drug_ID', 'Drug', 'Y']
LONG_LABEL_REQUIRED_COLUMNS = ('task', 'row_index', 'y_true')
CLASSIFICATION_METRICS = ('AUROC', 'AUPRC')
REGRESSION_METRICS = ('MAE', 'Spearman')

REGISTERED_TEMPLATE_SHA256 = (
    '8ee41589d2c98e7b93081c058b3f928ac09bea4b3ffc899fa13677051e9baa20'
)
REGISTERED_TOTALS = {
    'tasks': 22,
    'train_rows': 53695,
    'validation_rows': 11735,
    'test_rows': 16379,
    'template_rows': 16379,
}
REGISTERED_BLANK_DRUG_ID_COUNT = 1

REGISTERED_TASK_COUNTS = {
    'ames': (4684, 1137, 1457),
    'bbb_martins': (1421, 203, 406),
    'bioavailability_ma': (448, 64, 128),
    'caco2_wang': (637, 91, 182),
    'clearance_hepatocyte_az': (848, 122, 243),
    'clearance_microsome_az': (770, 111, 221),
    'cyp2c9_substrate_carbonmangels': (467, 67, 135),
    'cyp2c9_veith': (8463, 1210, 2419),
    'cyp2d6_substrate_carbonmangels': (465, 67, 135),
    'cyp2d6_veith': (9191, 1313, 2626),
    'cyp3a4_substrate_carbonmangels': (468, 67, 135),
    'cyp3a4_veith': (8628, 1233, 2467),
    'dili': (331, 48, 96),
    'half_life_obach': (465, 67, 135),
    'herg': (457, 66, 132),
    'hia_hou': (403, 58, 117),
    'ld50_zhu': (3970, 1937, 1478),
    'lipophilicity_astrazeneca': (2940, 420, 840),
    'pgp_broccatelli': (851, 122, 245),
    'ppbr_az': (1952, 279, 559),
    'solubility_aqsoldb': (5045, 2940, 1997),
    'vdss_lombardo': (791, 113, 226),
}

REGISTERED_METRICS = {
    'ames': 'AUROC',
    'bbb_martins': 'AUROC',
    'bioavailability_ma': 'AUROC',
    'caco2_wang': 'MAE',
    'clearance_hepatocyte_az': 'Spearman',
    'clearance_microsome_az': 'Spearman',
    'cyp2c9_substrate_carbonmangels': 'AUPRC',
    'cyp2c9_veith': 'AUPRC',
    'cyp2d6_substrate_carbonmangels': 'AUPRC',
    'cyp2d6_veith': 'AUPRC',
    'cyp3a4_substrate_carbonmangels': 'AUROC',
    'cyp3a4_veith': 'AUPRC',
    'dili': 'AUROC',
    'half_life_obach': 'Spearman',
    'herg': 'AUROC',
    'hia_hou': 'AUROC',
    'ld50_zhu': 'MAE',
    'lipophilicity_astrazeneca': 'MAE',
    'pgp_broccatelli': 'AUROC',
    'ppbr_az': 'MAE',
    'solubility_aqsoldb': 'MAE',
    'vdss_lombardo': 'Spearman',
}

REGISTERED_METRIC_HISTOGRAM = {'AUROC': 8, 'AUPRC': 5, 'MAE': 5, 'Spearman': 4}


class ContractError(RuntimeError):
    pass


def utc_now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _package_dir():
    return Path(__file__).resolve().parent


def find_data_root(explicit=None):
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get('ADMET_EVAL_DATA_ROOT')
    if env:
        candidates.append(Path(env))
    pkg = _package_dir()
    for depth in (2, 3, 4):
        candidates.append(pkg.parents[depth] if len(pkg.parents) > depth else None)
    candidates.append(Path.cwd())
    for cand in candidates:
        if cand is None:
            continue
        cand = Path(cand)
        if (cand / 'data' / 'official' / 'submission_template.csv').is_file():
            return str(cand)
    if explicit:
        raise ContractError('data root not found at %s (missing data/official/submission_template.csv)' % explicit)
    raise ContractError(
        'could not locate data root; pass --data-root pointing at the project root '
        'that contains data/official/submission_template.csv'
    )


def default_template_path(data_root):
    return os.path.join(data_root, 'data', 'official', 'submission_template.csv')


def default_schema_path():
    here = _package_dir()
    for depth in (2, 3, 4):
        if len(here.parents) > depth:
            cand = here.parents[depth] / 'reference-harness' / 'competition' / 'task_schema.json'
            if cand.is_file():
                return str(cand)
    for cand in (Path.cwd() / 'reference-harness' / 'competition' / 'task_schema.json',):
        if cand.is_file():
            return str(cand)
    return None


def read_csv(path):
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        raise ContractError('empty CSV file: %s' % path)
    return rows[0], rows[1:]


def parse_csv_text(text):
    return list(csv.reader(io.StringIO(text, newline='')))


def parse_csv_line(line):
    rows = list(csv.reader(io.StringIO(line, newline='')))
    if len(rows) != 1:
        raise ContractError('line parses to %d rows: %r' % (len(rows), line[:80]))
    return rows[0]


def has_bom(raw):
    return raw[:3] == b'\xef\xbb\xbf'


def split_crlf_lines(text):
    """Split text into lines, requiring pure CRLF endings and a trailing CRLF."""
    n_lf = text.count('\n')
    n_crlf = text.count('\r\n')
    if n_lf != n_crlf:
        raise ContractError('line endings are not pure CRLF (LF=%d, CRLF=%d)' % (n_lf, n_crlf))
    if not text.endswith('\r\n'):
        raise ContractError('text does not end with CRLF')
    lines = text.split('\r\n')
    if lines[-1] != '':
        raise ContractError('unexpected content after final CRLF')
    return lines[:-1]


def csv_field_spans(line):
    """Return [(start, end), ...] raw field spans of one CSV line.

    Mirrors Python csv.reader default dialect lenient semantics: a field is
    quoted only when it starts with the quote character; inside quotes an
    doubled quote is an escaped quote; text after the closing quote up to the
    delimiter is appended literally; a quote elsewhere is literal data.
    """
    spans = []
    n = len(line)
    field_start = 0
    i = 0
    in_quotes = False
    while i < n:
        c = line[i]
        if in_quotes:
            if c == '"':
                if i + 1 < n and line[i + 1] == '"':
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            i += 1
            continue
        if c == ',':
            spans.append((field_start, i))
            i += 1
            field_start = i
            continue
        if c == '"' and i == field_start:
            in_quotes = True
            i += 1
            continue
        i += 1
    spans.append((field_start, n))
    return spans


def load_task_names(data_root):
    bench = os.path.join(data_root, 'data', 'official', 'data_benchmark')
    if not os.path.isdir(bench):
        raise ContractError('missing benchmark directory: %s' % bench)
    tasks = sorted(
        d for d in os.listdir(bench)
        if os.path.isdir(os.path.join(bench, d))
    )
    if not tasks:
        raise ContractError('no task directories under %s' % bench)
    return tasks


def split_path(data_root, task, split):
    subdir, filename = SPLIT_SOURCES[split]
    if split in ('train', 'test'):
        return os.path.join(data_root, 'data', 'official', 'data_benchmark', task, filename)
    return os.path.join(data_root, 'data', 'blind_validation', task, filename)


def load_split(data_root, task, split):
    path = split_path(data_root, task, split)
    if not os.path.isfile(path):
        raise ContractError('missing %s file for task %s: %s' % (split, task, path))
    return read_csv(path)


def load_template_rows(template_path):
    with open(template_path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8-sig')
    rows = parse_csv_text(text)
    if not rows:
        raise ContractError('empty template: %s' % template_path)
    return rows[0], rows[1:], raw


def metric_map_from_template(template_rows):
    mapping = {}
    errors = []
    for i, r in enumerate(template_rows, start=2):
        if len(r) != len(TEMPLATE_COLUMNS):
            errors.append('template line %d: %d fields (expected %d)' % (i, len(r), len(TEMPLATE_COLUMNS)))
            continue
        task, _sidx, _did, _smi, _yp, metric = r
        if task not in mapping:
            mapping[task] = metric
        elif mapping[task] != metric:
            errors.append('template line %d: task %s has conflicting metrics %r/%r' % (i, task, mapping[task], metric))
    if errors:
        raise ContractError('malformed template metric column: ' + '; '.join(errors[:5]))
    return mapping


class PredictionRow:
    __slots__ = ('task', 'split', 'row_index', 'y_pred', 'line_no')

    def __init__(self, task, split, row_index, y_pred, line_no):
        self.task = task
        self.split = split
        self.row_index = row_index
        self.y_pred = y_pred
        self.line_no = line_no

    def key(self):
        return (self.task, self.split, self.row_index)


def load_predictions_csv(path):
    """Load a prediction file with the strict contract task,split,row_index,y_pred."""
    import math

    header, rows = read_csv(path)
    if sorted(header) != sorted(PRED_COLUMNS) or len(header) != len(PRED_COLUMNS):
        raise ContractError(
            'prediction file %s must contain exactly the columns %s (order free), got %r'
            % (path, list(PRED_COLUMNS), header)
        )
    idx = {name: header.index(name) for name in PRED_COLUMNS}
    parsed = []
    errors = []
    for i, r in enumerate(rows, start=2):
        if len(r) != len(header):
            errors.append('line %d: %d fields (expected %d)' % (i, len(r), len(header)))
            continue
        task = r[idx['task']]
        split = r[idx['split']]
        row_index_raw = r[idx['row_index']]
        y_pred_raw = r[idx['y_pred']]
        line_no = i
        try:
            row_index = int(row_index_raw)
            if str(row_index) != row_index_raw.strip():
                raise ValueError(row_index_raw)
        except ValueError:
            errors.append('line %d: row_index %r is not an integer' % (line_no, row_index_raw))
            continue
        try:
            y_pred = float(y_pred_raw)
            if not math.isfinite(y_pred):
                raise ValueError(y_pred_raw)
        except ValueError:
            errors.append('line %d: y_pred %r is not a finite number' % (line_no, y_pred_raw))
            continue
        if split not in SPLITS:
            errors.append('line %d: split %r not in %s' % (line_no, split, list(SPLITS)))
            continue
        parsed.append(PredictionRow(task, split, row_index, y_pred, line_no))
    if errors:
        raise ContractError('prediction file contract violations: ' + '; '.join(errors[:10]) +
                            (' (%d errors total)' % len(errors) if len(errors) > 10 else ''))
    return parsed


def verify_template_test_alignment(data_root, template_rows):
    """Verify that template (task, sample_idx) maps to test.csv row_index.

    For each task the check requires, in template file order: sample_idx equals
    0..n-1, per-row drug_id and smiles equal the test.csv row at the same
    position, and template row count equals test row count. This is an
    evidence-based mapping check, not an assumption.
    """
    tasks = load_task_names(data_root)
    per_task = {}
    ok = True
    errors = []
    tpl_by_task = {}
    for i, r in enumerate(template_rows, start=2):
        if len(r) != len(TEMPLATE_COLUMNS):
            errors.append('template line %d: %d fields' % (i, len(r)))
            ok = False
            continue
        tpl_by_task.setdefault(r[0], []).append((i, r))
    template_tasks = set(tpl_by_task)
    data_tasks = set(tasks)
    if template_tasks != data_tasks:
        errors.append('task sets differ: template-only=%s data-only=%s'
                      % (sorted(template_tasks - data_tasks), sorted(data_tasks - template_tasks)))
        ok = False
    for task in sorted(template_tasks & data_tasks):
        entries = tpl_by_task[task]
        header, test_rows = load_split(data_root, task, 'test')
        n_test = len(test_rows)
        n_tpl = len(entries)
        try:
            seq = [int(r[1]) for _line, r in entries]
        except ValueError:
            seq = None
        seq_ok = seq is not None and seq == list(range(n_tpl)) and n_tpl == n_test
        drug_match = 0
        smiles_match = 0
        for pos, (_line, r) in enumerate(entries):
            if pos < n_test:
                if r[2] == test_rows[pos][0]:
                    drug_match += 1
                if r[3] == test_rows[pos][1]:
                    smiles_match += 1
        task_ok = seq_ok and drug_match == n_test and smiles_match == n_test
        per_task[task] = {
            'template_rows': n_tpl,
            'test_rows': n_test,
            'sample_idx_sequence_is_0_to_n_minus_1_in_file_order': seq_ok,
            'drug_id_rowwise_match': drug_match,
            'smiles_rowwise_match': smiles_match,
            'ok': task_ok,
        }
        if not task_ok:
            ok = False
            errors.append('task %s: template/test alignment failed (%s)' % (task, per_task[task]))
    return {
        'ok': ok,
        'conclusion': (
            'verified: for every task, template sample_idx equals test.csv row_index '
            '(0..n-1) in file order and drug_id/smiles match row-by-row'
            if ok else 'NOT verified; see per_task and errors'
        ),
        'per_task': per_task,
        'errors': errors,
    }


def result_item(name, status, detail):
    return {'name': name, 'status': status, 'detail': detail}


def print_result(overall):
    print('RESULT: %s' % ('PASS' if overall else 'FAIL'))
