from pathlib import Path
import re,ast,os,collections,json,hashlib
P=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def trace(path,remote_root):
    pending={};outside=[];unknown=[];denied=collections.Counter();devices=collections.Counter();counts=collections.Counter()
    path_calls={'mkdir','mkdirat','rmdir','unlink','unlinkat','rename','renameat','renameat2','link','linkat','symlink','symlinkat','truncate','chmod','chown','lchown','utime','utimes','utimensat','mknod','mknodat','setxattr','removexattr'}
    fd_calls={'write','writev','pwrite64','pwritev','ftruncate','fchmod','fchown','fallocate','fsetxattr','fremovexattr'}
    for number,line in enumerate(path.open(errors='replace'),1):
        m=re.match(r'^(\d+)\s+(.*)',line.rstrip('\n'))
        if not m:continue
        pid,body=m.groups()
        body=re.sub(r'^\d+\.\d+\s+','',body)
        if '<unfinished ...>' in body:pending[pid]=(number,body.split('<unfinished ...>')[0]);continue
        if body.startswith('<... '):
            old=pending.pop(pid,None)
            if old is None:unknown.append({'line':number,'why':'orphan resumed'});continue
            number,first=old;body=first+body.split('resumed>',1)[1].lstrip()
        if ' = ' not in body:continue
        args,returned=body.rsplit(' = ',1);call=args.split('(',1)[0]
        opened=call in ('open','openat','openat2','creat') and (call=='creat' or re.search(r'O_WRONLY|O_RDWR|O_CREAT|O_TRUNC',args))
        shared=call=='mmap' and 'MAP_SHARED' in args and 'PROT_WRITE' in args
        if not (opened or shared or call in path_calls or call in fd_calls):continue
        counts[call]+=1
        if returned.startswith('-1 '):denied[returned.split()[1]]+=1;continue
        if not re.match(r'(\d|0x)',returned):unknown.append({'line':number,'why':'unparsed return','text':body[:400]});continue
        paths=[]
        if call in fd_calls or shared:
            section=args.split(',',1)[0] if call in fd_calls else args
            paths=re.findall(r'<(/[^>]*)>',section)
            if not paths and not any(x in section for x in ('pipe:','socket:','TCP:','UDP:','anon_inode','MAP_ANONYMOUS')):unknown.append({'line':number,'why':'unresolved fd','text':section[:300]})
        else:
            quoted=re.findall(r'"(?:[^"\\]|\\.)*"',args)
            if opened:quoted=quoted[:1]
            if call in ('symlink','symlinkat'):quoted=quoted[1:]
            for literal in quoted:
                try:value=ast.literal_eval(literal)
                except (ValueError,SyntaxError):unknown.append({'line':number,'why':'unparsed quoted path'});continue
                if value.startswith('/'):paths.append(value)
                elif value:
                    bases=re.findall(r'<(/[^>]*)>',args)
                    if bases:paths.append(os.path.normpath(bases[0]+'/'+value))
                    else:unknown.append({'line':number,'why':'unresolved relative path','path':value})
        for value in paths:
            value=value.split('<char ',1)[0].removesuffix(' (deleted)')
            if value==remote_root or value.startswith(remote_root+'/'):counts['inside']+=1
            elif value=='/dev/null' or re.fullmatch(r'/dev/nvidia(?:\d+|ctl|-uvm|-uvm-tools|-modeset)',value) or value.startswith('/dev/nvidia-caps/'):devices[value]+=1
            else:outside.append({'line':number,'pid':int(pid),'call':call,'path':value,'raw':body[:800]})
    return {'sha256':sha(path),'counts':dict(counts),'outside_successful_file_mutations':outside,'unknown':unknown,'pending':pending,'denied':dict(denied),'device_IO_operations':dict(devices),'coverage':'narrow file/write/mmap trace; not all ioctls or whole-host audit'}
results=[]
for n in ['write01.strace','cpu-check.strace','cpu-check02.strace']:
 f=P/'global-evidence/raw'/n;v=trace(f,'task-storage://admet/scaler-six28-20261102');v.update(name=n,raw_tail=f.read_text().splitlines()[-6:]);results.append(v)
(P/'write-scope-verification.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps([{'name':x['name'],'outside':len(x['outside_successful_file_mutations']),'unknown':len(x['unknown']),'pending':len(x['pending']),'denied':x['denied'],'counts':x['counts']} for x in results]))
