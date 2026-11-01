"""Score a product CSV against labels — SYNTHETIC / LOCAL-ONLY entry.

There are no real valid/test labels in this pack, so this script refuses to score
the blind splits against anything but labels you supply explicitly (e.g. a local
held-out file you are authorised to use).  For the prep-session checks it is run
only on clearly synthetic arrays via ``metrics.py``.

Guarantees:

* The complete expected key set is verified before any scoring
  (``predict_io.read_products``); missing/extra/duplicate/non-finite keys fail.
* Empty expected set fails; empty label set yields an explicit ``undefined``
  record, never a fabricated score.
* Single-class classification and constant-vector Spearman are reported as
  ``defined: false`` with a reason, not silently dropped or coerced.
* Never writes anything outside ``--output``.

Labels file schema (operator-supplied, NOT part of the task pack):
``task,split,row_index,Y``.
"""

import argparse
import csv
import json
import os
import sys

from dataio import read_split
from errors import ScoringError
from metrics import score
from predict_io import read_products


def _read_labels(path):
    labels = {}
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = tuple(next(reader, ()))
        if header != ("task", "split", "row_index", "Y"):
            raise ScoringError(f"{path}: label header {header}")
        for lineno, row in enumerate(reader, start=2):
            if len(row) != 4:
                raise ScoringError(f"{path}:{lineno}: expected 4 fields")
            task, split, row_index, y = row
            try:
                key = (task, split, int(row_index))
                val = float(y)
            except ValueError:
                raise ScoringError(f"{path}:{lineno}: bad row_index/Y {row!r}")
            if not (val == val and abs(val) != float("inf")):
                raise ScoringError(f"{path}:{lineno}: non-finite Y")
            if key in labels:
                raise ScoringError(f"{path}:{lineno}: duplicate label key {key}")
            labels[key] = val
    return labels


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--products", required=True)
    ap.add_argument("--labels", required=True, help="task,split,row_index,Y (operator-supplied)")
    ap.add_argument("--tasks", nargs="*", required=True)
    ap.add_argument("--splits", nargs="*", default=["valid"])
    ap.add_argument("--output", required=True)
    args = ap.parse_args(argv)

    metric_by_task = _metric_map()
    expected = {}
    tables = {}
    for task in args.tasks:
        for split in args.splits:
            tab = read_split(args.data_root, task, split)
            tables[(task, split)] = tab
            for r in tab["rows"]:
                expected[(task, split, r["row_index"])] = None
    preds = read_products(args.products, expected, splits=tuple(args.splits))
    labels = _read_labels(args.labels)
    for key in expected:
        if key not in labels:
            raise ScoringError(f"labels missing for key {key}")

    out = {}
    for task in args.tasks:
        metric = metric_by_task[task]
        for split in args.splits:
            tab = tables[(task, split)]
            keys = [(task, split, r["row_index"]) for r in tab["rows"]]
            if not keys:
                out[f"{task}/{split}"] = {"metric": metric, "defined": False,
                                          "reason": "empty expected set"}
                continue
            y_true = [labels[k] for k in keys]
            y_pred = [preds[k] for k in keys]
            out[f"{task}/{split}"] = score(metric, y_true, y_pred)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print(json.dumps(out, indent=2))
    return 0


def _metric_map():
    return {
        "ames": "AUROC", "bbb_martins": "AUROC", "bioavailability_ma": "AUROC",
        "caco2_wang": "MAE", "clearance_hepatocyte_az": "Spearman",
        "clearance_microsome_az": "Spearman", "cyp2c9_substrate_carbonmangels": "AUPRC",
        "cyp2c9_veith": "AUPRC", "cyp2d6_substrate_carbonmangels": "AUPRC",
        "cyp2d6_veith": "AUPRC", "cyp3a4_substrate_carbonmangels": "AUROC",
        "cyp3a4_veith": "AUPRC", "dili": "AUROC", "half_life_obach": "Spearman",
        "herg": "AUROC", "hia_hou": "AUROC", "ld50_zhu": "MAE",
        "lipophilicity_astrazeneca": "MAE", "pgp_broccatelli": "AUROC", "ppbr_az": "MAE",
        "solubility_aqsoldb": "MAE", "vdss_lombardo": "Spearman",
    }


if __name__ == "__main__":
    sys.exit(main())