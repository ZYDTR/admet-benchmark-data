"""Validate research artifact structure/references/counts; never load a model or execute input code."""
from pathlib import Path
import argparse,json,hashlib,copy,re

def parse(path):
 def pairs(items):
  out={}
  for k,v in items:
   if k in out:raise ValueError(f'duplicate JSON key {k} in {path}')
   out[k]=v
  return out
 return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return digest(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--write-report',action='store_true');a=ap.parse_args();D=a.root
 tests=[]
 def check(name,ok,detail):
  tests.append({'check_id':name,'passed':bool(ok),'detail':detail})
  if not ok:raise AssertionError((name,detail))
 data={p.relative_to(D).as_posix():parse(p) for p in D.rglob('*.json') if p.name!='delivery-manifest.json'}
 check('ALL_JSON_PARSE',True,len(data))
 required={
 'review.json':'schema_version request_id round_id manifest_sha256 status read_receipt read_checks findings missing_evidence not_assessed comparison_groups stop_reasons decision_coverage'.split(),
 'issues.json':'issue_id status severity category statement affected_run_ids evidence_refs hypothesis counterevidence impact proposed_resolution verification_criterion related_proposal_ids'.split(),
 'next_experiments.json':'proposal_id priority hypothesis control_run_or_config task scientific_asset_id asset_versions change_only hold_fixed split_id seeds metric direction minimum_effect_or_decision_rule success_criterion falsification_criterion compute_budget dependencies within_current_scope stage exact_config preparation_mode reuse_assets estimated_run_count trigger skip_or_stop_if review_checkpoint direction_ids training_objective design_type'.split(),
 'search_space.json':'direction_id linked_issues rationale evidence_refs counterevidence candidate_models_or_modules parameters combination_constraints search_method configuration_count_or_counting_rule seeds estimated_run_count cost_assumptions readiness priority scope_status'.split()}
 for f,fields in required.items():
  val=data[f];check('ROOT_'+f,isinstance(val,dict if f=='review.json' else list),type(val).__name__)
  for j,r in enumerate([val] if isinstance(val,dict) else val):check('FIELDS_'+f+'_'+str(j),set(fields)<=set(r),sorted(set(fields)-set(r)))
 for f in ['analysis.md','next_batch_guide.md']:check('TEXT_'+f,(D/f).is_file() and len((D/f).read_text())>1000,(D/f).stat().st_size)
 rev=data['review.json'];check('IDENTITY',rev['request_id']=='admet-breadth-six24-pro-20261102-001' and rev['round_id']=='six-task-breadth24-review-20261102' and rev['manifest_sha256']=='d4ce680da124d6f8fbede0fe33d0ade98ab7b7acfb1a87a42fab4581c472ee98',rev['request_id'])
 check('REVIEW_STATUS',rev['status'] in ['complete','needs_evidence','inconclusive'],rev['status'])
 cv=rev['decision_coverage'];check('EXACT_Q0_Q8',len(cv)==9 and {x['question_id'] for x in cv}=={f'Q{i}' for i in range(9)},[x['question_id'] for x in cv])
 for c in cv:check('COVERAGE_'+c['question_id'],set('question_id status answer_summary answer_location evidence_refs unresolved affected_decisions'.split())<=set(c) and c['status'] in ['answered','partial','needs_evidence'],c['status'])
 check('COMPLETE_REQUIRES_ANSWERED',rev['status']!='complete' or all(c['status']=='answered' for c in cv),'no hidden partial question')
 P=data['next_experiments.json'];I=data['issues.json'];S=data['search_space.json'];G=data['preparation_tasks.json'];M=data['matrix-expanded.json'];B=data['budget-scenarios.json'];idx=data['evidence-index.json'];base={x['task']:x for x in data['evidence/mini22-transcription.json']}
 ids={k:{r[k]:r for r in rows} for k,rows in [('proposal_id',P),('issue_id',I),('direction_id',S),('gate_id',G)]}
 for k,rows in [('proposal_id',P),('issue_id',I),('direction_id',S),('gate_id',G)]:check('UNIQUE_'+k,len(ids[k])==len(rows),len(rows))
 known=set(idx)|set().union(*(set(x) for x in ids.values()))
 refkeys={'evidence_refs','new_evidence','supporting_evidence','direction_ids','linked_issues','related_proposal_ids','affected_proposal_ids','control_proposal_ids','issue_ids'}
 def walk(z,where):
  if isinstance(z,dict):
   for k,v in z.items():
    if k in refkeys:check('REF_'+where+'/'+k,all(t in known for t in v),[t for t in v if t not in known])
    walk(v,where+'/'+k)
  elif isinstance(z,list):
   for j,v in enumerate(z):walk(v,where+'/'+str(j))
 for f in ['review.json','issues.json','next_experiments.json','search_space.json','issue-events.json','conditional_followups.json','preparation_tasks.json']:walk(data[f],f)
 current=[parse(p) for p in (D/'evidence/configs24').glob('*.json')];runnames={x['run_id'] for x in current}|{r['run_id'] for r in data['evidence/historical-run-identities.json']}
 for i in I:check('ISSUE_RUNS_'+i['issue_id'],set(i['affected_run_ids'])<=runnames,i['affected_run_ids'])
 for p in P:
  pid=p['proposal_id'];c=p['exact_config'];check('PREP_'+pid,p['preparation_mode'] in ['config_only','new_code','blocked_assets'],p['preparation_mode']);check('STAGE_'+pid,p['stage'] in ['screen','confirm','reserve'],p['stage']);check('DESIGN_'+pid,p['design_type'] in ['control','one_factor','bundle'],p['design_type'])
  check('TASK_'+pid,p['task'] in base and c['task']==p['task'] and p['scientific_asset_id']=='chemeleon',p['task'])
  check('METRIC_'+pid,p['metric']==base[p['task']]['metric'] and p['direction']==base[p['task']]['direction'],(p['metric'],p['direction']))
  o=p['training_objective'];check('OBJECTIVE_'+pid,set('loss loss_scale early_stopping_metric early_stopping_direction prediction_scale'.split())<=set(o) and o['early_stopping_direction']==p['direction'] and p['metric'] in o['early_stopping_metric'],o)
  check('SEEDS_'+pid,len(p['seeds'])==len(set(p['seeds'])) and all(isinstance(s,int) for s in p['seeds']) and p['estimated_run_count']==len(p['seeds']),p['seeds'])
  check('GATES_'+pid,all(g in ids['gate_id'] for g in p['dependencies']),p['dependencies'])
  ctr=p['control_run_or_config'];check('CONTROLS_'+pid,set(ctr.get('existing_run_ids',[]))<=runnames and set(ctr.get('proposal_ids',[]))<=set(ids['proposal_id']),ctr)
  check('AUTH_'+pid,p['compute_budget']['approved'] is False,'all proposal_only')
  check('REAL_FIELDS_'+pid,set(c['head'])==set(['feature_dim','hidden_dim','activation','dropout','optimizer','lr','weight_decay','batch_size','max_epochs','patience','seed']),list(c['head']))
 # Gate dependency cycles.
 graph={r['gate_id']:r.get('dependencies',[]) for r in G}
 def dfs(v,trail):
  if v in trail:raise AssertionError(('dependency cycle',trail+[v]))
  for w in graph.get(v,[]):dfs(w,trail+[v])
 for v in graph:dfs(v,[])
 check('GATE_GRAPH_ACYCLIC',True,len(graph))
 # Existing original config bytes and paired controlled difference.
 originals=data['checks/configs24-byte-check.json']
 for x in originals:
  raw=(D/x['local_path']).read_bytes();check('CONFIG_BYTES_'+x['entry_id'],len(raw)==x['bytes'] and digest(raw)==x['source_version']['sha256'],digest(raw))
 for t in sorted({r['task'] for r in current}):
  for seed in [44,45]:
   z=[copy.deepcopy(r) for r in current if r['task']==t and r['head']['seed']==seed];assert len(z)==2
   for r in z:r.pop('run_id');r['head'].pop('dropout')
   check('DROPOUT_ONLY_'+t+str(seed),z[0]==z[1],'all other actual fields equal')
 tuples=[]
 for r in M:
  p=ids['proposal_id'][r['proposal_id']];c=parse(D/r['config_path']);check('EXPANDED_'+r['fit_id'],r['seed'] in p['seeds'] and c['head']['seed']==r['seed'] and c['task']==r['task'],r['config_path'])
  scientific=copy.deepcopy(c);scientific.pop('run_id');scientific['head'].pop('seed');key=canonical({'asset':p['scientific_asset_id'],'versions':p['asset_versions'],'task':p['task'],'config':scientific,'split':p['split_id'],'seed':r['seed']});tuples.append(key)
  check('CONFIG_KEY_'+r['fit_id'],key==r['deduplication_key'] and canonical(scientific)==r['scientific_config_sha256'],key)
  check('NOT_ALREADY_DONE_'+r['fit_id'],not(r['task'] in {x['task'] for x in current} and r['variant']=='H0' and r['seed'] in [44,45]),'historical controls not newly counted')
 check('MATRIX_COUNTS',len(P)==44 and len(M)==88 and len(set(tuples))==88,{'proposals':len(P),'fits':len(M),'unique':len(set(tuples))})
 sets={s['scenario_id']:set(s['fit_ids']) for s in B};fitids={r['fit_id'] for r in M}
 check('SCENARIOS', [s['unique_new_fits'] for s in B]==[8,28,88] and all(len(sets[s['scenario_id']])==s['unique_new_fits'] for s in B),{s['scenario_id']:s['unique_new_fits'] for s in B})
 check('NESTED_AND_UNION',sets['light']<sets['medium']<sets['large'] and set.union(*sets.values())==fitids,88)
 check('CONDITIONAL_CAP',sum(x['new_fit_cap'] for x in data['conditional_followups.json'])==16,'0 scheduled;16 maximum after registration')
 # Source reading ranges refer to actual browser calls, never to a locally computed source hash.
 cat=data['evidence/source-catalog.json'];check('MANDATORY38',len(cat)==38 and len({x['entry_id'] for x in cat})==38,len(cat))
 for r in cat:
  covered=set()
  for v in r['views']:covered.update(range(v['line_start'],v['line_end']+1))
  missing=set(range(r['rendered_total_lines']))-covered
  check('READ_'+r['entry_id'],not missing and r['unread_line_ranges']==[],sorted(missing))
 for r in rev['read_receipt']:check('RECEIPT_'+r['entry_id'],set('entry_id layer uri source_version read_mode evidence_locator observed_fact limitation'.split())<=set(r) and set(r['source_version'])=={'commit','sha256'},r['entry_id'])
 for k,v in idx.items():
  if 'target' in v:check('SOURCE_ALIAS_'+k,v['target'] in idx,v['target'])
  if 'local_path' in v:check('LOCAL_SOURCE_'+k,(D/v['local_path']).exists() or v['local_path']=='checks/delivery-validation.json',v['local_path'])
 check('FIXTURES14',data['checks/independent-synthetic-fixtures.json']['passed']==14 and data['checks/independent-synthetic-fixtures.json']['failed']==0,'synthetic only')
 check('HISTORY34',data['history-coverage.json']['record_count']==34 and len(data['history-coverage.json']['records'])==34,'index-level all34, not all116anchors')
 report={'status':'pass','checks_passed':len(tests),'checks_failed':0,'scope':'structure, references, config hashes, counts and recorded reading coverage; no models/training/real truth','summary':{'mandatory_originals_read':38,'consumed_config_byte_hash_matches':24,'issues':len(I),'directions':len(S),'proposals':len(P),'unique_new_fits':88,'scenario_fits':[8,28,88],'conditional_unscheduled_cap':16,'synthetic_fixtures_passed':14},'tests':tests}
 if a.write_report:(D/'checks/delivery-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='tests'},ensure_ascii=False))
if __name__=='__main__':main()
