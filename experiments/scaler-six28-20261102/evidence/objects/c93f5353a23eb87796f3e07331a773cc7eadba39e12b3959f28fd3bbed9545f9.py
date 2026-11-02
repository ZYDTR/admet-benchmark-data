import hainan
from pathlib import Path
p=Path(__file__).resolve().parent
out=hainan.once((p/'cpu-launch03.py').read_text(),'cpu-check03',timeout=300)
(p/'cpu-check-result.json').write_bytes(out);print(out.decode())
