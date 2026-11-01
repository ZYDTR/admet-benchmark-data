"""Parent-authored, offline audit. Reads returned evidence, never executes child code."""
import ast, collections, hashlib, json, re
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
import sys
FETCH = RUN / 'raw' / (sys.argv[1] if len(sys.argv)>1 else 'final-fetch')
ROOT = '<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-follow-20261031'
mutations = {'mkdir','mkdirat','rmdir','unlink','unlinkat','rename','renameat','renameat2','link','linkat','symlink','symlinkat','truncate','chmod','chown','lchown','utime','utimes','utimensat','mknod','mknodat','setxattr','removexattr'}
fdmutations = {'write','writev','pwrite64','pwritev','ftruncate','fchmod','fchown','fallocate','fsetxattr','fremovexattr'}

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def audit_trace(p):
    counts=collections.Counter(); pending={}; outside=[]; devices=collections.Counter(); unresolved=[]; denied=collections.Counter(); raw_hits=[]
    for n,line in enumerate(p.open(errors='replace'),1):
        line=line.rstrip('\n'); m=re.match(r'^(\d+)\s+(.*)',line)
        if not m: continue
        pid,body=m.groups()
        if '<unfinished ...>' in body:
            pending[pid]=(n,body.split('<unfinished ...>',1)[0]); continue
        if body.startswith('<... '):
            prior=pending.pop(pid,None)
            if prior is None: unresolved.append({'line':n,'reason':'orphan resumed'}); continue
            body=prior[1]+body.split('resumed>',1)[1].lstrip(); origin=prior[0]
        else: origin=n
        if ' = ' not in body: continue
        args,result=body.rsplit(' = ',1); call=args.split('(',1)[0]
        is_open=call in {'open','openat','openat2','creat'} and (call=='creat' or re.search(r'O_WRONLY|O_RDWR|O_CREAT|O_TRUNC',args))
        shared=call=='mmap' and 'MAP_SHARED' in args and 'PROT_WRITE' in args
        if not (is_open or shared or call in mutations or call in fdmutations): continue
        counts[call]+=1
        if result.startswith('-1 '): denied[result.split()[1]]+=1; continue
        if not re.match(r'(?:\d|0x)',result): unresolved.append({'line':origin,'reason':'unknown return','call':call}); continue
        paths=[]
        if call in fdmutations or shared:
            section=args.split(',',1)[0] if call in fdmutations else args
            paths=re.findall(r'<(/[^>]*)>',section)
            if not paths:
                if 'pipe:' in section or 'socket:' in section or 'TCP:' in section or 'UDP:' in section or 'anon_inode:[eventfd]' in section: counts['ipc_fd']+=1
                elif shared and 'MAP_ANONYMOUS' in args: counts['anonymous_memory']+=1
                else: unresolved.append({'line':origin,'reason':'unresolved fd','call':call,'excerpt':args[:200]})
                continue
        else:
            quoted=re.findall(r'"(?:[^"\\]|\\.)*"',args)
            if is_open: quoted=quoted[:1]
            if call in {'symlink','symlinkat'}: quoted=quoted[1:]
            for q in quoted:
                try: value=ast.literal_eval(q)
                except (ValueError,SyntaxError): continue
                if value.startswith('/'): paths.append(value)
                elif value:
                    bases=re.findall(r'<(/[^>]*)>',args)
                    if bases: paths.append(str(Path(bases[0])/value))
                    else: unresolved.append({'line':origin,'reason':'relative path without annotated dirfd','call':call,'path':value})
        for path in paths:
            path=path.split('<char ',1)[0].removesuffix(' (deleted)')
            if path==ROOT or path.startswith(ROOT+'/'): counts['inside']+=1
            elif path=='/dev/null' or re.fullmatch(r'/dev/nvidia(?:\d+|ctl|-uvm|-uvm-tools|-modeset)',path) or path.startswith('/dev/nvidia-caps/'):
                devices[path]+=1
            else:
                outside.append({'line':origin,'pid':int(pid),'call':call,'path':path,'raw':body[:1200]})
        if '/dev/shm/sem.' in body: raw_hits.append({'line':origin,'pid':int(pid),'raw':body})
    return {'path':str(p.relative_to(FETCH)),'sha256':sha(p),'counts':dict(counts),'outside_mutation_evidence':outside,'device_operations':dict(devices),'denied_counts':dict(denied),'unresolved_count':len(unresolved),'unresolved_examples':unresolved[:15],'pending_at_eof':pending,'semaphore_mutation_lines':raw_hits}

manifest=json.loads((FETCH/'fetch-manifest.json').read_text()); mismatches=[]
for name,meta in manifest.items():
    p=FETCH/name
    if not p.is_file() or p.stat().st_size!=meta['size'] or sha(p)!=meta['sha256']: mismatches.append(name)
traces=[audit_trace(p) for p in sorted((FETCH/'raw').glob('*.strace'))]
out={'auditor':'parent independent offline parser; no child audit code imported','manifest_files':len(manifest),'manifest_mismatches':mismatches,'traces':traces,'limitations':['Conservative traced filesystem syscall review only; not whole-server proof, ioctl/device partitioning or SSH-daemon audit.','Relative paths without annotated dirfd and unresolved inherited descriptors are reported, not silently passed.','Argument parser is narrow; exact positive findings independently checked against original line numbers.']}
(RUN/'acceptance'/('parent-audit-'+FETCH.name+'.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'manifest_files':len(manifest),'mismatches':mismatches,'traces':len(traces),'outside':[{ 'trace':x['path'],'effects':len(x['outside_mutation_evidence'])} for x in traces if x['outside_mutation_evidence']],'unresolved_total':sum(x['unresolved_count'] for x in traces)},ensure_ascii=False))
