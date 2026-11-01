"""Main review: local read only; no returned-code execution or learning."""
from pathlib import Path
import ast, csv, io, json, hashlib, math, re, zipfile, pickletools
from decimal import Decimal, localcontext
C = Path(__file__).resolve().parents[2]
P = C / 'retrieval/phase2'
PUB = P / 'candidate'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def parse(data):

    def pairs(items):
        d = {}
        for k, v in items:
            assert k not in d, ('duplicate JSON key', k)
            d[k] = v
        return d

    def number(s):
        v = float(s)
        assert math.isfinite(v)
        return v
    return json.loads(data, object_pairs_hook=pairs, parse_float=number, parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))

def read(p):
    return parse(p.read_bytes())

def rows(p):
    return list(csv.DictReader(io.StringIO(p.read_text(encoding='utf-8-sig'), newline='')))
manifest = read(P / 'candidate-manifest.json')
assert sha(P / 'candidate-manifest.json') == '7cba6983f9112fb6b952d853fa0ade2091ba9b5176d9130083893c75c89299eb'
expected = {e['path']: e for e in manifest['files']}
actual = {str(p.relative_to(PUB)): p for p in PUB.rglob('*') if p.is_file()}
assert set(actual) == set(expected)
assert not any((p.is_symlink() for p in PUB.rglob('*')))
for n, p in actual.items():
    e = expected[n]
    assert sha(p) == e['sha256'] and p.stat().st_size == e['bytes']
    assert e['repository_path'] == manifest['public_prefix'] + n
root = manifest['repository_root_navigation']
rp = P / root['path']
assert sha(rp) == root['sha256'] and rp.stat().st_size == root['bytes']
assert rp.read_bytes().startswith((P / 'originals/repository-root-README.before').read_bytes())
assert sum((e['bytes'] for e in expected.values())) + root['bytes'] == manifest['total_bytes']
delivery = read(P / 'DELIVERY_MANIFEST.json')
for e in delivery['files']:
    p = P / e['path']
    assert sha(p) == e['sha256'] and p.stat().st_size == e['bytes'], e['path']
before = read(P / 'manifests/remote-before.json')
after = read(P / 'manifests/remote-after.json')
assert before['entries'] == after['entries'] and before['identity']['roots'] == after['identity']['roots']
remote = {e['path']: e for e in before['entries'] if e['type'] == 'file'}
local = {str(p.relative_to(P / 'snapshot')): p for p in (P / 'snapshot').rglob('*') if p.is_file()}
assert set(remote) == set(local) and len(remote) == 119
for name, e in remote.items():
    assert sha(local[name]) == e['sha256'] and local[name].stat().st_size == e['size_bytes']
assert sum((e['size_bytes'] for e in remote.values())) == 128539145
old = C.parents[1] / 'runs/hainan-index-cycle-20261031/raw/execution-02/remote-snapshot-v2'
for p in old.rglob('*'):
    if p.is_file() and (P / 'snapshot/run' / p.relative_to(old)).exists():
        assert sha(p) == sha(P / 'snapshot/run' / p.relative_to(old))
mapping = read(P / 'manifests/source-to-public.json')
changes = []
text_changes = []
markers = re.compile('<LOCAL_PRIVATE_PATH><AUTHORIZED_PROJECT_ROOT>|<COMPUTE_ADDRESS>|<GATEWAY_ADDRESS>|<GATEWAY_HOST>|<GATEWAY_ALIAS>|private-compute|private-compute|GPU-[0-9a-fA-F-]{16,}|<PRIVATE_UI_REFERENCE>){3}-[0-9a-f]{12}|[A-Z]:\\\\Users\\\\', re.I)

def semantics(a, b, where, protected=False):
    assert type(a) == type(b), where
    if isinstance(a, dict):
        assert a.keys() == b.keys(), where
        for k in a:
            semantics(a[k], b[k], where + '/' + k, protected or bool(re.search('smiles|scaffold|canonical|molecule|^Drug$|^Drug_ID$', k, re.I)))
    elif isinstance(a, list):
        assert len(a) == len(b), where
        for i, (x, y) in enumerate(zip(a, b)):
            semantics(x, y, where + '/' + str(i), protected)
    elif isinstance(a, str) and a != b:
        assert not protected and markers.search(a), (where, a[:100], b[:100])
        changes.append(where)
    else:
        assert a == b, where
for e in mapping:
    if e.get('source_path'):
        source = Path(e['source_path'])
        assert sha(source) == e['source_sha256']
    if e.get('public_path'):
        assert sha(PUB / e['public_path']) == e['public_sha256']
    if e['status'] != 'included':
        continue
    source = Path(e['source_path'])
    public = PUB / e['public_path']
    fidelity = e['fidelity']
    if fidelity == 'exact_bytes':
        assert source.read_bytes() == public.read_bytes()
    elif fidelity == 'typed_full_document':
        semantics(read(source), read(public), e['public_path'])
    elif fidelity == 'typed_full_jsonl':
        a = [parse(s) for s in source.read_bytes().splitlines() if s.strip()]
        b = [parse(s) for s in public.read_bytes().splitlines() if s.strip()]
        semantics(a, b, e['public_path'])
    else:
        a = source.read_text()
        b = public.read_text()
        assert len(a.splitlines()) == len(b.splitlines()), e['public_path']
        for n, (x, y) in enumerate(zip(a.splitlines(), b.splitlines())):
            if x != y:
                assert markers.search(x), (e['public_path'], n, x[:100])
                text_changes.append([e['public_path'], n])
        if source.suffix == '.py':
            aa = ast.parse(a)
            bb = ast.parse(b)
            semantics(ast.dump(aa), ast.dump(bb), e['public_path'] + '/AST') if a == b else None
banned = [b'/Users/', b'<PRIVATE_RUNTIME_PATH>', b'<COMPUTE_ADDRESS>', b'<GATEWAY_ADDRESS>', b'PRIVATE KEY-----', b'<PRIVATE_UI_REFERENCE>', b'BEGIN OPENSSH', b'SSHPASS=']
json_count = 0
links = 0
binary_metadata = 0
for n, p in actual.items():
    b = p.read_bytes()
    assert not any((x in b for x in banned)), n
    if p.suffix == '.json':
        read(p)
        json_count += 1
    elif p.suffix == '.jsonl':
        for line in b.splitlines():
            if line.strip():
                parse(line)
    elif p.suffix == '.pt':
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            for entry in z.namelist():
                data = z.read(entry)
                assert not any((x in data for x in banned)), (n, entry)
                if entry.endswith('.pkl'):
                    list(pickletools.genops(data))
                    binary_metadata += 1
    elif p.suffix == '.md':
        for target in re.findall('\\]\\(([^\\s)]+)\\)', b.decode()):
            if target.startswith(('https://', 'http://', '#')):
                continue
            q = (p.parent / target.split('#')[0]).resolve()
            assert q.is_relative_to(PUB.resolve()) and q.is_file(), (n, target)
            links += 1
contract = read(PUB / 'reading-contract.json')
ids = set()
for e in contract['requirements']:
    assert e['entry_id'] not in ids
    ids.add(e['entry_id'])
    assert e['required_read_mode'] == 'original'
    if e.get('candidate_path'):
        assert sha(PUB / e['candidate_path']) == e['source_version']['sha256']
        assert e['publication_path'] == manifest['public_prefix'] + e['candidate_path']
    else:
        assert re.search('/[0-9a-f]{40}/', e['uri'])
assert {'actual-config', 'actual-science', 'encoder', 'predictions', 'train-internal-predictions', 'training-process', 'v1-failure', 'v2-unique-learning', 'caco2-valid-original'} <= ids
assert (PUB / 'history/claims/events.jsonl').read_bytes() == (P.parent / 'candidate-scoped/history/claims/events.jsonl').read_bytes()
task = read(C / 'control/SCORING_TASK.json')
truth_path = Path(task['truth']['path'])
assert sha(truth_path) == task['truth']['sha256']
truth = rows(truth_path)
blind = rows(P / 'snapshot/run/data/valid.csv')
prediction = rows(P / 'snapshot/run/artifacts/predictions.csv')
assert len(truth) == len(blind) == 91 and len(prediction) == 273
valid = [p for p in prediction if p['split'] == 'valid']
assert len(valid) == 91
with localcontext() as ctx:
    ctx.prec = 50
    err = []
    for i, (t, b, p) in enumerate(zip(truth, blind, valid)):
        assert p['row_index'] == str(i) and p['task'] == 'caco2_wang'
        for k in ['Drug_ID', 'Drug']:
            assert t[k] == b[k] == p[k]
        y = Decimal(t['Y'])
        v = Decimal(p['y_pred'])
        assert y.is_finite() and v.is_finite()
        err.append(abs(y - v))
    verified = sum(err) / Decimal(len(err))
score = read(P / 'private_scoring/scores.json')
assert abs(Decimal(str(score['value'])) - verified) < Decimal('1e-14')
assert read(P / 'private_scoring/call-ledger.json')['metric_calls'] == 1
result = dict(status='PASS', candidate_files=201, candidate_bytes=manifest['total_bytes'], delivery_files=len(delivery['files']), local_source_files=len(local), local_source_bytes=128539145, source_stability=True, source_public_pairs=len(mapping), typed_changed_infrastructure_strings=len(changes), text_changed_infrastructure_lines=len(text_changes), json_files=json_count, navigation_links=links, torch_archive_metadata_parsed_without_execution=binary_metadata, required_original_reads=len(ids), historic_claim_events_preserved=5, registered_score_verified_by_main=True, main_verification='Decimal50 independent same-prediction recomputation', verified_mae=str(verified), role_metric_calls=1, valid_rows=91, test_excluded=182, candidate_manifest_sha256=sha(P / 'candidate-manifest.json'), new_metric_selection=False, private_truth_uploaded=False, model_or_returned_code_executed=False)
print(json.dumps(result, ensure_ascii=False, indent=2))
