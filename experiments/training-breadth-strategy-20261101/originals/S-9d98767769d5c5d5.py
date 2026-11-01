from pathlib import Path
import csv,json,subprocess,sys,os,shutil,copy
A=Path(__file__).resolve().parent; R=A.parent; W=A/'work'; L=A/'logs'; L.mkdir(exist_ok=True)
for role in ('model','data-eval'):
    dst=W/role/'output'
    if not dst.exists():
        shutil.copytree(R/'originals'/role/'output',dst,ignore=shutil.ignore_patterns('__pycache__'))
        for p in dst.rglob('*'):
            if p.is_file(): p.chmod(0o644)
    inp=W/role/'input'
    if not inp.exists(): inp.symlink_to(R/role/'input',target_is_directory=True)
D=W/'data-eval'/'output'; S=A/'synthetic'; F=A/'fixtures'; F.mkdir(exist_ok=True)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(A/'tmp')); (A/'tmp').mkdir(exist_ok=True)
rows=[]
def run(name,args,expected=0,cwd=D):
    p=subprocess.run([sys.executable,*map(str,args)],cwd=cwd,env=env,text=True,capture_output=True,timeout=60)
    (L/(name+'.log')).write_text(p.stdout+'\nSTDERR\n'+p.stderr)
    ok=p.returncode==0 if expected==0 else p.returncode!=0
    rows.append(dict(name=name,expected='accept' if expected==0 else 'reject',exit_code=p.returncode,pass_check=ok,log=str((L/(name+'.log')).relative_to(A))))
    return p
for role in ('model','data-eval'):
    run(role+'-selftests',['-m','unittest','discover','-s','tests','-v'],cwd=W/role/'output')
schema=D/'admet_eval/task_schema.json'; template=W/'data-eval/input/data/official/submission_template.csv'
si=F/'split-inputs.json'
run('make-split-inputs',['scripts/make_split_inputs.py','--schema',schema,'--out',si])
def dump(name,doc):
    p=F/name; p.write_text(json.dumps(doc,allow_nan=True)); return p
for p in S.glob('*.csv'):
    recs=[]
    for r in csv.DictReader(p.open()):
        recs.append(dict(task=r['task'],split=r['split'],row_index=int(r['row_index']),y_pred=float(r['y_pred'])))
    dump(p.stem+'.json',dict(schema_version=1,predictions=recs))
labels=[]
for p in sorted((S/'labels').glob('*.csv')):
    for i,r in enumerate(csv.DictReader(p.open())):
        labels.append(dict(task=p.stem,split='valid',row_index=i,y=float(r['Y'])))
lp=dump('labels.json',dict(schema_version=1,split_id='synthetic-fixed',labels=labels))
base=['scripts/score.py','--schema',schema,'--template',template,'--labels-json',lp]
for pred in sorted(F.glob('valid-*.json')):
    run('score-'+pred.stem,[*base,'--predictions',pred,'--split-inputs',si],0 if pred.stem=='valid-perfect' else 1)
run('score-required-csv',[*base,'--predictions',S/'valid-perfect.csv','--split-inputs',si])
class_task=next(t['task'] for t in json.loads(schema.read_text())['tasks'] if t['kind']=='classification')
for label,bad in [('fraction',0.5),('nan',float('nan')),('inf',float('inf'))]:
    v=copy.deepcopy(labels); next(x for x in v if x['task']==class_task)['y']=bad
    file=dump('labels-'+label+'.json',dict(schema_version=1,split_id='synthetic',labels=v))
    run('labels-'+label,['scripts/score.py','--schema',schema,'--template',template,'--labels-json',file,'--predictions',F/'valid-perfect.json','--split-inputs',si],1)
for mode in ('empty','truncated'):
    keep=[] if mode=='empty' else [x for x in labels if x['task']==class_task][:2]
    l=dump(mode+'-labels.json',dict(schema_version=1,split_id='synthetic',labels=keep))
    p=dump(mode+'-pred.json',dict(schema_version=1,predictions=[dict(task=x['task'],split=x['split'],row_index=x['row_index'],y_pred=x['y']) for x in keep]))
    run('default-'+mode,['scripts/score.py','--schema',schema,'--template',template,'--labels-json',l,'--predictions',p],1)
for typ,expected in [('json',0),('csv',0)]:
    dest=F/('submission-'+typ+'.csv')
    run('export-'+typ,['scripts/export_submission.py','--schema',schema,'--template',template,'--predictions',(F/'test-full.json' if typ=='json' else S/'test-full.csv'),'--output',dest],expected)
    if dest.exists():
        tr=list(csv.DictReader(template.open())); out=list(csv.DictReader(dest.open()))
        exact=len(out)==16379 and len(tr)==len(out) and all({k:v for k,v in t.items() if k!='y_pred'}=={k:v for k,v in o.items() if k!='y_pred'} for t,o in zip(tr,out))
        rows.append(dict(name='independent-export-fields-'+typ,pass_check=exact,rows=len(out)))
# Small format challenge: schema checking intentionally omitted only for custom tiny template test.
sys.path.insert(0,str(D)); from scripts.export_submission import export
small=F/'format-template.csv'; small.write_bytes(b'\xef\xbb\xbftask,drug_id,smiles,y_pred\r\n"ames","001","C",0\r\n')
sp=dump('format-pred.json',dict(schema_version=1,predictions=[dict(task='ames',split='test',row_index=0,y_pred=0.25)]))
so=F/'format-out.csv'; export(str(small),str(sp),str(so),None)
raw=so.read_bytes(); expect=small.read_bytes().replace(b',0\r\n',b',0.25\r\n')
rows.append(dict(name='non-prediction-format-byte-preservation',pass_check=raw==expect,expected=repr(expect),actual=repr(raw)))
from admet_eval import metrics as m
for name,args,expected in [('auroc-ties',('AUROC','classification',[0,1,0,1],[.5,.5,.5,.5]),.5),('ap-ties',('AUPRC','classification',[0,1,0,1],[.5,.5,.5,.5]),.5),('ap-single',('AUPRC','classification',[1,1],[.1,.2]),'undefined'),('auc-single',('AUROC','classification',[0,0],[.1,.2]),'undefined'),('spearman-constant',('Spearman','regression',[1,1],[.1,.2]),'undefined')]:
    try: value=m.compute(*args)
    except m.MetricUndefined: value='undefined'
    rows.append(dict(name=name,actual=value,expected=expected,pass_check=value==expected))
(A/'data-results.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
