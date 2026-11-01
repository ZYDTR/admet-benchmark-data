import importlib.util,json,os,sys,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
RUNTIME=HERE.parents[2]/'runtime/source/runtime-v1'
sys.path.insert(0,str(RUNTIME))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('old_scan',HERE/'original-resource_checks.py');new=load('new_scan',HERE/'resource_checks.py')
def root(name):
 p=HERE/'fixtures'/name;p.mkdir(parents=True);(p/'raw').mkdir();(p/'artifacts').mkdir();return p
results=[]
for label,mod,expected in [('original',old,'FileNotFoundError'),('candidate',new,39)]:
 p=root('rename-'+label);tmp=p/'raw/worker-start.json.0123456789abcdef0123456789abcdef.tmp';tmp.write_bytes(b'x'*39);real=mod.safe;called=[]
 def race(r,path,existing=False):
  if Path(path)==tmp and tmp.exists():os.replace(tmp,p/'raw/worker-start.json');called.append(1)
  return real(r,path,existing)
 mod.safe=race
 try:got=mod.result_bytes(p)
 except FileNotFoundError:got='FileNotFoundError'
 finally:mod.safe=real
 assert got==expected and len(called)==1,(label,got)
 results.append({'case':'exact_atomic_replace_'+label,'result':got,'passed':True})
for kind in ['symlink','hardlink','permission','missing_root','missing_output_root','persistent_churn','quota']:
 p=root(kind);f=p/'raw/evidence';f.write_bytes(b'x'*100);real=new.safe;calls=[]
 if kind=='symlink':(p/'raw/link').symlink_to(f)
 if kind=='hardlink':os.link(f,p/'raw/link')
 if kind=='missing_root':p.rename(p.with_name(kind+'-moved'))
 if kind=='missing_output_root':(p/'artifacts').rmdir()
 if kind in ['permission','persistent_churn']:
  def fault(r,path,existing=False):
   if Path(path)==f and existing:
    calls.append(1)
    if kind=='permission':raise PermissionError(13,'injected denial',str(f))
    raise FileNotFoundError(2,'injected concurrent disappearance',str(f))
   return real(r,path,existing)
  new.safe=fault
 try:
  amount=new.result_bytes(p)
  if kind=='quota':new.enforce_observation({'tree_rss_bytes':0,'result_bytes':amount,'apps_csv':''},{'ram_target_gib':1,'result_budget_gib':1e-9,'gpu_peak_target_mib':4096},'GPU-fixture',[])
 except (ValueError,OSError,RuntimeError) as err:
  if kind=='permission':assert isinstance(err,PermissionError) and len(calls)==1
  if kind=='persistent_churn':assert isinstance(err,FileNotFoundError) and len(calls)==3
  results.append({'case':kind,'error_type':type(err).__name__,'calls':len(calls),'passed':True})
 else:raise AssertionError('failure not preserved: '+kind)
 finally:new.safe=real
p=root('normal');(p/'raw/nested').mkdir();(p/'raw/nested/a').write_bytes(b'a'*123);(p/'artifacts/b').write_bytes(b'b'*321);audit=[]
assert new.result_bytes(p,audit.append)==444
results.append({'case':'complete_nested_bytes','result':444,'audit':audit,'passed':True})
(HERE/'test-results.json').write_text(json.dumps({'passed':True,'tests':results},indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(results)}))
