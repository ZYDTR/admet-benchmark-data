"""从声明的证据生成本地知识索引；不联网、不评分、不执行源代码。"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from urllib.parse import quote, urlparse


class CatalogError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise CatalogError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique(items, kind):
    result = {}
    for item in items:
        key = item.get('id')
        require(isinstance(key, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', key),
                f'{kind}: invalid id {key!r}')
        require(key not in result, f'{kind}: duplicate id {key}')
        result[key] = item
    return result


def refs(ids, targets, owner):
    require(isinstance(ids, list) and len(ids) == len(set(ids)), f'{owner}: invalid references')
    require(bool(ids), f'{owner}: missing evidence references')
    for key in ids:
        require(key in targets, f'{owner}: dangling reference {key}')


def source_file(root, relative):
    rel = PurePosixPath(relative)
    require(not rel.is_absolute() and '..' not in rel.parts, f'source path escapes root: {relative}')
    p = root
    for part in rel.parts:
        p = p / part
        require(not p.is_symlink(), f'symlink source rejected: {relative}')
    require(p.resolve().is_relative_to(root), f'source path escapes root: {relative}')
    require(p.is_file(), f'source not a regular file: {relative}')
    return p


def validate(data, root):
    require(data.get('schema_version') == 1, 'unsupported schema_version')
    for key in ('catalog_id', 'as_of', 'scope', 'current_batch'):
        require(isinstance(data.get(key), str) and data[key].strip(), f'missing {key}')
    require(data.get('history_coverage') in ('partial', 'complete'), 'invalid history_coverage')
    gaps = data.get('history_gaps')
    require(isinstance(gaps, list), 'history_gaps must be explicit')
    require((data['history_coverage'] == 'partial') == bool(gaps), 'coverage and gaps conflict')
    sources = unique(data['sources'], 'sources')
    for key, s in sources.items():
        p = source_file(root, s['path'])
        require(sha(p.read_bytes()) == s['sha256'], f'source hash mismatch: {key}')
        require(bool(s.get('title')), f'missing source title: {key}')
        if s.get('public_uri'):
            u = urlparse(s['public_uri'])
            require(u.scheme == 'https' and u.netloc and not u.username and not u.password,
                    f'invalid public uri: {key}')
            # 此版本只生成local_only索引，不据此自动认定URL可访问或获准公开。
    refs(data['context_source_ids'], sources, 'context')
    runs, issues, batches = (unique(data[k], k) for k in ('runs', 'issues', 'batches'))
    for kind, items in [('run', runs), ('issue', issues), ('batch', batches)]:
        for key, item in items.items():
            refs(item['source_ids'], sources, key)
            if kind == 'run':
                require(all(isinstance(item.get(k), str) and item[k] for k in
                            ('task', 'state', 'comparison_group')), f'incomplete run: {key}')
            if kind == 'issue':
                require(item.get('state') and item.get('statement'), f'incomplete issue: {key}')
            if kind == 'batch':
                refs(item['run_ids'], runs, key)
                require(isinstance(item.get('delta'), list) and isinstance(item.get('missing_evidence'), list),
                        f'incomplete batch: {key}')
    require(data['current_batch'] in batches, 'current_batch not found')
    latest, event_ids = {}, set()
    for e in data['claim_events']:
        cid, eid = e['claim_id'], e['event_id']
        for k in (cid, eid):
            require(isinstance(k, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', k),
                    f'invalid event/claim id: {k!r}')
        require(eid not in event_ids, f'duplicate event id: {eid}')
        previous = latest.get(cid)
        require(e.get('supersedes_event_id') == (previous['event_id'] if previous else None),
                f'broken supersedes chain: {eid}')
        require(e['status'] in ('proposed', 'supported', 'refuted', 'inconclusive'), f'invalid claim status: {eid}')
        for k in ('statement', 'reason', 'reviewer', 'scope', 'time_precision'):
            require(isinstance(e.get(k), str) and e[k].strip(), f'{eid}: missing {k}')
        require('occurred_at' in e and (e['occurred_at'] is not None or e['time_precision'] == 'historical_order_only'),
                f'{eid}: unknown timestamp must be declared')
        require(isinstance(e.get('affected_proposals'), list), f'{eid}: missing impact list')
        if previous:
            require(e['statement'] == previous['statement'], f'claim meaning changed under same id: {cid}')
        refs(e['source_ids'], sources, eid)
        latest[cid] = e
        event_ids.add(eid)
    return sources, runs, issues, batches, latest


def clean(value):
    return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def check_extension(data, previous):
    if previous is None:
        return
    old = previous['claim_events']
    require(data['claim_events'][:len(old)] == old, 'historical claim events removed or rewritten')
    for key in ('sources', 'runs', 'issues', 'batches'):
        current = {x['id']: x for x in data[key]}
        for item in previous[key]:
            require(item['id'] in current, f'historical {key} entry removed: {item["id"]}')
            if key == 'sources':
                require(item['sha256'] == current[item['id']]['sha256'],
                        f'historical evidence changed under same id: {item["id"]}')


def build(data, output, source_root, previous=None):
    root = source_root.resolve(strict=True)
    sources, runs, issues, batches, latest = validate(data, root)
    check_extension(data, previous)
    require(not output.exists() and not output.is_symlink(), f'output must be new: {output}')
    # 全部输入通过后才创建输出。异常时保留partial目录，由调用方登记，不覆盖重跑。
    output.mkdir(parents=True, exist_ok=False)

    def write(rel, body):
        p = output / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('x', encoding='utf-8') as f:
            f.write(body)

    def js(rel, obj):
        write(rel, json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

    snapshot_paths = {}
    for sid, source in sources.items():
        raw = source_file(root, source['path']).read_bytes()
        require(sha(raw) == source['sha256'], f'source changed during snapshot: {sid}')
        name = Path(source['path']).name
        # 原Markdown的相对链接依赖原目录。快照保留字节并按纯文本展示，避免伪装成可搬运的网页。
        if name.lower().endswith(('.md', '.markdown')):
            name += '.txt'
        rel = f'evidence/{source["sha256"]}/{name}'
        p = output / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            with p.open('xb') as f:
                f.write(raw)
        snapshot_paths[sid] = rel

    def evidence(ids, rel):
        base = (output / rel).parent
        links = []
        for sid in ids:
            s = sources[sid]
            target = quote(os.path.relpath(output / snapshot_paths[sid], base), safe='/.-_')
            original = quote(os.path.relpath(root / s['path'], base), safe='/.-_')
            links.append(f'[{clean(sid)}快照]({target}) / [原位置]({original})')
        return ' · '.join(links)

    cur = data['current_batch']
    warning = '本地索引示例，尚未发布或经新Chat实读。'
    write('README.md', f'# ADMET实验资料入口\n\n{warning}\n\n'
          f'范围：{data["scope"]}\n\n截止：{data["as_of"]}；历史覆盖：**{data["history_coverage"]}**。\n\n'
          '从这里进入，不必递归全仓库：\n\n'
          '- [规则与项目上下文](context/README.md)\n'
          '- [历史总览、实验和失败](history/README.md)\n'
          f'- [最新批次：{cur}](batches/{cur}/README.md)\n'
          '- [当前结论及推翻记录](history/claims/README.md)\n'
          '- [未解问题与已解决问题](history/issues.md)\n\n'
          '阅读顺序：当前规则和历史总表→本批及对照→相关问题/反证→所需原件。'
          '全文保留，摘要不冒充原文；旧结论可以推翻，但不能覆盖其历史。'
          'Markdown快照按原字节纯文本保存，原文内的相对链接应从旁边的原位置访问；未声明的嵌套原件未收入快照。\n\n'
          '覆盖缺口：\n\n' + ('\n'.join('- ' + x for x in data['history_gaps']) or '- 声明范围内无缺口。') + '\n')
    write('context/README.md', '# 当前规则与上下文\n\n' +
          '\n'.join(f'- {clean(sources[x]["title"])}：{evidence([x], "context/README.md")}' for x in data['context_source_ids']) +
          '\n\n文件是证据；当前宿主规则优先于历史实现。标签可见性和公开权限分别登记。\n')
    run_table = '| 实验 | 任务 | 状态 | 比较组 | 原件 |\n|---|---|---|---|---|\n'
    for x in runs.values():
        run_table += f'| {clean(x["id"])} | {clean(x["task"])} | {clean(x["state"])} | {clean(x["comparison_group"])} | {evidence(x["source_ids"], "history/README.md")} |\n'
    write('history/README.md', '# 历史实验与失败\n\n' + f'范围：{data["scope"]}；覆盖：{data["history_coverage"]}。\n\n' + run_table +
          '\n[结论变更](claims/README.md) · [问题](issues.md) · [批次](batches.json)\n')
    js('history/runs.json', list(runs.values()))
    js('history/batches.json', list(batches.values()))
    js('history/issues.json', list(issues.values()))
    write('history/issues.md', '# 问题账本\n\n问题修复状态与科学假设真伪分开。\n\n' +
          '| ID | 状态 | 问题 | 证据 |\n|---|---|---|---|\n' + ''.join(
              f'| {x["id"]} | {clean(x["state"])} | {clean(x["statement"])} | {evidence(x["source_ids"], "history/issues.md")} |\n' for x in issues.values()))
    js('history/claims/current.json', latest)
    write('history/claims/events.jsonl', ''.join(json.dumps(e, ensure_ascii=False, allow_nan=False) + '\n' for e in data['claim_events']))
    claim_table = '# 当前结论与验证／推翻记录\n\n所有判断仅在各自scope内成立；历史不会被当前投影覆盖。\n\n| ID | 当前状态 | 命题 | 变更链 |\n|---|---|---|---|\n'
    for cid, e in latest.items():
        claim_table += f'| {cid} | {e["status"]} | {clean(e["statement"])} | [完整卡片]({cid}.md) |\n'
        rel = f'history/claims/{cid}.md'
        body = f'# {cid}\n\n命题：{e["statement"]}\n\n当前状态：**{e["status"]}**\n\n'
        for item in data['claim_events']:
            if item['claim_id'] != cid:
                continue
            body += f'**{item["event_id"]} · {item["status"]}**\n\n'
            body += f'发生时间：{item["occurred_at"] or "历史顺序已知，精确时刻未知"}。审查者：{item["reviewer"]}。\n\n'
            body += f'{item["reason"]}\n\n适用范围：{item["scope"]}\n\n证据：{evidence(item["source_ids"], rel)}\n\n'
            body += f'受影响方案／决策：{", ".join(item["affected_proposals"]) or "无"}；状态变化后由主控重新审查，不自动执行。\n\n'
        write(rel, body)
    write('history/claims/README.md', claim_table)
    for bid, b in batches.items():
        rel = f'batches/{bid}/README.md'
        write(rel, f'# 批次 {bid}\n\n[仓库历史入口](../../README.md) · [历史总表](../../history/README.md)\n\n'
              f'包含run：{", ".join(b["run_ids"])}\n\n本批变化：\n\n' + '\n'.join('- ' + x for x in b['delta']) +
              '\n\n必读证据：' + evidence(b['source_ids'], rel) + '\n\n缺口：\n\n' +
              ('\n'.join('- ' + x for x in b['missing_evidence']) or '- 声明范围内无缺口。') + '\n')
    js('reading-map.json', {'context': data['context_source_ids'], 'history': 'history/README.md',
                           'current_batch': f'batches/{cur}/README.md', 'claim_changes': 'history/claims/README.md',
                           'read_coverage_is_not_implied': True})
    js('source-manifest.json', [{**s, 'snapshot_path': snapshot_paths[s['id']],
                                'relative_links_base': str(Path(s['path']).parent),
                                'nested_linked_sources_implicitly_copied': False} for s in data['sources']])
    generated = [{'path': p.relative_to(output).as_posix(), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                 for p in sorted(output.rglob('*')) if p.is_file()]
    result = {'schema_version': 1, 'catalog_id': data['catalog_id'], 'mode': 'local_only',
              'input_sha256': sha(json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()),
              'history_coverage': data['history_coverage'], 'files': generated,
              'checks': {'source_hashes': True, 'id_references': True, 'claim_event_chains': True,
                         'previous_history_preserved': previous is not None},
              'not_verified': ['scientific_validity', 'public_access', 'fresh_chat_read', 'complete_autonomous_loop']}
    js('manifest.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--previous-input', type=Path, help='已有历史时必填；验证旧事件及实体未丢失')
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text())
        previous = json.loads(args.previous_input.read_text()) if args.previous_input else None
        result = build(data, args.output, args.source_root, previous)
    except (CatalogError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'error', 'type': type(exc).__name__, 'detail': str(exc)}, ensure_ascii=False))
        raise SystemExit(1) from exc
    print(json.dumps({'status': 'local_index_built', 'files': len(result['files']), 'mode': result['mode'],
                      'history_coverage': result['history_coverage']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
