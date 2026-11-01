from pathlib import Path
import zipfile,csv,io,json,hashlib,collections,decimal
R=Path(__file__).resolve().parent
Z=Path('<LOCAL_PRIVATE_PATH>).zip')
B=R.parent/'admet_deepseek_skill_coldstart_20261030/model/input/data'
P='data_benchmark/cleaned_data_20261029/'
result={'source_zip':str(Z),'archive_sha256':hashlib.sha256(Z.read_bytes()).hexdigest(),'checks':{},'errors':[],'split_counts':{},'per_task':[]}
with zipfile.ZipFile(Z) as z:
 def read(name):return z.read(name)
 def table(name):return list(csv.DictReader(io.StringIO(read(name).decode('utf-8-sig'),newline='')))
 manifest=json.loads(read(P+'processed/manifest.json')); before=json.loads(read(P+'processed/source_manifest_before.json')); after=json.loads(read(P+'processed/source_manifest_after.json'))
 result['recorded_generation']= {k:manifest[k] for k in ('created_at_utc','rdkit_version','source_root')}
 result['checks']['source_before_after_equal']=before==after
 for group,mapping,prefix in [('source',before,'data_benchmark/'),('output',manifest['output_sha256'],P+'processed/'),('implementation',manifest['implementation_sha256'],P)]:
  bad=[]
  for name,value in mapping.items():
   expected=value['sha256'] if isinstance(value,dict) else value
   if hashlib.sha256(read(prefix+name)).hexdigest()!=expected:bad.append(name)
  result['checks'][group+'_hashes']={'checked':len(mapping),'mismatches':bad}
 rawtables={}; processed={}; totals=collections.Counter(); issues=collections.Counter(); earlier_mismatch=[]; dedup_total=0; weight_total=0; conflicts=0; identities=set(); splitlabelcounts=collections.Counter()
 tasks=sorted(json.loads(read(P+'config/tasks.json')))
 for task in tasks:
  info={'task':task}
  for split in ('train','valid','test'):
   raw=table(f'data_benchmark/{task}/{split}.csv'); clean=table(P+f'processed/tasks/{task}/{split}.csv'); rawtables[(task,split)]=raw;processed[(task,split)]=clean
   if len(raw)!=len(clean):result['errors'].append([task,split,'row_count'])
   counts=collections.Counter()
   for i,(a,b) in enumerate(zip(raw,clean)):
    expected_id=f'{task}/{split}/{i:06d}'
    ok=(b['task']==task and b['split']==split and b['sample_idx']==str(i) and b['row_id']==expected_id and b['drug_id']==a['Drug_ID'] and b['smiles_original']==a['Drug'] and b['y_original']==a.get('Y','') and b['sample_weight']=='1')
    if not ok:result['errors'].append([task,split,i,'identity_or_original'])
    if b['row_id'] in identities:result['errors'].append([task,split,i,'duplicate_row_id'])
    identities.add(b['row_id'])
    if split=='test':
     if b['y'] or b['y_original']:result['errors'].append([task,split,i,'test_label_added'])
    elif decimal.Decimal(a['Y'])!=decimal.Decimal(b['y']):result['errors'].append([task,split,i,'numeric_label_changed'])
    if b['y']:splitlabelcounts[split]+=1
    counts['rows']+=1;counts['model_smiles_text_changed']+=b['smiles']!=a['Drug'];counts['label_text_changed']+=b['y']!=a.get('Y','');counts['invalid_structure']+=b['parse_status']=='invalid';counts['empty_id']+=not b['drug_id'];counts['fallback']+=b['needs_structure_fallback']=='1'
    issues.update(x for x in b['issue_codes'].split(';') if x)
   result['split_counts'].setdefault(split,collections.Counter()).update(counts)
   local=B/(f'blind_validation/{task}/valid.csv' if split=='valid' else f'official/data_benchmark/{task}/{split}.csv')
   if split=='valid':
    old=list(csv.DictReader(local.open(encoding='utf-8-sig',newline='')))
    equal=[(x['Drug_ID'],x['Drug']) for x in old]==[(x['Drug_ID'],x['Drug']) for x in raw]
   else:equal=hashlib.sha256(local.read_bytes()).digest()==hashlib.sha256(read(f'data_benchmark/{task}/{split}.csv')).digest()
   if not equal:earlier_mismatch.append([task,split])
   info[split]=len(clean)
   if split=='train':
    dedup=table(P+f'processed/tasks/{task}/train_deduplicated.csv');lookup={x['row_id']:x for x in clean}; covered=[];groupkeys=set()
    for row in dedup:
     ids=json.loads(row['source_row_ids']);covered.extend(ids);w=int(row['sample_weight']);weight_total+=w
     if w!=len(ids):result['errors'].append([task,'weight_mismatch'])
     key=(row['molecule_id'],decimal.Decimal(row['y']))
     if key in groupkeys:result['errors'].append([task,'dedup_key_repeated'])
     groupkeys.add(key)
     for rid in ids:
      src=lookup.get(rid)
      if src is None or (src['molecule_id'],decimal.Decimal(src['y']))!=key:result['errors'].append([task,'dedup_membership'])
    if collections.Counter(covered)!=collections.Counter(lookup.keys()):result['errors'].append([task,'dedup_coverage'])
    dedup_total+=len(dedup);info['train_deduplicated']=len(dedup)
  result['per_task'].append(info)
 result['checks']['same_inputs_as_preparation']={'checked':66,'train_test_byte_equality':44,'valid_id_smiles_equality':22,'mismatches':earlier_mismatch}
 result['deduplication']={'train_before':result['split_counts']['train']['rows'],'train_after':dedup_total,'removed_extra_observations':result['split_counts']['train']['rows']-dedup_total,'sample_weight_sum':weight_total}
 result['labels_present_in_cleaned']=dict(splitlabelcounts);result['issue_counts']=dict(issues)
 template=table(P+'reference/submission_template.csv');mapping=table(P+'processed/submission/test_row_mapping.csv');bad=[]
 for idx,(t,m) in enumerate(zip(template,mapping)):
  key=(t['task'],'test');i=int(t['sample_idx']);raw=rawtables[key][i];proc=processed[key][i]
  if m['template_row']!=str(idx) or m['row_id']!=proc['row_id'] or m['drug_id']!=raw['Drug_ID'] or m['smiles_original']!=raw['Drug'] or (t['drug_id'],t['smiles'])!=(raw['Drug_ID'],raw['Drug']):bad.append(idx)
 result['checks']['submission_mapping']={'template_rows':len(template),'mapping_rows':len(mapping),'mismatches':bad,'template_sha256':hashlib.sha256(read(P+'reference/submission_template.csv')).hexdigest()}
 result['checks']['deep_rdkit_recomputed_this_turn']=False
 result['checks']['training_or_scoring_executed']=False
 result['checks']['records_compared']=sum(x['rows'] for x in result['split_counts'].values())
result['split_counts']={k:dict(v) for k,v in result['split_counts'].items()}
(R/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ('per_task','source_zip','recorded_generation')},ensure_ascii=False,indent=2))
