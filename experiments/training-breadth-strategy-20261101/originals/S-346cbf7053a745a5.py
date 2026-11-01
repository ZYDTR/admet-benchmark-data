"""Host audit: synthetic labels only; frozen candidate files remain unchanged."""
from pathlib import Path
import csv
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
CODE = ROOT.parent / 'originals/output/data-eval'
MODEL = ROOT.parent / 'originals/output/model'
INPUT = REPO / 'adhoc_jobs/admet_deepseek_skill_coldstart_20261030/model/input'
SYN = REPO / 'adhoc_jobs/admet_deepseek_skill_coldstart_20261030/acceptance/synthetic'
TMP = ROOT / 'tmp'
TMP.mkdir(exist_ok=True)
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': str(TMP),
       'ADMET_EVAL_DATA_ROOT': str(INPUT)}
results = []

def run(name, args, expected=0, cwd=CODE):
    proc = subprocess.run([sys.executable, *map(str, args)], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=90)
    (ROOT / (name + '.log')).write_text(proc.stdout + proc.stderr)
    item = dict(name=name, returncode=proc.returncode, expected=expected,
                pass_condition=proc.returncode == expected if expected == 0 else proc.returncode != 0,
                command=list(map(str, args)), tail=(proc.stdout + proc.stderr)[-600:])
    results.append(item)
    print(json.dumps(item, ensure_ascii=False), flush=True)

run('selftest', ['run_admet_eval.py', 'selftest', '--report', ROOT/'selftest.json'])
run('verify-inputs', ['run_admet_eval.py', 'verify-inputs', '--data-root', INPUT,
                     '--schema', INPUT/'reference-harness/competition/task_schema.json', '--report', ROOT/'verify-inputs.json'])
run('model-data', ['-m', 'chemeleon_baseline.selfcheck', 'data', '--data-root', INPUT/'data',
                  '--report', ROOT/'model-data.json'], cwd=MODEL)
for case in ['perfect', 'missing', 'duplicate', 'unknown-task', 'nan', 'inf', 'wrong-split', 'negative-index', 'empty']:
    run('score-'+case, ['run_admet_eval.py', 'score', '--pred', SYN/f'valid-{case}.csv',
                       '--labels', SYN/'labels', '--data-root', INPUT, '--report', ROOT/f'score-{case}.json'],
        expected=0 if case == 'perfect' else 1)
run('export-full', ['run_admet_eval.py', 'export', '--pred', SYN/'test-full.csv',
                    '--data-root', INPUT, '--output', ROOT/'synthetic-submission.csv', '--check-range',
                    '--report', ROOT/'export-full.json'])
run('validate-full', ['run_admet_eval.py', 'validate-submission', '--submission', ROOT/'synthetic-submission.csv',
                      '--template', INPUT/'data/official/submission_template.csv', '--report', ROOT/'validate-full.json'])

# Independent field comparison, using stdlib CSV rather than candidate validation.
original = list(csv.reader((INPUT/'data/official/submission_template.csv').open(encoding='utf-8-sig', newline='')))
candidate = list(csv.reader((ROOT/'synthetic-submission.csv').open(encoding='utf-8-sig', newline='')))
y = original[0].index('y_pred')
assert len(original) == len(candidate) == 16380
assert original[0] == candidate[0]
assert all([a[:y]+a[y+1:] == b[:y]+b[y+1:] for a,b in zip(original[1:],candidate[1:])])

sys.path.insert(0, str(CODE))
from admet_eval import metrics
edge = {}
for key, fn, ys, ps in [('auc_tie', metrics.auroc, [0,1], [0.5,0.5]),
                        ('ap_tie', metrics.average_precision, [0,1], [0.5,0.5]),
                        ('ap_all_positive', metrics.average_precision, [1,1], [0.2,0.8]),
                        ('ap_all_negative', metrics.average_precision, [0,0], [0.2,0.8]),
                        ('spearman_constant', metrics.spearman, [1,1], [0,1]),
                        ('fractional_label', metrics.auroc, [0.4,1], [0.1,0.9])]:
    try:
        edge[key] = {'result': fn(ys,ps)}
    except Exception as e:
        edge[key] = {'exception': type(e).__name__, 'message': str(e)}
(ROOT/'data-checks.json').write_text(json.dumps({'runs':results,'edge':edge,'independent_template_rows':len(candidate)-1},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'edge':edge,'pass_count':sum(x['pass_condition'] for x in results),'runs':len(results)},ensure_ascii=False))
