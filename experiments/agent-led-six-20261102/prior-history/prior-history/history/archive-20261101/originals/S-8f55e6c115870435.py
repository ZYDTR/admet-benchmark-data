"""End-to-end wiring self-test with a *dependency-free* NumPy reference head.

Purpose: prove that the data -> internal-split -> scaler(fit on train only) -> train loop ->
inverse-transform -> valid/test prediction wire is correct, with full row coverage, WITHOUT
running the real training that belongs to the main Codex, and without torch/rdkit.

It deliberately avoids the frozen encoder: instead of CheMeleon features it uses a small
deterministic NumPy embedding of the SMILES characters (16-d). This exercises plumbing and
row bookkeeping, not model quality. Outputs go to a throwaway tmp dir.

Run: python3 selftest_tiny.py [--root <project root>] [--tasks ames caco2_wang]
Exit 0 = wiring checks passed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (GLOBAL_FILL_VALUE, TEMPLATE_REL, TEST_REL, TRAIN_REL,  # noqa: E402
                    VALID_REL, read_csv_rows, resolve, task_kind)
from heads import build_np_head, compress_features, np_forward, np_train_epoch  # noqa: E402
from train import _prepare_arrays  # noqa: E402


def fake_embed(smiles: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic character-bigram-ish embedding standing in for CheMeleon."""
    dim = 32
    out = np.zeros((len(smiles), dim), dtype=np.float32)
    ok = np.ones(len(smiles), dtype=bool)
    for i, s in enumerate(smiles):
        for j, ch in enumerate(s):
            out[i, (ord(ch) + j) % dim] += 1.0
        if not s:
            ok[i] = False
            out[i] = np.nan
    return out, ok


def run_task(task: str, epochs: int = 40) -> dict:
    tr = read_csv_rows(resolve(TRAIN_REL.format(task=task)))
    va = read_csv_rows(resolve(VALID_REL.format(task=task)))
    te = read_csv_rows(resolve(TEST_REL.format(task=task)))

    Xtr, oktr = fake_embed([r["Drug"] for r in tr])
    Xva, okva = fake_embed([r["Drug"] for r in va])
    Xte, okte = fake_embed([r["Drug"] for r in te])
    y = np.asarray([float(r["Y"]) for r in tr], dtype=np.float32)

    kind = task_kind(task)
    cfg = {"seed": 0, "val_fraction_from_train": 0.2}
    Xs, y_s, tr_idx, va_idx, mu, sd, y_mu, y_sd = _prepare_arrays(Xtr, y, kind, cfg)
    Xc = compress_features(Xs)
    head = build_np_head(Xc.shape[1], 32, seed=0)
    rng = np.random.default_rng(0)
    for _ in range(epochs):
        np_train_epoch(head, Xc[tr_idx], y_s[tr_idx], kind, 0.05, 64, rng)

    def infer(Xraw):
        Xc_ = compress_features((np.where(np.isfinite(Xraw), Xraw, GLOBAL_FILL_VALUE) - mu) / sd)
        z = np_forward(head, Xc_)
        return (z * y_sd + y_mu) if kind == "regression" else 1.0 / (1.0 + np.exp(-z))

    pva, pte = infer(Xva), infer(Xte)
    return {
        "task": task,
        "kind": kind,
        "train_rows": len(tr),
        "valid_rows": len(va),
        "test_rows": len(te),
        "valid_pred_len": len(pva),
        "test_pred_len": len(pte),
        "all_finite": bool(np.isfinite(pva).all() and np.isfinite(pte).all()),
        "scaler_mu_finite": bool(np.isfinite(mu).all()),
        "regression_scale_restored": bool(kind != "regression" or y_sd > 0),
        "train_pred_range": [float(pva.min()), float(pva.max())],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="*", default=["ames", "caco2_wang", "cyp2c9_veith"])
    ap.add_argument("--epochs", type=int, default=40)
    args = ap.parse_args()

    results, failures = [], []
    for task in args.tasks:
        r = run_task(task, args.epochs)
        results.append(r)
        if not r["all_finite"]:
            failures.append(f"{task}: non-finite predictions")
        if r["valid_pred_len"] != r["valid_rows"]:
            failures.append(f"{task}: valid coverage {r['valid_pred_len']}/{r['valid_rows']}")
        if r["test_pred_len"] != r["test_rows"]:
            failures.append(f"{task}: test coverage {r['test_pred_len']}/{r['test_rows']}")
        if not r["scaler_mu_finite"]:
            failures.append(f"{task}: scaler non-finite")
        print(f"[tiny] {task:20s} {r['kind']:14s} valid={r['valid_rows']} test={r['test_rows']} "
              f"pred_range=[{r['train_pred_range'][0]:.3g},{r['train_pred_range'][1]:.3g}]")

    # Cross-check: test row count must equal the template block for each task.
    tmpl = read_csv_rows(resolve(TEMPLATE_REL))
    for task in args.tasks:
        n_tmpl = sum(1 for r in tmpl if r["task"] == task)
        n_test = sum(1 for _ in read_csv_rows(resolve(TEST_REL.format(task=task))))
        if n_tmpl != n_test:
            failures.append(f"{task}: template {n_tmpl} != test {n_test}")

    print("RESULT:", "PASS" if not failures else "FAIL")
    for f in failures:
        print("  -", f)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())