"""Generate valid/test predictions from trained heads on the frozen features.

Output contract (unified numeric inference files):

- one CSV per split: valid_predictions.csv and test_predictions.csv
- exactly the columns task,split,row_index,y_pred (in that order)
- rows ordered by tasks.json task order, then row_index ascending within task
- split column is the literal "valid" or "test"; row_index is the 0-based CSV
  data-row position in that task/split file (header excluded)
- classification y_pred = P(Y=1) in (0,1); regression y_pred is de-standardized
  back to the original Y scale; all values finite

Safety properties enforced before anything is written:

- freeze chain: every head checkpoint records the digests of the feature cache
  it consumed; the current cache files are re-hashed and must match, otherwise
  the run fails (weights -> cache -> heads -> predictions)
- full coverage: every row of every selected task/split gets exactly one
  prediction line; duplicate or missing row_index, or non-finite y_pred, fails
  the run
- fallback provenance: rows served by the train-only fallback vector are listed
  in predict_summary.json and predictions_provenance.json; they are still
  model-generated predictions (never hand-edited), just flagged for audit

Usage (from output/model/):

    python -m chemeleon_baseline.predict \
        --data-root ../../data \
        --features ../../runs/features \
        --heads ../../runs/train_v1/heads \
        --out ../../runs/predictions \
        --device cpu --threads 8
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

from .data_io import DEFAULT_DATA_ROOT, read_rows, split_path
from .features import FeatureStore
from .heads import load_head, stable_sigmoid_np
from .tasks import load_tasks, select_tasks, validate_data_root

PREDICTION_COLUMNS = ["task", "split", "row_index", "y_pred"]


def _log(msg: str) -> None:
    print(f"[predict {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def predict_split(
    head: torch.nn.Module,
    meta: dict,
    X: np.ndarray,
) -> np.ndarray:
    """Standardize with the checkpoint scalers, run the head, map to y_pred."""
    input_mean = meta["input_mean"].numpy().astype(np.float64)
    input_std = meta["input_std"].numpy().astype(np.float64)
    Xz = ((X - input_mean) / input_std).astype(np.float32)
    device = next(head.parameters()).device
    with torch.no_grad():
        logits = head(torch.from_numpy(Xz).to(device)).detach().cpu().numpy()
    if meta["kind"] == "classification":
        y_pred = stable_sigmoid_np(logits)
    else:
        y_pred = logits.astype(np.float64) * float(meta["y_std"]) + float(meta["y_mean"])
    return y_pred


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    ap.add_argument("--features", required=True)
    ap.add_argument("--heads", required=True, help="directory containing <task>.pt head checkpoints")
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--tasks", default="all")
    args = ap.parse_args(argv)

    torch.set_num_threads(max(1, args.threads))
    device = args.device

    tasks = select_tasks(load_tasks(), args.tasks)
    data_root = Path(args.data_root)
    validate_data_root(data_root, tasks)

    store = FeatureStore(args.features)
    current = store.file_hashes()
    _log(f"cache: {store.dir} dim={store.dim}")

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    heads_dir = Path(args.heads).resolve()

    summary = {
        "schema_version": 1,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "features_dir": str(store.dir.resolve()),
        "heads_dir": str(heads_dir),
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "columns": PREDICTION_COLUMNS,
        "splits": {},
    }
    provenance: list[dict] = []
    problems: list[str] = []

    for split in ("valid", "test"):
        split_rows: list[tuple[str, int, float]] = []
        split_counts: dict = {}
        split_problems: list[str] = []
        for t in tasks:
            task_name = t["task"]
            ckpt_path = heads_dir / f"{task_name}.pt"
            if not ckpt_path.is_file():
                raise FileNotFoundError(f"missing head checkpoint: {ckpt_path}")
            head, meta = load_head(ckpt_path, device=device)

            # freeze chain: head must have consumed exactly this cache
            ident = meta["features_identity"]
            mismatches = []
            for name, digest in current.items():
                key = f"sha256_{name}"
                if key not in ident or ident[key] != digest:
                    mismatches.append(name)
            if ident.get("weights_sha256") != store.weights_sha256():
                mismatches.append("weights_sha256(metadata)")
            if ident.get("fingerprint_dim") != store.dim:
                mismatches.append("fingerprint_dim")
            if mismatches:
                raise RuntimeError(
                    f"{task_name}: head was trained on a different feature cache "
                    f"(mismatch: {sorted(set(mismatches))}); refusing to predict"
                )
            if meta["kind"] != t["kind"]:
                raise RuntimeError(f"{task_name}: checkpoint kind {meta['kind']} != registry kind {t['kind']}")

            rows = read_rows(split_path(data_root, task_name, split), expect_y=False)
            for r in rows:
                r["task"] = task_name
                r["split"] = split
            X, fallback_mask, fb_refs = store.vectors_for(rows)
            y_pred = predict_split(head, meta, X)

            if y_pred.shape[0] != len(rows):
                raise RuntimeError(f"{task_name}/{split}: prediction count {y_pred.shape[0]} != rows {len(rows)}")
            if not np.all(np.isfinite(y_pred)):
                split_problems.append(f"{task_name}/{split}: non-finite y_pred")
            if t["kind"] == "classification":
                lo, hi = float(y_pred.min()), float(y_pred.max())
                if lo < 0.0 or hi > 1.0:
                    split_problems.append(f"{task_name}/{split}: classification y_pred outside [0,1] ({lo},{hi})")
            provenance.extend(fb_refs)
            for r, p in zip(rows, y_pred):
                split_rows.append((task_name, r["row_index"], float(p)))

            split_counts[task_name] = {
                "rows": len(rows),
                "fallback_rows": int(fallback_mask.sum()),
                "y_pred_min": float(y_pred.min()),
                "y_pred_max": float(y_pred.max()),
            }
            _log(f"{task_name}/{split}: {len(rows)} rows, fallback={int(fallback_mask.sum())}")

        # coverage assertion: every row exactly once, contiguous 0..n-1 per task
        for t in tasks:
            got = sorted(ri for (name, ri, _) in split_rows if name == t["task"])
            expected = list(range(t["rows"][split]))
            if got != expected:
                split_problems.append(
                    f"{t['task']}/{split}: row_index coverage mismatch (got {len(got)} rows, "
                    f"expected {len(expected)}; first divergence at "
                    f"{next((i for i, (a, b) in enumerate(zip(got, expected)) if a != b), 'len')})"
                )
                break

        problems.extend(f"{split}: {p}" for p in split_problems)
        if split_problems:
            _log(f"NOT writing {split}_predictions.csv: {len(split_problems)} problem(s) detected")
            summary["splits"][split] = {"file": None, "rows": len(split_rows), "tasks": split_counts, "problems": split_problems}
            continue

        out_path = out_dir / f"{split}_predictions.csv"
        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(PREDICTION_COLUMNS)
            for name, ri, p in split_rows:
                w.writerow([name, split, ri, f"{p:.10g}"])
        _log(f"wrote {out_path} ({len(split_rows)} rows)")
        summary["splits"][split] = {"file": str(out_path), "rows": len(split_rows), "tasks": split_counts}

    (out_dir / "predictions_provenance.json").write_text(json.dumps(provenance, indent=1), encoding="utf-8")
    summary["fallback_rows_total"] = len(provenance)
    summary["problems"] = problems
    (out_dir / "predict_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    if problems:
        print("ERROR: prediction problems detected:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2
    _log(f"predictions complete; fallback rows: {len(provenance)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
