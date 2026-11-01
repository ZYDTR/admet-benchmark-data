import concurrent.futures,datetime,hashlib,json,subprocess,time,urllib.request
from pathlib import Path
T=Path(__file__).resolve().parents[1]; pub=T/'retrieval/publication'; repo=pub/'repository'
start=time.monotonic(); at=datetime.datetime.now(datetime.timezone.utc).isoformat()
a=json.loads((T/'control/PUBLISH_APPROVAL.json').read_text()); push=json.loads((pub/'push-result.json').read_text()); commit=push['commit']; baseline=push['baseline']; prefix='experiments/public-repo-20261031/'
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
changes=[x.split('\t',1) for x in git('diff','--name-status',baseline,commit).decode().splitlines()]
assert len(changes)==393 and all(s=='A' and p.startswith(prefix) for s,p in changes)
approved={f['path']:f for f in a['files']}
assert {p[len(prefix):] for s,p in changes}==set(approved)
checked=[]
for name,expected in approved.items():
    b=git('show',commit+':'+prefix+name); sha=hashlib.sha256(b).hexdigest()
    assert sha==expected['sha256'] and len(b)==expected['bytes'],name
    checked.append({'path':name,'sha256':sha,'bytes':len(b)})
# Other existing files must retain their Git objects and modes.
def tree(ref):
    return {line.split('\t',1)[1]:line.split('\t',1)[0] for line in git('ls-tree','-r',ref).decode().splitlines()}
old=tree(baseline);new=tree(commit);assert all(new.get(p)==v for p,v in old.items())
paths=['START_HERE.md','ANALYSIS_BUNDLE.md','manifest.json','rules/CURRENT_RULES.md','runs/hainan-frozen-training-20261031/artifacts/predictions.csv','runs/hainan-skill-follow-20261031/artifacts/predictions.csv']
base=f'https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/{commit}/{prefix}'
def fetch(name):
    t=time.monotonic();req=urllib.request.Request(base+name,headers={'User-Agent':'ADMET-controller-readback','Accept-Encoding':'identity'})
    with urllib.request.urlopen(req,timeout=30) as r: b=r.read();status=r.status
    sha=hashlib.sha256(b).hexdigest();assert status==200 and sha==approved[name]['sha256'] and len(b)==approved[name]['bytes'],name
    return {'path':name,'url':base+name,'status':status,'bytes':len(b),'sha256':sha,'seconds':time.monotonic()-t}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: reads=list(pool.map(fetch,paths))
r={'checked_at':at,'commit':commit,'baseline':baseline,'all_393_committed_files_match_approval':True,'original_tree_unchanged':True,'changed_paths_add_only':True,'anonymous_controller_sample':reads,'checked_files':checked,'seconds':time.monotonic()-start,'publisher_full_anonymous_verification_pending':True}
(T/'acceptance/independent-publication.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n'); print(json.dumps({k:v for k,v in r.items() if k not in ['checked_files','anonymous_controller_sample']},indent=2))
