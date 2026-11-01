"""validate-submission: verify a candidate CSV preserves the official template.

The submission must equal the template byte-for-byte except for the y_pred
column: same header, same 16379 data rows in the same order, identical raw
field text for task/sample_idx/drug_id/smiles/metric, and a finite numeric
y_pred in every row. Misordering, missing or extra rows, duplicate keys,
modified non-prediction fields and non-finite or empty y_pred values all fail.
Formatting-only differences inside y_pred (e.g. extra decimals) are reported as
warnings, not failures. This validates format only; it says nothing about
prediction quality or platform acceptance.
"""
from __future__ import annotations

import json
import math
import os

from . import common
from .common import REGISTERED_TEMPLATE_SHA256, TEMPLATE_COLUMNS, ContractError, result_item


def validate_bytes(sub_raw, tpl_raw):
    items = []

    def add(name, ok, detail, level='pass'):
        status = 'pass' if ok else ('fail' if level == 'pass' else level)
        items.append(result_item(name, status, detail))
        return ok

    ok = True
    for label, raw in (('template', tpl_raw), ('submission', sub_raw)):
        ok &= add('%s.utf8_bom' % label, common.has_bom(raw), 'file starts with UTF-8 BOM')
        try:
            text = raw.decode('utf-8-sig')
            ok &= add('%s.utf8_decodable' % label, True, 'decoded after BOM strip')
        except UnicodeDecodeError as e:
            add('%s.utf8_decodable' % label, False, str(e))
            return items, False, None
    try:
        tpl_lines = common.split_crlf_lines(tpl_raw.decode('utf-8-sig'))
        ok &= add('template.pure_crlf_with_trailing_newline', True,
                  '%d lines' % len(tpl_lines))
    except ContractError as e:
        add('template.pure_crlf_with_trailing_newline', False, str(e))
        return items, False, None
    try:
        sub_lines = common.split_crlf_lines(sub_raw.decode('utf-8-sig'))
        ok &= add('submission.pure_crlf_with_trailing_newline', True,
                  '%d lines' % len(sub_lines))
    except ContractError as e:
        add('submission.pure_crlf_with_trailing_newline', False, str(e))
        return items, False, None

    if tpl_lines[0] != sub_lines[0]:
        ok &= add('submission.header_identical', False,
                  'template=%r submission=%r' % (tpl_lines[0][:80], sub_lines[0][:80]))
        return items, False, None
    ok &= add('submission.header_identical', True, 'raw header line identical')
    header = common.parse_csv_line(tpl_lines[0])
    if header != TEMPLATE_COLUMNS:
        add('template.header_columns', False, 'header=%r' % (header,))
        return items, False, None
    y_col = header.index('y_pred')

    ok &= add('submission.row_count_equal', len(sub_lines) == len(tpl_lines),
              'template data lines=%d submission data lines=%d' % (len(tpl_lines) - 1, len(sub_lines) - 1))

    bad_fields = []
    bad_raw = []
    bad_yp = []
    ypred_format_notes = []
    keys = []
    dup_keys = []
    seen_keys = set()
    for i in range(1, min(len(tpl_lines), len(sub_lines))):
        tpl_line = tpl_lines[i]
        sub_line = sub_lines[i]
        try:
            tpl_fields = common.parse_csv_line(tpl_line)
            sub_fields = common.parse_csv_line(sub_line)
        except ContractError as e:
            bad_fields.append('line %d: %s' % (i + 1, e))
            continue
        if len(tpl_fields) != len(TEMPLATE_COLUMNS) or len(sub_fields) != len(TEMPLATE_COLUMNS):
            bad_fields.append('line %d: field counts %d/%d' % (i + 1, len(tpl_fields), len(sub_fields)))
            continue
        if [f for j, f in enumerate(tpl_fields) if j != y_col] != [f for j, f in enumerate(sub_fields) if j != y_col]:
            bad_fields.append('line %d: non-y_pred fields differ (%r vs %r)'
                              % (i + 1, tpl_fields[:y_col] + tpl_fields[y_col + 1:], sub_fields[:y_col] + sub_fields[y_col + 1:]))
        tpl_spans = common.csv_field_spans(tpl_line)
        sub_spans = common.csv_field_spans(sub_line)
        if len(tpl_spans) != len(TEMPLATE_COLUMNS) or len(sub_spans) != len(TEMPLATE_COLUMNS):
            bad_raw.append('line %d: span counts %d/%d' % (i + 1, len(tpl_spans), len(sub_spans)))
        else:
            for j in range(len(TEMPLATE_COLUMNS)):
                if j == y_col:
                    continue
                if tpl_line[tpl_spans[j][0]:tpl_spans[j][1]] != sub_line[sub_spans[j][0]:sub_spans[j][1]]:
                    bad_raw.append('line %d: raw field %d differs' % (i + 1, j))
                    break
        if tpl_fields[y_col] != '':
            bad_yp.append('line %d: template y_pred not empty (%r)' % (i + 1, tpl_fields[y_col][:40]))
        raw_yp = sub_line[sub_spans[y_col][0]:sub_spans[y_col][1]]
        try:
            v = float(sub_fields[y_col])
            if not math.isfinite(v):
                raise ValueError(sub_fields[y_col])
        except ValueError:
            bad_yp.append('line %d: y_pred %r is not a finite number' % (i + 1, sub_fields[y_col][:40]))
        else:
            if raw_yp != repr(v):
                ypred_format_notes.append('line %d: y_pred raw %r != canonical %r' % (i + 1, raw_yp, repr(v)))
        key = (sub_fields[0], sub_fields[1])
        if key in seen_keys:
            dup_keys.append('line %d: duplicate (task,sample_idx) %s' % (i + 1, key))
        seen_keys.add(key)
        keys.append(key)
    ok &= add('submission.non_y_pred_fields_identical', not bad_fields,
              'mismatches: %s' % (bad_fields[:5] if bad_fields else 'none'))
    ok &= add('submission.non_y_pred_raw_format_identical', not bad_raw,
              'raw-format deviations: %s' % (bad_raw[:5] if bad_raw else 'none'))
    ok &= add('submission.y_pred_finite_non_empty', not bad_yp,
              'problems: %s' % (bad_yp[:5] if bad_yp else 'none'))
    ok &= add('submission.no_duplicate_task_sample_idx', not dup_keys,
              'duplicates: %s' % (dup_keys[:5] if dup_keys else 'none'))
    if len(sub_lines) == len(tpl_lines) and not bad_fields:
        ok &= add('submission.row_order_and_keys_match_template', keys == [(common.parse_csv_line(l)[0], common.parse_csv_line(l)[1]) for l in tpl_lines[1:]],
                  'row order and (task,sample_idx) sequence identical to template')
    if ypred_format_notes:
        add('submission.y_pred_formatting_canonical', False,
            '%d rows use non-canonical y_pred formatting (first: %s) [warning only]'
            % (len(ypred_format_notes), ypred_format_notes[0]), level='warn')
    info = {
        'template_data_rows': len(tpl_lines) - 1,
        'submission_data_rows': len(sub_lines) - 1,
        'y_pred_formatting_notes': len(ypred_format_notes),
    }
    return items, ok, info


def run(args):
    sub_path = args.submission
    tpl_path = args.template
    if not os.path.isfile(sub_path):
        print('ERROR: submission file not found: %s' % sub_path)
        return 2
    if not os.path.isfile(tpl_path):
        print('ERROR: template file not found: %s' % tpl_path)
        return 2
    with open(sub_path, 'rb') as f:
        sub_raw = f.read()
    with open(tpl_path, 'rb') as f:
        tpl_raw = f.read()
    tpl_sha = common.sha256_bytes(tpl_raw)
    registered_ok = tpl_sha == REGISTERED_TEMPLATE_SHA256
    if not registered_ok and not getattr(args, 'allow_unregistered_template', False):
        print('ERROR: template sha256 %s is not the registered official template %s '
              '(pass --allow-unregistered-template to proceed anyway)' % (tpl_sha, REGISTERED_TEMPLATE_SHA256))
        return 1
    items, ok, info = validate_bytes(sub_raw, tpl_raw)
    for item in items:
        print('%-4s %s: %s' % (item['status'].upper(), item['name'], item['detail']))
    if not registered_ok:
        print('WARN: template sha256 %s is not the registered official template' % tpl_sha)
    common.print_result(ok)
    report = {
        'schema_version': 1,
        'tool': '%s %s' % (common.TOOL_NAME, common.TOOL_VERSION),
        'command': 'validate-submission',
        'generated_at_utc': common.utc_now_iso(),
        'submission_path': sub_path,
        'submission_sha256': common.sha256_bytes(sub_raw),
        'template_path': tpl_path,
        'template_sha256': tpl_sha,
        'template_is_registered_official': registered_ok,
        'items': items,
        'info': info,
        'overall': 'pass' if ok else 'fail',
    }
    if getattr(args, 'report', None):
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('report written: %s' % args.report)
    return 0 if ok else 1
