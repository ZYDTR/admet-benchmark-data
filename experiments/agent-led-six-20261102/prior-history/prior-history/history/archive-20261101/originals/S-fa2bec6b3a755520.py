"""Controller-only static verification. Never imports or runs returned code/models."""
from pathlib import Path, PurePosixPath
from decimal import Decimal
import collections
import datetime
import hashlib
import json
import re
import stat
import zipfile

T = Path(__file__).resolve().parents[1]
ARCHIVE = Path('<LOCAL_PRIVATE_PATH>')
EXPECTED_ARCHIVE = '0a001c01bad77643eaf8759104ad0319d37b5807f10778eac8d3d7622c22d33a'
REQUEST = 'admet-public-repo-pro-20261031-001'
MANIFEST = 'dbdec244caa8ddb106721877cf93625c1957b9184985c07b1cf751eed5d70505'
NAMES = ['analysis.md', 'review.json', 'issues.json', 'next_batch_guide.md', 'next_experiments.json', 'search_space.json']
errors = []
checks = {}
def check(name, condition):
    checks[name] = bool(condition)
    if not condition:
        errors.append(name)

check('original_archive_hash', hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == EXPECTED_ARCHIVE)
with zipfile.ZipFile(ARCHIVE) as z:
    infos = z.infolist()
    check('unique_zip_names', len(infos) == len({i.filename for i in infos}))
    check('safe_paths_regular_files', all(not PurePosixPath(i.filename).is_absolute() and '..' not in PurePosixPath(i.filename).parts and not stat.S_ISLNK(i.external_attr >> 16) for i in infos))
    check('bounded_expansion', len(infos) <= 100 and sum(i.file_size for i in infos) <= 2_000_000)
    check('zip_crc', z.testzip() is None)
    blobs = {n: z.read('deliverables/' + n) for n in NAMES}
    self_manifest = json.loads(z.read('final-delivery-checks.json'))
    for row in self_manifest['files']:
        b = blobs[row['file']]
        check('artifact_hash_' + row['file'], hashlib.sha256(b).hexdigest() == row['sha256'] and len(b) == row['bytes'])
    docs = {n: json.loads(b) for n, b in blobs.items() if n.endswith('.json')}
    for n, d in docs.items():
        check('identity_' + n, d['request_id'] == REQUEST and d['manifest_sha256'] == MANIFEST and d['round_id'] == 'public-repo-round001' and d['packet_version'] == 2)
    required = {
        'review.json': 'schema_version request_id round_id manifest_sha256 status read_receipt findings missing_evidence not_assessed comparison_groups stop_reasons'.split(),
        'issues.json': 'issue_id status severity category statement affected_run_ids evidence_refs hypothesis counterevidence impact proposed_resolution verification_criterion related_proposal_ids'.split(),
        'next_experiments.json': 'proposal_id priority hypothesis control_run_or_config task asset_versions change_only hold_fixed split_id seeds metric direction minimum_effect_or_decision_rule success_criterion falsification_criterion compute_budget dependencies within_current_scope'.split(),
        'search_space.json': 'direction_id linked_issues rationale evidence_refs counterevidence candidate_models_or_modules parameters combination_constraints search_method configuration_count_or_counting_rule seeds estimated_run_count cost_assumptions readiness priority scope_status'.split(),
    }
    collections_by_file = {'issues.json': 'issues', 'next_experiments.json': 'experiments', 'search_space.json': 'directions'}
    for n, fields in required.items():
        rows = [docs[n]] if n == 'review.json' else docs[n][collections_by_file[n]]
        check('required_fields_' + n, all(set(fields) <= set(row) for row in rows))
    issues = docs['issues.json']['issues']
    proposals = docs['next_experiments.json']['experiments']
    directions = docs['search_space.json']['directions']
    ids = {x['issue_id'] for x in issues}
    pids = {x['proposal_id'] for x in proposals}
    dids = {x['direction_id'] for x in directions}
    check('unique_ids', len(ids) == len(issues) and len(pids) == len(proposals) and len(dids) == len(directions))
    check('issue_proposal_links', all(set(x['related_proposal_ids']) <= pids for x in issues))
    check('direction_issue_links', all(set(x['linked_issues']) <= ids for x in directions))
    check('proposal_direction_links', {x['direction_id'] for x in proposals} == dids)
    check('all_execution_false', all(x['within_current_scope']['execution'] is False for x in proposals))
    check('valid_issue_statuses', all(x['status'] in ['open', 'investigating', 'resolved', 'deferred'] for x in issues))

    expected = json.loads((T / 'acceptance/read-oracle-recomputed-public.json').read_text())['checks']
    for row in docs['review.json']['read_checks']:
        e = expected[row['run_id']]
        check('computed_read_check_' + row['run_id'], all(row[k] == e[k] for k in ['all_prediction_rows', 'valid_rows', 'optimizer_steps', 'best_epoch_1_based']) and abs(Decimal(row['mean_valid_prediction']) - Decimal(str(e['mean_valid_prediction']))) < Decimal('1e-12'))

    public = json.loads((T / 'retrieval/public_candidate/manifest.json').read_text())['payload_files']
    manifest_index = {r['path']: r for r in public}
    download_claims = json.loads(z.read('download-receipt.json'))
    text_claims = [r for r in download_claims if r.get('read_status') == 'downloaded_hash_verified']
    feature_claims = json.loads(z.read('agent-reviews/feature-byte-audit.json'))['downloads']
    check('380_text_receipt_identities_match_publication', len(text_claims) == 380 and all(r['path'] in manifest_index and all(r[k] == manifest_index[r['path']][k] for k in ['bytes', 'sha256']) for r in text_claims))
    check('initial_receipt_discloses_12_unread_binaries', sum(r.get('read_status') == 'not_downloaded_binary_use_structure_record' for r in download_claims) == 12)
    check('six_feature_receipt_identities_match_publication', len(feature_claims) == 6 and all(r['path'] in manifest_index and all(r[k] == manifest_index[r['path']][k] for k in ['bytes', 'sha256']) for r in feature_claims))
    independent = json.loads((T / 'acceptance/independent-cache-diagnostics.json').read_text())['runs']
    feature = json.loads(z.read('root-checks/feature-independent-check.json'))
    for split, block in feature.items():
        for run, value in block['per_run'].items():
            e = independent[run]['extrema'][split]
            check(f'feature_extremum_{run}_{split}', abs(value['max_abs_z'] - e['maximum_absolute_standardized_feature_double_arithmetic']) < 1e-8 and value['row_index'] == e['row_index'] and value['feature_index'] == e['feature_index'])

    guide = blobs['next_batch_guide.md'].decode()
    check('ten_guide_work_items', len(re.findall(r'^## W\d\d[：:]', guide, re.M)) == 10)
    check('guide_no_exact_valid_scores', all(token not in guide for token in ['0.378625', '0.389188', '0.523504', '0.520506']))
    check('guide_explicit_preparation_boundary', '只准备' in guide and '私有验证标签' in guide and '精确分数' in guide and '全部参数及buffer' in guide and '当前执行预算0' in guide)
    check('core_count_arithmetic', 4*3 == 12 and 3+4-1 == 6 and 4+3+3-2 == 8 and 2+2*4+2+2 == 14 and 10+4*3 == 22 and 2*3*3 == 18)
    audit_sources = [i.filename for i in infos if i.filename.endswith('.py')]

result = {
    'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status': 'pass' if not errors else 'fail',
    'archive_sha256': EXPECTED_ARCHIVE,
    'archive_bytes': ARCHIVE.stat().st_size,
    'archive_entries': len(infos),
    'checks': checks, 'errors': errors,
    'counts': {'issues': len(issues), 'proposals': len(proposals), 'directions': len(directions), 'work_items': 10},
    'files': [{'name': n, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for n, b in blobs.items()],
    'returned_audit_source_files_not_executed': audit_sources,
    'limitations': [
        'Structural and identity validation supplements, not replaces, controller personal scientific review.',
        'A matching download receipt is a claim consistent with the manifest; actual-read conclusion also uses held-out numerical recomputation and visible tool activity.',
        'Original final-response stream/REVIEW_COMPLETE marker not recovered; valid attachments do not prove that the Chat turn reached terminal state.',
        'Preparation guide is a specification; future execution requires concrete code/config/split/asset hashes and a budget.'
    ],
    'no_model_execution_no_training_no_private_truth_access': True,
}
(T / 'acceptance/independent-chat-artifacts.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'check_count': len(checks), 'errors': errors, 'counts': result['counts']}, ensure_ascii=False))
