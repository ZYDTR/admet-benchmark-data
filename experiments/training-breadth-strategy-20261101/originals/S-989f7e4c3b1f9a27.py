from pathlib import Path
import subprocess,json,time
R=Path(__file__).resolve().parents[1]
def run(script,*args):
 p=subprocess.run(['python3','-B',str(R/'source'/script),*args],check=True,text=True,capture_output=True);return p.stdout
for n in range(16):
 v=json.loads(run('operate02.py','status'))['train01']
 if 'exit.json' in v:
  result=json.loads(v['exit.json']);print('train01 exit:',json.dumps(result),flush=True);assert result['exit_code']==0,result;break
 time.sleep(3)
else:raise RuntimeError('Training status still pending: query original phase, do not submit another')
print(run('collect.py','final-fetch'),flush=True)
print(run('audit_raw.py','final-fetch'),flush=True)
print(run('postcheck.py'),flush=True)
