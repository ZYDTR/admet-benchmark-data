"""One-off root review of returned research against existing aggregate evidence.
No returned code is imported; no labels, models, remote calls, or learning.
"""
import json, hashlib, math, statistics, copy
from pathlib import Path
from datetime import datetime, timezone

A = Path(__file__).resolve().parent
N = A.parent.parent
R = N.parent.parent
B = N / 'gateway/pro-breadth-001/recovery-001/execution/originals/extracted'
D = N / 'retrieval/batch24-001/candidate'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name, passed, detail=None):
    checks.append(dict(name=name, passed=bool(passed), detail=detail))
def close(a,b): return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
scores=read(D/'current/scores.json')['scores']
byrun={a['run_id']:a for a in scores}
copied=read(B/'evidence/scores24-transcription.json')['rows']
fields=['task','config_tag','seed','metric','direction','n','missing','status','value']
check('24 score transcriptions match accepted source',len(copied)==24 and all(all(a[k]==byrun[a['run_id']][k] for k in fields) for a in copied))
mini=read(R/'cycles/agent-led-resume-20261102/retrieval/final-six-candidate-001/candidate/prior-history/prior-history/history/archive-20261101/originals/S-764562710384d47e.json')['tasks']
mc=read(B/'evidence/mini22-transcription.json')
check('22 historical aggregate scores and class counts match original',len(mc)==22 and all(all(a[k]==mini[a['task']].get('n' if k=='n_valid' else k) for k in ['metric','n_valid','value','direction','kind','n_positive','n_negative']) for a in mc))
recomputed=[]
for t in sorted({s['task'] for s in scores}):
    sub=[s for s in scores if s['task']==t]; h0=[next(s['value'] for s in sub if s['config_tag']=='H0' and s['seed']==k) for k in [44,45]];h1=[next(s['value'] for s in sub if s['config_tag']=='H1' and s['seed']==k) for k in [44,45]]
    ds=[y-x for x,y in zip(h0,h1)];sign=-1 if sub[0]['direction']=='minimize' else 1
    values=dict(H0_mean=statistics.mean(h0),H1_mean=statistics.mean(h1),H0_sample_sd=statistics.stdev(h0),H1_sample_sd=statistics.stdev(h1),H1_minus_H0_seed44=ds[0],H1_minus_H0_seed45=ds[1],mean_paired_delta=statistics.mean(ds),sample_sd_paired_delta=statistics.stdev(ds),H1_improved_seeds=sum(v*sign>0 for v in ds),H0_improved_seeds=sum(v*sign<0 for v in ds),Mini22=mini[t]['value'],H0_mean_minus_Mini22=statistics.mean(h0)-mini[t]['value'],H1_mean_minus_Mini22=statistics.mean(h1)-mini[t]['value'])
    got=next(x for x in read(B/'checks/scores24-recomputed.json') if x['task']==t)
    check(t+' independent means/SD/paired deltas',all(close(v,got[k]) for k,v in values.items()))
    recomputed.append(dict(task=t,**values))
check('current valid counts',sum(s['n'] for s in scores)==27740 and sum(s['n'] for s in scores if s['config_tag']=='H0' and s['seed']==44)==6935)
cfgs={}
for a in read(B/'checks/configs24-byte-check.json'):
    src=D/'evidence/objects'/a['uri'].rsplit('/',1)[1];p=B/a['local_path']
    check('consumed configuration '+a['run_id'],p.read_bytes()==src.read_bytes() and sha(src)==a['source_version']['sha256'])
    c=read(p);cfgs[(c['task'],c['head']['dropout'],c['head']['seed'])]=c
diag=read(N/'controller/retrieval-score-intake-001/feature-distribution-diagnostic.json')['runs']
for a in read(B/'evidence/feature-summary-transcription.json')['rows']:
    s=next(x for x in diag if x['task']==a['task']);pp=s['partitions']
    expected={'used_sd_min':s['fit_std_min'],'used_sd_lt1e5':s['fit_std_below1e-5_count'],'used_sd_lt1e3':s['fit_std_below1e-3_count'],'fit_z_max':pp['train']['internal_row_max_quantiles']['fit']['1.0'],'stop_z_max':pp['train']['internal_row_max_quantiles']['stop']['1.0']}
    for split in ['train','valid','test']:expected[split+'_n']=pp[split]['rows']
    for split in ['valid','test']:
        expected[split+'_z_max']=pp[split]['absolute_standardized_feature_max']
        for lim in [100,1000]:expected[f'{split}_rows_gt{lim}']=pp[split][f'rows_with_any_abs_z_above{lim}']
    expected.update(valid_rowmax_median=pp['valid']['row_max_quantiles']['0.5'],valid_rowmax_p99=pp['valid']['row_max_quantiles']['0.99'])
    check(a['task']+' no-label feature transcription',all(close(v,a[k]) for k,v in expected.items()))
proposals=read(B/'next_experiments.json'); matrix=read(B/'matrix-expanded.json');scenarios=read(B/'budget-scenarios.json')
ids={x['fit_id'] for x in matrix};pids={x['proposal_id'] for x in proposals};unique=set();selected=[]
medium=set(next(x['fit_ids'] for x in scenarios if x['scenario_id']=='medium'))
for a in matrix:
    c=read(B/a['config_path']);p=next(x for x in proposals if x['proposal_id']==a['proposal_id'])
    expected=copy.deepcopy(p['exact_config']);expected['run_id']=c['run_id'];expected['head']['seed']=a['seed']
    check(a['fit_id']+' seed expansion',c==expected and a['seed'] in p['seeds'] and c['task']==a['task'])
    cc=copy.deepcopy(c);cc.pop('run_id');identity=json.dumps(cc,sort_keys=True);check(a['fit_id']+' unique scientific config/seed',identity not in unique);unique.add(identity)
    check(a['fit_id']+' metric mapping',(c['monitor_metric'],c['monitor_direction'],c['kind'])==tuple(mini[c['task']][k] for k in ['metric','direction','kind']))
    if a['fit_id'] in medium:
        baseline=copy.deepcopy(cfgs[(c['task'],0.1,44)]); baseline['run_id']=c['run_id'];baseline['head']['seed']=c['head']['seed']
        actual=copy.deepcopy(c);scaler=actual.pop('feature_scaler',None)
        check(a['fit_id']+' H0 one-factor equivalence',actual==baseline)
        if a['variant']=='H0':check(a['fit_id']+' legacy unchanged',scaler is None and a['seed']==46)
        else:check(a['fit_id']+' floor semantics',scaler['denominator_floor']==({'F001':.001,'F010':.01}[a['variant']]) and scaler['legacy_epsilon']==1e-8 and scaler['legacy_low_std_replacement']==1 and scaler['ddof']==0 and scaler['fit_statistic_dtype']=='float32' and scaler['transform_dtype']=='float32' and scaler['fit_scope']=='internal_fit_only')
        selected.append(a)
check('44 proposals and 88 unique expanded fits',len(proposals)==len(pids)==44 and len(matrix)==len(ids)==len(unique)==88)
sets={s['scenario_id']:set(s['fit_ids']) for s in scenarios}
check('8/28/88 nested budgets',all(len(sets[k])==v for k,v in [('light',8),('medium',28),('large',88)]) and sets['light']<sets['medium']<sets['large'] and sets['large']==ids)
check('28 fit design exact',len(selected)==28 and sum(a['seed']==46 for a in selected)==4 and sum(a['variant']=='H0' for a in selected)==2 and len({a['task'] for a in selected})==6)
source=read(N/'gateway/pro-breadth-001/values.fixed-input-commit.json')['reading_contract']['requirements']; receipts=read(B/'evidence/all-read-receipts.json');rr={x['entry_id']:x for x in receipts}
check('38 required source receipt identities',len(source)==38 and all(x['entry_id'] in rr and x['uri']==rr[x['entry_id']]['uri'] and x['source_version']==rr[x['entry_id']]['source_version'] for x in source),'Receipt identity is not independent proof of reading; numeric/code claims separately checked above.')
directions={x['direction_id'] for x in read(B/'search_space.json')};gates={x['gate_id'] for x in read(B/'preparation_tasks.json')};issues={x['issue_id'] for x in read(B/'issues.json')}
check('proposal references resolve',all(set(x['direction_ids'])<=directions and set(x['dependencies'])<=gates for x in proposals))
check('direction issue references resolve',all(set(x['linked_issues'])<=issues for x in read(B/'search_space.json')))
check('full task strategy coverage',set(x['task'] for x in read(B/'task-strategy22.json'))==set(mini))
result=dict(at=datetime.now(timezone.utc).isoformat(),passed=all(x['passed'] for x in checks),checks=checks,statistics=recomputed,selected_medium=selected,private_labels_read=False,returned_code_executed=False,training=False,corrections=['analysis prose says20 directions; structured output has21','implementation-spec names heads SHA as scaler_and_head; scaler actually in cache.py SHA c0bc8c...; dispatch binds actual module source map','Pro proposal-only permission wording does not override already authorized private dependencies and lightweight no-update prep'],unverified=['causality of extreme features','full raw-cache float64 recomputation and row-wise blind feature/prediction association','all scientific claims for reserve/new asset directions','actual preparation implementation and real new training'])
(A/'scientific-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(passed=result['passed'],checks=len(checks),failures=[x for x in checks if not x['passed']],selected=len(selected)),ensure_ascii=False))
