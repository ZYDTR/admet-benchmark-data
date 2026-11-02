import hainan,json,xml.etree.ElementTree as ET
from pathlib import Path
p=Path(__file__).resolve().parent
out=hainan.read((p/'postcheck01.py').read_text(),'postcheck01',timeout=60)
(p/'postcheck01.json').write_bytes(out)
d=json.loads(out);g=ET.fromstring(d['gpu_query']['stdout']).find('gpu');summary={'at':d['at'],'registered_released_lifetimes':len(d['jobs']),'GPU_recovery':g.findtext('gpu_recovery_action'),'GPU_used':g.findtext('fb_memory_usage/used'),'GPU_util':g.findtext('utilization/gpu_util'),'GPU_PIDs':[x.findtext('pid') for x in g.findall('processes/process_info')],'cache_unchanged_files':d['original_cache_unchanged_files'],'environment_metadata_unchanged':d['shared_environment_metadata_unchanged'],'CPU_verification':{k:v for k,v in d['independent-CPU-verification.json'].items() if k!='runs'},'worker_peaks':{k:v for k,v in d['study-complete.json'].items() if 'peak' in k}}
(p/'postcheck01-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
