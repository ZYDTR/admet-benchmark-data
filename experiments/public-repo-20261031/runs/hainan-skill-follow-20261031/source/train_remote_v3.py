"""One genuine Caco2 GPU run: frozen CheMeleon plus a new 256-unit head.
Only the three allowlisted CSV files and fixed checkpoint are opened as model/data inputs.
"""
import csv,hashlib,json,os,sys,time,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common_guarded import ROOT,GPU_UUID,environment,now,safe,sha,write_json
os.chdir(safe(ROOT,True));os.environ.clear();os.environ.update(environment())
import numpy as np
import torch
from torch import nn
from encoder import CheMeleonEmbedder
from chemprop import nn as chemprop_nn
from chemprop.models import MPNN
from chemprop.nn import RegressionFFN
cfg=json.loads((ROOT/'source/config.json').read_text());hc=cfg['head_config'];start=time.monotonic()
assert hc['hidden_dims']==[256] and hc['lr']==0.0005 and hc['seed']==43
assert torch.cuda.is_available() and torch.cuda.device_count()==1,'Single explicit CUDA device required'
torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.manual_seed(hc['seed']);np.random.seed(hc['seed'])
torch.cuda.set_device(0);props=torch.cuda.get_device_properties(0)
torch.cuda.set_per_process_memory_fraction((4096*1024**2)/props.total_memory,0)
device='cuda:0'
write_json(ROOT/'raw/train-runtime.json',{'at':now(),'pid':os.getpid(),'pgid':os.getpgid(0),'start_stat':Path('/proc/self/stat').read_text(),'torch':torch.__version__,'cuda':torch.version.cuda,'device':device,'device_name':props.name,'visible_gpu_uuid':os.environ['CUDA_VISIBLE_DEVICES'],'device_properties':str(props),'cpu_affinity':sorted(os.sched_getaffinity(0)),'torch_threads':torch.get_num_threads(),'dataloader_workers':0,'limits':{'allocator_fraction':(4096*1024**2)/props.total_memory,'allocator_target_bytes':4096*1024**2,'note':'PyTorch allocator cap only, excludes CUDA context/third-party allocations. Supervisor observes RSS and walltime.'}})

rows={}
for inp in cfg['inputs']:
    p=safe(ROOT/inp['path'],True);assert sha(p)==inp['sha256']
    with p.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f);cols=reader.fieldnames;table=list(reader)
    split={'train':'train','validation':'valid','test':'test'}[inp['role']]
    assert len(table)==inp['rows'] and 'Drug_ID' in cols and 'Drug' in cols
    assert ('Y' in cols)==(split=='train')
    rows[split]=table
checkpoint=safe(ROOT/'assets/chemeleon_mp.pt',True);assert sha(checkpoint)==cfg['pretrained_sha256']

def digest_state(model):
    each={};aggregate=hashlib.sha256()
    kinds={name:'parameter' for name,_ in model.named_parameters()}
    kinds.update({name:'buffer' for name,_ in model.named_buffers()})
    for name,t in sorted(model.state_dict().items()):
        value=t.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        item={'sha256':hashlib.sha256(value).hexdigest(),'shape':list(t.shape),'dtype':str(t.dtype),'kind':kinds.get(name,'state')}
        each[name]=item;aggregate.update(name.encode()+b'\0'+json.dumps(item,sort_keys=True).encode()+b'\0')
    return {'sha256':aggregate.hexdigest(),'tensors':each}

enc=CheMeleonEmbedder(checkpoint,device=device,batch_size=64);enc.assert_frozen()
assert all(p.device.type=='cuda' for p in enc.model.parameters())
before=digest_state(enc.model);write_json(ROOT/'artifacts/encoder-before.json',before)
enc_events=[]
def enc_hook(module,inputs,out):
    tensors=[out] if isinstance(out,torch.Tensor) else [x for x in out if isinstance(x,torch.Tensor)]
    assert tensors and all(x.device.type=='cuda' for x in tensors)
    assert not torch.is_grad_enabled() and not enc.model.training
    enc_events.append({'output_shapes':[list(x.shape) for x in tensors],'devices':[str(x.device) for x in tensors],'grad_enabled':torch.is_grad_enabled(),'training':enc.model.training})
enc_handle=enc.model.message_passing.register_forward_hook(enc_hook)
X={};masks={}
for split in ['train','valid','test']:
    enc.assert_frozen();X[split],masks[split]=enc.embed([r['Drug'] for r in rows[split]])
    assert X[split].shape==(len(rows[split]),enc.feature_dim)
    np.savez(ROOT/'artifacts'/f'features-{split}.npz',features=X[split],parse_mask=masks[split])
    print(json.dumps({'phase':'encoded','split':split,'rows':len(rows[split]),'parsed':int(masks[split].sum()),'feature_dim':enc.feature_dim,'at':now()}),flush=True)
y=np.asarray([float(r['Y']) for r in rows['train']],dtype=np.float32);assert np.isfinite(y).all()
rng=np.random.default_rng(hc['seed']);idx=rng.permutation(len(y));nv=max(1,int(round(len(y)*hc['val_fraction_from_train'])));va=idx[:nv];tr=idx[nv:]
filled={split:np.where(np.isfinite(v),v,np.float32(0)).astype(np.float32) for split,v in X.items()}
mu=filled['train'][tr].mean(axis=0);sd=filled['train'][tr].std(axis=0);sd[sd<1e-8]=1
ym=float(y[tr].mean());ys=float(y[tr].std()) or 1.;yy=(y-ym)/ys
scaled={k:(v-mu)/sd for k,v in filled.items()}
assert all(np.isfinite(v).all() for v in scaled.values())
np.savez(ROOT/'artifacts/preprocessing.npz',feature_mean=mu,feature_std=sd,train_row_indices=tr,internal_validation_row_indices=va,target_mean=ym,target_std=ys)

def build_head(seed):
    torch.manual_seed(seed)
    width=int(hc['hidden_dims'][0])
    return nn.Sequential(nn.Linear(enc.feature_dim,width),nn.ReLU(),nn.Dropout(hc['dropout']),nn.Linear(width,1)).to(device)
head=build_head(hc['seed']);initial={k:v.detach().cpu().clone() for k,v in head.state_dict().items()};initial_digest=digest_state(head)
torch.save({'state_dict':initial,'seed':hc['seed']},ROOT/'artifacts/head-initial.pt')
opt=torch.optim.AdamW(head.parameters(),lr=hc['lr'],weight_decay=hc['weight_decay'])
eids={id(p) for p in enc.model.parameters()};hids={id(p) for p in head.parameters()};oids={id(p) for g in opt.param_groups for p in g['params']}
assert oids==hids and oids.isdisjoint(eids)
optimizer_check={'optimizer_param_count':len(oids),'head_param_count':len(hids),'encoder_param_count':len(eids),'optimizer_exactly_head':oids==hids,'optimizer_encoder_intersection':len(oids & eids),'encoder_requires_grad_count':sum(p.requires_grad for p in enc.model.parameters()),'encoder_training':enc.model.training}
write_json(ROOT/'artifacts/optimizer-separation.json',optimizer_check)
Xt=torch.as_tensor(np.ascontiguousarray(scaled['train'][tr]),device=device);yt=torch.as_tensor(yy[tr],device=device).reshape(-1,1)
Xv=torch.as_tensor(np.ascontiguousarray(scaled['train'][va]),device=device);yv=torch.as_tensor(yy[va],device=device).reshape(-1,1)
loss_fn=nn.MSELoss();gen=torch.Generator(device='cpu').manual_seed(hc['seed']);best=float('inf');best_epoch=-1;best_state=None;steps=0;nonzero_steps=0;grad_max=0.;history=[];head_devices=set()
for epoch in range(hc['epochs']):
    enc.assert_frozen();head.train();perm=torch.randperm(len(tr),generator=gen);train_loss=0.
    for s in range(0,len(tr),hc['batch_size']):
        sel=perm[s:s+hc['batch_size']].to(device);opt.zero_grad(set_to_none=True);out=head(Xt[sel]);assert out.device.type=='cuda';head_devices.add(str(out.device));loss=loss_fn(out,yt[sel]);assert torch.isfinite(loss)
        loss.backward();grad=sum(float(p.grad.detach().abs().sum()) for p in head.parameters() if p.grad is not None)
        assert np.isfinite(grad) and grad>0 and all(p.grad is None or p.grad.device.type=='cuda' for p in head.parameters())
        nonzero_steps+=1;grad_max=max(grad_max,grad);opt.step();steps+=1;train_loss+=float(loss)*len(sel)
        assert all(p.grad is None for p in enc.model.parameters())
    head.eval()
    with torch.no_grad():val=float(loss_fn(head(Xv),yv))
    history.append({'epoch':epoch+1,'train_standardized_mse':train_loss/len(tr),'internal_validation_standardized_mse':val,'steps':steps})
    print(json.dumps({'phase':'head_training',**history[-1]}),flush=True)
    if val<best-1e-7:
        best=val;best_epoch=epoch;best_state={k:v.detach().clone() for k,v in head.state_dict().items()}
    elif epoch-best_epoch>=hc['patience']:break
assert best_state is not None and steps>0 and nonzero_steps>0
head.load_state_dict(best_state);head.eval();final_digest=digest_state(head)
changed={k:float((v.detach().cpu()-initial[k]).abs().max()) for k,v in head.state_dict().items()}
assert any(v>0 for v in changed.values()) and final_digest['sha256']!=initial_digest['sha256']
ck={'format':'hainan_caco2_chemeleon_head_v1','run_id':cfg['run_id'],'task':'caco2_wang','encoder_sha256':cfg['pretrained_sha256'],'head_config':hc,'feature_dim':enc.feature_dim,'state_dict':{k:v.detach().cpu() for k,v in head.state_dict().items()},'feature_mean':mu.tolist(),'feature_std':sd.tolist(),'target_mean':ym,'target_std':ys,'fill_value':0.,'fit_row_indices':tr.tolist(),'internal_validation_row_indices':va.tolist()}
torch.save(ck,ROOT/'artifacts/caco2_wang-head.pt')

def predict(model,features,mean,std,ym,ys):
    a=np.where(np.isfinite(features),features,np.float32(0));a=(a-mean)/std
    out=[]
    with torch.no_grad():
        for s in range(0,len(a),128):
            yhat=model(torch.as_tensor(np.ascontiguousarray(a[s:s+128]),dtype=torch.float32,device=device));assert yhat.device.type=='cuda';out.append(yhat.cpu().numpy().reshape(-1))
    result=np.concatenate(out)*ys+ym;assert np.isfinite(result).all();return result
pred={s:predict(head,X[s],mu,sd,ym,ys) for s in ['valid','test']}
after=digest_state(enc.model);assert before==after and all(p.grad is None for p in enc.model.parameters());enc.assert_frozen();enc_handle.remove()
# Reload our saved head and a fresh fixed encoder, then repeat blind inference on CUDA.
loaded=torch.load(ROOT/'artifacts/caco2_wang-head.pt',map_location='cpu',weights_only=True)
reloaded=build_head(0);reloaded.load_state_dict(loaded['state_dict']);reloaded.eval();assert digest_state(reloaded)==final_digest
torch.manual_seed(hc['seed'])  # Reproduce the frozen, unused MPNN predictor initialization too.
enc2=CheMeleonEmbedder(checkpoint,device=device,batch_size=64);enc2.assert_frozen();assert digest_state(enc2.model)==before
reload_checks={};pred_rows=[]
for split in ['valid','test']:
    xx,ok=enc2.embed([r['Drug'] for r in rows[split]]);assert np.array_equal(ok,masks[split])
    pp=predict(reloaded,xx,np.asarray(loaded['feature_mean'],dtype=np.float32),np.asarray(loaded['feature_std'],dtype=np.float32),loaded['target_mean'],loaded['target_std'])
    delta=float(np.max(np.abs(pred[split]-pp)));assert np.allclose(pred[split],pp,rtol=1e-5,atol=1e-5)
    reload_checks[split]={'rows':len(pp),'max_abs_prediction_difference':delta,'allclose_rtol':1e-5,'allclose_atol':1e-5}
    for i,(row,v) in enumerate(zip(rows[split],pp)):
        pred_rows.append({'task':'caco2_wang','split':split,'row_index':i,'Drug_ID':row['Drug_ID'],'Drug':row['Drug'],'y_pred':format(float(v),'.10g')})
assert digest_state(enc.model)==before and digest_state(enc2.model)==before
assert sha(checkpoint)==cfg['pretrained_sha256']
with (ROOT/'artifacts/predictions.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['task','split','row_index','Drug_ID','Drug','y_pred']);writer.writeheader();writer.writerows(pred_rows)
write_json(ROOT/'artifacts/encoder-after.json',after)
write_json(ROOT/'artifacts/training-evidence.json',{'started_at':json.loads((ROOT/'raw/train-runtime.json').read_text())['at'],'completed_at':now(),'device':device,'gpu_uuid':GPU_UUID,'encoder_forward_events':enc_events,'encoder_state_unchanged':before==after,'encoder_gradients_none':all(p.grad is None for p in enc.model.parameters()),'encoder_eval':not enc.model.training,'encoder_parameters_frozen':all(not p.requires_grad for p in enc.model.parameters()),'encoder_checkpoint_sha256_unchanged':sha(checkpoint)==cfg['pretrained_sha256'],'optimizer_separation':optimizer_check,'head_output_devices':sorted(head_devices),'head_initial_sha256':initial_digest['sha256'],'head_final_sha256':final_digest['sha256'],'head_changed_max_abs_by_tensor':changed,'head_config':hc,'head_parameter_shapes':{k:list(v.shape) for k,v in head.state_dict().items()},'optimizer_config':[{'lr':g['lr'],'weight_decay':g['weight_decay']} for g in opt.param_groups],'optimizer_steps':steps,'nonzero_gradient_steps':nonzero_steps,'maximum_gradient_l1':grad_max,'epochs_run':len(history),'best_epoch_1_based':best_epoch+1,'history':history,'fit_rows':len(tr),'internal_validation_rows':len(va),'parse_counts':{s:{'rows':len(v),'parsed':int(masks[s].sum())} for s,v in rows.items()},'reload_checks':reload_checks,'official_validation_scoring':False,'test_fitting':False,'cuda_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'cuda_peak_reserved_bytes':torch.cuda.max_memory_reserved(),'elapsed_seconds':time.monotonic()-start,'maximum_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
write_json(ROOT/'raw/train-complete.json',{'status':'success','at':now(),'optimizer_steps':steps,'prediction_rows':len(pred_rows),'encoder_frozen':True})
print(json.dumps({'status':'success','optimizer_steps':steps,'rows':len(pred_rows),'elapsed_seconds':time.monotonic()-start}),flush=True)
