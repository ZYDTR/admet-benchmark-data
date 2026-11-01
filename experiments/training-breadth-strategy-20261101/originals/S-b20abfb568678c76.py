"""Local-only exact v4 reviewed overlay and GPU binding; no network/launch."""
import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
RUN = PROJECT / 'runs/hainan-mae-monitor-20261101'
OLD = RUN / 'operator/execution-02'
PROFILE = 'source/production-adapter-v1/execution-profile.json'
ASSET = 'assets/chemeleon_mp.pt'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def build(gpu_uuid, gpu_index, output):
    if not re.fullmatch(r'GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', gpu_uuid):
        raise ValueError('invalid GPU UUID')
    if type(gpu_index) is not int or not 0 <= gpu_index < 8:
        raise ValueError('invalid registered host GPU index')
    pins = json.loads((HERE / 'rebind-input-pins.json').read_text())
    for relative, expected in pins.items():
        if SHA((RUN / relative).read_bytes()) != expected:
            raise ValueError('input identity drift: ' + relative)
    manifest = json.loads((OLD / 'deployment-files.json').read_text())
    expected = {x['path']: x for x in manifest['files']}
    if len(expected) != 47 or len(manifest['files']) != 47:
        raise ValueError('unexpected deployment file set')
    with zipfile.ZipFile(OLD / 'deployment-small.zip') as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(expected) - {ASSET}:
            raise ValueError('unexpected payload members')
        data = {name: archive.read(name) for name in names}
    for name, content in data.items():
        if len(content) != expected[name]['size'] or SHA(content) != expected[name]['sha256']:
            raise ValueError('original payload mismatch: ' + name)
    original_expected = json.loads(json.dumps(expected))
    overlay_path = HERE / 'overlay-manifest.json'
    if SHA(overlay_path.read_bytes()) != 'f462365606b37d331c1688b259cfc6e73fe7d759398af0eb66005a5085530023':
        raise ValueError('unapproved overlay manifest')
    overlay = json.loads(overlay_path.read_text())
    if overlay['original_47_file_manifest_sha256'] != SHA((OLD/'deployment-files.json').read_bytes()):
        raise ValueError('wrong original overlay base')
    for item in overlay['files']:
        name = item['path']
        if name not in expected or name == ASSET:
            raise ValueError('unapproved replacement path')
        content = (HERE / 'overlay' / name).read_bytes()
        if SHA(content) != item['sha256'] or len(content) != item['size']:
            raise ValueError('overlay source drift: '+name)
        data[name] = content
        expected[name] = dict(item)
    manifest['files'] = [expected[name] for name in sorted(expected)]
    base = json.loads((HERE / 'overlay/admission/execution-profile.base.json').read_text())
    profile = dict(base, gpu_uuid=gpu_uuid, gpu_index=gpu_index,
                   execution_enabled=True, stage='v4_fresh_gpu_selected_before_first_deployment')
    allowed = {'gpu_uuid', 'gpu_index', 'execution_enabled', 'stage'}
    if {k for k in base if profile[k] != base[k]} != allowed or set(profile) != set(base):
        raise ValueError('non-selection profile changes')
    data[PROFILE] = encode(profile)
    changed = [name for name, content in data.items() if SHA(content) != expected[name]['sha256']]
    if changed != [PROFILE]:
        raise ValueError('only the execution profile may change')
    new_manifest = json.loads(json.dumps(manifest))
    for item in new_manifest['files']:
        if item['path'] == PROFILE:
            item.update(size=len(data[PROFILE]), sha256=SHA(data[PROFILE]))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_STORED) as archive:
        for name, content in sorted(data.items()):
            archive.writestr(zipfile.ZipInfo(name, (2026, 11, 1, 0, 0, 0)), content)
    payload = buffer.getvalue()
    receiver = (OLD / 'deploy_small_remote.py').read_text()
    assignments = {'MANIFEST': repr(new_manifest), 'PAYLOAD_SIZE': repr(len(payload)),
                   'PAYLOAD_SHA256': repr(SHA(payload))}
    for key, value in assignments.items():
        receiver, count = re.subn(r'^' + key + r'=.*$', lambda _: key + '=' + value,
                                  receiver, flags=re.MULTILINE)
        if count != 1:
            raise ValueError('unexpected receiver constant: ' + key)
    receiver = receiver.replace('hainan-mae-monitor-20261101:deploy-recovery-v2',
                                'hainan-mae-monitor-20261101:deploy-residual-v4')
    launcher = (RUN / 'operator/execution-01/launch_remote.py').read_text()
    old_profile_sha = original_expected[PROFILE]['sha256']
    if launcher.count(old_profile_sha) != 1:
        raise ValueError('unexpected launcher profile binding')
    launcher = launcher.replace(old_profile_sha, SHA(data[PROFILE]))
    receipt = {'schema_version': 1, 'run_id': RUN.name,
               'gpu_uuid': gpu_uuid, 'gpu_index': gpu_index,
               'source_changes': ['source/runtime-v1/resource_checks.py'], 'deployment_content_changes': [name for name,content in data.items() if SHA(content)!=original_expected[name]['sha256']],
               'science_plan_inputs_unchanged': True, 'runtime_changes': 'exact main-reviewed six-file overlay',
               'profile_changes_from_admitted_base': sorted(allowed),
               'profile_sha256': SHA(data[PROFILE]), 'payload_sha256': SHA(payload),
               'receiver_sha256': SHA(receiver.encode()), 'launcher_sha256': SHA(launcher.encode()),
               'payload_bytes': len(payload), 'file_count': 47,
               'remote_operations': 0, 'resource_eligibility_verified': False,
               'launch_authorized': False,
               'required_before_use': 'Fresh resource/identity/environment evidence; original receiver/deployment/learning reconciliation; current main dispatch.'}
    output.mkdir(parents=True, exist_ok=False)
    for name, content in {'deployment-small.zip': payload,
                          'deployment-files.json': encode(new_manifest),
                          'execution-profile.json': data[PROFILE],
                          'deploy_small_remote.py': receiver.encode(),
                          'launch_remote.py': launcher.encode(),
                          'rebind-receipt.json': encode(receipt)}.items():
        with (output / name).open('xb') as stream:
            stream.write(content)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--gpu-index', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.gpu_uuid, args.gpu_index, args.output)))
