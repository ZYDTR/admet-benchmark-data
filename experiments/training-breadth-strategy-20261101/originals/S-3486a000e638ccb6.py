"""export: fill model predictions into the official submission template.

Workflow: re-verify the template identity and the evidence-based
sample_idx <-> test.csv row_index mapping, require exact prediction coverage of
every test row (no filling, no defaults), then splice y_pred values into the
template line by line, leaving every other byte untouched (BOM, CRLF endings,
field order, quoting, blank drug_id, all 16379 rows). Each spliced line is
re-parsed and compared field-by-field against the original line before the
output is assembled, and the finished bytes are re-validated internally before
being written atomically. y_pred values are written as the shortest Python
float representation that round-trips exactly.
"""
from __future__ import annotations

import json
import math
import os

from . import common
from . import validate_submission as vs
from .common import (
    CLASSIFICATION_METRICS,
    REGISTERED_TEMPLATE_SHA256,
    TEMPLATE_COLUMNS,
    ContractError,
)


def format_prediction(x):
    x = float(x)
    if not math.isfinite(x):
        raise ContractError('non-finite prediction %r' % x)
    s = repr(x)
    if float(s) != x:
        raise ContractError('float formatting does not round-trip for %r' % x)
    return s


def splice_y_pred(line, y_col, value_str, line_no):
    if '"' in value_str or ',' in value_str:
        raise ContractError('refusing to write y_pred needing CSV quoting: %r' % value_str)
    spans = common.csv_field_spans(line)
    if len(spans) != len(TEMPLATE_COLUMNS):
        raise ContractError('template line %d: %d raw fields (expected %d)'
                            % (line_no, len(spans), len(TEMPLATE_COLUMNS)))
    s, e = spans[y_col]
    if line[s:e] != '':
        raise ContractError('template line %d: y_pred field is not empty (%r); refusing to overwrite'
                            % (line_no, line[s:e][:40]))
    new_line = line[:s] + value_str + line[e:]
    orig_fields = common.parse_csv_line(line)
    new_fields = common.parse_csv_line(new_line)
    expected_fields = orig_fields[:y_col] + [value_str] + orig_fields[y_col + 1:]
    if new_fields != expected_fields:
        raise ContractError('template line %d: splice self-check failed (%r vs %r)'
                            % (line_no, new_fields, expected_fields))
    return new_line


def run(args):
    data_root = common.find_data_root(getattr(args, 'data_root', None))
    template_path = args.template or common.default_template_path(data_root)
    out_path = args.output
    if not os.path.isfile(template_path):
        print('ERROR: template not found: %s' % template_path)
        return 2
    with open(template_path, 'rb') as f:
        tpl_raw = f.read()
    tpl_sha = common.sha256_bytes(tpl_raw)
    registered_ok = tpl_sha == REGISTERED_TEMPLATE_SHA256
    if not registered_ok and not getattr(args, 'allow_unregistered_template', False):
        print('ERROR: template sha256 %s is not the registered official template %s '
              '(pass --allow-unregistered-template to proceed anyway)' % (tpl_sha, REGISTERED_TEMPLATE_SHA256))
        return 1

    text = tpl_raw.decode('utf-8-sig')
    try:
        lines = common.split_crlf_lines(text)
    except ContractError as e:
        print('ERROR: template structure: %s' % e)
        return 1
    header_fields = common.parse_csv_line(lines[0])
    if header_fields != TEMPLATE_COLUMNS:
        print('ERROR: template header %r != %r' % (header_fields, TEMPLATE_COLUMNS))
        return 1
    y_col = header_fields.index('y_pred')

    template_rows = [common.parse_csv_line(l) for l in lines[1:]]
    bad = [i for i, r in enumerate(template_rows, start=2) if len(r) != len(TEMPLATE_COLUMNS)]
    if bad:
        print('ERROR: template lines with wrong field count: %s' % bad[:5])
        return 1
    try:
        metric_map = common.metric_map_from_template(template_rows)
    except ContractError as e:
        print('ERROR: %s' % e)
        return 1

    alignment = common.verify_template_test_alignment(data_root, template_rows)
    if not alignment['ok']:
        print('ERROR: template<->test.csv mapping is NOT verified; refusing to export')
        for err in alignment['errors'][:10]:
            print('  %s' % err)
        return 1

    try:
        preds = common.load_predictions_csv(args.pred)
    except ContractError as e:
        print('ERROR: %s' % e)
        return 1
    test_preds = [p for p in preds if p.split == 'test']
    if not test_preds:
        print('ERROR: prediction file has no rows for split "test"')
        return 1
    tasks = common.load_task_names(data_root)
    expected_keys = {}
    for task in tasks:
        _h, rows = common.load_split(data_root, task, 'test')
        expected_keys[task] = len(rows)
    expected = {(t, i) for t, n in expected_keys.items() for i in range(n)}
    got = [ (p.task, p.row_index) for p in test_preds ]
    dup = sorted({k for k in got if got.count(k) > 1})
    missing = sorted(expected - set(got))
    extra = sorted(set(got) - expected)
    if dup or missing or extra:
        print('ERROR: test-split prediction coverage is not exact: duplicates=%d missing=%d extra=%d'
              % (len(dup), len(missing), len(extra)))
        if dup:
            print('  duplicates (first 5): %s' % dup[:5])
        if missing:
            print('  missing (first 5): %s' % missing[:5])
        if extra:
            print('  extra (first 5): %s' % extra[:5])
        print('  no predictions are filled or substituted automatically; fix the prediction file')
        return 1
    pred_by_key = {(p.task, p.row_index): p.y_pred for p in test_preds}

    if getattr(args, 'check_range', False):
        violations = [
            'line for (%s,%d): y_pred %r outside [0,1] on a %s task'
            % (p.task, p.row_index, p.y_pred, metric_map.get(p.task))
            for p in test_preds
            if metric_map.get(p.task) in CLASSIFICATION_METRICS and not (0.0 <= p.y_pred <= 1.0)
        ]
        if violations:
            print('ERROR: --check-range violations: %d (first: %s)' % (len(violations), violations[:5]))
            return 1

    if os.path.exists(out_path) and not getattr(args, 'overwrite', False):
        print('ERROR: output already exists: %s (pass --overwrite to replace)' % out_path)
        return 1

    new_lines = [lines[0]]
    written = 0
    per_task_stats = {}
    try:
        for idx, line in enumerate(lines[1:], start=2):
            fields = template_rows[idx - 2]
            task = fields[0]
            sidx = int(fields[1])
            key = (task, sidx)
            if key not in pred_by_key:
                raise ContractError('internal error: template row %s at line %d has no prediction' % (key, idx))
            value_str = format_prediction(pred_by_key[key])
            new_line = splice_y_pred(line, y_col, value_str, idx)
            new_lines.append(new_line)
            written += 1
            stats = per_task_stats.setdefault(task, {'rows': 0, 'min': None, 'max': None})
            v = pred_by_key[key]
            stats['rows'] += 1
            stats['min'] = v if stats['min'] is None else min(stats['min'], v)
            stats['max'] = v if stats['max'] is None else max(stats['max'], v)
    except ContractError as e:
        print('ERROR: %s' % e)
        return 1

    new_text = '\r\n'.join(new_lines) + '\r\n'
    new_raw = b'\xef\xbb\xbf' + new_text.encode('utf-8')
    items, ok, info = vs.validate_bytes(new_raw, tpl_raw)
    if not ok:
        print('ERROR: internal validation of the assembled submission failed')
        for item in items:
            if item['status'] == 'fail':
                print('  FAIL %s: %s' % (item['name'], item['detail']))
        return 1

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    tmp_path = out_path + '.tmp'
    with open(tmp_path, 'wb') as f:
        f.write(new_raw)
    os.replace(tmp_path, out_path)

    out_sha = common.sha256_file(out_path)
    print('exported submission: %s' % out_path)
    print('rows with y_pred written: %d (template data rows: %d)' % (written, len(lines) - 1))
    print('output sha256: %s' % out_sha)
    print('mapping: %s' % alignment['conclusion'])
    print('internal validation: pass (%d items, warnings: %d)'
          % (len(items), info.get('y_pred_formatting_notes', 0) if info else 0))
    report = {
        'schema_version': 1,
        'tool': '%s %s' % (common.TOOL_NAME, common.TOOL_VERSION),
        'command': 'export',
        'generated_at_utc': common.utc_now_iso(),
        'pred_file': args.pred,
        'template_path': template_path,
        'template_sha256': tpl_sha,
        'template_is_registered_official': registered_ok,
        'output_path': out_path,
        'output_sha256': out_sha,
        'rows_written': written,
        'pred_rows_total': len(preds),
        'pred_rows_other_splits_ignored': len(preds) - len(test_preds),
        'template_test_alignment': {
            'ok': alignment['ok'],
            'conclusion': alignment['conclusion'],
            'per_task': alignment['per_task'],
        },
        'per_task_y_pred_stats': per_task_stats,
        'internal_validation': {'items': items, 'info': info},
        'overall': 'pass',
    }
    common.print_result(True)
    if getattr(args, 'report', None):
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('report written: %s' % args.report)
    return 0
