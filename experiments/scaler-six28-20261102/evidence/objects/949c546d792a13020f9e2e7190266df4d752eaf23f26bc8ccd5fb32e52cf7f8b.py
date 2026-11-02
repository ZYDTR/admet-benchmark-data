import hainan,json
from pathlib import Path
p=Path(__file__).resolve().parent
d=json.loads(hainan.once((p/'runtime-revision01.py').read_text(),'runtime-revision01',timeout=60))
(p/'runtime-revision01-result.json').write_text(json.dumps(d,indent=2)+'\n')
(p/'runtime-manifest.json').write_text(json.dumps(d['manifest'],indent=2)+'\n');print(json.dumps({'changes':d['changes']}))
