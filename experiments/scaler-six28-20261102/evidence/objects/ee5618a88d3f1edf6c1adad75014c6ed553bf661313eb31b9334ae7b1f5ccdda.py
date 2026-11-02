#!/usr/bin/env python3
"""SCIENTIFIC_TASK item 4: float64 refit diagnostic (no labels consumed).

For every task's official-train raw cache: recompute fit-row statistics in
float64 from the stored float32 array, compare against the stored float32
statistics, and report per-policy train-fit/stop/valid/test quantiles, max
abs z and threshold-exceeding row counts.  Diagnostic only -- production
transforms stay float32.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]          # output/
PACKET = PKG.parent                                 # packet root
sys.path.insert(0, str(PKG / "src"))
sys.path.insert(0, str(PKG / "env" / "site-cpu"))

import numpy as np



from admet_breadth.cache import (FLOOR_METHOD, LEGACY_METHOD, FeatureScaler,
                                 fill_raw, fit_feature_scaler,
                                 load_raw_cache)
from admet_breadth.common import sha256_file, sha256_hex
from admet_breadth.data_io import load_split_table, split_train_stop_groups

DATA = PACKET / "input" / "data"
LEG_CACHE = PACKET / "input" / "legacy" / "cache" / "chemeleon_mp"
EVIDENCE = PACKET / "input" / "legacy" / "run-evidence"
OUT = PKG / "reports" / "float64-diagnostic.json"

TASKS = ["lipophilicity_astrazeneca", "bbb_martins", "clearance_hepatocyte_az",
         "cyp2d6_veith", "ld50_zhu", "solubility_aqsoldb"]
POLICIES = [("H0", None), ("F001", 0.001), ("F010", 0.01)]


def q(v):
    v = np.asarray(v, dtype=np.float64)
    return [round(float(x), 6) for x in np.quantile(v, [0.0, 0.25, 0.5, 0.75, 1.0])]


def _jsonable(o):
    # numpy 2.x scalars are NOT Python int/float subclasses — decode them by kind
    if isinstance(o, np.generic):
        k = o.dtype.kind
        if k == "b":
            return bool(o)
        if k in "iu":
            return int(o)
        if k == "f":
            f = float(o)
            return f if np.isfinite(f) else None
        return str(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (bool, int, float, str)) or o is None:
        return o
    return str(o)


def task_rows(task):
    rows = {s: load_split_table(DATA, task, s) for s in ("train", "valid", "test")}
    src = {s: sha256_file(DATA / task / f"{s}.csv") for s in rows}
    return rows, src


def run():
    report = {"schema": "float64_refit_diagnostic_v1", "tasks": {}}
    for task in TASKS:
        rows, src = task_rows(task)
        Xtr, oktr = load_raw_cache(LEG_CACHE, task, "train", rows["train"],
                                   src["train"], allow_migrated_legacy=True)
        ev_dir = sorted(EVIDENCE.glob(f"hainan-breadth-{task}-h0-s44-*"))
        sp = json.loads((ev_dir[0] / "internal-split.json").read_text()) \
            if ev_dir else None
        rec = split_train_stop_groups(rows["train"], seed=43, validation_fraction=0.1)
        assert sp is None or rec["split_record_sha256"] == sp["split_record_sha256"]
        fit_idx = [int(i) for i in rec["fit_row_indices"]]
        stop_idx = [int(i) for i in rec["stop_row_indices"]]

        # stored float32 legacy stats (same inputs -> same fit rows)
        sc32 = fit_feature_scaler(fill_raw(Xtr)[np.asarray(fit_idx)], fit_idx,
                                  {"method": LEGACY_METHOD})
        # float64 refit from the stored float32 representation
        A64 = fill_raw(Xtr).astype(np.float64)[fit_idx]
        mean64 = A64.mean(axis=0)
        std64 = A64.std(axis=0, ddof=0)
        d0_64 = np.where(std64 < 1e-8, 1.0, std64)

        m32, s32 = sc32.mean.astype(np.float64), sc32.std.astype(np.float64)
        changed_mean = int((m32 != mean64).sum())
        changed_std = int((s32 != d0_64).sum())
        eps = float(np.max(np.abs(s32 - d0_64)))

        out_valid = {}
        for split in ("valid", "test"):
            Xs, oks = load_raw_cache(LEG_CACHE, task, split, rows[split],
                                     src[split], allow_migrated_legacy=True)
            out_valid[split] = (fill_raw(Xs), oks)

        entry = {
            "fit_rows": len(fit_idx),
            "stored_float32_stats": {
                "min_std": float(np.min(sc32.std)),
                "n_constant_dims": int((sc32.std <= 1e-8).sum()),
                "stored_mean_sha256": sha256_hex(sc32.mean.tobytes()),
                "stored_std_sha256": sha256_hex(sc32.std.tobytes()),
            },
            "float64_vs_float32": {
                "dims_changed_mean": changed_mean,
                "dims_changed_denominator": changed_std,
                "max_abs_denominator_delta": eps,
                "float64_min_std": float(np.min(std64)),
            },
            "policies": {},
        }
        for name, floor in POLICIES:
            pol = ({"method": LEGACY_METHOD} if floor is None else
                   {"method": FLOOR_METHOD, "denominator_floor": floor})
            sc = fit_feature_scaler(fill_raw(Xtr)[np.asarray(fit_idx)], fit_idx, pol)

            def zstats(X, sc=sc):
                Z = ((X - sc.mean) / sc.std).astype(np.float64)
                absz = np.abs(Z).max(axis=1)
                return {"quantiles_abs_z_per_row_max": [round(float(x), 6) for x in np.quantile(absz, [0.0, 0.25, 0.5, 0.75, 1.0])],
                        "cells_over_threshold_10": int((np.abs(Z) > 10.0).sum()),
                        "rows_with_cell_over_threshold": int((absz > 10.0).sum())}
            d_at_floor = (int((sc.denominators_pre_floor < floor).sum())
                          if floor is not None else 0)
            p = {"denominator_floor_active_dims": d_at_floor,
                 "train_fit": zstats(fill_raw(Xtr)[np.asarray(fit_idx)]),
                 "train_stop": zstats(fill_raw(Xtr)[np.asarray(stop_idx)])}
            for split in ("valid", "test"):
                X, _ok = out_valid[split]
                p[split] = zstats(X)
            entry["policies"][name] = p
        report["tasks"][task] = entry

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1, default=_jsonable))
    print(f"wrote {OUT}")
    print("updates=0 by construction (numpy stats only)")


if __name__ == "__main__":
    run()
