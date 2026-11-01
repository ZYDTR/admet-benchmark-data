"""Lossless ADMET cleaning, weighted exact-observation deduplication and audit.

Only the requested new output directory is written. Original splits, row order,
IDs, SMILES and label text remain recoverable from the lossless output tables.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import decimal
import hashlib
import html
import importlib.metadata
import json
import logging
import math
import pathlib
import platform
import re
import statistics
import sys

from rdkit import Chem, RDLogger, rdBase
from rdkit.Chem.Scaffolds import MurckoScaffold

PACKAGE = pathlib.Path(__file__).resolve().parents[1]
SPLITS = ("train", "valid", "test")
NUMERIC = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
FIELDS = [
    "task", "split", "sample_idx", "row_id", "drug_id", "smiles_original",
    "smiles", "canonical_smiles", "molecule_id", "y", "y_original",
    "task_type", "metric", "parse_status", "label_status",
    "graph_eligible", "supervised_eligible", "needs_structure_fallback",
    "scaffold_smiles", "scaffold_id", "scaffold_type", "fragment_count",
    "atom_count", "formal_charge", "molecule_observation_count",
    "identical_observation_count", "label_conflict", "sample_weight", "issue_codes",
]
MOLECULE_FIELDS = [
    "molecule_id", "representative_smiles_original", "canonical_smiles", "parse_status",
    "parse_error", "scaffold_smiles", "scaffold_id", "scaffold_type",
    "fragment_count", "atom_count", "formal_charge", "record_count", "task_count", "splits",
]
ISSUE_FIELDS = ["task", "split", "sample_idx", "row_id", "molecule_id", "issue_code", "detail"]
DUP_FIELDS = ["task", "split", "molecule_id", "y", "record_count", "source_row_ids"]
CONFLICT_FIELDS = ["task", "split", "molecule_id", "distinct_labels", "record_count", "source_row_ids"]


def sha256(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_text(text, prefix):
    return prefix + hashlib.sha256(text.encode("utf-8")).hexdigest()


def dump_json(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, fields, rows):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def read_source(path, split):
    with pathlib.Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ["Drug_ID", "Drug"] + ([] if split == "test" else ["Y"])
        if reader.fieldnames != expected:
            raise ValueError(f"Unexpected columns in {path}: {reader.fieldnames}; expected {expected}")
        rows = list(reader)
    if not rows or any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError(f"Empty file or malformed CSV record in {path}")
    return rows


def normalize_label(raw, task_type, split):
    if split == "test":
        return "", "not_provided"
    value = raw.strip()
    if not value:
        return "", "missing"
    if not NUMERIC.fullmatch(value):
        return "", "invalid_numeric"
    number = decimal.Decimal(value)
    if not number.is_finite() or not math.isfinite(float(number)):
        return "", "invalid_numeric"
    if task_type == "classification" and number not in (0, 1):
        return "", "invalid_binary_label"
    # Decimal formatting avoids changing a scientific measurement by float rounding.
    normalized = format(number, "f") if number else "0"
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized, "valid"


def inspect_smiles(raw):
    value = raw.strip()
    mol = None
    error = "empty SMILES" if not value else ""
    if value:
        try:
            mol = Chem.MolFromSmiles(value)
        except Exception as exc:
            error = str(exc)
    if mol is None:
        if value and not error:
            try:
                unsanitized = Chem.MolFromSmiles(value, sanitize=False)
                if unsanitized is not None:
                    problems = Chem.DetectChemistryProblems(unsanitized)
                    error = "; ".join(p.Message() for p in problems)
            except Exception as exc:
                error = str(exc)
        return {
            "molecule_id": digest_text(value, "invalid_"), "canonical_smiles": "",
            "parse_status": "invalid", "parse_error": error or "RDKit default parse/sanitization failed",
            "scaffold_smiles": "", "scaffold_id": "", "scaffold_type": "unavailable",
            "fragment_count": "", "atom_count": "", "formal_charge": "",
        }
    canonical = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)
    return {
        "molecule_id": digest_text(canonical, "mol_"), "canonical_smiles": canonical,
        "parse_status": "valid", "parse_error": "", "scaffold_smiles": scaffold,
        "scaffold_id": digest_text(scaffold, "scf_") if scaffold else "",
        "scaffold_type": "ring_scaffold" if scaffold else "acyclic",
        "fragment_count": len(Chem.GetMolFrags(mol)), "atom_count": mol.GetNumAtoms(),
        "formal_charge": Chem.GetFormalCharge(mol),
    }


def annotate_group(rows):
    molecules = collections.defaultdict(list)
    observations = collections.defaultdict(list)
    ids = collections.Counter(row["drug_id"] for row in rows if row["drug_id"])
    for row in rows:
        molecules[row["molecule_id"]].append(row)
        observations[(row["molecule_id"], row["y"] if row["label_status"] == "valid" else row["y_original"])].append(row)
    conflicts = []
    duplicate_groups = []
    for molecule_id, group in molecules.items():
        labels = sorted({row["y"] for row in group if row["label_status"] == "valid"}, key=decimal.Decimal)
        conflict = len(labels) > 1
        for row in group:
            row["molecule_observation_count"] = len(group)
            row["label_conflict"] = int(conflict)
            if conflict:
                row["_issues"].append(("CONFLICTING_LABELS", "Same molecule and task has multiple observed labels; all retained"))
        if conflict:
            conflicts.append({"task": group[0]["task"], "split": group[0]["split"],
                              "molecule_id": molecule_id, "distinct_labels": json.dumps(labels),
                              "record_count": len(group), "source_row_ids": json.dumps([r["row_id"] for r in group])})
    for (molecule_id, label), group in observations.items():
        for row in group:
            row["identical_observation_count"] = len(group)
            if len(group) > 1:
                row["_issues"].append(("REPEATED_TEST_STRUCTURE" if row["split"] == "test" else "DUPLICATE_OBSERVATION",
                                       "Repeated molecule/label (or test molecule); original rows and order retained"))
        if len(group) > 1:
            duplicate_groups.append({"task": group[0]["task"], "split": group[0]["split"],
                                     "molecule_id": molecule_id, "y": label, "record_count": len(group),
                                     "source_row_ids": json.dumps([r["row_id"] for r in group])})
    for row in rows:
        if row["drug_id"] and ids[row["drug_id"]] > 1:
            row["_issues"].append(("DUPLICATE_DRUG_ID", "ID is not a unique row key; use task/split/sample_idx"))
    dedup = []
    if rows and rows[0]["split"] == "train":
        seen = set()
        for row in rows:
            key = (row["molecule_id"], row["y"] if row["label_status"] == "valid" else row["y_original"])
            if key in seen:
                continue
            seen.add(key)
            group = observations[key]
            # The representative retains provenance; weighting preserves observation multiplicity.
            selected = {field: row[field] for field in FIELDS if field != "issue_codes"}
            selected["issue_codes"] = ";".join(sorted({code for code, _ in row["_issues"]}))
            selected["sample_weight"] = len(group)
            selected["source_row_ids"] = json.dumps([r["row_id"] for r in group])
            dedup.append(selected)
    return conflicts, duplicate_groups, dedup


def snapshot_sources(source, tasks):
    result = {}
    for task in sorted(tasks):
        for split in SPLITS:
            rel = f"{task}/{split}.csv"
            path = source / rel
            result[rel] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    return result


def validate_output_location(source, output, tasks):
    source, output = source.resolve(), output.resolve()
    if output == source or output in source.parents:
        raise ValueError("Output may not be the input root or its ancestor")
    for task in tasks:
        original_dir = (source / task).resolve()
        if output == original_dir or original_dir in output.parents:
            raise ValueError(f"Output may not be inside an original dataset: {output}")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite an existing output directory: {output}")


def table_html(fields, rows):
    return "<table><thead><tr>" + "".join(f"<th>{html.escape(str(x))}</th>" for x in fields) + "</tr></thead><tbody>" + "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(row.get(x, '')))}</td>" for x in fields) + "</tr>" for row in rows) + "</tbody></table>"


def render_report(path, summary, split_summary):
    per_task = []
    for name in summary["tasks"]:
        group = {r["split"]: r for r in split_summary if r["task"] == name}
        per_task.append({"任务": name, "指标": group["train"]["metric"],
                         "训练": group["train"]["rows"], "验证": group["valid"]["rows"], "测试": group["test"]["rows"],
                         "训练去重后": group["train"]["deduplicated_rows"],
                         "训练冲突分子": group["train"]["conflicting_label_molecules"]})
    sections = """
<p>本次只做数据整理和质量标记。未训练模型、未重新划分数据、未使用外部训练数据、未对标签做缩放或对数变换。</p>
<h2>处理规则</h2><ul>
<li>读取 UTF-8 BOM，统一列名；ID 始终作为字符串，原始空值、前导零等不推断成数值。</li>
<li>逐行保留原始 SMILES 和标签文本，另存 RDKit 规范化且保留立体信息的 SMILES。未去盐、未中和、未统一互变异构体。</li>
<li>训练、验证、测试原始行数、顺序及划分保持不变。测试无标签，y 列留空。</li>
<li>训练另提供 train_deduplicated.csv：仅合并同一任务、同一分子、同一数值标签，sample_weight 为原观测条数。不同标签保留为不同观测。</li>
<li>解析失败不猜测修复、不删除，用 needs_structure_fallback=1 标记。测试推理必须覆盖这些行。</li>
<li>空 Murcko 骨架标记为 acyclic；scaffold_id 留空，不能把全部空值直接当同一交叉验证分组。</li>
</ul>
<h2>使用入口</h2><ul>
<li>单任务：tasks/&lt;task&gt;/train.csv、valid.csv、test.csv。</li>
<li>需要压缩重复训练观测：tasks/&lt;task&gt;/train_deduplicated.csv，读取 sample_weight 和 source_row_ids。</li>
<li>多任务：multitask/train.csv、valid.csv、test.csv，采用长表保留重复测量。禁止按 molecule_id 无条件合并三个 split。</li>
<li>提交映射：submission/test_row_mapping.csv；严格使用 task + sample_idx，对照 reference/submission_template.csv，只填写官方模板的 y_pred。</li>
<li>机器可读审计：reports/summary.json、split_summary.csv、issues.csv、label_conflicts.csv、scaffold_distribution.csv、cross_split_molecules.csv。</li>
</ul>
<h2>建模时需要注意</h2><ul>
<li>AMES 官方验证集集中在苯环骨架，水溶性及 LD50 验证集集中在无环分子。见 scaffold_distribution.csv；不能将单个验证结果当作所有结构的泛化表现。</li>
<li>相同分子可能出现在不同任务的不同 split。其他任务的训练标签并不自动构成同端点标签泄漏，但未见分子验证需跨任务统一分组。</li>
<li>重复测量和标签冲突是质量标记，不等于错误数据。验证和测试重复行均保留，按官方行权重评价。</li>
<li>所有拟合型处理（填补、标准化、特征选择、标签变换）必须在后续各训练折内部进行。</li>
</ul>
"""
    body = f"<h1>ADMET 数据清洗与整理</h1><p>任务 {len(summary['tasks'])} 个；原始 CSV {summary['source_file_count']} 个；原始文件 SHA-256 前后校验：一致。</p>"
    metrics = [{"项目": k, "数量": v} for k, v in summary["counts"].items() if isinstance(v, (str, int, float))]
    body += table_html(["项目", "数量"], metrics) + sections + "<h2>任务统计</h2>" + table_html(list(per_task[0]), per_task)
    path.write_text("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
                    "<title>ADMET 数据清洗报告</title><style>body{max-width:1180px;margin:36px auto;padding:0 24px;font:16px/1.7 system-ui,sans-serif;color:#182536}"
                    "h1,h2{line-height:1.3}h2{margin-top:32px}table{border-collapse:collapse;width:100%;font-size:14px;margin:18px 0}"
                    "td,th{padding:8px 12px;border-bottom:1px solid #dde3ea;text-align:left;overflow-wrap:anywhere}th{background:#edf2f7}li{margin:8px 0}</style>"
                    + body + "</html>\n", encoding="utf-8")


def run(source, output, config_path, template_path):
    tasks = json.loads(config_path.read_text(encoding="utf-8"))
    validate_output_location(source, output, tasks)
    before = snapshot_sources(source, tasks)
    output.mkdir(parents=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(output / "run.log", encoding="utf-8")], force=True)
    dump_json(output / "source_manifest_before.json", before)
    RDLogger.DisableLog("rdApp.*")
    raw = {(task, split): read_source(source / task / f"{split}.csv", split) for task in sorted(tasks) for split in SPLITS}
    logging.info("Loaded %d rows from %d original CSV files", sum(map(len, raw.values())), len(raw))
    unique_smiles = sorted({r["Drug"] for rows in raw.values() for r in rows})
    chemistry = {}
    for i, smiles in enumerate(unique_smiles, 1):
        chemistry[smiles] = inspect_smiles(smiles)
        if i % 10000 == 0:
            logging.info("Parsed %d / %d unique SMILES", i, len(unique_smiles))
    logging.info("Chemistry checks complete; %d unique SMILES require fallback", sum(c["parse_status"] != "valid" for c in chemistry.values()))
    processed = {}; all_issues = []; conflicts = []; duplicates = []; split_summary = []; scaffold_rows = []
    all_dedup = []; molecule_records = collections.defaultdict(list)
    for (task, split), source_rows in raw.items():
        rows = []
        for idx, original in enumerate(source_rows):
            chem = chemistry[original["Drug"]]
            raw_y = original.get("Y", "")
            label, label_status = normalize_label(raw_y, tasks[task]["task_type"], split)
            valid_structure = chem["parse_status"] == "valid"
            row = {
                "task": task, "split": split, "sample_idx": idx, "row_id": f"{task}/{split}/{idx:06d}",
                "drug_id": original["Drug_ID"], "smiles_original": original["Drug"],
                "smiles": chem["canonical_smiles"] or original["Drug"].strip(),
                "canonical_smiles": chem["canonical_smiles"], "molecule_id": chem["molecule_id"],
                "y": label, "y_original": raw_y, **tasks[task], "parse_status": chem["parse_status"],
                "label_status": label_status, "graph_eligible": int(valid_structure),
                "supervised_eligible": int(valid_structure and label_status == "valid"),
                "needs_structure_fallback": int(not valid_structure),
                **{k: chem[k] for k in ["scaffold_smiles", "scaffold_id", "scaffold_type", "fragment_count", "atom_count", "formal_charge"]},
                "sample_weight": 1, "_issues": [],
            }
            if not original["Drug_ID"]:
                row["_issues"].append(("EMPTY_DRUG_ID", "Original empty ID retained; row_id is the internal key"))
            if original["Drug"] != original["Drug"].strip():
                row["_issues"].append(("SMILES_OUTER_WHITESPACE", "Outer whitespace removed only in model input; raw text retained"))
            if not valid_structure:
                row["_issues"].append(("INVALID_SMILES", chem["parse_error"]))
            if label_status not in ("valid", "not_provided"):
                row["_issues"].append(("INVALID_LABEL", label_status))
            rows.append(row)
        task_conflicts, task_duplicates, dedup = annotate_group(rows)
        conflicts.extend(task_conflicts); duplicates.extend(task_duplicates); all_dedup.extend(dedup)
        for row in rows:
            issues = row.pop("_issues")
            row["issue_codes"] = ";".join(sorted({code for code, _ in issues}))
            all_issues.extend({**{k: row[k] for k in ISSUE_FIELDS[:5]}, "issue_code": code, "detail": detail} for code, detail in issues)
            molecule_records[row["molecule_id"]].append(row)
        processed[(task, split)] = rows
        write_csv(output / "tasks" / task / f"{split}.csv", FIELDS, rows)
        if split == "train":
            write_csv(output / "tasks" / task / "train_deduplicated.csv", FIELDS + ["source_row_ids"], dedup)
        ys = [float(r["y"]) for r in rows if r["label_status"] == "valid"]
        scount = collections.Counter((r["scaffold_type"], r["scaffold_id"], r["scaffold_smiles"]) for r in rows)
        for (stype, sid, smi), count in sorted(scount.items()):
            scaffold_rows.append({"task": task, "split": split, "scaffold_type": stype, "scaffold_id": sid,
                                  "scaffold_smiles": smi, "rows": count, "audit_only_acyclic_bucket": int(stype == "acyclic")})
        split_summary.append({
            "task": task, "split": split, **tasks[task], "rows": len(rows),
            "unique_molecules": len({r["molecule_id"] for r in rows}),
            "invalid_smiles_rows": sum(r["parse_status"] != "valid" for r in rows),
            "missing_id_rows": sum(not r["drug_id"] for r in rows),
            "invalid_label_rows": sum(r["label_status"] not in ("valid", "not_provided") for r in rows),
            "duplicate_observation_extra_rows": sum(x["record_count"] - 1 for x in task_duplicates),
            "conflicting_label_molecules": len(task_conflicts),
            "deduplicated_rows": len(dedup) if split == "train" else "",
            "acyclic_rows": sum(r["scaffold_type"] == "acyclic" for r in rows),
            "nonempty_scaffold_count": sum(bool(sid) for _, sid, _ in scount),
            "largest_nonempty_scaffold_rows": max((n for (_, sid, _), n in scount.items() if sid), default=0),
            "positive_rows": sum(y == 1 for y in ys) if tasks[task]["task_type"] == "classification" and ys else "",
            "positive_fraction": sum(ys) / len(ys) if tasks[task]["task_type"] == "classification" and ys else "",
            "y_min": min(ys) if ys else "", "y_median": statistics.median(ys) if ys else "", "y_max": max(ys) if ys else "",
        })
    for split in SPLITS:
        write_csv(output / "multitask" / f"{split}.csv", FIELDS,
                  (row for task in sorted(tasks) for row in processed[(task, split)]))
    write_csv(output / "multitask/train_deduplicated.csv", FIELDS + ["source_row_ids"], all_dedup)
    molecules = []; cross_split = []
    for molecule_id, rows in sorted(molecule_records.items()):
        first = rows[0]; chem = chemistry[first["smiles_original"]]
        splits = sorted({r["split"] for r in rows}); task_names = sorted({r["task"] for r in rows})
        molecules.append({**chem, "representative_smiles_original": first["smiles_original"],
                          "record_count": len(rows), "task_count": len(task_names), "splits": ";".join(splits)})
        if len(splits) > 1:
            split_tasks = {s: sorted({r["task"] for r in rows if r["split"] == s}) for s in SPLITS}
            same_task = any(len({r["split"] for r in rows if r["task"] == t}) > 1 for t in task_names)
            cross_split.append({"molecule_id": molecule_id, "splits": ";".join(splits), "record_count": len(rows),
                                "same_task_cross_split": int(same_task),
                                **{s + "_tasks": ";".join(split_tasks[s]) for s in SPLITS}})
    write_csv(output / "molecules.csv", MOLECULE_FIELDS, molecules)
    write_csv(output / "reports/cross_split_molecules.csv", ["molecule_id", "splits", "record_count", "same_task_cross_split", "train_tasks", "valid_tasks", "test_tasks"], cross_split)
    within_overlap = []
    for task in sorted(tasks):
        for a, b in [("train", "valid"), ("train", "test"), ("valid", "test")]:
            ids = {r["molecule_id"] for r in processed[(task, a)]} & {r["molecule_id"] for r in processed[(task, b)]}
            within_overlap.append({"task": task, "split_a": a, "split_b": b, "overlapping_molecules": len(ids)})
    write_csv(output / "reports/within_task_split_overlap.csv", ["task", "split_a", "split_b", "overlapping_molecules"], within_overlap)
    write_csv(output / "reports/split_summary.csv", list(split_summary[0]), split_summary)
    write_csv(output / "reports/issues.csv", ISSUE_FIELDS, all_issues)
    write_csv(output / "reports/label_conflicts.csv", CONFLICT_FIELDS, conflicts)
    write_csv(output / "reports/duplicate_groups.csv", DUP_FIELDS, duplicates)
    write_csv(output / "reports/scaffold_distribution.csv", list(scaffold_rows[0]), scaffold_rows)
    invalid_rows = [r for rows in processed.values() for r in rows if r["parse_status"] == "invalid"]
    write_csv(output / "reports/invalid_smiles.csv", FIELDS + ["parse_error"],
              ({**r, "parse_error": chemistry[r["smiles_original"]]["parse_error"]} for r in invalid_rows))
    with template_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["task", "sample_idx", "drug_id", "smiles", "y_pred", "metric"]:
            raise ValueError("Unexpected official template columns")
        template = list(reader)
    mapping = []; keys = set()
    for index, item in enumerate(template):
        key = (item["task"], int(item["sample_idx"]))
        if key in keys:
            raise ValueError(f"Duplicate official template row key: {key}")
        keys.add(key)
        row = processed[(key[0], "test")][key[1]]
        if (item["drug_id"], item["smiles"], item["metric"]) != (row["drug_id"], row["smiles_original"], row["metric"]):
            raise ValueError(f"Official template does not match original test row: {key}")
        mapping.append({"template_row": index, **{k: row[k] for k in ["task", "sample_idx", "row_id", "drug_id", "smiles_original", "molecule_id", "parse_status", "needs_structure_fallback", "metric"]}})
    if len(keys) != sum(len(rows) for (task, split), rows in processed.items() if split == "test"):
        raise ValueError("Official template does not cover all test rows exactly once")
    write_csv(output / "submission/test_row_mapping.csv", list(mapping[0]), mapping)
    after = snapshot_sources(source, tasks)
    dump_json(output / "source_manifest_after.json", after)
    if before != after:
        raise RuntimeError("Original source files changed during processing; outputs must not be used")
    train_ids = {r["molecule_id"] for (t, s), rows in processed.items() if s == "train" for r in rows}
    valid_ids = {r["molecule_id"] for (t, s), rows in processed.items() if s == "valid" for r in rows}
    counts = {s + "_rows": sum(len(rows) for (t, sp), rows in processed.items() if sp == s) for s in SPLITS}
    counts.update({"all_rows": sum(map(len, processed.values())), "unique_raw_smiles": len(chemistry),
                   "unique_valid_molecules": sum(m["parse_status"] == "valid" for m in molecules),
                   "unique_labeled_molecules": len(train_ids | valid_ids), "train_deduplicated_rows": len(all_dedup),
                   "train_exact_duplicate_rows_collapsed": counts["train_rows"] - len(all_dedup),
                   "invalid_smiles_rows": len(invalid_rows), "empty_id_rows": sum(not r["drug_id"] for rows in processed.values() for r in rows),
                   "invalid_label_rows": sum(r["label_status"] not in ("valid", "not_provided") for rows in processed.values() for r in rows),
                   "conflicting_molecule_task_split_groups": len(conflicts),
                   "within_task_cross_split_overlap_total": sum(r["overlapping_molecules"] for r in within_overlap),
                   "cross_task_train_valid_molecule_overlap": len(train_ids & valid_ids), "official_template_rows": len(template)})
    summary = {"tasks": sorted(tasks), "source_file_count": len(before), "counts": counts,
               "issue_code_counts": dict(sorted(collections.Counter(r["issue_code"] for r in all_issues).items())),
               "original_files_unchanged": True, "test_template_matches": True,
               "no_label_transform_or_imputation": True, "no_split_changes": True,
               "deduplication": "train only; same molecule + numerically identical label; multiplicity in sample_weight",
               "chemistry_policy": "RDKit default sanitization; isomeric canonical SMILES; no salt stripping, neutralization, tautomer normalization or guessed repairs"}
    dump_json(output / "reports/summary.json", summary)
    render_report(output / "reports/cleaning_report.html", summary, split_summary)
    versions = {name: importlib.metadata.version(name) for name in ["rdkit", "numpy", "pillow"]}
    artifacts = {p.relative_to(output).as_posix(): sha256(p) for p in sorted(output.rglob("*")) if p.is_file() and p.name != "run.log"}
    implementation = [p for p in sorted((PACKAGE / "scripts").glob("*")) if p.is_file()]
    implementation += [PACKAGE / "run_cleaning.sh", config_path]
    implementation += [p for p in [PACKAGE / "requirements.txt", PACKAGE / "requirements.lock.txt"] if p.exists()]
    manifest = {"pipeline_schema_version": 1, "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "source_root": str(source), "output_root": str(output), "config_path": str(config_path),
                "template_path": str(template_path), "template_sha256": sha256(template_path),
                "python_version": platform.python_version(), "platform": platform.platform(), "package_versions": versions,
                "rdkit_version": rdBase.rdkitVersion, "source_files": before,
                "source_hashes_verified_unchanged": True,
                "implementation_sha256": {str(p.relative_to(PACKAGE)) if p.is_relative_to(PACKAGE) else str(p): sha256(p) for p in implementation},
                "output_sha256": artifacts, "counts": counts}
    dump_json(output / "manifest.json", manifest)
    logging.info("Finished. Original file hashes unchanged. Counts: %s", counts)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=pathlib.Path, default=PACKAGE.parent)
    parser.add_argument("--output-dir", type=pathlib.Path, default=PACKAGE / "processed")
    parser.add_argument("--config", type=pathlib.Path, default=PACKAGE / "config/tasks.json")
    parser.add_argument("--template", type=pathlib.Path, default=PACKAGE / "reference/submission_template.csv")
    args = parser.parse_args()
    run(args.source_dir.resolve(), args.output_dir.resolve(), args.config.resolve(), args.template.resolve())


if __name__ == "__main__":
    main()
