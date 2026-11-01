from pathlib import Path
import json,copy,subprocess,sys,csv,os
A=Path(__file__).resolve().parent; F=A/'fixtures'; D=A/'work/data-eval/output'; S=D/'admet_eval/task_schema.json'; T=A/'work/data-eval/input/data/official/submission_template.csv'; base=json.loads((F/'test-full.json').read_text()); results=[]
for case in ('missing','duplicate','unknown','wrong-split','nan','inf','empty'):
    x=copy.deepcopy(base)
    if case=='missing': x['predictions'].pop()
    if case=='duplicate': x['predictions'].append(copy.deepcopy(x['predictions'][0]))
    if case=='unknown': x['predictions'][0]['task']='UNKNOWN'
    if case=='wrong-split': x['predictions'][0]['split']='valid'
    if case in ('nan','inf'): x['predictions'][0]['y_pred']=float(case)
    if case=='empty': x['predictions']=[]
    p=F/('test-'+case+'.json');p.write_text(json.dumps(x)); dest=F/('export-bad-'+case+'.csv')
    args=[sys.executable,str(D/'scripts/export_submission.py'),'--schema',str(S),'--template',str(T),'--predictions',str(p),'--output',str(dest)]
    proc=subprocess.run(args,cwd=D,text=True,capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),timeout=30)
    (A/'logs'/('export-bad-'+case+'.log')).write_text(proc.stdout+'\n'+proc.stderr)
    results.append(dict(case=case,exit_code=proc.returncode,pass_check=proc.returncode!=0 and not dest.exists()))
(A/'export-negatives.json').write_text(json.dumps(results,indent=2)); print(json.dumps(results))
