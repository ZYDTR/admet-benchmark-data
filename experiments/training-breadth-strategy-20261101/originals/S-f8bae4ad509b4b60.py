"""Train one small MLP head per task on cached frozen CheMeleon embeddings.

Only official train rows (with official numeric Y) are used for fitting. The scaler and all
regression target statistics are fitted on train rows only. Validation and test are consumed
read-only at inference; no validation labels are read by this script at all (the blind
validation copy has no Y column).

The encoder is *not* loaded here: features come from the cache produced by
``build_features.py``. This keeps the train step provably encoder-free.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

from common import (GLOBAL_FILL_VALUE, TASKS, TRAIN_REL, read_csv_rows,  # noqa: E402
                    resolve, task_kind, write_json)
from heads import build_head, make_optimizer, predict_logits  # noqa: E402

DEFAULT_HIDDEN = [512]
DEFAULT_CFG = {
    "hidden_dims": DEFAULT_HIDDEN,
    "dropout": 0.1,
    "lr": 1e-3,
    "weight_decay": 1e-4,
    "batch_size": 128,
    "epochs": 50,
    "patience": 8,
    "val_fraction_from_train": 0.1,
    "seed": 42,
}


def fit_scaler(X):
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd < 1e-8] = 1.0
    return mu.astype(np.float32), sd.astype(np.float32)


def apply_fill(X: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(X), X, np.float32(GLOBAL_FILL_VALUE))


def internal_split(n: int, seed: int, val_fraction: float):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    n_val = max(1, int(round(n * val_fraction)))
    return idx[n_val:], idx[:n_val]


def _prepare_arrays(X_raw: np.ndarray, y_raw: np.ndarray, kind: str, cfg: dict):
    X = apply_fill(X_raw)
    tr_idx, va_idx = internal_split(len(y_raw), cfg["seed"], cfg["val_fraction_from_train"])
    mu, sd = fit_scaler(X[tr_idx])
    Xs = (X - mu) / sd
    if kind == "regression":
        y_mu = float(y_raw[tr_idx].mean())
        y_sd = float(y_raw[tr_idx].std()) or 1.0
        y_s = (y_raw - y_mu) / y_sd
    else:
        y_mu, y_sd = 0.0, 1.0
        y_s = y_raw
    return Xs, y_s, tr_idx, va_idx, mu, sd, y_mu, y_sd


def _fit_metric(kind: str, y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if kind == "regression":
        return float(np.mean((y_pred - y_true) ** 2))
    p = np.clip(y_pred, 1e-7, 1 - 1e-7)
    return float(-np.mean(y_true * np.log(p) + (1 - y_true) * np.log(1 - p)))


def train_one_task(task: str, X_raw: np.ndarray, y_raw: np.ndarray, cfg: dict, device: str):
    import torch
    from torch import nn

    kind = task_kind(task)
    Xs, y_s, tr_idx, va_idx, mu, sd, y_mu, y_sd = _prepare_arrays(X_raw, y_raw, kind, cfg)

    model = build_head(Xs.shape[1], 1, cfg["hidden_dims"], cfg["dropout"], cfg["seed"]).to(device)
    opt = make_optimizer(model, cfg["lr"], cfg["weight_decay"])
    loss_fn = nn.BCEWithLogitsLoss() if kind == "classification" else nn.MSELoss()

    Xt = torch.as_tensor(np.ascontiguousarray(Xs[tr_idx]), dtype=torch.float32, device=device)
    yt = torch.as_tensor(y_s[tr_idx], dtype=torch.float32, device=device).reshape(-1, 1)
    Xv = torch.as_tensor(np.ascontiguousarray(Xs[va_idx]), dtype=torch.float32, device=device)
    yv = torch.as_tensor(y_s[va_idx], dtype=torch.float32, device=device).reshape(-1, 1)

    gen = torch.Generator(device="cpu").manual_seed(cfg["seed"])
    best_val, best_epoch, best_state = float("inf"), -1, None
    n = len(tr_idx)
    for epoch in range(cfg["epochs"]):
        model.train()
        perm = torch.randperm(n, generator=gen)
        for start in range(0, n, cfg["batch_size"]):
            sel = perm[start:start + cfg["batch_size"]]
            opt.zero_grad(set_to_none=True)
            loss = loss_fn(model(Xt[sel]), yt[sel])
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(Xv), yv).item())
        if val_loss < best_val - 1e-7:
            best_val, best_epoch = val_loss, epoch
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        elif epoch - best_epoch >= cfg["patience"]:
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    tr_logits = predict_logits(model, Xs[tr_idx], device)
    va_logits = predict_logits(model, Xs[va_idx], device)

    def to_y(logit):
        if kind == "regression":
            return logit * y_sd + y_mu
        return 1.0 / (1.0 + np.exp(-logit))

    tr_pred, va_pred = to_y(tr_logits), to_y(va_logits)

    ckpt = {
        "format": "chemeleon_mlp_head_v1",
        "task": task,
        "kind": kind,
        "encoder": "chemeleon_mp",
        "feature_dim": int(Xs.shape[1]),
        "fill_value": GLOBAL_FILL_VALUE,
        "scaler": {"mean": mu, "std": sd},
        "target": {"mean": y_mu, "std": y_sd},
        "head": {
            "hidden_dims": cfg["hidden_dims"],
            "dropout": cfg["dropout"],
            "activation": "relu",
            "output": "sigmoid_probability" if kind == "classification"
                      else "linear_standardized_then_unscaled",
        },
        "train_config": cfg,
        "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
        "fit_rows": int(len(tr_idx)),
        "internal_val_rows": int(len(va_idx)),
    }
    metrics = {
        "task": task,
        "kind": kind,
        "epochs_run": epoch + 1,
        "best_epoch": best_epoch,
        "best_internal_val_loss": best_val,
        "train_rows": int(len(tr_idx)),
        "internal_val_rows": int(len(va_idx)),
        "train_fit_metric": _fit_metric(kind, y_raw[tr_idx], tr_pred),
        "internal_val_fit_metric": _fit_metric(kind, y_raw[va_idx], va_pred),
        "note": "internal split from official train only; official blind validation is never "
                "read by train.py",
    }
    return model, ckpt, metrics


def load_ckpt(path: Path, device: str):
    import torch

    ck = torch.load(path, map_location="cpu", weights_only=False)
    model = build_head(ck["feature_dim"], 1, ck["head"]["hidden_dims"],
                      ck["head"].get("dropout", 0.0), 0)
    model.load_state_dict(ck["state_dict"])
    model.to(device)
    model.eval()
    return model, ck


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[3]
    ap.add_argument("--cache", type=Path, default=root / "output/model/cache/chemeleon_mp")
    ap.add_argument("--out", type=Path, default=root / "output/model/runs/chemeleon_mlp_v1")
    ap.add_argument("--tasks", nargs="*", default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("--epochs", type=int, default=None, help="override cfg epochs (smoke tests)")
    ap.add_argument("--seed", type=int, default=DEFAULT_CFG["seed"])
    args = ap.parse_args()

    import torch

    from build_features import load_split

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    cfg = dict(DEFAULT_CFG)
    cfg["seed"] = args.seed
    if args.epochs is not None:
        cfg["epochs"] = args.epochs

    tasks = args.tasks or TASKS
    out = args.out
    (out / "heads").mkdir(parents=True, exist_ok=True)
    write_json(out / "train_config.json", cfg)

    all_metrics = {}
    t0 = time.time()
    for task in tasks:
        X, ok, rows = load_split(args.cache, task, "train")
        assert all(r["row_index"] == i for i, r in enumerate(rows))
        table = read_csv_rows(resolve(TRAIN_REL.format(task=task)))
        assert len(table) == len(rows), f"{task}: cache/train row mismatch"
        y = np.asarray([float(r["Y"]) for r in table], dtype=np.float32)

        model, ckpt, metrics = train_one_task(task, X, y, cfg, device)
        torch.save(ckpt, out / "heads" / f"{task}.pt")
        all_metrics[task] = metrics
        print(f"[train] {task:35s} kind={metrics['kind']:14s} "
              f"epochs={metrics['epochs_run']:3d} best_epoch={metrics['best_epoch']:3d} "
              f"val_loss={metrics['best_internal_val_loss']:.4f}", flush=True)

    write_json(out / "metrics.json", {
        "encoder": "chemeleon_mp",
        "device": device,
        "train_config": cfg,
        "elapsed_seconds": round(time.time() - t0, 2),
        "tasks": all_metrics,
    })
    print(f"trained {len(tasks)} heads -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())