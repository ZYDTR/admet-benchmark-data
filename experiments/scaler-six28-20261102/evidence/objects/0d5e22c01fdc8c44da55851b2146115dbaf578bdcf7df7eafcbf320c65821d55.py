import os,json
from pathlib import Path
R=Path('task-storage://admet/scaler-six28-20261102');assert os.getuid()==1012
print(json.dumps({n:(R/'raw'/n).read_text() for n in ['cpu-check-exit.json','cpu-check.stderr','cpu-check.stdout','cpu-check-identity.json']}))
