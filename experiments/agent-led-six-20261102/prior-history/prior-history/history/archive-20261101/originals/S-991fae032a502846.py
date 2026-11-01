"""Offline failure-injection: no server access or training."""
from pathlib import Path
import subprocess,sys,json
A=Path(__file__).resolve().parent;D=A/'gate-regression';D.mkdir(exist_ok=False)
results=[]
# Reproduce the observed failure masking with harmless local commands.
plain=subprocess.run(['/bin/zsh','-c','exit_status=255\n/bin/sh -c "exit $exit_status"\n: > downstream-ran'],cwd=D)
results.append({'case':'unguarded_multiline_negative_control','outer_exit':plain.returncode,'downstream_ran':(D/'downstream-ran').exists()})
assert plain.returncode==0 and (D/'downstream-ran').exists()
# Correct dependency semantics: child check failure prevents the second operation.
for fail in [True,False]:
 marker=D/('guarded-failure' if fail else 'guarded-success');status=0
 try:
  subprocess.run([sys.executable,'-B','-c','import sys;sys.exit('+('255' if fail else '0')+')'],check=True,capture_output=True)
  subprocess.run([sys.executable,'-B','-c','from pathlib import Path;import sys;Path(sys.argv[1]).write_text("downstream")',str(marker)],check=True,capture_output=True)
 except subprocess.CalledProcessError as e:status=e.returncode
 results.append({'case':'guarded_failure' if fail else 'guarded_success','outer_exit':status,'downstream_ran':marker.exists()})
 assert (status==255 and not marker.exists()) if fail else (status==0 and marker.exists())
(A/'parent-gate-regression.json').write_text(json.dumps({'passed':True,'scope':'local synthetic dependency-chain semantics only; no rerun of training agent','cases':results},indent=2)+'\n')
print(json.dumps(results))
