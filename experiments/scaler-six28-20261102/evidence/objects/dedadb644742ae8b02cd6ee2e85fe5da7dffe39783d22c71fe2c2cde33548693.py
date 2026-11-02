import hainan,json,sys
from pathlib import Path
p=Path(__file__).resolve().parent;tag=sys.argv[1]
out=hainan.read((p/'progress.py').read_text(),tag,timeout=50)
(p/(tag+'.json')).write_bytes(out);print(out.decode())
