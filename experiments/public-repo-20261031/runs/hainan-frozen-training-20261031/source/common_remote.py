"""Task-only paths and clean subprocess environment. No target credential handling."""
import datetime,hashlib,json,os,stat
from pathlib import Path
ROOT=Path('<RUN_ROOT>')
VENV=Path('<ENV_ROOT>')
GPU_UUID='<SELECTED_GPU_UUID>'

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def safe(p,existing=False):
    p=Path(p);assert p==ROOT or ROOT in p.parents
    assert p.resolve(strict=existing)==p
    for a in [p,*p.parents]:
        if a.exists():
            st=a.lstat();assert not stat.S_ISLNK(st.st_mode)
            if stat.S_ISREG(st.st_mode):assert st.st_nlink==1
        if a==Path('/'):break
    mounts=[line.split()[4] for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    assert not any(Path(m)!=Path('/mnt/data') and (Path(m)==ROOT or ROOT in Path(m).parents) for m in mounts)
    return p

def write_json(p,v):
    p=safe(p);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def environment():
    d={'PATH':str(VENV/'bin')+':/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(ROOT/'home'),'TMPDIR':str(ROOT/'tmp'),'TMP':str(ROOT/'tmp'),'TEMP':str(ROOT/'tmp'),'XDG_CACHE_HOME':str(ROOT/'cache/xdg'),'XDG_CONFIG_HOME':str(ROOT/'config'),'XDG_DATA_HOME':str(ROOT/'datahome'),'XDG_STATE_HOME':str(ROOT/'state'),'PIP_CACHE_DIR':str(ROOT/'cache/pip'),'PIP_CONFIG_FILE':'/dev/null','PIP_DISABLE_PIP_VERSION_CHECK':'1','PIP_NO_INPUT':'1','PIP_KEYRING_PROVIDER':'disabled','HF_HOME':str(ROOT/'cache/hf'),'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TORCH_HOME':str(ROOT/'cache/torch'),'TORCH_EXTENSIONS_DIR':str(ROOT/'cache/extensions'),'TORCHINDUCTOR_CACHE_DIR':str(ROOT/'cache/inductor'),'TRITON_CACHE_DIR':str(ROOT/'cache/triton'),'CUDA_CACHE_PATH':str(ROOT/'cache/cuda'),'NUMBA_CACHE_DIR':str(ROOT/'cache/numba'),'MPLCONFIGDIR':str(ROOT/'cache/matplotlib'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','NUMEXPR_NUM_THREADS':'2','VECLIB_MAXIMUM_THREADS':'2','CUDA_VISIBLE_DEVICES':GPU_UUID,'CUDA_DEVICE_ORDER':'PCI_BUS_ID','WANDB_MODE':'disabled','WANDB_DIR':str(ROOT/'cache/wandb'),'WANDB_DISABLED':'true','CUBLAS_WORKSPACE_CONFIG':':4096:8'}
    for v in d.values():
        if v.startswith(str(ROOT)) and ':' not in v:safe(Path(v))
    return d
