"""Predict the test split and emit both products and (optionally) the submission.

Reads ONLY: cached test features, ``<out>/<task>/head.pt``, and — only for
``--submission`` — the pinned template + test CSVs.  Never reads valid products.

Products (shared interface): ``task,split,row_index,y_pred`` with split=``test``.
Submission: rebuilt from the full-identity template join (see submission.py);
only ``y_pred`` is written and only for the exported tasks.  Classification heads
output logits during scoring; the submission receives ``sigmoid(logit)``
(monotone, so rank metrics are unchanged and values are valid probabilities).

Unencodable test rows follow the same explicit fallback policy as predict_valid
(``--fallback error|train_mean``); a submission is only produced for the tasks
whose product file covers every test row.
"""

import argparse
import json
import os
import sys

try:  # pragma: no cover - torch is only installed in the training env
    import numpy as np
except Exception:  # pragma: no cover
    np = None

from assets import load_lock, package_versions
from dataio import read_template
from errors import ContractError
from predict_io import write_products
from predict_valid import predict_tables
from submission import build_submission, verify_submission


def _apply_probabilities(records, out_dir, tasks):
    """Convert classification logits to probabilities for the submission.

    Works on copies; the product CSV keeps raw logits so both representations are
    traceable.  Regression records are returned unchanged.
    """
    kinds = {}
    for task in tasks:
        from head_model import load_head

        _, meta = load_head(os.path.join(out_dir, task, "head.pt"), expect_task=task)
        kinds[task] = meta["task_kind"]
    out = []
    for rec in records:
        new = dict(rec)
        if kinds[rec["task"]] == "classification":
            z = np.clip(rec["y_pred"], -50.0, 50.0)
            new["y_pred"] = float(1.0 / (1.0 + np.exp(-z)))
        out.append(new)
    return out, kinds


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--asset-lock", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tasks", nargs="*", required=True)
    ap.add_argument("--feature-dim", type=int, required=True)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--output", required=True, help="test product CSV path")
    ap.add_argument("--submission", default=None, help="optional submission CSV path")
    ap.add_argument("--fallback", choices=["error", "train_mean"], default="error")
    args = ap.parse_args(argv)

    lock = load_lock(args.asset_lock)
    weights_meta = {"size": lock["weights_size"], "md5": lock["weights_md5"],
                    "sha256": lock["weights_sha256"]}
    deps = package_versions()
    missing = [k for k, v in deps.items() if v is None]
    if missing:
        print(f"[deps] missing packages: {missing}", file=sys.stderr)
        return 2

    recs, per_task = predict_tables(
        args.data_root, args.cache, args.out, args.tasks, "test",
        args.feature_dim, weights_meta, deps, args.batch_size, fallback=args.fallback,
    )
    write_products(args.output, recs)

    result = {"output": args.output, "tasks": per_task}
    if args.submission:
        template = read_template(args.data_root)
        prob_recs, kinds = _apply_probabilities(recs, args.out, args.tasks)
        prob_path = os.path.join(os.path.dirname(os.path.abspath(args.output)),
                                 "test_probabilities.csv")
        write_products(prob_path, prob_recs)
        info = build_submission(args.data_root, args.tasks, prob_path, args.submission,
                                template=template)
        verify_submission(template, args.submission, args.tasks)
        result["submission"] = info
        result["probability_products"] = prob_path
        result["task_kinds"] = kinds
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())