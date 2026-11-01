"""Run-local standard-library helpers, adapted from the validated common_guarded.

No credentials, transport, science imports, or launch side effects at import time.
Path checks are preflight checks; Linux Landlock plus trace remains necessary evidence.
"""
import datetime
import hashlib
import json
import os
import stat
import uuid
from pathlib import Path


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def safe(root, path, existing=False):
    root, path = Path(root), Path(path)
    if not root.is_absolute() or not path.is_absolute():
        raise ValueError("absolute paths required")
    if root.resolve(strict=True) != root or not root.is_dir():
        raise ValueError("root identity changed")
    if path != root and root not in path.parents:
        raise ValueError("path outside run root")
    if path.resolve(strict=existing) != path:
        raise ValueError("noncanonical or linked path")
    for ancestor in (path, *path.parents):
        if ancestor.exists() or ancestor.is_symlink():
            info = ancestor.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ValueError("symbolic link")
            if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
                raise ValueError("multiply linked file")
    mountinfo = Path('/proc/self/mountinfo')
    if mountinfo.exists():
        for line in mountinfo.read_text().splitlines():
            # Linux mountinfo octal-escapes spaces and backslashes in mount paths.
            encoded = line.split()[4]
            for escape, literal in ((r'\040', ' '), (r'\011', '\t'),
                                    (r'\012', '\n'), (r'\134', '\\')):
                encoded = encoded.replace(escape, literal)
            mounted = Path(encoded)
            if mounted == root or root in mounted.parents:
                raise ValueError("nested mount in run root")
    return path


def write_json(root, path, value):
    path = safe(root, path)
    temporary = safe(root, path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp'))
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        safe(root, path)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def environment(root, python, cpu_threads=2, gpu_uuid=None):
    """Explicit clean environment. The caller creates only the returned run dirs."""
    root = safe(root, root, True)
    if type(cpu_threads) is not int or cpu_threads < 1:
        raise ValueError("invalid CPU thread budget")
    env = {
        'PATH': str(Path(python).parent) + ':/usr/bin:/bin',
        'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
        'HOME': str(root/'home'), 'TMPDIR': str(root/'tmp'),
        'TMP': str(root/'tmp'), 'TEMP': str(root/'tmp'),
        'XDG_CACHE_HOME': str(root/'cache/xdg'),
        'XDG_CONFIG_HOME': str(root/'config'),
        'XDG_DATA_HOME': str(root/'datahome'), 'XDG_STATE_HOME': str(root/'state'),
        'PIP_CACHE_DIR': str(root/'cache/pip'), 'PIP_CONFIG_FILE': '/dev/null',
        'PIP_DISABLE_PIP_VERSION_CHECK': '1', 'PIP_NO_INPUT': '1',
        'PIP_KEYRING_PROVIDER': 'disabled',
        'HF_HOME': str(root/'cache/hf'), 'HF_HUB_OFFLINE': '1',
        'TRANSFORMERS_OFFLINE': '1', 'TORCH_HOME': str(root/'cache/torch'),
        'TORCH_EXTENSIONS_DIR': str(root/'cache/extensions'),
        'TORCHINDUCTOR_CACHE_DIR': str(root/'cache/inductor'),
        'TRITON_CACHE_DIR': str(root/'cache/triton'),
        'CUDA_CACHE_PATH': str(root/'cache/cuda'),
        'NUMBA_CACHE_DIR': str(root/'cache/numba'),
        'MPLCONFIGDIR': str(root/'cache/matplotlib'),
        'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1',
        'CUDA_VISIBLE_DEVICES': gpu_uuid or '', 'CUDA_DEVICE_ORDER': 'PCI_BUS_ID',
        'WANDB_MODE': 'disabled', 'WANDB_DISABLED': 'true',
        'WANDB_DIR': str(root/'cache/wandb'),
        'CUBLAS_WORKSPACE_CONFIG': ':4096:8',
        'JOBLIB_MULTIPROCESSING': '0', 'JOBLIB_TEMP_FOLDER': str(root/'tmp/joblib'),
    }
    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        env[key] = str(cpu_threads)
    return env


def prepare_environment_dirs(root, env):
    for key, value in env.items():
        if key not in ('PATH', 'PIP_CONFIG_FILE') and value.startswith(str(root) + '/'):
            safe(root, Path(value)).mkdir(parents=True, exist_ok=True)
