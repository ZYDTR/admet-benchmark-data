"""Conservative strace file-write audit. Reconstructs unfinished syscalls and uses -yy
resolved fd paths / dirfd paths. Unknown write paths stay unknown; does not prove system isolation.
"""
import ast,collections,json,posixpath,re
from pathlib import Path
ROOT='<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030'
Q=re.compile(r'"(?:\\.|[^"\\])*"')
MUT={'mkdir','mkdirat','unlink','unlinkat','rmdir','rename','renameat','renameat2','link','linkat','symlink','symlinkat','chmod','fchmod','fchmodat','fchmodat2','chown','lchown','fchown','fchownat','truncate','ftruncate','utime','utimes','futimesat','utimensat','setxattr','lsetxattr','fsetxattr','removexattr','lremovexattr','fremovexattr','mknod','mknodat','fallocate','copy_file_range','sendfile','sendfile64'}

def audit(path):
    counts=collections.Counter();inside=collections.Counter();devices=collections.Counter();outside=[];failed=[];unknown=[];pending={};cwd={};read_private=[];lines=0
    def classify(p,line,success,call):
        if p is None:
            (unknown if success else failed).append({'syscall':call,'path':None,'line':line[:1000]});return
        p=p.removesuffix(' (deleted)')
        if p.startswith('/memfd:') or p.startswith('memfd:'):counts['anonymous_memfd']+=1;return
        if p.startswith('/dev/') and '<char ' in p:p=p.split('<char ',1)[0]
        if p.startswith(('TCP:','UDP:','TCPv6:','UDPv6:','UNIX:','NETLINK:','pipe:','socket:','anon_inode:')):counts['non_file_descriptor']+=1;return
        if not p.startswith('/'):
            (unknown if success else failed).append({'syscall':call,'path':p,'line':line[:1000]});return
        p=posixpath.normpath(p)
        if p==ROOT or p.startswith(ROOT+'/'):
            if success:inside[p]+=1
            else:counts['failed_inside_attempt']+=1
        elif p=='/dev/null' or p.startswith('/dev/nvidia'):
            if success:devices[p]+=1
            else:counts['failed_device_attempt']+=1
        else:(outside if success else failed).append({'syscall':call,'path':p,'line':line[:1000]})
    for raw in Path(path).open(errors='replace'):
        lines+=1;line=raw.rstrip('\n')
        m=re.match(r'^(\d+)\s+(.*)$',line)
        if not m:continue
        pid,body=m.groups()
        if '<unfinished ...>' in body:pending[pid]=body.split('<unfinished ...>')[0];continue
        if body.startswith('<... '):
            resumed=re.match(r'<\.\.\. (\w+) resumed>(.*)',body)
            if not resumed:continue
            if pid not in pending:unknown.append({'unmatched_resumed':line});continue
            body=pending.pop(pid)+resumed.group(2)
        m=re.match(r'(\w+)\((.*)\)\s+=\s+(.*)$',body)
        if not m:continue
        call,args,result=m.groups();success=not result.startswith('-1 ');counts['parsed_syscalls']+=1
        strings=[]
        for s in Q.findall(args):
            try:strings.append(ast.literal_eval(s))
            except Exception:strings.append(None)
        dirfd=re.search(r'AT_FDCWD<([^>]+)>',args) or re.search(r'^\d+<([^>]+)>',args)
        base=dirfd.group(1) if dirfd else cwd.get(pid)
        def full(p):
            if p is None:return None
            if p.startswith('/'):return p
            return posixpath.normpath(base+'/'+p) if base else None
        if call=='chdir' and success and strings:cwd[pid]=full(strings[0]);continue
        if call=='fchdir' and success:
            fd=re.search(r'^\d+<([^>]+)>',args);cwd[pid]=fd.group(1) if fd else None;continue
        if call in ['open','openat','openat2','creat']:
            iswrite=call=='creat' or bool(re.search(r'O_(WRONLY|RDWR|CREAT|TRUNC|APPEND|TMPFILE)',args))
            if iswrite:
                fd=re.match(r'\d+<([^>]+)>',result)
                classify(fd.group(1) if fd and success else full(strings[0]) if strings else None,line,success,call)
            elif success:
                fd=re.match(r'\d+<([^>]+)>',result)
                if fd:
                    p=fd.group(1)
                    if p.startswith('<PRIVATE_RUNTIME_PATH>') and not (p==ROOT or p.startswith(ROOT+'/')):read_private.append({'path':p,'line':line[:600]})
        elif call in ['write','writev','pwrite64','ftruncate']:
            fd=re.match(r'\d+<([^>]+)>',args);classify(fd.group(1) if fd else None,line,success,call)
        elif call=='mmap' and 'MAP_SHARED' in args and 'PROT_WRITE' in args and 'MAP_ANONYMOUS' not in args:
            fds=re.findall(r'\d+<([^>]+)>',args);classify(fds[-1] if fds else None,line,success,call)
        elif call in MUT:
            if call in ['symlink','symlinkat']:paths=[strings[-1]] if strings else []
            elif call in ['rename','renameat','renameat2','link','linkat']:paths=strings[:2]
            elif strings:paths=strings[:1]
            else:
                fds=re.findall(r'\d+<([^>]+)>',args);paths=fds[1:2] if call=='copy_file_range' else fds[:1]
            if not paths:classify(None,line,success,call)
            for p in paths:classify(full(p),line,success,call)
    return {'trace':str(path),'line_count':lines,'counts':dict(counts),'successful_inside_path_count':len(inside),'successful_inside_paths':dict(inside),'device_nodes':dict(devices),'successful_outside_file_effects':outside,'failed_outside_or_unknown_attempts':failed,'unknown_write_effects':unknown,'unfinished_at_eof':pending,'outside_task_home_reads':read_private,'verdict':'pass_for_traced_file_effects' if not outside and not unknown and not pending else 'not_verified','limitations':['Traces child process filesystem calls, not SSH daemon/kernel audit or unrelated processes.','Open-for-write and mutating syscalls are conservative evidence of file effects; device/sockets classified separately.','Does not establish OS sandboxing or prove zero system-wide changes.']}
if __name__=='__main__':
    import sys
    out=[audit(p) for p in sys.argv[1:]];print(json.dumps(out,indent=2))
