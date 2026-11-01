"""Resolve only, without installation or model execution, for CPython3.12 Linux.
Use official pinned pip wheel, explicit compatibility tags and Linux dependency marker env.
Remote pip check will additionally verify the realized environment.
"""
import os,sys
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]
for d in ['raw/host-resolve-home','raw/host-resolve-tmp']:(RUN/d).mkdir(exist_ok=True)
os.environ['HOME']=str(RUN/'raw/host-resolve-home');os.environ['TMPDIR']=str(RUN/'raw/host-resolve-tmp');os.environ['PIP_CONFIG_FILE']='/dev/null';os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['PIP_DISABLE_PIP_VERSION_CHECK']='1';os.environ['PIP_KEYRING_PROVIDER']='disabled'
sys.path.insert(0,str(RUN/'raw/pip-25.3-py3-none-any.whl'))
from pip._vendor.packaging import markers
original=markers.default_environment

def linux_environment():
    env=original();env.update({'implementation_name':'cpython','os_name':'posix','platform_machine':'x86_64','platform_system':'Linux','python_version':'3.12','python_full_version':'3.12.3','implementation_version':'3.12.3','sys_platform':'linux'});return env
markers.default_environment=linux_environment
from pip._internal.cli.main import main
args=['install','--dry-run','--ignore-installed','--only-binary=:all:','--no-cache-dir','--disable-pip-version-check','--python-version','3.12','--implementation','cp','--abi','cp312','--platform','manylinux1_x86_64','--platform','manylinux2010_x86_64','--platform','manylinux2014_x86_64','--platform','manylinux_2_17_x86_64','--platform','manylinux_2_28_x86_64','--index-url','https://pypi.org/simple','--report',str(RUN/'raw/linux-resolution.json'),'-r',str(RUN/'source/requirements.in')]
raise SystemExit(main(args))
