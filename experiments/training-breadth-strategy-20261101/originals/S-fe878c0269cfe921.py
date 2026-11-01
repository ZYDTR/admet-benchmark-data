"""Main's read-only candidate audit. No remote access, scoring or model loading."""
import ast, array, csv, hashlib, importlib.util, io, json, math, pickletools, re, struct, sys, zipfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
C = HERE.parents[1]
T = C / 'retrieval'
P = T / 'candidate'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text())

def check_files(base, rows):
    for e in rows:
        p = base / e['path']
        assert p.resolve().is_relative_to(base.resolve()) and (not p.is_symlink()), e['path']
        assert p.stat().st_size == e['bytes'] and digest(p) == e['sha256'], e['path']

def main():
    m = read(T / 'candidate-manifest.json')
    assert digest(T / 'candidate-manifest.json') == '18fd12942789f00187c95b543b83bd55f61d4ef062c218dddbccc632a83af450'
    check_files(P, m['files'])
    assert sorted((e['path'] for e in m['files'])) == sorted((str(p.relative_to(P)) for p in P.rglob('*') if p.is_file()))
    assert len(m['files']) == 144 and sum((e['bytes'] for e in m['files'])) == 19509946
    assert all((e['repository_path'] == 'experiments/monitor-mae-e2e-20261101/' + e['path'] for e in m['files']))
    d = read(T / 'DELIVERY_MANIFEST.json')
    check_files(T, d['files'])
    pubm = read(P / 'manifest.json')
    check_files(P, pubm['payload_files'])
    assert set((e['path'] for e in pubm['payload_files'])) == set((e['path'] for e in m['files'])) - {'manifest.json'}
    spec = importlib.util.spec_from_file_location('qualified_projection', T / 'source/public_projection.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mapped = 0
    ast_changes = []
    semantic = []
    for e in read(T / 'manifests/source-to-public.json'):
        if not e.get('public_path'):
            continue
        src = Path(e['source_path'])
        dst = P / e['public_path']
        assert digest(src) == e['source_sha256'] and digest(dst) == e['public_sha256']
        a = src.read_bytes()
        b = dst.read_bytes()
        f = e['fidelity']
        if f == 'exact_bytes':
            assert a == b
        elif f == 'typed_full_document':
            assert mod.typed_public(json.loads(a)) == json.loads(b)
            mod.protect_compare(json.loads(a), json.loads(b))
        elif f == 'typed_full_jsonl':
            aa = [json.loads(x) for x in a.splitlines() if x.strip()]
            bb = [json.loads(x) for x in b.splitlines() if x.strip()]
            assert len(aa) == len(bb)
            for x, y in zip(aa, bb):
                assert mod.typed_public(x) == y
                mod.protect_compare(x, y)
        elif f == 'full_text_infrastructure_strings_redacted':
            assert mod.public_string(a.decode()).encode() == b
        else:
            raise AssertionError(f)
        if src.suffix == '.py':
            x = ast.parse(a)
            y = ast.parse(b)
            xx = list(ast.walk(x))
            yy = list(ast.walk(y))
            assert len(xx) == len(yy)
            for u, v in zip(xx, yy):
                if isinstance(u, ast.Constant) and isinstance(u.value, str) and (u.value != v.value):
                    assert mod.public_string(u.value) == v.value
                    ast_changes.append({'path': e['public_path'], 'line': u.lineno, 'original': u.value, 'public': v.value})
                    u.value = v.value
            assert ast.dump(x) == ast.dump(y), e['public_path']
        mapped += 1
        semantic.append({'path': e['public_path'], 'method': f})
    base = P / 'runs/hainan-mae-monitor-20261101'
    for split, n in [('train', 637), ('valid', 91), ('test', 182)]:
        with (base / 'data' / f'{split}.csv').open(encoding='utf-8-sig', newline='') as f:
            r = csv.DictReader(f)
            rows = list(r)
            assert len(rows) == n
            if split != 'train':
                assert set(r.fieldnames) == {'Drug_ID', 'Drug'}, r.fieldnames
    feedback = read(P / 'batches/monitor-mae-e2e-20261101/preparation-feedback.json')
    assert not any((k in json.dumps(feedback) for k in ['row_residuals', 'row_truth', 'row_predictions']))
    findings = []
    json_count = 0
    patterns = ['<LOCAL_PRIVATE_PATH><>]+', '<PRIVATE_RUNTIME_PATH>', '<COMPUTE_ADDRESS>', '<GATEWAY_ADDRESS>', '-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY', '(?i)(?:sk-proj-|ghp_)[A-Za-z0-9]{16,}', 'https://chatgpt\\.com/c/', '<PRIVATE_UI_REFERENCE>']
    for p in P.rglob('*'):
        if not p.is_file():
            continue
        texts = []
        if p.suffix == '.pt':
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    if n.endswith('.pkl'):
                        texts += [arg for op, arg, pos in pickletools.genops(z.read(n)) if isinstance(arg, str)]
        elif p.suffix != '.npz':
            try:
                texts = [p.read_text()]
            except UnicodeDecodeError:
                raise AssertionError(str(p))
        if p.suffix == '.json':
            json.loads(p.read_text(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
            json_count += 1
        for pattern in patterns:
            if any((re.search(pattern, t) for t in texts)):
                findings.append({'path': str(p.relative_to(P)), 'pattern': pattern})
    assert not findings, findings
    links = 0
    for p in P.rglob('*.md'):
        for link in re.findall('\\[[^\\]\\n]*\\]\\(([^\\s)]+)\\)', p.read_text()):
            if '://' in link or link.startswith('#'):
                continue
            assert (p.parent / link.split('#')[0]).is_file(), (str(p), link)
            links += 1
    r = read(P / 'reading-contract.json')
    bypath = {e['path']: e for e in m['files']}
    for e in r['requirements']:
        if e.get('candidate_path'):
            assert e['source_version']['sha256'] == bypath[e['candidate_path']]['sha256']
            assert e['publication_path'] == m['prefix'] + e['candidate_path']
    old = C.parents[1] / 'exchange/trials/progressive-index-e2e-20261031/retrieval/phase2/snapshot/run/artifacts'
    task = read(T / 'control/RETRIEVAL_TASK.json')
    old = next((Path(x) / 'retrieval/phase2/snapshot/run/artifacts' for x in task['read_only_local_references'] if Path(x).name == 'progressive-index-e2e-20261031'))

    def values(p):
        with zipfile.ZipFile(p) as z:
            raw = z.read('features.npy')
        assert raw[:6] == b'\x93NUMPY'
        v = raw[6]
        off = 10 if v == 1 else 12
        length = struct.unpack('<H' if v == 1 else '<I', raw[8:off])[0]
        header = ast.literal_eval(raw[off:off + length].decode('latin1'))
        assert header['descr'] == '<f4' and (not header['fortran_order'])
        payload = raw[off + length:]
        arr = array.array('f')
        arr.frombytes(payload)
        if sys.byteorder != 'little':
            arr.byteswap()
        assert len(arr) == math.prod(header['shape'])
        return (header, arr, hashlib.sha256(payload).hexdigest())
    features = []
    for e in read(T / 'derived/feature-comparison.json')['splits']:
        split = e['split']
        ha, a, sa = values(old / f'features-{split}.npz')
        hb, b, sb = values(T / f'snapshot/run/artifacts/features-{split}.npz')
        assert ha == hb and sa == e['prior_payload_sha256'] and (sb == e['current_payload_sha256'])
        diffs = [abs(x - y) for x, y in zip(a, b)]
        assert all((math.isfinite(x) for x in diffs))
        assert max(diffs) == e['max_absolute_difference'] and sum((x != 0 for x in diffs)) == e['exactly_different_scalars']
        assert sum((x > 1e-06 for x in diffs)) == 0
        features.append({'split': split, 'max_absolute_difference': max(diffs), 'scalars': len(diffs)})
    result = {'state': 'passed', 'candidate_manifest_sha256': digest(T / 'candidate-manifest.json'), 'files': 144, 'bytes': 19509946, 'sealed_delivery_files': len(d['files']), 'typed_projections_verified': mapped, 'json_files_parsed': json_count, 'python_ast_string_changes': len(ast_changes), 'internal_links': links, 'reading_contract_items': len(r['requirements']), 'feature_comparison_independently_verified': features, 'privacy_scan_findings': findings, 'model_execution': False, 'score_calls': 0, 'remote_calls': 0, 'publication': False, 'limitations': ['String redaction verification reuses personally reviewed declared projector; source hashes, Python AST, data bytes, navigation and full feature payload comparison checked separately.', 'Observed comparison is one pair with minute feature differences, not proof of monitor-only causation.', 'Worker success and supervisor 125 preserved separately.']}
    (HERE / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    (HERE / 'python-string-changes.private.json').write_text(json.dumps(ast_changes, indent=2) + '\n')
    print(json.dumps(result, indent=2))
if __name__ == '__main__':
    main()
