from pathlib import Path
import importlib.util,json
A=Path(__file__).resolve().parent
R=A.parents[3]
p=R/'runs/hainan-mae-monitor-20261101/operator/execution-01/transport.py'
s=importlib.util.spec_from_file_location('admet_transport_reviewed',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.EVIDENCE=A/'raw';m.EVIDENCE.mkdir(exist_ok=True)
out=m.read_only((A/'reconcile_remote.py').read_text(),'exact-receiver-and-own-asset',timeout=30)
result=json.loads(out);(A/'reconciliation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
