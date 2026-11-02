"""Independent CPU readback of all produced models and every prediction row."""
import csv,hashlib,json,math,os,time
from pathlib import Path
import numpy as np
import torch
from admet_breadth.common import canonical_json_bytes,write_json,sha256_file
from admet_breadth.cache import load_raw_cache,FeatureScaler
from admet_breadth.cache_provenance import CacheTrust
from admet_breadth.heads import load_head,forward_logits,postprocess,build_head
from admet_breadth.data_io import load_split_table,split_train_stop_groups
R=Path('task-storage://admet/scaler-six28-20261102');t=json.loads((R/'input/TASK.json').read_text())
assert os.environ['CUDA_VISIBLE_DEVICES']==''
torch.set_num_threads(1);torch.set_num_interop_threads(1)
began=time.monotonic();trust=CacheTrust(R/'input/INPUT_MANIFEST.json',t['raw_cache']['trusted_manifest_sha256'])
cache={};tables={};reports=[];paired={};totals={'train':0,'valid':0,'test':0}
def equal(a,b):
 if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(v,b[k]) for k,v in a.items())
 if isinstance(a,(tuple,list)):return type(a)==type(b) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 return a==b
def tensor_sha(state):
 h=hashlib.sha256()
 for k,v in sorted(state.items()):h.update(k.encode());h.update(v.contiguous().numpy().tobytes())
 return h.hexdigest()
for e in t['runs']:
 run=R/e['run_id'];a=run/'artifacts';cfg=json.loads((run/'source/config.json').read_text());assert sha256_file(run/'source/config.json')==e['config_sha256']
 state=torch.load(a/'training-state-last.pt',map_location='cpu',weights_only=True)
 ck={n:torch.load(a/f'head-{n}.pt',map_location='cpu',weights_only=True) for n in ['initial','best','last']}
 assert equal(ck['initial']['state_dict'],state['initial_state_dict'])
 assert equal(ck['best']['state_dict'],state['best_state_dict']) and equal(ck['last']['state_dict'],state['last_state_dict'])
 assert equal(ck['last']['optimizer_state'],state['optimizer_state']) and equal(ck['last']['rng_state'],state['rng_state'])
 assert not equal(ck['initial']['state_dict'],ck['best']['state_dict'])
 initial=build_head(2048,256,.1,e['seed']);assert equal(initial.state_dict(),ck['initial']['state_dict'])
 assert sum(v.numel() for v in ck['best']['state_dict'].values())==524801
 assert all(bool(torch.isfinite(v).all()) for n in ck.values() for v in n['state_dict'].values())
 rows=tables.setdefault((e['task'],'train'),load_split_table(R/'input/data',e['task'],'train'))
 rec=split_train_stop_groups(rows,43,.1);assert rec==json.loads((a/'internal-split.json').read_text())
 history=state['history'];steps=state['progress']['cumulative_steps'];per_epoch=math.ceil(rec['fit_rows']/128)
 assert steps==len(history)*per_epoch==state['nonzero_steps']
 assert ck['last']['progress']==state['progress']
 assert ck['best']['progress']=={'epochs_completed':state['best_epoch'],'cumulative_steps':per_epoch*state['best_epoch']}
 assert all(float(v['step'])==steps for v in state['optimizer_state']['state'].values())
 rng=state['rng_state'];assert len(rng['numpy']['keys'])==624 and len(rng['torch_cuda'])==1 and rng['torch_cpu'].dtype==rng['sampler'].dtype==torch.uint8 and len(rng['python'])==3
 best=None;best_epoch=None;gen=torch.Generator(device='cpu').manual_seed(e['seed'])
 for index,h in enumerate(history,1):
  assert h['epoch']==index and h['steps']==index*per_epoch and math.isfinite(h['value'])
  perm=torch.randperm(rec['fit_rows'],generator=gen);assert hashlib.sha256(perm.numpy().tobytes()).hexdigest()==h['permutation_sha256']
  improved=best is None or (h['value']<best-1e-7 if cfg['monitor_direction']=='minimize' else h['value']>best+1e-7)
  assert improved==h['improved']
  if improved:best=h['value'];best_epoch=index
  assert h['best_epoch']==best_epoch and h['best_value']==best
  batches=[b for b in state['batch_evidence'] if b['epoch']==index]
  assert len(batches)==per_epoch and sum(b['rows'] for b in batches)==rec['fit_rows']
  assert all(math.isfinite(b['loss']) and math.isfinite(b['gradient_l1']) and b['gradient_l1']>0 for b in batches)
  assert abs(sum(b['rows']*b['loss'] for b in batches)/rec['fit_rows']-h['train_loss'])<1e-12
 assert best_epoch==state['best_epoch'] and best==state['best_value']
 assert len(history)==50 or len(history)-best_epoch==8
 assert torch.equal(gen.get_state(),rng['sampler'])
 model,_,scaler,target=load_head(a/'head-best.pt','cpu');scaler.assert_matches_config(cfg.get('feature_scaler'))
 pp=json.loads((a/'preprocessing.json').read_text());assert scaler.to_dict()==pp['feature_scaler'] and (None if target is None else target.to_dict())==pp['target_scaler']
 before=json.loads((a/'encoder-before.json').read_text());after=json.loads((a/'encoder-after.json').read_text());assert before==after and before['encoding_calls']==before['encoded_smiles_count']==0
 assert len(before['parameters'])==8 and len(before['buffers'])==3 and not before['training']
 assert all(not v['requires_grad'] and v['grad_is_none'] for v in before['parameters'].values())
 fitset=set(rec['fit_row_indices']);cpu_checks={};blind=[]
 for split in ['train','valid','test']:
  key=(e['task'],split)
  if key not in tables:tables[key]=load_split_table(R/'input/data',e['task'],split)
  original=tables[key]
  if key not in cache:cache[key]=load_raw_cache(Path(t['raw_cache']['preferred_existing_remote_readonly']),e['task'],split,original,sha256_file(R/'input/data'/e['task']/f'{split}.csv'),allow_migrated_legacy=True,cache_trust=trust)
  X,ok=cache[key]
  if split=='train':
   A=X[rec['fit_row_indices']];mean=A.mean(axis=0);std=A.std(axis=0);d0=np.where(std<1e-8,np.float32(1),std).astype(np.float32);floor=cfg.get('feature_scaler',{}).get('denominator_floor');d=d0 if floor is None else np.maximum(d0,np.float32(floor))
   assert np.array_equal(scaler.mean,mean) and np.array_equal(scaler.std,d)
   if floor is not None:assert np.array_equal(scaler.denominators_pre_floor,d0)
   if target:
    yy=np.array([float(original[i]['Y']) for i in rec['fit_row_indices']],dtype=np.float64);assert target.mean==float(yy.mean()) and target.std==(float(yy.std()) or 1.)
  records=list(csv.DictReader((a/f'predictions-{split}.csv').open(newline='')));assert len(records)==len(original)
  vals=[]
  for i,(row,pred) in enumerate(zip(original,records)):
   assert (pred['task'],pred['split'],int(pred['row_index']),pred['Drug_ID'],pred['Drug'])==(e['task'],split,i,row['Drug_ID'],row['Drug'])
   assert pred['Y']==row.get('Y','') and pred['parsed']==str(bool(ok[i]))
   assert pred['internal_partition']==(('fit' if i in fitset else 'stop') if split=='train' else '')
   value=float(pred['y_pred']);assert math.isfinite(value)
   if cfg['kind']=='classification':assert 0<=value<=1
   vals.append(value)
  expected=postprocess(cfg['kind'],forward_logits(model,scaler.apply(X),'cpu'),target)
  std_scale=1 if target is None else target.std;rtol=3e-5;atol=3e-5*(1+std_scale)
  assert np.allclose(vals,expected,rtol=rtol,atol=atol)
  cpu_checks[split]={'rows':len(records),'max_abs_difference':float(np.max(np.abs(np.array(vals)-expected))),'rtol':rtol,'atol':atol}
  totals[split]+=len(records)
  if split!='train':blind.extend(records)
 assert blind==list(csv.DictReader((a/'predictions.csv').open(newline='')))
 group=(e['task'],e['seed']);fingerprint={'init':tensor_sha(state['initial_state_dict']),'split':rec['split_record_sha256'],'mean':hashlib.sha256(scaler.mean.tobytes()).hexdigest(),'d0':hashlib.sha256(d0.tobytes()).hexdigest(),'permutations':[x['permutation_sha256'] for x in history]}
 if group in paired:
  base=paired[group];assert all(base[k]==fingerprint[k] for k in ['init','split','mean','d0']);n=min(len(base['permutations']),len(fingerprint['permutations']));assert base['permutations'][:n]==fingerprint['permutations'][:n]
 else:paired[group]=fingerprint
 reports.append({'run_id':e['run_id'],'epochs':len(history),'steps':steps,'best_epoch':best_epoch,'best_steps':best_epoch*per_epoch,'config_sha256':e['config_sha256'],'tensor_optimizer_full_RNG_exact':True,'scaler_actual_f32_recomputed_exact':True,'row_identity_parse_and_trainY_exact':True,'CPU_best_reload':cpu_checks,'encoder_unchanged':True})
assert totals==t['expected_prediction_rows'] and len(reports)==28 and len(cache)==18 and len(paired)==14
write_json(R/'raw/independent-CPU-verification.json',{'runs':reports,'verified_runs':28,'paired_groups':14,'cache_partitions':18,'prediction_rows':totals,'optimizer_steps':sum(x['steps'] for x in reports),'CPU_seconds':time.monotonic()-began,'CUDA_visible_devices':os.environ['CUDA_VISIBLE_DEVICES'],'training_updates':0})
print(json.dumps({'verified_runs':28,'paired_groups':14,'prediction_rows':totals,'optimizer_steps':sum(x['steps'] for x in reports),'CPU_seconds':time.monotonic()-began}),flush=True)
