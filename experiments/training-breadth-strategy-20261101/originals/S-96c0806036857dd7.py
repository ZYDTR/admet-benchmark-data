"""Check prediction coverage against the official template (test split).

Confirms every template (task, sample_idx) has exactly one test prediction, with
no missing, extra, or duplicate keys, and no non-finite values. Read-only.

Usage:
  python3 check_coverage.py --predictions P.csv \
      --template data/official/submission_template.csv [--json out.json]
"""

import argparse
import csv
import io
import sys

import predictions_io as pio


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--template", default="data/official/submission_template.csv")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    with open(args.template, "rb") as fh:
        text = fh.read().decode("utf-8-sig")
    trows = list(csv.DictReader(io.StringIO(text, newline="")))
    per_task = {}
    for r in trows:
        per_task.setdefault(r["task"], []).append(r)

    try:
        records = pio.load_predictions(args.predictions)
    except pio.PredictionError as e:
        print(f"[FAIL] load: {e}")
        return 1

    expected = pio.build_expected_index(per_task)
    result = pio.check_coverage(records, expected)
    print(f"expected test keys: {result['n_expected']}")
    print(f"test prediction records: {result['n_test_records']} (of {result['n_records']} total)")
    print(f"missing: {result['missing_count']}  extra: {result['extra_count']}  duplicates: {result['duplicate_count']}")
    if result["missing_count"]:
        print(f"  missing head: {result['missing_head']}")
    if result["extra_count"]:
        print(f"  extra head: {result['extra_head']}")
    if result["duplicate_count"]:
        print(f"  duplicate head: {result['duplicates_head']}")

    if args.json:
        import json
        with open(args.json, "w") as fh:
            json.dump(result, fh, indent=2)

    print("[OK] coverage complete" if result["ok"] else "[FAIL] coverage incomplete")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())