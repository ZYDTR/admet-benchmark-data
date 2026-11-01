"""score: out-of-container per-task scoring of predictions against real labels.

Labels are never guessed or recovered from this project's inputs: the caller
must pass --labels explicitly, either as a directory of per-task official-format
CSVs (columns Drug_ID,Drug,Y; rows must match the project's registered copies
row-by-row, which is verified before scoring) or as a single long-format CSV
with columns task,row_index,y_true (extra columns ignored).

Metrics come from the official template's metric column (cross-checked against
registered values). AUROC/AUPRC/MAE/Spearman are the LOCAL implementations in
admet_eval.metrics; the official total-score aggregation is unconfirmed, so no
official total is produced. Macro means are reported only as clearly labelled
local unofficial values.
"""
from __future__ import annotations

import json
import math
import os

from . import common
from . import metrics as met
from .common import (
    REGISTERED_METRICS,
    SPLITS,
    ContractError,
    LONG_LABEL_REQUIRED_COLUMNS,
    OFFICIAL_LABEL_COLUMNS,
)

EXAMPLE_LIMIT = 5


def _expected_keys(data_root, tasks, split):
    expected = {}
    for task in tasks:
        _h, rows = common.load_split(data_root, task, split)
        expected[task] = len(rows)
    return expected


def _parse_y(values, where, errors):
    out = []
    for i, v in enumerate(values, start=2):
        try:
            y = float(v)
            if not math.isfinite(y):
                raise ValueError(v)
        except ValueError:
            errors.append('%s line %d: y_true %r is not a finite number' % (where, i, v))
            return None
        out.append(y)
    return out


def load_labels_dir(labels_path, split, data_root, tasks, expected_counts):
    labels = {}
    errors = []
    sub, fname = common.SPLIT_SOURCES[split]
    for task in tasks:
        candidates = [
            os.path.join(labels_path, task + '.csv'),
            os.path.join(labels_path, task, fname),
        ]
        path = next((p for p in candidates if os.path.isfile(p)), None)
        if path is None:
            errors.append('labels: no file for task %s (tried %s)' % (task, candidates))
            continue
        header, rows = common.read_csv(path)
        if header != OFFICIAL_LABEL_COLUMNS:
            errors.append('labels %s: header %r != %r' % (path, header, OFFICIAL_LABEL_COLUMNS))
            continue
        try:
            _h, copy_rows = common.load_split(data_root, task, split)
        except ContractError as e:
            errors.append('labels: cannot align task %s: %s' % (task, e))
            continue
        if len(rows) != len(copy_rows):
            errors.append('labels %s: %d rows but project %s copy has %d rows'
                          % (path, len(rows), split, len(copy_rows)))
            continue
        mismatch = [i for i, (a, b) in enumerate(zip(rows, copy_rows), start=2)
                    if a[0] != b[0] or a[1] != b[1]]
        if mismatch:
            errors.append('labels %s: Drug_ID/Drug mismatch vs project %s copy at lines %s'
                          % (path, split, mismatch[:EXAMPLE_LIMIT]))
            continue
        ys = _parse_y([r[2] for r in rows], path, errors)
        if ys is not None and len(ys) != expected_counts.get(task):
            errors.append('labels %s: %d values != expected %d' % (path, len(ys), expected_counts.get(task)))
            continue
        if ys is not None:
            labels[task] = ys
    return labels, errors


def load_labels_long(path, tasks, expected_counts):
    labels = {}
    errors = []
    header, rows = common.read_csv(path)
    lower = [h.strip() for h in header]
    missing = [c for c in LONG_LABEL_REQUIRED_COLUMNS if c not in lower]
    if missing:
        errors.append('labels %s: missing required columns %s (header=%r)' % (path, missing, header))
        return labels, errors
    idx = {c: lower.index(c) for c in LONG_LABEL_REQUIRED_COLUMNS}
    by_task = {t: {} for t in tasks}
    for i, r in enumerate(rows, start=2):
        if len(r) != len(header):
            errors.append('labels %s line %d: %d fields' % (path, i, len(r)))
            continue
        task = r[idx['task']]
        ri_raw = r[idx['row_index']]
        try:
            ri = int(ri_raw)
        except ValueError:
            errors.append('labels %s line %d: row_index %r not an integer' % (path, i, ri_raw))
            continue
        if task not in expected_counts or not (0 <= ri < expected_counts.get(task, 0)):
            errors.append('labels %s line %d: (%s,%d) outside expected range' % (path, i, task, ri))
            continue
        if ri in by_task.get(task, {}):
            errors.append('labels %s line %d: duplicate key (%s,%d)' % (path, i, task, ri))
            continue
        by_task[task][ri] = r[idx['y_true']]
    for task in tasks:
        want = expected_counts.get(task, 0)
        if len(by_task[task]) != want:
            errors.append('labels %s: task %s covers %d/%d rows' % (path, task, len(by_task[task]), want))
    if errors:
        return labels, errors
    for task in tasks:
        ordered = [by_task[task][ri] for ri in range(expected_counts[task])]
        ys = _parse_y(ordered, path, errors)
        if ys is None:
            break
        labels[task] = ys
    return labels, errors


def run(args):
    split = args.split
    if split not in SPLITS:
        print('ERROR: invalid split %r' % split)
        return 2
    data_root = common.find_data_root(getattr(args, 'data_root', None))
    template_path = args.template or common.default_template_path(data_root)
    try:
        _header, template_rows, _raw = common.load_template_rows(template_path)
        metric_map = common.metric_map_from_template(template_rows)
    except (ContractError, OSError) as e:
        print('ERROR: template problem: %s' % e)
        return 2
    try:
        tasks = common.load_task_names(data_root)
    except ContractError as e:
        print('ERROR: %s' % e)
        return 2
    if set(tasks) != set(metric_map):
        print('ERROR: template tasks != data tasks (%s vs %s)' % (sorted(set(tasks) - set(metric_map)), sorted(set(metric_map) - set(tasks))))
        return 1
    metric_mismatch = {t: (m, REGISTERED_METRICS[t]) for t, m in metric_map.items()
                       if t in REGISTERED_METRICS and REGISTERED_METRICS[t] != m}
    if metric_mismatch:
        print('ERROR: template metric disagrees with registered values: %s' % metric_mismatch)
        return 1

    try:
        preds = common.load_predictions_csv(args.pred)
    except ContractError as e:
        print('ERROR: %s' % e)
        return 1
    split_preds = [p for p in preds if p.split == split]
    if not split_preds:
        print('ERROR: prediction file has no rows for split %r (splits present: %s)'
              % (split, sorted({p.split for p in preds})))
        return 1
    expected_counts = _expected_keys(data_root, tasks, split)
    expected = {(t, i) for t, n in expected_counts.items() for i in range(n)}
    got_keys = [(p.task, p.row_index) for p in split_preds]
    dup = sorted({k for k in got_keys if got_keys.count(k) > 1})
    missing = sorted(expected - set(got_keys))
    extra = sorted(set(got_keys) - expected)
    if dup or missing or extra:
        print('ERROR: prediction coverage for split %r is not exact: duplicates=%d missing=%d extra=%d'
              % (split, len(dup), len(missing), len(extra)))
        if dup:
            print('  duplicate keys (first %d): %s' % (EXAMPLE_LIMIT, dup[:EXAMPLE_LIMIT]))
        if missing:
            print('  missing keys (first %d): %s' % (EXAMPLE_LIMIT, missing[:EXAMPLE_LIMIT]))
        if extra:
            print('  extra keys (first %d): %s' % (EXAMPLE_LIMIT, extra[:EXAMPLE_LIMIT]))
        return 1

    if not os.path.exists(args.labels):
        print('ERROR: labels path not found: %s' % args.labels)
        return 2
    if os.path.isdir(args.labels):
        labels, label_errors = load_labels_dir(args.labels, split, data_root, tasks, expected_counts)
    else:
        labels, label_errors = load_labels_long(args.labels, tasks, expected_counts)
    if label_errors:
        for e in label_errors[:20]:
            print('FAIL %s' % e)
        print('RESULT: FAIL')
        return 1

    results = []
    for task in tasks:
        y_true = labels[task]
        by_idx = {p.row_index: p.y_pred for p in split_preds if p.task == task}
        y_pred = [by_idx[i] for i in range(expected_counts[task])]
        metric = metric_map[task]
        entry = {
            'task': task,
            'metric': metric,
            'n': len(y_true),
            'n_pos': sum(1 for y in y_true if y == 1.0) if metric in common.CLASSIFICATION_METRICS else None,
            'n_neg': sum(1 for y in y_true if y == 0.0) if metric in common.CLASSIFICATION_METRICS else None,
            'value': None,
            'status': None,
            'reason': None,
        }
        try:
            value, reason = met.compute_metric(metric, y_true, y_pred)
            if value is None:
                entry['status'] = 'undefined'
                entry['reason'] = reason
            else:
                entry['status'] = 'scored'
                entry['value'] = value
        except ValueError as e:
            entry['status'] = 'error'
            entry['reason'] = str(e)
        results.append(entry)

    errors = [r for r in results if r['status'] == 'error']
    undefined = [r for r in results if r['status'] == 'undefined']
    scored = [r for r in results if r['status'] == 'scored']

    print('%-38s %-8s %6s %6s %6s %12s %s' % ('task', 'metric', 'n', 'n_pos', 'n_neg', 'value', 'status'))
    for r in results:
        print('%-38s %-8s %6d %6s %6s %12s %s' % (
            r['task'], r['metric'], r['n'],
            '-' if r['n_pos'] is None else r['n_pos'],
            '-' if r['n_neg'] is None else r['n_neg'],
            '-' if r['value'] is None else '%.6f' % r['value'],
            r['status'] + (': ' + r['reason'] if r['reason'] else ''),
        ))
    per_metric = {}
    for m in sorted({r['metric'] for r in results}):
        vals = [r['value'] for r in scored if r['metric'] == m]
        per_metric[m] = {
            'n_tasks_total': sum(1 for r in results if r['metric'] == m),
            'n_scored': len(vals),
            'local_unofficial_macro_mean': (sum(vals) / len(vals)) if vals else None,
        }
    overall_macro = (sum(r['value'] for r in scored) / len(scored)) if scored else None
    print('summary: scored=%d undefined=%d error=%d' % (len(scored), len(undefined), len(errors)))
    for m, s in per_metric.items():
        mean = s['local_unofficial_macro_mean']
        print('  local_unofficial_macro_mean[%s] = %s (over %d scored tasks)'
              % (m, '-' if mean is None else '%.6f' % mean, s['n_scored']))
    print('  local_unofficial_macro_mean[all] = %s (over %d scored tasks)'
          % ('-' if overall_macro is None else '%.6f' % overall_macro, len(scored)))
    print('NOTE: values use LOCAL metric definitions; the official AUPRC convention and '
          'total-score aggregation are unconfirmed, so no official total is reported.')

    report = {
        'schema_version': 1,
        'tool': '%s %s' % (common.TOOL_NAME, common.TOOL_VERSION),
        'command': 'score',
        'generated_at_utc': common.utc_now_iso(),
        'pred_file': args.pred,
        'labels_path': args.labels,
        'labels_format': 'official_dir' if os.path.isdir(args.labels) else 'long_csv',
        'split': split,
        'data_root': data_root,
        'template_path': template_path,
        'template_sha256': common.sha256_file(template_path),
        'coverage': {'rows_expected': sum(expected_counts.values()), 'rows_present': len(split_preds)},
        'results': results,
        'summary': {
            'n_scored': len(scored),
            'n_undefined': len(undefined),
            'n_error': len(errors),
            'per_metric': per_metric,
            'local_unofficial_overall_macro_mean': overall_macro,
            'official_total': 'not_computed: official aggregation unconfirmed',
        },
        'overall': 'fail' if errors else 'pass',
    }
    common.print_result(not errors)
    if getattr(args, 'report', None):
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('report written: %s' % args.report)
    if getattr(args, 'report_csv', None):
        os.makedirs(os.path.dirname(os.path.abspath(args.report_csv)), exist_ok=True)
        with open(args.report_csv, 'w', encoding='utf-8', newline='') as f:
            import csv as _csv
            w = _csv.writer(f)
            w.writerow(['task', 'metric', 'n', 'n_pos', 'n_neg', 'value', 'status', 'reason'])
            for r in results:
                w.writerow([r['task'], r['metric'], r['n'], r['n_pos'] or '', r['n_neg'] or '',
                            '' if r['value'] is None else repr(r['value']), r['status'], r['reason'] or ''])
        print('report csv written: %s' % args.report_csv)
    return 0 if not errors else 1
