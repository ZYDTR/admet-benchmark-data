"""Host-only fixed grader. Never imports worker code or loads model checkpoints."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def rows(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write_private(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    path.chmod(0o600)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--predictions',required=True,type=Path)
    ap.add_argument('--run-id',required=True)
    args=ap.parse_args()
    if not args.run_id.replace('-','').replace('_','').isalnum():
        raise ValueError('invalid run ID')
    loc=json.loads((REPO/'adhoc_jobs/admet_sap_setup_20261029/minimal-revision/v6/private-vault-location.json').read_text())
    vault=Path(loc['vault'])
    out=vault/'evaluations'/args.run_id
    out.mkdir(parents=True,exist_ok=False,mode=0o700)
    out.parent.chmod(0o700)
    package=out/'fixed_scorer/admet_harness'
    package.mkdir(parents=True,mode=0o700)
    (package/'__init__.py').write_text('')
    fixed=REPO/'adhoc_jobs/admet_agent_harness/src/admet_harness'
    for name in ['evaluation.py','common.py']:
        shutil.copyfile(fixed/name,package/name)
    schema=out/'task_schema.json'
    shutil.copyfile(REPO/'adhoc_jobs/admet_agent_harness/competition/task_schema.json',schema)
    pred=out/'valid_predictions.csv'
    if args.predictions.is_symlink() or not args.predictions.is_file():
        raise ValueError('prediction must be ordinary file')
    if not 0 < args.predictions.stat().st_size <= 16 * 1024 * 1024:
        raise ValueError('prediction file exceeds bounded input size')
    pred_digest=digest(args.predictions)
    shutil.copyfile(args.predictions,pred)
    pred.chmod(0o600)
    if digest(pred)!=pred_digest:raise ValueError('prediction changed during copy')
    schema_data=json.loads(schema.read_text())
    tasks={t['task']:t for t in schema_data['tasks']}
    manifest=json.loads((vault/'label-vault-manifest.json').read_text())
    task_records={r['task']:r for r in manifest['records']}
    if set(tasks)!=set(task_records) or len(tasks)!=22:raise ValueError('task set mismatch')
    template=rows(ROOT/'execution/data/official/submission_template.csv')
    for r in template:
        if tasks[r['task']]['metric']!=r['metric']:raise ValueError('metric map mismatch')
    predictions={}
    with pred.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames != ['task','split','row_index','y_pred']:
            raise ValueError('invalid or duplicated CSV header')
        prediction_rows=list(reader)
    for r in prediction_rows:
        if set(r)!={'task','split','row_index','y_pred'} or r['split']!='valid':
            raise ValueError('invalid prediction schema or split')
        i=int(r['row_index']);yp=float(r['y_pred']);key=(r['task'],i)
        if key in predictions or r['task'] not in tasks or i<0 or not math.isfinite(yp):
            raise ValueError('invalid, duplicate or non-finite prediction')
        predictions[key]=yp
    joined=[];expected=set();verified=[]
    for task,rec in task_records.items():
        original=Path(rec['original_path']);blind=ROOT/'execution'/rec['agent_path']
        if original.is_symlink() or blind.is_symlink():raise ValueError('linked input')
        if digest(original)!=rec['original_sha256'] or digest(blind)!=rec['agent_sha256']:
            raise ValueError('label/projection digest mismatch')
        labels=rows(original);projected=rows(blind)
        if len(labels)!=len(projected) or len(labels)!=rec['rows']:raise ValueError('row count mismatch')
        for i,(a,b) in enumerate(zip(labels,projected)):
            if set(b)!={'Drug_ID','Drug'} or a['Drug_ID']!=b['Drug_ID'] or a['Drug']!=b['Drug']:
                raise ValueError('label/projection identity mismatch')
            key=(task,i);expected.add(key)
            if key not in predictions:raise ValueError('missing prediction row')
            y=float(a['Y'])
            if not math.isfinite(y):raise ValueError('nonfinite truth')
            if tasks[task]['kind']=='classification' and y not in (0,1):raise ValueError('nonbinary truth')
            joined.append({'task':task,'sample_id':f'{task}/validation/{i}','y_true':y,'y_pred':predictions[key]})
        verified.append({'task':task,'rows':len(labels),'original_sha256':rec['original_sha256'],
                         'projection_sha256':rec['agent_sha256']})
    if set(predictions)!=expected or len(joined)!=11735:raise ValueError('incomplete validation set')
    records=out/'records-with-private-labels.json'
    write_private(records,{'schema_version':1,'split_id':'official-valid-20261029-v6','records':joined})
    sys.path.insert(0,str(out/'fixed_scorer'))
    from admet_harness.evaluation import evaluate_records
    result=evaluate_records(schema,records)
    write_private(out/'scores.json',result)
    write_private(out/'receipt.json',{'prediction_sha256':pred_digest,'run_id':args.run_id,
        'validation_rows':11735,'verified_inputs':verified,'feedback_to_agents':'not_released',
        'scorer_files':{p.name:digest(p) for p in package.glob('*.py')},
        'schema_sha256':digest(schema),'worker_code_executed':False,'checkpoint_loaded':False})
    lines=['# CheMeleon 冻结底座首版：本地验证结果','',
        '固定单次配置；官方 train 内部90/10早停。未用官方 valid 标签训练或选参。',
        '宿主固定评分器核对22任务、11735行完整覆盖及原始行身份。AUPRC采用本地AP，官方总分与等价性未确认。',
        '精确结果只留在宿主私有区，不回传准备会话。','',
        '| 任务 | 指标 | 本地结果 | 验证行数 |','|---|---|---:|---:|']
    for task in sorted(result['tasks']):
        row=result['tasks'][task];val=f"{row['value']:.6g}" if row['value'] is not None else row['status']
        lines.append(f"| {task} | {row['metric']} | {val} | {row['n']} |")
    lines+=['','完整机器可读结果：[scores.json](scores.json)。没有计算官方总分，没有上传比赛。']
    (out/'validation-report.md').write_text('\n'.join(lines)+'\n');(out/'validation-report.md').chmod(0o600)
    print(json.dumps({'ok':True,'task_count':result['task_count'],'record_count':result['record_count'],
                      'private_report':str(out/'validation-report.md'),'scores':str(out/'scores.json')},ensure_ascii=False))

if __name__=='__main__':main()
