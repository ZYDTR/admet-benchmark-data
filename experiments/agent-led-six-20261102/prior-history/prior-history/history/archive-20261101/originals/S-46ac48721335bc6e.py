"""Cross-check every resolver-selected wheel with official PyPI metadata before remote use."""
import concurrent.futures,hashlib,json,urllib.request,urllib.parse
from pathlib import Path
RUN=Path(__file__).resolve().parents[1]
report=json.loads((RUN/'raw/linux-resolution.json').read_text())

def verify(item):
    name=item['metadata']['name'];version=item['metadata']['version'];url=item['download_info']['url'];filename=urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit('/',1)[1]);digest=item['download_info']['archive_info']['hashes']['sha256']
    assert urllib.parse.urlparse(url).hostname=='files.pythonhosted.org' and filename.endswith('.whl')
    endpoint='https://pypi.org/pypi/'+urllib.parse.quote(name)+'/'+urllib.parse.quote(version)+'/json'
    with urllib.request.urlopen(endpoint,timeout=30) as r:data=r.read();meta=json.loads(data)
    p=next(x for x in meta['urls'] if x['filename']==filename);assert p['digests']['sha256']==digest and p['url']==url
    return {'name':name,'version':version,'filename':filename,'sha256':digest,'size_bytes':p['size'],'official_url':url,'official_metadata_url':endpoint,'official_metadata_sha256':hashlib.sha256(data).hexdigest(),'mirror_url':'https://pypi.tuna.tsinghua.edu.cn'+urllib.parse.urlparse(url).path,'official_pypi_sha256_verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:manifest=list(pool.map(verify,report['install']))
total=sum(x['size_bytes'] for x in manifest);assert total<8*1024**3
(RUN/'source/wheels-linux.lock.json').write_text(json.dumps({'platform':'CPython3.12 Linux x86_64','source':'Official PyPI JSON and pinned pip25.3 resolver report','total_bytes':total,'wheels':manifest},indent=2)+'\n')
(RUN/'source/requirements-linux.lock').write_text('\n'.join(f'{x["name"]}=={x["version"]} --hash=sha256:{x["sha256"]}' for x in manifest)+'\n')
print('Official hashes verified:',len(manifest),'wheels,',total,'bytes')
