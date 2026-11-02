"""Independent mathematical/synthetic checks only; does not import or execute archived code/models."""
from pathlib import Path
import json, math, hashlib, itertools
import numpy as np
import argparse, tempfile
parser=argparse.ArgumentParser(); parser.add_argument('--output-dir',type=Path)
args=parser.parse_args(); O=args.output_dir or Path(tempfile.mkdtemp(prefix='admet-fixtures-')); O.mkdir(parents=True,exist_ok=True)
checks=[]
def add(name,observed,expected,ok,scope):
 assert bool(ok), (name,observed,expected)
 checks.append(dict(check_id=name,observed=observed,expected=expected,passed=True,scope=scope))
x=np.array([[0.,3.],[0.,3.],[0.,3.],[1.,3.]],dtype=np.float32)
mu=x.mean(0,dtype=np.float32); sd=x.std(0,dtype=np.float32,ddof=0); used=np.where(sd<1e-8,np.float32(1),sd)
z=(x-mu)/used
add('FIT_POPULATION_STD',sd.tolist(),[math.sqrt(3)/4,0],np.allclose(sd,[math.sqrt(3)/4,0]),'synthetic arithmetic, not production execution')
add('CONSTANT_DIM_UNIT_DENOMINATOR',used.tolist(),[math.sqrt(3)/4,1.],used[1]==1.,'matches audited strict below-epsilon replacement rule')
s=np.array([0,0.999e-8,1e-8,2e-8,1e-5,.01],np.float64)
u=np.where(s<1e-8,1,s)
add('STRICT_EPSILON',u.tolist(),[1,1,1e-8,2e-8,1e-5,.01],np.array_equal(u,[1,1,1e-8,2e-8,1e-5,.01]),'independent float64 boundary illustration; production fixture must test float32 representation too')
floor=np.maximum(u,1e-3)
add('F001_PRESERVES_CONSTANT_DIM',floor.tolist(),[1,1,.001,.001,.001,.01],np.array_equal(floor,[1,1,.001,.001,.001,.01]),'proposed denominator policy; does not clip any input row or prediction')
# A rare fit activation attains sqrt(n-1), while blind activation can exceed it.
n=100; rare=np.zeros(n); rare[0]=1; m=float(rare.mean()); d=float(rare.std(ddof=0))
fitmax=float(np.max(abs((rare-m)/d))); blindz=(100-m)/d
add('RARE_DIM_BOUND',fitmax,math.sqrt(n-1),abs(fitmax-math.sqrt(n-1))<1e-12,'exact synthetic fit population std; not empirical causality')
add('OOD_Z_CAN_EXCEED_FIT_BOUND',blindz,'greater than sqrt(99), finite',blindz>fitmax and math.isfinite(blindz),'counterexample to inferring raw overflow from a large standardized value')
# Fit/stop scope counterexample.
fit=np.array([1.,2.,3.]); stop=np.array([100.]); stop2=np.array([1e6])
fitstats=(fit.mean(),fit.std(ddof=0)); allstats=(np.r_[fit,stop].mean(),np.r_[fit,stop].std())
add('FIT_ONLY_SCOPE',[float(a) for a in fitstats],[2.,math.sqrt(2/3)],np.allclose(fitstats,[2,math.sqrt(2/3)]),'changing stop must not enter fit-statistics routine')
add('ALL_TRAIN_LEAKAGE_COUNTEREXAMPLE',[float(v) for v in allstats], 'different from fit-only statistics',not np.allclose(fitstats,allstats),'demonstrates why production fit indices must be enforced')
y=np.array([20.,22.]); pred_z=np.array([5.,6.]); pred=pred_z*2+10
mae=float(abs(pred-y).mean()); bad=float(abs(pred-(y*2+10)).mean())
add('INVERSE_ONCE_MAE',[mae,bad],[0.,31.],mae==0 and bad==31,'expected result for scale-transmission fixture; no model inference')
# An epoch improves only if native metric changes strictly beyond min_delta.
series=[1., .9]+[.9]*8
best=math.inf; best_epoch=None; stopped=None
for ep,v in enumerate(series,1):
 if v < best-1e-7: best=v; best_epoch=ep
 if ep-best_epoch>=8: stopped=ep;break
add('NATIVE_METRIC_PATIENCE',[best_epoch,stopped],[2,10],(best_epoch,stopped)==(2,10),'minimize example: ties retain earlier epoch; patience eight elapsed epochs')
def ranks(a):
 out=[0.]*len(a); order=sorted(range(len(a)), key=a.__getitem__); i=0
 while i<len(a):
  j=i+1
  while j<len(a) and a[order[j]]==a[order[i]]: j+=1
  for k in order[i:j]:out[k]=(i+j+1)/2
  i=j
 return out
def auc(y,p):
 pos=sum(y); neg=len(y)-pos
 if not pos or not neg:return None
 r=ranks(p); return (sum(a for a,b in zip(r,y) if b)-pos*(pos+1)/2)/(pos*neg)
def ap(y,p):
 pos=sum(y)
 if not pos or pos==len(y):return None
 order=sorted(range(len(y)),key=lambda i:-p[i]);seen=tp=0;v=0.;i=0
 while i<len(y):
  j=i+1
  while j<len(y) and p[order[j]]==p[order[i]]:j+=1
  k=sum(y[t] for t in order[i:j]);seen+=j-i;tp+=k;v+=k/pos*tp/seen;i=j
 return v
y=[1,0,1,0];p=[.9,.9,.2,.1]
add('TIED_AP_AUC',[ap(y,p),auc(y,p)],[7/12,5/8],abs(ap(y,p)-7/12)<1e-15 and auc(y,p)==5/8,'independent formula oracle for production parity; AP not trapezoid PR area')
vals={(round(ap([y[i] for i in q],[p[i] for i in q]),15),auc([y[i] for i in q],[p[i] for i in q])) for q in itertools.permutations(range(4))}
add('TIE_PERMUTATION_INVARIANCE',len(vals),1,len(vals)==1,'24 permutations; all observations synthetic')
add('ONE_CLASS_UNDEFINED',[ap([1,1],[.8,.2]),auc([0,0],[.8,.2])],[None,None],ap([1,1],[.8,.2]) is None and auc([0,0],[.8,.2]) is None,'required comparison policy, not universal sklearn convention')
# Hash coverage fixture demonstrates buffers must be included; it is not a real encoder proof.
def state_digest(state):
 h=hashlib.sha256()
 for k in sorted(state):h.update(k.encode());h.update(state[k].tobytes())
 return h.hexdigest()
s0={'parameter':np.array([1.,2.]),'buffer':np.array([0.])};s1={k:v.copy() for k,v in s0.items()};s1['buffer'][0]=1
add('BUFFER_MUTATION_DETECTED',state_digest(s0)!=state_digest(s1),True,state_digest(s0)!=state_digest(s1),'synthetic digest coverage; actual frozen encoder accepted by controller, not reloaded here')
res={'execution_kind':'aggregate and synthetic arithmetic only','archived_code_executed':False,'models_loaded':False,'new_fits':0,'model_inferences':0,'valid_truth_reads':0,'checks':checks,'passed':len(checks),'failed':0,'limitations':['These are independent expected-value fixtures; they do not certify a newly implemented production branch.','No raw feature NPY was downloaded, no stored model evaluated.']}
(O/'independent-synthetic-fixtures.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print('synthetic checks passed',len(checks))
