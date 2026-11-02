"""Root's one-off production checks: synthetic labels only, zero learning."""
import os, sys, json, shutil, copy, csv, hashlib, importlib.util
from pathlib import Path
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
PACKET = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / 'src'))
from admet_breadth import cache, migration, pipeline, heads, trainer, diagnostics
from admet_breadth.cache_provenance import CacheTrust
from admet_breadth.common import (InterfaceError, FEATURE_DIM, CHEMELEON_SHA256,
    sha256_file, row_identity_sha256, array_digest)
from admet_breadth.metrics import EarlyStopMonitor

REPORT = ROOT / 'evidence'
REPORT.mkdir(exist_ok=True)
TMP = ROOT / 'scratch'
TMP.mkdir(exist_ok=True)
results = []
def passed(name, details=None):
    results.append(dict(name=name, passed=True, details=details))
def refuse(name, fn, reason):
    try: fn()
    except InterfaceError as e:
        assert reason in str(e), (name, str(e), reason)
        passed(name, str(e)); return
    raise AssertionError(name+' unexpectedly accepted')
def no_updates(*args, **kwargs): raise AssertionError('parameter update forbidden')
torch.Tensor.backward = no_updates
torch.autograd.backward = no_updates
torch.optim.AdamW.step = no_updates
torch.set_num_threads(2)

# Independent two-row cache fixture, with trust fixed BEFORE mutations.
fixture = TMP/'cache-fixture'
(fixture/'ames').mkdir(parents=True, exist_ok=True)
X = np.zeros((2,FEATURE_DIM),np.float32); X[:,0]=[1,2]
mask=np.array([True,True]); rows=[{'Drug_ID':'a','Drug':'C'}, {'Drug_ID':'b','Drug':'CC'}]
src='a'*64
arr,mp,meta = cache.cache_paths(fixture,'ames','train')
np.save(arr,X); np.save(mp,mask)
m={'contract':{'version':1,'task':'ames','split':'train','n_rows':2,
    'feature_dim':FEATURE_DIM,'fill_value':0.0,'source_csv_sha256':src,
    'row_identity_sha256':row_identity_sha256(rows),'encoder_checkpoint_sha256':CHEMELEON_SHA256,
    'implementation_sha256':cache.current_environment()['implementation_sha256'],'packages':{}},
    'files':{'arr':sha256_file(arr),'mask':sha256_file(mp)},
    'identity':{'features':array_digest(X),'parse_mask':array_digest(mask),
                'parsed_true_count':2,'unparsed_row_indices':[]}}
meta.write_text(json.dumps(m))
manifest=TMP/'fixture-manifest.json'
manifest.write_text(json.dumps({'files':[{'path':f'input/legacy/cache/chemeleon_mp/ames/{f.name}',
    'bytes':f.stat().st_size,'sha256':sha256_file(f)} for f in [arr,mp,meta]]}))
fixture_sha=sha256_file(manifest)
anchor=CacheTrust(manifest,fixture_sha)
clean={f:f.read_bytes() for f in [arr,mp,meta]}
def reset():
    for f,data in clean.items(): f.write_bytes(data)
    got,_=cache.load_raw_cache(fixture,'ames','train',rows,src,
        allow_migrated_legacy=True,cache_trust=anchor)
    assert np.array_equal(got,X)
def load_fixture():
    return cache.load_raw_cache(fixture,'ames','train',rows,src,
        allow_migrated_legacy=True,cache_trust=anchor)
reset();passed('clean fixture really loads before negative cases')
for change in ['changed_value','row_swap','float64_dtype','short_shape','mask_change','asset_change','encoder_change','forged_v2']:
    reset(); mm=copy.deepcopy(m);a=X.copy();mask2=mask.copy()
    if change=='changed_value':a[0,0]=9
    elif change=='row_swap':a=a[::-1].copy()
    elif change=='float64_dtype':a=a.astype(np.float64)
    elif change=='short_shape':a=a[:1]
    elif change=='mask_change':mask2[0]=False;a[0,:]=0
    elif change=='asset_change':mm['contract']['encoder_checkpoint_sha256']='0'*64
    elif change=='encoder_change':mm['contract']['implementation_sha256']['encoder.py']='0'*64
    else:mm['contract']=cache.representation_contract('ames','train',src,rows)
    np.save(arr,a);np.save(mp,mask2)
    mm['files']={'arr':sha256_file(arr),'mask':sha256_file(mp)}
    mm['identity']={'features':array_digest(a),'parse_mask':array_digest(mask2),
                    'parsed_true_count':int(mask2.sum()),'unparsed_row_indices':np.nonzero(~mask2)[0].tolist()}
    meta.write_text(json.dumps(mm))
    refuse(change+' plus self-consistent metadata',load_fixture,'trusted cache digest mismatch')
reset()
refuse('missing independent trust',lambda:cache.load_raw_cache(fixture,'ames','train',rows,src,allow_migrated_legacy=True),'controller-anchored')
refuse('wrong ordered row identity',lambda:cache.load_raw_cache(fixture,'ames','train',rows[::-1],src,allow_migrated_legacy=True,cache_trust=anchor),'row_identity')
refuse('wrong source digest',lambda:cache.load_raw_cache(fixture,'ames','train',rows,'b'*64,allow_migrated_legacy=True,cache_trust=anchor),'source_csv_sha256')
manifest.write_text(manifest.read_text()+' ')
refuse('changed manifest cannot supply its own trust',lambda:CacheTrust(manifest,fixture_sha),'trusted manifest digest mismatch')

# Diagnostic oracles chosen independently from production implementation.
assert diagnostics.spearman([2,2,2],[1,2,3]) is None
assert abs(diagnostics.spearman([1,1,2],[1,2,3])-np.sqrt(.75))<1e-14
assert diagnostics.raw_statistics(np.array([[4,1],[4,3]],np.float32))['exact_constant_dimensions']==1
passed('diagnostic average ties, constant undefined, raw constant count')
preds=[dict(task='ames',split='valid',row_index=str(k),Drug_ID=r['Drug_ID'],Drug=r['Drug'],y_pred=str(k),parse_ok='True') for k,r in enumerate(rows)]
assert diagnostics.checked_predictions(preds,rows,'ames','valid',mask)==[0,1]
refuse('same-length reordered predictions',lambda:diagnostics.checked_predictions(preds[::-1],rows,'ames','valid',mask),'row identity mismatch')
bad=copy.deepcopy(preds);bad[0]['Drug']='N'
refuse('wrong SMILES in prediction',lambda:diagnostics.checked_predictions(bad,rows,'ames','valid',mask),'row identity mismatch')

# Actual source comparison. Raw cache consumption is independently verified by
# the pinned controller manifest; original scientific math is imported separately.
spec=importlib.util.spec_from_file_location('baseline_math',PACKET/'input/legacy/src/admet_breadth/__init__.py',submodule_search_locations=[str(PACKET/'input/legacy/src/admet_breadth')])
old=importlib.util.module_from_spec(spec);sys.modules['baseline_math']=old;spec.loader.exec_module(old)
from baseline_math import cache as old_cache, heads as old_heads
trusted=CacheTrust(PACKET/'INPUT_MANIFEST.json','44d92d0f6e71f5f6cb35120d31e1ac09503740950d3f70d9f5f48e82122e2a88')
config_files=sorted((PACKET/'input/configs').glob('*.json'))
allcfg=[json.loads(f.read_text()) for f in config_files]
tasks=sorted({x['task'] for x in allcfg})
rawroot=PACKET/'input/legacy/cache/chemeleon_mp'
checked_partition_count=0
stored_differences={}
for task in tasks:
    pipe=pipeline.TaskPipeline(task,PACKET/'input/data',TMP/task,PACKET/'input/task-metrics.json',
        allow_migrated_legacy_cache=True,cache_trust=trusted,raw_cache_root=rawroot)
    pipe.load();pipe.make_internal_split();pipe.fit_transforms() # genuinely no configure
    Xtr,_=pipe.load_cache('train');idx=pipe.split_record['fit_row_indices']
    oscale=old_cache.fit_feature_scaler(Xtr[idx],idx)
    assert np.array_equal(pipe.scaler.mean,oscale.mean) and np.array_equal(pipe.scaler.std,oscale.std)
    stored_path=next((PACKET/'input/legacy/run-evidence').glob(f'*{task}-h0-s44-*/preprocessing.json'))
    stored=json.loads(stored_path.read_text())['feature_scaler']
    stored_differences[task]={'mean_max_abs_difference':float(np.max(np.abs(pipe.scaler.mean-np.array(stored['mean'],np.float32)))),
                             'denominator_max_abs_difference':float(np.max(np.abs(pipe.scaler.std-np.array(stored['std'],np.float32))))}
    assert np.array_equal(pipe.scaler.mean,np.array(stored['mean'],np.float32))
    assert np.array_equal(pipe.scaler.std,np.array(stored['std'],np.float32))
    for split in ['train','valid','test']:
        pipe.load_cache(split);checked_partition_count+=1
    passed(task+' old no-config transform and stored production H0 statistics',stored_differences[task])
    for cfg in [x for x in allcfg if x['task']==task]:
        pipe.configure(cfg);pipe.fit_transforms()
        original_sd=Xtr[idx].std(axis=0);denom=np.where(original_sd<1e-8,np.float32(1),original_sd)
        floor=cfg.get('feature_scaler',{}).get('denominator_floor')
        if floor is not None:denom=np.maximum(denom,np.float32(floor))
        assert np.array_equal(pipe.scaler.std,denom)
        restored=cache.FeatureScaler.from_dict(pipe.scaler.to_dict())
        assert np.array_equal(restored.apply(Xtr[:5]),pipe.scaler.apply(Xtr[:5]))
        captured={}
        def fake_train(**kw):captured.update(kw);return None,{}
        actual_train=pipeline.train_head; pipeline.train_head=fake_train
        try:pipe.fit_head(cfg,'cpu',preparation=False)
        finally:pipeline.train_head=actual_train
        assert captured['cfg']==cfg
        assert np.array_equal(captured['X_fit'],((Xtr-pipe.scaler.mean)/denom).astype(np.float32)[idx])
        si=pipe.split_record['stop_row_indices']
        labels=np.array([float(row['Y']) for row in pipe.rows['train']],np.float64)
        assert np.array_equal(captured['y_stop'],labels[si])
        expected_y=(labels.astype(np.float32)[idx] if cfg['kind']=='classification' else pipe.target_scaler.transform_f32(labels[idx]))
        assert np.array_equal(captured['y_fit'],expected_y)
        assert (captured['monitor'].metric,captured['monitor'].direction)==(cfg['monitor_metric'],cfg['monitor_direction'])
        passed(cfg['run_id']+' actual pipeline captures correct scaled fit/native-stop inputs')
    last=copy.deepcopy(cfg);last['feature_scaler']={'method':cache.FLOOR_METHOD,'denominator_floor':(.001 if floor!=.001 else .01)}
    pipe.configure(last)
    refuse(task+' changed scaler invalidates transforms',lambda:pipe._scaled(Xtr[:2]),'transforms absent')
passed('all actual raw partitions checked',checked_partition_count)

A=np.array([[4,2,8],[4,2.0004,8.04]],np.float32)
for floor in [None,.001,.01]:
    sc=cache.fit_feature_scaler(A,[0,1],None if floor is None else {'method':cache.FLOOR_METHOD,'denominator_floor':floor})
    assert sc.std[0]==1
    if floor is not None:
        bad=copy.deepcopy(sc.to_dict());bad['scaler_config_sha256']='0'*64
        refuse('saved scaler hash mismatch '+str(floor),lambda:cache.FeatureScaler.from_dict(bad),'policy/denominator mismatch')
mon=EarlyStopMonitor('MAE','minimize')
assert trainer.evaluate_stop('regression',[0,1,2],[10,12,14],mon,1,cache.TargetScaler(10,2))['value']==0
passed('single inverse to native target scale')

# Head identity and saved-floor consumption, no encoder or learning invoked.
cfg=allcfg[0]
new=heads.build_head(2048,256,.1,44);baseline=old_heads.build_head(2048,256,.1,44)
assert all(torch.equal(new.state_dict()[k],v) for k,v in baseline.state_dict().items())
F=np.zeros((3,2048),np.float32);F[:,0]=[0,.0001,.0002]
sc=cache.fit_feature_scaler(F,[0,1,2],{'method':cache.FLOOR_METHOD,'denominator_floor':.001})
save=TMP/'head-no-update.pt';heads.save_head(save,task='ames',kind='classification',model=new,
    scaler_dict=sc.to_dict(),target_scaler_dict=None,train_config=cfg['head'])
restored,_,fs,_=heads.load_head(save,'cpu')
assert np.array_equal(fs.apply(F),sc.apply(F))
assert np.array_equal(heads.forward_logits(new.eval(),sc.apply(F),'cpu'),heads.forward_logits(restored,fs.apply(F),'cpu'))
passed('same seeded head and saved-floor production forward reload')
result={'passed':True,'checks':results,'config_count':len(allcfg),'cache_partitions':checked_partition_count,
        'parameter_updates':0,'private_valid_labels':False,'encoder_loaded':False,
        'environment':{'numpy':np.__version__,'torch':torch.__version__},'stored_H0_statistics':stored_differences}
(REPORT/'repair-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'checks':len(results),'configs':len(allcfg),'updates':0}))
