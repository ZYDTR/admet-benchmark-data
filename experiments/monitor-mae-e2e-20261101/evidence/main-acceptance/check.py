"""Primary's local acceptance. No ML imports, inference, pickle load, score or remote calls."""
import ast, array, collections, contextlib, csv, hashlib, io, json, math, re, sys
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent
R = OUT.parents[3]
RUN = R/'runs/hainan-mae-monitor-20261101'
OP = RUN/'operator/execution-04'
FETCH = RUN/'raw/execution-04/remote-snapshot'
load = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, value):
    with (OUT/name).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')

# Reuse the personally reviewed stdlib checker, retaining all original operator
# files. Remove its sole result write and return its computed record to this run.
reader = OP/'verify_artifacts.py'
tree = ast.parse(reader.read_text())
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=='main')
writes = [n for n in main.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
          and isinstance(n.value.func, ast.Attribute) and n.value.func.attr=='write_text']
assert len(writes)==1
main.body[main.body.index(writes[0])] = ast.Return(value=ast.Name(id='result', ctx=ast.Load()))
ast.fix_missing_locations(tree)
ns = {'__name__':'primary_reviewed_reader', '__file__':str(reader)}
exec(compile(tree, str(reader), 'exec'), ns)
result = ns['main']()
result['main_independent_acceptance'] = 'artifact checks reproduced by primary; separate source/trace checks below'
save('artifact-recheck.json', result)

# Recompute trace classification from original strace bytes, not operator PASS.
trace_source = OP/'audit_trace.py'
tree = ast.parse(trace_source.read_text())
nodes = [n for n in tree.body if isinstance(n,ast.FunctionDef)]
scope = {k:globals()[k] for k in ['ast','collections','hashlib','json','re','Path','FETCH']}
scope['ROOT'] = '<AUTHORIZED_PROJECT_ROOT>/admet/hainan-mae-monitor-20261101'
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('mutations','fdmutations') for t in n.targets):
        exec(compile(ast.Module(body=[n],type_ignores=[]),str(trace_source),'exec'),scope)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(trace_source),'exec'),scope)
traces = [scope['audit_trace'](p) for p in sorted((FETCH/'raw').rglob('*.strace'))]
assert len(traces)==2
assert all(not x['outside_mutation_evidence'] and not x['unresolved_count'] and not x['pending_at_eof'] for x in traces)
save('write-trace-recheck.json', {'traces':traces,'parser_sha256':sha(trace_source),
    'scope':'traced filesystem mutations; no claim of whole-server, read or ioctl isolation'})

cfg=load(FETCH/'source/config.json'); plan=load(RUN/'PLAN.json')
assert {k:v for k,v in cfg['head_config'].items() if k!='optimizer'}==plan['head_config']
assert cfg['head_config']['optimizer']=='AdamW' and cfg['split_config']==plan['split_config']
e=load(FETCH/'artifacts/training-evidence.json'); history=e['history']
assert e['head_config']==cfg['head_config'] and e['optimizer_config']==[{'lr':0.0005,'weight_decay':0.0001}]
assert e['head_parameter_shapes']=={'0.weight':[256,2048],'0.bias':[256],'3.weight':[1,256],'3.bias':[1]}
assert e['encoder_forward_events'] and all(not x['grad_enabled'] and not x['training'] and set(x['devices'])=={'cuda:0'} for x in e['encoder_forward_events'])
assert e['head_output_devices']==['cuda:0']
assert e['optimizer_separation']['encoder_requires_grad_count']==0
assert e['optimizer_separation']['encoder_training'] is False
best_i=None; best=float('inf')
for i,row in enumerate(history):
    assert row['epoch']==i+1 and row['steps']==5*(i+1) and row['steps_this_epoch']==5
    assert row['learning_rate']==[0.0005] and math.isfinite(row['max_gradient_l1_so_far'])
    assert row['monitor_value']==row['internal_validation_raw_mae']==row['stop_eval_mae']
    if row['monitor_value']<best-1e-7: best=row['monitor_value']; best_i=i
assert best_i==6 and len(history)==15 and len(history)-1-best_i==cfg['head_config']['patience']
tables={}
for item in cfg['inputs']:
    p=FETCH/item['path']; assert sha(p)==item['sha256']
    with p.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); table=list(reader)
        assert len(table)==item['rows'] and ('Y' in reader.fieldnames)==(item['role']=='train')
    tables[item['role']]=table
with (FETCH/'artifacts/train-predictions.csv').open(newline='') as f: pred=list(csv.DictReader(f))
train_metric_checks={}
for marker,prefix in [('fit','fit_eval'),('internal_stop','stop_eval')]:
    group=[x for x in pred if x['split_marker']==marker]
    diffs=[float(x['y_pred'])-float(x['Y']) for x in group]
    actual={'mae':sum(abs(d) for d in diffs)/len(diffs),'mse':sum(d*d for d in diffs)/len(diffs)}
    for key,value in actual.items():
        expected=history[best_i][prefix+'_'+key]
        assert abs(value-expected)<2e-5, (marker,key,value,expected)
    train_metric_checks[marker]={'rows':len(group),'mae_and_mse_match_best_epoch':True,'absolute_tolerance':2e-5}

post=load(OP/'postcheck.json'); identity=load(OP/'identity-resources.json')
assert identity['hostname']=='<COMPUTE_HOST>' and identity['uid']==1012
assert len(post['own_processes'])==8 and all(x['state']=='gone' for x in post['own_processes'])
profile=load(FETCH/'source/production-adapter-v1/execution-profile.json')
gpu_uuid=profile['gpu_uuid']
prelaunch=[]
for phase in ['preflight','train']:
    status=load(FETCH/'raw/attempt-01'/phase/'status.json')
    proof=load(FETCH/'raw/attempt-01'/phase/'protection.json')
    assert proof['landlock_applied'] is True and proof['guard']['restrict_self_return_code']==0
    assert proof['limits']['cpu_affinity']==[0,1]
    observations=load(FETCH/'raw/attempt-01'/phase/'prelaunch.json')
    for obs in observations:
        gpu=next(x for x in ET.fromstring(obs['health_xml']).findall('gpu') if x.findtext('uuid')==gpu_uuid)
        assert gpu.findtext('gpu_recovery_action')=='None'
        assert int(gpu.findtext('fb_memory_usage/free').split()[0])>=8192
        assert not gpu.findall('processes/process_info')
        assert not any(gpu_uuid in line for line in obs['apps_csv'].splitlines())
    prelaunch.append({'phase':phase,'observations':len(observations),'health_and_no_active_load':True})
gpu=next(x for x in ET.fromstring(post['gpu_health_xml']).findall('gpu') if x.findtext('uuid')==gpu_uuid)
assert gpu.findtext('gpu_recovery_action')=='None' and not gpu.findall('processes/process_info')
assert gpu.findtext('utilization/gpu_util')=='0 %'
assert not any(gpu_uuid in line for line in post['gpu_apps'].splitlines())
learning=load(FETCH/'state/learning-started.lock')
assert learning['offline'] is False
assert learning['token']==load(FETCH/'raw/attempt-01/train/status.json')['token']
registered={x['pid'] for x in post['own_processes']}
max_rss=0; samples=0
for phase in ['preflight','train']:
    events=[json.loads(x) for x in (FETCH/'raw/attempt-01'/phase/'events.jsonl').read_text().splitlines()]
    for row in events:
        if 'tree_rss_bytes' not in row: continue
        samples+=1; max_rss=max(max_rss,row['tree_rss_bytes'])
        assert row['tree_rss_bytes']<=8*1024**3
    assert events[-1]['child_returncode']==0
additional={'config_matches_frozen_plan':True,'new_head_shapes':e['head_parameter_shapes'],
    'head_lr':0.0005,'head_seed':43,'best_epoch_recomputed':best_i+1,'early_stop_patience_recomputed':8,
    'train_only_metric_rechecks':train_metric_checks,'blind_valid_test_columns_verified':True,
    'cuda_encoder_and_head_events_verified':True,'prelaunch':prelaunch,'host':'<COMPUTE_HOST>','uid':1012,
    'postcheck_own_pids_gone':sorted(registered),'gpu_released_at_recorded_postcheck':True,
    'resource_sample_count':samples,'maximum_tree_rss_bytes':max_rss,
    'learning_lock_retained':True,'official_valid_truth_read':False,'official_scoring_performed':False,
    'scientific_result_accepted_for_downstream_scoring':True,'supervisor_success':False,
    'supervisor_actual_exit_code':125,'supervisor_fault_root_cause':'unknown; failing stat/status not captured',
    'retrieval_snapshot_complete_run':False,'missing_from_execution_snapshot':['root encoder.py','large pretrained asset; reuse or fresh transfer required'],
    'source_review':['train_remote_v4.py complete','production completion and state_contract','operator binary reader and write-trace parser','previously admitted science/runtime hashes'],
    'limitations':['recorded postcheck is not a new remote observation','RAM/GPU observations are not hard OS quotas','occupied-GPU sharing and exact resumed-learning trajectory untested','no independent GPU re-execution']}
save('main-additional-checks.json', additional)
print(json.dumps({'accepted_for_scoring':True,'epochs':15,'steps':75,'best_epoch':7,'traces':len(traces),'outer_exit':125}))
