"""Standard-library bridge to immutable stage-one helpers and legacy science API."""
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

ADAPTER = Path(__file__).resolve().parent
RUN = ADAPTER.parents[1]
RUNTIME = RUN/'source/runtime-v1'


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generic = _load('_admet_generic_guard_v1', RUNTIME/'common_guarded.py')


def load_runtime(name):
    # linux_boundary captures generic.safe before science receives legacy.safe.
    # This bootstrap is single-threaded and imports only the standard library.
    previous = sys.modules.get('common_guarded')
    sys.modules['common_guarded'] = generic
    try:
        return _load('_admet_'+name+'_v1', RUNTIME/(name+'.py'))
    finally:
        if previous is None:
            sys.modules.pop('common_guarded', None)
        else:
            sys.modules['common_guarded'] = previous


def load_boundary():
    return load_runtime('linux_boundary')


def legacy_module(root, python, gpu_uuid):
    root = generic.safe(Path(root), Path(root), True)
    module = types.ModuleType('common_guarded')
    module.ROOT = root
    module.GPU_UUID = gpu_uuid
    module.environment = lambda: generic.environment(root, python, cpu_threads=2,
                                                     gpu_uuid=gpu_uuid)
    module.now = generic.now
    module.safe = lambda path, existing=False: generic.safe(root, Path(path), existing)
    module.sha = lambda path: generic.sha(module.safe(path, True))
    module.write_json = lambda path, value: generic.write_json(root, Path(path), value)
    return module


def establish_environment(root, python, gpu_uuid):
    heavy = ('torch', 'numpy', 'chemprop', 'rdkit', 'joblib', 'encoder')
    if any(name.split('.')[0] in heavy for name in sys.modules):
        raise RuntimeError('scientific module already imported before protection')
    legacy = legacy_module(root, python, gpu_uuid)
    env = legacy.environment()
    generic.prepare_environment_dirs(root, env)
    os.environ.clear()
    os.environ.update(env)
    os.chdir(root)
    sys.modules['common_guarded'] = legacy
    return legacy


def strict_json(path):
    def bad(value):
        raise ValueError('nonfinite JSON: '+value)
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('duplicate JSON key: '+key)
            value[key] = item
        return value
    return json.loads(Path(path).read_text(), parse_constant=bad, object_pairs_hook=pairs)


def write(root, path, value):
    generic.write_json(root, path, value)


def process_identity(pid):
    result = {'pid': pid, 'pgid': os.getpgid(pid)}
    path = Path('/proc')/str(pid)/'stat'
    if path.exists():
        value = path.read_text()
        result.update(start_stat=value, start_ticks=value.rsplit(')', 1)[1].split()[19])
    return result
