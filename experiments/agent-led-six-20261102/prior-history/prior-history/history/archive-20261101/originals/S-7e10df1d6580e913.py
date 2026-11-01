"""Read-only analysis of already published predictions and numeric feature caches.
No model/scoring code imports, no external data, no fit, no inference.
"""
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
import ast, csv, hashlib, json, math, statistics, struct, zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'agent-reviews'
RUNS=['hainan-frozen-training-20261031','hainan-skill-follow-20261031']
receipt={}
def text(p,scope):
    b=(ROOT/p).read_bytes()
    receipt[p]={'artifact_path':p,'sha256':hashlib.sha256(b).hexdigest(),'lines':len(b.splitlines()),'coverage':scope}
    return b.decode('utf-8-sig')
def js(p,scope='full JSON parsed; all values relevant to stated checks traversed'):
    return json.loads(text(p,scope))
def table(p):
    return list(csv.DictReader(text(p,'all CSV records and fields parsed and checked').splitlines()))
def features(p):
    b=(ROOT/p).read_bytes()
    receipt[p]={'artifact_path':p,'sha256':hashlib.sha256(b).hexdigest(),'lines':None,'coverage':'ZIP/NPY header plus all numeric float32 values and boolean masks decoded with stdlib; no pickle/native code'}
    with zipfile.ZipFile(ROOT/p) as z:
        members={name:z.read(name) for name in z.namelist()}
    def unpack(b):
        assert b[:6]==b'\x93NUMPY'
        w=2 if b[6]==1 else 4
        n=int.from_bytes(b[8:8+w],'little')
        h=ast.literal_eval(b[8+w:8+w+n].decode())
        assert h['descr'] in ['<f4','|b1'] and not h['fortran_order']
        payload=b[8+w+n:]
        count=math.prod(h['shape'])
        code='f' if h['descr']=='<f4' else '?'
        vals=struct.unpack('<'+code*count,payload)
        return h,vals
    h,x=unpack(members['features.npy']);hm,mask=unpack(members['parse_mask.npy'])
    assert all(mask) and all(map(math.isfinite,x))
    receipt[p]['shape']=h['shape'];receipt[p]['parse_mask_rows']=len(mask)
    return x,h['shape']

for name in ['START_HERE.md','rules/CURRENT_RULES.md','rules/current-policy.json','comparison.md','scoring/validation-report.md']:
    text(name,'full prose/current boundary read')
source=js('source-map.json','all 440 entries parsed for source disposition; selected excluded trace/private/acceptance identities reviewed')
scores=js('scoring/scores.json')
js('scoring/scoring-identity.json')
js('scoring/independent-controller-check.json')
js('evidence/coverage.json')
man=js('manifest.json','full manifest parsed; fixed packet SHA and file identities checked')
assert hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest()=='dbdec244caa8ddb106721877cf93625c1957b9184985c07b1cf751eed5d70505'
data={s:table('data/'+s+'.csv') for s in ['train','valid','test']}
assert 'Y' in data['train'][0] and all('Y' not in data[s][0] for s in ['valid','test'])
train_y=[float(x['Y']) for x in data['train']]
predictions={};zmax={};report={'runs':{},'cross_run':{},'scoring_comparison':{}}
for run in RUNS:
    base='runs/'+run+'/'
    p=table(base+'artifacts/predictions.csv');predictions[run]=p
    ep=table(base+'learning-curve.csv')
    evidence=js(base+'artifacts/training-evidence.json')
    arrays=js(base+'preprocessing-readable.json')['arrays']
    js(base+'binary-structure.json');js(base+'source/config.json');js(base+'audit-summary.json')
    text(base+'source/train_remote_v3.py','full source read; analysis emphasis lines57-119 for transform, train/eval loss, early stop, reload')
    text(base+'historical-acceptance.md','full historical acceptance read; F1 and run validity/record limitations checked')
    mu=arrays['feature_mean']['values'];sd=arrays['feature_std']['values']
    tr=arrays['train_row_indices']['values'];va=arrays['internal_validation_row_indices']['values']
    assert len(p)==273 and len({(x['task'],x['split'],x['row_index']) for x in p})==273
    stat={};zmax[run]={}
    for split in ['train','valid','test']:
        x,shape=features(base+f'artifacts/features-{split}.npz')
        assert shape==(len(data[split]),2048)
        zm=[max(abs((x[i*2048+j]-mu[j])/sd[j]) for j in range(2048)) for i in range(shape[0])]
        zmax[run][split]=zm
        summary={'n':shape[0],'max_abs_standardized_input':max(zm),'max_row':zm.index(max(zm)),'row_counts':{'>10':sum(v>10 for v in zm),'>100':sum(v>100 for v in zm)}}
        if split=='train':
            for label,indices in [('fit',tr),('internal_stop',va)]:
                v=[zm[i] for i in indices]
                summary[label]={'n':len(v),'max_z':max(v),'median_row_max_z':statistics.median(v),'rows_z_gt_100':sum(t>100 for t in v)}
        else:
            sp=[t for t in p if t['split']==split]
            assert len(sp)==len(data[split])
            for i,(pred,inp) in enumerate(zip(sp,data[split])):
                assert pred['task']=='caco2_wang' and pred['row_index']==str(i) and all(pred[k]==inp[k] for k in ['Drug','Drug_ID'])
            vals=[float(t['y_pred']) for t in sp];assert all(map(math.isfinite,vals))
            with localcontext() as ctx:
                ctx.prec=50
                mean=sum(Decimal(t['y_pred']) for t in sp)/Decimal(len(sp))
            groups=defaultdict(list)
            for t in sp:groups[t['Drug']].append(t['y_pred'])
            summary['predictions']={'mean_decimal':str(mean),'population_std':statistics.pstdev(vals),'minimum':min(vals),'maximum':max(vals),'unique_values':len(set(vals)),'outside_train_Y_range':sum(v<min(train_y) or v>max(train_y) for v in vals),'duplicate_smiles_consistent_predictions':all(len(set(v))==1 for v in groups.values())}
        stat[split]=summary
    best=min(ep,key=lambda x:float(x['internal_validation_standardized_mse']))
    report['runs'][run]={'rows':len(p),'optimizer_steps':evidence['optimizer_steps'],'best_epoch_1_based':int(best['epoch']),'distribution':stat,'curve':{'best_internal_standardized_mse':float(best['internal_validation_standardized_mse']),'last_internal_standardized_mse':float(ep[-1]['internal_validation_standardized_mse']),'last_training_online_dropout_mse':float(ep[-1]['train_standardized_mse']),'epochs':len(ep)}}

for split in ['valid','test']:
    a=[float(x['y_pred']) for x in predictions[RUNS[0]] if x['split']==split]
    b=[float(x['y_pred']) for x in predictions[RUNS[1]] if x['split']==split]
    delta=[abs(v-u) for u,v in zip(a,b)]
    mz=[max(u,v) for u,v in zip(zmax[RUNS[0]][split],zmax[RUNS[1]][split])]
    ii=sorted(range(len(a)),key=lambda i:delta[i],reverse=True)[:5]
    highest_z=max(range(len(mz)),key=mz.__getitem__)
    def row(i):return {'row_index':i,'prediction_A':a[i],'prediction_B':b[i],'abs_prediction_difference':delta[i],'maximum_input_z_across_runs':mz[i]}
    report['cross_run'][split]={'n':len(a),'prediction_correlation':statistics.correlation(a,b),'mean_abs_prediction_difference':statistics.fmean(delta),'max_abs_prediction_difference':max(delta),'largest_prediction_differences':[row(i) for i in ii],'highest_z_row':row(highest_z),'note':'These are prediction differences, not residuals, errors, confidence or quality.'}

sa,sb=scores['scores']
report['scoring_comparison']={'source':'scoring/scores.json published aggregates only','MAE_B_minus_A':float(Decimal(str(sb['value']))-Decimal(str(sa['value']))),'RMSE_B_minus_A':sb['diagnostic_aggregates']['rmse']-sa['diagnostic_aggregates']['rmse'],'bin_sum_A':sum(sa['diagnostic_aggregates']['absolute_error_bin_counts'].values()),'bin_sum_B':sum(sb['diagnostic_aggregates']['absolute_error_bin_counts'].values()),'no_new_scoring':True}
report['not_assessed']=['Any individual valid/test residual','Molecular error slices','Prediction calibration/slope against truth','Paired loss uncertainty','New ensemble performance','Internal training/stop residuals, absent predictions','Causal attribution to high-z inputs']
js('agent-reviews/feature-byte-audit.json','cross-review implementation route numeric conclusions against independent full NPZ computation')
(OUT/'failure-predictions-calculations.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'failure-predictions-read-receipt.json').write_text(json.dumps({'packet_commit':'eaec280cf142839597fe75ce748cd2b9a8a897d4','files':list(receipt.values())},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
