"""Read aggregate evidence and verify arithmetic. No model/code/label loading or writes."""
from pathlib import Path
import argparse,json,statistics,math
from decimal import Decimal,localcontext

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);root=parser.parse_args().root
 read=lambda p:json.loads((root/p).read_text(encoding='utf-8'))
 rows=read('evidence/scores24-transcription.json')['rows'];expected=read('checks/scores24-recomputed.json')
 assert len(rows)==24
 for out in expected:
  r=[x for x in rows if x['task']==out['task']];vals={h:[x['value'] for x in sorted(r,key=lambda x:x['seed']) if x['config_tag']==h] for h in ['H0','H1']}
  a,b=vals['H0'],vals['H1'];d=[y-x for x,y in zip(a,b)]
  actual={'H0_mean':statistics.mean(a),'H1_mean':statistics.mean(b),'H0_sample_sd':statistics.stdev(a),'H1_sample_sd':statistics.stdev(b),'mean_paired_delta':statistics.mean(d),'sample_sd_paired_delta':statistics.stdev(d)}
  for k,v in actual.items():assert math.isclose(v,out[k],rel_tol=0,abs_tol=1e-14),(out['task'],k,v,out[k])
  sign=-1 if out['direction']=='minimize' else 1
  assert sum(sign*x>0 for x in d)==out['H1_improved_seeds']
  with localcontext() as ctx:
   ctx.prec=50;da=[Decimal(str(x)) for x in a];db=[Decimal(str(x)) for x in b];dd=[y-x for x,y in zip(da,db)]
   mean=sum(dd)/2;sd=abs(dd[1]-dd[0])/Decimal(2).sqrt()
   assert abs(float(mean)-out['mean_paired_delta'])<1e-14 and abs(float(sd)-out['sample_sd_paired_delta'])<1e-14
 base=read('evidence/mini22-transcription.json');assert len(base)==22
 assert sum(x['n_valid'] for x in base)==11735
 assert sum(x['n'] for x in rows)==27740
 assert sum(x['n_valid'] for x in expected)==6935
 print(json.dumps({'status':'pass','aggregate_scores':24,'tasks_current':6,'tasks_historical':22,'valid_rows_current':6935,'scored_prediction_rows':27740,'valid_rows_22':11735,'new_training':0,'model_inference':0,'row_validY_read':0}))
if __name__=='__main__':main()
