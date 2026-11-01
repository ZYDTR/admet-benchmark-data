"""Host review of frozen worker code; synthetic labels only, never private Y."""
import csv
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'acceptance-original'
CODE = PROJECT / 'output/data-eval'
sys.path.insert(0, str(CODE))
import score
import metrics

results = {}
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
tmp_root = ROOT / 'acceptance/tmp'
tmp_root.mkdir(exist_ok=True)
env['TMPDIR'] = str(tmp_root)

for script in ['test_metrics.py', 'smoke_test.py']:
    p = subprocess.run([sys.executable, '-B', str(CODE/script)], cwd=PROJECT,
                       env=env, capture_output=True, text=True, timeout=60)
    (ROOT/'acceptance'/f'original-{script}.log').write_text(p.stdout+p.stderr)
    results[script] = {'exit_code': p.returncode}

with tempfile.TemporaryDirectory(dir=tmp_root) as td:
    td = Path(td)
    (td/'labels').mkdir()
    (td/'template.csv').write_text('task,metric\ncaco2_wang,MAE\n')
    (td/'labels/caco2_wang.csv').write_text('Y\n0\n10\n')
    for name, records in {
        'missing_row': [('caco2_wang','valid',0,0)],
        'duplicate_row': [('caco2_wang','valid',0,99),('caco2_wang','valid',0,0),('caco2_wang','valid',1,10)],
        'unknown_task': [('caco2_wang','valid',0,0),('caco2_wang','valid',1,10),('unknown','valid',0,5)],
    }.items():
        pred=td/f'{name}.csv'
        with pred.open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['task','split','row_index','y_pred']);w.writerows(records)
        out=td/f'{name}.json'
        p=subprocess.run([sys.executable,'-B',str(CODE/'score.py'),'--predictions',str(pred),
                          '--labels-dir',str(td/'labels'),'--template',str(td/'template.csv'),
                          '--out',str(out)],capture_output=True,text=True,timeout=10,env=env)
        results[name]={'exit_code':p.returncode,'incorrectly_accepted':p.returncode==0,
                       'result':json.loads(out.read_text()) if out.exists() else None}

try:
    value=metrics.auroc([0.2,0.8],[0.1,0.9])
    results['fractional_binary_labels']={'incorrectly_accepted':True,'value':value}
except ValueError:
    results['fractional_binary_labels']={'incorrectly_accepted':False}

results['single_class_ap']={'value':metrics.average_precision([1,1],[0.1,0.9]),
                            'project_expected':None}
(ROOT/'acceptance/original-review.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2))
