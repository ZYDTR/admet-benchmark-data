"""No fitting: synthetic cache and random untrained head serialization checks."""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from chemeleon_baseline.features import FeatureStore, CACHE_FILES
from chemeleon_baseline.heads import MLPHead, HEAD_FORMAT, HEAD_CONFIG, load_head

torch.set_num_threads(1)
out = Path('/result')
cache = out/'synthetic-cache'
cache.mkdir(exist_ok=True)
key = hashlib.sha256(b'C').hexdigest()
np.save(cache/'fingerprints.npy', np.array([[1,2,3]],dtype=np.float32))
np.save(cache/'fallback_vector.npy', np.zeros(3,dtype=np.float32))
(cache/'keys.json').write_text(json.dumps({key:0}))
(cache/'uncoded.json').write_text('{}')
hashes = {n: hashlib.sha256((cache/n).read_bytes()).hexdigest() for n in CACHE_FILES}
meta = {'partial':False, 'cache_files_sha256':hashes, 'weights':{'sha256':'synthetic-not-real-weights'},
        'encoder_parameter_digest':'synthetic-not-real-encoder'}
(cache/'metadata.json').write_text(json.dumps(meta))
rows = [{'smiles':'C', 'row_index':0, 'task':'synthetic', 'split':'train'}]
report = {'torch':str(torch.__version__), 'numpy':np.__version__, 'training_executed':False,
          'private_labels_read':False,'cache':{}}
for case, matrix in [('original', [[1,2,3]]), ('tampered',[[9,8,7]]), ('nonfinite',[[float('nan'),2,3]])]:
    np.save(cache/'fingerprints.npy', np.array(matrix,dtype=np.float32))
    try:
        store = FeatureStore(cache)
        X, _, _ = store.vectors_for(rows)
        report['cache'][case] = {'accepted':True,'finite':bool(np.isfinite(X).all()),
            'values':[[str(v) for v in row] for row in X],
            'recorded_hash_matches':store.file_hashes()['fingerprints.npy']==hashes['fingerprints.npy']}
    except Exception as e:
        report['cache'][case] = {'accepted':False, 'error':repr(e)}

# Same torch_version expression as candidate train.py line 226; no train_one call.
head = MLPHead(3)
ckpt = {'format':HEAD_FORMAT,'d_in':3,'head_config':HEAD_CONFIG,'state_dict':head.state_dict(),
        'torch_version':torch.__version__}
report['checkpoint']={}
for case, version in [('candidate_version_type',torch.__version__),('string_version_control',str(torch.__version__))]:
    ckpt['torch_version']=version
    path=out/(case+'.pt')
    torch.save(ckpt,path)
    try:
        loaded,_=load_head(path)
        report['checkpoint'][case]={'loaded':True,'parameter_count':loaded.n_parameters()}
    except Exception as e:
        report['checkpoint'][case]={'loaded':False,'error_type':type(e).__name__,'error':str(e)}
(out/'model-probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
