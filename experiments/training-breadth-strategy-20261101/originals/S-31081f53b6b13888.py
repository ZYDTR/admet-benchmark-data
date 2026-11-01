#!/usr/bin/env python3
"""Synthetic end-to-end demo of the task-B pipeline on fake data.

Builds a small synthetic project tree (4 tasks, official-format files, a
template with BOM/CRLF and quoted drug_id fields, a prediction file covering
valid+test, and official-format label CSVs), then drives the real CLI through
check-predictions -> score -> export -> validate-submission via subprocess.
Everything is synthetic and fixed; no training, no real labels, no model.

Usage:
  python3 examples/run_synthetic_demo.py [--workdir DIR] [--report PATH]
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)
RUNNER = os.path.join(PKG_ROOT, 'run_admet_eval.py')

DEMO_TASKS = [
    ('demo_auroc', 'AUROC', 12),
    ('demo_auprc', 'AUPRC', 12),
    ('demo_mae', 'MAE', 9),
    ('demo_spearman', 'Spearman', 9),
]

SPECIAL_IDS = {
    ('demo_auprc', 2): "Apigenin (5,7,4'-THF), mix",
    ('demo_auprc', 3): 'drug "quoted" \\ backslash',
    ('demo_mae', 0): '',
    ('demo_spearman', 5): '\1,2,2-dimethylbutane\\"',
}


def mol(task, i, offset):
    did = SPECIAL_IDS.get((task, i), 'D%d' % (i + offset))
    return [did, 'C%sO' % ('C' * (i + 1))]


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, lineterminator='\r\n')
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def build_fixture(workdir):
    for task, metric, n in DEMO_TASKS:
        bench = os.path.join(workdir, 'data', 'official', 'data_benchmark', task)
        write_csv(os.path.join(bench, 'train.csv'), ['Drug_ID', 'Drug', 'Y'],
                  [mol(task, i, 300) + [0] for i in range(n)])
        write_csv(os.path.join(bench, 'test.csv'), ['Drug_ID', 'Drug'],
                  [mol(task, i, 100) for i in range(n)])
        write_csv(os.path.join(workdir, 'data', 'blind_validation', task, 'valid.csv'),
                  ['Drug_ID', 'Drug'], [mol(task, i, 0) for i in range(n)])
        write_csv(os.path.join(workdir, 'labels', task + '.csv'),
                  ['Drug_ID', 'Drug', 'Y'],
                  [mol(task, i, 0) + [label_value(metric, i, n)] for i in range(n)])
    tpl_rows = []
    for task, metric, n in DEMO_TASKS:
        for i in range(n):
            did, smi = mol(task, i, 100)
            tpl_rows.append([task, str(i), did, smi, '', metric])
    write_csv(os.path.join(workdir, 'data', 'official', 'submission_template.csv'),
              ['task', 'sample_idx', 'drug_id', 'smiles', 'y_pred', 'metric'], tpl_rows)
    pred_rows = []
    for task, metric, n in DEMO_TASKS:
        for i in range(n):
            pred_rows.append([task, 'valid', str(i), repr(pred_value(metric, i, n, 'valid'))])
        for i in range(n):
            pred_rows.append([task, 'test', str(i), repr(pred_value(metric, i, n, 'test'))])
    write_csv(os.path.join(workdir, 'preds.csv'), ['task', 'split', 'row_index', 'y_pred'], pred_rows)
    return workdir


def label_value(metric, i, n):
    if metric in ('AUROC', 'AUPRC'):
        return 1 if i < n // 3 else 0
    if metric == 'MAE':
        return round(1.0 + 0.5 * i, 3)
    return i % 3


def pred_value(metric, i, n, split):
    if metric in ('AUROC', 'AUPRC'):
        if split == 'valid':
            return round(1.0 - 0.05 * i, 4)
        return round(0.05 * i, 4)
    if metric == 'MAE':
        return round(0.9 + 0.5 * i, 3)
    return float(i % 3)


def run_cli(label, args, steps):
    cmd = [sys.executable, RUNNER] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=PKG_ROOT)
    steps.append({
        'step': label,
        'command': ' '.join(args),
        'exit_code': proc.returncode,
        'stdout_tail': '\n'.join(proc.stdout.strip().splitlines()[-6:]),
        'stderr_tail': proc.stderr.strip()[-400:],
    })
    print('[%s] exit=%d' % (label, proc.returncode))
    for line in proc.stdout.strip().splitlines()[-4:]:
        print('   %s' % line)
    return proc.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', default=None)
    parser.add_argument('--report', default=os.path.join(PKG_ROOT, 'reports', 'demo_report.json'))
    args = parser.parse_args()
    workdir = args.workdir or tempfile.mkdtemp(prefix='admet_eval_demo_')
    build_fixture(workdir)
    print('synthetic fixture: %s' % workdir)
    steps = []
    data_root = workdir
    tpl = os.path.join(workdir, 'data', 'official', 'submission_template.csv')
    pred = os.path.join(workdir, 'preds.csv')
    sub = os.path.join(workdir, 'submission.csv')
    codes = []
    codes.append(run_cli('check-predictions', [
        'check-predictions', '--pred', pred, '--data-root', data_root,
        '--report', os.path.join(workdir, 'check_report.json')], steps))
    codes.append(run_cli('score', [
        'score', '--pred', pred, '--split', 'valid', '--labels', os.path.join(workdir, 'labels'),
        '--data-root', data_root, '--template', tpl,
        '--report', os.path.join(workdir, 'score_report.json')], steps))
    codes.append(run_cli('export', [
        'export', '--pred', pred, '--template', tpl, '--output', sub, '--data-root', data_root,
        '--allow-unregistered-template',
        '--report', os.path.join(workdir, 'export_report.json')], steps))
    codes.append(run_cli('validate-submission', [
        'validate-submission', '--submission', sub, '--template', tpl,
        '--allow-unregistered-template',
        '--report', os.path.join(workdir, 'validate_report.json')], steps))
    ok = all(c == 0 for c in codes)
    print('demo result: %s (fixture kept at %s)' % ('PASS' if ok else 'FAIL', workdir))
    report = {
        'schema_version': 1,
        'command': 'run_synthetic_demo',
        'workdir': workdir,
        'fixture': {'tasks': [t[0] for t in DEMO_TASKS], 'rows_per_task': {t[0]: t[2] for t in DEMO_TASKS}},
        'steps': steps,
        'overall': 'pass' if ok else 'fail',
    }
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('report written: %s' % args.report)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
