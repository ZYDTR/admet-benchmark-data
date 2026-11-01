"""Train one small MLP head per task on cached frozen CheMeleon fingerprints.

Runs the FIXED v1 configuration from heads.py (no hyperparameter search, no
CLI overrides for the training knobs - only device/threads/seed/scope are
exposed). Fitted quantities per task:

- input standardization (mean/std over that task's train rows, including any
  fallback rows; std floored at 1e-8),
- Y mean/std for regression (train rows only; predictions are de-standardized
  back to the original Y scale),
- pos_weight = n_neg/n_pos for classification.

Only train.csv rows of the selected tasks are read. The blind validation split
(never labeled in this workspace) and the test split are not touched at all.
The saved model is the state after the last fixed epoch: no early stopping and
no label-based selection anywhere.

Each head checkpoint records the identity of the feature cache it consumed
(file digests + weights sha256 + encoder parameter digest) so predict.py can
refuse to mix heads with a different cache (freeze chain: weights -> cache ->
heads -> predictions).

Usage (from output/model/):

    python -m chemeleon_baseline.train \
        --features ../../runs/features \
        --out ../../runs/train_v1 \
        --device cuda:0 --threads 8 --seed 42

Expected wall time on one modern GPU: well under 10 minutes for all 22 tasks
(53,695 rows total, ~2e5-parameter heads, 100 fixed epochs).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from .data_io import read_rows, split_path
from .features import FeatureStore
from .heads import HEAD_CONFIG, HEAD_FORMAT, MLPHead
from .tasks import load_tasks, select_tasks, validate_data_root


def _log(msg: str) -> None:
    print(f"[train {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def train_one(
    task: dict,
    rows: list[dict],
    X: np.ndarray,
    fallback_mask: np.ndarray,
    device: torch.device,
    seed: int,
) -> tuple[MLPHead, dict, float]:
    """Train a single task head. Returns (head, fitted scalars, final avg loss)."""
    kind = task["kind"]
    d_in = X.shape[1]

    input_mean = X.mean(axis=0, dtype=np.float64)
    input_std = X.std(axis=0, dtype=np.float64)
    input_std = np.where(input_std < 1e-8, 1.0, input_std)
    Xz = ((X - input_mean) / input_std).astype(np.float32)

    y = np.asarray([r["y"] for r in rows], dtype=np.float64)
    if kind == "classification":
        n_pos = float((y == 1.0).sum())
        n_neg = float((y == 0.0).sum())
        if n_pos == 0.0 or n_neg == 0.0:
            _log(f"WARNING: {task['task']} has a single class in train; pos_weight falls back to 1.0")
            pos_weight = 1.0
        else:
            pos_weight = n_neg / n_pos
        y_mean, y_std = 0.0, 1.0
        target = y.astype(np.float32)
    else:
        pos_weight = None
        y_mean = float(y.mean())
        y_std = float(y.std())
        if y_std < 1e-12:
            raise ValueError(f"{task['task']}: train Y is constant (std={y_std}); cannot standardize")
        target = ((y - y_mean) / y_std).astype(np.float32)

    torch.manual_seed(seed)
    if device.type == "cuda" and torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    head = MLPHead(d_in, tuple(HEAD_CONFIG["hidden_sizes"]), HEAD_CONFIG["dropout"]).to(device)
    opt = torch.optim.AdamW(head.parameters(), lr=HEAD_CONFIG["lr"], weight_decay=HEAD_CONFIG["weight_decay"])

    Xt = torch.from_numpy(Xz).to(device)
    yt = torch.from_numpy(target).to(device)
    if kind == "classification":
        pw = torch.tensor(float(pos_weight), dtype=torch.float32, device=device)
        loss_fn = lambda logits, tgt: nn.functional.binary_cross_entropy_with_logits(  # noqa: E731
            logits, tgt, pos_weight=pw
        )
    else:
        loss_fn = nn.functional.smooth_l1_loss

    n = Xt.shape[0]
    g = torch.Generator()
    g.manual_seed(seed)
    bs = int(HEAD_CONFIG["batch_size"])
    head.train()
    for epoch in range(int(HEAD_CONFIG["epochs"])):
        perm = torch.randperm(n, generator=g)
        tot, seen = 0.0, 0
        for start in range(0, n, bs):
            idx = perm[start : start + bs]
            logits = head(Xt[idx])
            loss = loss_fn(logits, yt[idx])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            tot += float(loss.detach()) * int(idx.shape[0])
            seen += int(idx.shape[0])
    head.eval()
    final_loss = tot / max(1, seen)

    fitted = {
        "input_mean": torch.from_numpy(input_mean.astype(np.float32)),
        "input_std": torch.from_numpy(input_std.astype(np.float32)),
        "y_mean": y_mean,
        "y_std": y_std,
        "pos_weight": None if pos_weight is None else float(pos_weight),
    }
    return head, fitted, final_loss


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-root", default=None, help="defaults to the project data root; only train.csv of selected tasks is read")
    ap.add_argument("--features", required=True, help="features cache dir produced by chemeleon_baseline.features")
    ap.add_argument("--out", required=True, help="output dir; heads written to <out>/heads/<task>.pt")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--threads", type=int, default=8, help="torch CPU threads (bounded CPU; GPU runs may set 1-2)")
    ap.add_argument("--seed", type=int, default=HEAD_CONFIG["seed"], help="run identity for reproducibility; fixed by default, not a search knob")
    ap.add_argument("--tasks", default="all")
    args = ap.parse_args(argv)

    torch.set_num_threads(max(1, args.threads))
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        print(f"ERROR: CUDA requested but torch.cuda.is_available() is False", flush=True)
        return 2

    tasks = select_tasks(load_tasks(), args.tasks)
    from .data_io import DEFAULT_DATA_ROOT

    data_root = Path(args.data_root) if args.data_root else DEFAULT_DATA_ROOT
    validate_data_root(data_root, tasks)

    store = FeatureStore(args.features)
    cache_hashes = store.file_hashes()
    _log(f"cache: {store.dir} dim={store.dim} encoded={store.matrix.shape[0]} fallback_rows_available")
    _log(f"weights sha256: {store.weights_sha256()}")
    _log(f"encoder parameter digest: {store.encoder_digest()}")

    features_identity = {
        "cache_dir": str(store.dir.resolve()),
        "weights_sha256": store.weights_sha256(),
        "encoder_parameter_digest": store.encoder_digest(),
        "fingerprint_dim": store.dim,
        **{f"sha256_{name}": h for name, h in cache_hashes.items()},
    }

    out_dir = Path(args.out).resolve()
    heads_dir = out_dir / "heads"
    heads_dir.mkdir(parents=True, exist_ok=True)

    summary: dict = {
        "schema_version": 1,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "fixed_config": dict(HEAD_CONFIG),
        "seed": args.seed,
        "device": args.device,
        "torch_threads": max(1, args.threads),
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "features_dir": str(store.dir.resolve()),
        "features_identity": features_identity,
        "tasks": {},
    }

    for t in tasks:
        started = time.time()
        rows = read_rows(split_path(data_root, t["task"], "train"), expect_y=True)
        for r in rows:
            r["task"] = t["task"]
            r["split"] = "train"
        X, fallback_mask, _fb_refs = store.vectors_for(rows)
        head, fitted, final_loss = train_one(t, rows, X, fallback_mask, device, args.seed)
        ckpt = {
            "format": HEAD_FORMAT,
            "task": t["task"],
            "kind": t["kind"],
            "metric": t["metric"],
            "d_in": int(X.shape[1]),
            "head_config": {
                "hidden_sizes": list(HEAD_CONFIG["hidden_sizes"]),
                "dropout": HEAD_CONFIG["dropout"],
                "epochs": HEAD_CONFIG["epochs"],
                "batch_size": HEAD_CONFIG["batch_size"],
                "lr": HEAD_CONFIG["lr"],
                "weight_decay": HEAD_CONFIG["weight_decay"],
            },
            "state_dict": head.state_dict(),
            "input_mean": fitted["input_mean"],
            "input_std": fitted["input_std"],
            "y_mean": fitted["y_mean"],
            "y_std": fitted["y_std"],
            "pos_weight": fitted["pos_weight"],
            "n_train_rows": len(rows),
            "n_train_fallback_rows": int(fallback_mask.sum()),
            "n_head_parameters": head.n_parameters(),
            "final_train_loss": final_loss,
            "seed": args.seed,
            "features_identity": features_identity,
            "torch_version": torch.__version__,
        }
        ckpt_path = heads_dir / f"{t['task']}.pt"
        torch.save(ckpt, ckpt_path)
        secs = round(time.time() - started, 1)
        summary["tasks"][t["task"]] = {
            "kind": t["kind"],
            "metric": t["metric"],
            "n_train_rows": len(rows),
            "n_train_fallback_rows": int(fallback_mask.sum()),
            "pos_weight": fitted["pos_weight"],
            "final_train_loss": final_loss,
            "n_head_parameters": head.n_parameters(),
            "seconds": secs,
            "checkpoint": str(ckpt_path),
        }
        _log(
            f"{t['task']}: rows={len(rows)} fallback={int(fallback_mask.sum())} "
            f"kind={t['kind']} final_loss={final_loss:.6f} params={head.n_parameters()} ({secs}s)"
        )

    (out_dir / "train_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    _log(f"trained {len(tasks)} heads -> {heads_dir}")
    _log(f"summary -> {out_dir / 'train_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
