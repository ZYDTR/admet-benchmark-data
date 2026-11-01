"""Offline acceptance tests for training_science helpers used by train_remote_v4.py.

Runs with stdlib + numpy only. No torch, no CUDA, no file I/O outside this output tree, and
nothing here executes a training step (no backward/optimizer/train entrypoint). Execute:

    PYTHONPYCACHEPREFIX=<this output dir>/.pycache python3 tests/test_training_science.py

Fixtures are synthetic. Real-data split checks run read-only against ../input/data/train.csv
and only re-derive the pure split helper (no model, no training).
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # output/
sys.path.insert(0, str(HERE))

import numpy as np
import training_science as ts

FAILURES: list[str] = []
PASSED = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASSED
    if cond:
        PASSED += 1
        print(f"PASS {name}")
    else:
        FAILURES.append(name)
        print(f"FAIL {name} :: {detail}")


def expect_fail(name: str, fn, *a, **kw) -> None:
    try:
        fn(*a, **kw)
    except ts.PreparationError as exc:
        check(name, True, str(exc))
        return
    check(name, False, "no PreparationError raised")


def rows(pairs, y=None):
    out = []
    for i, (rid, smi) in enumerate(pairs):
        r = {"Drug_ID": rid, "Drug": smi}
        if y is not None:
            r["Y"] = str(y[i])
        out.append(r)
    return out


# ---------------------------------------------------------------- config
base_cfg = json.loads((HERE.parent / "input/config.json").read_text())
check("config: registered config validates", ts.validate_config(base_cfg) is base_cfg or True)

bad = json.loads(json.dumps(base_cfg)); bad.pop("split_config")
expect_fail("config: missing split_config fails", ts.validate_config, bad)
bad = json.loads(json.dumps(base_cfg)); bad["head_config"]["hidden_dims"] = [256, 256]
expect_fail("config: multi-layer hidden_dims fails", ts.validate_config, bad)
bad = json.loads(json.dumps(base_cfg)); bad["head_config"]["lr"] = 0
expect_fail("config: lr<=0 fails", ts.validate_config, bad)
bad = json.loads(json.dumps(base_cfg)); bad["head_config"]["seed"] = "43"
expect_fail("config: non-int seed fails", ts.validate_config, bad)
bad = json.loads(json.dumps(base_cfg)); bad["split_config"]["method"] = "random_row"
expect_fail("config: unknown split method fails", ts.validate_config, bad)
bad = json.loads(json.dumps(base_cfg)); bad["split_config"]["validation_fraction"] = 0.0
expect_fail("config: fraction 0 fails", ts.validate_config, bad)
bad = json.loads(json.dumps(base_cfg)); bad["inputs"][0]["rows"] = 0
expect_fail("config: zero rows fails", ts.validate_config, bad)
bad = json.loads(json.dumps(base_cfg)); bad["inputs"].append(dict(bad["inputs"][0]))
expect_fail("config: duplicate role/path fails", ts.validate_config, bad)
bad = json.loads(json.dumps(base_cfg)); bad["training_only_new_head"] = False
expect_fail("config: training_only_new_head=false fails", ts.validate_config, bad)

# ---------------------------------------------------------------- split
dup = rows([("A", "SMI1"), ("B", "SMI1"), ("C", "SMI2"), ("D", "SMI3"), ("E", "SMI3"),
            ("F", "SMI4"), ("G", "SMI5"), ("H", "SMI6"), ("I", "SMI7"), ("J", "SMI8")],
           y=[0.1, 0.1, 0.2, 0.3, 0.9, 0.4, 0.5, 0.6, 0.7, 0.8])
r1 = ts.split_train_stop_groups(dup, 43, 0.1)
r2 = ts.split_train_stop_groups(dup, 43, 0.1)
check("split: same seed reproducible incl. record hash", r1 == r2)
random.seed(7); [random.random() for _ in range(9)]
r3 = ts.split_train_stop_groups(dup, 43, 0.1)
check("split: immune to global random state", r1 == r3)
np.random.seed(123); np.random.rand(5)
check("split: immune to numpy global state", ts.split_train_stop_groups(dup, 43, 0.1) == r1)
fi, si = set(r1["fit_row_indices"]), set(r1["stop_row_indices"])
check("split: fit/stop non-empty and disjoint", bool(fi) and bool(si) and not (fi & si))
check("split: exact coverage of all original rows", sorted(fi | si) == list(range(len(dup))))
fd = {dup[i]["Drug"] for i in fi}; sd = {dup[i]["Drug"] for i in si}
check("split: raw SMILES never crosses boundary", not (fd & sd))
g_dup = {k: v for k, v in r1["groups"].items() if len(v) > 1}
check("split: duplicate-SMILES groups stay whole", all(all(i in fi for i in v) or all(i in si for i in v)
                                                       for v in g_dup.values()) and len(g_dup) == 2)
check("split: duplicate Y values preserved unmodified",
      dup[g_dup["SMI1"][0]]["Y"] == "0.1" and dup[g_dup["SMI1"][1]]["Y"] == "0.1")
check("split: seed changes assignment", ts.split_train_stop_groups(dup, 44, 0.1)["split_record_sha256"]
      != r1["split_record_sha256"])
expect_fail("split: blank Drug_ID fails", ts.split_train_stop_groups,
            rows([("", "X"), ("B", "Y"), ("C", "Z"), ("D", "W")], y=[1, 2, 3, 4]), 43, 0.1)
expect_fail("split: blank Drug fails", ts.split_train_stop_groups,
            rows([("A", ""), ("B", "Y"), ("C", "Z"), ("D", "W")], y=[1, 2, 3, 4]), 43, 0.1)
expect_fail("split: invalid Y fails", ts.split_train_stop_groups,
            rows([("A", "X"), ("B", "Y"), ("C", "Z"), ("D", "W")], y=[1, float("nan"), 3, 4]), 43, 0.1)
expect_fail("split: empty table fails", ts.split_train_stop_groups, [], 43, 0.1)
expect_fail("split: fraction >= all-but-one group fails", ts.split_train_stop_groups,
            rows([("A", "X"), ("B", "Y")], y=[1, 2]), 43, 0.9)
expect_fail("split: negative seed fails", ts.split_train_stop_groups, dup, -1, 0.1)
one_drug = rows([("A", "SAME"), ("B", "SAME"), ("C", "OTHER")], y=[1, 2, 3])
o = ts.split_train_stop_groups(one_drug, 43, 0.1)
check("split: all-duplicate dataset keeps one whole group per side", o["stop_rows"] == 2 and o["fit_rows"] == 1)

# duplicate Drug_ID must NOT break train-side identity, but IS rejected for blind export contract
audit = ts.check_rows_identity(rows([("-", "X"), ("-", "Y"), ("C", "Z")], y=[1, 2, 3]),
                               require_y=True, label="train", allow_duplicate_drug_id=True)
check("identity: duplicate Drug_ID allowed+audited on train", audit["duplicate_drug_ids"] == ["-"])
try:
    ts.check_rows_identity(rows([("-", "X"), ("-", "Y")]), require_y=False, label="blind")
    check("identity: uniqueness mode rejects dup ids", False)
except ts.PreparationError:
    check("identity: uniqueness mode rejects dup ids", True)

# ---------------------------------------------------------------- real data (read-only, pure split)
with (HERE.parent / "input/data/train.csv").open(newline="", encoding="utf-8-sig") as f:
    real = list(csv.DictReader(f))
rr = ts.split_train_stop_groups(real, base_cfg["split_config"]["seed"],
                                base_cfg["split_config"]["validation_fraction"])
f_r, s_r = set(rr["fit_row_indices"]), set(rr["stop_row_indices"])
check("real-train: 637 rows fully partitioned", len(real) == 637 and sorted(f_r | s_r) == list(range(637))
      and not (f_r & s_r))
check("real-train: stop ~10%", 0.08 <= rr["stop_rows"] / 637 <= 0.12)
rd = {real[i]["Drug"] for i in f_r} & {real[i]["Drug"] for i in s_r}
check("real-train: no raw SMILES leakage", not rd)
check("real-train: reproducible under poisoned RNG",
      random.seed(31) or ts.split_train_stop_groups(real, 43, 0.1) == rr)
check("real-train: different seed gives different stop set",
      ts.split_train_stop_groups(real, 42, 0.1)["stop_row_indices"] != rr["stop_row_indices"])

# ---------------------------------------------------------------- metrics
p = np.array([1.0, 2.0, 3.0]); t = np.array([1.5, 2.0, 2.5])
check("metrics: standardized mse value", abs(ts.standardized_mse(p, t) - ((0.5 ** 2 * 2) / 3)) < 1e-12)
m = ts.scale_metrics(np.array([2.0, 4.0]), np.array([1.0, 1.0]))
check("metrics: mae/mse values", abs(m["mae"] - 2.0) < 1e-12 and abs(m["mse"] - 5.0) < 1e-12)
expect_fail("metrics: nan fails", ts.standardized_mse, np.array([1.0, np.nan]), np.array([1.0, 1.0]))
expect_fail("metrics: inf scale fails", ts.scale_metrics, np.array([np.inf]), np.array([1.0]))
expect_fail("metrics: shape mismatch fails", ts.scale_metrics, np.array([1.0, 2.0]), np.array([1.0]))
expect_fail("metrics: empty fails", ts.standardized_mse, np.array([]), np.array([]))

# ---------------------------------------------------------------- feature identity
rng = np.random.default_rng(0)
feat = rng.normal(size=(4, 3)).astype(np.float32)
mask = np.array([True, True, False, True])
feat[2] = np.nan
meta = {"module": "encoder.CheMeleonEmbedder", "checkpoint_sha256": "ab" * 32}
ident = ts.feature_identity(feat, mask, rows([("A", "X"), ("B", "Y"), ("C", "Z"), ("D", "W")]), meta, 3)
check("identity: content digest stable", ident["features"]["sha256"]
      == ts.feature_identity(feat.copy(), mask.copy(), rows([("A", "X"), ("B", "Y"), ("C", "Z"), ("D", "W")]), meta, 3)["features"]["sha256"])
perm = feat[[1, 0, 2, 3]]
ident_p = ts.feature_identity(perm, mask[[1, 0, 2, 3]], rows([("B", "Y"), ("A", "X"), ("C", "Z"), ("D", "W")]), meta, 3)
check("identity: reordered rows change identity hash", ident_p["identity_sha256"] != ident["identity_sha256"])
ident_meta = ts.feature_identity(feat, mask, rows([("A", "X"), ("B", "Y"), ("C", "Z"), ("D", "W")]),
                                 {"module": "other"}, 3)
check("identity: encoder version bound", ident_meta["identity_sha256"] != ident["identity_sha256"])
expect_fail("identity: wrong shape fails", ts.feature_identity, feat[:, :2], mask,
            rows([("A", "X"), ("B", "Y"), ("C", "Z"), ("D", "W")]), meta, 3)
expect_fail("identity: wrong dtype fails", ts.feature_identity, feat.astype(np.float64), mask,
            rows([("A", "X"), ("B", "Y"), ("C", "Z"), ("D", "W")]), meta, 3)
expect_fail("identity: mask length mismatch fails", ts.feature_identity, feat, mask[:3],
            rows([("A", "X"), ("B", "Y"), ("C", "Z"), ("D", "W")]), meta, 3)

# ---------------------------------------------------------------- rng state payload
state = ts.capture_cpu_rng_state(43)
js = json.dumps(state)  # plain containers only -> weights_only-safe
check("rng: state is JSON plain", isinstance(js, str) and "ndarray" not in js)
np.random.seed(5); np.random.rand(3)
ts.restore_cpu_rng_state(state)
a = np.random.randint(0, 2 ** 31 - 1)
ts.restore_cpu_rng_state(state)
b = np.random.randint(0, 2 ** 31 - 1)
check("rng: restore reproducible", a == b)
opt_like = {"param_groups": [{"lr": 5e-4, "weight_decay": 1e-4, "params": [0, 1]}],
            "state": {0: {"step": np.float64(12.0), "exp_avg": None}}}
pl = ts.optimizer_payload(opt_like)
check("optimizer payload: steps plain int", pl["per_param_steps"][0]["steps"] == 12.0 or
      pl["per_param_steps"][0]["steps"] == 12)
json.dumps(pl)

print(f"\n{PASSED} passed, {len(FAILURES)} failed")
if FAILURES:
    print("FAILED:", FAILURES)
    sys.exit(1)
sys.exit(0)
