"""Root-only independent arithmetic; writes aggregate comparisons, no row labels."""
from pathlib import Path
import json,csv,hashlib,math,statistics,decimal,datetime
D=Path(__file__).parents[2]/'retrieval/batch28-001';A=Path(__file__).parent
T=json.loads((D/'SCORING_TASK.json').read_text());S=json.loads((D/'private-scoring/scores.json').read_text());reported={x['run_id']:x for x in S['scores']};truths={};checks=[];started=datetime.datetime.now(datetime.timezone.utc).isoformat()
def rows(spec):
 p=Path(spec['path']);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==spec['sha256']
 with p.open(encoding='utf-8-sig',newline='') as f:r=list(csv.DictReader(f))
 assert len(r)==spec['rows'];return r

def rank(v):
 by={}
 for i,x in enumerate(v):by.setdefault(x,[]).append(i)
 r=[0.]*len(v);start=1
 for value,ids in sorted(by.items()):
  mean=start+(len(ids)-1)/2
  for i in ids:r[i]=mean
  start+=len(ids)
 return r
assert len(T['runs'])==len(reported)==28
for x in T['runs']:
 key=x['truth']['path']
 if key not in truths:truths[key]=rows(x['truth'])
 t=truths[key];b=rows(x['blind']);p=rows(x['prediction']);y=[];v=[]
 for i,(ti,bi,pi) in enumerate(zip(t,b,p)):
  assert (ti['Drug_ID'],ti['Drug'])==(bi['Drug_ID'],bi['Drug'])==(pi['Drug_ID'],pi['Drug'])
  assert (pi['task'],pi['split'],pi['row_index'])==(x['task'],'valid',str(i));y.append(float(ti['Y']));v.append(float(pi['y_pred']))
 assert all(math.isfinite(z) for z in y+v)
 assert all(pi['parse_ok'] in ('True','False') for pi in p)
 if x['metric'] in ('AUROC','AUPRC'): assert set(y)<={0.,1.} and all(0<=z<=1 for z in v)
 name=x['metric'];exact=None
 if name=='MAE':
  with decimal.localcontext() as c:
   c.prec=50;q=sum(abs(decimal.Decimal(a['Y'])-decimal.Decimal(b['y_pred'])) for a,b in zip(t,p))/len(t);exact=str(q);value=float(q)
 elif name=='AUROC':
  pos=[z for yi,z in zip(y,v) if yi==1];neg=[z for yi,z in zip(y,v) if yi==0];value=sum(1. if a>b else .5 if a==b else 0. for a in pos for b in neg)/(len(pos)*len(neg))
 elif name=='AUPRC':
  thresholds=sorted(set(v),reverse=True);last_recall=0.;value=0.;positive=sum(y)
  for threshold in thresholds:
   predicted=[i for i,z in enumerate(v) if z>=threshold];tp=sum(y[i] for i in predicted);recall=tp/positive;value+=(recall-last_recall)*(tp/len(predicted));last_recall=recall
 else:value=statistics.correlation(rank(y),rank(v))
 r=reported[x['run_id']];assert math.isclose(value,r['value'],rel_tol=2e-12,abs_tol=2e-12),(x['run_id'],value,r['value'])
 checks.append(dict(run_id=x['run_id'],task=x['task'],metric=name,rows=len(t),reported=r['value'],independent=value,absolute_difference=abs(value-r['value']),Decimal50=exact))
result=dict(passed=True,scoring_verified=True,checks=checks,independent_root_truth_source_reads=len(truths),independent_root_truth_rows=sum(len(v) for v in truths.values()),new_formal_model_evaluations=0,independent_verification_not_new_model_selection=True,row_labels_or_residuals_written=False,started_at=started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(A/'scores-independent.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'verified':len(checks),'root_truth_reads':len(truths),'largest_difference':max(x['absolute_difference'] for x in checks)}))
