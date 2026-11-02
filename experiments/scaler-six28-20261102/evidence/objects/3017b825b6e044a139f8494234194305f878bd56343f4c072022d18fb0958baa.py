import sys,pathlib,json,hashlib,io,importlib.util,ast
import numpy as np
root=pathlib.Path('/workspace/context-infrastructure/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/preparation/packet');sys.path.insert(0,str(root/'output/src'))
from admet_breadth import cache as c,migration as m
from admet_breadth.common import CHEMELEON_SHA256,FEATURE_DIM,GLOBAL_FILL_VALUE,row_identity_sha256,array_digest
X=np.zeros((2,FEATURE_DIM),dtype=np.float32); X[0,0]=1;X[1,0]=2; mask=np.array([True,True],dtype=np.bool_);rows=[{'Drug_ID':'a','Drug':'C'},{'Drug_ID':'b','Drug':'CC'}];src='a'*64;task='ames';split='train';env=m.current_environment()
def npbytes(a):
 q=io.BytesIO();np.save(q,a,allow_pickle=False);return q.getvalue()
store={'arr':npbytes(X),'mask':npbytes(mask)}
def sha(k):return hashlib.sha256(store[k]).hexdigest()
meta={'contract':{'version':1,'source_csv_sha256':src,'row_identity_sha256':row_identity_sha256(rows),'n_rows':2,'feature_dim':FEATURE_DIM,'fill_value':GLOBAL_FILL_VALUE,'task':task,'split':split,'encoder_checkpoint_sha256':CHEMELEON_SHA256,'implementation_sha256':{'encoder.py':env['implementation_sha256']['encoder.py']},'packages':{}},'files':{'arr':sha('arr'),'mask':sha('mask')},'identity':{'features':array_digest(X),'parse_mask':array_digest(mask),'parsed_true_count':2,'unparsed_row_indices':[]}}
class Mem:
 def __init__(self,key):self.key=key
 def is_file(self):return True
 def read_text(self,**kwargs):return json.dumps(meta)
 def __str__(self):return self.key
arr,maskp,metap=Mem('arr'),Mem('mask'),Mem('meta')
c.cache_paths=lambda *_:(arr,maskp,metap);m.cache_paths=lambda *_:(arr,maskp,metap);original_sha256_file=c.sha256_file;c.sha256_file=lambda x:sha(x.key) if isinstance(x,Mem) else original_sha256_file(x);m.sha256_file=lambda x:sha(x.key) if isinstance(x,Mem) else original_sha256_file(x);original_np_load=np.load;np.load=lambda x,**kwargs:original_np_load(io.BytesIO(store[x.key]),**kwargs)
clean,_=c.load_raw_cache('/synthetic',task,split,rows,src,allow_migrated_legacy=True);X2=X.copy();X2[0,0]=7;store['arr']=npbytes(X2);meta['files']['arr']=sha('arr');meta['identity']['features']=array_digest(X2)
try:
 altered,_=c.load_raw_cache('/synthetic',task,split,rows,src,allow_migrated_legacy=True);self_consistent_modified_raw_accepted=bool(altered[0,0]!=clean[0,0])
except Exception:self_consistent_modified_raw_accepted=False
np.load=original_np_load
spec=importlib.util.spec_from_file_location('independent_assoc',root/'output/tests/association_diagnostic.py');assoc=importlib.util.module_from_spec(spec);spec.loader.exec_module(assoc);tie_result=assoc.spearman(np.array([2.,2.,2.]),np.array([1.,2.,3.]));constant_spearman_returned_non_none=tie_result is not None
A=np.array([[4.,1.],[4.,3.]],dtype=np.float32);sc=c.fit_feature_scaler(A,[0,1],{'method':c.LEGACY_METHOD});raw_std=A.std(axis=0,ddof=0);reported_count=int((sc.std<=1e-8).sum());actual_count=int((raw_std<1e-8).sum());constant_count_wrong=reported_count!=actual_count
source=(root/'output/tests/association_diagnostic.py').read_text();tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');asserts=[n for n in ast.walk(fn) if isinstance(n,ast.Assert)];identity_checks=[ast.unparse(n.test) for n in asserts];only_length_asserted=any('len(preds)' in x for x in identity_checks) and not any('row_index' in x or 'Drug_ID' in x for x in identity_checks)
print(json.dumps({'modified_raw_and_metadata_accepted':self_consistent_modified_raw_accepted,'constant_vector_spearman_not_undefined':constant_spearman_returned_non_none,'constant_dimension_count_wrong':constant_count_wrong,'association_identity_only_length_asserted':only_length_asserted,'training_steps':0,'loaded_model_weights':False}))
from admet_breadth.pipeline import TaskPipeline
legacy=TaskPipeline.__new__(TaskPipeline);legacy.task='ames';legacy.kind='classification';legacy.config=None;legacy.scaler_policy=None;legacy.transform_identity=None;legacy.task_metrics={}
try:
 legacy._require_config();legacy_default_without_config='accepted'
except Exception as e:
 legacy_default_without_config=type(e).__name__+': '+str(e)
print(json.dumps({'preexisting_legacy_pipeline_without_config':legacy_default_without_config}))
from admet_breadth.trainer import validate_config,evaluate_stop
from admet_breadth.metrics import EarlyStopMonitor,load_task_metrics
from admet_breadth.cache import TargetScaler
packet_task=json.loads((root/'TASK.json').read_text());metric_contract=load_task_metrics(root/'input/task-metrics.json');valid_count=0
for item in packet_task['configs']:
 cfg=json.loads((root/item['path']).read_text());validate_config(cfg,metric_contract);valid_count+=1
assert valid_count==28
A=np.array([[4.,2.,8.],[4.,2.0004,8.04]],dtype=np.float32);raw=A.std(axis=0,ddof=0);base=np.where(raw<1e-8,np.float32(1.),raw)
for floor in (None,0.001,0.01):
 policy=None if floor is None else {'method':c.FLOOR_METHOD,'denominator_floor':floor}
 sf=c.fit_feature_scaler(A,[0,1],policy);expected=base if floor is None else np.maximum(base,np.float32(floor));assert np.array_equal(sf.std,expected);assert sf.std[0]==1.0
 copy=c.FeatureScaler.from_dict(sf.to_dict());assert np.array_equal(copy.apply(A),sf.apply(A))
mon=EarlyStopMonitor('MAE','minimize');r=evaluate_stop('regression',np.array([0.,1.,2.]),[10.,12.,14.],mon,1,TargetScaler(mean=10.,std=2.));assert r['value']==0.
print(json.dumps({'twenty_eight_actual_configs_production_validation':'pass','synthetic_floor_constant_and_reload':'pass','raw_scale_single_inverse_synthetic':'pass','training_steps':0}))
