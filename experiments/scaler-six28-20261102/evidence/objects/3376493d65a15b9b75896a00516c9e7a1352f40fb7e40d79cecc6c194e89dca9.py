"""Root's one-off read-only evidence verification; no training, truth or returned code."""
import ast, collections, csv, hashlib, io, json, math, pickle, random, struct, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

OUT=Path(__file__).resolve().parent; C=OUT.parent.parent; O=C/'operator'; P=C/'preparation/packet'
def j(p): return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rows(p):
 with Path(p).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]

# Inert tensor descriptions only: all external globals denied except these exact data constructors.
def tensor(storage,offset,size,stride,*ignored):
 kind,data=storage; widths={'FloatStorage':4,'LongStorage':8,'ByteStorage':1}
 expected=[];n=1
 for d in reversed(size):expected.insert(0,n);n*=d
 assert tuple(stride)==tuple(expected) or n==1,(size,stride)
 b=data[offset*widths[kind]:(offset+n)*widths[kind]];assert len(b)==n*widths[kind]
 return {'_tensor':True,'kind':kind,'shape':tuple(size),'bytes':b}
class Inert(pickle.Unpickler):
 def find_class(self,module,name):
  if (module,name)==('collections','OrderedDict'):return collections.OrderedDict
  if module=='torch' and name in ('FloatStorage','ByteStorage','LongStorage'):return name
  if (module,name)==('torch._utils','_rebuild_tensor_v2'):return tensor
  raise ValueError(('disallowed external global',module,name))
 def persistent_load(self,pid):
  assert pid[0]=='storage' and len(pid)==5
  _,kind,key,device,count=pid;b=self.z.read(self.prefix+'data/'+key)
  assert len(b)==count*{'FloatStorage':4,'ByteStorage':1,'LongStorage':8}[kind]
  return kind,b
def checkpoint(p):
 with zipfile.ZipFile(p) as z:
  names=z.namelist();assert len(names)==len(set(names))
  assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
  name=next(n for n in names if n.endswith('/data.pkl'))
  u=Inert(io.BytesIO(z.read(name)));u.z=z;u.prefix=name[:-len('data.pkl')]
  return u.load()
def tensor_floats(t):
 assert t['kind']=='FloatStorage';return [x[0] for x in struct.iter_unpack('<f',t['bytes'])]
def tensor_digest(sd):return hashlib.sha256(b''.join(k.encode()+v['bytes'] for k,v in sorted(sd.items()))).hexdigest()
def mask(p):
 with p.open('rb') as f:
  assert f.read(6)==b'\x93NUMPY';v=f.read(2);n=struct.unpack('<H' if v[0]==1 else '<I',f.read(2 if v[0]==1 else 4))[0]
  header=ast.literal_eval(f.read(n).decode());b=f.read();assert header['descr']=='|b1' and not header['fortran_order'] and len(b)==header['shape'][0]
  return list(map(bool,b))

t=j(C/'TASK.json');idx=j(O/'ARTIFACT_INDEX.json');m=j(O/'evidence-manifest.json')
assert sha(O/'ARTIFACT_INDEX.json')=='faf960b8e7f8b761e211187d8bfcfd742751206c263ce47fa55d9df577f402ce'
assert sha(O/'evidence-manifest.json')=='10107bd8118a6a567733afc44a51f5924730bde611b344367249428d58284a43'
assert sha(C/'TASK.json')==m['TASK_sha256']
for rel,meta in m['files'].items():
 p=O/rel;assert not p.is_symlink() and p.resolve().is_relative_to(O.resolve())
 assert p.stat().st_size==meta['size'] and sha(p)==meta['sha256'],rel
scientific=list((C/'controller/preparation-repair-001/src/admet_breadth').glob('*.py'))
for p in scientific:assert sha(p)==sha(O/'global-evidence/src/admet_breadth'/p.name)
assert len(idx['runs'])==28 and {x['run_id'] for x in idx['runs']}=={x['run_id'] for x in t['runs']}
reference={x['run_id']:x for x in t['runs']};tables={};totals=collections.Counter();steps=0;reports=[];paired={}
global_encoder=j(O/'global-evidence/raw/encoder-start.json');assert global_encoder==j(O/'global-evidence/raw/encoder-end.json')
for e in idx['runs']:
 run=Path(e['local_snapshot']);assert run.resolve().is_relative_to((O/'snapshots').resolve())
 cfg=j(run/'source/config.json');assert sha(run/'source/config.json')==reference[e['run_id']]['config_sha256']
 for rel,meta in e['files'].items():
  if meta['downloaded']:assert sha(run/rel)==meta['sha256'] and (run/rel).stat().st_size==meta['size']
 task=e['task'];art=run/'artifacts';split=j(art/'internal-split.json');train=tables.setdefault((task,'train'),rows(P/'input/data'/task/'train.csv'))
 groups=collections.defaultdict(list)
 for i,x in enumerate(train):groups[x['Drug']].append(i)
 keys=sorted(groups);random.Random(43).shuffle(keys);stop=[]
 for k in keys[:-1]:
  if len(stop)>=max(1,round(len(train)*.1)):break
  stop.extend(groups[k])
 stop=set(stop);fit=set(range(len(train)))-stop
 assert sorted(stop)==split['stop_row_indices'] and sorted(fit)==split['fit_row_indices']
 before=j(art/'encoder-before.json');assert before==j(art/'encoder-after.json')==global_encoder
 assert len(before['parameters'])==8 and len(before['buffers'])==3 and before['training'] is False
 assert all(v['requires_grad'] is False and v['grad_is_none'] for v in before['parameters'].values())
 assert before['encoding_calls']==before['encoded_smiles_count']==0
 state=checkpoint(art/'training-state-last.pt');cks={n:checkpoint(art/f'head-{n}.pt') for n in ('initial','best','last')}
 for n,ck in cks.items():
  assert ck['state_dict']==state[n+'_state_dict']
  assert sorted(tuple(v['shape']) for v in ck['state_dict'].values())==[(1,),(1,256),(256,),(256,2048)]
  assert all(math.isfinite(x) for v in ck['state_dict'].values() for x in tensor_floats(v))
 assert cks['initial']['state_dict']!=cks['best']['state_dict']
 assert cks['last']['optimizer_state']==state['optimizer_state'] and cks['last']['rng_state']==state['rng_state']
 hist=state['history'];per=math.ceil(len(fit)/128);last=per*len(hist);assert last==e['steps']==state['progress']['cumulative_steps']==state['nonzero_steps']
 best=None;be=0
 for i,h in enumerate(hist,1):
  assert h['epoch']==i and h['steps']==i*per and math.isfinite(h['value'])
  improved=best is None or (h['value']<best-1e-7 if cfg['monitor_direction']=='minimize' else h['value']>best+1e-7)
  assert h['improved']==improved
  if improved:best=h['value'];be=i
  assert h['best_epoch']==be and h['best_value']==best
  batches=[b for b in state['batch_evidence'] if b['epoch']==i]
  assert len(batches)==per and sum(b['rows'] for b in batches)==len(fit)
  assert all(math.isfinite(b['loss']) and math.isfinite(b['gradient_l1']) and b['gradient_l1']>0 for b in batches)
  assert abs(math.fsum(b['rows']*b['loss'] for b in batches)/len(fit)-h['train_loss'])<1e-10
 assert be==e['best_epoch']==state['best_epoch'] and (len(hist)==50 or len(hist)-be==8)
 assert cks['best']['progress']=={'epochs_completed':be,'cumulative_steps':be*per}
 assert all(tensor_floats(v['step'])==[last] for v in state['optimizer_state']['state'].values())
 assert len(state['rng_state']['numpy']['keys']['bytes'])==624*8 and len(state['rng_state']['torch_cuda'])==1
 pp=j(art/'preprocessing.json');sc=pp['feature_scaler'];floor=cfg.get('feature_scaler',{}).get('denominator_floor')
 old=j(next((P/'input/legacy/run-evidence').glob('hainan-breadth-'+task+'-h0-s44-*/preprocessing.json')))
 oldsc=old.get('feature_scaler',old.get('feature'))
 assert oldsc is not None,old.keys()
 assert sc['mean']==oldsc['mean'] and sc['fit_n_rows']==len(fit)
 d0=oldsc['std'];denom=d0 if floor is None else [max(x,f32(floor)) for x in d0]
 assert sc['std']==denom
 if floor is not None:assert sc['denominators_pre_floor']==d0
 target=pp['target_scaler']
 if target:
  y=[float(train[i]['Y']) for i in sorted(fit)];mu=math.fsum(y)/len(y);sd=(math.fsum((v-mu)**2 for v in y)/len(y))**.5 or 1.
  assert abs(target['mean']-mu)<1e-12 and abs(target['std']-sd)<1e-12
 blind=[]
 for partition in ('train','valid','test'):
  src=tables.setdefault((task,partition),rows(P/'input/data'/task/(partition+'.csv')));pred=rows(art/f'predictions-{partition}.csv');ok=mask(P/'input/legacy/cache/chemeleon_mp'/task/f'mask_{partition}.npy')
  assert len(src)==len(pred)==len(ok)
  for i,(x,y) in enumerate(zip(src,pred)):
   assert (y['task'],y['split'],int(y['row_index']),y['Drug_ID'],y['Drug'],y['Y'])==(task,partition,i,x['Drug_ID'],x['Drug'],x.get('Y',''))
   assert y['parsed']==str(ok[i]) and y['internal_partition']==(('fit' if i in fit else 'stop') if partition=='train' else '')
   value=float(y['y_pred']);assert math.isfinite(value)
   if cfg['kind']=='classification':assert 0<=value<=1
  totals[partition]+=len(pred)
  if partition!='train':blind+=pred
 assert blind==rows(art/'predictions.csv')
 pair=(task,e['seed']);fp={'initial':tensor_digest(state['initial_state_dict']),'split':split['split_record_sha256'],'mean':sc['mean'],'d0':d0,'perms':[h['permutation_sha256'] for h in hist]}
 if pair in paired:
  oldp=paired[pair];assert all(oldp[k]==fp[k] for k in ('initial','split','mean','d0'));n=min(len(fp['perms']),len(oldp['perms']));assert oldp['perms'][:n]==fp['perms'][:n]
 else:paired[pair]=fp
 steps+=last;reports.append({'run_id':e['run_id'],'steps':last,'epochs':len(hist),'best_epoch':be,'floor':floor,'head_tensors_changed':True,'full_rows_verified':True,'encoder_record_unchanged':True})
assert dict(totals)==t['expected_prediction_rows'] and steps==13842 and len(paired)==14
job=j(O/'global-evidence/raw/job-exit01.json');own=j(O/'global-evidence/raw/worker-identity.json')['pid'];samples=[json.loads(x) for x in (O/'global-evidence/raw/resource01.jsonl').read_text().splitlines()];peak=0
for sample in samples:
 q=sample['query'];assert q['exit']==0 and sample['stop_reason'] is None
 gpu=ET.fromstring(q['stdout']).find('gpu');assert gpu.findtext('uuid')=='GPU-b9fbba0f-b366-d145-720a-37b369c234a0' and gpu.findtext('gpu_recovery_action')=='None'
 assert {int(x.text) for x in gpu.findall('processes/process_info/pid')}<={own}
 peak=max(peak,int(gpu.findtext('fb_memory_usage/used').split()[0]))
assert len(samples)==115 and peak==839 and job['actual_strace_wait_exit']==0
result={'manifest_files_checked':len(m['files']),'manifest_bytes_checked':sum(x['size'] for x in m['files'].values()),'scientific_modules_unchanged':len(scientific),'runs':reports,'prediction_rows':dict(totals),'steps':steps,'paired_groups':len(paired),'resource_samples':len(samples),'device_peak_MiB':peak,'gpu_job_seconds':job['elapsed_gpu_job_seconds'],'private_truth_read':False,'new_training_or_inference':False,'checkpoint_reader':'restricted inert storage/tensor decoding; no torch or returned program execution','limits':['No new model forward in root; executor separate CPU full-row readback code and raw execution evidence reviewed separately','Resource evidence is point sampling, not continuous isolation','Existing field traces do not prove all-parent/all-ioctl/whole-host zero effect']}
(OUT/'independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='runs'},ensure_ascii=False))
