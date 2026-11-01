"""No transport. Exact local normalized admission contract for later main binding."""
import re
from pathlib import Path

from adapter_common import generic, strict_json

SCIENCE_PATHS = {'train_remote_v4.py': 'source/train_remote_v4.py',
                 'training_science.py': 'source/training_science.py',
                 'encoder.py': 'encoder.py', 'config.json': 'source/config.json'}
RUNTIME_REQUIRED = {
    'source/production-adapter-v2/'+name+'.py'
    for name in ('adapter_common', 'admission', 'completion', 'guarded_worker',
                 'job_waiter', 'phase_supervisor', 'pipeline', 'state_contract', 'storage_probe', 'process_state', 'trace_contract', 'batch')
} | {'source/production-adapter-v2/batch-registration.json'} | {'source/runtime-v1/'+name+'.py' for name in ('common_guarded', 'linux_boundary', 'resource_checks')}


class GateClosed(ValueError):
    pass


def require_target_root(profile, plan, root):
    expected = Path('<AUTHORIZED_PROJECT_ROOT>/admet')/profile['run_id']
    if root != expected or profile.get('remote_root') != str(expected) or plan.get('remote_directory') != str(expected):
        raise GateClosed('run/profile/PLAN must bind exact approved project-owner target')


def require_production(profile, root):
    if profile.get('execution_enabled') is not True:
        raise GateClosed('production execution disabled in preparation profile')
    registration = strict_json(Path(__file__).resolve().parent/'batch-registration.json')
    if (profile.get('cycle_id') != registration['cycle_id'] or profile.get('run_id') not in {x['run_id'] for x in registration['runs']}):
        raise GateClosed('unregistered batch/run identity')
    if profile.get('run_id') != root.name or str(root) != profile.get('remote_root'):
        raise GateClosed('production run/root identity mismatch')
    if not re.fullmatch(r'GPU-[0-9a-fA-F-]+', profile.get('gpu_uuid') or ''):
        raise GateClosed('explicit GPU UUID required')
    if type(profile.get('gpu_index')) is not int or profile['gpu_index'] < 0:
        raise GateClosed('explicit GPU index required')
    binding_path = profile.get('admission_binding')
    if not binding_path:
        raise GateClosed('no main admission/dispatch binding')
    binding = strict_json(generic.safe(root, root/binding_path, True))
    if (binding['manifest']['sha256'] != profile['accepted_manifest']['sha256']
            or binding['acceptance']['sha256'] != profile['main_scientific_acceptance']['sha256']):
        raise GateClosed('binding differs from pinned main scientific admission')
    plan_path = generic.safe(root, root/'PLAN.json', True)
    if generic.sha(plan_path) != profile['plan_sha256'] or binding.get('plan_sha256') != profile['plan_sha256']:
        raise GateClosed('PLAN identity mismatch')
    documents = {}
    for name in ('acceptance', 'manifest', 'formal_dispatch'):
        spec = binding[name]
        path = generic.safe(root, root/spec['path'], True)
        if generic.sha(path) != spec['sha256']:
            raise GateClosed(name+' document hash mismatch')
        documents[name] = strict_json(path)
    acceptance, manifest, dispatch = (documents[k] for k in ('acceptance', 'manifest', 'formal_dispatch'))
    if acceptance.get('passed') is not True or acceptance.get('run_id') != profile['run_id']:
        raise GateClosed('main acceptance not passed for run')
    manifest_hash = binding['manifest']['sha256']
    if acceptance.get('manifest') != profile['accepted_manifest']['authority_path']:
        raise GateClosed('acceptance does not reference pinned source authority')
    formal = profile.get('formal_execution_message')
    if (not isinstance(formal, dict) or not formal.get('message_id')
            or formal.get('origin_thread_id') != 'private-role-298cc5edc25e'):
        raise GateClosed('formal main execution message not bound in profile')
    if (dispatch.get('action') != 'execute_one_frozen_run'
            or dispatch.get('run_id') != profile['run_id']
            or dispatch.get('accepted_source_manifest_sha256') != manifest_hash
            or dispatch.get('scientific_acceptance_sha256') != binding['acceptance']['sha256']
            or dispatch.get('plan_sha256') != profile['plan_sha256']
            or type(dispatch.get('max_training_jobs')) is not int
            or dispatch['max_training_jobs'] != 1
            or dispatch.get('message_id') != formal['message_id']
            or dispatch.get('origin_thread_id') != formal['origin_thread_id']):
        raise GateClosed('formal dispatch missing or mismatched')
    runtime = profile.get('runtime_source_manifest')
    if (not runtime or not runtime.get('sha256')
            or dispatch.get('runtime_source_manifest_sha256') != runtime['sha256']):
        raise GateClosed('formal dispatch does not bind reviewed runtime source')
    runtime_path = generic.safe(root, root/runtime['path'], True)
    if generic.sha(runtime_path) != runtime['sha256']:
        raise GateClosed('runtime source manifest hash mismatch')
    runtime_document = strict_json(runtime_path)
    if (runtime_document.get('cycle_id') != profile['cycle_id']
            or runtime_document.get('run_id') not in (None, profile['run_id'])):
        raise GateClosed('runtime source cycle/run identity mismatch')
    runtime_seen = set()
    for item in runtime_document['files']:
        relative = item['path']
        if (relative in runtime_seen or Path(relative).is_absolute() or '..' in Path(relative).parts
                or not any(relative.startswith(prefix) for prefix in
                           ('source/production-adapter-v2/', 'source/runtime-v1/', 'source/runtime-compat/'))
                or '/checks/' in relative):
            raise GateClosed('invalid runtime source path')
        runtime_seen.add(relative)
        path = generic.safe(root, root/relative, True)
        if generic.sha(path) != item['sha256'] or path.stat().st_size != item['size']:
            raise GateClosed('reviewed runtime source drift: '+relative)
    if not RUNTIME_REQUIRED <= runtime_seen:
        raise GateClosed('reviewed runtime source set incomplete')
    if not isinstance(manifest, dict) or set(manifest) != set(SCIENCE_PATHS):
        raise GateClosed('expected exact four-file science authority map')
    seen = set()
    for name, relative in SCIENCE_PATHS.items():
        item = manifest[name]
        seen.add(relative)
        path = generic.safe(root, root/relative, True)
        if (not path.is_file() or generic.sha(path) != item['sha256']
                or path.stat().st_size != item['size']):
            raise GateClosed('accepted source identity mismatch: '+relative)
    entry = profile.get('science_entry')
    if entry not in seen or 'source/config.json' not in seen or 'encoder.py' not in seen:
        raise GateClosed('science entry/config/encoder absent from accepted manifest')
    if 'source/training_science.py' not in seen:
        raise GateClosed('science helper absent from accepted manifest')
    plan = strict_json(plan_path)
    require_target_root(profile, plan, root)
    cfg = strict_json(root/'source/config.json')
    if (plan['run_id'] != profile['run_id'] or cfg['run_id'] != profile['run_id']
            or cfg['monitor'] != plan['monitor'] or profile['monitor'] != plan['monitor']
            or {k: v for k, v in cfg['head_config'].items() if k != 'optimizer'} != plan['head_config']
            or cfg['head_config'].get('optimizer') != 'AdamW'
            or cfg['split_config'] != plan['split_config']
            or profile['resource_budget'] != plan['resource_budget']):
        raise GateClosed('configuration/monitor/budget differs from PLAN')
    frozen = profile['frozen_inputs_manifest']
    frozen_path = generic.safe(root, root/frozen['path'], True)
    if generic.sha(frozen_path) != frozen['sha256'] or dispatch.get('frozen_inputs_manifest_sha256') != frozen['sha256']:
        raise GateClosed('formal dispatch does not bind exact frozen run instructions')
    for item in strict_json(frozen_path):
        path = generic.safe(root, root/item['path'], True)
        if generic.sha(path) != item['sha256']:
            raise GateClosed('frozen instruction drift: '+item['path'])
    verify_runtime_inputs(root, cfg, plan)
    return {'binding': binding, 'documents': documents, 'manifest_sha256': manifest_hash,
            'entry': generic.safe(root, root/entry, True), 'files': seen, 'config': cfg}


def verify_runtime_inputs(root, cfg, plan):
    """Read only fixed admitted files before any scientific import; no encoding."""
    import csv
    expected = {item['role']: item for item in plan['inputs']}
    names = {'train': 'data/train.csv', 'validation': 'data/valid.csv', 'test': 'data/test.csv'}
    if len(cfg['inputs']) != 3 or {x['role'] for x in cfg['inputs']} != set(names):
        raise GateClosed('input role mismatch')
    for item in cfg['inputs']:
        authority = expected[item['role']]
        if item['path'] != names[item['role']] or any(item[key] != authority[key] for key in ('sha256', 'rows', 'task')):
            raise GateClosed('input contract mismatch')
        path = generic.safe(root, root/item['path'], True)
        if generic.sha(path) != item['sha256']:
            raise GateClosed('input file hash mismatch')
        with path.open(newline='', encoding='utf-8-sig') as stream:
            reader = csv.DictReader(stream)
            if ('Y' in reader.fieldnames) != (item['role'] == 'train'):
                raise GateClosed('input label boundary mismatch')
            if sum(1 for _ in reader) != item['rows']:
                raise GateClosed('input row count mismatch')
    checkpoint = generic.safe(root, root/'assets/chemeleon_mp.pt', True)
    if cfg['pretrained_sha256'] != plan['pretrained_backbone_sha256'] or generic.sha(checkpoint) != plan['pretrained_backbone_sha256']:
        raise GateClosed('backbone checkpoint identity mismatch')


def runtime_preload(profile, admitted, root):
    """Keep optional runtime shim admission separate from the fixed 4 science files."""
    preload = profile.get('compatibility_preload')
    if not preload:
        return None
    spec = profile.get('runtime_artifacts_manifest')
    if not spec:
        raise GateClosed('runtime shim requires a separately bound artifact manifest')
    path = generic.safe(root, root/spec['path'], True)
    if (generic.sha(path) != spec['sha256']
            or admitted['documents']['formal_dispatch'].get('runtime_artifacts_manifest_sha256') != spec['sha256']):
        raise GateClosed('formal dispatch does not bind exact runtime artifacts')
    manifest = strict_json(path)
    files = {}
    for item in manifest['files']:
        relative = item['path']
        if relative in files or Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise GateClosed('bad runtime artifact path')
        actual = generic.safe(root, root/relative, True)
        if generic.sha(actual) != item['sha256']:
            raise GateClosed('runtime artifact hash mismatch')
        files[relative] = item['sha256']
    if files.get(preload['path']) != preload['sha256']:
        raise GateClosed('shim missing/mismatched in runtime artifact manifest')
    return generic.safe(root, root/preload['path'], True)
