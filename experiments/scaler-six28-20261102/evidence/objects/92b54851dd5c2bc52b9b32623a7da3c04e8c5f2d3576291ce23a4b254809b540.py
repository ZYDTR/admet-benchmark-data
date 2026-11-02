"""One-off no-label feature/prediction measurement for the accepted six tasks."""
import csv, json, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
PACKET=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(ROOT/'src'))
from admet_breadth.cache_provenance import CacheTrust
from admet_breadth.cache import load_raw_cache, fit_feature_scaler, FLOOR_METHOD
from admet_breadth.common import sha256_file, row_identity_sha256
from admet_breadth.data_io import load_split_table, split_train_stop_groups
from admet_breadth.diagnostics import raw_statistics, checked_predictions, association

trust=CacheTrust(PACKET/'INPUT_MANIFEST.json','44d92d0f6e71f5f6cb35120d31e1ac09503740950d3f70d9f5f48e82122e2a88')
tasks=sorted(p.name for p in (PACKET/'input/data').iterdir() if p.is_dir())
result={'scope':'no_label_feature_and_prediction_diagnostic','private_valid_truth_read':False,
        'parameter_updates':0,'numpy':np.__version__,'production_dtype_unchanged':'float32',
        'causality':'not established','tasks':{}}
def stats(z):
    a=np.abs(z).max(axis=1)
    return {'rows':len(a),'max_abs_z':float(a.max()),
            'row_max_quantiles':dict(zip(['0','0.5','0.9','0.99','1'],map(float,np.quantile(a,[0,.5,.9,.99,1])))),
            'rows_above':{str(t):int((a>t).sum()) for t in [10,100,1000]}}
for task in tasks:
    rows={s:load_split_table(PACKET/'input/data',task,s) for s in ['train','valid','test']}
    source={s:sha256_file(PACKET/'input/data'/task/(s+'.csv')) for s in rows}
    arrays={};masks={}
    for split in rows:
        arrays[split],masks[split]=load_raw_cache(PACKET/'input/legacy/cache/chemeleon_mp',task,split,
            rows[split],source[split],allow_migrated_legacy=True,cache_trust=trust)
    record=split_train_stop_groups(rows['train'],seed=43,validation_fraction=.1)
    fi=record['fit_row_indices'];si=record['stop_row_indices'];fit=arrays['train'][fi]
    old_path=next((PACKET/'input/legacy/run-evidence').glob(f'*{task}-h0-s44-*/preprocessing.json'))
    stored=json.loads(old_path.read_text())['feature_scaler']
    m32=np.array(stored['mean'],np.float32);d32=np.array(stored['std'],np.float32)
    a64=fit.astype(np.float64);m64=a64.mean(0);s64=a64.std(0);d64=np.where(s64<1e-8,1,s64)
    entry={'input_sha256':source,'split_sha256':record['split_record_sha256'],
           'stored_preprocessing_sha256':sha256_file(old_path),'raw_statistics':raw_statistics(fit),
           'float64_refit_vs_stored_production':{
               'max_abs_mean_difference':float(np.abs(m32.astype(np.float64)-m64).max()),
               'max_abs_denominator_difference':float(np.abs(d32.astype(np.float64)-d64).max()),
               'changed_mean_dimensions':int((m32!=m64).sum()),
               'changed_denominator_dimensions':int((d32!=d64).sum())},'policies':{}}
    predictions={}
    for file in sorted((PACKET/'input/legacy/run-evidence').glob(f'*{task}-*/predictions-valid.csv')):
        with file.open(encoding='utf-8-sig',newline='') as h: pred=list(csv.DictReader(h))
        predictions[file.parent.name]=checked_predictions(pred,rows['valid'],task,'valid',masks['valid'])
    assert len(predictions)==4
    for name,floor in [('H0',None),('F001',.001),('F010',.01)]:
        sc=fit_feature_scaler(fit,fi,None if floor is None else {'method':FLOOR_METHOD,'denominator_floor':floor})
        assert np.array_equal(sc.mean,m32)
        if floor is None:assert np.array_equal(sc.std,d32)
        values={'train_fit':fit,'train_stop':arrays['train'][si],
                'valid':arrays['valid'],'test':arrays['test']}
        ev={'changed_denominator_dimensions':int((sc.std!=d32).sum()),
            'partitions':{},'blind_valid_associations':{},'valid_row_identity_sha256':row_identity_sha256(rows['valid'])}
        for split,x in values.items():
            z=sc.apply(x);ev['partitions'][split]=stats(z)
            if split=='valid':
                magnitude=np.abs(z).max(axis=1)
                for run,pred in predictions.items():ev['blind_valid_associations'][run]=association(magnitude,pred)
        entry['policies'][name]=ev
    result['tasks'][task]=entry
out=ROOT/'evidence/no-label-diagnostics-corrected.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({'tasks':len(result['tasks']),'policies_per_task':3,'old_prediction_sets':24,'updates':0}))
