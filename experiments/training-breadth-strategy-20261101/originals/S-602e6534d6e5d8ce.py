"""Independent static evidence arithmetic; no model execution, fitting or private labels."""
from pathlib import Path
import array,ast,csv,json,math,struct,sys,zipfile
T=Path(__file__).resolve().parents[1];C=T/'retrieval/public_candidate'
def npz(path):
 out={}
 with zipfile.ZipFile(path) as z:
  assert len(z.infolist())<=12 and sum(i.file_size for i in z.infolist())<64000000
  for info in z.infolist():
   b=z.read(info); assert b[:6]==b'\x93NUMPY'; major=b[6]; hs=2 if major==1 else 4; n=int.from_bytes(b[8:8+hs],'little'); h=ast.literal_eval(b[8+hs:8+hs+n].decode('latin1')); assert not h['fortran_order']
   descr=h['descr'];code={'<f4':'f','<f8':'d','<i8':'q','|b1':'b'}[descr];v=array.array(code);v.frombytes(b[8+hs+n:]);assert len(v)==math.prod(h['shape']);assert sys.byteorder=='little';out[info.filename.removesuffix('.npy')]=(h['shape'],v)
 return out
rows=list(csv.DictReader((C/'data/train.csv').open(encoding='utf-8-sig',newline='')));results={}
for rid in ['hainan-frozen-training-20261031','hainan-skill-follow-20261031']:
 d=C/'runs'/rid/'artifacts';p=npz(d/'preprocessing.npz');tr=p['train_row_indices'][1];va=p['internal_validation_row_indices'][1];mu=p['feature_mean'][1];sd=p['feature_std'][1]
 ts={rows[i]['Drug'] for i in tr};vs={rows[i]['Drug'] for i in va};overlap=sorted(ts&vs)
 extrema={}
 for split in ['train','valid','test']:
  shape,x=npz(d/f'features-{split}.npz')['features'];assert shape[1]==len(mu)==len(sd);best=(-1,None,None)
  for n,value in enumerate(x):
   k=n%shape[1];val=abs((value-mu[k])/sd[k]);
   if val>best[0]:best=(val,n//shape[1],k)
  extrema[split]={'maximum_absolute_standardized_feature_double_arithmetic':best[0],'row_index':best[1],'feature_index':best[2],'training_fit_std_at_dimension':sd[best[2]]}
 results[rid]={'exact_raw_SMILES_overlap_fit_internal_validation':len(overlap),'overlap_rows':[{'fit':[i for i in tr if rows[i]['Drug']==s],'internal_validation':[i for i in va if rows[i]['Drug']==s]} for s in overlap],'smallest_stored_feature_std':min(sd),'std_below_1e_4':sum(v<1e-4 for v in sd),'std_below_1e_6':sum(v<1e-6 for v in sd),'extrema':extrema}
out={'method':'Standard-library NPY parsing, exact raw-SMILES overlap and double arithmetic on already cached features; no training, inference, fitting or valid truth','scope_limit':'Raw-SMILES equality only, not full chemical canonicalization; arithmetic uses stored float32 values promoted to double rather than reproducing all float32 operations; no causal attribution to prediction error','runs':results}
(T/'acceptance/independent-cache-diagnostics.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
