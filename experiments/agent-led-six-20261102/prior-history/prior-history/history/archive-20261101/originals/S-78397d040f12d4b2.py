"""Generate predictions for valid and test using the frozen CheMeleon cache + trained heads.

Outputs (in ``--out``):
* ``valid_predictions.csv``  task,split,row_index,y_pred        (no y_true)
* ``test_predictions.csv``   task,split,row_index,y_pred        (no y_true)
* ``test_predictions.json``  schema_version=1, run_id, model_artifact_sha256, predictions
* ``manifest.json``          input/cache/predictions hashes and row counts

Every row from every requested split is predicted. Unparseable inputs already carry a
constant-fill embedding (see build_features.py) so they still receive a finite prediction;
this is the auditable "complete coverage" scheme.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

from common import TASKS, sha256_file, write_json  # noqa: E402
from heads import predict_logits  # noqa: E402
from train import apply_fill, load_ckpt  # noqa: E402


def predict_task(task: str, ckpt_dir: Path, cache: Path, device: str, split: str):
    from build_features import load_split

    model, ck = load_ckpt(ckpt_dir / "heads" / f"{task}.pt", device)
    X_raw, ok, rows = load_split(cache, task, split)
    X = apply_fill(X_raw).astype(np.float32)
    X = np.ascontiguousarray((X - ck["scaler"]["mean"]) / ck["scaler"]["std"], dtype=np.float32)
    logits = predict_logits(model, X, device)
    if ck["kind"] == "regression":
        y = logits * ck["target"]["std"] + ck["target"]["mean"]
    else:
        y = 1.0 / (1.0 + np.exp(-logits))
    if not np.isfinite(y).all():
        raise RuntimeError(f"{task}/{split}: non-finite prediction produced")
    return rows, y.astype(np.float64), ck


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[3]
    ap.add_argument("--ckpt", type=Path, default=root / "output/model/runs/chemeleon_mlp_v1")
    ap.add_argument("--cache", type=Path, default=root / "output/model/cache/chemeleon_mp")
    ap.add_argument("--out", type=Path, default=root / "output/model/predictions/chemeleon_mlp_v1")
    ap.add_argument("--tasks", nargs="*", default=None)
    ap.add_argument("--splits", nargs="*", default=["valid", "test"])
    ap.add_argument("--device", default=None)
    ap.add_argument("--run-id", default="chemeleon-mlp-valid1",
                    help="run_id recorded in test_predictions.json (predict run)")
    args = ap.parse_args()

    import torch

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    tasks = args.tasks or TASKS
    args.out.mkdir(parents=True, exist_ok=True)

    all_rows = {"valid": [], "test": []}
    head_hashes = {}
    for task in tasks:
        head_path = args.ckpt / "heads" / f"{task}.pt"
        if head_path.is_file():
            head_hashes[task] = sha256_file(head_path)
        for split in args.splits:
            rows, y, ck = predict_task(task, args.ckpt, args.cache, device, split)
            for r, p in zip(rows, y):
                all_rows[split].append((task, split, r["row_index"], float(p)))
            print(f"[predict] {task:35s} {split:5s} rows={len(rows)}", flush=True)

    for split in args.splits:
        path = args.out / f"{split}_predictions.csv"
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["task", "split", "row_index", "y_pred"])
            for task, sp, idx, p in all_rows[split]:
                w.writerow([task, sp, idx, f"{p:.10g}"])

    # submission-shaped JSON (schema from reference-harness/skills/submission/references/format.md)
    combined_sha = sha256_file(args.out / "test_predictions.csv")
    payload = {
        "schema_version": 1,
        "run_id": args.run_id,
        "model_artifact_sha256": _combined_artifact_hash(head_hashes, tasks),
        "predictions": [
            {"task": t, "sample_idx": str(idx), "y_pred": p}
            for (t, sp, idx, p) in all_rows["test"]
        ],
    }
    write_json(args.out / "test_predictions.json", payload)

    write_json(args.out / "manifest.json", {
        "device": device,
        "run_id": args.run_id,
        "splits": args.splits,
        "row_counts": {
            "valid": len(all_rows.get("valid", [])),
            "test": len(all_rows.get("test", [])),
        },
        "head_sha256": head_hashes,
        "test_predictions_csv_sha256": combined_sha,
    })
    print(f"wrote predictions to {args.out}", flush=True)
    return 0


def _combined_artifact_hash(head_hashes: dict, tasks: list[str]) -> str:
    import hashlib

    h = hashlib.sha256()
    for t in sorted(tasks):
        h.update(t.encode())
        h.update(head_hashes.get(t, "").encode())
    return h.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())