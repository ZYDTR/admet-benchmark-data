"""Controller's read-only inventory and publication checks. Never executes candidate code."""
import csv
import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import time

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / 'retrieval/public_candidate'
PATTERNS = {
    'private_key': rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'github_credential': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})',
    'openai_style_credential': rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{35,}',
    'bearer_credential': rb'(?i)bearer\s+[A-Za-z0-9._-]{30,}',
    'personal_local_path': rb'<LOCAL_PRIVATE_PATH>]+/',
    'compute_account_path': rb'<PRIVATE_RUNTIME_PATH>',
    'private_host_address': rb'(?:<COMPUTE_ADDRESS>|<RELAY_ADDRESS>)',
    'windows_user_path': rb'(?i)[A-Z]:\\Users\\',
}


def main():
    start = time.monotonic()
    files, issues, csv_checks = [], [], []
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT).as_posix()
        if path.is_symlink():
            issues.append({'path': rel, 'kind': 'symlink'})
            continue
        if not path.is_file():
            continue
        data = path.read_bytes()
        files.append({'path': rel, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        if len(data) >= 100 * 1024**2:
            issues.append({'path': rel, 'kind': 'git_blob_too_large'})
        for kind, pattern in PATTERNS.items():
            match = re.search(pattern, data)
            if match:
                issues.append({'path': rel, 'kind': kind, 'byte_offset': match.start()})
        if path.suffix == '.json':
            try:
                json.loads(data)
            except Exception as exc:
                issues.append({'path': rel, 'kind': 'invalid_json', 'error': type(exc).__name__})
        if path.name in ('valid.csv', 'test.csv'):
            rows = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
            header = rows.fieldnames
            count = sum(1 for _ in rows)
            csv_checks.append({'path': rel, 'header': header, 'rows': count})
            if 'Y' in (header or []):
                issues.append({'path': rel, 'kind': 'unexpected_new_truth_copy'})
        if any(x in path.name for x in ('labeled-records', 'original-valid', 'private-vault')):
            issues.append({'path': rel, 'kind': 'private_scoring_work_file'})
    report = {
        'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'file_count': len(files), 'total_bytes': sum(x['bytes'] for x in files),
        'files': files, 'issues': issues, 'blind_csv_checks': csv_checks,
        'seconds': time.monotonic() - start,
        'automated_scan_passed': bool(files) and not issues,
        'limitation': 'Pattern scan does not prove all secrets absent; controller also reviews source disposition and actual content.',
    }
    destination = BASE / 'acceptance/public-candidate-inspection.json'
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('file_count', 'total_bytes', 'issues', 'automated_scan_passed')}))


if __name__ == '__main__':
    main()
