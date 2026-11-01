import hashlib,json,stat,tarfile
from pathlib import Path
from transport import RUN,remote

def fetch(tag):
    target=RUN/'raw'/tag;target.mkdir()
    data=remote(RUN/'source/fetch_evidence_remote.py',tag,timeout=150)
    archive=target/'evidence.tar.gz';archive.write_bytes(data)
    with tarfile.open(archive) as tar:
        manifest_member=tar.next();assert manifest_member.name=='fetch-manifest.json' and manifest_member.isfile()
        manifest=json.load(tar.extractfile(manifest_member));(target/'fetch-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        for m in tar:
            if m.name=='fetch-manifest.json':continue
            assert m.isfile() and m.name in manifest and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
            assert m.size==manifest[m.name]['size'] and m.size<=1024**3
            p=target/m.name;p.parent.mkdir(parents=True,exist_ok=True);assert p.resolve()==p and target in p.parents
            content=tar.extractfile(m).read();assert hashlib.sha256(content).hexdigest()==manifest[m.name]['sha256']
            with p.open('xb') as f:f.write(content)
    return target,manifest
