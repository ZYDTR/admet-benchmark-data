"""Read-only scientific-delivery checks (stdlib only).
No model loading, training, inference, network, or quality-score computation.
Operates only on this delivery's JSON, already accepted aggregate transcriptions,
and new matrix counts. Prints its result; it does not modify any input file.
"""
from pathlib import Path
from decimal import Decimal
import json, hashlib, re, collections
P=Path(__file__).resolve().parent
REQ='admet-pro-next-research-20261103-003'
INPUT_SHA='c61e67a6dc85e2aada50e0a46b6d9a9d7241b385f26f15629ab5ecce790d0eb8'
checks=[]
def ok(name,condition,detail):
 if not condition: raise AssertionError(name+': '+str(detail))
 checks.append({'check_id':name,'status':'pass','detail':detail})
def load(n):return json.loads((P/n).read_text(encoding='utf-8'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
files={p.name:load(p.name) for p in P.glob('*.json') if p.name not in {'delivery-manifest.json','validation_report.json'}}
for f in ['analysis.md','review.json','issues.json','next_batch_guide.md','next_experiments.json','search_space.json']:
 ok('exists:'+f,(P/f).is_file() and (P/f).stat().st_size>0,'actual nonempty UTF-8 file')
for f in ['issues.json','next_experiments.json','search_space.json']:
 ok('root:'+f,isinstance(files[f],list),'array root')
r=files['review.json']; ps=files['next_experiments.json']; issues=files['issues.json']; ds=files['search_space.json']; er=files['evidence_registry.json']; controls=files['controls.json']; assets=files['scientific_assets.json']; splits=files['split_register.json']
pmap={x['proposal_id']:x for x in ps}; imap={x['issue_id']:x for x in issues}; dmap={x['direction_id']:x for x in ds}; emap={x['source_id']:x for x in er['sources']}; cmap={x['control_id']:x for x in controls}; amap={x['asset_id']:x for x in assets}; smap={x['split_id']:x for x in splits}
for name,items,m in [('proposals',ps,pmap),('issues',issues,imap),('directions',ds,dmap),('sources',er['sources'],emap),('controls',controls,cmap),('assets',assets,amap),('splits',splits,smap)]:ok('unique:'+name,len(items)==len(m),len(items))
ok('identity',r['request_id']==REQ and r['manifest_sha256']==INPUT_SHA and er['input_manifest_sha256']==INPUT_SHA,'request and manifest binding')
ok('questions',{x['question_id'] for x in r['decision_coverage']}=={f'Q{i}' for i in range(1,7)} and len(r['decision_coverage'])==6,'Q1–Q6 exactly once')
for q in r['decision_coverage']:
 ok('coverage:'+q['question_id'],all(k in q and q[k] for k in ['answer_summary','answer_location','evidence_refs','supporting_evidence','counterevidence','unresolved','affected_decisions']) and q['status'] in {'answered','partial','needs_evidence'},'answer/support/counterevidence/location/unresolved retained')
ok('scientific_status',r['status']=='needs_evidence' and any(q['status']=='partial' for q in r['decision_coverage']),'partial question not falsely declared complete')
# Resolve every structured ID reference, including nested asset and evidence data.
refkeys={'evidence_refs':emap,'source_refs':emap,'related_proposal_ids':pmap,'proposal_ids':pmap,'direction_ids':dmap,'issue_ids':imap,'linked_issues':imap,'reused_control_ids':cmap,'controls':dict(cmap,**pmap)}
def walk(x,path=''):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in refkeys and isinstance(v,list) and all(isinstance(t,str) for t in v):
    bad=[t for t in v if t not in refkeys[k]]
    if bad:raise AssertionError('unresolved '+path+'/'+k+': '+repr(bad))
   if k=='source_id' and isinstance(v,str) and v not in emap:raise AssertionError('source_id '+path+': '+v)
   walk(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'/'+str(i))
for n,x in files.items():walk(x,n)
ok('references',True,'all structured issue/direction/proposal/control/source references resolve')
# Manuscript source labels, not inferred bare web turn IDs.
for n in ['analysis.md','next_batch_guide.md']:
 refs=set(re.findall(r'\b[EHX]-[A-Z0-9]+(?:-[A-Z0-9]+)*\b',(P/n).read_text()))
 bad=refs-set(emap)
 ok('markdown_refs:'+n,not bad,sorted(bad) if bad else str(len(refs))+' source IDs resolved')
TASKS={
 'ames':'AUROC','bbb_martins':'AUROC','bioavailability_ma':'AUROC','caco2_wang':'MAE',
 'clearance_hepatocyte_az':'Spearman','clearance_microsome_az':'Spearman',
 'cyp2c9_substrate_carbonmangels':'AUPRC','cyp2c9_veith':'AUPRC',
 'cyp2d6_substrate_carbonmangels':'AUPRC','cyp2d6_veith':'AUPRC',
 'cyp3a4_substrate_carbonmangels':'AUROC','cyp3a4_veith':'AUPRC','dili':'AUROC',
 'half_life_obach':'Spearman','herg':'AUROC','hia_hou':'AUROC','ld50_zhu':'MAE',
 'lipophilicity_astrazeneca':'MAE','pgp_broccatelli':'AUROC','ppbr_az':'MAE',
 'solubility_aqsoldb':'MAE','vdss_lombardo':'Spearman'}
actions=files['task22_actions.json']
ok('task22',len(actions)==22 and {a['task'] for a in actions}==set(TASKS),'all22 endpoints')
for a in actions:
 ok('task_metric:'+a['task'],a['metric']==TASKS[a['task']] and a['direction']==('minimize' if a['metric']=='MAE' else 'maximize'),'local registered metric, not official-equivalence assertion')
 ok('task_action:'+a['task'],all(a.get(k) for k in ['action_category','facts_supporting_retention','counterevidence_and_rejected_scope','unresolved','next_discriminator','scientific_scope_closure']),'fact/counterevidence/unknown/decision/closure')
identities=[]; stage=collections.Counter(); mode=collections.Counter()
required=['proposal_id','task','scientific_asset_id','asset_version','split','model_seeds','seed_semantics','preprocessing','production_config','training_objective','preparation_mode','design_type','controls','direction_ids','issue_ids','new_gradient_fits','new_context_fits','trigger','skip_or_stop_if']
for x in ps:
 pid=x['proposal_id']; t=x['task']; o=x['training_objective']; c=x['production_config']
 ok('fields:'+pid,all(k in x for k in required),'complete scientific config')
 ok('one_task_one_split:'+pid,isinstance(t,str) and t in TASKS and x['split']==smap[x['split']['split_id']],'one actual task and one registered split')
 ok('asset:'+pid,x['scientific_asset_id'] in amap and x['asset_version']==amap[x['scientific_asset_id']],'exact asset version copied; no execution LLM')
 ok('seeds:'+pid,x['model_seeds']==[44,45] and x['split']['split_seed']==43,'model seeds separate from splitseed')
 metric=TASKS[t]; direc='minimize' if metric=='MAE' else 'maximize'
 ok('objectives:'+pid,all(o.get(k) for k in ['loss','formula','loss_scale','early_stopping_metric','early_stopping_direction','prediction_scale','external_metric','external_metric_direction']) and o['external_metric']==metric and o['external_metric_direction']==direc and o['early_stopping_metric']==metric and o['early_stopping_direction']==direc and c['monitor_metric']==metric and c['monitor_direction']==direc,'loss scale/monitor/external/prediction separately defined')
 ok('boundary:'+pid,x['new_context_fits']==0 and x['new_wholeValid_scores']==0 and x['split']['external_split']=='nativeTrain.stress' and x['status']=='proposal_only_not_authorized','no new wholeValid/contextfit/authorization')
 ok('fit_count:'+pid,x['new_gradient_fits']==len(x['model_seeds']),'one physicalgradientfit perseed')
 ok('design:'+pid,x['design_type'] in ['control','one_factor','bundle'] and x['preparation_mode'] in ['config_only','new_code','blocked_assets'],'design/readiness enums')
 ok('no_half_life:'+pid,t!='half_life_obach','no repeated half-life seed or recipe')
 if metric=='AUPRC':ok('binary_no_target_scaling:'+pid,x['preprocessing']['target_statistics'].startswith('none;'),'binary original labels, no standardized target')
 if x['stage_id']=='G':ok('geometry_blocked:'+pid,x['preparation_mode']=='blocked_assets' and x['asset_version'].get('weights_sha256') and x['seed_semantics']['geometry_seed']==42,'exact checkpoint and geometryseed, not ready')
 block={'task':t,'asset':x['asset_version'],'split':x['split'],'preprocessing':x['preprocessing'],'objective':o,'production_config':c}
 h=hashlib.sha256(json.dumps(block,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
 ok('config_digest:'+pid,h==x['full_scientific_configuration_id'],'independently recomputed new config digest')
 for seed in x['model_seeds']:identities.append((h,seed))
 stage[x['stage_id']]+=len(x['model_seeds']);mode[x['preparation_mode']]+=len(x['model_seeds'])
ok('new_identity_unique',len(identities)==len(set(identities))==66,'full scientificconfiguration+modelseed')
ok('closed_form_counts',dict(stage)=={'R':28,'X':16,'N':8,'G':8,'K':4,'T':2},dict(stage))
ok('readiness_counts',dict(mode)=={'config_only':48,'new_code':10,'blocked_assets':8},dict(mode))
# Check control graph and common seeds; no self dependency/cycles.
def dfs(pid,stack,done):
 if pid in stack:raise AssertionError('control cycle '+repr(stack+[pid]))
 if pid in done:return
 x=pmap[pid]
 for c in x['controls']:
  parent=pmap.get(c,cmap.get(c))
  ok('control_task:'+pid+':'+c,parent['task']==x['task'],'shared task')
  ok('control_seeds:'+pid+':'+c,set(x['model_seeds'])<=set(parent['model_seeds']),'shared modelseed')
  if c in pmap:dfs(c,stack+[pid],done)
 done.add(pid)
done=set()
for pid in pmap:dfs(pid,[],done)
ok('control_graph',True,'acyclic proposal controls and exact existingcontrol references')
used={c for x in ps for c in x['controls'] if c in cmap}
ok('controls_unique',len(used)==11 and sum(len(cmap[c]['model_seeds']) for c in used)==22,'11controlgroups/22existingfits, reusedonce')
for c in controls:ok('control_no_new_fit:'+c['control_id'],c['new_fits']==0,'accepted parent reused')
# Prove one-factor claims in declared same-dimensional loss pairs.
for x in ps:
 if x['stage_id'] in ['R','X'] and x['training_objective']['loss'] not in ['HalfMSELoss','MSELoss']:
  candidates=[pmap[c] for c in x['controls'] if c in pmap]
  if candidates:
   h=next(y for y in candidates if y['training_objective']['loss']=='HalfMSELoss')
   ok('onefactor_loss:'+x['proposal_id'],all(x[k]==h[k] for k in ['task','asset_version','split','preprocessing','production_config','model_seeds']),'only declared objective changes vsHalfMSE')
# Existing outstanding physical fits stay outside new matrix; raw/native is not just a string cosmetic.
ex=files['exclusions_and_reuse.json']['active_or_preparing_exclusions']
for x in ps:
 for e in ex:
  if x['task']==e['task'] and e['state'] not in ['scientifically_skipped_equivalent','skipped_equivalent']:
   # No exact old raw/dual/window design is allowed in a new native matrix.
   ok('pending_separation:'+x['proposal_id']+':'+e['exclusion_id'],x['split']['external_split']=='nativeTrain.stress' and e['split'] not in [x['split']['split_id']], 'distinct declared scientific split/objective; not a view recounted as fit')
# Scenario sums and reused controls are generated independently from proposal inclusion.
for sc in files['budget_scenarios.json']['scenarios']:
 subset=[pmap[k] for k in sc['proposal_ids']]; ids={c for x in subset for c in x['controls'] if c in cmap}
 ok('budget:'+sc['scenario_id'],sum(x['new_gradient_fits'] for x in subset)==sc['new_gradient_fits'],'derived from explicit matrix')
 ok('budget_tasks:'+sc['scenario_id'],{x['task'] for x in subset}==set(sc['task_ids']),'exact taskset')
 ok('budget_control:'+sc['scenario_id'],set(sc['reused_control_ids'])==ids and sum(len(cmap[c]['model_seeds']) for c in ids)==sc['unique_existing_control_fits'],'shared controls countedonce')
 ok('budget_readiness:'+sc['scenario_id'],dict(collections.Counter({k:sum(x['new_gradient_fits'] for x in subset if x['preparation_mode']==k) for k in sc['readiness_counts']}))==sc['readiness_counts'],'readiness fit sum')
# Decimal recomputation only of accepted task-level aggregates, not a model metric.
a=files['aggregate_inputs_and_new_checks.json']; inp=a['aggregate_input_transcriptions']; checkmap={x['check_id']:x for x in a['checks']}; tol=Decimal('1e-12')
for key in ['half_life_stress','micro_stress','hep_stress']:
 d=[Decimal(str(x['candidate']))-Decimal(str(x['control'])) for x in inp[key]]; ch=checkmap['CHK-'+key]
 ok('aggregate_delta:'+key,all(abs(z-Decimal(str(y)))<tol for z,y in zip(d,ch['deltas'])),'Decimal subtraction of alreadyaccepted scalarinputs')
 ok('aggregate_sign:'+key,sum(z>0 for z in d)==ch['positive_count'],'positive signs only, no pvalue')
 ok('aggregate_mean:'+key,abs(sum(d)/len(d)-Decimal(str(ch['mean_delta_descriptive'])))<tol,'descriptive mean')
raw=[Decimal(str(v)) for v in inp['half_life_raw_rank_minus_halfmse'].values()]
ok('raw_mean',abs(sum(raw)/4-Decimal(str(checkmap['CHK-RAW-HALFMSE']['mean_delta'])))<tol,'mean of4registered differences')
for pair,n in checkmap['CHK-CAPACITY']['counts'].items():
 D,h=map(int,re.findall(r'\d+',pair));ok('capacity:'+pair,D*h+2*h+1==n,'algebraic MLP count, no model instantiated')
ok('cohort_bound_not_claimed',checkmap['CHK-COMMON-ERROR-BOUND']['actual_bound_computed'] is False and checkmap['CHK-COMMON-ERROR-BOUND']['new_truth_needed'] is False,'bound proposed, not a measured newscore')
# All known historical predecessor IDs targeted in original claim-events source.
known={'E-RANKING8-20261103','A015-CONFIRM14','E-HEPATOCYTE-CONFIRM4-20261103','A012-AMES6','A014-MINIMOL12-CONFIRMATION','astra-fixed-cohort96-consumption-20261103','E-LD50-STRESS4-20261103','E-STRESS48-COMPLETE-SCIENCE-20261103','E-HEPATOCYTE-STRESS8-20261103'}
for ev in files['claim_events.json']:
 ok('event:'+ev['event_id'],ev['occurred_at'] is None and ev['destructive_history_edit'] is False and (ev['previous_event_id'] is None or ev['previous_event_id'] in known),'append-only, known predecessor or explicitnull, no invented eventtime')
# Source receipts distinguish reading from registered hash values and unavailable routes.
ok('reads_honest',all(s.get('read_scope') and s.get('visible_tool_refs') and isinstance(s.get('source_version'),dict) for s in er['sources']),'per-source scope/tool/version')
ok('no_agent',r['no_agent_delegation']['performed'] is False and r['execution_authorized'] is False,'no delegation/execution authorization')
result={'request_id':REQ,'input_manifest_sha256':INPUT_SHA,'status':'pass','method_scope':'stdlib JSON/reference/count/Decimal aggregate arithmetic checks only; no archived code/model/data execution; not a scientific-quality or causality proof','checks':checks,'summary':{'files_parsed':len(files),'check_count':len(checks),'tasks':22,'questions':6,'proposals':33,'new_unique_gradient_fit_caps':{'small':28,'medium':44,'large':66},'readiness':dict(mode),'existing_control_fits_reused_once':22,'new_wholeValid_scores':0,'new_context_fits':0},'unresolved_not_overridden':'review.json and evidence_gaps.json; scientific_status remains needs_evidence','draft_corrections_before_sealing':['binary-target metadata corrected to no scaling','unverified zero-std fallback not asserted as production fact','new VDss and nestedfit split rules distinguished from reused parent membership','mis-transcribed claims.json URL corrected to registered claim-events.json; original accessible','partial reading scopes not promoted to full original reading']}
print(json.dumps(result,ensure_ascii=False,indent=2))
