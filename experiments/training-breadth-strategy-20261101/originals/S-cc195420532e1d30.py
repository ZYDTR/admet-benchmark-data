"""Read-only, standard-library audit. Never inspect or summarize test labels."""
import argparse
import collections
import csv
import hashlib
import json
import math
import pathlib
import statistics



def read_rows(path, role):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        # For test inputs, retain only identities and SMILES. Unexpected label
        # columns are flagged by header, never emitted or statistically examined.
        if role == 'test':
            rows = [{k: row.get(k, '') for k in ['Drug_ID', 'Drug']} for row in reader]
        else:
            rows = list(reader)
    return fields, rows

def label_stats(rows):
    missing = 0
    nonnumeric = []
    values = []
    for row in rows:
        raw = row.get('Y', '')
        if raw.strip() == '' or raw.strip().lower() in {'nan', 'na', 'none', 'null'}:
            missing += 1
            continue
        try:
            value = float(raw)
            if not math.isfinite(value):
                nonnumeric.append(raw)
            else:
                values.append(value)
        except ValueError:
            nonnumeric.append(raw)
    s = {'rows': len(rows), 'missing_labels': missing, 'nonnumeric_or_nonfinite_labels': len(nonnumeric)}
    if values:
        ordered = sorted(values)
        s.update({'min': min(values), 'max': max(values), 'mean': statistics.mean(values),
                  'median': statistics.median(values), 'unique_numeric_values': len(set(values)),
                  'zero_count': values.count(0), 'one_count': values.count(1)})
        if set(values).issubset({0, 1}):
            s['positive_fraction'] = values.count(1) / len(values)
            s['minority_count'] = min(values.count(0), values.count(1))
    return s

def role_stats(rows, labelled):
    counts = collections.Counter(r['Drug'] for r in rows)
    ids = collections.Counter(r['Drug_ID'] for r in rows)
    result = {'rows': len(rows), 'unique_raw_smiles': len(counts),
              'duplicate_raw_smiles_extra_rows': sum(n - 1 for n in counts.values()),
              'blank_smiles': sum(not r['Drug'].strip() for r in rows),
              'blank_drug_id': sum(not r['Drug_ID'].strip() for r in rows),
              'duplicate_nonblank_drug_ids_extra_rows': sum(n - 1 for v, n in ids.items() if v),
              'raw_smiles_length_min': min(map(len, counts), default=0),
              'raw_smiles_length_max': max(map(len, counts), default=0),
              'dot_containing_rows': sum('.' in r['Drug'] for r in rows),
              'at_sign_containing_rows': sum('@' in r['Drug'] for r in rows)}
    if labelled:
        by_molecule = collections.defaultdict(set)
        for r in rows:
            by_molecule[r['Drug']].add(r['Y'])
        result['duplicate_smiles_with_distinct_label_strings'] = sum(len(v) > 1 for v in by_molecule.values())
        result['labels'] = label_stats(rows)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--official-template', type=pathlib.Path)
    args = parser.parse_args()
    DATA, OUT = args.snapshot, args.output
    OUT.mkdir(parents=True, exist_ok=True)
    _, template = read_rows(DATA / 'upload_template.csv', 'template')
    task_template = collections.defaultdict(list)
    for row in template:
        task_template[row['task']].append(row)
    records = {}
    audit = {'commit': '0275588ac7a5d3df032ec7dc0794cab21dfcfeeb', 'audit_date': '2026-10-30',
             'source': 'https://github.com/ZYDTR/admet-benchmark-data',
             'authority': 'User-supplied data snapshot; not independently proven official training package',
             'limits': ['No test labels read into audit records or analyzed',
                        'Raw SMILES equality is string identity, not chemically canonical equivalence',
                        'This script only performs a byte/string audit; see the separate chemistry audit for chemical identity and scaffold observations',
                        'Label statistics do not establish units, log transforms, or assay semantics'],
             'tasks': {}}
    for task_dir in sorted((DATA / 'data_benchmark').iterdir()):
        if not task_dir.is_dir():
            continue
        task = task_dir.name
        records[task] = {}
        ts = {'splits': {}, 'headers': {}, 'metric': sorted(set(r['metric'] for r in task_template[task]))}
        for role in ['train', 'valid', 'test']:
            fields, rows = read_rows(task_dir / (role + '.csv'), role)
            records[task][role] = rows
            ts['headers'][role] = fields
            ts['splits'][role] = role_stats(rows, role != 'test')
            if role == 'test':
                ts['unexpected_test_fields'] = sorted(set(fields) - {'Drug_ID', 'Drug'})
        ts['same_task_overlap'] = {}
        for a, b in [('train','valid'),('train','test'),('valid','test')]:
            ts['same_task_overlap'][a + '_' + b] = {
                'raw_smiles': len({r['Drug'] for r in records[task][a]} & {r['Drug'] for r in records[task][b]}),
                'nonblank_drug_ids': len({r['Drug_ID'] for r in records[task][a] if r['Drug_ID']} &
                                         {r['Drug_ID'] for r in records[task][b] if r['Drug_ID']})}
        template_rows = task_template[task]
        expected = [{'sample_idx': str(i), 'drug_id': r['Drug_ID'], 'smiles': r['Drug']} for i, r in enumerate(records[task]['test'])]
        actual = [{k: r[k] for k in ['sample_idx','drug_id','smiles']} for r in template_rows]
        ts['template_test_mapping'] = {'template_rows': len(template_rows), 'test_rows': len(expected),
                                       'exact_ordered_nonprediction_match': actual == expected,
                                       'field_mismatch_counts': {k: sum(a[k] != b[k] for a, b in zip(actual, expected))
                                                                 for k in ['sample_idx','drug_id','smiles']}}
        audit['tasks'][task] = ts
    train_union = {r['Drug'] for splits in records.values() for r in splits['train']}
    valid_union = {r['Drug'] for splits in records.values() for r in splits['valid']}
    test_union = {r['Drug'] for splits in records.values() for r in splits['test']}
    for task, splits in records.items():
        other_train = {r['Drug'] for t, sp in records.items() if t != task for r in sp['train']}
        audit['tasks'][task]['cross_task_overlap'] = {
            'valid_rows_with_raw_smiles_in_another_tasks_train': sum(r['Drug'] in other_train for r in splits['valid']),
            'test_rows_with_raw_smiles_in_another_tasks_train': sum(r['Drug'] in other_train for r in splits['test'])}
    audit['totals'] = {'tasks': len(records), 'csv_files': len(list(DATA.rglob('*.csv'))),
                       'rows_by_split': {role: sum(len(s[role]) for s in records.values()) for role in ['train','valid','test']},
                       'unique_raw_smiles_by_split': {'train': len(train_union), 'valid':len(valid_union), 'test':len(test_union)},
                       'unique_raw_smiles_all': len(train_union | valid_union | test_union),
                       'metric_task_counts': dict(collections.Counter(m for t in audit['tasks'].values() for m in t['metric'])),
                       'train_valid_union_raw_smiles_intersection':len(train_union & valid_union),
                       'train_test_union_raw_smiles_intersection':len(train_union & test_union),
                       'valid_test_union_raw_smiles_intersection':len(valid_union & test_union),
                       'all_same_task_raw_smiles_split_intersections':sum(o['raw_smiles'] for t in audit['tasks'].values() for o in t['same_task_overlap'].values()),
                       'all_template_test_exact_matches': all(t['template_test_mapping']['exact_ordered_nonprediction_match'] for t in audit['tasks'].values()),
                       'template_prediction_cells_all_blank': all(r['y_pred'] == '' for r in template),
                       'template_rows':len(template)}
    old = args.official_template
    if old is not None and old.exists():
        old_fields, old_rows = read_rows(old, 'template')
        examples = []
        differences = collections.Counter()
        for row_index, (a, b) in enumerate(zip(old_rows, template)):
            for key in old_fields:
                if a[key] != b[key]:
                    differences[key] += 1
                    if len(examples) < 5:
                        examples.append({'row_index': row_index, 'task': a['task'], 'field': key,
                                         'previous_value': a[key], 'repository_value': b[key]})
        audit['previous_template_comparison'] = {
            'previous_path': str(old), 'previous_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),
            'current_sha256': hashlib.sha256((DATA/'upload_template.csv').read_bytes()).hexdigest(),
            'parsed_rows_equal': old_rows == template, 'previous_rows':len(old_rows), 'current_rows':len(template),
            'field_mismatch_counts':dict(differences), 'examples':examples}
    (OUT/'dataset-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    lines = ['# 数据快照审计', '', '来源：用户指定的 [数据仓库](https://github.com/ZYDTR/admet-benchmark-data)。',
             '', f"固定提交：`{audit['commit']}`；核对日期：2026-10-30（Asia/Shanghai）。", '',
             '## 边界', '', *['- '+v for v in audit['limits']], '',
             '## 总览', '', '```json',json.dumps(audit['totals'],ensure_ascii=False,indent=2),'```','',
             '## 逐任务', '', '| 任务 | 指标 | Train | Valid | Test | Train 正类比例 | Valid 正类/总数 |',
             '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for task, ts in audit['tasks'].items():
        sp=ts['splits']; tr=sp['train']['labels']; va=sp['valid']['labels']
        pos = f"{tr['positive_fraction']:.4f}" if 'positive_fraction' in tr else '回归'
        vp = f"{va['one_count']}/{va['rows']}" if 'positive_fraction' in va else '回归'
        lines.append(f"| {task} | {','.join(ts['metric'])} | {sp['train']['rows']} | {sp['valid']['rows']} | {sp['test']['rows']} | {pos} | {vp} |")
    lines += ['', '## 原始字符串重复与跨划分重合', '', '| 任务 | Train 重复额外行 | Valid 重复额外行 | Train/Valid 同 SMILES | Valid 分子出现在其他任务 Train 的行数 |',
              '| --- | ---: | ---: | ---: | ---: |']
    for task,ts in audit['tasks'].items():
        lines.append(f"| {task} | {ts['splits']['train']['duplicate_raw_smiles_extra_rows']} | {ts['splits']['valid']['duplicate_raw_smiles_extra_rows']} | {ts['same_task_overlap']['train_valid']['raw_smiles']} | {ts['cross_task_overlap']['valid_rows_with_raw_smiles_in_another_tasks_train']} |")
    lines += ['', '## 解释限制', '',
              '- 文件已提供固定 train/valid/test 划分；不能从目录名或任务名推断其构造算法。',
              '- 同分子在不同任务之间重合，需在多任务方案中解释信息可用性；不能自动判定为目标标签泄漏，也不能无条件忽略。',
              '- 此审计不更改样本、不补外部标签、不创建训练资产，不执行模型训练。',
              '- 标签的单位、正类生物含义及变换仍需材料佐证；数值范围本身不能确定。',
              '- 统计明细与来源哈希见 dataset-audit.json 和 snapshot-manifest.json。']
    lines += ['', '## 对调研有直接影响的发现', '',
              '- Train/Valid 所有 Y 都可解析为有限数值且无缺失；合并为多任务宽表后，未测量的任务仍必须使用缺失掩码，不能补 0。',
              '- DILI 验证集仅 48 行（13 个正类），HIA 验证集 58 行（10 个负类），CYP2C9/CYP2D6 substrate 验证集各 67 行（12/14 个正类）。单次小幅提分不足以支持强结论。',
              '- PPBR Train 有 1,952 行但仅 1,282 个原始 SMILES，其中 481 个 SMILES 出现不同标签字符串；clearance_hepatocyte Train 有 848 行、712 个原始 SMILES，136 个 SMILES 出现不同标签。重复可能反映重复测量或条件差异，不能凭重复就删除或平均。',
              '- BBB Train 中有 7 个原始 SMILES 同时出现 0 和 1 标签，Valid 中有 1 个；完全拟合训练标签不能作为这类输入的普遍验收条件。',
              '- hERG 的 Drug_ID 有空值（Train 20、Valid 1、Test 1）；不能把 Drug_ID 单独作为不可空唯一主键。',
              '- LD50 和 solubility 的 train/valid 比例明显不同于简单的 7:1:2 模式；不能凭任务名重建公开基准默认划分。',
              '- 原始 SMILES 字符串最长为 681；字符串长度不是 tokenizer token 数，更不是原子数。需单独检查候选模型 token/原子限制，不能直接据此截断。',
              '- 仓库模板与此前留存的官方模板相同位置有 7,611 个 drug_id 字符串差异，其他字段相同；各 test.csv 与仓库模板亦只有该字段出现 7,611 个差异。须单独固定用于最终导出的官方模板版本，不依赖 Drug_ID 自动归一化对齐。']
    (OUT/'dataset-audit.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(audit['totals'],ensure_ascii=False,indent=2))
    print(json.dumps(audit.get('previous_template_comparison'),ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
