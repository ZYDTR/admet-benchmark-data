"""Primary verifies existing retrieval and score; no fixed scorer invocation or model execution."""
import ast, csv, decimal, hashlib, io, json, math
from datetime import datetime, timezone
from pathlib import Path

OUT=Path(__file__).resolve().parent
C=OUT.parents[1]
R=C.parents[1]
T=C/'retrieval'
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
task=load(T/'control/SCORING_TASK.json')
before=load(T/'manifests/remote-before.json');after=load(T/'manifests/remote-after.json')
files={x['path']:x for x in before['entries'] if x['type']=='file' and x['disposition']=='transfer'}
assert len(files)==99
end={x['path']:x for x in after['entries'] if x['type']=='file' and x['disposition']=='transfer'}
assert set(files)==set(end)
for name,item in files.items():
    p=T/'snapshot'/name
    assert not Path(name).is_absolute() and '..' not in Path(name).parts
    assert p.resolve(strict=True)==p and p.stat().st_nlink==1
    assert p.stat().st_size==item['size_bytes'] and sha(p)==item['sha256']
    assert all(item[k]==end[name][k] for k in ['size_bytes','sha256','device','inode','mtime_ns','ctime_ns'])
assert {p.relative_to(T/'snapshot').as_posix() for p in (T/'snapshot').rglob('*') if p.is_file()}==set(files)
assert load(T/'manifests/source-stability.json')['stable'] is True
cfg=load(T/'snapshot/run/source/config.json')
assert sha(T/'snapshot/run/assets/chemeleon_mp.pt')==cfg['pretrained_sha256']
science=load(T/'snapshot/run/admission/science-manifest.json')
assert sha(T/'snapshot/run/encoder.py')==science['encoder.py']['sha256']

for field,filename in [('fixed_function','fixed_mae.py'),('strict_wrapper','strict_caco2_scorer.py')]:
    assert sha(T/'source'/filename)==task[field]['sha256']
origin=Path(task['scorer_origin']['source']);assert sha(origin)==task['scorer_origin']['source_sha256']
def function(text):return next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='_mae')
assert ast.dump(function(origin.read_text()),include_attributes=False)==ast.dump(function((T/'source/fixed_mae.py').read_text()),include_attributes=False)
receipt=load(T/'private_scoring/scoring-receipt.json');ledger=load(T/'private_scoring/call-ledger.json')
assert receipt['metric_calls']==ledger['metric_calls']==1 and receipt['metric_completed'] is True
assert receipt['run_id']==task['run_id'] and receipt['rows']==91 and receipt['test_rows_excluded']==182

def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f); result=list(reader)
        assert len(reader.fieldnames)==len(set(reader.fieldnames)) and all(None not in x and all(v is not None for v in x.values()) for x in result)
        return reader.fieldnames,result
truth_path=T/'private_scoring/original-valid.csv'
assert sha(truth_path)==task['truth']['sha256']
truth_fields,truth=rows(truth_path)
assert set(truth_fields)=={'Drug_ID','Drug','Y'} and len(truth)==91
blind_path=T/'snapshot/run/data/valid.csv';assert sha(blind_path)==task['blind_projection_sha256']
fields,blind=rows(blind_path);assert set(fields)=={'Drug_ID','Drug'} and len(blind)==91
prediction=T/'snapshot/run/artifacts/predictions.csv';assert sha(prediction)==task['prediction_identity']['sha256']
fields,pred=rows(prediction);assert len(pred)==273
valid=[x for x in pred if x['split']=='valid'];test=[x for x in pred if x['split']=='test']
assert len(valid)==91 and len(test)==182 and pred==valid+test
decimal.getcontext().prec=50
errors=[]
for i,(v,b,y) in enumerate(zip(valid,blind,truth)):
    assert v['task']=='caco2_wang' and v['row_index']==str(i)
    assert v['Drug_ID']==b['Drug_ID']==y['Drug_ID'] and v['Drug']==b['Drug']==y['Drug']
    yp=decimal.Decimal(v['y_pred']);yt=decimal.Decimal(y['Y']);assert yp.is_finite() and yt.is_finite()
    errors.append(abs(yp-yt))
value=sum(errors)/len(errors)
score=load(T/'private_scoring/scores.json')
assert score['metric']=='MAE' and score['direction']=='minimize' and score['n']==91
assert abs(value-decimal.Decimal(str(score['value'])))<decimal.Decimal('1e-12')
previous=R/'cycles/progressive-index-e2e-20261031/retrieval/phase2'
old_score=load(previous/'private_scoring/scores.json')
old_cfg=load(previous/'snapshot/run/source/config.json')
differences={k:{'old':old_cfg.get(k),'new':cfg.get(k)} for k in set(old_cfg)|set(cfg) if old_cfg.get(k)!=cfg.get(k)}
assert set(differences)=={'run_id','monitor'}
split=load(T/'snapshot/run/artifacts/internal-split.json');old_split=load(previous/'snapshot/run/artifacts/internal-split.json')
assert split['fit_row_indices']==old_split['fit_row_indices'] and split['stop_row_indices']==old_split['stop_row_indices']
old_value=decimal.Decimal(str(old_score['value']))
result={'recorded_at':datetime.now(timezone.utc).isoformat(),'run_id':task['run_id'],'retrieval_files_independently_hashed':len(files),
    'retrieval_bytes':sum(x['size_bytes'] for x in files.values()),'source_snapshot_stable':True,'large_asset_and_encoder_completed':True,
    'fixed_function_ast_matches_host':True,'executor_fixed_metric_calls':1,'controller_fixed_metric_calls':0,
    'controller_verification':'Independent Decimal50 arithmetic from already-produced private score inputs; no rerun of scoring wrapper',
    'metric':'MAE','rows':91,'test_rows_not_scored':182,'reported_score':score['value'],'decimal50_verified_score':str(value),
    'score_verified':True,'previous_reported_score':old_score['value'],'absolute_improvement':str(old_value-value),
    'relative_improvement_percent':str(100*(old_value-value)/old_value),'comparison_config_differences':differences,
    'same_internal_row_split':True,'causal_or_generalization_claim':False,'row_truth_or_residuals_exported':False,
    'evidence_sha256':{str(p.relative_to(T)):sha(p) for p in [T/'private_scoring/scores.json',T/'private_scoring/scoring-receipt.json',T/'source/score_once.py',T/'manifests/remote-before.json',T/'manifests/remote-after.json']},
    'publication_candidate_accepted':False,'full_cycle_complete':False}
with (OUT/'result.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['retrieval_files_independently_hashed','score_verified','reported_score','previous_reported_score','relative_improvement_percent']}))
