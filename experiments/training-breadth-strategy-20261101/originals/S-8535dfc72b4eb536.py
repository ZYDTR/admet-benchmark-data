"""Read-only arithmetic on public CSV/JSON; never loads a model or a label from outside packet."""
from pathlib import Path
from decimal import Decimal, localcontext
from collections import Counter, defaultdict
import csv, json, math, statistics, hashlib
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'root-checks'; OUT.mkdir(exist_ok=True)
read=[]
def get(p):
    b=(ROOT/p).read_bytes()
    read.append({'path':p,'lines':len(b.splitlines()),'sha256':hashlib.sha256(b).hexdigest(),'coverage':'entire content parsed for stated checks'})
    return b.decode('utf-8-sig')
def rows(p):return list(csv.DictReader(get(p).splitlines()))
def js(p):return json.loads(get(p))
tables={s:rows('data/'+s+'.csv') for s in ['train','valid','test']}
assert list(tables['train'][0])==['Drug_ID','Drug','Y']
assert all(set(tables[s][0])=={'Drug_ID','Drug'} for s in ['valid','test'])
ys=[float(r['Y']) for r in tables['train']]
data={s:{'rows':len(v),'fields':list(v[0]),'unique_raw_smiles':len({r['Drug'] for r in v}),'unique_ids':len({r['Drug_ID'] for r in v})} for s,v in tables.items()}
data['train_Y']={'mean':statistics.fmean(ys),'std_population':statistics.pstdev(ys),'minimum':min(ys),'maximum':max(ys),'all_finite':all(map(math.isfinite,ys))}
data['cross_split_raw_smiles_overlap']={a+'__'+b:len({r['Drug'] for r in tables[a]}&{r['Drug'] for r in tables[b]}) for a,b in [('train','valid'),('train','test'),('valid','test')]}
runs=['hainan-frozen-training-20261031','hainan-skill-follow-20261031']
checks=[];arrays=[];preds=[]
for run in runs:
    base='runs/'+run+'/'
    p=rows(base+'artifacts/predictions.csv');preds.append(p)
    t=js(base+'artifacts/training-evidence.json'); cfg=js(base+'source/config.json')
    h=rows(base+'learning-curve.csv'); a=js(base+'preprocessing-readable.json')['arrays']; arrays.append(a)
    before=js(base+'artifacts/encoder-before.json');after=js(base+'artifacts/encoder-after.json');bs=js(base+'binary-structure.json')
    assert before==after
    assert h==[{k:str(v) for k,v in x.items()} for x in t['history']]
    expected=[('valid',i,r) for i,r in enumerate(tables['valid'])]+[('test',i,r) for i,r in enumerate(tables['test'])]
    assert len(p)==len(expected)==273
    assert len({(x['task'],x['split'],x['row_index']) for x in p})==273
    for x,(split,i,r) in zip(p,expected):
        assert x['task']=='caco2_wang' and x['split']==split and x['row_index']==str(i)
        assert x['Drug_ID']==r['Drug_ID'] and x['Drug']==r['Drug'] and math.isfinite(float(x['y_pred']))
    v=[x for x in p if x['split']=='valid']
    with localcontext() as ctx:
        ctx.prec=50
        mean=sum((Decimal(x['y_pred']) for x in v),Decimal(0))/Decimal(len(v))
    tr=a['train_row_indices']['values'];va=a['internal_validation_row_indices']['values']
    assert len(tr)==len(set(tr))==573 and len(va)==len(set(va))==64
    assert not set(tr)&set(va) and set(tr)|set(va)==set(range(637))
    overlap={tables['train'][i]['Drug'] for i in tr}&{tables['train'][i]['Drug'] for i in va}
    duplicate_groups=[]
    for smi in sorted(overlap):
        ids=[i for i,r in enumerate(tables['train']) if r['Drug']==smi]
        duplicate_groups.append({'row_indices':ids,'roles':['fit' if i in tr else 'internal_stop' for i in ids],'Drug_ID':[tables['train'][i]['Drug_ID'] for i in ids],'train_Y':[tables['train'][i]['Y'] for i in ids]})
    fit_y=[ys[i] for i in tr];stop_y=[ys[i] for i in va]
    best=min(t['history'], key=lambda x:x['internal_validation_standardized_mse'])
    assert best['epoch']==t['best_epoch_1_based']
    assert t['optimizer_steps']==math.ceil(len(tr)/cfg['head_config']['batch_size'])*t['epochs_run']
    dist={}
    for s in ['valid','test']:
        z=[float(x['y_pred']) for x in p if x['split']==s]
        dist[s]={'n':len(z),'mean':statistics.fmean(z),'std_population':statistics.pstdev(z),'minimum':min(z),'maximum':max(z),'unique_prediction_values':len(set(z))}
    checks.append({'run_id':run,'all_prediction_rows':len(p),'valid_rows':len(v),'mean_valid_prediction':str(mean),'optimizer_steps':t['optimizer_steps'],'best_epoch_1_based':t['best_epoch_1_based'],'epochs_run':t['epochs_run'],'row_alignment_passed':True,'prediction_distribution':dist,'split_identity':{'fit_payload_sha256':a['train_row_indices']['payload_sha256'],'stop_payload_sha256':a['internal_validation_row_indices']['payload_sha256'],'fit_rows':573,'stop_rows':64,'fit_stop_raw_smiles_overlap':duplicate_groups},'train_transform':{'recorded_target_mean':a['target_mean']['values'][0],'independent_double_mean':statistics.fmean(fit_y),'recorded_target_std':a['target_std']['values'][0],'independent_double_std':statistics.pstdev(fit_y),'stop_mean':statistics.fmean(stop_y),'stop_std':statistics.pstdev(stop_y)},'encoder_before_after_equal':before==after,'tensor_kinds':dict(Counter(x['kind'] for x in before['tensors'].values())),'encoder_events':{'count':len(t['encoder_forward_events']),'all_no_grad_eval_cuda':all(not x['grad_enabled'] and not x['training'] and x['devices']==['cuda:0'] for x in t['encoder_forward_events'])},'best_internal_raw_RMSE_from_logged_MSE':math.sqrt(best['internal_validation_standardized_mse'])*a['target_std']['values'][0],'last_to_best_internal_mse_ratio':t['history'][-1]['internal_validation_standardized_mse']/best['internal_validation_standardized_mse']})
paired={}
for split in ['valid','test']:
    a=[float(x['y_pred']) for x in preds[0] if x['split']==split];b=[float(x['y_pred']) for x in preds[1] if x['split']==split]
    delta=[v-u for u,v in zip(a,b)]
    paired[split]={'mean_B_minus_A':statistics.fmean(delta),'mean_abs_prediction_difference':statistics.fmean(map(abs,delta)),'rms_prediction_difference':math.sqrt(statistics.fmean([d*d for d in delta])),'maximum_abs_prediction_difference':max(map(abs,delta)),'pearson_prediction_correlation':statistics.correlation(a,b),'n':len(a)}
scores=js('scoring/scores.json')['scores']
score_delta=Decimal(str(scores[1]['value']))-Decimal(str(scores[0]['value']))
out={'method':'Python stdlib csv/json/statistics; means from decimal strings in prediction CSV, never inferred from scores. Original valid/test Y not present or accessed. No scorer or model executed.','read_checks':checks,'data_checks':data,'paired_prediction_comparison':paired,'published_score_delta_B_minus_A':str(score_delta),'internal_stop_index_intersection':len(set(arrays[0]['internal_validation_row_indices']['values'])&set(arrays[1]['internal_validation_row_indices']['values']))}
(OUT/'read-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(OUT/'read-receipt.json').write_text(json.dumps(read,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
