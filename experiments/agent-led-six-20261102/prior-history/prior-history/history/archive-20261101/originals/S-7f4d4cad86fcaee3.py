#!/usr/bin/env python3
"""只读验收已取回的 Caco2/CheMeleon 参考产物，不联网、不加载模型、不评分。"""
import array,csv,hashlib,json,math,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path

def require(value,message):
    if not value:raise ValueError(message)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def table(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def tensor_storage(p):
    with zipfile.ZipFile(p) as z:
        require(z.testzip() is None,'checkpoint CRC failed')
        names=[x for x in z.namelist() if '/data/' in x]
        require(len(names)==4,'expected four head tensors')
        return [z.read(x) for x in sorted(names)]
def check(run):
    run=Path(run).resolve(strict=True);f=run/'raw/final-fetch';a=f/'artifacts'
    load=lambda p:json.loads(p.read_text())
    manifest=load(f/'fetch-manifest.json')
    for name,meta in manifest.items():
        p=f/name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and p.resolve()==p,'unsafe manifest path')
        require(p.is_file() and p.stat().st_nlink==1 and p.stat().st_size==meta['size'] and sha(p)==meta['sha256'],'returned file identity: '+name)
    for name,meta in load(run/'raw/upload-manifest.json').items():
        require(sha(f/name)==meta['sha256'],'reviewed source identity: '+name)
    plan=load(run/'PLAN.json');cfg=load(f/'source/config.json');post=load(run/'acceptance/postcheck.json')
    for name,digest in post['source_hashes'].items():
        require(sha(f/'source'/name)==digest,'post-run source changed: '+name)
    require(plan['run_id']==cfg['run_id'] and cfg['task']=='caco2_wang','reference scope')
    require(plan['head_config']==cfg['head_config'],'configuration changed')
    require(plan['pretrained_backbone_frozen'] is True and plan['validation_labels_allowed'] is False and plan['test_fitting_allowed'] is False,'policy drift')
    for role in ['train','validation','test']:
        local=next(x for x in plan['inputs'] if x['role']==role);remote=next(x for x in cfg['inputs'] if x['role']==role)
        require(local['sha256']==remote['sha256']==sha(f/remote['path'])==post['input_hashes'][remote['path']],'input identity: '+role)
    require(post['input_hashes']['assets/chemeleon_mp.pt']==plan['pretrained_backbone_sha256']==post['original_checkpoint_sha256'],'checkpoint changed')
    for phase in ['cuda01','train01']:
        require(load(f/'raw'/f'{phase}-exit.json')['exit_code']==0,'phase exit failure: '+phase)
        require(load(f/'raw'/f'guard-{phase}.json')['restrict_self_return_code']==0,'write guard not established')
        for observation in load(f/'raw'/f'{phase}-prelaunch.json'):
            g=ET.fromstring(observation['health_xml']).find('gpu')
            require(g.findtext('uuid')==plan['gpu_uuid'] and g.findtext('gpu_recovery_action')=='None' and g.findtext('fb_memory_usage/used')=='0 MiB' and g.findtext('utilization/gpu_util')=='0 %','prelaunch GPU unavailable')
    audit=load(run/'acceptance/audit-final-fetch.json')
    require(not audit['manifest_mismatches'] and len(audit['traces'])==2,'trace inventory incomplete')
    for trace in audit['traces']:
        require(not trace['outside_mutation_evidence'] and trace['unresolved_count']==0 and not trace['pending_at_eof'],'write-scope trace not cleared')
    before=load(a/'encoder-before.json');after=load(a/'encoder-after.json')
    require(before==after and len(before['tensors'])>0,'encoder changed or empty')
    h=hashlib.sha256()
    for name,item in sorted(before['tensors'].items()):h.update(name.encode()+b'\0'+json.dumps(item,sort_keys=True).encode()+b'\0')
    require(h.hexdigest()==before['sha256'],'encoder state manifest digest inconsistent')
    e=load(a/'training-evidence.json')
    for name in ['encoder_state_unchanged','encoder_gradients_none','encoder_eval','encoder_parameters_frozen','encoder_checkpoint_sha256_unchanged']:require(e[name] is True,'runtime freeze: '+name)
    o=e['optimizer_separation'];require(o['optimizer_exactly_head'] and o['optimizer_encoder_intersection']==0 and o['encoder_requires_grad_count']==0 and not o['encoder_training'],'optimizer separation')
    require(e['gpu_uuid']==plan['gpu_uuid'] and e['head_output_devices']==['cuda:0'],'CUDA identity')
    require(e['optimizer_steps']>0 and e['nonzero_gradient_steps']==e['optimizer_steps'],'head never learned')
    require(e['official_validation_scoring'] is False and e['test_fitting'] is False,'label boundary')
    require(e['encoder_forward_events'] and all(not x['grad_enabled'] and not x['training'] and all(d=='cuda:0' for d in x['devices']) for x in e['encoder_forward_events']),'encoder forward missing/grad-enabled')
    initial=tensor_storage(a/'head-initial.pt');final=tensor_storage(a/'caco2_wang-head.pt')
    differences=[]
    for x,y in zip(initial,final):
        require(len(x)==len(y),'head tensor shape changed');v=array.array('f');w=array.array('f');v.frombytes(x);w.frombytes(y)
        if sys.byteorder!='little':v.byteswap();w.byteswap()
        require(all(math.isfinite(z) for z in v) and all(math.isfinite(z) for z in w),'nonfinite head')
        differences.append(max(abs(c-d) for c,d in zip(v,w)))
    require(all(x>0 for x in differences),'unchanged head tensor')
    preds=table(a/'predictions.csv');require(len(preds)==273,'prediction count')
    for split,name in [('valid','valid.csv'),('test','test.csv')]:
        expected=table(f/'input'/name);actual=[x for x in preds if x['split']==split]
        require(len(actual)==len(expected),'split count')
        for i,(x,y) in enumerate(zip(actual,expected)):
            require(x['task']=='caco2_wang' and x['row_index']==str(i) and x['Drug_ID']==y['Drug_ID'] and x['Drug']==y['Drug'] and math.isfinite(float(x['y_pred'])),'row identity or finite prediction')
        require(e['reload_checks'][split]['rows']==len(expected) and e['reload_checks'][split]['max_abs_prediction_difference']<=1e-5,'reload mismatch')
    require(all(p['status'] in ['gone','pid_reused','exited_zombie'] for p in post['own_processes']),'own process still running')
    require(all(int(r[1]) not in {p['pid'] for p in post['own_processes'] if p['status']!='pid_reused'} for r in csv.reader(post['apps'].splitlines()) if r),'own GPU process persists')
    g=ET.fromstring(post['gpu_health']).find('gpu');require(g.findtext('uuid')==plan['gpu_uuid'] and g.findtext('gpu_recovery_action')=='None','post-run GPU health')
    return {'checks_passed':True,'run_id':plan['run_id'],'returned_files':len(manifest),'encoder_state_sha256':before['sha256'],'encoder_state_tensors':len(before['tensors']),'head_tensor_max_abs_changes':differences,'optimizer_steps':e['optimizer_steps'],'prediction_rows':len(preds),'own_processes_checked':len(post['own_processes']),'limitations':['仅参考格式的一致性及已保存证据检查；不能代替主控审读执行代码、原始轨迹与来源。','未读取私有验证标签，未做赛事评分；不证明共享/并行或全服务器零影响。','不执行返回代码，不反序列化 pickle；直接比较 checkpoint ZIP 的原始张量存储。']}
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: python3 -B check_evidence.py /absolute/run')
    print(json.dumps(check(sys.argv[1]),ensure_ascii=False,indent=2))
