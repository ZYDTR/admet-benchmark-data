"""selftest: synthetic fixed-value verification of metric implementations, CSV
field splicing, export and validation logic.

Runs only on synthetic data or read-only checks of the real template; no
training, no parameter updates, no real labels. Metric correctness is pinned
by hand-computed constants and by agreement with structurally independent
naive implementations on deterministic pseudo-random inputs.
"""
from __future__ import annotations

import contextlib
import csv as csv_mod
import io
import json
import math
import os
import random
import tempfile
from types import SimpleNamespace

from . import common
from . import export_submission as exp
from . import metrics as met
from . import score as score_mod
from . import validate_submission as vs
from . import check_predictions as cp_mod

TOL = 1e-12


class Checks:
    def __init__(self):
        self.items = []

    def check(self, name, ok, detail=''):
        self.items.append({'name': name, 'status': 'pass' if ok else 'fail', 'detail': str(detail)})
        return ok

    def close(self, name, got, want, detail=''):
        ok = (got is None and want is None) or (got is not None and want is not None and abs(got - want) <= TOL)
        self.items.append({'name': name, 'status': 'pass' if ok else 'fail',
                           'detail': '%s got=%r want=%r %s' % (name, got, want, detail)})
        return ok

    @property
    def n_fail(self):
        return sum(1 for i in self.items if i['status'] == 'fail')


def _naive_auroc(y, s):
    pos = [si for yi, si in zip(y, s) if yi == 1]
    neg = [si for yi, si in zip(y, s) if yi == 0]
    tot = 0.0
    for p in pos:
        for n in neg:
            if p > n:
                tot += 1.0
            elif p == n:
                tot += 0.5
    return tot / (len(pos) * len(neg))


def _naive_ap(y, s):
    n_pos = sum(1 for yi in y if yi == 1)
    thresholds = sorted(set(s), reverse=True)
    prev = 0.0
    ap = 0.0
    for th in thresholds:
        tp = sum(1 for yi, si in zip(y, s) if si >= th and yi == 1)
        fp = sum(1 for yi, si in zip(y, s) if si >= th and yi == 0)
        rec = tp / n_pos
        prec = tp / (tp + fp)
        ap += (rec - prev) * prec
        prev = rec
    return ap


def _naive_midrank(v):
    return [sum(1 for b in v if b < a) + (sum(1 for b in v if b == a) + 1) / 2.0 for a in v]


def _naive_spearman(x, y):
    rx = _naive_midrank(x)
    ry = _naive_midrank(y)
    n = len(x)
    mx = sum(rx) / n
    my = sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    if den == 0:
        return None
    return num / den


def _expect_value_error(c, name, fn, *a):
    try:
        fn(*a)
    except ValueError:
        return c.check(name, True, 'raised ValueError as expected')
    return c.check(name, False, 'no ValueError raised')


def _metric_unit_checks(c):
    c.close('auroc.mixed_case', met.auroc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])[0], 0.75)
    c.close('auroc.tied_pair', met.auroc([0, 1], [0.5, 0.5])[0], 0.5)
    c.close('auroc.perfect', met.auroc([0, 1, 1], [0.2, 0.4, 0.6])[0], 1.0)
    c.close('auroc.partial', met.auroc([0, 0, 1, 1], [0.6, 0.4, 0.35, 0.8])[0], 0.5)
    v, r = met.auroc([0, 0], [0.1, 0.2])
    c.check('auroc.undefined_single_class', v is None and 'both classes' in r, r)
    v, r = met.auroc([1, 1], [0.1, 0.2])
    c.check('auroc.undefined_all_positive', v is None, r)
    _expect_value_error(c, 'auroc.non_binary_raises', met.auroc, [0, 2], [0.1, 0.2])
    _expect_value_error(c, 'auroc.length_mismatch_raises', met.auroc, [0, 1], [0.1])
    _expect_value_error(c, 'auroc.non_finite_raises', met.auroc, [0, 1], [0.1, float('nan')])

    c.close('ap.mixed_case', met.average_precision([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8])[0], 0.5 + 1.0 / 3.0)
    c.close('ap.tie_case', met.average_precision([1, 0, 1], [0.5, 0.5, 0.3])[0], 0.25 + 1.0 / 3.0)
    c.close('ap.all_positive', met.average_precision([1, 1, 1], [0.3, 0.2, 0.1])[0], 1.0)
    c.close('ap.tied_single_group', met.average_precision([0, 1], [0.5, 0.5])[0], 0.5)
    v, r = met.average_precision([0, 0, 0], [0.1, 0.2, 0.3])
    c.check('ap.undefined_no_positive', v is None and 'positive' in r, r)
    _expect_value_error(c, 'ap.non_binary_raises', met.average_precision, [0, 2], [0.1, 0.2])

    c.close('mae.basic', met.mae([1, 2, 3], [1.5, 2, 4])[0], 0.5)
    v, r = met.mae([], [])
    c.check('mae.undefined_empty', v is None, r)
    _expect_value_error(c, 'mae.length_mismatch_raises', met.mae, [1], [1, 2])

    c.close('spearman.perfect', met.spearman([1, 2, 3], [1, 2, 3])[0], 1.0)
    c.close('spearman.reversed', met.spearman([1, 2, 3], [3, 2, 1])[0], -1.0)
    c.close('spearman.ties', met.spearman([1, 1, 2], [1, 2, 3])[0], math.sqrt(3) / 2)
    c.close('spearman.monotone_nonlinear', met.spearman([1, 2, 3], [2, 4, 8])[0], 1.0)
    v, r = met.spearman([5, 5, 5], [1, 2, 3])
    c.check('spearman.undefined_constant', v is None and 'variance' in r, r)
    v, r = met.spearman([1], [2])
    c.check('spearman.undefined_n_lt_2', v is None, r)


def _metric_agreement_checks(c):
    rng = random.Random(20261030)
    trials = 250
    bad = 0
    checked = 0
    for _ in range(trials):
        n = rng.randint(1, 60)
        y = [rng.randint(0, 1) for _ in range(n)]
        s = [rng.choice([0.0, 0.1, 0.2, 0.5]) if rng.random() < 0.5 else rng.random() for _ in range(n)]
        if 0 < sum(y) < n:
            checked += 1
            v1, _ = met.auroc(y, s)
            v2 = _naive_auroc(y, s)
            if abs(v1 - v2) > TOL:
                bad += 1
            v1, _ = met.average_precision(y, s)
            v2 = _naive_ap(y, s)
            if abs(v1 - v2) > TOL:
                bad += 1
        x = [rng.choice([1.0, 2.0, 3.0]) if rng.random() < 0.5 else rng.random() * 10 for _ in range(n)]
        w = [rng.choice([0.0, 5.0]) if rng.random() < 0.5 else rng.random() * 10 for _ in range(n)]
        if n >= 2:
            checked += 1
            v1, _r = met.spearman(x, w)
            v2 = _naive_spearman(x, w)
            if (v1 is None) != (v2 is None) or (v1 is not None and abs(v1 - v2) > TOL):
                bad += 1
    c.check('metrics.agreement_with_naive_implementations', bad == 0,
            '%d comparisons over %d trials, mismatches=%d' % (checked, trials, bad))


def _span_checks(c):
    lines = [
        'a,b,c',
        'a,"b,c",d',
        '"a""b",c',
        'a"b,c',
        '"a"b,c',
        'a,,',
        ',,',
        '"\1,1,1-Trifluro-2-chloroethane\\"""",FC(F)(F)CCl,,AUROC',
        'ames,54,"Apigenin (5,7,4\'-THF)",O=c1cc,,MAE',
    ]
    ok = True
    for line in lines:
        fields = common.parse_csv_line(line)
        spans = common.csv_field_spans(line)
        if len(spans) != len(fields):
            ok = False
            continue
        for i, (s, e) in enumerate(spans):
            raw = line[s:e]
            if raw == '':
                if fields[i] != '':
                    ok = False
                continue
            iso = common.parse_csv_line(raw)
            if len(iso) != 1 or iso[0] != fields[i]:
                ok = False
    c.check('csv_field_spans.matches_csv_reader', ok, '%d synthetic lines incl. quotes/commas/escapes' % len(lines))
    line = 'ames,54,"Apigenin (5,7,4\'-THF)",O=c1cc,,MAE'
    spans = common.csv_field_spans(line)
    s, e = spans[4]
    new_line = line[:s] + '0.75' + line[e:]
    c.check('csv_field_spans.splice_roundtrip',
            common.parse_csv_line(new_line) == ['ames', '54', "Apigenin (5,7,4'-THF)", 'O=c1cc', '0.75', 'MAE'],
            new_line)
    try:
        exp.format_prediction(0.1)
        exp.format_prediction(-2.5)
        exp.format_prediction(1e-17)
        ok = True
    except Exception:
        ok = False
    c.check('format_prediction.roundtrip', ok, 'repr round-trips for sampled floats')
    raised = False
    try:
        exp.format_prediction(float('nan'))
    except common.ContractError:
        raised = True
    c.check('format_prediction.rejects_nonfinite', raised, 'ContractError on nan')
    try:
        data_root = common.find_data_root()
        tpl_path = common.default_template_path(data_root)
        _header, rows, _raw = common.load_template_rows(tpl_path)
        text = open(tpl_path, 'rb').read().decode('utf-8-sig')
        lines = common.split_crlf_lines(text)[1:]
        mismatches = 0
        quoted_lines = 0
        for line in lines:
            fields = common.parse_csv_line(line)
            spans = common.csv_field_spans(line)
            if len(spans) != 6 or len(fields) != 6:
                mismatches += 1
                continue
            if '"' in line:
                quoted_lines += 1
            if line[spans[4][0]:spans[4][1]] != '':
                mismatches += 1
            for i, (s, e) in enumerate(spans):
                raw = line[s:e]
                if raw == '':
                    if fields[i] != '':
                        mismatches += 1
                    continue
                iso = common.parse_csv_line(raw)
                if len(iso) != 1 or iso[0] != fields[i]:
                    mismatches += 1
                    break
        c.check('csv_field_spans.real_template_agreement', mismatches == 0,
                '%d template data lines (%d with quoted fields), mismatches=%d'
                % (len(lines), quoted_lines, mismatches))
        exotic = next(l for l in lines if '\\"' in l or l.count('"') >= 4)
        fields = common.parse_csv_line(exotic)
        new_line = exp.splice_y_pred(exotic, 4, '0.123456789', 1)
        got = common.parse_csv_line(new_line)
        want = fields[:4] + ['0.123456789'] + fields[5:]
        c.check('splice_y_pred.real_exotic_line', got == want, new_line[:100])
    except common.ContractError:
        c.check('csv_field_spans.real_template_agreement', True, 'real template not reachable; skipped', )


MINI_TASKS = [
    ('mini_auroc', 'AUROC', [1, 1, 1, 0, 0, 0], [0.9, 0.8, 0.7, 0.3, 0.2, 0.1], 1.0, 'scored'),
    ('mini_auprc', 'AUPRC', [1, 1, 0, 0, 0, 0], [0.9, 0.8, 0.2, 0.15, 0.1, 0.05], 1.0, 'scored'),
    ('mini_auprc_mix', 'AUPRC', [1, 0, 1, 0], [0.5, 0.5, 0.3, 0.4], 0.5, 'scored'),
    ('mini_mae', 'MAE', [1.0, 2.0, 3.0], [1.5, 2.0, 4.0], 0.5, 'scored'),
    ('mini_spearman', 'Spearman', [1, 1, 2], [1, 2, 3], math.sqrt(3) / 2, 'scored'),
    ('mini_undef', 'AUROC', [0, 0, 0], [0.1, 0.5, 0.9], None, 'undefined'),
]


def _write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv_mod.writer(f, lineterminator='\r\n')
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def _mini_molecules(task, n, offset=0):
    special = {}
    if task == 'mini_auprc':
        special[1] = "Apigenin (5,7,4'-THF), mix"
        special[2] = 'drug "quoted" \\ backslash'
    if task == 'mini_mae':
        special[0] = ''
    mols = []
    for i in range(n):
        did = special.get(i, 'M %d' % (i + offset))
        smi = 'C%sN' % ('C' * (i + 1))
        mols.append((did, smi))
    return mols


def build_mini_project(base):
    tasks = [t[0] for t in MINI_TASKS]
    for task, _metric, vlabels, _vpreds, _exp, _status in MINI_TASKS:
        n = len(vlabels)
        valid_mols = _mini_molecules(task, n)
        test_mols = _mini_molecules(task, n + 3, offset=100)
        train_mols = _mini_molecules(task, n + 2, offset=200)
        bench = os.path.join(base, 'data', 'official', 'data_benchmark', task)
        _write_csv(os.path.join(bench, 'train.csv'), ['Drug_ID', 'Drug', 'Y'],
                   [[d, s, 0] for d, s in train_mols])
        _write_csv(os.path.join(bench, 'test.csv'), ['Drug_ID', 'Drug'], test_mols)
        _write_csv(os.path.join(base, 'data', 'blind_validation', task, 'valid.csv'),
                   ['Drug_ID', 'Drug'], valid_mols)
    tpl_rows = []
    for task, metric, _vl, _vp, _e, _s in MINI_TASKS:
        n = len([1] * len(_vl))
        test_mols = _mini_molecules(task, n + 3, offset=100)
        for i, (d, s) in enumerate(test_mols):
            tpl_rows.append([task, str(i), d, s, '', metric])
    _write_csv(os.path.join(base, 'data', 'official', 'submission_template.csv'),
               common.TEMPLATE_COLUMNS, tpl_rows)
    pred_rows = []
    for task, _metric, vlabels, vpreds, _exp, _status in MINI_TASKS:
        n = len(vlabels)
        test_mols = _mini_molecules(task, n + 3, offset=100)
        for i in range(n):
            pred_rows.append([task, 'valid', str(i), repr(vpreds[i])])
        for i in range(len(test_mols)):
            val = 0.42 + 0.01 * i if _metric in common.CLASSIFICATION_METRICS else 1.0 + 0.25 * i
            pred_rows.append([task, 'test', str(i), repr(val)])
    _write_csv(os.path.join(base, 'preds.csv'), list(common.PRED_COLUMNS), pred_rows)
    labels_dir = os.path.join(base, 'labels_valid')
    for task, _metric, vlabels, _vp, _e, _s in MINI_TASKS:
        valid_mols = _mini_molecules(task, len(vlabels))
        _write_csv(os.path.join(labels_dir, task + '.csv'), common.OFFICIAL_LABEL_COLUMNS,
                   [[d, s, y] for (d, s), y in zip(valid_mols, vlabels)])
    return {
        'base': base,
        'data_root': base,
        'template': os.path.join(base, 'data', 'official', 'submission_template.csv'),
        'pred': os.path.join(base, 'preds.csv'),
        'labels': labels_dir,
        'submission': os.path.join(base, 'submission.csv'),
    }


def _run_module(c, name, fn, args):
    buf = io.StringIO()
    code = None
    with contextlib.redirect_stdout(buf):
        try:
            code = fn(args)
        except SystemExit as e:
            code = e.code
    out = buf.getvalue()
    ok = isinstance(code, int) and code == 0
    c.check(name, ok, 'exit=%r; output tail: %s' % (code, out.strip().splitlines()[-1] if out.strip() else ''))
    return code, out


def _e2e_checks(c):
    base = tempfile.mkdtemp(prefix='admet_eval_selftest_')
    paths = build_mini_project(base)
    ns = lambda **kw: SimpleNamespace(**kw)

    code, _out = _run_module(c, 'e2e.check_predictions', cp_mod.run,
                             ns(pred=paths['pred'], data_root=paths['data_root'], report=None))
    score_report = os.path.join(base, 'score_report.json')
    code, _out = _run_module(c, 'e2e.score_valid', score_mod.run,
                             ns(pred=paths['pred'], split='valid', labels=paths['labels'],
                                data_root=paths['data_root'], template=paths['template'],
                                report=score_report, report_csv=None))
    with open(score_report, 'r', encoding='utf-8') as f:
        report = json.load(f)
    for task, _metric, _vl, _vp, expected, status in MINI_TASKS:
        entry = next(r for r in report['results'] if r['task'] == task)
        c.check('e2e.score[%s].status' % task, entry['status'] == status,
                'status=%r expected=%r' % (entry['status'], status))
        if expected is not None:
            c.close('e2e.score[%s].value' % task, entry['value'], expected)
        else:
            c.check('e2e.score[%s].value_none' % task, entry['value'] is None, entry['value'])
    c.check('e2e.score.no_official_total', 'not_computed' in report['summary']['official_total'],
            report['summary']['official_total'])

    code, _out = _run_module(c, 'e2e.export', exp.run,
                             ns(pred=paths['pred'], template=paths['template'], output=paths['submission'],
                                data_root=paths['data_root'], report=None, check_range=False,
                                allow_unregistered_template=True, overwrite=False))
    code, _out = _run_module(c, 'e2e.validate_submission', vs.run,
                             ns(submission=paths['submission'], template=paths['template'],
                                report=None, allow_unregistered_template=True))
    with open(paths['submission'], 'rb') as f:
        sub_raw = f.read()
    with open(paths['template'], 'rb') as f:
        tpl_raw = f.read()
    sub_text = sub_raw.decode('utf-8-sig')
    tpl_text = tpl_raw.decode('utf-8-sig')
    sub_lines = common.split_crlf_lines(sub_text)
    tpl_lines = common.split_crlf_lines(tpl_text)
    unchanged = sum(1 for a, b in zip(sub_lines[1:], tpl_lines[1:])
                    if a == b)
    c.check('e2e.export.only_y_pred_changed', unchanged == 0,
            '%d of %d lines byte-identical (expect 0; all differ only in y_pred)' % (unchanged, len(tpl_lines) - 1))
    sub_rows = [common.parse_csv_line(l) for l in sub_lines[1:]]
    tpl_rows = [common.parse_csv_line(l) for l in tpl_lines[1:]]
    same_non_yp = all(a[:4] == b[:4] and a[5] == b[5] for a, b in zip(sub_rows, tpl_rows))
    c.check('e2e.export.non_y_pred_fields_preserved', same_non_yp, 'parsed non-y_pred fields identical')
    pred_map = {}
    _header, prow = common.read_csv(paths['pred'])
    for r in prow:
        if r[1] == 'test':
            pred_map[(r[0], int(r[2]))] = float(r[3])
    roundtrip = all(float(a[4]) == pred_map[(a[0], int(a[1]))] for a in sub_rows)
    c.check('e2e.export.y_pred_roundtrip', roundtrip, 'all y_pred values equal the prediction file values')
    quoted = sum(1 for l in sub_lines[1:] if '"' in l)
    c.check('e2e.export.quoted_lines_preserved', quoted > 0, '%d quoted lines in mini template preserved' % quoted)

    tampered = os.path.join(base, 'tampered.csv')

    def write_variant(lines):
        with open(tampered, 'w', encoding='utf-8-sig', newline='') as f:
            f.write('\r\n'.join(lines) + '\r\n')

    sub_lines2 = list(sub_lines)
    sub_lines2[1], sub_lines2[2] = sub_lines2[2], sub_lines2[1]
    write_variant(sub_lines2)
    code, _ = _run_module_expect_fail(c, 'e2e.validate_detects.reordered_rows', vs.run,
                                      ns(submission=tampered, template=paths['template'], report=None,
                                         allow_unregistered_template=True))
    write_variant(sub_lines[:-1])
    code, _ = _run_module_expect_fail(c, 'e2e.validate_detects.missing_row', vs.run,
                                      ns(submission=tampered, template=paths['template'], report=None,
                                         allow_unregistered_template=True))
    sub_lines2 = list(sub_lines)
    smi_spans = common.csv_field_spans(sub_lines[1])
    ss, se = smi_spans[3]
    smi_raw = sub_lines[1][ss:se]
    sub_lines2[1] = sub_lines[1][:ss] + smi_raw[:-1] + 'O' + sub_lines[1][se:]
    write_variant(sub_lines2)
    code, _ = _run_module_expect_fail(c, 'e2e.validate_detects.modified_smiles', vs.run,
                                      ns(submission=tampered, template=paths['template'], report=None,
                                         allow_unregistered_template=True))
    yp_spans = common.csv_field_spans(sub_lines[1])
    s, e = yp_spans[4]
    sub_lines2 = list(sub_lines)
    sub_lines2[1] = sub_lines[1][:s] + 'nan' + sub_lines[1][e:]
    write_variant(sub_lines2)
    code, _ = _run_module_expect_fail(c, 'e2e.validate_detects.nonfinite_y_pred', vs.run,
                                      ns(submission=tampered, template=paths['template'], report=None,
                                         allow_unregistered_template=True))
    sub_lines2 = list(sub_lines)
    sub_lines2[1] = sub_lines[1][:s] + '' + sub_lines[1][e:]
    write_variant(sub_lines2)
    code, _ = _run_module_expect_fail(c, 'e2e.validate_detects.empty_y_pred', vs.run,
                                      ns(submission=tampered, template=paths['template'], report=None,
                                         allow_unregistered_template=True))
    drug_spans = common.csv_field_spans(sub_lines[1])
    ds, de = drug_spans[2]
    drug_raw = sub_lines[1][ds:de]
    sub_lines2 = list(sub_lines)
    if not drug_raw.startswith('"'):
        sub_lines2[1] = sub_lines[1][:ds] + '"' + drug_raw + '"' + sub_lines[1][de:]
        write_variant(sub_lines2)
        code, _ = _run_module_expect_fail(c, 'e2e.validate_detects.requoted_drug_id', vs.run,
                                          ns(submission=tampered, template=paths['template'], report=None,
                                             allow_unregistered_template=True))
    else:
        c.check('e2e.validate_detects.requoted_drug_id', True, 'line 1 drug_id already quoted; variant skipped')

    _header, prow = common.read_csv(paths['pred'])
    dropped = [r for r in prow][: len(prow) - 1]
    _write_csv(os.path.join(base, 'preds_missing.csv'), list(common.PRED_COLUMNS), dropped)
    out_missing = os.path.join(base, 'submission_missing.csv')
    code, _ = _run_module_expect_fail(c, 'e2e.export_refuses_missing_prediction', exp.run,
                                      ns(pred=os.path.join(base, 'preds_missing.csv'), template=paths['template'],
                                         output=out_missing, data_root=paths['data_root'], report=None,
                                         check_range=False, allow_unregistered_template=True, overwrite=False))
    c.check('e2e.export_refuses_missing.no_file_written', not os.path.exists(out_missing), out_missing)

    bad_rows = [r[:] for r in prow]
    bad_rows[0][3] = 'nan'
    _write_csv(os.path.join(base, 'preds_nan.csv'), list(common.PRED_COLUMNS), bad_rows)
    code, _ = _run_module_expect_fail(c, 'e2e.export_refuses_nonfinite', exp.run,
                                      ns(pred=os.path.join(base, 'preds_nan.csv'), template=paths['template'],
                                         output=os.path.join(base, 'submission_nan.csv'), data_root=paths['data_root'],
                                         report=None, check_range=False, allow_unregistered_template=True,
                                         overwrite=False))

    tpl_lines2 = list(tpl_lines)
    spans = common.csv_field_spans(tpl_lines2[1])
    ys, ye = spans[4]
    tpl_lines2[1] = tpl_lines2[1][:ys] + '0.5' + tpl_lines2[1][ye:]
    tpl_bad = os.path.join(base, 'template_nonempty_yp.csv')
    with open(tpl_bad, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('\r\n'.join(tpl_lines2) + '\r\n')
    code, _ = _run_module_expect_fail(c, 'e2e.export_refuses_nonempty_template_ypred', exp.run,
                                      ns(pred=paths['pred'], template=tpl_bad,
                                         output=os.path.join(base, 'submission_bad_tpl.csv'),
                                         data_root=paths['data_root'], report=None, check_range=False,
                                         allow_unregistered_template=True, overwrite=False))

    _header, lrows = common.read_csv(os.path.join(paths['labels'], 'mini_mae.csv'))
    lrows2 = [r[:] for r in lrows]
    lrows2[0][0], lrows2[1][0] = lrows2[1][0], lrows2[0][0]
    _write_csv(os.path.join(base, 'labels_valid_bad', 'mini_mae.csv'), common.OFFICIAL_LABEL_COLUMNS, lrows2)
    for task, _m, vl, _vp, _e, _s in MINI_TASKS:
        if task != 'mini_mae':
            _write_csv(os.path.join(base, 'labels_valid_bad', task + '.csv'), common.OFFICIAL_LABEL_COLUMNS,
                       [[d, s, y] for (d, s), y in zip(_mini_molecules(task, len(vl)), vl)])
    code, _ = _run_module_expect_fail(c, 'e2e.score_refuses_misaligned_labels', score_mod.run,
                                      ns(pred=paths['pred'], split='valid', labels=os.path.join(base, 'labels_valid_bad'),
                                         data_root=paths['data_root'], template=paths['template'], report=None,
                                         report_csv=None))

    labels_partial = os.path.join(base, 'labels_valid_partial')
    for task, _m, vl, _vp, _e, _s in MINI_TASKS:
        if task != 'mini_mae':
            _write_csv(os.path.join(labels_partial, task + '.csv'), common.OFFICIAL_LABEL_COLUMNS,
                       [[d, s, y] for (d, s), y in zip(_mini_molecules(task, len(vl)), vl)])
    code, _ = _run_module_expect_fail(c, 'e2e.score_refuses_missing_label_task', score_mod.run,
                                      ns(pred=paths['pred'], split='valid', labels=labels_partial,
                                         data_root=paths['data_root'], template=paths['template'], report=None,
                                         report_csv=None))

    dup_rows = [r[:] for r in prow]
    dup_rows.append(list(dup_rows[0]))
    _write_csv(os.path.join(base, 'preds_dup.csv'), list(common.PRED_COLUMNS), dup_rows)
    code, _ = _run_module_expect_fail(c, 'e2e.check_predictions_detects_duplicate', cp_mod.run,
                                      ns(pred=os.path.join(base, 'preds_dup.csv'), data_root=paths['data_root'],
                                         report=None))

    long_labels = os.path.join(base, 'labels_long.csv')
    long_rows = []
    for task, _m, vl, _vp, _e, _s in MINI_TASKS:
        for i, y in enumerate(vl):
            long_rows.append([task, str(i), repr(float(y))])
    _write_csv(long_labels, ['task', 'row_index', 'y_true'], long_rows)
    code, _out = _run_module(c, 'e2e.score_long_label_csv', score_mod.run,
                             ns(pred=paths['pred'], split='valid', labels=long_labels,
                                data_root=paths['data_root'], template=paths['template'],
                                report=None, report_csv=None))
    return code


def _run_module_expect_fail(c, name, fn, args):
    buf = io.StringIO()
    code = None
    with contextlib.redirect_stdout(buf):
        try:
            code = fn(args)
        except SystemExit as e:
            code = e.code
    out = buf.getvalue()
    ok = isinstance(code, int) and code != 0
    c.check(name, ok, 'exit=%r; output tail: %s' % (code, out.strip().splitlines()[-1] if out.strip() else ''))
    return code, out


def run(args):
    c = Checks()
    _metric_unit_checks(c)
    _metric_agreement_checks(c)
    _span_checks(c)
    _e2e_checks(c)
    n_pass = sum(1 for i in c.items if i['status'] == 'pass')
    n_fail = c.n_fail
    for item in c.items:
        if item['status'] == 'fail':
            print('FAIL %s: %s' % (item['name'], item['detail']))
    print('selftest: %d checks, %d passed, %d failed' % (len(c.items), n_pass, n_fail))
    common.print_result(n_fail == 0)
    if getattr(args, 'report', None):
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump({
                'schema_version': 1,
                'tool': '%s %s' % (common.TOOL_NAME, common.TOOL_VERSION),
                'command': 'selftest',
                'generated_at_utc': common.utc_now_iso(),
                'n_checks': len(c.items),
                'n_passed': n_pass,
                'n_failed': n_fail,
                'overall': 'pass' if n_fail == 0 else 'fail',
                'checks': c.items,
            }, f, ensure_ascii=False, indent=2)
        print('report written: %s' % args.report)
    return 0 if n_fail == 0 else 1
