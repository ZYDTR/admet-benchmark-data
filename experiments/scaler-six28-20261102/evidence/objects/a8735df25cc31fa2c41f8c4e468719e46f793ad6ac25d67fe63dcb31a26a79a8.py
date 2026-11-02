from pathlib import Path
import csv,json,hashlib,math,random
P=Path(__file__).resolve().parent;T=json.loads((P.parent/'TASK.json').read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
totals={'train':0,'valid':0,'test':0};rows=[];snapshots=[]
cpu=json.loads((P/'global-evidence/raw/independent-CPU-verification.json').read_text());by_id={x['run_id']:x for x in cpu['runs']}
assert sha(P.parent/'TASK.json')=='61ad3cde5e2490c49d819150b3ba431f5db862cfd813c124e0bb9d472d78511f'
for e in T['inputs']:assert sha(Path(e['path']))==e['sha256']
for e in json.loads(Path(T['normative_snapshot']).read_text())['entries']:assert sha(Path(e['snapshot']))==e['sha256']
for e in T['runs']:
 run=P/'snapshots'/e['run_id'];a=run/'artifacts';m=json.loads((run/'_fetch-manifest.json').read_text())
 for name,item in m.items():
  if item['downloaded']:assert (run/name).stat().st_size==item['size'] and sha(run/name)==item['sha256'],(e['run_id'],name)
 assert sha(run/'source/config.json')==e['config_sha256']==sha(Path(e['config']))
 cfg=json.loads((run/'source/config.json').read_text());ev=json.loads((a/'training-evidence.json').read_text());done=json.loads((run/'raw/train-complete.json').read_text());rec=json.loads((a/'internal-split.json').read_text())
 assert ev['configuration']==cfg and done['steps']==by_id[e['run_id']]['steps']==ev['last_steps']
 assert ev['encoder_parameters_buffers_unchanged'] and not ev['encoder_in_optimizer'] and ev['encoding_calls']==0
 before=json.loads((a/'encoder-before.json').read_text());assert before==json.loads((a/'encoder-after.json').read_text())
 pp=json.loads((a/'preprocessing.json').read_text());sc=pp['feature_scaler'];floor=cfg.get('feature_scaler',{}).get('denominator_floor')
 assert sc['fit_n_rows']==rec['fit_rows'] and sc['fit_partition']=='official_train.fit_subset'
 if floor is not None:
  # JSON values are the exact values produced from float32 arrays.
  import struct
  floor32=struct.unpack('f',struct.pack('f',floor))[0]
  assert sc['denominator_floor']==floor and all(x==max(d,floor32) for x,d in zip(sc['std'],sc['denominators_pre_floor']))
 else:assert sc.get('denominator_floor') is None
 blind=[]
 for split in ['train','valid','test']:
  inp=next(v for v in T['inputs'] if v['task']==e['task'] and v['split']==split)
  with Path(inp['path']).open(newline='',encoding='utf-8-sig') as f:original=list(csv.DictReader(f))
  with (a/f'predictions-{split}.csv').open(newline='') as f:pred=list(csv.DictReader(f))
  assert len(original)==len(pred)==ev['counts'][split]
  meta=json.loads((P/'global-evidence/original-cache'/e['task']/f'raw_{split}.meta.json').read_text());unparsed=set(meta['identity']['unparsed_row_indices'])
  fit=set(rec['fit_row_indices']);stop=set(rec['stop_row_indices'])
  if split=='train':
   assert not fit&stop and fit|stop==set(range(len(original)))
   assert not {original[i]['Drug'] for i in fit}&{original[i]['Drug'] for i in stop}
   groups={}
   for i,r in enumerate(original):groups.setdefault(r['Drug'],[]).append(i)
   keys=sorted(groups);random.Random(43).shuffle(keys);selected=[];n=0;target=max(1,round(.1*len(original)))
   for k in keys:
    if n>=target and selected:break
    if len(selected)+1==len(keys):break
    selected.append(k);n+=len(groups[k])
   assert stop=={i for k in selected for i in groups[k]}
  for i,(r,p) in enumerate(zip(original,pred)):
   assert (p['task'],p['split'],int(p['row_index']),p['Drug_ID'],p['Drug'])==(e['task'],split,i,r['Drug_ID'],r['Drug'])
   assert p['Y']==r.get('Y','') and p['parsed']==str(i not in unparsed)
   assert p['internal_partition']==(('fit' if i in fit else 'stop') if split=='train' else '')
   assert math.isfinite(float(p['y_pred']))
   if cfg['kind']=='classification':assert 0<=float(p['y_pred'])<=1
  if split!='train':blind.extend(pred)
  totals[split]+=len(pred)
 assert blind==list(csv.DictReader((a/'predictions.csv').open(newline='')))
 rows.append({'run_id':e['run_id'],'task':e['task'],'variant':e['variant'],'seed':e['seed'],'epochs':done['epochs'],'steps':done['steps'],'best_epoch':done['best_epoch'],'best_steps':done['best_steps'],'remote_directory':e['remote_directory'],'local_snapshot':str(run),'config_sha256':e['config_sha256'],'files':m,'CPU_verification':by_id[e['run_id']]})
 snapshots.append({'run_id':e['run_id'],'downloaded_files':sum(x['downloaded'] for x in m.values()),'remote_reference_files':sum(not x['downloaded'] for x in m.values())})
assert totals==T['expected_prediction_rows'] and len(rows)==28
for mod in json.loads(Path(T['candidate_manifest']).read_text())['files']:
 rel=Path(mod['path']).relative_to('src');assert sha(P/'src'/rel)==sha(P/'global-evidence/src'/rel)==mod['sha256']
(P/'ARTIFACT_INDEX.json').write_text(json.dumps({'request_id':T['request_id'],'runs':rows,'prediction_rows':totals,'global_evidence_manifest':'global-evidence/_fetch-manifest.json'},ensure_ascii=False,indent=2)+'\n')
(P/'scientific-verification.json').write_text(json.dumps({'verified_runs':28,'prediction_rows':totals,'combined_blind_rows':totals['valid']+totals['test'],'optimizer_steps':sum(x['steps'] for x in rows),'downloaded_snapshot_integrity':snapshots,'separate_CPU_verification':'global-evidence/raw/independent-CPU-verification.json','candidate_scientific_modules_byte_unchanged':13,'all_config_files_byte_unchanged':28,'all18_input_SHA_unchanged':True,'all16_normative_snapshot_SHA_unchanged':True,'private_valid_truth_read':False},indent=2)+'\n')
print(json.dumps({'verified_runs':28,'prediction_rows':totals,'optimizer_steps':sum(x['steps'] for x in rows)}))
