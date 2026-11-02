import hainan
from pathlib import Path
p=Path(__file__).resolve().parent
out=hainan.read("import os,json\nfrom pathlib import Path\nR=Path('task-storage://admet/scaler-six28-20261102');assert os.getuid()==1012\nprint(json.dumps({n:(R/'raw'/n).read_text() for n in ['cpu-check-exit.json','cpu-check.stderr','cpu-check.stdout','cpu-check-identity.json']}))\n",'read-cpu-error01',timeout=40)
(p/'cpu-error01.json').write_bytes(out);print(out.decode())
