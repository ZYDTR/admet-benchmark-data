"""Check integrity of the shared inputs (template, train, test, valid).

Read-only. Never writes to input files. Prints a per-task report and exits
non-zero if any hard check fails.

Checks performed:
  * Template: row count == 16379, header == fixed 6 columns, encoding UTF-8 BOM,
    CRLF line endings, sample_idx unique per task, sample_idx contiguous 0..n-1,
    metric consistent per task, sha256 recorded.
  * Per task test.csv: 1:1 alignment with template rows by position; Drug_ID and
    Drug equal template's drug_id/smiles (whitespace-insensitive compare), BOM.
  * Per task train.csv: expected columns Drug_ID,Drug,Y; no missing Y.
  * Per task valid.csv: columns Drug_ID,Drug only (labels withheld); row count
    matches registered projection counts and sha256 (if manifest provided).

The official template sha256 is fixed here (from reference-harness/contract.json
and competition/sources.json): 8ee41589d2c98e7b93081c058b3f928ac09bea4b3ffc899fa13677051e9baa20
"""

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import defaultdict

TEMPLATE_HEADER = ["task", "sample_idx", "drug_id", "smiles", "y_pred", "metric"]
TEMPLATE_ROWS = 16379
TEMPLATE_SHA256 = (
    "8ee41589d2c98e7b93081c058b3f928ac09bea4b3ffc899fa13677051e9baa20"
)

FAILS = []
WARNS = []


def fail(msg):
    FAILS.append(msg)
    print(f"[FAIL] {msg}")


def warn(msg):
    WARNS.append(msg)
    print(f"[WARN] {msg}")


def ok(msg):
    print(f"[ ok ] {msg}")


def read_csv_rows(path):
    """Return (rows, meta) reading a CSV as UTF-8 (BOM tolerated) preserving raw text."""
    with open(path, "rb") as fh:
        raw = fh.read()
    meta = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size": len(raw),
        "bom": raw[:3] == b"\xef\xbb\xbf",
        "crlf": raw.count(b"\r\n"),
        "lf": raw.count(b"\n"),
    }
    text = raw.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    return rows, meta


def check_template(template_path):
    rows, meta = read_csv_rows(template_path)
    if meta["sha256"] != TEMPLATE_SHA256:
        fail(f"template sha256 {meta['sha256']} != expected {TEMPLATE_SHA256}")
    else:
        ok(f"template sha256 matches official ({TEMPLATE_SHA256[:16]}...)")
    if not meta["bom"]:
        warn("template has no UTF-8 BOM (official template has BOM)")
    else:
        ok("template encoding has UTF-8 BOM")
    if meta["crlf"] != meta["lf"]:
        warn(f"template has mixed line endings (crlf={meta['crlf']} lf={meta['lf']})")
    else:
        ok(f"template line endings uniform (crlf={meta['crlf']} lf={meta['lf']})")
    if len(rows) != TEMPLATE_ROWS:
        fail(f"template rows {len(rows)} != expected {TEMPLATE_ROWS}")
    else:
        ok(f"template rows == {TEMPLATE_ROWS}")
    if list(rows[0].keys()) != TEMPLATE_HEADER:
        fail(f"template header {list(rows[0].keys())} != {TEMPLATE_HEADER}")
    else:
        ok("template header matches fixed 6 columns")

    # y_pred must be blank in template (nothing to preserve there).
    nonblank_pred = sum(1 for r in rows if r["y_pred"].strip() != "")
    if nonblank_pred:
        warn(f"template y_pred has {nonblank_pred} non-blank cells")

    per_task = defaultdict(list)
    for r in rows:
        per_task[r["task"]].append(r)

    # sample_idx uniqueness + contiguity + metric consistency.
    for task, rs in sorted(per_task.items()):
        idxs = [int(r["sample_idx"]) for r in rs]
        if len(set(idxs)) != len(idxs):
            fail(f"{task}: duplicate sample_idx in template")
        if sorted(idxs) != list(range(len(idxs))):
            fail(f"{task}: sample_idx not contiguous 0..{len(idxs)-1} (min={min(idxs)} max={max(idxs)})")
        metrics = set(r["metric"] for r in rs)
        if len(metrics) != 1:
            fail(f"{task}: inconsistent metric in template {metrics}")
    ok(f"template: {len(per_task)} tasks, sample_idx contiguous & unique per task")
    return rows, meta, per_task


def check_task_inputs(task, tmpl_rows, data_root):
    # test.csv vs template
    test_path = f"{data_root}/official/data_benchmark/{task}/test.csv"
    test_rows, test_meta = read_csv_rows(test_path)
    if not test_meta["bom"]:
        warn(f"{task}: test.csv missing UTF-8 BOM")
    if len(test_rows) != len(tmpl_rows):
        fail(f"{task}: test.csv rows {len(test_rows)} != template rows {len(tmpl_rows)}")
    else:
        mism = []
        idx_mism = 0
        for i, (xrow, trow) in enumerate(zip(test_rows, tmpl_rows)):
            # sample_idx MUST equal the 0-based test.csv data-row position.
            # This is verified here, not assumed: if the template ordering ever
            # diverged from test.csv row order these checks would fail.
            if trow["sample_idx"] != str(i):
                idx_mism += 1
            if (xrow.get("Drug_ID") or "").strip() != (trow["drug_id"] or "").strip():
                mism.append(("id", i))
            elif (xrow.get("Drug") or "").strip() != (trow["smiles"] or "").strip():
                mism.append(("smiles", i))
        if idx_mism:
            fail(f"{task}: {idx_mism} template sample_idx != test row position")
        if mism:
            fail(f"{task}: {len(mism)} test/template row mismatches (first: {mism[:3]})")
        if not idx_mism and not mism:
            ok(f"{task}: sample_idx==test row position; id+drug align 1:1 with template")

    # train.csv
    train_path = f"{data_root}/official/data_benchmark/{task}/train.csv"
    train_rows, _ = read_csv_rows(train_path)
    if list(train_rows[0].keys())[:3] != ["Drug_ID", "Drug", "Y"]:
        fail(f"{task}: train.csv unexpected columns {list(train_rows[0].keys())}")
    missing_y = sum(1 for r in train_rows if (r.get("Y") or "").strip() == "")
    if missing_y:
        fail(f"{task}: train.csv has {missing_y} empty Y")
    else:
        ok(f"{task}: train.csv {len(train_rows)} rows, no empty Y")

    # valid.csv
    valid_path = f"{data_root}/blind_validation/{task}/valid.csv"
    valid_rows, valid_meta = read_csv_rows(valid_path)
    cols = list(valid_rows[0].keys())
    if cols != ["Drug_ID", "Drug"]:
        fail(f"{task}: valid.csv columns {cols} (expected [Drug_ID, Drug])")
    return {
        "task": task,
        "test_rows": len(test_rows),
        "train_rows": len(train_rows),
        "valid_rows": len(valid_rows),
        "valid_sha256": valid_meta["sha256"],
        "test_sha256": test_meta["sha256"],
    }


def check_valid_against_manifest(valid_info, manifest_path):
    with open(manifest_path) as fh:
        proj = json.load(fh)
    exp = {f["task"]: f for f in proj["files"]}
    for info in valid_info:
        task = info["task"]
        e = exp.get(task)
        if not e:
            fail(f"{task}: missing from validation-projection manifest")
            continue
        if info["valid_rows"] != e["rows"]:
            fail(f"{task}: valid rows {info['valid_rows']} != manifest {e['rows']}")
        elif info["valid_sha256"] != e["sha256"]:
            fail(f"{task}: valid sha256 mismatch vs manifest")
        else:
            ok(f"{task}: valid matches registered projection (rows+sha256)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", default="data",
                    help="root containing official/ and blind_validation/")
    ap.add_argument("--template", default="data/official/submission_template.csv")
    ap.add_argument("--manifest", default=None,
                    help="optional validation-projection.json to cross-check valid hashes")
    ap.add_argument("--report-json", default=None,
                    help="optional path to write a JSON summary")
    args = ap.parse_args()

    print("== Template ==")
    tmpl_rows, tmpl_meta, per_task = check_template(args.template)

    print("\n== Per-task inputs ==")
    infos = []
    for task in sorted(per_task):
        infos.append(check_task_inputs(task, per_task[task], args.data_root))

    if args.manifest:
        print("\n== Valid vs manifest ==")
        check_valid_against_manifest(infos, args.manifest)

    summary = {
        "template_sha256": tmpl_meta["sha256"],
        "template_rows": len(tmpl_rows),
        "tasks": len(per_task),
        "per_task": infos,
        "fails": FAILS,
        "warns": WARNS,
    }
    if args.report_json:
        with open(args.report_json, "w") as fh:
            json.dump(summary, fh, indent=2)
        print(f"\nSummary written to {args.report_json}")

    print(f"\n== Result: {len(FAILS)} fail, {len(WARNS)} warn ==")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())