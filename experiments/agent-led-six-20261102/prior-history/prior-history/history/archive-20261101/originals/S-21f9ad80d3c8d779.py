#!/usr/bin/env python3
"""本地渲染/核对主控封口的Chat Prompt；不联网、不发送消息。"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import importlib.util
from urllib.parse import urlsplit

SLOT = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
SHA = re.compile(r"[0-9a-f]{64}")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse(data):
    return json.loads(data, object_pairs_hook=unique_pairs)


def pinned_repository(uri):
    u = urlsplit(uri)
    if u.scheme != "https" or u.username or u.password or u.query or u.fragment or u.port:
        raise ValueError("evidence URI must be a plain HTTPS commit-pinned URL")
    parts = u.path.strip("/").split("/")
    if u.netloc == "github.com" and len(parts) >= 4 and parts[2] in ("blob", "tree"):
        owner, repo, commit = parts[0], parts[1], parts[3]
    elif u.netloc == "raw.githubusercontent.com" and len(parts) >= 4:
        owner, repo, commit = parts[:3]
    else:
        raise ValueError("evidence URI must use the registered GitHub publication form")
    if not owner or not repo or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("evidence URI lacks a full fixed commit")
    return owner, repo, commit


def render(template_bytes, contract_bytes, values_bytes, binding, context_bytes=None):
    expected = {"request_id", "template_sha256", "contract_sha256", "values_sha256"}
    contract = parse(contract_bytes)
    if contract.get('template_revision', 0) >= 11:
        expected.add('context_sha256')
        if context_bytes is None or digest(context_bytes) != binding.get('context_sha256'):
            raise ValueError('missing or changed controller context contract')
        project = Path(__file__).resolve().parents[3]
        spec = importlib.util.spec_from_file_location('admet_control_contract', project/'scripts/control_contract.py')
        checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
        bundle = parse(context_bytes)
        checker.context(bundle, root=project)
        if not bundle['send_ready']:
            raise ValueError('context not ready for sending')
    if set(binding) != expected:
        raise ValueError("controller binding keys differ from the contract")
    for key, data in (("template", template_bytes), ("contract", contract_bytes), ("values", values_bytes)):
        if binding[key + "_sha256"] != digest(data):
            raise ValueError(f"{key} SHA256 differs from controller dispatch")
    contract, values = parse(contract_bytes), parse(values_bytes)
    fields = contract["fields"]
    if not isinstance(values, dict) or set(values) != set(fields):
        raise ValueError("missing or extra prompt values")
    blocks = re.findall(r"^```text\n(.*?)^```\s*$", template_bytes.decode("utf-8"), re.M | re.S)
    if len(blocks) != 1:
        raise ValueError("template requires exactly one text block")
    body = blocks[0].strip() + "\n"
    if set(SLOT.findall(body)) != set(fields):
        raise ValueError("template placeholders differ from field contract")
    repositories = set()
    replacements = {}
    for key, spec in fields.items():
        value = values[key]
        if spec['type'] == 'reading_contract':
            if not isinstance(value, dict) or not isinstance(value.get('requirements'), list) or not value['requirements']:
                raise ValueError('reading_contract must contain exact published requirements')
            entry_ids = set()
            layers = set()
            for row in value['requirements']:
                if not all(row.get(k) for k in ('entry_id','layer','uri','source_version')) or row['entry_id'] in entry_ids:
                    raise ValueError('invalid or duplicate reading requirement')
                entry_ids.add(row['entry_id'])
                layers.add(row['layer'])
                repo = pinned_repository(row['uri']); repositories.add(repo)
                version = row['source_version']
                if not isinstance(version, dict) or version.get('commit') != repo[2] or not SHA.fullmatch(version.get('sha256', '')):
                    raise ValueError('reading source version mismatch')
            if not {'entry', 'context', 'history', 'batch'} <= layers:
                raise ValueError('missing mandatory progressive reading layer')
            rendered = json.dumps(value, ensure_ascii=False, indent=2)
        elif spec["type"] == "string_array":
            if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value):
                raise ValueError(f"{key} must be a nonempty string array")
            if len(set(value)) != len(value):
                raise ValueError(f"{key} contains duplicate identities")
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key} must be a nonempty string")
            rendered = value
        if "{{" in rendered or "}}" in rendered or "\x00" in rendered:
            raise ValueError(f"{key} contains unresolved template syntax or NUL")
        if spec.get("format") == "sha256" and not SHA.fullmatch(value):
            raise ValueError(f"{key} is not SHA256")
        if spec.get("format") == "pinned_github_uri":
            repositories.add(pinned_repository(value))
        replacements[key] = rendered
    if len(repositories) != 1:
        raise ValueError("all evidence entry points must use the same repository commit")
    if context_bytes is not None:
        for row in parse(context_bytes)['history_records']:
            for source in row.get('sources', []):
                if pinned_repository(source['uri']) not in repositories:
                    raise ValueError('history source does not use the same fixed publication commit')
    if values["request_id"] != binding["request_id"]:
        raise ValueError("request identity differs from controller dispatch")
    prompt = SLOT.sub(lambda match: replacements[match.group(1)], body).encode("utf-8")
    if b"{{" in prompt or b"}}" in prompt:
        raise ValueError("unexpanded placeholder syntax")
    receipt = {"schema_version": 1, **binding, "prompt_sha256": digest(prompt),
               "prompt_bytes": len(prompt), "fields": sorted(fields),
               "scope": "text identity only; not permission, source truth, reachability or Chat compliance"}
    return prompt, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("render", "verify"))
    for name in ("template", "contract", "values", "binding", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument('--context', type=Path)
    args = parser.parse_args()
    prompt, receipt = render(args.template.read_bytes(), args.contract.read_bytes(),
                             args.values.read_bytes(), parse(args.binding.read_bytes()),
                             args.context.read_bytes() if args.context else None)
    if args.mode == "render":
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out / "prompt.txt").write_bytes(prompt)
        (args.out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    else:
        if (args.out / "prompt.txt").read_bytes() != prompt:
            raise ValueError("prompt differs from controller-bound rendering")
        if parse((args.out / "receipt.json").read_bytes()) != receipt:
            raise ValueError("render receipt differs from controller-bound rendering")
    print(json.dumps({"mode": args.mode, "request_id": receipt["request_id"],
                      "prompt_sha256": receipt["prompt_sha256"], "ok": True}))


if __name__ == "__main__":
    main()
