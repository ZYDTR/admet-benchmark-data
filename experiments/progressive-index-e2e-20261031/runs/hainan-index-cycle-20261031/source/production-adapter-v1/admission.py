"""No transport. Exact local normalized admission contract for later main binding."""
import re
from pathlib import Path

from adapter_common import generic, strict_json


class GateClosed(ValueError):
    pass


def require_production(profile, root):
    if profile.get('execution_enabled') is not True:
        raise GateClosed('production execution disabled in preparation profile')
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
    if acceptance.get('accepted_source_manifest_sha256') != manifest_hash:
        raise GateClosed('acceptance does not bind exact manifest')
    formal = profile.get('formal_execution_message')
    if (not isinstance(formal, dict) or not formal.get('message_id')
            or formal.get('origin_thread_id') != '<PRIVATE_ROLE_REF_298cc5edc2>'):
        raise GateClosed('formal main execution message not bound in profile')
    if (dispatch.get('action') != 'execute_one_frozen_run'
            or dispatch.get('run_id') != profile['run_id']
            or dispatch.get('accepted_source_manifest_sha256') != manifest_hash
            or dispatch.get('plan_sha256') != profile['plan_sha256']
            or type(dispatch.get('max_training_jobs')) is not int
            or dispatch['max_training_jobs'] != 1
            or dispatch.get('message_id') != formal['message_id']
            or dispatch.get('origin_thread_id') != formal['origin_thread_id']):
        raise GateClosed('formal dispatch missing or mismatched')
    seen = set()
    for item in manifest['files']:
        relative = Path(item.get('deploy_path', item['path']))
        if relative.is_absolute() or '..' in relative.parts or str(relative) in seen:
            raise GateClosed('noncanonical/duplicate source manifest path')
        seen.add(str(relative))
        path = generic.safe(root, root/relative, True)
        if not path.is_file() or generic.sha(path) != item['sha256']:
            raise GateClosed('accepted source hash mismatch: '+str(relative))
    entry = profile.get('science_entry')
    if entry not in seen or 'source/config.json' not in seen or 'encoder.py' not in seen:
        raise GateClosed('science entry/config/encoder absent from accepted manifest')
    if 'source/training_science.py' not in seen:
        raise GateClosed('science helper absent from accepted manifest')
    return {'binding': binding, 'documents': documents, 'manifest_sha256': manifest_hash,
            'entry': generic.safe(root, root/entry, True), 'files': seen}


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
