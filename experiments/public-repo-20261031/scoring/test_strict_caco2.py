"""Fixed synthetic counterexamples, run before the truth file is read."""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import time
from strict_caco2_scorer import score_once,validate_valid,truth_identity,select_valid_from_original_csv

ROOT=Path(__file__).resolve().parents[1]
start=time.monotonic_ns()
blind=[{'Drug_ID':'','Drug':'CC'},{'Drug_ID':'','Drug':'CO'}]
truth=[dict(**b,Y=y) for b,y in zip(blind,['1','3'])]
pred=[dict(task='caco2_wang',split='valid',row_index=str(i),**b,y_pred=y)
      for i,(b,y) in enumerate(zip(blind,['2','5']))]
cases=[]
assert score_once(truth,blind,pred)['value']==1.5
cases.append(dict(case='known_mae_and_duplicate_empty_ids',passed=True))
perfect=[{**p,'y_pred':t['Y']} for p,t in zip(pred,truth)]
assert score_once(truth,blind,perfect)['value']==0
cases.append(dict(case='perfect_zero',passed=True))
for name,change in [
    ('missing_row',lambda x:x.pop()),('extra_row',lambda x:x.append(copy.deepcopy(x[0]))),
    ('duplicated_identity',lambda x:x[1].update(row_index='0')),
    ('wrong_id',lambda x:x[0].update(Drug_ID='other')),('wrong_smiles',lambda x:x[0].update(Drug='CCC')),
    ('wrong_task',lambda x:x[0].update(task='other_task')),('nonvalid_split',lambda x:x[0].update(split='test')),
    ('wrong_index',lambda x:x[0].update(row_index='1')),('extra_field',lambda x:x[0].update(Y='1')),
    ('nan_prediction',lambda x:x[0].update(y_pred='NaN')),('infinite_prediction',lambda x:x[0].update(y_pred='Infinity')),
    ('boolean_prediction',lambda x:x[0].update(y_pred=True)),('reordered_rows',lambda x:x.reverse())]:
    data=copy.deepcopy(pred);change(data)
    try:score_once(truth,blind,data)
    except ValueError as err:cases.append(dict(case=name,passed=True,rejection=str(err)))
    else:raise AssertionError('Counterexample accepted: '+name)
for name,tr,bl in [('truth_blind_mismatch',[{**truth[0],'Drug':'CCC'},truth[1]],blind),
                   ('nonfinite_truth',[{**truth[0],'Y':'NaN'},truth[1]],blind),
                   ('empty_input',[],[])]:
    try:score_once(tr,bl,pred if bl else [])
    except ValueError as err:cases.append(dict(case=name,passed=True,rejection=str(err)))
    else:raise AssertionError('Truth counterexample accepted: '+name)
out={'passed':True,'cases':cases,'case_count':len(cases),'private_truth_read':False,
     'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'end_monotonic_ns':time.monotonic_ns(),'seconds':(time.monotonic_ns()-start)/1e9,
     'wrapper_sha256':hashlib.sha256((ROOT/'source/strict_caco2_scorer.py').read_bytes()).hexdigest()}
with (ROOT/'manifests/scorer-tests.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps({'passed':True,'synthetic_cases':len(cases)}))
