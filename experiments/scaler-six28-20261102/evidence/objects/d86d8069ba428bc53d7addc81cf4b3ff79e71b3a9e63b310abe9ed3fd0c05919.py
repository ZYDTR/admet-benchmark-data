import hainan,json
from pathlib import Path
p=Path(__file__).resolve().parent
assert (p/'runtime-revision01-result.json').exists()
out=hainan.once((p/'measure28.py').read_text(),'train02',timeout=7400)
(p/'train02-result.json').write_bytes(out);print(out.decode())
