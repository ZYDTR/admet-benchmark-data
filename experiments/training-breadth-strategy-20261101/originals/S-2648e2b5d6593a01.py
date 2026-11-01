"""Lightweight, no-training / no-parameter-update self-check.

Two layers:
  A. Pure-Python checks that run without torch/rdkit/chemprop: input row coverage,
     template<->test alignment, split column contracts, task list consistency, and the
     known unparseable / oversize rows observed under RDKit 2024.9.6.
  B. If torch is importable, a *synthetic* MLP forward/backward-free shape check: build the
     head, run a forward pass on random features in eval() only. No optimizer, no backward.

Run: python3 selfcheck.py                 # layer A always; B skipped if torch missing
     python3 selfcheck.py --with-torch    # require layer B
Exit code 0 = all executed checks passed.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (CLASSIFICATION_TASKS, TASKS, TEMPLATE_REL, TEST_REL,  # noqa: E402
                    TRAIN_REL, VALID_REL, read_csv_rows, resolve)


def check_inputs() -> list[str]:
    problems = []
    for task in TASKS:
        tr = read_csv_rows(resolve(TRAIN_REL.format(task=task)))
        va = read_csv_rows(resolve(VALID_REL.format(task=task)))
        te = read_csv_rows(resolve(TEST_REL.format(task=task)))
        if list(tr[0].keys()) != ["Drug_ID", "Drug", "Y"]:
            problems.append(f"{task}: train columns {list(tr[0].keys())}")
        if list(va[0].keys()) != ["Drug_ID", "Drug"]:
            problems.append(f"{task}: valid columns {list(va[0].keys())}")
        if list(te[0].keys()) != ["Drug_ID", "Drug"]:
            problems.append(f"{task}: test columns {list(te[0].keys())}")
        for name, rows in (("train", tr), ("valid", va), ("test", te)):
            if any(r["Drug"] == "" for r in rows):
                problems.append(f"{task}/{name}: empty SMILES")
        if any(r["Y"].strip() == "" for r in tr):
            problems.append(f"{task}: empty Y in train")
    return problems


def check_template() -> list[str]:
    problems = []
    tmpl = read_csv_rows(resolve(TEMPLATE_REL))
    if len(tmpl) != 16379:
        problems.append(f"template rows {len(tmpl)} != 16379")
    if any(r["y_pred"] != "" for r in tmpl):
        problems.append("template y_pred column not empty")
    by_task = {}
    for r in tmpl:
        by_task.setdefault(r["task"], []).append(r)
    if sorted(by_task) != TASKS:
        problems.append("template task set differs from TASKS")
    for task in TASKS:
        te = read_csv_rows(resolve(TEST_REL.format(task=task)))
        sub = by_task.get(task, [])
        if len(sub) != len(te):
            problems.append(f"{task}: template {len(sub)} != test {len(te)}")
            continue
        for i in range(len(te)):
            if sub[i]["drug_id"] != te[i]["Drug_ID"] or sub[i]["smiles"] != te[i]["Drug"]:
                problems.append(f"{task}: template row {i} drug/smiles mismatch")
                break
        if [int(r["sample_idx"]) for r in sub] != list(range(len(te))):
            problems.append(f"{task}: sample_idx not 0..{len(te)-1} sequential")
    return problems


def check_known_rows() -> list[str]:
    """Assert the specific anomalies documented in research/data-profile.md still hold."""
    problems = []
    te = read_csv_rows(resolve(TEST_REL.format(task="solubility_aqsoldb")))
    if len(te) != 1997:
        problems.append("solubility_aqsoldb test row count changed")
    elif not (te[1159]["Drug"].startswith("CC1=CC=C[NH+2]") and te[1160]["Drug"].startswith("O=C(O)C1=C[NH+2]")):
        problems.append("solubility rows 1159/1160 no longer the documented N-oxide failures")
    if len(te[171]["Drug"]) < 600:
        problems.append("solubility row 171 no longer the 681-char oversize SMILES")
    return problems


def check_classification_balance() -> list[str]:
    problems = []
    for task in CLASSIFICATION_TASKS:
        tr = read_csv_rows(resolve(TRAIN_REL.format(task=task)))
        y = {float(r["Y"]) for r in tr}
        if not y <= {0.0, 1.0}:
            problems.append(f"{task}: classification Y not in {{0,1}}: {sorted(y)[:5]}")
    if not CLASSIFICATION_TASKS < set(TASKS):
        problems.append("CLASSIFICATION_TASKS not a subset of TASKS")
    return problems


def check_torch_forward() -> list[str]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return [f"torch unavailable: {exc}"]
    from heads import build_head, predict_logits
    from train import DEFAULT_CFG, apply_fill

    problems = []
    model = build_head(2048, 1, DEFAULT_CFG["hidden_dims"], 0.0, 0)
    model.eval()
    X = apply_fill(torch.randn(7, 2048).numpy())
    out = predict_logits(model, X, "cpu")
    if out.shape != (7,):
        problems.append(f"head forward shape {out.shape} != (7,)")
    # trainable parameters exist only in the head (encoder is not built here)
    n_params = sum(p.numel() for p in model.parameters())
    if n_params == 0:
        problems.append("head has no parameters")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-torch", action="store_true")
    args = ap.parse_args()

    sections = {
        "inputs": check_inputs(),
        "template_alignment": check_template(),
        "known_rows": check_known_rows(),
        "classification_labels": check_classification_balance(),
    }
    torch_problems = check_torch_forward()
    sections["torch_forward"] = torch_problems
    torch_ok = not any(p.startswith("torch unavailable") for p in torch_problems)

    failed = []
    for name, probs in sections.items():
        status = "PASS" if not probs else "FAIL"
        if name == "torch_forward" and not torch_ok:
            status = "SKIP (torch not installed)"
            if args.with_torch:
                status = "FAIL (required)"
                failed.append(name)
        print(f"[{status}] {name} ({len(probs)} problem(s))")
        for p in probs:
            if not (name == "torch_forward" and not torch_ok):
                print(f"    - {p}")
                failed.append(name)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())