#!/usr/bin/env python3
"""SCIENTIFIC_TASK item 4b: no-label association diagnostic.

Uses ONLY (a) the stored raw feature cache and (b) the legacy run-evidence
valid predictions (no ground truth is read). For each task and each scaler
policy we compute, per valid/test row: the max |z| feature magnitude, then
correlate it with the recorded prediction value / |prediction - median|.
Row identity (split, row_index, Drug_ID) is preserved in every record.
Association only — no causal claim, no truth access.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]          # output/
PACKET = PKG.parent                                 # packet root
sys.path.insert(0, str(PKG / "src"))
sys.path.insert(0, str(PKG / "env" / "site-cpu"))

import numpy as np

from admet_breadth.cache import (FLOOR_METHOD, LEGACY_METHOD, fill_raw,
                                 fit_feature_scaler, load_raw_cache)
from admet_breadth.common import sha256_file
from admet_breadth.data_io import load_split_table, split_train_stop_groups

DATA = PACKET / "input" / "data"
LEG_CACHE = PACKET / "input" / "legacy" / "cache" / "chemeleon_mp"
EVIDENCE = PACKET / "input" / "legacy" / "run-evidence"
OUT = PKG / "reports" / "association-diagnostic.json"

TASKS = ["lipophilicity_astrazeneca", "bbb_martins", "clearance_hepatocyte_az",
         "cyp2d6_veith", "ld50_zhu", "solubility_aqsoldb"]
POLICIES = [("H0", None), ("F001", 0.001), ("F010", 0.01)]


def pearson(a, b):
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(np.float64)
    rb = np.argsort(np.argsort(b)).astype(np.float64)
    return pearson(ra, rb)


def main():
    report = {"schema": "no_label_association_v1",
              "note": "feature magnitude vs legacy valid predictions; NO truth used",
              "tasks": {}}
    for task in TASKS:
        rows = {s: load_split_table(DATA, task, s) for s in ("train", "valid")}
        src = {s: sha256_file(DATA / task / f"{s}.csv") for s in ("train", "valid")}
        Xtr, _ = load_raw_cache(LEG_CACHE, task, "train", rows["train"],
                                src["train"], allow_migrated_legacy=True)
        rec = split_train_stop_groups(rows["train"], seed=43, validation_fraction=0.1)
        fit_idx = [int(i) for i in rec["fit_row_indices"]]
        Xv, okv = load_raw_cache(LEG_CACHE, task, "valid", rows["valid"],
                                 src["valid"], allow_migrated_legacy=True)
        Fv = fill_raw(Xv)

        ev = sorted(EVIDENCE.glob(f"hainan-breadth-{task}-h0-s44-*"))[0]
        with open(ev / "predictions-valid.csv", newline="", encoding="utf-8-sig") as fh:
            preds = list(csv.DictReader(fh))
        y_pred = np.array([float(p["y_pred"]) for p in preds], dtype=np.float64)
        parse_ok = np.array([p["parse_ok"] == "True" for p in preds])
        assert len(preds) == Fv.shape[0]
        ident = [(p["row_index"], p["Drug_ID"]) for p in preds]

        entry = {"n_valid_rows": len(preds),
                 "identity_sample": ident[:3] + ident[-1:],
                 "policies": {}}
        for name, floor in POLICIES:
            pol = ({"method": LEGACY_METHOD} if floor is None else
                   {"method": FLOOR_METHOD, "denominator_floor": floor})
            sc = fit_feature_scaler(fill_raw(Xtr)[np.asarray(fit_idx)], fit_idx, pol)
            Z = np.abs((Fv - sc.mean) / sc.std).astype(np.float64)
            mag = Z.max(axis=1)                      # per-row feature magnitude
            dev = np.abs(y_pred - float(np.median(y_pred)))
            entry["policies"][name] = {
                "pearson_mag_vs_y_pred": pearson(mag, y_pred),
                "spearman_mag_vs_y_pred": spearman(mag, y_pred),
                "pearson_mag_vs_pred_deviation": pearson(mag, dev),
                "spearman_mag_vs_pred_deviation": spearman(mag, dev),
                "top10_by_mag_mean_pred_dev": round(float(dev[np.argsort(-mag)[:10]].mean()), 6),
                "overall_mean_pred_dev": round(float(dev.mean()), 6),
            }
        report["tasks"][task] = entry

    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT}")
    print("updates=0; no labels read")


if __name__ == "__main__":
    main()
