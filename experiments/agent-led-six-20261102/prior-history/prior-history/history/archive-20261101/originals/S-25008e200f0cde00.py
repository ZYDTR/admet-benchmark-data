"""Exercise real packaging and unchanged remote code without networking."""
import ast
import copy
import importlib.util
import json
import shutil
import zipfile
from pathlib import Path
import rebind_deployment as tool

A = Path(__file__).resolve().parent
OUT = A / 'local-checks'
OUT.mkdir(exist_ok=False)
checks = []
uuid = '<REGISTERED_GPU>'
receipt = tool.build(uuid, 2, OUT / 'gpu2-fixture')
assert receipt['launch_authorized'] is False
with zipfile.ZipFile(tool.OLD / 'deployment-small.zip') as old, zipfile.ZipFile(OUT / 'gpu2-fixture/deployment-small.zip') as new:
    assert set(old.namelist()) == set(new.namelist())
    assert [n for n in old.namelist() if old.read(n) != new.read(n)] == [tool.PROFILE]
    previous = json.loads(old.read(tool.PROFILE))
    current = json.loads(new.read(tool.PROFILE))
    assert {k for k in previous if previous[k] != current[k]} == {'gpu_uuid', 'gpu_index', 'stage'}
    assert current['gpu_uuid'] == uuid and current['gpu_index'] == 2
checks.append('real package changes only GPU/index/stage; all other members byte-identical')
tool.build(uuid, 2, OUT / 'gpu2-repeat-fixture')
for name in ('deployment-small.zip', 'deployment-files.json', 'deploy_small_remote.py', 'launch_remote.py'):
    assert (OUT / 'gpu2-fixture' / name).read_bytes() == (OUT / 'gpu2-repeat-fixture' / name).read_bytes()
checks.append('same binding generates byte-identical payload/receiver/launcher')

def functions(path):
    tree = ast.parse(path.read_text())
    return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}

old_functions = functions(tool.OLD / 'deploy_small_remote.py')
new_functions = functions(OUT / 'gpu2-fixture/deploy_small_remote.py')
old_functions['main'] = old_functions['main'].replace('deploy-recovery-v2', 'deploy-resource-v3')
assert old_functions == new_functions
old_launch = (tool.RUN / 'operator/execution-01/launch_remote.py').read_text()
old_profile = json.loads((tool.OLD / 'deployment-files.json').read_text())
digest = next(x['sha256'] for x in old_profile['files'] if x['path'] == tool.PROFILE)
assert old_launch.replace(digest, receipt['profile_sha256']) == (OUT / 'gpu2-fixture/launch_remote.py').read_text()
checks.append('receiver function AST unchanged except receipt identity; launcher only changes pinned hash')

spec = importlib.util.spec_from_file_location('new_receiver', OUT / 'gpu2-fixture/deploy_small_remote.py')
receiver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receiver)
cached = OUT / 'cached.pt'
with zipfile.ZipFile(tool.RUN / 'operator/execution-01/deployment.zip') as original:
    cached.write_bytes(original.read(tool.ASSET))
payload = (OUT / 'gpu2-fixture/deployment-small.zip').read_bytes()
verified = receiver.collect_verified(payload, receiver.MANIFEST, cached, OUT)
assert len(verified) == 47
checks.append('actual new receiver validates 47 files and exact cached checkpoint')
for broken in (payload[:-1], payload[:-1] + bytes([payload[-1] ^ 1])):
    try:
        receiver.collect_verified(broken, receiver.MANIFEST, cached, OUT)
    except AssertionError:
        pass
    else:
        raise AssertionError('damaged payload accepted')
checks.append('short and corrupted payload rejected by actual receiver')

for bad_uuid, index in [('GPU-bad', 2), (uuid, -1), (uuid, 8), (uuid, True)]:
    try:
        tool.build(bad_uuid, index, OUT / 'bad')
    except ValueError:
        pass
    else:
        raise AssertionError('bad identity accepted')
assert not (OUT / 'bad').exists()
checks.append('invalid GPU/index rejected before output')
try:
    tool.build(uuid, 2, OUT / 'gpu2-fixture')
except FileExistsError:
    pass
else:
    raise AssertionError('existing output overwritten')
checks.append('previous attempt output cannot be overwritten')

saved_run, saved_old = tool.RUN, tool.OLD
fake = OUT / 'drift-fixture'
for relative in json.loads((A / 'rebind-input-pins.json').read_text()):
    dest = fake / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(saved_run / relative, dest)
with (fake / 'admission/execution-profile.base.json').open('a') as stream:
    stream.write(' ')
try:
    tool.RUN, tool.OLD = fake, fake / 'operator/execution-02'
    try:
        tool.build(uuid, 2, OUT / 'drift-output')
    except ValueError as error:
        assert 'input identity drift' in str(error)
    else:
        raise AssertionError('source drift accepted')
finally:
    tool.RUN, tool.OLD = saved_run, saved_old
checks.append('pinned input drift rejected without changing originals')
result = {'passed': True, 'checks': checks, 'remote_operations': 0,
          'training_started': False, 'resource_eligibility_verified': False,
          'fixture_is_not_a_deployment': True}
(A / 'rebind-tests.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
