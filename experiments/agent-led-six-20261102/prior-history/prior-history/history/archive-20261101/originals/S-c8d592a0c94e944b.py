#!/usr/bin/env python3
"""Analysis-side only. Read exact local public CSV originals; no network/model/training.
Usage: python reproduce_checks.py --truth valid.csv --current predictions.csv
       [--historic-a oldA.csv --historic-b oldB.csv --training-evidence training-evidence.json]
       [--require-full-source-hashes]
Do NOT forward source truth, numeric output or this audit package to preparation/training.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from decimal import Decimal, localcontext
from pathlib import Path
EXPECTED={
 'truth':'63328bf307b850a4a0986165d0800bae5aa737c41bd63f1026d16114d8560bb4',
 'current':'0d1f4121f2eb6d2af9fd4471b32f05b3056030504b37e513d9ed2904092a3bda',
 'historic_a':'e674439f83d55a17703e2a0d59bc3142874b4ad956d9f6fbb7a3377b40675993',
 'historic_b':'aa33ca53bc0e1570aba6cf6d4ec1e82f41e126dc0fd57715cd52c32d2ee29bfb'}
def read_csv(path:Path, required:set[str]):
 with path.open(encoding='utf-8',newline='') as f:
  reader=csv.DictReader(f)
  if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):raise ValueError(f'{path}: missing/duplicate header')
  if not required.issubset(reader.fieldnames):raise ValueError(f'{path}: missing required columns')
  rows=list(reader)
 if any(None in row for row in rows):raise ValueError(f'{path}: malformed CSV row')
 return rows

def main()->int:
 ap=argparse.ArgumentParser(description=__doc__)
 for key in ['truth','current','historic-a','historic-b','training-evidence']:
  ap.add_argument('--'+key,type=Path,required=key in ['truth','current'])
 ap.add_argument('--require-full-source-hashes',action='store_true')
 args=ap.parse_args(); hashes={}
 for key,expected in EXPECTED.items():
  path=getattr(args,key)
  if path is not None:
   raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
   hashes[key]={'bytes':len(raw),'observed_sha256':digest,'expected_sha256':expected,'matches':digest==expected}
   if key=='truth' and (len(raw)!=8098 or digest!=expected):raise ValueError('Approved truth source byte identity mismatch')
   if args.require_full_source_hashes and digest!=expected:raise ValueError(f'{key}: full-source hash mismatch')
 truth=read_csv(args.truth,{'Drug_ID','Drug','Y'})
 if len(truth)!=91:raise ValueError('truth must retain all 91 original rows')
 result={'scope':'caco2-analysis-20261031-cycle002','source_bytes':hashes,'model_executions':0,'host_scoring_calls':0,'models':{}}
 with localcontext() as ctx:
  ctx.prec=50; yy=[Decimal(x['Y']) for x in truth]
  if not all(x.is_finite() for x in yy):raise ValueError('Nonfinite Y')
  for key in ['current','historic_a','historic_b']:
   path=getattr(args,key)
   if path is None:continue
   rows=read_csv(path,{'task','split','row_index','Drug_ID','Drug','y_pred'})
   rows=[r for r in rows if r['task']=='caco2_wang' and r['split']=='valid']
   if len(rows)!=91:raise ValueError(f'{key}: expected exactly 91 matching rows')
   for i,(t,r) in enumerate(zip(truth,rows)):
    if int(r['row_index'])!=i or r['Drug_ID']!=t['Drug_ID'] or r['Drug']!=t['Drug']:raise ValueError(f'{key}: row identity mismatch at {i}')
   pp=[Decimal(x['y_pred']) for x in rows]
   if not all(x.is_finite() for x in pp):raise ValueError(f'{key}: nonfinite prediction')
   ae=[abs(a-b) for a,b in zip(pp,yy)]
   result['models'][key]={'n':91,'identity_match':True,'mae_decimal':str(sum(ae)/Decimal(91)),
      'mae_float_fsum':math.fsum(map(float,ae))/91,'rmse':math.sqrt(math.fsum(float(x*x) for x in ae)/91),
      'p95_nearest_rank':float(sorted(ae)[math.ceil(.95*91)-1])}
   if key=='current':
    # Literal contract filter, not a statistic inferred from the aggregate score.
    first=[Decimal(r['y_pred']) for r in rows if 0<=int(r['row_index'])<=9]
    if len(first)!=10:raise ValueError('CSV-002 did not select 10 rows')
    result['CSV-002']=float(sum(first)/Decimal(10))
 if args.training_evidence is not None:
  evidence=json.loads(args.training_evidence.read_text(encoding='utf-8'))
  h=evidence['history']
  result['epoch_check']={'n':len(h),'mse_best_epoch':min(h,key=lambda r:r['internal_validation_standardized_mse'])['epoch'],
     'mae_best_epoch':min(h,key=lambda r:r['stop_eval_mae'])['epoch']}
 print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False));return 0
if __name__=='__main__':
 try:sys.exit(main())
 except (OSError,ValueError,KeyError,ArithmeticError) as exc:
  print(f'CHECK_FAILED: {exc}',file=sys.stderr);sys.exit(1)
