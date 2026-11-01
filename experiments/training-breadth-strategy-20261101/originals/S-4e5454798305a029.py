"""Independent read-only delivery checks using CSV/ZIP/JSON standard library; no model execution."""
import csv,hashlib,json,math,zipfile
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]

def validate(artifact_dir,remote_inventory):
    plan=json.loads((RUN/'PLAN.json').read_text());art=Path(artifact_dir)
    evidence=json.loads((art/'training-evidence.json').read_text())
    before=json.loads((art/'encoder-before.json').read_text());after=json.loads((art/'encoder-after.json').read_text())
    assert before==after and evidence['encoder_state_unchanged']
    assert evidence['encoder_parameters_frozen'] and evidence['encoder_eval'] and evidence['encoder_gradients_none']
    assert evidence['optimizer_separation']['optimizer_exactly_head'] and evidence['optimizer_separation']['optimizer_encoder_intersection']==0
    assert evidence['optimizer_steps']==evidence['nonzero_gradient_steps']>0
    assert evidence['optimizer_steps']==evidence['epochs_run']*math.ceil(evidence['fit_rows']/plan['head_config']['batch_size'])
    assert evidence['fit_rows']+evidence['internal_validation_rows']==637
    assert evidence['head_initial_sha256']!=evidence['head_final_sha256'] and any(v>0 for v in evidence['head_changed_max_abs_by_tensor'].values())
    assert evidence['device']=='cuda:0' and evidence['head_output_devices']==['cuda:0']
    assert evidence['encoder_forward_events'] and all(not e['grad_enabled'] and not e['training'] and all(x=='cuda:0' for x in e['devices']) for e in evidence['encoder_forward_events'])
    with (art/'predictions.csv').open(newline='') as f:reader=csv.DictReader(f);cols=reader.fieldnames;pred=list(reader)
    assert cols==['task','split','row_index','Drug_ID','Drug','y_pred'] and len(pred)==273
    coverage={}
    for inp in plan['inputs']:
        if inp['role']=='train':continue
        p=Path(inp['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==inp['sha256']
        with p.open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
        split={'validation':'valid','test':'test'}[inp['role']];out=[r for r in pred if r['split']==split]
        assert len(out)==len(rows)==inp['rows']
        for i,(x,y) in enumerate(zip(rows,out)):
            assert y['task']=='caco2_wang' and int(y['row_index'])==i and x['Drug_ID']==y['Drug_ID'] and x['Drug']==y['Drug'] and math.isfinite(float(y['y_pred']))
        coverage[split]={'rows':len(out),'all_original_rows_and_order_preserved':True,'finite_predictions':True,'min_prediction':min(float(r['y_pred']) for r in out),'max_prediction':max(float(r['y_pred']) for r in out)}
    def storage_bytes(p):
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            return {n.split('/data/',1)[1]:z.read(n) for n in z.namelist() if '/data/' in n}
    init=storage_bytes(art/'head-initial.pt');final=storage_bytes(art/'caco2_wang-head.pt')
    assert set(init)==set(final) and len(init)==4
    changes={k:{'size_initial':len(v),'size_final':len(final[k]),'initial_sha256':hashlib.sha256(v).hexdigest(),'final_sha256':hashlib.sha256(final[k]).hexdigest(),'changed':v!=final[k]} for k,v in init.items()}
    assert all(x['changed'] for x in changes.values())
    asset=next(x for x in remote_inventory['files'] if x['path']=='assets/chemeleon_mp.pt');assert asset['sha256']==plan['pretrained_backbone_sha256']
    result={'status':'pass','official_train_Y_used':True,'official_validation_labels_read':False,'test_labels_read':False,'model_executed_locally':False,'encoder_state_json_equal':True,'encoder_state_sha256':before['sha256'],'optimizer_steps':evidence['optimizer_steps'],'head_zip_storage_checks':changes,'coverage':coverage,'asset_sha256':asset['sha256'],'source':'Byte-level checkpoint ZIP comparison and fixed-input CSV identities, not accuracy scoring'}
    (RUN/'operator/artifact-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
