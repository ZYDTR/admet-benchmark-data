"""Use exact admitted dependency signature; no target access or ML import."""
import ast, hashlib, importlib.util, inspect, json, os, sys, types
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 old=HERE.parent/'recovery-01';adapter=load('_actual_adapter',HERE.parent/'batch-package/source/production-adapter-v2/adapter_common.py')
 signature=inspect.signature(adapter.process_identity)
 native=types.ModuleType('process_state')
 native.native_identity=lambda pid:{'pid':pid,'fixture_native_identity':True}
 sys.modules['process_state']=native
 rows=[]
 for name,source in [('original',old/'outer.py'),('fixed',HERE/'outer.py')]:
  dest=HERE/'raw/contract'/name;dest.mkdir(parents=True)
  def record(n,v):(dest/n).write_text(json.dumps(v,indent=2)+'\n')
  def prepare():raise ValueError('reached actual identity dependency successfully')
  ctx=types.SimpleNamespace(identity=adapter.process_identity,record=record,prepare=prepare)
  actual=load('_outer_'+name,source).run_outer(ctx)
  outcome=json.loads((dest/'outer-outcome.json').read_text())
  expected=70 if name=='original' else 78
  assert actual==expected,(name,actual,outcome)
  assert ('missing 1 required positional argument' in outcome['error'])==(name=='original')
  invalid=[]
  for node in ast.walk(ast.parse(source.read_text())):
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='identity':
    try:signature.bind(*[object() for _ in node.args],**{k.arg:object() for k in node.keywords})
    except TypeError:invalid.append(node.lineno)
  assert (len(invalid)==2 if name=='original' else len(invalid)==0)
  rows.append({'source':name,'OS_process_test':False,'actual_function_return':actual,'actual_dependency':str(signature),'incompatible_calls':invalid,'error':outcome['error']})
 builder=load('_builder',HERE/'make_binding.py')
 observation={'passed':True,'selected':{'gpu_index':3,'gpu_uuid':'<REGISTERED_GPU>'}}
 bound=builder.build(observation,5363.641942024231,HERE/'binding-test-only')
 assert len(bound['profile_specs'])==6
 for item in bound['profile_specs']:
  path=HERE/'binding-test-only'/item['run_id']/item['profile'];profile=json.loads(path.read_text())
  base=json.loads((Path('<LOCAL_WORKSPACE>/adhoc_jobs/admet_training/runs')/item['run_id']/'admission/execution-profile.base.json').read_text())
  assert {k:v for k,v in profile.items() if k not in ('gpu_index','gpu_uuid','execution_enabled','stage')}=={k:v for k,v in base.items() if k not in ('gpu_index','gpu_uuid','execution_enabled','stage')}
  assert hashlib.sha256(path.read_bytes()).hexdigest()==item['profile_sha256']
 result={'passed':True,'dependency_contract_cases':rows,'six_profile_bindings_derived_and_checked':True,'test_binding_not_authorized_for_deploy':True,'real_Linux_identity_verified':False,'remote_operations':False,'ML':False}
 (HERE/'raw/actual-contract-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
