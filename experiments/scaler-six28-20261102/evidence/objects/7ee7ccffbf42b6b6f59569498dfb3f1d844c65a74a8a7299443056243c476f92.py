import hainan,json
from pathlib import Path
p=Path(__file__).resolve().parent
out=hainan.read((p/'probe01.py').read_text(),'probe01',timeout=90)
(p/'probe01.json').write_bytes(out)
d=json.loads(out);print(json.dumps({'identity':{k:d[k] for k in ['observed_at','hostname','uid','gid']},'cache_verified_files':len(d['cache']),'cpu_two':d['cpu']['chosen_two'],'gpu_queries':[{k:v for k,v in q.items() if k!='stdout'} for q in d['gpu_queries']],'gpu_inventory':d['gpu_queries'][0].get('stdout')}))
