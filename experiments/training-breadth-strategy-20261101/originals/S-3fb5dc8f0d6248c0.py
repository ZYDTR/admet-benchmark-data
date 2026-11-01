"""Independently verify source immutability, row provenance and deduplication."""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import decimal
import hashlib
import json
import pathlib
import sys

PACKAGE = pathlib.Path(__file__).resolve().parents[1]


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def hash_file(path):
    with pathlib.Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_csv(path):
    with pathlib.Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def verify(output, source=None, deep=False):
    output = output.resolve()
    manifest = json.loads((output / "manifest.json").read_text())
    source = (source or pathlib.Path(manifest["source_root"])).resolve()
    config_path = pathlib.Path(manifest["config_path"])
    template_path = pathlib.Path(manifest["template_path"])
    tasks = json.loads(config_path.read_text())
    before = json.loads((output / "source_manifest_before.json").read_text())
    after = json.loads((output / "source_manifest_after.json").read_text())
    check(before == after == manifest["source_files"], "Before/after source manifests differ")
    for relative, metadata in before.items():
        path = source / relative
        check(hash_file(path) == metadata["sha256"] and path.stat().st_size == metadata["bytes"], f"Original modified: {relative}")
    for relative, expected in manifest["output_sha256"].items():
        check(hash_file(output / relative) == expected, f"Generated output changed: {relative}")
    for relative, expected in manifest["implementation_sha256"].items():
        check(hash_file(PACKAGE / relative) == expected, f"Implementation changed since run: {relative}")
    check(hash_file(template_path) == manifest["template_sha256"], "Official template snapshot changed")
    row_count = collections.Counter(); combined = collections.defaultdict(list)
    all_rows = {}; molecule_rows = collections.defaultdict(list); combined_dedup = []
    canonical_cache = {}
    if deep:
        from rdkit import Chem, RDLogger
        RDLogger.DisableLog("rdApp.*")
    for task in sorted(tasks):
        for split in ("train", "valid", "test"):
            original = read_csv(source / task / f"{split}.csv")
            cleaned = read_csv(output / "tasks" / task / f"{split}.csv")
            check(len(original) == len(cleaned), f"Row count changed: {task}/{split}")
            for index, (raw, row) in enumerate(zip(original, cleaned)):
                key = f"{task}/{split}/{index:06d}"
                check(row["row_id"] == key and row["sample_idx"] == str(index), f"Row order or ID mismatch: {key}")
                check(row["task"] == task and row["split"] == split, f"Split/task changed: {key}")
                check(row["drug_id"] == raw["Drug_ID"], f"Original ID changed: {key}")
                check(row["smiles_original"] == raw["Drug"], f"Original SMILES changed: {key}")
                check(row["y_original"] == raw.get("Y", ""), f"Original label text changed: {key}")
                check(row["sample_weight"] == "1", f"Lossless view weight changed: {key}")
                if split == "test":
                    check(row["y"] == "" and row["label_status"] == "not_provided" and row["supervised_eligible"] == "0", f"Test labels introduced: {key}")
                elif row["label_status"] == "valid":
                    check(decimal.Decimal(row["y"]) == decimal.Decimal(raw["Y"]), f"Label value changed: {key}")
                    if tasks[task]["task_type"] == "classification":
                        check(row["y"] in ("0", "1"), f"Invalid binary label: {key}")
                else:
                    check(row["y"] == "" and row["supervised_eligible"] == "0", f"Invalid label treated as valid: {key}")
                check(row["metric"] == tasks[task]["metric"], f"Metric mismatch: {key}")
                if deep:
                    smi = raw["Drug"].strip()
                    if smi not in canonical_cache:
                        mol = Chem.MolFromSmiles(smi) if smi else None
                        canonical_cache[smi] = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True) if mol is not None else ""
                    check(row["canonical_smiles"] == canonical_cache[smi], f"Canonical structure mismatch: {key}")
                canonical = row["canonical_smiles"]
                if canonical:
                    check(row["parse_status"] == "valid" and row["needs_structure_fallback"] == "0" and row["graph_eligible"] == "1", f"Valid structure flags inconsistent: {key}")
                    check(row["smiles"] == canonical, f"Canonical model input mismatch: {key}")
                    expected_id = "mol_" + hashlib.sha256(canonical.encode()).hexdigest()
                else:
                    check(row["parse_status"] == "invalid" and row["needs_structure_fallback"] == "1" and row["graph_eligible"] == "0", f"Invalid structure silently accepted: {key}")
                    expected_id = "invalid_" + hashlib.sha256(raw["Drug"].strip().encode()).hexdigest()
                check(row["molecule_id"] == expected_id, f"Unstable molecule identity: {key}")
                if row["scaffold_type"] == "acyclic":
                    check(row["scaffold_id"] == row["scaffold_smiles"] == "", f"Acyclic scaffold mislabeled: {key}")
                check(key not in all_rows, f"Duplicate row_id: {key}")
                all_rows[key] = row; molecule_rows[row["molecule_id"]].append(row)
            row_count[split] += len(cleaned); combined[split].extend(cleaned)
        original_train = {r["row_id"]: r for r in combined["train"] if r["task"] == task}
        dedup = read_csv(output / "tasks" / task / "train_deduplicated.csv")
        covered = []; keys = set()
        for row in dedup:
            ids = json.loads(row["source_row_ids"])
            check(bool(ids) and int(row["sample_weight"]) == len(ids), f"Incorrect duplicate weight: {task}")
            check(ids[0] == row["row_id"], f"Representative provenance lost: {task}")
            target = row["y"] if row["label_status"] == "valid" else row["y_original"]
            key = (row["molecule_id"], target)
            check(key not in keys, f"Deduplicated observation still repeated: {task}")
            keys.add(key)
            for row_id in ids:
                check(row_id in original_train, f"Cross-split or foreign row entered training: {row_id}")
                source_row = original_train[row_id]
                source_target = source_row["y"] if source_row["label_status"] == "valid" else source_row["y_original"]
                check((source_row["molecule_id"], source_target) == key, f"Conflicting measurements merged: {row_id}")
            covered.extend(ids)
        check(collections.Counter(covered) == collections.Counter(original_train.keys()), f"Missing or duplicated provenance after dedup: {task}")
        check(sum(int(r["sample_weight"]) for r in dedup) == len(original_train), f"Weighted observation count changed: {task}")
        combined_dedup.extend(dedup)
    for split in ("train", "valid", "test"):
        check(read_csv(output / "multitask" / f"{split}.csv") == combined[split], f"Multitask view differs from task files: {split}")
    check(read_csv(output / "multitask/train_deduplicated.csv") == combined_dedup, "Multitask deduplicated view mismatch")
    molecules = read_csv(output / "molecules.csv")
    check(len(molecules) == len(molecule_rows), "Molecule registry cardinality mismatch")
    check({m["molecule_id"] for m in molecules} == set(molecule_rows), "Molecule registry does not cover observations")
    for molecule in molecules:
        check(int(molecule["record_count"]) == len(molecule_rows[molecule["molecule_id"]]), "Molecule observation count mismatch")
    template = read_csv(template_path)
    mapping = read_csv(output / "submission/test_row_mapping.csv")
    check(len(template) == len(mapping) == row_count["test"], "Submission mapping count mismatch")
    mapped = set()
    for index, (ref, row) in enumerate(zip(template, mapping)):
        key = f"{ref['task']}/test/{int(ref['sample_idx']):06d}"
        check(row["template_row"] == str(index) and row["row_id"] == key, "Submission row order changed")
        check(key not in mapped, "Duplicate submission mapping key")
        mapped.add(key)
        check(row["drug_id"] == ref["drug_id"] == all_rows[key]["drug_id"], "Submission ID mismatch")
        check(row["smiles_original"] == ref["smiles"] == all_rows[key]["smiles_original"], "Submission SMILES mismatch")
        check(row["metric"] == ref["metric"] == all_rows[key]["metric"], "Submission metric mismatch")
    summary = json.loads((output / "reports/summary.json").read_text())
    for split, count in row_count.items():
        check(summary["counts"][split + "_rows"] == count, "Summary row count mismatch")
    check(summary["counts"]["train_deduplicated_rows"] == len(combined_dedup), "Summary dedup count mismatch")
    result = {
        "status": "passed", "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "deep_rdkit_check": deep, "original_files_verified": len(before),
        "output_checksums_verified": len(manifest["output_sha256"]),
        "rows_checked": sum(row_count.values()), "row_counts": dict(row_count),
        "deduplicated_train_rows": len(combined_dedup),
        "deduplicated_train_weight_sum": sum(int(r["sample_weight"]) for r in combined_dedup),
        "template_rows_checked": len(mapping),
        "checks": ["source files unchanged", "output hashes", "implementation hashes", "original row order and split",
                   "ID and original SMILES preserved", "labels unchanged", "no test labels introduced",
                   "weighted dedup provenance complete", "conflicting labels not collapsed",
                   "multitask views identical to per-task views", "molecule registry coverage", "official template alignment"],
    }
    if deep:
        result["checks"].append("independent RDKit canonicalization of every unique source SMILES")
    (output / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=pathlib.Path, default=PACKAGE / "processed")
    parser.add_argument("--source-dir", type=pathlib.Path)
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.output_dir, args.source_dir, args.deep), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
