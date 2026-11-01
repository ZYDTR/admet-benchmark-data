#!/usr/bin/env python3
"""verify-data: integrity + identity check of inputs and template.

Checks, using only the task package inputs:
  * every task has train.csv (Drug_ID,Drug,Y) and test.csv (Drug_ID,Drug)
  * no dropped rows relative to the registered validation projection
  * template: 16379 rows, 22 tasks, per-task sample_idx is 0..n-1 unique
  * template rows == test.csv rows, matched by (drug_id, smiles) at each
    zero-based row_index  (this is the sample_idx <-> original row relation)
  * all train Y parse as finite numbers; classification tasks are strictly 0/1
  * input sha256 for every file; split identity digest for reuse by score/export

Writes a JSON report (default: stdout).  Does NOT clean or modify inputs.
Exit 0 on success, 2 on any contract failure, 3 on internal/unexpected error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from admet_eval import common as C  # noqa: E402


def verify(official_base, blind_base, template_path, schema_path, report_path):
    report = {"ok": False, "checks": {}, "files": {}, "splits": {}}
    err = None
    try:
        # 1. schema derived from template bytes, cross-checked against file
        derived = C.build_schema_from_template(template_path)
        if schema_path:
            C.load_and_check_schema(schema_path, template_path)
        report["checks"]["schema_from_template"] = {
            "pass": True,
            "template_sha256": derived["source_template_sha256"],
            "template_rows": derived["template_rows"],
            "n_tasks": len(derived["tasks"]),
        }

        # 2. template structure
        traw = C.read_bytes(template_path)
        theader, trows = C.parse_csv(traw, template_path)
        report["checks"]["template_header"] = {
            "pass": theader == list(C.REQUIRED_TEMPLATE_FIELDS),
            "header": theader,
        }
        report["checks"]["template_rows"] = {
            "pass": len(trows) == 16379, "actual": len(trows), "expected": 16379,
        }
        report["checks"]["template_format"] = C.sniff_format(traw)

        task_meta = {t["task"]: t for t in derived["tasks"]}
        template_by_task = {t: [] for t in task_meta}
        for ri, row in enumerate(trows):
            rec = dict(zip(theader, row))
            template_by_task[rec["task"]].append((ri, rec))

        # sample_idx values are per-task and 0..n-1 unique; they are NOT the
        # absolute template row index.  Report both relations explicitly.
        idx_ok = True
        idx_problems = []
        sample_idx_equals_abs_row = True
        for task, entries in template_by_task.items():
            seen = []
            for ri, rec in entries:
                try:
                    sidx = int(rec["sample_idx"])
                except ValueError:
                    idx_ok = False
                    idx_problems.append({"task": task, "row_index": ri, "why": "non-int sample_idx"})
                    continue
                seen.append(sidx)
                if sidx != ri:  # absolute template data-row index
                    sample_idx_equals_abs_row = False
            if sorted(seen) != list(range(len(entries))):
                idx_ok = False
                idx_problems.append({"task": task, "why": "sample_idx not permutation of 0..n-1"})
        report["checks"]["template_sample_idx"] = {
            "pass": idx_ok,
            "semantics": "per-task 0-based position; equals the task's original CSV row_index",
            "sample_idx_equals_absolute_template_row_index": sample_idx_equals_abs_row,
            "problems": idx_problems[:20],
        }

        # 3. per-split files
        all_tasks = list(task_meta.keys())
        missing_files = []
        split_reports = {"train": {}, "test": {}, "valid": {}}
        for task in all_tasks:
            # train
            try:
                tr = C.read_split("train", task, official_base, blind_base)
            except C.ContractError as e:
                if e.code == "FILE_MISSING":
                    missing_files.append(e.context.get("path"))
                    continue
                raise
            trinfo = _train_summary(tr, task_meta[task]["kind"])
            split_reports["train"][task] = trinfo

            te = C.read_split("test", task, official_base, blind_base)
            # template rows == test rows at same zero-based index
            tmpl_entries = template_by_task.get(task, [])
            match_ok = len(tmpl_entries) == te["n_rows"]
            mismatches = []
            for ri in range(min(len(tmpl_entries), te["n_rows"])):
                _, trec = tmpl_entries[ri]
                trow = te["rows"][ri]
                if trec["drug_id"] != trow[0] or trec["smiles"] != trow[1]:
                    match_ok = False
                    mismatches.append({"row_index": ri,
                                       "template": [trec["drug_id"], trec["smiles"][:30]],
                                       "test": [trow[0], trow[1][:30]]})
            split_reports["test"][task] = {
                "sha256": te["sha256"], "n_rows": te["n_rows"],
                "format": te["format"], "row_index_sha256": te["row_index_sha256"],
                "template_matches_test": match_ok,
                "template_mismatches": mismatches[:10],
            }

            va = C.read_split("valid", task, official_base, blind_base)
            split_reports["valid"][task] = {
                "sha256": va["sha256"], "n_rows": va["n_rows"],
                "format": va["format"], "row_index_sha256": va["row_index_sha256"],
            }

        report["splits"] = split_reports
        report["checks"]["no_missing_files"] = {"pass": not missing_files,
                                                "missing": missing_files}

        # 4. template/test identity is a hard gate
        identity_ok = all(v["template_matches_test"] for v in split_reports["test"].values())
        report["checks"]["template_matches_test"] = {"pass": identity_ok}

        # 5. train label validity
        label_ok = all(v["labels_ok"] for v in split_reports["train"].values())
        report["checks"]["train_labels_valid"] = {"pass": label_ok}

        # 6. per-split identity digests (reuse by score/export preflight)
        digests = {}
        for split, per_task in split_reports.items():
            digests[split] = {}
            for task, info in per_task.items():
                digests[split][task] = C.split_identity_digest(
                    task, split, info["sha256"], info["n_rows"], info["row_index_sha256"])
        report["split_identity_digests"] = digests
        report["task_meta"] = {t: {"kind": m["kind"], "metric": m["metric"]} for t, m in task_meta.items()}

        report["ok"] = all(
            c.get("pass", True) for c in report["checks"].values()
        )
    except C.ContractError as e:
        err = e.to_dict()
    except Exception as e:  # pragma: no cover
        err = {"error": "INTERNAL", "message": repr(e)}
    if err:
        report["error"] = err
        report["ok"] = False
    _emit(report, report_path)
    return 0 if report["ok"] else 2


def _train_summary(split, kind):
    rows = split["rows"]
    vals = []
    problems = []
    for ri, row in enumerate(rows):
        y = row[2]
        try:
            v = float(y)
        except ValueError:
            problems.append({"row_index": ri, "why": "unparseable Y", "value": y})
            continue
        if v != v or v in (float("inf"), float("-inf")):
            problems.append({"row_index": ri, "why": "non-finite Y", "value": y})
        vals.append(v)
    labels_ok = not problems
    if kind == "classification":
        for ri, row in enumerate(rows):
            try:
                v = float(row[2])
            except ValueError:
                continue
            if v not in (0.0, 1.0):
                labels_ok = False
                problems.append({"row_index": ri, "why": "classification Y not 0/1", "value": row[2]})
    return {
        "sha256": split["sha256"], "n_rows": split["n_rows"],
        "format": split["format"], "row_index_sha256": split["row_index_sha256"],
        "y_min": min(vals) if vals else None,
        "y_max": max(vals) if vals else None,
        "y_uniq": len(set(vals)),
        "labels_ok": labels_ok,
        "label_problems": problems[:10],
    }


def _emit(report, report_path):
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if report_path:
        d = os.path.dirname(os.path.abspath(report_path))
        os.makedirs(d, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--official-base", default=C.DEFAULT_OFFICIAL_BASE)
    p.add_argument("--blind-base", default=C.DEFAULT_BLIND_BASE)
    p.add_argument("--template", default=os.path.join(C.DEFAULT_OFFICIAL_BASE, "submission_template.csv"))
    p.add_argument("--schema", default=None, help="task schema json to cross-check")
    p.add_argument("--report", default=None, help="write JSON report here, else stdout")
    a = p.parse_args(argv)
    try:
        return verify(a.official_base, a.blind_base, a.template, a.schema, a.report)
    except SystemExit:
        raise
    except Exception as e:  # pragma: no cover
        sys.stderr.write(json.dumps({"error": "INTERNAL", "message": repr(e)}) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())