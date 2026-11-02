import os,json
from pathlib import Path
R=Path('task-storage://admet/scaler-six28-20261102');assert os.getuid()==1012
print(json.dumps({n:(R/'raw'/n).read_text() for n in ['cpu-check02-exit.json','cpu-check02.stderr','cpu-check02.stdout','cpu-check02-identity.json']}))
