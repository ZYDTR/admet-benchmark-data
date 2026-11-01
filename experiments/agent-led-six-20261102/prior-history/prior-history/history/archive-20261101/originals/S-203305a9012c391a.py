"""check-predictions: coverage and contract checks for prediction files.

The prediction file contract is fixed: exactly the columns
task,split,row_index,y_pred (order free), where split is one of
train/valid/test and row_index is the 0-based position of the data row in the
task's CSV for that split. Checks parse validity, duplicate keys, known
tasks/splits, in-range row_index, finite y_pred, and full per-split coverage
against the live input files. Read-only; no predictions are added or modified.
"""
from __future__ import annotations

import json
import os

from . import common
from .common import SPLITS, ContractError

EXAMPLE_LIMIT = 5


def run(args):
    data_root = common.find_data_root(getattr(args, 'data_root', None))
    pred_path = args.pred
    if not os.path.isfile(pred_path):
        print('ERROR: prediction file not found: %s' % pred_path)
        return 2
    try:
        preds = common.load_predictions_csv(pred_path)
    except ContractError as e:
        print('ERROR: %s' % e)
        return 1

    tasks = common.load_task_names(data_root)
    split_rows = {}
    missing_inputs = []
    for split in SPLITS:
        split_rows[split] = {}
        for task in tasks:
            try:
                _header, rows = common.load_split(data_root, task, split)
                split_rows[split][task] = len(rows)
            except ContractError as e:
                split_rows[split][task] = None
                missing_inputs.append(str(e))

    unknown_tasks = sorted({p.task for p in preds} - set(tasks))
    errors = []
    if unknown_tasks:
        errors.append('unknown tasks in prediction file: %s' % unknown_tasks[:EXAMPLE_LIMIT])
    referenced_missing = sorted(
        {(p.task, p.split) for p in preds
         if p.task in tasks and split_rows.get(p.split, {}).get(p.task) is None}
    )
    if referenced_missing:
        errors.append('predictions reference task/split with missing input files: %s'
                      % referenced_missing[:EXAMPLE_LIMIT])

    keys = {}
    dup_keys = {}
    for p in preds:
        if p.task not in split_rows.get(p.split, {}):
            continue
        k = p.key()
        if k in keys:
            dup_keys.setdefault(k, [keys[k]]).append(p.line_no)
        else:
            keys[k] = p.line_no
    if dup_keys:
        examples = ['%s first=%d later=%s' % (k, v[0], v[1:][:3]) for k, v in list(dup_keys.items())[:EXAMPLE_LIMIT]]
        errors.append('duplicate (task,split,row_index) keys: %d total; e.g. %s' % (len(dup_keys), '; '.join(examples)))

    out_of_range = []
    for p in preds:
        n = split_rows.get(p.split, {}).get(p.task)
        if n is not None and not (0 <= p.row_index < n):
            out_of_range.append('line %d: (%s,%s,%d) but split has %d rows' % (p.line_no, p.task, p.split, p.row_index, n))
    if out_of_range:
        errors.append('row_index out of range: %d total; e.g. %s' % (len(out_of_range), '; '.join(out_of_range[:EXAMPLE_LIMIT])))

    present_splits = sorted({p.split for p in preds})
    coverage = {}
    for split in present_splits:
        expected = {}
        for task in tasks:
            n = split_rows[split].get(task)
            if n is not None:
                expected[task] = n
        have = {}
        for p in preds:
            if p.split == split and p.task in expected:
                have[p.task] = have.get(p.task, 0) + 1
        missing = {t: expected[t] - have.get(t, 0) for t in expected if expected[t] - have.get(t, 0) > 0}
        extra = {t: have.get(t, 0) - expected[t] for t in have if have.get(t, 0) > expected.get(t, 0)}
        coverage[split] = {
            'tasks': len(expected),
            'rows_expected': sum(expected.values()),
            'rows_present': sum(have.values()),
            'missing_rows': sum(missing.values()),
            'extra_rows': sum(extra.values()),
            'missing_by_task': missing,
            'extra_by_task': extra,
            'complete': not missing and not extra and not dup_keys,
        }
        if missing:
            examples = ['%s:%d' % (t, c) for t, c in list(sorted(missing.items()))[:EXAMPLE_LIMIT]]
            errors.append('split %s missing predictions: %d rows; e.g. %s' % (split, sum(missing.values()), '; '.join(examples)))
        if extra:
            examples = ['%s:%d' % (t, c) for t, c in list(sorted(extra.items()))[:EXAMPLE_LIMIT]]
            errors.append('split %s extra predictions: %d rows; e.g. %s' % (split, sum(extra.values()), '; '.join(examples)))

    overall = not errors and not unknown_tasks and bool(present_splits)
    if not present_splits:
        errors.append('prediction file contains no rows for any known split')
    if unknown_tasks or missing_inputs or errors:
        for e in (missing_inputs[:5] + errors):
            print('FAIL %s' % e)
    for split in present_splits:
        c = coverage[split]
        print('coverage[%s] tasks=%d rows_expected=%d rows_present=%d missing=%d extra=%d complete=%s'
              % (split, c['tasks'], c['rows_expected'], c['rows_present'], c['missing_rows'], c['extra_rows'], c['complete']))
    report = {
        'schema_version': 1,
        'tool': '%s %s' % (common.TOOL_NAME, common.TOOL_VERSION),
        'command': 'check-predictions',
        'generated_at_utc': common.utc_now_iso(),
        'pred_file': pred_path,
        'data_root': data_root,
        'total_pred_rows': len(preds),
        'splits_present': present_splits,
        'coverage': coverage,
        'duplicate_keys': {str(k): v for k, v in list(dup_keys.items())[:20]},
        'unknown_tasks': unknown_tasks,
        'errors': errors,
        'overall': 'pass' if overall else 'fail',
    }
    common.print_result(overall)
    if getattr(args, 'report', None):
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('report written: %s' % args.report)
    return 0 if overall else 1
