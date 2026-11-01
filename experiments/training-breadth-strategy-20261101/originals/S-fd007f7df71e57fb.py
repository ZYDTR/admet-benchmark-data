"""Predict the blind valid split for one or more tasks (valid-only entry).

Reads ONLY: cached valid features, ``<out>/<task>/head.pt``.  Does not read test
features, test predictions, or the template.  Writes the shared product CSV
``task,split,row_index,y_pred`` with split fixed to ``valid``.

Unencodable rows (recorded in the feature cache ``failures.json``) cannot receive
a feature-based prediction.  The default policy is to FAIL with the full list; the
explicit ``--fallback train_mean`` flag predicts the *train-feature* target mean
(regression) or train positive rate (classification) for those rows and records
the fallback in ``<out>/<task>/valid_fallback.json``.  Either way the product CSV
covers every valid row exactly once.
"""

import argparse
import json
import os
import sys

try:  # pragma: no cover - torch is only installed in the training env
    import numpy as np
except Exception:  # pragma: no cover
    np = None

from assets import CHEMELEON_CODE_COMMIT, load_lock, package_versions
from dataio import read_split
from errors import CacheError, ContractError, FeaturizationError
from feature_cache import build_manifest, load_cache
from head_model import load_head, predict
from predict_io import records_from_predictions, write_products


def _keys_for(table):
    return {(table["task"], table["split"], r["row_index"]): None for r in table["rows"]}


def predict_tables(data_root, cache_dir, out_dir, tasks, split, feature_dim,
                   weights_meta, deps, batch_size, fallback="error"):
    """Return ``(all_records, per_task)`` for every row of each requested task."""
    if split not in ("valid", "test"):
        raise ContractError(f"unsupported split {split!r}")
    all_records = []
    per_task = {}
    for task in tasks:
        head, meta = load_head(os.path.join(out_dir, task, "head.pt"), expect_task=task)
        table = read_split(data_root, task, split)
        meta_in = {
            "id": "chemeleon_mp",
            "code_commit": CHEMELEON_CODE_COMMIT,
            "feature_dim": feature_dim,
            "weights": weights_meta,
        }
        manifest = build_manifest(table, meta_in, deps, batch_size)
        feats, cached = load_cache(cache_dir, manifest)
        kept = cached["kept_row_indices"]
        failures = cached.get("failures", [])
        scores = predict(head, feats, meta["task_kind"], meta["scaler"])
        recs = records_from_predictions(task, split, feats, scores, kept)
        got = {(r["task"], r["split"], r["row_index"]) for r in recs}
        missing = [r for r in table["rows"]
                   if (task, split, r["row_index"]) not in got]
        if missing and fallback == "error":
            raise FeaturizationError(
                f"{task}/{split}: {len(missing)} rows lack features and no fallback "
                f"was requested; row_index={[r['row_index'] for r in missing]}",
                failures=[{"row_index": r["row_index"], "smiles": r["smiles"]}
                          for r in missing],
            )
        if missing:
            fill = _fallback_value(task, split, out_dir, data_root, meta, feature_dim,
                                   weights_meta, deps, batch_size)
            for r in missing:
                recs.append({"task": task, "split": split, "row_index": r["row_index"],
                             "y_pred": float(fill)})
            os.makedirs(os.path.join(out_dir, task), exist_ok=True)
            with open(os.path.join(out_dir, task, f"{split}_fallback.json"), "w",
                      encoding="utf-8") as fh:
                json.dump({"policy": fallback, "value": float(fill),
                           "rows": [{"row_index": r["row_index"], "smiles": r["smiles"]}
                                    for r in missing], "failures": failures},
                          fh, indent=2, ensure_ascii=False)
        recs.sort(key=lambda r: r["row_index"])
        if len(recs) != table["n_rows"]:
            raise ContractError(f"{task}/{split}: wrote {len(recs)} rows != {table['n_rows']}")
        per_task[task] = {"n_rows": table["n_rows"], "cache_key": cached["key"],
                          "n_fallback": len(missing)}
        all_records.extend(recs)
    return all_records, per_task


def _fallback_value(task, split, out_dir, data_root, head_meta, feature_dim,
                    weights_meta, deps, batch_size):
    """Target mean over the train feature rows (regression) / positive rate (clf)."""
    from head_model import TargetScaler

    if head_meta["task_kind"] == "regression":
        scaler = head_meta["scaler"]
        if scaler is None:
            raise ContractError(f"{task}: regression head has no scaler for fallback")
        return TargetScaler.from_dict(scaler.to_dict()).mean
    trainer = os.path.join(out_dir, task, "train_log.json")
    if not os.path.isfile(trainer):
        raise ContractError(f"{task}: fallback for classification needs train_log.json")
    with open(trainer, "r", encoding="utf-8") as fh:
        log = json.load(fh)
    rate = log.get("positive_rate")
    if rate is None:
        raise ContractError(
            f"{task}: train_log.json lacks positive_rate; re-run train_heads.py "
            "to enable classification fallback"
        )
    return float(rate)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--asset-lock", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tasks", nargs="*", required=True)
    ap.add_argument("--feature-dim", type=int, required=True)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--output", required=True)
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
        args.data_root, args.cache, args.out, args.tasks, "valid",
        args.feature_dim, weights_meta, deps, args.batch_size, fallback=args.fallback,
    )
    write_products(args.output, recs)
    print(json.dumps({"output": args.output, "tasks": per_task}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())