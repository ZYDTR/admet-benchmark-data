"""Local-only exact bundle staging; pending scientific admission cannot stage."""
import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path


def stage(spec, output):
    if spec.get('science_acceptance_passed') is not True or spec.get('runtime_acceptance_passed') is not True:
        raise ValueError('main science/runtime acceptance required before package staging')
    names, contents, manifest = set(), {}, []
    for item in spec['files']:
        name, source = Path(item['deploy_path']), Path(item['local_path'])
        if name.is_absolute() or '..' in name.parts or str(name) != item['deploy_path'] or str(name) in names:
            raise ValueError('invalid or duplicate deployment path')
        names.add(str(name))
        if str(name).startswith(('state/', 'raw/', 'artifacts/', 'cache/', 'home/')):
            raise ValueError('old run state/output/cache is never a deployment input')
        if source.resolve(strict=True) != source or source.is_symlink():
            raise ValueError('linked/noncanonical source')
        metadata = source.stat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError('source must be single-link regular file')
        content = source.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != item['sha256'] or len(content) != item['size']:
            raise ValueError('source digest/size mismatch')
        contents[str(name)] = content
        manifest.append({'path': str(name), 'sha256': digest, 'size': len(content)})
    checkpoint = spec['reuse_own_checkpoint']
    if (checkpoint['sha256'] != 'c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651'
            or checkpoint['size'] != 34859448
            or not checkpoint['remote_source'].startswith('<AUTHORIZED_PROJECT_ROOT>/admet/')):
        raise ValueError('unapproved own checkpoint copy contract')
    if 'assets/chemeleon_mp.pt' in names:
        raise ValueError('frozen weight is a verified own target-side copy, not repeated network payload')
    output.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(output/'deployment-small.zip', 'x', zipfile.ZIP_STORED) as archive:
        for name, content in sorted(contents.items()):
            archive.writestr(name, content)
    receipt = {'run_id': spec['run_id'], 'files': manifest, 'reuse_own_checkpoint': checkpoint,
               'payload_sha256': hashlib.sha256((output/'deployment-small.zip').read_bytes()).hexdigest(),
               'payload_bytes': (output/'deployment-small.zip').stat().st_size,
               'remote_operations': 0, 'training': False,
               'required_target_checks': ['strict identity and current read-only private environment',
                   'checkpoint path/nonlink/size/hash before copy', 'fresh GPU qualification',
                   'exact framed receiver and independent complete deployment receipt',
                   'formal per-run admission plus finite guarded preflight before lifetime learning lock']}
    (output/'deployment-files.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(json.loads(args.spec.read_text()), args.output)))
