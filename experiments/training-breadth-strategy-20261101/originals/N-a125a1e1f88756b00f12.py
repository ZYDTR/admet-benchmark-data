"""Actual outer and held-parent subprocess regressions, never ML/remote."""
import datetime,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    suite=HERE/'raw/offline'/uuid.uuid4().hex[:10];suite.mkdir(parents=True)
    cases=[]
    for name,code in [('bad_gpu',78),('query_exit9',78),('prepare_error',78),('budget',124),('ambiguous',70),('watch',78)]:
        root=suite/name;root.mkdir()
        command=[sys.executable,'-I','-B',str(HERE/'offline_entry.py'),str(root),name]
        start=datetime.datetime.now(datetime.timezone.utc).isoformat();clock=time.monotonic()
        p=subprocess.run(command,capture_output=True,text=True,timeout=15)
        record={'argv':command,'started_at':start,'elapsed_seconds':time.monotonic()-clock,
                'true_OS_exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
        (root/'actual-process.json').write_text(json.dumps(record,indent=2)+'\n')
        assert p.returncode==code,(name,record)
        outcome=json.loads((root/'outer-outcome.json').read_text())
        assert outcome['returncode']==code and outcome['elapsed_seconds']>0
        assert (root/'batch-invoked').exists()==(name=='ambiguous')
        if name in ('bad_gpu','watch'):
            raw=json.loads((root/'query-00.json').read_text())
            assert raw['actual_OS_exit']==0 and '<gpu_util>100 %</gpu_util>' in raw['stdout']
            assert 'raw stderr retained' in raw['stderr']
            assert 'utilization/gpu_util' in outcome['error'] and not outcome['batch_invocation_attempted']
        if name=='query_exit9':assert json.loads((root/'query-00.json').read_text())['actual_OS_exit']==9
        if name=='ambiguous':assert outcome['release_verified'] is None
        if name=='watch':
            waited=json.loads((root/'watch-actual-exit.json').read_text())
            assert waited['actual_outer_OS_exit']==78 and waited['release_verified'] is True
        cases.append({'case':name,'passed':True,'true_OS_exit':p.returncode})
    command=[sys.executable,'-I','-B',str(HERE/'outer.py'),'--fixture','bad_gpu']
    p=subprocess.run(command,capture_output=True,text=True);assert p.returncode==78
    (HERE/'raw/production-fixture-rejection.json').write_text(json.dumps({'argv':command,'actual_OS_exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})+'\n')
    original=HERE.parent;manifest=json.loads((original/'evidence-manifest.json').read_text())
    for item in manifest['files']:
        path=original/item['path'];assert path.stat().st_size==item['size'] and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
    result={'passed':True,'actual_subprocess_cases':cases,'production_fixture_bypass_rejected':True,
            'original_immutable_files_verified':len(manifest['files']),'remote_operations':False,'ML_training':False}
    (HERE/'raw/test-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
