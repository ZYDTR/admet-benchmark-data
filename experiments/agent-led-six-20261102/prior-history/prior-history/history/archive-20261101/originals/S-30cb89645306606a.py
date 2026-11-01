"""verify-inputs: integrity verification of registered inputs and the official template.

Read-only. No training, no parameter updates, no label recovery.
"""
from __future__ import annotations

import json
import math
import os

from . import common
from .common import (
    REGISTERED_BLANK_DRUG_ID_COUNT,
    REGISTERED_METRIC_HISTOGRAM,
    REGISTERED_METRICS,
    REGISTERED_TASK_COUNTS,
    REGISTERED_TEMPLATE_SHA256,
    REGISTERED_TOTALS,
    TEMPLATE_COLUMNS,
    ContractError,
    result_item,
)


class Recorder:
    def __init__(self):
        self.items = []

    def add(self, name, ok, detail, level='pass'):
        status = 'pass' if ok else ('fail' if level == 'pass' else level)
        self.items.append(result_item(name, status, detail))
        return ok

    @property
    def ok(self):
        return all(i['status'] != 'fail' for i in self.items)


def _check_template(rec, template_path, data_root):
    with open(template_path, 'rb') as f:
        raw = f.read()
    sha = common.sha256_bytes(raw)
    rec.add('template.sha256_matches_registered', sha == REGISTERED_TEMPLATE_SHA256,
            'sha256=%s registered=%s' % (sha, REGISTERED_TEMPLATE_SHA256))
    rec.add('template.utf8_bom', common.has_bom(raw), 'file starts with UTF-8 BOM')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError as e:
        rec.add('template.utf8_decodable', False, str(e))
        return None
    rec.add('template.utf8_decodable', True, 'decoded after BOM strip')
    try:
        lines = common.split_crlf_lines(text)
        rec.add('template.pure_crlf_with_trailing_newline', True,
                '%d CRLF line endings, final CRLF present' % (text.count('\r\n')))
    except ContractError as e:
        rec.add('template.pure_crlf_with_trailing_newline', False, str(e))
        return None
    rec.add('template.line_count', len(lines) == REGISTERED_TOTALS['template_rows'] + 1,
            'lines=%d (expected %d data lines + header)' % (len(lines), REGISTERED_TOTALS['template_rows']))
    rows = common.parse_csv_text(text)
    rec.add('template.parsed_row_count', len(rows) == len(lines),
            'parsed rows=%d equals physical lines=%d (no embedded newlines)' % (len(rows), len(lines)))
    header = rows[0]
    rec.add('template.header_exact', header == TEMPLATE_COLUMNS, 'header=%r' % (header,))
    data = rows[1:]
    bad_field_counts = [i for i, r in enumerate(data, start=2) if len(r) != len(TEMPLATE_COLUMNS)]
    rec.add('template.field_count_all_rows', not bad_field_counts,
            'rows with wrong field count: %s' % (bad_field_counts[:5] if bad_field_counts else 'none'))
    tasks = [r[0] for r in data if len(r) == len(TEMPLATE_COLUMNS)]
    uniq_tasks = sorted(set(tasks))
    rec.add('template.task_count', len(uniq_tasks) == REGISTERED_TOTALS['tasks'],
            'tasks=%d (expected %d)' % (len(uniq_tasks), REGISTERED_TOTALS['tasks']))
    keys = [(r[0], r[1]) for r in data if len(r) == len(TEMPLATE_COLUMNS)]
    dup_keys = sorted({k for k in keys if keys.count(k) > 1})
    rec.add('template.unique_task_sample_idx', not dup_keys,
            'duplicate (task,sample_idx) keys: %s' % (dup_keys[:5] if dup_keys else 'none'))
    nonempty_yp = [i for i, r in enumerate(data, start=2)
                   if len(r) == len(TEMPLATE_COLUMNS) and r[4].strip() != '']
    rec.add('template.y_pred_all_empty', not nonempty_yp,
            'lines with non-empty y_pred: %s' % (nonempty_yp[:5] if nonempty_yp else 'none'))
    blank_drug = sum(1 for r in data if len(r) == len(TEMPLATE_COLUMNS) and r[2].strip() == '')
    rec.add('template.blank_drug_id_count', blank_drug == REGISTERED_BLANK_DRUG_ID_COUNT,
            'blank drug_id rows=%d (registered=%d)' % (blank_drug, REGISTERED_BLANK_DRUG_ID_COUNT))
    bad_sidx = [i for i, r in enumerate(data, start=2)
                if len(r) == len(TEMPLATE_COLUMNS) and not r[1].isdigit()]
    rec.add('template.sample_idx_nonnegative_integers', not bad_sidx,
            'lines with non-integer sample_idx: %s' % (bad_sidx[:5] if bad_sidx else 'none'))
    blocks = []
    prev_task = None
    prev_idx = -1
    order_ok = True
    for r in data:
        if len(r) != len(TEMPLATE_COLUMNS):
            continue
        task, sidx = r[0], int(r[1])
        if task != prev_task:
            blocks.append(task)
            prev_task = task
            prev_idx = -1
        if sidx != prev_idx + 1:
            order_ok = False
        prev_idx = sidx
    rec.add('template.physical_order_task_blocks_ascending_sample_idx',
            order_ok and blocks == uniq_tasks,
            'contiguous task blocks=%d, sample_idx ascending from 0 within each block' % len(blocks))
    try:
        metric_map = common.metric_map_from_template(data)
    except ContractError as e:
        rec.add('template.metric_column_single_per_task', False, str(e))
        return data
    hist = {}
    for m in metric_map.values():
        hist[m] = hist.get(m, 0) + 1
    rec.add('template.metric_histogram_matches_registered', hist == REGISTERED_METRIC_HISTOGRAM,
            'histogram=%s registered=%s' % (hist, REGISTERED_METRIC_HISTOGRAM))
    mismatch = {t: (m, REGISTERED_METRICS[t]) for t, m in metric_map.items()
                if t in REGISTERED_METRICS and REGISTERED_METRICS[t] != m}
    unknown = sorted(set(metric_map) - set(REGISTERED_METRICS))
    rec.add('template.metric_map_matches_registered', not mismatch and not unknown,
            'mismatches=%s unknown_tasks=%s' % (mismatch, unknown if unknown else 'none'))
    return data


def _check_splits(rec, data_root, tasks):
    totals = {'train': 0, 'valid': 0, 'test': 0}
    per_task = {}
    y_issues = []
    count_mismatches = []
    header_issues = []
    for task in tasks:
        counts = {}
        for split in ('train', 'valid', 'test'):
            try:
                header, rows = common.load_split(data_root, task, split)
            except ContractError as e:
                header_issues.append(str(e))
                counts[split] = None
                continue
            expected_cols = common.OFFICIAL_LABEL_COLUMNS if split == 'train' else ['Drug_ID', 'Drug']
            if header != expected_cols:
                header_issues.append('%s %s header=%r expected=%r' % (task, split, header, expected_cols))
            counts[split] = len(rows)
            totals[split] += len(rows)
            if split == 'train':
                for i, r in enumerate(rows):
                    if len(r) != 3:
                        y_issues.append('%s train line %d: %d fields' % (task, i + 2, len(r)))
                        continue
                    try:
                        v = float(r[2])
                        if not math.isfinite(v):
                            y_issues.append('%s train line %d: non-finite Y %r' % (task, i + 2, r[2]))
                    except ValueError:
                        y_issues.append('%s train line %d: non-numeric Y %r' % (task, i + 2, r[2]))
        per_task[task] = counts
        reg = REGISTERED_TASK_COUNTS.get(task)
        if reg is None:
            count_mismatches.append('%s: not in registered counts' % task)
        elif (counts.get('train'), counts.get('valid'), counts.get('test')) != reg:
            count_mismatches.append('%s: observed=%s registered=%s' % (task, (counts.get('train'), counts.get('valid'), counts.get('test')), reg))
    rec.add('splits.files_and_headers', not header_issues,
            'header problems: %s' % (header_issues[:5] if header_issues else 'none'))
    rec.add('splits.row_counts_match_registered', not count_mismatches,
            'count mismatches: %s' % (count_mismatches[:5] if count_mismatches else 'none'))
    rec.add('splits.train_y_numeric_finite', not y_issues,
            'Y problems: %s' % (y_issues[:5] if y_issues else 'none'))
    totals_ok = (
        totals['train'] == REGISTERED_TOTALS['train_rows']
        and totals['valid'] == REGISTERED_TOTALS['validation_rows']
        and totals['test'] == REGISTERED_TOTALS['test_rows']
    )
    rec.add('splits.totals_match_registered', totals_ok,
            'train=%d valid=%d test=%d (registered %d/%d/%d)'
            % (totals['train'], totals['valid'], totals['test'],
               REGISTERED_TOTALS['train_rows'], REGISTERED_TOTALS['validation_rows'], REGISTERED_TOTALS['test_rows']))
    return per_task, totals


def _check_schema(rec, schema_path, metric_map, per_task_counts=None):
    if not schema_path:
        rec.add('schema.reference_schema_available', False,
                'reference-harness/competition/task_schema.json not found; cross-check skipped', level='warn')
        return
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except (OSError, ValueError) as e:
        rec.add('schema.reference_schema_parsable', False, str(e))
        return
    tasks = schema.get('tasks', [])
    schema_map = {t['task']: t['metric'] for t in tasks}
    schema_rows = {t['task']: t['template_rows'] for t in tasks}
    mismatch = [t for t in schema_map if t in metric_map and schema_map[t] != metric_map[t]]
    only_schema = sorted(set(schema_map) - set(metric_map))
    only_template = sorted(set(metric_map) - set(schema_map))
    rec.add('schema.metric_map_agrees', not mismatch and not only_schema and not only_template,
            'mismatches=%s only_schema=%s only_template=%s' % (mismatch, only_schema, only_template))
    rec.add('schema.template_sha256_agrees', schema.get('source_sha256') == REGISTERED_TEMPLATE_SHA256,
            'schema source_sha256=%r' % (schema.get('source_sha256'),))
    schema_rows_bad = [
        '%s: schema template_rows=%s' % (t, v)
        for t, v in schema_rows.items()
        if t in (per_task_counts or {}) and per_task_counts[t].get('test') != v
    ] if per_task_counts else []
    rec.add('schema.template_rows_match_live_test_rows', not schema_rows_bad,
            'mismatches: %s' % (schema_rows_bad[:5] if schema_rows_bad else 'none'))


def _hash_inputs(rec, data_root, tasks):
    hashes = {}
    missing = []
    paths = [os.path.join(data_root, 'data', 'official', 'submission_template.csv')]
    for task in tasks:
        for split in ('train', 'test'):
            paths.append(common.split_path(data_root, task, split))
        paths.append(common.split_path(data_root, task, 'valid'))
    for p in paths:
        if os.path.isfile(p):
            hashes[os.path.relpath(p, data_root)] = common.sha256_file(p)
        else:
            missing.append(p)
    rec.add('inputs.all_files_present', not missing, 'missing: %s' % (missing[:5] if missing else 'none'))
    return hashes


def run(args):
    data_root = common.find_data_root(getattr(args, 'data_root', None))
    template_path = args.template or common.default_template_path(data_root)
    schema_path = args.schema
    if schema_path is None:
        schema_path = common.default_schema_path()
    elif schema_path.lower() == 'none':
        schema_path = None

    sections = []
    rec = Recorder()
    rec.add('inputs.data_root_resolved', os.path.isdir(data_root), 'data_root=%s' % data_root)
    rec.add('inputs.template_exists', os.path.isfile(template_path), 'template=%s' % template_path)
    try:
        tasks = common.load_task_names(data_root)
        rec.add('inputs.task_dirs', len(tasks) > 0, '%d task directories' % len(tasks))
    except ContractError as e:
        rec.add('inputs.task_dirs', False, str(e))
        tasks = []
    sections.append(('inputs', rec))
    template_rows = None
    if os.path.isfile(template_path):
        rec_t = Recorder()
        template_rows = _check_template(rec_t, template_path, data_root)
        sections.append(('template', rec_t))
    rec_d = Recorder()
    per_task_counts = totals = None
    if tasks:
        per_task_counts, totals = _check_splits(rec_d, data_root, tasks)
    sections.append(('data_splits', rec_d))
    rec_a = Recorder()
    metric_map = {}
    if template_rows is not None and tasks:
        try:
            metric_map = common.metric_map_from_template(template_rows)
        except ContractError:
            metric_map = {}
        alignment = common.verify_template_test_alignment(data_root, template_rows)
        rec_a.add('template_test_alignment.verified', alignment['ok'], alignment['conclusion'])
        if not alignment['ok']:
            for err in alignment['errors'][:5]:
                rec_a.add('template_test_alignment.error', False, err)
        sections.append(('template_test_alignment', rec_a))
    rec_s = Recorder()
    if metric_map:
        _check_schema(rec_s, schema_path, metric_map, per_task_counts)
        sections.append(('reference_schema_crosscheck', rec_s))
    rec_h = Recorder()
    hashes = _hash_inputs(rec_h, data_root, tasks) if tasks else {}
    sections.append(('input_file_hashes', rec_h))

    overall = all(r.ok for _n, r in sections)
    report = {
        'schema_version': 1,
        'tool': '%s %s' % (common.TOOL_NAME, common.TOOL_VERSION),
        'command': 'verify-inputs',
        'generated_at_utc': common.utc_now_iso(),
        'data_root': data_root,
        'template_path': template_path,
        'overall': 'pass' if overall else 'fail',
        'sections': {name: {'items': rec.items, 'ok': rec.ok} for name, rec in sections},
        'per_task_row_counts': per_task_counts,
        'totals': totals,
        'input_file_sha256': hashes,
        'metric_map': metric_map,
    }
    for name, rec in sections:
        print('[%s]' % name)
        for item in rec.items:
            if item['status'] == 'pass' and not getattr(args, 'verbose', False):
                continue
            print('  %-4s %s: %s' % (item['status'].upper(), item['name'], item['detail']))
    common.print_result(overall)
    if getattr(args, 'report', None):
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('report written: %s' % args.report)
    return 0 if overall else 1
