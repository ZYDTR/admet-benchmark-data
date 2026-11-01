"""Root-controlled baseline, executed in a bounded offline container without valid Y."""
from pathlib import Path
import csv
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time

ROOT=Path('/work')
OUT=ROOT/'result'
SRC=ROOT/'output/model/src'
sys.path.insert(0,str(SRC))
OUT.mkdir(exist_ok=True)
t0=time.time()
CACHE=Path('/cache')
RUN_ID='chemeleon-host-v3-20261030'

def event(kind, **data):
    # Docker stdout is the event journal; do not reopen a shared append file.
    print(json.dumps({'time':time.time(),'event':kind,**data}), flush=True)

def phase(name, args):
    event('phase_start',phase=name,args=list(map(str,args)))
    with (OUT/(name+'.log')).open('w') as f:
        p=subprocess.run([sys.executable,'-B',*map(str,args)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,
                         timeout=max(10,3500-int(time.time()-t0)),check=False)
    event('phase_end',phase=name,exit_code=p.returncode)
    if p.returncode:raise RuntimeError(f'{name} failed: {p.returncode}')

try:
    import numpy as np
    import torch
    torch.set_num_threads(2)
    from encoder import CheMeleonEmbedder
    e=CheMeleonEmbedder(Path('/assets/chemeleon_mp.pt'),'cpu',32)
    e.assert_frozen()
    def model_hash():
        h=hashlib.sha256()
        for k,v in e.model.state_dict().items():h.update(k.encode());h.update(v.cpu().numpy().tobytes())
        return h.hexdigest()
    before=model_hash()
    a,ok=e.embed(['CCO','c1ccccc1','not_a_smiles'])
    b,ok2=e.embed(['CCO','c1ccccc1','not_a_smiles'])
    c,_=e.embed(['CCO'])
    assert a.shape==(3,2048) and ok.tolist()==[True,True,False]
    assert np.isfinite(a[ok]).all() and np.isnan(a[~ok]).all()
    assert np.array_equal(a,b,equal_nan=True) and np.allclose(a[:1],c,atol=1e-6)
    assert before==model_hash()
    del e
    freeze={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    (OUT/'environment.json').write_text(json.dumps({'python':sys.version,'dependencies':freeze,
        'encoder_frozen_before_after':before,'device':'cpu','threads':2},indent=2))
    event('encoder_preflight_pass')
    from build_features import build_coverage_report
    event('phase_start',phase='verify_reused_features',source='host-v2-readonly-cache')
    coverage=build_coverage_report(CACHE, {'sha256':'c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651'})
    assert coverage['total_rows']==81809 and coverage['total_unparseable_rows']==2
    (OUT/'feature-coverage.json').write_text(json.dumps(coverage,indent=2))
    event('phase_end',phase='verify_reused_features',exit_code=0,rows=coverage['total_rows'])
    phase('train',[SRC/'train.py','--cache',CACHE,'--out',OUT/'model','--device','cpu'])
    phase('predict',[SRC/'predict.py','--cache',CACHE,'--ckpt',OUT/'model','--out',OUT/'predictions',
          '--device','cpu','--run-id',RUN_ID])
    phase('test-coverage',[ROOT/'output/data-eval/check_coverage.py','--predictions',OUT/'predictions/test_predictions.csv',
          '--template',ROOT/'data/official/submission_template.csv','--json',OUT/'test-coverage.json'])
    phase('export',[ROOT/'output/data-eval/export_submission.py','--predictions',OUT/'predictions/test_predictions.csv',
          '--template',ROOT/'data/official/submission_template.csv','--out',OUT/'submission.csv'])
    # Independent complete valid coverage, no labels involved.
    from common import TASKS
    expected=set()
    for task in TASKS:
        with (ROOT/f'data/blind_validation/{task}/valid.csv').open(newline='',encoding='utf-8-sig') as f:
            rows=list(csv.DictReader(f))
        assert all(set(r)=={'Drug_ID','Drug'} for r in rows)
        expected.update((task,'valid',i) for i in range(len(rows)))
    with (OUT/'predictions/valid_predictions.csv').open(newline='') as f:records=list(csv.DictReader(f))
    keys=[(r['task'],r['split'],int(r['row_index'])) for r in records]
    assert len(keys)==len(set(keys)) and set(keys)==expected
    assert all(np.isfinite(float(r['y_pred'])) for r in records)
    # Preserve template non-prediction fields, BOM, line endings and all rows.
    raw=(ROOT/'data/official/submission_template.csv').read_bytes();out=(OUT/'submission.csv').read_bytes()
    assert raw.startswith(b'\xef\xbb\xbf') and out.startswith(b'\xef\xbb\xbf')
    assert out.count(b'\n')==out.count(b'\r\n')==16380
    import io
    left=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'),newline='')))
    right=list(csv.reader(io.StringIO(out.decode('utf-8-sig'),newline='')))
    assert len(left)==len(right)==16380 and left[0]==right[0]
    assert all(a[:4]+a[5:]==b[:4]+b[5:] for a,b in zip(left[1:],right[1:]))
    event('completed',valid_rows=len(keys),test_rows=16379,elapsed_seconds=time.time()-t0)
    (OUT/'status.json').write_text(json.dumps({'status':'completed','run_id':RUN_ID,'valid_rows':len(keys),'test_rows':16379,
          'elapsed_seconds':time.time()-t0,'scoring_status':'external_required'},indent=2))
except BaseException as exc:
    event('failed',error_type=type(exc).__name__,error=str(exc))
    (OUT/'status.json').write_text(json.dumps({'status':'failed','error_type':type(exc).__name__,'error':str(exc)},indent=2))
    raise
