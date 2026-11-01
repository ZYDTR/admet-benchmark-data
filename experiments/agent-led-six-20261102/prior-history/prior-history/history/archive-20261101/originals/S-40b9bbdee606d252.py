"""Parent offline checks, standard library only: no training or pickle execution."""
from pathlib import Path
import ast,array,csv,hashlib,json,math,pickletools,re,struct,sys,zipfile
R=Path(__file__).resolve().parents[1]; A=R/'acceptance'; F=R/'raw/final-fetch'; W=R.parents[3]
def load(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest_check(root,values):
 for n,m in values.items():
  p=root/n;assert p.is_file() and p.stat().st_size==m['size'] and sha(p)==m['sha256'],str(p)
 return len(values)
snapshot=manifest_check(A/'parent-originals',load(A/'parent-originals/run-manifest.json')['files'])
protected=manifest_check(W,load(A/'protected-manifest.json'))
prior=R.parent/'hainan-frozen-training-20261031';prior_n=manifest_check(prior,load(prior/'delivery-manifest.json'))
assert sha(R/'PLAN.json')=='ba04167c7b47110210ebd1e0fa7aa1a665386bdbd35c009331271c0e372f1323'
post=load(A/'parent-postcheck.json'); fm=load(F/'fetch-manifest.json')
assert all(post['returned_file_hashes'][n]==m['sha256'] for n,m in fm.items())
pre=load(R/'raw/environment-before02.stdout');after=post['environment']
for k in ['python_sha256','pyvenv_config','packages']:assert pre[k]==after[k],k
# Actual checkpoint structure: inspect opcodes as data, never call pickle.loads/torch.load.
shapes={'0.weight':[256,2048],'0.bias':[256],'3.weight':[1,256],'3.bias':[1]};pkproof={}
for file in ['head-initial.pt','caco2_wang-head.pt']:
 with zipfile.ZipFile(F/'artifacts'/file) as z:
  ops=list(pickletools.genops(z.read(next(n for n in z.namelist() if n.endswith('/data.pkl')))))
  for name,shape in shapes.items():
   i=next(i for i,(o,v,p) in enumerate(ops) if o.name=='BINUNICODE' and v==name)
   j=next(j for j in range(i,len(ops)) if ops[j][0].name=='BINPERSID')
   ints=[]
   for o,v,pos in ops[j+1:]:
    if o.name.startswith('TUPLE'):break
    if o.name in ['BININT','BININT1','BININT2']:ints.append(v)
   assert ints==[0]+shape,(file,name,ints)
  for key,value in ([('seed',43)] if file.startswith('head-initial') else [('lr',.0005),('seed',43),('feature_dim',2048)]):
   i=next(i for i,(o,v,p) in enumerate(ops) if o.name=='BINUNICODE' and v==key)
   assert ops[i+2][1]==value,(file,key)
  sizes=[len(z.read(n)) for n in sorted(z.namelist()) if '/data/' in n]
  assert sizes==[2097152,1024,1024,4],sizes
  pkproof[file]={'sha256':sha(F/'artifacts'/file),'shapes':shapes,'storage_bytes':sizes,'parameters':sum(sizes)//4}
e=load(F/'artifacts/training-evidence.json');assert e['head_parameter_shapes']==shapes
assert e['head_config']==load(R/'PLAN.json')['head_config']
assert e['optimizer_config']==[{'lr':.0005,'weight_decay':.0001}]
assert e['epochs_run']==19 and e['optimizer_steps']==95 and e['nonzero_gradient_steps']==95
# NPY arrays contain only numeric values; verify original train-row split and preprocessing.
def npy(z,n):
 b=z.read(n+'.npy');assert b[:6]==b'\x93NUMPY';v=b[6:8];hsize=2 if v==b'\x01\x00' else 4
 size=int.from_bytes(b[8:8+hsize],'little');info=ast.literal_eval(b[8+hsize:8+hsize+size].decode());assert info['fortran_order'] is False
 types={'<i8':'q','<f4':'f','<f8':'d','|b1':'B'};a=array.array(types[info['descr']]);a.frombytes(b[8+hsize+size:]);assert len(a)==math.prod(info['shape'])
 if sys.byteorder!='little' and a.itemsize>1:a.byteswap()
 return info,list(a)
with zipfile.ZipFile(F/'artifacts/preprocessing.npz') as z:
 arrays={n[:-4]:npy(z,n[:-4]) for n in z.namelist()};tr=arrays['train_row_indices'][1];va=arrays['internal_validation_row_indices'][1]
 assert len(tr)==573 and len(va)==64 and len(set(tr)&set(va))==0 and sorted(tr+va)==list(range(637))
 with (F/'input/train.csv').open(encoding='utf-8-sig') as f:yy=[float(x['Y']) for x in csv.DictReader(f)]
 mean=sum(yy[i] for i in tr)/len(tr);std=(sum((yy[i]-mean)**2 for i in tr)/len(tr))**.5
 assert abs(mean-arrays['target_mean'][1][0])<1e-5 and abs(std-arrays['target_std'][1][0])<1e-5
with zipfile.ZipFile(F/'artifacts/features-train.npz') as z:
 info,x=npy(z,'features');assert info['shape']==(637,2048)
 max_mean=max_sd=0
 for col in range(2048):
  values=[x[i*2048+col] if math.isfinite(x[i*2048+col]) else 0. for i in tr]
  mu=sum(values)/len(values);sd=(sum((v-mu)**2 for v in values)/len(values))**.5
  if sd<1e-8:sd=1.
  max_mean=max(max_mean,abs(mu-arrays['feature_mean'][1][col]));max_sd=max(max_sd,abs(sd-arrays['feature_std'][1][col]))
 assert max_mean<1e-4 and max_sd<1e-4,(max_mean,max_sd)
for part in ['valid','test']:
 with (F/'input'/f'{part}.csv').open(encoding='utf-8-sig') as f:assert set(csv.DictReader(f).fieldnames)=={'Drug_ID','Drug'}
# Confirm training PID was actually resident on chosen GPU, foreign conflict was different PID.
u=load(F/'source/config.json')['gpu_uuid'];pid=load(F/'raw/train-runtime.json')['pid'];own_samples=[];foreign=[]
for phase in ['cuda01','cuda02','train01']:
 for line in (F/'raw'/f'{phase}-observations.jsonl').read_text().splitlines():
  ob=json.loads(line);ids={p['pid'] for p in ob['processes']}
  for row in csv.reader(ob['apps'].splitlines()):
   if row and row[0].strip()==u:
    if phase=='train01' and int(row[1])==pid:own_samples.append({'pid':pid,'memory_mib':int(row[2]),'at':ob['at']})
    if phase=='cuda01' and int(row[1]) not in ids:foreign.append({'pid':int(row[1]),'at':ob['at']})
assert own_samples and foreign
assert load(F/'raw/cuda01-exit.json')['reason']=='Other process appeared; yield own job'
# Conservatively flag traced mutation syscalls not handled by the parser, if present.
extra=[]
for p in (F/'raw').glob('*.strace'):
 for i,line in enumerate(p.open(errors='replace'),1):
  if re.search(r'\b(copy_file_range|sendfile|msync|pwritev|renameat2|fchmodat|fchownat)\(',line):extra.append({'file':p.name,'line':i,'text':line.strip()})
assert not extra,extra[:5]
# Runtime source chain and originals, preserved independently.
source_sha={sha(p):str(p.relative_to(R)) for p in (R/'source').glob('*') if p.is_file()}
commands=[json.loads(x) for x in (R/'raw/commands.jsonl').read_text().splitlines()]
unmatched=[x for x in commands if 'source_sha256' in x and x['source_sha256'] not in source_sha]
assert not unmatched,unmatched
out={'passed':True,'snapshot_files':snapshot,'protected_files_unchanged':protected,'prior_delivery_files_unchanged':prior_n,'fresh_remote_hashes_match':len(fm),'environment_packages_unchanged':len(after['packages']),'checkpoint_direct_checks':pkproof,'internal_train_split':[len(tr),len(va)],'preprocessing_train_only_max_abs_error':{'feature_mean':max_mean,'feature_std':max_sd},'actual_gpu_training_pid':pid,'own_gpu_observation_count':len(own_samples),'own_peak_mib':max(x['memory_mib'] for x in own_samples),'first_preflight_foreign_observations':foreign,'unparsed_additional_mutations':extra,'remote_sources_all_matched':True,'thread_api_sha256':sha(A/'parent-originals/thread-api.json'),'no_model_execution_in_acceptance':True}
(A/'parent-supplemental.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['checkpoint_direct_checks','first_preflight_foreign_observations']},ensure_ascii=False,indent=2))
