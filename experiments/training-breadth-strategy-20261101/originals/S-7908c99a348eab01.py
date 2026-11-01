"""Independent exact Git-tree, anonymous-byte and reading-binding audit."""
import concurrent.futures, datetime, hashlib, json, subprocess, time, urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent
C=H.parents[1]; T=C/'retrieval'; P=T/'publication'; REPO=P/'repository'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def main():
    start=time.monotonic();r=read(P/'publication-receipt.json');m=read(T/'candidate-manifest.json')
    assert sha((P/'publication-receipt.json').read_bytes())=='cde25ce13b96ac0da11f228087f5dcb93eda0a30d5d736c69f84a8943a43c36f'
    assert r['candidate_manifest_sha256']==sha((T/'candidate-manifest.json').read_bytes())
    commit=r['commit_sha'];parent=r['actual_parent_commit'];prefix=r['prefix']
    assert git('rev-parse',commit+'^').decode().strip()==parent==m['expected_base']
    diff=git('diff-tree','--no-commit-id','--name-status','-r',commit).decode().splitlines()
    expected={e['repository_path']:e for e in m['files']}
    assert set(diff)=={'A\t'+k for k in expected} and len(diff)==144
    for path,e in expected.items():
        blob=git('show',commit+':'+path);assert len(blob)==e['bytes'] and sha(blob)==e['sha256']
    assert {x['path'] for x in r['per_file']}==set(expected)
    for e in r['per_file']:
        x=expected[e['path']];assert e['sha256']==x['sha256'] and e['bytes']==x['bytes']
        b=(T/e['readback_local_file']).read_bytes();assert sha(b)==e['sha256'] and len(b)==e['bytes']
    original=read(T/'candidate/reading-contract.json');bound=read(P/'published-reading-contract.json')
    assert len(original['requirements'])==len(bound['requirements'])==66
    for a,b in zip(original['requirements'],bound['requirements']):
        assert a['entry_id']==b['entry_id'] and a['source_version']['sha256']==b['source_version']['sha256']
        if a.get('uri_template'):assert b['uri']==a['uri_template'].replace('{publication_commit}',commit)
        else:assert b['uri']==a['uri']
    # Independent anonymous GET of every approved object, no cookies/authentication.
    def fetch(e):
        uri='https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/'+commit+'/'+e['repository_path']
        errors=[]
        for attempt in range(1,4):
            try:
                with urllib.request.urlopen(urllib.request.Request(uri,headers={'User-Agent':'ADMET-controller-verification'}),timeout=25) as f:b=f.read();status=f.status;actual=f.geturl()
                assert status==200 and actual==uri and len(b)==e['bytes'] and sha(b)==e['sha256'],e['path']
                return {'path':e['path'],'uri':uri,'bytes':len(b),'sha256':sha(b),'attempts':attempt,'prior_errors':errors}
            except (OSError,TimeoutError) as ex:
                errors.append(type(ex).__name__+': '+str(ex))
                if attempt==3:raise
                time.sleep(attempt)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(fetch,m['files']))
    out={'state':'independently_accepted','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':commit,'parent':parent,'exact_additions':144,'bytes':sum(x['bytes'] for x in results),'outside_prefix_changes':0,'local_git_blobs_verified':144,'executor_readback_files_rehashed':144,'independent_anonymous_GETs_verified':len(results),'reading_binding_items_verified':66,'seconds':time.monotonic()-start,'publication_receipt_sha256':sha((P/'publication-receipt.json').read_bytes()),'candidate_manifest_sha256':sha((T/'candidate-manifest.json').read_bytes()),'per_file':results,'Pro_read_verified':False}
    (H/'result.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='per_file'},indent=2))
if __name__=='__main__':main()
