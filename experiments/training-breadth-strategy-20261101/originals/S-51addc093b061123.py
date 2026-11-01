"""Main's production-function checks, original observations and counterexamples."""
import ast
import copy
import importlib.util
import json
import sys
import xml.etree.ElementTree as E
from pathlib import Path

A = Path(__file__).resolve().parent
R = A.parents[3]
RUN = R / 'runs/hainan-mae-monitor-20261101'
sys.path.insert(0, str(RUN / 'source/runtime-v1'))
spec = importlib.util.spec_from_file_location('reviewed_resource_v4', A / 'overlay/source/runtime-v1/resource_checks.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
uuid = '<REGISTERED_GPU>'
samples = json.loads((A / 'live-samples.json').read_text())['samples']
results = []
for s in samples:
    result = gate.validate_idle_gpu(s['xml'], s['apps'], uuid, 2)
    assert result['memory_used_mib'] == 4 and result['shared_use_verified'] is False
    rows = [r.split() for r in s['pmon'].splitlines() if r.strip() and not r.strip().startswith('#')]
    assert rows and all(r[0] == '2' and r[1] == '-' for r in rows)
results.append('three fresh real XML/apps/pmon samples qualify; residual cause remains unknown')
base = E.fromstring(samples[-1]['xml'])
apps = samples[-1]['apps']

def check(name, change=None, apps_value=None, expected=False, expected_uuid=uuid):
    tree = copy.deepcopy(base)
    if change:
        change(tree.find('gpu'))
    try:
        out = gate.validate_idle_gpu(E.tostring(tree, encoding='unicode'), apps if apps_value is None else apps_value, expected_uuid, 2)
    except (ValueError, TypeError):
        assert not expected, name
    else:
        assert expected and out['healthy'], name
    results.append(name)

check('zero-memory idle still accepted', lambda g: setattr(g.find('fb_memory_usage/used'), 'text', '0 MiB'), expected=True)
check('5 MiB is not arbitrarily rejected', lambda g: setattr(g.find('fb_memory_usage/used'), 'text', '5 MiB'), expected=True)
def resident_no_work(g):
    g.find('fb_memory_usage/used').text='16384 MiB'
    g.find('fb_memory_usage/free').text='64000 MiB'
check('allocated memory size alone does not block enough usable memory', resident_no_work, expected=True)
for field, value in [('fb_memory_usage/used','N/A'),
                     ('fb_memory_usage/used','-1 MiB'),('fb_memory_usage/free','8191 MiB'),
                     ('utilization/gpu_util','1 %'),('utilization/memory_util','1 %'),
                     ('gpu_recovery_action','Reset'),('mig_mode/current_mig','Enabled'),
                     ('remapped_rows/remapped_row_pending','Yes'),
                     ('ecc_errors/volatile/dram_uncorrectable','1')]:
    check('reject '+field+'='+value, lambda g,f=field,v=value: setattr(g.find(f),'text',v))
check('reject missing memory', lambda g:g.find('fb_memory_usage').remove(g.find('fb_memory_usage/used')))
check('reject missing process view', lambda g:g.remove(g.find('processes')))
check('reject XML graphics process', lambda g:E.SubElement(E.SubElement(g.find('processes'),'process_info'),'type').__setattr__('text','G'))
check('reject compute process despite tiny memory', apps_value=uuid+', 12345, 1\n')
check('reject missing ECC field', lambda g:g.find('ecc_errors/volatile').remove(g.find('ecc_errors/volatile/dram_uncorrectable')))
check('reject wrong UUID', expected_uuid='<REGISTERED_GPU>')
check('reject malformed process CSV', apps_value='unknown\n')
old = ast.parse((RUN/'source/runtime-v1/resource_checks.py').read_text())
new = ast.parse((A/'overlay/source/runtime-v1/resource_checks.py').read_text())
functions = lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!='validate_idle_gpu'}
assert functions(old)==functions(new)
results.append('own-PID monitoring, enforcement and all other functions unchanged')
out={'passed':True,'checks':results,'count':len(results),'network_or_training':False,'not_proof_of_future_gpu_availability':True}
(A/'resource-gate-tests.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
