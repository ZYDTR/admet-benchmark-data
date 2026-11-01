from pathlib import Path
import urllib.request, json, hashlib, concurrent.futures, zipfile, ast, struct, math
P=Path(__file__).resolve().parent.parent
RIDS=['hainan-frozen-training-20261031','hainan-skill-follow-20261031']
BASE='https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/eaec280cf142839597fe75ce748cd2b9a8a897d4/experiments/public-repo-20261031/'
manifest=json.loads((P/'manifest.json').read_text())
items={x['path']:x for x in manifest['payload_files']}
paths=[f'runs/{rid}/artifacts/features-{split}.npz' for rid in RIDS for split in ['train','valid','test']]
def get(name):
 q=P/name;x=items[name]
 if not q.exists():
  with urllib.request.urlopen(BASE+name,timeout=50) as r:b=r.read()
  assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];q.write_bytes(b)
 b=q.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256']
 return {'path':name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:downloads=list(pool.map(get,paths))

def npy(data):
 assert data[:6]==b'\x93NUMPY'
 major=data[6];prefix=10 if major==1 else 12
 n=struct.unpack('<H' if major==1 else '<I',data[8:prefix])[0]
 d=ast.literal_eval(data[prefix:prefix+n].decode('latin1'));payload=data[prefix+n:]
 assert not d['fortran_order'];count=math.prod(d['shape']);dtype=d['descr'];assert dtype in ['<f4','|b1']
 values=[x[0] for x in struct.iter_unpack('<f' if dtype=='<f4' else '<?',payload)]
 assert len(values)==count
 return d,values,hashlib.sha256(payload).hexdigest()

pre=[]
for rid in RIDS:
 a=json.loads((P/'runs'/rid/'preprocessing-readable.json').read_text())['arrays']
 pre.append({k:v['values'] for k,v in a.items()})
results=[]
for split in ['train','valid','test']:
 arrays=[]
 for rid in RIDS:
  file=P/'runs'/rid/'artifacts'/f'features-{split}.npz'
  with zipfile.ZipFile(file) as z:
   assert z.testzip() is None
   h,v,ph=npy(z.read('features.npy'));mh,mask,mph=npy(z.read('parse_mask.npy'))
  structure=json.loads((P/'runs'/rid/'binary-structure.json').read_text())['feature_npz'][split]
  assert ph==structure['features']['payload_sha256'] and mph==structure['parse_mask']['payload_sha256']
  assert all(math.isfinite(x) for x in v) and all(mask)
  arrays.append(v)
 rows,cols=h['shape'];assert cols==2048
 diffs=[abs(a-b) for a,b in zip(*arrays)];changed=sum(d>0 for d in diffs)
 scaled={}
 for j,rid in enumerate(RIDS):
  sd=pre[j]['feature_std'];mu=pre[j]['feature_mean']
  sd_delta=[d/sd[i%cols] for i,d in enumerate(diffs)]
  absstandard=[abs((v-mu[i%cols])/sd[i%cols]) for i,v in enumerate(arrays[j])]
  top=sorted(range(len(absstandard)),key=absstandard.__getitem__,reverse=True)[:5]
  scaled[rid]={'max_delta_using_same_run_scale':max(sd_delta),'mean_delta_using_same_run_scale':math.fsum(sd_delta)/len(sd_delta),'max_abs_scaled_feature':max(absstandard),'count_abs_scaled_gt_10':sum(x>10 for x in absstandard),'count_abs_scaled_gt_100':sum(x>100 for x in absstandard),'top_abs_scaled_locations':[{'row_index':i//cols,'feature_index':i%cols,'abs_scaled':absstandard[i],'feature':arrays[j][i],'mean':mu[i%cols],'sd':sd[i%cols]} for i in top]}
  if split=='train':
   tr=pre[j]['train_row_indices'];means=[];stds=[]
   for c in range(cols):
    vals=[arrays[j][r*cols+c] for r in tr];mean=math.fsum(vals)/len(vals);st=math.sqrt(math.fsum((x-mean)**2 for x in vals)/len(vals));st=1. if st<1e-8 else st
    means.append(mean);stds.append(st)
   scaled[rid]['fitted_feature_mean_max_difference_float64_recompute']=max(abs(a-b) for a,b in zip(means,mu))
   scaled[rid]['fitted_feature_std_max_difference_float64_recompute']=max(abs(a-b) for a,b in zip(stds,sd))
 results.append({'split':split,'shape':h['shape'],'values':len(diffs),'different_values':changed,'max_abs_difference':max(diffs),'mean_abs_difference':math.fsum(diffs)/len(diffs),'rms_difference':math.sqrt(math.fsum(d*d for d in diffs)/len(diffs)),'all_differences_le_1e_5':all(d<=1e-5 for d in diffs),'same_finite_masks':True,'same_parse_masks':True,'scaled_by_each_recorded_training_transform':scaled})
report={'method':'Read existing NPZ ZIP/NPY numeric payloads using only Python stdlib zipfile/ast.literal_eval/struct/math; no archive code/native model/pickle/torch.load/inference/training; float64 arithmetic audit, not scoring. Scaling comparisons apply each existing transform to both existing feature arrays to isolate encoder numeric drift; no fit change. Recomputed fit stats are double arithmetic diagnostic, not expected byte-identical to NumPy float32.','downloads':downloads,'results':results}
(P/'agent-reviews/feature-byte-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
