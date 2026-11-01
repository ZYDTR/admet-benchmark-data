"""Train one small MLP head per task on frozen CheMeleon features.

NOT executed in this preparation session (no torch, no weights, no batch features).
Main control runs this after ``encode_features.py``.

Design (fixed first version; no hyper-parameter search):

* Input: cached features for ``train`` and ``valid`` (cite-only for early
  stopping). Blind ``valid`` is *never* used to select weights — early stopping
  uses a fixed fraction of *train* rows as an internal holdout.
* Regression: ``TargetScaler`` fitted on train labels only; loss on z-scored
  targets; predictions de-standardised back to the original Y scale.
* Classification: single logit, BCE-with-logits on class-weighted targets.
* The encoder is not imported here, so it cannot be fine-tuned by construction.

Outputs per task under ``--out``:

    <task>/head.pt          (torch.save weights_only-readable payload)
    <task>/train_log.json   (loss curve, holdout split, digests, config)
    <task>/run.json         (input digests, cache keys, deps, seed)

``--tasks`` selects which tasks to train.  Each task is trained independently;
a failure in one task does not abort the others but is recorded in the exit
summary (nonzero exit if any task failed).
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
from dataio import input_digest, read_split
from errors import CacheError, ContractError, FeaturizationError
from feature_cache import build_manifest, load_cache
from head_model import HEAD_CONFIG, TargetScaler, build_head, save_head


def _load_features(cache_dir, table, feature_dim, weights_meta, deps, batch_size):
    meta = {
        "id": "chemeleon_mp",
        "code_commit": CHEMELEON_CODE_COMMIT,
        "feature_dim": feature_dim,
        "weights": weights_meta,
    }
    manifest = build_manifest(table, meta, deps, batch_size)
    feats, cached = load_cache(cache_dir, manifest)
    kept = cached["kept_row_indices"]
    labels_by_row = {r["row_index"]: r["label"] for r in table["rows"]}
    y = np.asarray([labels_by_row[i] for i in kept], dtype=np.float64)
    return feats, y, cached


def _internal_split(n, seed, frac=0.1):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    n_hold = max(1, int(round(n * frac))) if n >= 10 else max(1, n // 5)
    n_hold = min(n_hold, n - 1) if n > 1 else 0
    hold = np.sort(idx[:n_hold])
    fit = np.sort(idx[n_hold:])
    return fit, hold


def train_one(task, task_kind, Xtr, ytr, cfg):
    import torch

    torch.manual_seed(cfg["seed"])
    np.random.seed(cfg["seed"])
    if task_kind == "regression":
        # Fit the scaler on ALL train rows (fit portion + holdout) so evaluation
        # of holdout loss is on the same scale the final model would use; the
        # scaler never sees valid/test.
        scaler = TargetScaler.fit(ytr)
        z = scaler.transform(ytr)
    else:
        scaler = None
        z = ytr.astype(np.float64)

    fit_idx, hold_idx = _internal_split(len(z), cfg["seed"])
    if len(fit_idx) == 0:
        raise ContractError(f"{task}: no fit rows after internal split")

    head, _out_dim, cfg = build_head(Xtr.shape[1], task_kind, cfg)
    opt = torch.optim.AdamW(head.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])

    if task_kind == "classification":
        pos = float((z[fit_idx] == 1).sum())
        neg = float((z[fit_idx] == 0).sum())
        if pos == 0 or neg == 0:
            raise ContractError(f"{task}: single-class training labels; head undefined")
        pos_weight = torch.tensor([neg / pos], dtype=torch.float32)
        loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    else:
        loss_fn = torch.nn.MSELoss()

    Xtr_t = torch.from_numpy(Xtr.astype(np.float32))
    z_t = torch.from_numpy(z.astype(np.float32).reshape(-1, 1))

    best = {"epoch": -1, "hold_loss": float("inf"), "state": None}
    log = {"fit_rows": int(len(fit_idx)), "holdout_rows": int(len(hold_idx)), "epochs": []}
    bs = cfg["batch_size"]
    for epoch in range(cfg["max_epochs"]):
        head.train()
        order = np.random.permutation(fit_idx)
        running = 0.0
        nb = 0
        for start in range(0, len(order), bs):
            batch = order[start:start + bs]
            if len(batch) == 0:
                continue
            opt.zero_grad()
            out = head(Xtr_t[batch])
            loss = loss_fn(out, z_t[batch])
            loss.backward()
            opt.step()
            running += float(loss.item())
            nb += 1
        head.eval()
        with torch.no_grad():
            if len(hold_idx):
                out_h = head(Xtr_t[hold_idx])
                hold_loss = float(loss_fn(out_h, z_t[hold_idx]).item())
            else:
                hold_loss = float("nan")
        train_loss = running / max(nb, 1)
        log["epochs"].append({"epoch": epoch, "train_loss": train_loss,
                              "hold_loss": hold_loss})
        if hold_loss == hold_loss and hold_loss < best["hold_loss"]:
            best = {"epoch": epoch, "hold_loss": hold_loss,
                    "state": {k: v.detach().clone() for k, v in head.state_dict().items()}}
        if epoch - best["epoch"] >= cfg["early_stopping_patience"]:
            break
    if best["state"] is None:
        raise ContractError(f"{task}: no finite holdout loss observed")
    head.load_state_dict(best["state"])
    head.eval()
    log["best"] = {"epoch": best["epoch"], "hold_loss": best["hold_loss"]}
    return head, scaler, cfg, log


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--asset-lock", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tasks", nargs="*", required=True)
    ap.add_argument("--feature-dim", type=int, required=True,
                    help="must equal the encoder output dim recorded by encode_features")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--seed", type=int, default=HEAD_CONFIG["seed"])
    ap.add_argument("--train-table", default=None,
                    help="JSON {task: 'classification'|'regression'} override")
    args = ap.parse_args(argv)

    try:  # fail fast with a clear message instead of a NameError halfway through
        import torch  # noqa: F401
    except Exception as exc:
        print(f"[deps] torch import failed: {exc!r}; install 'chemprop>=2.2.0' "
              f"(which pulls torch) before training", file=sys.stderr)
        return 2
    if np is None:
        print("[deps] numpy import failed; install numpy before training", file=sys.stderr)
        return 2

    lock = load_lock(args.asset_lock)
    weights_meta = {"size": lock["weights_size"], "md5": lock["weights_md5"],
                    "sha256": lock["weights_sha256"]}
    deps = package_versions()
    missing = [k for k, v in deps.items() if v is None]
    if missing:
        print(f"[deps] missing packages: {missing}", file=sys.stderr)
        return 2

    kinds = None
    if args.train_table:
        with open(args.train_table, "r", encoding="utf-8") as fh:
            kinds = json.load(fh)

    cfg = dict(HEAD_CONFIG)
    cfg["seed"] = args.seed

    results = []
    failed = []
    for task in args.tasks:
        try:
            tr = read_split(args.data_root, task, "train")
            kind = (kinds or {}).get(task)
            if kind is None:
                kind = _default_kind(task)
            Xtr, ytr, ctr = _load_features(args.cache, tr, args.feature_dim,
                                           weights_meta, deps, args.batch_size)
            Xva, yva, cva = _load_features(
                args.cache, read_split(args.data_root, task, "valid"), args.feature_dim,
                weights_meta, deps, args.batch_size)
            head, scaler, cfg_used, log = train_one(task, kind, Xtr, ytr, cfg)
            if kind == "classification":
                log["positive_rate"] = float((ytr == 1).mean())
            outdir = os.path.join(args.out, task)
            save_head(head, os.path.join(outdir, "head.pt"), task, kind, scaler, cfg_used,
                      extra={"cache_keys": {"train": ctr["key"], "valid": cva["key"]}})
            digests = input_digest([("train", tr), ("valid", read_split(args.data_root, task, "valid"))])
            with open(os.path.join(outdir, "train_log.json"), "w", encoding="utf-8") as fh:
                json.dump({"task": task, "task_kind": kind, "config": cfg_used,
                           "split": log, "input_digest": digests,
                           "train_cache_key": ctr["key"]}, fh, indent=2, sort_keys=True)
            with open(os.path.join(outdir, "run.json"), "w", encoding="utf-8") as fh:
                json.dump({"task": task, "task_kind": kind, "deps": deps,
                           "weights": weights_meta, "encoder_commit": CHEMELEON_CODE_COMMIT,
                           "config": cfg_used, "input_digest": digests,
                           "cache_keys": {"train": ctr["key"], "valid": cva["key"]}},
                          fh, indent=2, sort_keys=True)
            results.append({"task": task, "status": "ok", "best_hold_loss": log["best"]["hold_loss"],
                            "best_epoch": log["best"]["epoch"]})
        except (ContractError, CacheError, FeaturizationError, ValueError) as exc:
            failed.append({"task": task, "status": "failed", "error": repr(exc)})
    print(json.dumps({"results": results, "failed": failed}, indent=2))
    return 1 if failed else 0


_KINDS = {
    "regression": ["caco2_wang", "clearance_hepatocyte_az", "clearance_microsome_az",
                   "half_life_obach", "ld50_zhu", "lipophilicity_astrazeneca",
                   "ppbr_az", "solubility_aqsoldb", "vdss_lombardo"],
}


def _default_kind(task):
    for kind, tasks in _KINDS.items():
        if task in tasks:
            return kind
    return "classification"


if __name__ == "__main__":
    sys.exit(main())