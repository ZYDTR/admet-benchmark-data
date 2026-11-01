import base64,hashlib,json,tarfile
from pathlib import Path
from transport import remote,RUN

def upload(files,dirs,tag):
    expected={k:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size} for k,p in files.items()}
    child='''import hashlib,json,os,sys,tarfile\nfrom pathlib import Path\nROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')\nassert ROOT.resolve(strict=True)==ROOT\nexpected=json.loads(EXPECTED_LITERAL)\ndirs=json.loads(DIRS_LITERAL)\nfor d in dirs:\n    p=ROOT/d;assert p.resolve()==p and ROOT in p.parents and not p.exists();p.mkdir()\nseen=[]\nwith tarfile.open(fileobj=sys.stdin.buffer,mode='r|gz') as tar:\n    for m in tar:\n        assert m.name in expected and m.isfile() and m.name not in seen\n        p=ROOT/m.name;assert p.resolve()==p and ROOT in p.parents\n        assert m.size==expected[m.name]['size'] and m.size<50000000\n        data=tar.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==expected[m.name]['sha256']\n        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)\n        with os.fdopen(fd,'wb') as f:f.write(data)\n        seen.append(m.name)\nassert set(seen)==set(expected)\nprint(json.dumps({'uploaded':expected,'dirs_created':dirs}))\n'''.replace('EXPECTED_LITERAL',repr(json.dumps(expected))).replace('DIRS_LITERAL',repr(json.dumps(dirs)))
    (RUN/'source'/f'unpack_{tag}.py').write_text(child)
    source='''import base64,json,os,socket,subprocess,sys\nfrom pathlib import Path\nROOT=Path('<AUTHORIZED_PROJECT_ROOT>/admet/hainan-skill-pilot-20261030')\nassert ROOT.resolve(strict=True)==ROOT and socket.gethostname().split('.')[0]=='private-compute' and os.getuid()==1012\nchild=base64.b64decode(CHILD_LITERAL).decode()\np=subprocess.run(['/usr/bin/strace','-f','-qq','-yy','-s','160','-e','trace=%file,write,writev,pwrite64,ftruncate','-o',str(ROOT/'raw/TRACE_LITERAL.strace'),'/usr/bin/python3','-I','-B','-c',child],stdin=sys.stdin.buffer,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=ROOT,env={'PATH':'/usr/bin:/bin','HOME':str(ROOT/'home'),'TMPDIR':str(ROOT/'tmp')})\nprint(json.dumps({'exit_code':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()}));assert p.returncode==0\n'''.replace('CHILD_LITERAL',repr(base64.b64encode(child.encode()).decode())).replace('TRACE_LITERAL',tag)
    (RUN/'source'/f'upload_{tag}.py').write_text(source)
    (RUN/'raw'/f'{tag}-manifest.json').write_text(json.dumps(expected,indent=2)+'\n')
    arc=RUN/'raw'/f'{tag}.tar.gz'
    with tarfile.open(arc,'w:gz',format=tarfile.USTAR_FORMAT) as tar:
        for name,p in files.items():
            info=tarfile.TarInfo(name);info.size=p.stat().st_size;info.mode=0o644
            with p.open('rb') as f:tar.addfile(info,f)
    return remote(source,tag,payload=arc.read_bytes(),timeout=70)
