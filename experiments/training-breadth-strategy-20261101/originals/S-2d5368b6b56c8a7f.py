"""Per-task scoring on ordinary data files.

This scorer NEVER looks up labels on its own. The real validation label file is
passed explicitly by the main Codex process (label path is external). It reads:
  * predictions: task,split,row_index,y_pred (test and/or valid)
  * labels: a CSV with columns Drug_ID,Drug,Y (full official valid file) OR
            a minimal CSV/JSON keyed by row_index with the Y column.

Scoring is done per task; within a task, valid predictions are matched to label
rows by row_index (0-based position in the label CSV). For test predictions no
labels exist, so no score is produced (test is for submission export only).

Metrics per task are taken from the template `metric` column:
  AUROC / AUPRC / MAE / Spearman. AUPRC is reported as Average Precision (AP);
  the official AUPRC definition and overall aggregation are UNCONFIRMED, so we
  print a clear per-task local report and never fabricate an official total.

Usage:
  python3 score.py --predictions P.csv \
      --labels-dir /external/labels/valid \
      --template data/official/submission_template.csv \
      --out results.json
where labels-dir/<task>.csv contains the true Y for valid (extra columns allowed;
row_index is the 0-based data-row order in that file).
"""

import argparse
import csv
import io
import json
import sys
from collections import defaultdict

import metrics


def read_template(path):
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    task_metric = {}
    for r in rows:
        task_metric[r["task"]] = r["metric"]
    return task_metric


def read_labels(path):
    """Read a label file. Returns list of Y floats in file order (row_index)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    if not rows:
        raise ValueError(f"{path}: empty label file")
    cols = rows[0].keys()
    ycol = None
    for cand in ("Y", "y", "label", "target"):
        if cand in cols:
            ycol = cand
            break
    if ycol is None:
        raise ValueError(f"{path}: no Y-like column in {list(cols)}")
    out = []
    for i, r in enumerate(rows):
        v = r[ycol].strip()
        if v == "":
            raise ValueError(f"{path}: row_index {i} has empty {ycol}")
        out.append(float(v))
    return out


def load_preds_for_split(path, want_split):
    """Return dict task -> {row_index: y_pred} for the requested split."""
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8-sig")
    stripped = text.lstrip()
    recs = []
    if path.endswith(".json") or stripped.startswith("["):
        recs = json.loads(text)
    elif path.endswith(".jsonl"):
        recs = [json.loads(l) for l in text.splitlines() if l.strip()]
    else:
        recs = list(csv.DictReader(io.StringIO(text, newline="")))
    out = defaultdict(dict)
    for r in recs:
        if str(r["split"]) != want_split:
            continue
        task = str(r["task"])
        ri = int(str(r["row_index"]).strip())
        out[task][ri] = float(str(r["y_pred"]).strip())
    return out


def score_task(metric_name, y_true, y_pred):
    fn = metrics.METRIC_FUNCS.get(metric_name)
    if fn is None:
        raise ValueError(f"unknown metric {metric_name}")
    return fn(y_true, y_pred)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--predictions", required=True,
                    help="prediction file (csv/jsonl/json) covering valid split")
    ap.add_argument("--labels-dir", required=True,
                    help="dir of <task>.csv with true Y for valid (external path)")
    ap.add_argument("--template", default="data/official/submission_template.csv")
    ap.add_argument("--out", default=None, help="optional JSON results path")
    args = ap.parse_args()

    task_metric = read_template(args.template)
    preds = load_preds_for_split(args.predictions, "valid")

    results = {}
    print(f"{'task':<38} {'metric':<9} {'score':>12} {'n':>6} {'pos':>5}")
    print("-" * 76)
    for task in sorted(task_metric):
        metric_name = task_metric[task]
        if task not in preds:
            print(f"{task:<38} {metric_name:<9} {'MISSING':>12}")
            results[task] = {"metric": metric_name, "score": None, "error": "no valid predictions"}
            continue
        label_path = f"{args.labels_dir.rstrip('/')}/{task}.csv"
        try:
            y_true_all = read_labels(label_path)
        except FileNotFoundError:
            print(f"{task:<38} {metric_name:<9} {'NO_LABELS':>12}")
            results[task] = {"metric": metric_name, "score": None, "error": f"missing {label_path}"}
            continue
        pred_map = preds[task]
        y_true, y_pred = [], []
        bad = []
        for ri, yv in pred_map.items():
            if ri < 0 or ri >= len(y_true_all):
                bad.append(ri)
                continue
            y_true.append(y_true_all[ri])
            y_pred.append(yv)
        if bad:
            results[task] = {"metric": metric_name, "score": None,
                             "error": f"row_index out of range: {sorted(bad)[:10]}"}
            print(f"{task:<38} {metric_name:<9} {'BAD_IDX':>12}")
            continue
        score = score_task(metric_name, y_true, y_pred)
        n = len(y_true)
        pos = sum(1 for v in y_true if round(float(v)) == 1) if metric_name in ("AUROC", "AUPRC") else "-"
        if score is None:
            print(f"{task:<38} {metric_name:<9} {'UNDEFINED':>12} {n:>6} {str(pos):>5}")
            results[task] = {"metric": metric_name, "score": None,
                             "n": n, "pos": pos, "note": "metric undefined"}
        else:
            print(f"{task:<38} {metric_name:<9} {score:>12.6f} {n:>6} {str(pos):>5}")
            results[task] = {"metric": metric_name, "score": score, "n": n, "pos": pos}

    print("-" * 76)
    print("NOTE: per-task local scores only. AUPRC == Average Precision (AP).")
    print("Official total-score aggregation is UNCONFIRMED; no official total is computed.")

    summary = {
        "auprc_definition": "average_precision (scikit-learn / TDC pr-auc convention)",
        "official_aggregation": "unconfirmed",
        "per_task": results,
    }
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(summary, fh, indent=2)
        print(f"\nResults written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())