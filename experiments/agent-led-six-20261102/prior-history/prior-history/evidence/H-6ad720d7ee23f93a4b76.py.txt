"""Deferred Linux x86_64 boundary/trace primitives adapted from guard_exec_v3.

Not executed during stage one. These are not a scientific launcher. CUDA,
dependency import compatibility, syscall coverage, and actual write scope must
be verified on the target after a separate formal execution instruction.
"""
import ctypes
import os
import stat
import sys
from pathlib import Path

from common_guarded import safe

TRACE_SYSCALLS = ('%file,write,writev,pwrite64,ftruncate,mmap,msync,close,dup,dup2,'
                  'dup3,fchdir,fchmod,fchown,fsetxattr,fremovexattr,fallocate,'
                  'copy_file_range,sendfile,landlock_create_ruleset,'
                  'landlock_add_rule,landlock_restrict_self,prctl')
LIMITATIONS = [
    'No read isolation, GPU partition, ioctl restriction, or system-wide audit.',
    'Landlock ABI3 write rules do not cover chmod/chown/xattr/utime.',
    'Device I/O and denied attempts require explicit trace review.',
    'Environment settings and affinity do not enforce an aggregate RAM/GPU quota.',
]


def trace_command(python, guard_launcher, trace_path, phase_args):
    """Only construct argv; never launch or accept a shell command."""
    return ['/usr/bin/strace', '-f', '-qq', '-yy', '-s', '160', '-e',
            'trace=' + TRACE_SYSCALLS, '-o', str(trace_path), str(python),
            '-I', '-B', '-u', str(guard_launcher), *phase_args]


def apply_process_limits(cpu_threads, file_bytes=450*1024**2):
    if sys.platform != 'linux':
        raise RuntimeError('Linux-only deferred limit setup')
    import resource
    available = sorted(os.sched_getaffinity(0))
    if cpu_threads < 1 or len(available) < cpu_threads:
        raise RuntimeError('insufficient CPU affinity')
    selected = available[:cpu_threads]
    os.sched_setaffinity(0, selected)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (file_bytes, file_bytes))
    return {'cpu_affinity': selected, 'core_bytes': 0, 'file_bytes': file_bytes,
            'ram_quota_enforced': False, 'gpu_quota_enforced': False}


def apply_write_guard(root):
    root = Path(root)
    safe(root, root, True)
    if sys.platform != 'linux' or os.uname().machine != 'x86_64':
        raise RuntimeError('requires reviewed Linux x86_64 syscall ABI')
    if len(list(Path('/proc/self/task').iterdir())) != 1:
        raise RuntimeError('guard must precede library-created threads')
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long

    def check(rc, label):
        if rc < 0:
            raise OSError(ctypes.get_errno(), label)
        return rc

    abi = check(libc.syscall(444, 0, 0, 1), 'Landlock ABI query')
    if abi < 3:
        raise RuntimeError('Landlock ABI >= 3 required by this implementation')

    class Ruleset(ctypes.Structure):
        _fields_ = [('handled_access_fs', ctypes.c_uint64)]

    class Beneath(ctypes.Structure):
        _pack_ = 1
        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]

    rights = sum(1 << bit for bit in (1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14))
    attr = Ruleset(rights)
    ruleset = check(libc.syscall(444, ctypes.byref(attr), ctypes.sizeof(attr), 0),
                    'create write ruleset')
    rules = []

    def add(path, access):
        fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
        try:
            rule = Beneath(access, fd)
            check(libc.syscall(445, ruleset, 1, ctypes.byref(rule), 0), 'add write rule')
        finally:
            os.close(fd)
        rules.append({'path': str(path), 'allowed_access': access})

    try:
        add(root, rights)
        devices = [Path('/dev/null')]
        devices += [p for p in Path('/dev').iterdir()
                    if p.name.startswith('nvidia') and stat.S_ISCHR(p.lstat().st_mode)]
        caps = Path('/dev/nvidia-caps')
        if caps.is_dir() and not caps.is_symlink():
            devices += [p for p in caps.iterdir() if stat.S_ISCHR(p.lstat().st_mode)]
        for device in devices:
            if device.resolve() != device or not stat.S_ISCHR(device.lstat().st_mode):
                raise RuntimeError('noncanonical/non-character device')
            add(device, 1 << 1)
        check(libc.prctl(38, 1, 0, 0, 0), 'PR_SET_NO_NEW_PRIVS')
        check(libc.syscall(446, ruleset, 0), 'Landlock restrict self')
    finally:
        os.close(ruleset)
    return {'abi': abi, 'handled_access_fs': rights, 'rules': rules,
            'no_new_privs': True, 'restrict_self_return_code': 0,
            'applied_before_threads': True, 'limitations': LIMITATIONS}
