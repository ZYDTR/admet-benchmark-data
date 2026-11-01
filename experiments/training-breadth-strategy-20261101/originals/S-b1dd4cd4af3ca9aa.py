# Independent audit of frozen candidate, no fitting/backward/optimizer calls.
from pathlib import Path
import sys,json,hashlib,copy,traceback,subprocess,os
sys.path.insert(0,'/candidate')
import numpy as np,torch
from feature_cache import build_manifest,save_cache,load_cache
from feature_array import Array
from assets import package_versions
from encode_features import encode_table,_encoder_meta
from chemeleon_encoder import FrozenCheMeleonEncoder
from head_model import build_head,save_head,load_head,predict,TargetScaler
from train_heads import _load_features
from dataio import read_split
O=Path('/evidence'); rows=[]
torch.set_num_threads(2)
def check(name,fn,reject=False):
    try:
        detail=fn(); result=not reject
        rows.append(dict(name=name,pass_check=result,actual='accepted',detail=detail))
        return detail
    except Exception as e:
        rows.append(dict(name=name,pass_check=reject,actual='rejected',error=type(e).__name__+': '+str(e),traceback=traceback.format_exc()))
        return None
weights='/assets/chemeleon_mp.pt'
enc=FrozenCheMeleonEncoder(weights)
def state_hash(model):
    h=hashlib.sha256()
    for k,v in model.state_dict().items(): h.update(k.encode()); h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()
before=state_hash(enc.model)
raw,kept,failed=enc.encode_smiles(['C','CC'],batch_size=2)
rows.append(dict(name='real-encoder-two-molecules',pass_check=raw.shape==(2,2048) and np.isfinite(raw).all().item(),shape=list(raw.shape),frozen=all(not p.requires_grad for p in enc.model.parameters())))
pack=O/'pack'; (pack/'official/data_benchmark/ames').mkdir(parents=True,exist_ok=True)
(pack/'official/data_benchmark/ames/train.csv').write_text('Drug_ID,Drug,Y\na,C,0\nb,CC,1\n')
table=read_split(str(pack),'ames','train'); deps=package_versions(); meta=_encoder_meta(enc,enc.weight_metadata); manifest=build_manifest(table,meta,deps,2)
check('actual-encode-table-to-cache',lambda:encode_table(enc,table,str(O/'entry-cache'),deps,2))
# Wrap only independent fixture to isolate later defects; do not patch candidate.
entry=Path(save_cache(str(O/'wrapped-cache'),manifest,Array(raw),kept,failed))
check('cache-wrapped-hit',lambda:list(load_cache(str(O/'wrapped-cache'),manifest)[0].shape))
check('producer-to-consumer-manifest',lambda:_load_features(str(O/'wrapped-cache'),table,enc.feature_dim,enc.weight_metadata,deps,2))
# Independent blind-valid fixture: consumer manifest provided solely to isolate label handling.
(pack/'blind_validation/ames').mkdir(parents=True,exist_ok=True)
(pack/'blind_validation/ames/valid.csv').write_text('Drug_ID,Drug\na,C\nb,CC\n')
vtab=read_split(str(pack),'ames','valid'); vmeta=copy.deepcopy(meta); vmeta.pop('hyper_parameters')
vman=build_manifest(vtab,vmeta,deps,2)
save_cache(str(O/'valid-cache'),vman,Array(raw),kept,failed)
check('blind-valid-feature-loader',lambda:_load_features(str(O/'valid-cache'),vtab,enc.feature_dim,enc.weight_metadata,deps,2))
head,_,cfg=build_head(enc.feature_dim,'classification'); hb=state_hash(head)
check('predict-cached-array',lambda:predict(head,load_cache(str(O/'wrapped-cache'),manifest)[0],'classification').tolist())
rows.append(dict(name='training-array-astype-contract',pass_check=hasattr(load_cache(str(O/'wrapped-cache'),manifest)[0],'astype'),note='Train entrance not invoked; source requires Xtr.astype(np.float32).'))
p0=predict(head,raw,'classification'); save_head(head,str(O/'head.pt'),'ames','classification',None,cfg)
h2,payload=load_head(str(O/'head.pt'),expect_task='ames'); p1=predict(h2,raw,'classification')
rows.append(dict(name='untrained-head-save-load',pass_check=np.array_equal(p0,p1)))
check('wrong-head-task',lambda:load_head(str(O/'head.pt'),expect_task='caco2_wang'),reject=True)
scaler=TargetScaler(3.,2.); z=np.array([-1.,0.,1.]); rows.append(dict(name='regression-inverse-scale',pass_check=np.array_equal(scaler.inverse(z),np.array([1.,3.,5.]))))
for mode in ('rows','input','weights','deps'):
    t=copy.deepcopy(table); m=copy.deepcopy(meta); d=copy.deepcopy(deps)
    if mode=='rows': t['rows']=list(reversed(t['rows']))
    if mode=='input': t['sha256']='f'*64
    if mode=='weights': m['weights']['sha256']='f'*64
    if mode=='deps': d['numpy']='0.0.0'
    other=build_manifest(t,m,d,2)
    check('cache-change-'+mode,lambda x=other:load_cache(str(O/'wrapped-cache'),x),reject=True)
for mode in ('bytes','shape','dtype','nan','inf'):
    root=O/('tamper-'+mode); e=Path(save_cache(str(root),manifest,Array(raw),kept,failed)); fp=e/'features.npy'; mp=e/'manifest.json'; doc=json.loads(mp.read_text())
    if mode=='bytes':
        data=bytearray(fp.read_bytes()); data[-1]^=1; fp.write_bytes(data)
    else:
        changed=raw.copy()
        if mode=='shape': changed=changed[:1]
        if mode=='dtype': changed=changed.astype(np.float64)
        if mode=='nan': changed[0,0]=np.nan
        if mode=='inf': changed[0,0]=np.inf
        np.save(fp,changed,allow_pickle=False)
        doc['features_sha256']=hashlib.sha256(fp.read_bytes()).hexdigest(); mp.write_text(json.dumps(doc))
    check('cache-tamper-'+mode,lambda r=root:load_cache(str(r),manifest),reject=True)
check('duplicate-kept-row-indices',lambda:save_cache(str(O/'dups'),manifest,Array(np.concatenate([raw,raw[:1]])),[0,1,0],[]),reject=True)
rows.append(dict(name='encoder-and-head-parameters-unchanged',pass_check=before==state_hash(enc.model) and hb==state_hash(head)))
# Run supplied unittests with available actual deps, no train/fit entrance.
p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd='/candidate',text=True,capture_output=True,timeout=90)
(O/'model-selftests-with-deps.log').write_text(p.stdout+'\nSTDERR\n'+p.stderr)
rows.append(dict(name='supplied-tests-with-deps',pass_check=p.returncode==0,exit_code=p.returncode))
(O/'model-results.json').write_text(json.dumps(rows,indent=2,default=str))
(O/'environment.json').write_text(json.dumps(dict(deps=deps,torch=str(torch.__version__),weight_sha256=enc.weight_metadata['sha256'],training_executed=False),indent=2))
print(json.dumps(rows,indent=2,default=str))
