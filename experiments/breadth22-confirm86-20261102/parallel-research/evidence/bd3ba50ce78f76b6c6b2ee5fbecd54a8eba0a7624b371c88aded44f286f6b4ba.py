"""The fixed 22 scientific fits in this task; no scheduling or retry decisions."""
import csv,datetime,hashlib,json,math,os,sys,time,traceback
from pathlib import Path
import numpy as np
import torch
from admet_breadth.pipeline import TaskPipeline
from admet_breadth.cache_provenance import CacheTrust
from admet_breadth.cache import FeatureScaler,TargetScaler,legacy_denominator
from admet_breadth.common import write_json,sha256_file,array_digest
from admet_breadth.encoder import CheMeleonEmbedder
from admet_breadth.heads import build_head,save_head,load_head,forward_logits,postprocess
from admet_breadth.metrics import average_precision,auroc,spearman

R=Path('task-storage://admet/breadth22-confirm86-20261102/six22-001')
TASK=json.loads((R/'input/TASK.json').read_text())
CACHE=Path(TASK['raw_cache']['preferred_existing_remote_readonly'])
torch.set_num_threads(2);torch.set_num_interop_threads(2)
torch.use_deterministic_algorithms(True)
torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
assert np.__version__=='1.26.4' and torch.__version__=='2.6.0+cu124'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def atom_torch(path,obj):
 path=Path(path);path.parent.mkdir(exist_ok=True,parents=True)
 temp=path.with_suffix(path.suffix+'.tmp');torch.save(obj,temp)
 with open(temp,'rb') as f:os.fsync(f.fileno())
 os.replace(temp,path)
def frozen_record(enc):
 enc.assert_frozen()
 return {'digest':enc.state_digest(),'training':enc.model.training,
  'parameters':{k:{'requires_grad':p.requires_grad,'grad_is_none':p.grad is None,**array_digest(p.detach().cpu().numpy())} for k,p in enc.model.named_parameters()},
  'buffers':{k:array_digest(v.detach().cpu().numpy()) for k,v in enc.model.named_buffers()},
  'checkpoint':enc.checkpoint_meta,'encoding_calls':enc.encoding_calls,'encoded_smiles_count':enc.encoded_smiles_count}
trust=CacheTrust(R/'input/INPUT_MANIFEST.json',TASK['raw_cache']['trusted_manifest_sha256'],prefix=TASK['raw_cache']['manifest_prefix'])
# Loading this CPU-only frozen asset does not invoke embed or cold encoding.
enc=CheMeleonEmbedder(Path('task-storage://admet/scaler-six28-20261102/input/assets/chemeleon_mp.pt'),device='cpu')
frozen_start=frozen_record(enc);write_json(R/'raw/encoder-start.json',frozen_start)
assert torch.cuda.is_available() and torch.cuda.device_count()==1
torch.cuda.set_per_process_memory_fraction(4096/(torch.cuda.get_device_properties(0).total_memory/1024**2),0)
probe=torch.arange(64,dtype=torch.float32,device='cuda').reshape(8,8)
assert float((probe@torch.eye(8,device='cuda')).sum())==2016
torch.cuda.synchronize();del probe
write_json(R/'raw/cuda.json',{'torch':torch.__version__,'CUDA':torch.version.cuda,'device':torch.cuda.get_device_name(0),'visible':os.environ['CUDA_VISIBLE_DEVICES'],'matmul_check':True,'deterministic':torch.are_deterministic_algorithms_enabled(),'CUBLAS_WORKSPACE_CONFIG':os.environ.get('CUBLAS_WORKSPACE_CONFIG'),'at':now()})
def same(a,b):
 if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(same(v,b[k]) for k,v in a.items())
 if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 return a==b
completed=[]
try:
 for entry in TASK['runs']:
  run=R/entry['run_id'];assert not run.exists(),str(run)
  art=run/'artifacts';raw=run/'raw';source=run/'source'
  for d in [art,raw,source]:d.mkdir(parents=True,exist_ok=False)
  cfgpath=R/'input/configs'/Path(entry['config']).name
  assert sha256_file(cfgpath)==entry['config_sha256']
  cfg=json.loads(cfgpath.read_text());(source/'config.json').write_bytes(cfgpath.read_bytes())
  pipe=TaskPipeline(entry['task'],Path('task-storage://admet/scaler-six28-20261102/input/data'),run,R/'input/task-metrics.json',allow_migrated_legacy_cache=True,cache_trust=trust,raw_cache_root=CACHE)
  counts=pipe.load();assert all(pipe.source_sha[v['split']]==v['sha256'] for v in TASK['inputs'] if v['task']==entry['task']);rec=pipe.make_internal_split(seed=cfg['split']['seed'],stop_fraction=cfg['split']['stop_fraction'])
  pipe.configure(cfg);summary=pipe.fit_transforms()
  # Independent float32 recomputation explicitly checks the two-step floor.
  X,mask=pipe.load_cache('train');A=np.asarray(X[rec['fit_row_indices']],dtype=np.float32)
  mu=A.mean(axis=0);sd=A.std(axis=0);d0=np.where(sd<1e-8,np.float32(1),sd).astype(np.float32)
  floor=cfg.get('feature_scaler',{}).get('denominator_floor')
  denom=d0 if floor is None else np.maximum(d0,np.float32(floor))
  assert np.array_equal(mu,pipe.scaler.mean) and np.array_equal(denom,pipe.scaler.std)
  if floor is not None:assert np.array_equal(d0,pipe.scaler.denominators_pre_floor)
  if pipe.target_scaler:
   fit_y=np.array([float(pipe.rows['train'][i]['Y']) for i in rec['fit_row_indices']],dtype=np.float64)
   assert pipe.target_scaler.mean==float(fit_y.mean()) and pipe.target_scaler.std==(float(fit_y.std()) or 1.)
  write_json(art/'internal-split.json',rec)
  write_json(art/'preprocessing.json',{'feature_scaler':pipe.scaler.to_dict(),'target_scaler':None if pipe.target_scaler is None else pipe.target_scaler.to_dict(),'summary':summary,'independent_fit_recomputation_exact':True,'floor_after_legacy_replacement':True})
  before=frozen_record(enc);write_json(art/'encoder-before.json',before)
  def checkpoint(state):
   atom_torch(art/'progress.pt',state)
   write_json(raw/'progress.json',{'at':now(),'epoch':len(state['history']),'steps':state['steps'],'best_epoch':state['best_epoch'],'best_value':state['best_value']})
   with open(raw/'epochs.jsonl','a') as f:f.write(json.dumps(state['history'][-1],allow_nan=False)+'\n')
  write_json(raw/'learning-started.json',{'at':now(),'run_id':entry['run_id'],'device':'cuda:0','pid':os.getpid(),'config_sha256':entry['config_sha256']})
  model,result=pipe.fit_head(cfg,'cuda',preparation=False,checkpoint_callback=checkpoint)
  atom_torch(art/'training-state-last.pt',result)
  last_steps=result['progress']['cumulative_steps'];best_steps=result['history'][result['best_epoch']-1]['steps']
  scaler=pipe.scaler.to_dict();target=None if pipe.target_scaler is None else pipe.target_scaler.to_dict()
  saves={}
  for which,state,progress in [('initial',result['initial_state_dict'],{'epochs_completed':0,'cumulative_steps':0}),('best',result['best_state_dict'],{'epochs_completed':result['best_epoch'],'cumulative_steps':best_steps}),('last',result['last_state_dict'],result['progress'])]:
   sm=build_head(2048,256,.1,cfg['head']['seed']);sm.load_state_dict(state)
   saves[which]=save_head(art/f'head-{which}.pt',task=entry['task'],kind=cfg['kind'],model=sm,scaler_dict=scaler,target_scaler_dict=target,train_config=cfg['head'],optimizer_state=result['optimizer_state'] if which=='last' else None,rng_state=result['rng_state'] if which=='last' else None,progress=progress)
  last_loaded=torch.load(art/'head-last.pt',map_location='cpu',weights_only=True)
  assert same(last_loaded['state_dict'],result['last_state_dict']) and same(last_loaded['optimizer_state'],result['optimizer_state']) and same(last_loaded['rng_state'],result['rng_state'])
  assert last_loaded['progress']==result['progress']
  del last_loaded
  cpu,ck,cs,ct=load_head(art/'head-best.pt','cpu')
  assert cs.to_dict()==scaler and (None if ct is None else ct.to_dict())==target
  assert all(torch.equal(ck['state_dict'][k],v) for k,v in result['best_state_dict'].items())
  assert any(not torch.equal(result['initial_state_dict'][k],v) for k,v in result['best_state_dict'].items())
  assert sum(p.numel() for p in model.parameters())==524801
  reload_checks={};pred_summary={};blind=[];fitset=set(rec['fit_row_indices'])
  fields=['task','split','row_index','Drug_ID','Drug','Y','y_pred','parsed','internal_partition']
  def export(path,records):
   with open(path,'w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(records)
  for split in ['train','valid','test']:
   predictions=pipe.predict_split(model,split,'cuda');XX,ok=pipe.load_cache(split)
   independent=postprocess(cfg['kind'],forward_logits(cpu,cs.apply(XX),'cpu'),ct)
   yy=np.array([x['y_pred'] for x in predictions]);std=1 if ct is None else ct.std
   rtol=3e-5;atol=3e-5*(1+std)
   assert np.allclose(yy,independent,rtol=rtol,atol=atol),(entry['run_id'],split,float(np.abs(yy-independent).max()))
   records=[]
   for i,(inputrow,pred) in enumerate(zip(pipe.rows[split],predictions)):
    assert pred['row_index']==i and math.isfinite(pred['y_pred'])
    if cfg['kind']=='classification':assert 0<=pred['y_pred']<=1
    records.append({**pred,'Drug_ID':inputrow['Drug_ID'],'Drug':inputrow['Drug'],'Y':inputrow.get('Y',''),'parsed':bool(ok[i]),'internal_partition':('fit' if i in fitset else 'stop') if split=='train' else ''})
   assert len(records)==counts[split]
   export(art/f'predictions-{split}.csv',records)
   if split!='train':blind.extend(records)
   reload_checks[split]={'rows':len(records),'max_abs_difference':float(np.abs(yy-independent).max()),'rtol':rtol,'atol':atol,'independent_CPU_best':True}
   pred_summary[split]={'rows':len(records),'sha256':sha256_file(art/f'predictions-{split}.csv'),'parse_false_rows':np.nonzero(~ok)[0].tolist()}
  export(art/'predictions.csv',blind)
  after=frozen_record(enc);assert before==after;write_json(art/'encoder-after.json',after)
  assert enc.encoding_calls==enc.encoded_smiles_count==0
  assert sha256_file(Path('task-storage://admet/scaler-six28-20261102/input/assets/chemeleon_mp.pt'))==TASK['backbone']['sha256']
  for epoch in result['history']:
   batches=[v for v in result['batch_evidence'] if v['epoch']==epoch['epoch']]
   assert abs(sum(v['loss']*v['rows'] for v in batches)/sum(v['rows'] for v in batches)-epoch['train_loss'])<1e-12
  evidence={'run_id':entry['run_id'],'configuration':cfg,'counts':counts,'history':result['history'],'best_epoch':result['best_epoch'],'best_steps':best_steps,'last_steps':last_steps,'nonzero_gradient_steps':result['nonzero_steps'],'maximum_gradient_l1':result['maximum_gradient_l1'],'parameter_count':524801,'encoder_parameters_buffers_unchanged':True,'encoder_in_optimizer':False,'encoding_calls':0,'raw_cache_root':str(CACHE),'cache_trust_sha256':trust.manifest_sha256,'migration_evidence':pipe.migration_evidence,'CPU_best_reload':reload_checks,'prediction_summary':pred_summary,'save_summaries':saves,'stop_reason':'patience8' if result['stopped_at_epoch'] else 'max_epochs50','weighted_train_loss_recomputed':True,'at':now()}
  write_json(art/'training-evidence.json',evidence)
  write_json(raw/'train-complete.json',{'at':now(),'run_id':entry['run_id'],'epochs':len(result['history']),'steps':last_steps,'best_epoch':result['best_epoch'],'best_steps':best_steps,'full_predictions':pred_summary,'CPU_reload_verified':True,'frozen':True})
  completed.append(entry['run_id']);write_json(R/'raw/study-progress.json',{'at':now(),'completed':completed,'count':len(completed)})
  print(json.dumps({'completed':len(completed),'run_id':entry['run_id'],'steps':last_steps}),flush=True)
  del model,cpu,sm,result,X,A,XX;torch.cuda.empty_cache()
 write_json(R/'raw/encoder-end.json',frozen_record(enc))
 assert frozen_record(enc)==frozen_start
 import resource
 write_json(R/'raw/study-complete.json',{'at':now(),'completed':completed,'count':22,'cold_encoding_calls':0,'expected_prediction_rows':TASK['expected_prediction_rows'],'worker_peak_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'CUDA_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'CUDA_peak_reserved_bytes':torch.cuda.max_memory_reserved()})
except BaseException:
 write_json(R/'raw/science-error.json',{'at':now(),'completed':completed,'traceback':traceback.format_exc()})
 raise
