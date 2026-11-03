"""Fixed HOOF001 analysis; stdlib only, no model/feature loading or fitting.

Caller supplies authenticated OOF predictions in original row order.
Native Metric/group interval definitions are injected from the previously
accepted ME001 native_statistics.py when this is executed on the host.
"""
import collections, math, random, statistics


def fold_mean_interval(y, control, treatment, groups, fold_ids,
                       replicates=2000, seed=20261103):
    """Paired whole-group resampling independently within each fixed fold.

    This is conditional descriptive uncertainty, not a correction for the
    history of adaptive model choice or an independent generalization test.
    """
    assert len(y)==len(control)==len(treatment)==len(groups)==len(fold_ids)
    folds=[]
    for fold in range(5):
        idx=[i for i,f in enumerate(fold_ids) if f==fold]
        yy=[y[i] for i in idx];cc=[control[i] for i in idx];tt=[treatment[i] for i in idx]
        gm=collections.defaultdict(list)
        for local,i in enumerate(idx):gm[groups[i]].append(local)
        folds.append((Metric(yy,cc,'Spearman'),Metric(yy,tt,'Spearman'),gm,len(idx)))
    assert sum(f[3] for f in folds)==len(y)
    observed=[b()-a() if a() is not None and b() is not None else None for a,b,_,_ in folds]
    out={'metric':'unweighted_mean_of5_fold_Spearman_differences','fold_differences':observed,
         'delta':statistics.mean(observed) if all(x is not None for x in observed) else None,
         'CI95':None,'seed':seed,'replicates':replicates,'valid_replicates':0,
         'scope':'descriptive conditional whole-group bootstrap within eachfold; historical adaptation uncorrected'}
    if out['delta'] is None:return out
    rng=random.Random(seed);sample=[]
    for _ in range(replicates):
        ds=[]
        for a,b,gm,n in folds:
            keys=sorted(gm);ng=len(keys);counts=[0]*ng
            for j in range(ng):counts[rng.randrange(ng)]+=1
            weights=[0]*n
            for key,cnt in zip(keys,counts):
                for i in gm[key]:weights[i]=cnt
            av,bv=a(weights),b(weights)
            if av is None or bv is None:break
            ds.append(bv-av)
        if len(ds)==5:sample.append(statistics.mean(ds))
    out['valid_replicates']=len(sample)
    if len(sample)>=math.ceil(.95*replicates):out['CI95']=[quantile(sample,.025),quantile(sample,.975)]
    return out


def analyze_oof(bundle, scheme, predictions):
    """predictions: {mlp|local|tabicl:{44|45: [848 finite values]}}."""
    methods=['mlp','local','tabicl'];seeds=['44','45'];n=bundle['full_row_count']
    assert set(predictions)==set(methods) and n==848
    for method in methods:
        assert set(predictions[method])==set(seeds)
        for seed in seeds:
            p=predictions[method][seed]
            assert len(p)==n and all(math.isfinite(v) for v in p)
    rows=bundle['rows'];assert [r['row_index'] for r in rows]==list(range(n))
    y=[r['Y'] for r in rows];groups=[r['groups'][scheme] for r in rows]
    folds=[None]*n
    for rec in bundle['partitions'][scheme]:
        for i in rec['test']:
            assert folds[i] is None;folds[i]=rec['fold']
    assert all(f is not None for f in folds)
    assert all(len({folds[i] for i,g in enumerate(groups) if g==group})==1 for group in set(groups))
    avg={m:[(a+b)/2 for a,b in zip(predictions[m]['44'],predictions[m]['45'])] for m in methods}
    metrics={}
    for m in methods:
        fm=[]
        for fold in range(5):
            ids=[i for i in range(n) if folds[i]==fold]
            fm.append({'fold':fold,'n':len(ids),'equal_seed_prediction_metrics':summarize([y[i] for i in ids],[avg[m][i] for i in ids]),
                       'each_seed':{s:summarize([y[i] for i in ids],[predictions[m][s][i] for i in ids]) for s in seeds}})
        metrics[m]={'folds':fm,'mean_fold_equal_seed_Spearman':statistics.mean(f['equal_seed_prediction_metrics']['Spearman'] for f in fm),
                    'pooled_OOF_descriptive_only':summarize(y,avg[m]),
                    'pooled_each_seed_descriptive':{s:summarize(y,predictions[m][s]) for s in seeds}}
    contrasts=[]
    for control,treatment in [('tabicl','local'),('mlp','local'),('mlp','tabicl')]:
        co={'control':control,'treatment':treatment,
            'primary_foldwise':fold_mean_interval(y,avg[control],avg[treatment],groups,folds),
            'seedwise_fold_differences':{},'fixed_cohorts':{}}
        for s in seeds:
            ds=[]
            for f in range(5):
                ids=[i for i in range(n) if folds[i]==f]
                yy=[y[i] for i in ids]
                ds.append(Metric(yy,[predictions[treatment][s][i] for i in ids],'Spearman')()-Metric(yy,[predictions[control][s][i] for i in ids],'Spearman')())
            co['seedwise_fold_differences'][s]=ds
        for name,ids in bundle['cohorts'].items():
            yy=[y[i] for i in ids];cc=[avg[control][i] for i in ids];tt=[avg[treatment][i] for i in ids];gg=[groups[i] for i in ids]
            co['fixed_cohorts'][name]={'MAE':paired_group_interval(yy,cc,tt,gg,'MAE'),
                                     'control_descriptive':summarize(yy,cc),'treatment_descriptive':summarize(yy,tt)}
        contrasts.append(co)
    names=['better','worse','equal','material_improvement5','material_harm5','both_large50','low_disagreement10_both_large50','Tab_only_large50','local_only_large50','neither_large50']
    cohorts={k:[] for k in names};diagnostic_rows=[]
    for i in range(n):
        a,b=avg['tabicl'][i],avg['local'][i];ea,eb=abs(a-y[i]),abs(b-y[i]);d=eb-ea
        flags={'better':d<0,'worse':d>0,'equal':d==0,'material_improvement5':d<=-5,'material_harm5':d>=5,
               'both_large50':ea>=50 and eb>=50,'low_disagreement10_both_large50':ea>=50 and eb>=50 and abs(a-b)<=10,
               'Tab_only_large50':ea>=50 and eb<50,'local_only_large50':ea<50 and eb>=50,'neither_large50':ea<50 and eb<50}
        for k,v in flags.items():
            if v:cohorts[k].append(i)
        diagnostic_rows.append({'row_index':i,'fold':folds[i],'Drug_ID':rows[i]['Drug_ID'],'Drug':rows[i]['Drug'],'group':groups[i],'Y':y[i],
                                'predictions_equal_seed':{m:avg[m][i] for m in methods},'Tab_abs_error':ea,'local_abs_error':eb,
                                'local_minus_Tab_abs_error':d,'flags':[k for k,v in flags.items() if v]})
    cohort_summary={}
    for name,ids in cohorts.items():
        complement=sorted(set(range(n))-set(ids))
        cohort_summary[name]={'n':len(ids),'groups':len({groups[i] for i in ids}),'members':ids,
                              'methods':{m:summarize([y[i] for i in ids],[avg[m][i] for i in ids]) for m in methods},
                              'complement':{'n':len(complement),'methods':{m:summarize([y[i] for i in complement],[avg[m][i] for i in complement]) for m in methods}}}
    return {'scheme':scheme,'n':n,'metrics':metrics,'contrasts':contrasts,'complete_error_cohorts':cohort_summary,
            'complete_diagnostic_rows':diagnostic_rows,'new_dataset_independence':False,'blending_or_temperature_search':False}
