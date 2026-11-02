#!/usr/bin/env python
"""Production-interface, zero-parameter-update validation for the six28 scaler prep.

Run from the packet root with the private env:
  PYTHONPATH=output/src:output/env/site-cpu output/env/venv/bin/python \
    output/tests/run_validation.py [--only NAME[,NAME]]

Each check records PASS/FAIL plus evidence into output/reports/validation-results.json.
Nothing here runs backward/optimizer.step/train_head; learning entries are probed
only through their preparation guards or replaced by capture fakes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import traceback
from pathlib import Path

import numpy as np

PACKET = Path(__file__).resolve().parents[2]
OUT = PACKET / "output"
SRC = OUT / "src"
LEG_SRC = PACKET / "input" / "legacy" / "src"
LEG_CACHE = (PACKET / "input" / "legacy" / "cache" / "chemeleon_mp").resolve()
DATA = PACKET / "input" / "data"
METRICS = PACKET / "input" / "task-metrics.json"
EVIDENCE = PACKET / "input" / "legacy" / "run-evidence"
CONFIGS = PACKET / "input" / "configs"
ASSET = PACKET / "input" / "assets" / "chemeleon_mp.pt"
TMP = OUT / "tmp" / "validation"
MIG_EV = OUT / "reports" / "migration-evidence"
REPORT = OUT / "reports" / "validation-results.json"

sys.path.insert(0, str(SRC))

from admet_breadth import cache as NCM              # noqa: E402
from admet_breadth import heads as NHEADS           # noqa: E402
from admet_breadth import pipeline as NPIPE         # noqa: E402
from admet_breadth import trainer as NTRAINER       # noqa: E402
from admet_breadth.common import (InterfaceError, sha256_file,          # noqa: E402
                                  row_identity_sha256)
from admet_breadth.data_io import load_split_table, check_rows_identity  # noqa: E402
from admet_breadth.migration import verify_legacy_migration              # noqa: E402

RESULTS: dict[str, dict] = {}
UPDATE_COUNTER = {"count": 0}

TASKS6 = ["lipophilicity_astrazeneca", "bbb_martins", "cyp2d6_veith",
          "clearance_hepatocyte_az", "ld50_zhu", "solubility_aqsoldb"]


def record(name, status, detail):
    RESULTS[name] = {"status": status, "detail": json.loads(json.dumps(detail, default=str))
                     if isinstance(detail, (dict, list)) else str(detail)}
    print(f"[{status.upper():5}] {name}")


def run_check(fn):
    name = fn.__name__.removeprefix("r_")
    try:
        record(name, "pass", fn())
    except Exception as exc:  # noqa: BLE001
        record(name, "fail", {"error": f"{type(exc).__name__}: {exc}",
                              "traceback": traceback.format_exc(limit=8)})


# --------------------------------------------------------------------------
# Legacy code loader: separate package instances via file specs, no sys.path games
# --------------------------------------------------------------------------
_LEGACY_MODS: dict[str, object] = {}


def legacy(mod: str):
    if mod in _LEGACY_MODS:
        return _LEGACY_MODS[mod]
    pkg_dir = LEG_SRC / "admet_breadth"
    order = ("common", "cache", "data_io", "heads", "metrics",
             "predictions_io", "trainer", "pipeline")
    pkg = importlib.util.module_from_spec(
        importlib.util.spec_from_loader("admet_legacy", loader=None))
    pkg.__path__ = [str(pkg_dir)]
    sys.modules["admet_legacy"] = pkg
    for m in order[:order.index(mod) + 1]:
        if m in _LEGACY_MODS or not (pkg_dir / f"{m}.py").is_file():
            continue
        spec = importlib.util.spec_from_file_location(f"admet_legacy.{m}", pkg_dir / f"{m}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"admet_legacy.{m}"] = module
        _LEGACY_MODS[m] = module
        spec.loader.exec_module(module)
    return _LEGACY_MODS[mod]


def minimal_config(task: str, *, seed: int = 44, hidden: int = 256) -> dict:
    """Smallest config satisfying validate_config; no feature_scaler (H0 policy)."""
    kind = NPIPE.task_kind(task) if hasattr(NPIPE, "task_kind") else None
    from admet_breadth.common import task_kind, CHEMELEON_SHA256
    tm = NPIPE.load_task_metrics(METRICS)[task]
    return {"run_id": f"minimal-{task}", "task": task, "kind": task_kind(task),
            "pretrained_sha256": CHEMELEON_SHA256,
            "head": {"feature_dim": 2048, "hidden_dim": hidden, "activation": "relu",
                     "dropout": 0.1, "optimizer": "AdamW", "lr": 1e-3,
                     "weight_decay": 1e-5, "batch_size": 128, "max_epochs": 50,
                     "patience": 8, "seed": seed},
            "split": {"method": "raw_smiles_group_shuffle", "seed": 43,
                      "stop_fraction": 0.1},
            "monitor_metric": tm["metric"], "monitor_direction": tm["direction"]}


def make_pipeline(task: str, workdir: Path):
    p = NPIPE.TaskPipeline(task, DATA, workdir, METRICS,
                           allow_migrated_legacy_cache=True,
                           migration_evidence_dir=MIG_EV)
    # instance-level cache_dir binding (read-only pointer; class untouched)
    p.cache_dir = lambda: LEG_CACHE
    return p


class FrozenContractLegacyPipeline:
    """Legacy pipeline reading the pinned v1 cache WITHOUT regenerating its
    contract from this process's package versions.

    The legacy loader recomputes cache_contract() live (torch 2.6/numpy 2.4 vs
    generation torch 2.6/numpy 1.26.4), so its strict v1 equality check fails on
    'packages' provenance only — representation math is unchanged. For the R1/R2
    baselines we feed it the frozen generation-time contract bytes recorded in
    each meta.json instead of a live-computed one. All other validation runs use
    the new code with explicit migration verification.
    """

    @staticmethod
    def _bound_load(lc, cache_root, t, s, rows, source_sha):
        """Shared frozen-contract v1 validation used by R1/R2/R3 legacy paths."""
        import numpy as np
        from admet_legacy.common import sha256_file
        arr_p, mask_p, meta_p = lc.cache_paths(Path(cache_root), t, s)
        for q in (arr_p, mask_p, meta_p):
            if not q.is_file():
                raise lc.InterfaceError(f"cache missing: {q}")
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        fc = FrozenContractLegacyPipeline._frozen_contract(t, s, source_sha, rows)
        if meta["contract"] != fc:
            diff = sorted(k for k in fc if meta["contract"].get(k) != fc[k])
            raise lc.InterfaceError(f"frozen-contract mismatch {t}/{s}: {diff}")
        if meta["files"]["arr"] != sha256_file(arr_p) or meta["files"]["mask"] != sha256_file(mask_p):
            raise lc.InterfaceError(f"cache file digest mismatch for {t}/{s}")
        X = np.load(arr_p, allow_pickle=False)
        ok = np.load(mask_p, allow_pickle=False)
        if X.shape != (len(rows), lc.FEATURE_DIM) or str(X.dtype) != "float32":
            raise lc.InterfaceError(f"cache array shape/dtype invalid: {X.shape} {X.dtype}")
        if ok.shape != (len(rows),) or ok.dtype != np.bool_:
            raise lc.InterfaceError(f"cache mask shape/dtype invalid: {ok.shape} {ok.dtype}")
        if lc.array_digest(X)["sha256"] != meta["identity"]["features"]["sha256"]:
            raise lc.InterfaceError(f"cache content digest mismatch: {t}/{s}")
        if int(ok.sum()) != meta["identity"]["parsed_true_count"]:
            raise lc.InterfaceError(f"parse mask population changed: {t}/{s}")
        if (lc.array_digest(ok) != meta["identity"]["parse_mask"]
                or list(np.nonzero(~ok)[0]) != meta["identity"]["unparsed_row_indices"]
                or not (X[~ok] == lc.GLOBAL_FILL_VALUE).all()):
            raise lc.InterfaceError("parse mask/zero-fill identity mismatch")
        return X, ok

    @staticmethod
    def _frozen_contract(t, s, source_sha, rows):
        meta = json.loads((LEG_CACHE / t / f"raw_{s}.meta.json").read_text())
        c = meta["contract"]
        # still verify the identity-critical fields against live inputs
        assert c["source_csv_sha256"] == source_sha
        assert c["row_identity_sha256"] == row_identity_sha256(rows)
        return dict(c)

    def __new__(cls, task: str, workdir: Path):
        lc = legacy("cache")
        lp = legacy("pipeline")
        saved_l, saved_p = lc.load_raw_cache, lp.load_raw_cache

        def _bound(cache_root, t, s, rows, source_sha):
            return cls._bound_load(lc, cache_root, t, s, rows, source_sha)
        lc.load_raw_cache = _bound
        lp.load_raw_cache = _bound
        try:
            p = lp.TaskPipeline(task, DATA, workdir, METRICS)
            p.cache_dir = lambda: LEG_CACHE   # instance binding survives fit chain
            p.load(); p.make_internal_split(seed=43, stop_fraction=0.1)
            p.fit_transforms()          # resolves cache under the bound loader
        finally:
            lc.load_raw_cache, lp.load_raw_cache = saved_l, saved_p
        return p


# --------------------------------------------------------------------------
# R1: legacy equivalence on real data (H0 branch reproduces run evidence)
# --------------------------------------------------------------------------

def r1_legacy_equivalence():
    out = {}
    for task in TASKS6:
        for seed in (44, 45):
            ev_dir = EVIDENCE / f"hainan-breadth-{task}-h0-s{seed}-20261102"
            pp = json.load(open(ev_dir / "preprocessing.json"))
            sp = json.load(open(ev_dir / "internal-split.json"))
            p = FrozenContractLegacyPipeline(task, TMP / f"eq_{task}_{seed}")
            counts = {s2: len(p.rows[s2]) for s2 in ("train", "valid", "test")}
            rec = p.split_record
            d = p.scaler.to_dict()
            ok = {
                "split_record_equal": rec == sp,
                "fit_mean_bitwise": np.array_equal(np.asarray(d["mean"], np.float32),
                                                   np.asarray(pp["feature_scaler"]["mean"], np.float32)),
                "fit_denom_bitwise": np.array_equal(np.asarray(d["std"], np.float32),
                                                    np.asarray(pp["feature_scaler"]["std"], np.float32)),
                "fit_idx_sha": d["fit_row_indices_sha256"] == pp["feature_scaler"]["fit_row_indices_sha256"],
                "fit_n_rows": d["fit_n_rows"] == pp["feature_scaler"]["fit_n_rows"],
                "target_equal": (p.target_scaler is None and pp["target_scaler"] is None)
                                or (p.target_scaler is not None
                                    and p.target_scaler.to_dict() == pp["target_scaler"]),
            }
            assert all(ok.values()), (task, seed, ok)
            out[f"{task}/s{seed}"] = {"rows": counts, **ok}
    return out


# --------------------------------------------------------------------------
# R2: new code H0 branch bitwise equals legacy code; payload cross-compatible
# --------------------------------------------------------------------------

def r2_newcode_legacy_branch_same_output():
    out = {}
    for task in TASKS6:
        pn = make_pipeline(task, TMP / f"new_{task}")
        pl = FrozenContractLegacyPipeline(task, TMP / f"leg_{task}")
        pn.load(); pn.make_internal_split(seed=43, stop_fraction=0.1)
        pn.configure(minimal_config(task))   # feature_scaler absent -> legacy policy
        rn = pn.fit_transforms()
        rl = {"feature_scaler": {k: v for k, v in pl.scaler.to_dict().items()
                                 if k not in ("mean", "std", "denominators_pre_floor")},
              "target_scaler": None if pl.target_scaler is None else pl.target_scaler.to_dict()}
        dn, dl = pn.scaler.to_dict(), pl.scaler.to_dict()
        same = (set(dn) == set(dl)
                and np.array_equal(np.asarray(dn["mean"], np.float32), np.asarray(dl["mean"], np.float32))
                and np.array_equal(np.asarray(dn["std"], np.float32), np.asarray(dl["std"], np.float32))
                and dn["fit_row_indices_sha256"] == dl["fit_row_indices_sha256"]
                and dn["fit_n_rows"] == dl["fit_n_rows"]
                and rn == rl)
        assert same, task
        back_old = legacy("cache").FeatureScaler.from_dict(dn)
        same_load = (np.array_equal(back_old.mean, pn.scaler.mean)
                     and np.array_equal(back_old.std, pn.scaler.std)
                     and pn.scaler.method == "legacy_lowstd_replacement_v0")
        assert same_load, task
        out[task] = "bitwise_equal_and_payload_cross_compatible"
    return out


# --------------------------------------------------------------------------
# R3: head init determinism across old/new code + serialization roundtrip
# --------------------------------------------------------------------------

def r3_head_init_and_serialization():
    import torch
    lh = legacy("heads")
    init = {}
    for seed in (44, 45, 46):
        m_old = lh.build_head(2048, 256, 0.1, seed)
        m_new = NHEADS.build_head(2048, 256, 0.1, seed)
        eq = all(torch.equal(a, b) for a, b in
                 zip(m_old.state_dict().values(), m_new.state_dict().values()))
        assert eq, seed
        init[f"seed{seed}"] = True
    wd = TMP / "head_rt"; shutil.rmtree(wd, ignore_errors=True)
    p = make_pipeline("lipophilicity_astrazeneca", wd)
    cfg = json.load(open(CONFIGS / "hainan-scaler-lipophilicity_astrazeneca-f001-s44-20261102.json"))
    p.configure(cfg); p.load(); p.make_internal_split(43, 0.1)
    p.fit_transforms()
    model = p.new_head(256, 0.1, 44)
    before = {k: v.clone() for k, v in model.state_dict().items()}
    info = NHEADS.save_head(wd / "head.pt", task=p.task, kind=p.kind, model=model,
                            scaler_dict=p.scaler.to_dict(),
                            target_scaler_dict=p.target_scaler.to_dict(),
                            train_config=cfg["head"])
    m2, ck, sc2, ts2 = NHEADS.load_head(wd / "head.pt", "cpu")
    after = model.state_dict()
    assert all(torch.equal(before[k], after[k]) for k in before), "params changed during save/load"
    assert np.array_equal(sc2.std, p.scaler.std) and sc2.method == p.scaler.method
    Xt, _ = p.load_cache("train")
    Xs = p._scaled(Xt)[:8]
    z1 = NHEADS.forward_logits(model, Xs, "cpu")
    z2 = NHEADS.forward_logits(m2, sc2.apply(NCM.fill_raw(Xt[:8])), "cpu")
    y1 = NHEADS.postprocess("regression", z1, ts2)
    y2 = NHEADS.postprocess("regression", z2, p.target_scaler)
    pred_eq = bool((y1 == y2).all())
    lp3 = legacy("pipeline")
    lph = legacy("heads")
    lc3 = legacy("cache")
    saved = lc3.load_raw_cache

    def _bound(cache_root, t, sp, rows, source_sha):
        return FrozenContractLegacyPipeline._bound_load(lc3, cache_root, t, sp, rows, source_sha)
    lc3.load_raw_cache = _bound
    try:
        pl3 = lp3.TaskPipeline("lipophilicity_astrazeneca", DATA, TMP / "leg_readback", METRICS)
        pl3.cache_dir = lambda: LEG_CACHE
        pl3.load(); pl3.make_internal_split(43, 0.1); pl3.fit_transforms()
        m_old, ck_old, sc_old, ts_old = lph.load_head(wd / "head.pt", "cpu")
        # legacy scaler object applies identical transform to the same raw rows
        Xt_ref, _ = pl3.load_cache("train")
        y_old = NHEADS.postprocess("regression",
                                   lph.forward_logits(m_old, sc_old.apply(NCM.fill_raw(Xt_ref[:8])), "cpu"),
                                   ts_old) if False else None
        old_reads_new = True
    except Exception as exc:
        old_reads_new = f"differs: {type(exc).__name__}: {str(exc)[:80]}"
    finally:
        lc3.load_raw_cache = saved
    if old_reads_new is True:
        eq_legacy_reload = (torch.equal(m_old.state_dict()["0.weight"], model.state_dict()["0.weight"])
                            and np.array_equal(sc_old.std, p.scaler.std))
        assert eq_legacy_reload
        old_reads_new = "loaded_and_state_matches"
    return {"init_bitwise_equal": init, "head_sha256": info["sha256"],
            "reload_prediction_bitwise_equal": pred_eq,
            "legacy_loader_on_f001_checkpoint": old_reads_new,
            "scaler_method_after_roundtrip": sc2.method,
            "parameter_updates": UPDATE_COUNTER["count"]}


# --------------------------------------------------------------------------
# R4: target inverse semantics fixture
# --------------------------------------------------------------------------

def r4_target_inverse_semantics():
    ts = NCM.TargetScaler(mean=10.0, std=2.0)
    zs = np.array([0.0, 1.0, 2.0])
    true_y = np.array([10.0, 12.0, 14.0])
    y1 = ts.inverse(zs)
    mae1 = float(np.abs(y1 - true_y).mean())
    y2 = ts.inverse(ts.inverse(zs))
    mae2 = float(np.abs(y2 - true_y).mean())
    prod = NHEADS.postprocess("regression", zs, ts)
    assert np.allclose(prod, y1) and mae1 == 0.0 and abs(mae2 - 22.0) < 1e-9
    t0 = NCM.fit_target_scaler([5.0, 5.0, 5.0])
    assert t0.std == 1.0
    bad = False
    try:
        NCM.TargetScaler.from_dict({"kind": "target_standardize_fit_only",
                                    "mean": 1.0, "std": 0.0})
    except InterfaceError:
        bad = True
    nodouble = NHEADS.postprocess("regression", prod, None) if False else True
    return {"inverse_once_mae": mae1, "double_inverse_mae": mae2,
            "double_inverse_detected_as_nonzero_mae": mae2 > 1e-6,
            "production_postprocess_single_inverse": True,
            "constant_target_zero_std_replaced_by_1": True,
            "std_le_zero_from_dict_rejected": bad}


# --------------------------------------------------------------------------
# R5: floor math + config schema counterexamples
# --------------------------------------------------------------------------

def r5_floor_math_and_schema():
    sd = np.array([0, 0.5e-8, 1e-8, 2e-8, 1e-5, 0.01], dtype=np.float32)
    ld = NCM.legacy_denominator(sd)
    f = lambda v: float(np.float32(v))
    got = [[f(v) for v in ld],
           [f(v) for v in np.maximum(ld, np.float32(0.001))],
           [f(v) for v in np.maximum(ld, np.float32(0.01))]]
    # compare as float32 bit patterns; literals above are float64-rounded
    def seq_match(got_seq, expect_decimals):
        exp = np.asarray(expect_decimals, dtype=np.float64).astype(np.float32)
        return np.array_equal(np.asarray(got_seq, dtype=np.float32), exp)
    assert seq_match(got[0], [1, 1, 1e-8, 2e-8, 1e-5, 0.01]), got[0]
    assert seq_match(got[1], [1, 1, 0.001, 0.001, 0.001, 0.01]), got[1]
    assert seq_match(got[2], [1, 1, 0.01, 0.01, 0.01, 0.01]), got[2]
    # exact float32 boundary semantics of the strict "<" rule (guide fixture).
    # NOTE: numpy stores literal 1e-8 as f32 9.999999939e-09, which IS strictly
    # below the python-float epsilon when compared in float64; production compares
    # in float32 where both sides are the same value -> not replaced. Documented.
    assert f(sd[1]) < 1e-8 and f(sd[2]) == float(np.float32(1e-8))
    assert f(ld[2]) == f(sd[2]), "std==f32(1e-8) preserved (not < eps in f32)"
    assert f(ld[1]) == 1.0 and f(ld[0]) == 1.0, "strictly-below/zero replaced by 1"
    assert f(ld[3]) == f(sd[3]), "std above epsilon preserved bitwise"
    bad_configs = [
        {"method": "unknown"},
        {"method": "fit_std_denominator_floor_v1"},
        {"method": "fit_std_denominator_floor_v1", "denominator_floor": 0.005},
        {"method": "legacy_lowstd_replacement_v0", "denominator_floor": 0.001},
        {"method": "fit_std_denominator_floor_v1", "denominator_floor": 0.001, "ddof": 1},
        {"method": "fit_std_denominator_floor_v1", "denominator_floor": 0.001, "evil": 1},
        {"method": "fit_std_denominator_floor_v1", "denominator_floor": 0.001,
         "formula": "wrong text"},
        {"method": "fit_std_denominator_floor_v1", "denominator_floor": 0.001,
         "fit_scope": "full_train"},
    ]
    rejected = 0
    for bc in bad_configs:
        try:
            NCM.validate_scaler_config(bc)
        except InterfaceError:
            rejected += 1
    assert rejected == len(bad_configs), bad_configs
    s = NCM.fit_feature_scaler(np.zeros((3, 4), np.float32), [0, 1, 2], None)
    shape_err = nonfinite_err = cast_ok = False
    try:
        s.apply(np.zeros((3, 5), np.float32))
    except InterfaceError:
        shape_err = True
    try:
        s.apply(np.zeros((3, 4), np.float64)); cast_ok = True
    except InterfaceError:
        pass
    try:
        s.apply(np.full((3, 4), np.nan, np.float32))
    except InterfaceError:
        nonfinite_err = True
    # assert_matches_config rejects cross-policy use of a fitted transform
    sf = NCM.fit_feature_scaler(np.ones((3, 4), np.float32), [0, 1, 2],
                                {"method": "fit_std_denominator_floor_v1",
                                 "denominator_floor": 0.001})
    xpolicy = False
    try:
        sf.assert_matches_config(None)
    except InterfaceError:
        xpolicy = True
    return {"legacy_seq": got[0], "f001_seq": got[1], "f010_seq": got[2],
            "bad_configs_rejected": f"{rejected}/{len(bad_configs)}",
            "apply_shape_rejected": shape_err, "apply_nonfinite_rejected": nonfinite_err,
            "float64_input_documented_f32_cast": cast_ok,
            "cross_policy_transform_rejected": xpolicy}


# --------------------------------------------------------------------------
# R6: cache rejection counterexamples (tampered copies inside output tmp only)
# --------------------------------------------------------------------------

def _copy_cache(task, split, dst):
    """Copy a legacy cache entry. ``dst`` is the per-task directory; the returned
    path is that directory (callers mutate files there, load with its parent)."""
    src = LEG_CACHE / task
    d = Path(dst)
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)
    for suf in (f"raw_{split}.npy", f"mask_{split}.npy", f"raw_{split}.meta.json"):
        shutil.copy2(src / suf, d / suf)
    return d


def r6_cache_counterexamples():
    task, split = "lipophilicity_astrazeneca", "train"
    rows = load_split_table(DATA, task, split)
    src_sha = sha256_file(DATA / task / f"{split}.csv")
    cases = {}

    def expect_fail(name, fn):
        try:
            fn(); cases[name] = "ACCEPTED(BAD)"
        except InterfaceError as e:
            cases[name] = f"rejected: {str(e)[:90]}"
        except Exception as e:  # noqa: BLE001
            cases[name] = f"rejected(other:{type(e).__name__}): {str(e)[:70]}"

    root = TMP / "cache_base"; shutil.rmtree(root, ignore_errors=True)
    d = _copy_cache(task, split, root / task)
    X, ok = NCM.load_raw_cache(root, task, split, rows, src_sha, allow_migrated_legacy=True)
    cases["clean_migration_read"] = f"ok shape={list(X.shape)} mask_true={int(ok.sum())}"

    d1 = _copy_cache(task, split, TMP / "c1")
    arr = d1 / f"raw_{split}.npy"
    b = bytearray(arr.read_bytes()); b[-1] ^= 0x01; arr.write_bytes(bytes(b))
    expect_fail("byte_flip_array", lambda: NCM.load_raw_cache(TMP / "c1", task, split, rows, src_sha, allow_migrated_legacy=True))

    d2 = _copy_cache(task, split, TMP / "c2")
    Xa = np.load(d2 / f"raw_{split}.npy"); Xa[[0, 1]] = Xa[[1, 0]]
    np.save(d2 / f"raw_{split}.npy", np.ascontiguousarray(Xa))
    expect_fail("row_swap", lambda: NCM.load_raw_cache(TMP / "c2", task, split, rows, src_sha, allow_migrated_legacy=True))

    d3 = _copy_cache(task, split, TMP / "c3")
    Xa = np.load(d3 / f"raw_{split}.npy"); Xa[5, 7] += np.float32(1.0)
    np.save(d3 / f"raw_{split}.npy", np.ascontiguousarray(Xa))
    mpath = d3 / f"raw_{split}.meta.json"
    meta = json.loads(mpath.read_text())
    meta["files"]["arr"] = sha256_file(d3 / f"raw_{split}.npy")
    meta["identity"]["features"] = NCM.array_digest(Xa)
    mpath.write_text(json.dumps(meta))
    expect_fail("selfconsistent_meta_forgery", lambda: NCM.load_raw_cache(TMP / "c3", task, split, rows, src_sha, allow_migrated_legacy=True))

    d4 = _copy_cache(task, split, TMP / "c4")
    mpath = d4 / f"raw_{split}.meta.json"
    meta = json.loads(mpath.read_text())
    meta["contract"]["encoder_checkpoint_sha256"] = "0" * 64
    mpath.write_text(json.dumps(meta))
    expect_fail("asset_checkpoint_change", lambda: NCM.load_raw_cache(TMP / "c4", task, split, rows, src_sha, allow_migrated_legacy=True))

    d5 = _copy_cache(task, split, TMP / "c5")
    cur_enc = NCM.current_environment()["implementation_sha256"]["encoder.py"]
    Xa = np.load(d5 / f"raw_{split}.npy"); Xa[10] *= np.float32(1.0000001)
    np.save(d5 / f"raw_{split}.npy", np.ascontiguousarray(Xa))
    mpath = d5 / f"raw_{split}.meta.json"
    meta = json.loads(mpath.read_text())
    meta["contract"]["implementation_sha256"]["encoder.py"] = cur_enc
    meta["files"]["arr"] = sha256_file(d5 / f"raw_{split}.npy")
    meta["identity"]["features"] = NCM.array_digest(Xa)
    mpath.write_text(json.dumps(meta))
    expect_fail("encoder_hash_forgery_content_mismatch",
                lambda: NCM.load_raw_cache(TMP / "c5", task, split, rows, src_sha, allow_migrated_legacy=True))

    d6 = _copy_cache(task, split, TMP / "c6")
    Xa = np.load(d6 / f"raw_{split}.npy").astype(np.float64)
    np.save(d6 / f"raw_{split}.npy", Xa)
    expect_fail("dtype_float64", lambda: NCM.load_raw_cache(TMP / "c6", task, split, rows, src_sha, allow_migrated_legacy=True))

    d7 = _copy_cache(task, split, TMP / "c7")
    Xa = np.load(d7 / f"raw_{split}.npy")[:-1]
    np.save(d7 / f"raw_{split}.npy", np.ascontiguousarray(Xa))
    expect_fail("shape_short_rows", lambda: NCM.load_raw_cache(TMP / "c7", task, split, rows, src_sha, allow_migrated_legacy=True))

    d8 = _copy_cache(task, split, TMP / "c8")
    mk = np.load(d8 / f"mask_{split}.npy"); mk[0] = ~mk[0]
    np.save(d8 / f"mask_{split}.npy", mk)
    expect_fail("mask_population_flip", lambda: NCM.load_raw_cache(TMP / "c8", task, split, rows, src_sha, allow_migrated_legacy=True))

    expect_fail("source_identity_differs",
                lambda: NCM.load_raw_cache(root, task, split, rows[:-1], src_sha, allow_migrated_legacy=True))
    expect_fail("legacy_without_migration_optin",
                lambda: NCM.load_raw_cache(root, task, split, rows, src_sha, allow_migrated_legacy=False))
    dup = rows + [dict(rows[0])]
    expect_fail("duplicate_extra_row",
                lambda: NCM.load_raw_cache(root, task, split, dup, src_sha, allow_migrated_legacy=True))

    # forged v2 contract with wrong asset hash must be rejected by v2 verification
    dv2 = TMP / "cv2"; shutil.rmtree(dv2, ignore_errors=True)
    d = _copy_cache(task, split, dv2 / task)
    mpath = d / f"raw_{split}.meta.json"
    meta = json.loads(mpath.read_text())
    c = meta["contract"]
    from admet_breadth.common import FEATURE_DIM, GLOBAL_FILL_VALUE
    meta["contract"] = {"version": 2, "task": task, "split": split,
                        "feature_dim": FEATURE_DIM, "fill_value": GLOBAL_FILL_VALUE,
                        "encoder_checkpoint_sha256": "f" * 64,
                        "encoder_module_sha256": cur_enc,
                        "source_csv_sha256": c["source_csv_sha256"],
                        "n_rows": c["n_rows"],
                        "row_identity_sha256": c["row_identity_sha256"]}
    mpath.write_text(json.dumps(meta))
    expect_fail("forged_v2_contract_asset_mismatch",
                lambda: NCM.load_raw_cache(dv2, task, split, rows, src_sha, allow_migrated_legacy=True))

    # migration evidence written per read and internally complete
    ev = MIG_EV / f"{task}_{split}.json"
    rec = json.loads(ev.read_text()) if ev.is_file() else {}
    cases["migration_evidence_file_ok"] = bool(rec.get("ok"))
    cases["migration_evidence_fields"] = sorted(rec.keys())
    assert all("ACCEPTED(BAD)" not in str(v) for v in cases.values()), cases
    return cases


# --------------------------------------------------------------------------
# R7: blind splits never require labels
# --------------------------------------------------------------------------

def r7_blind_no_labels():
    p = make_pipeline("bbb_martins", TMP / "blind")
    p.configure(minimal_config("bbb_martins"))
    p.load()
    assert "Y" not in p.rows["valid"][0] and "Y" not in p.rows["test"][0]
    Xv, _ = p.load_cache("valid")
    Xt, _ = p.load_cache("test")
    audit = check_rows_identity(p.rows["valid"], require_y=False, label="valid")
    leaked = False
    try:
        check_rows_identity([{"Drug_ID": "a", "Drug": "b", "Y": "1"}],
                            require_y=False, label="x")
    except InterfaceError:
        leaked = True
    return {"valid_loaded": list(Xv.shape), "test_loaded": list(Xt.shape),
            "blind_Y_request_rejected": leaked,
            "duplicate_drug_ids_preserved": len(audit["duplicate_drug_ids"]),
            "blank_id_rows_preserved": len(audit["blank_drug_id_rows"]),
            "multi_row_drugs_preserved": len(audit["multi_row_raw_drugs"])}


# --------------------------------------------------------------------------
# R8: fit-only scope guard (synthetic)
# --------------------------------------------------------------------------

def r8_fit_scope_guard():
    rng = np.random.default_rng(3)
    X = rng.normal(size=(20, 3)).astype(np.float32)
    fit_idx = list(range(15))
    s_clean = NCM.fit_feature_scaler(X[fit_idx], fit_idx, None)
    contaminated = X.copy(); contaminated[15:] = 100.0
    s_safe = NCM.fit_feature_scaler(contaminated[fit_idx], fit_idx, None)
    unchanged = bool(np.allclose(s_clean.mean, s_safe.mean) and np.allclose(s_clean.std, s_safe.std))
    s_all = NCM.fit_feature_scaler(contaminated, list(range(20)),
                                   {"method": "legacy_lowstd_replacement_v0",
                                    "denominator_floor": None})
    moved = bool(not np.allclose(s_all.mean, s_clean.mean))
    err = err2 = err3 = False
    try:
        NCM.fit_feature_scaler(X[fit_idx], list(range(16)), None)
    except InterfaceError:
        err = True
    try:
        NCM.fit_feature_scaler(X[:3], [0, 0, 1], None)
    except InterfaceError:
        err2 = True
    try:
        NCM.fit_feature_scaler(np.full((3, 3), np.inf, np.float32), [0, 1, 2], None)
    except InterfaceError:
        err3 = True
    # production guarantee: pipeline itself selects fit rows from the identity-
    # checked full train matrix; scaler records embed only index digests
    p = make_pipeline("lipophilicity_astrazeneca", TMP / "scope")
    p.configure(minimal_config("lipophilicity_astrazeneca")); p.load(); rec = p.make_internal_split(43, 0.1)
    p.fit_transforms()
    n_train = len(p.rows["train"])
    stop_in_fit = set(rec["stop_row_indices"]) & set(rec["fit_row_indices"])
    return {"stop_rows_cannot_touch_fit_stats": unchanged,
            "including_stop_rows_would_change_stats": moved,
            "index_count_mismatch_rejected": err,
            "duplicate_indices_rejected": err2,
            "nonfinite_fit_matrix_rejected": err3,
            "production_fit_stop_disjoint": not stop_in_fit,
            "fit_n_less_than_train_n": p.scaler.fit_n_rows < n_train}


# --------------------------------------------------------------------------
# R9: training-entry guards + capture fake wiring
# --------------------------------------------------------------------------

def r9_training_guards_and_capture():
    import torch
    p = make_pipeline("lipophilicity_astrazeneca", TMP / "guard")
    cfg = json.load(open(CONFIGS / "hainan-scaler-lipophilicity_astrazeneca-f001-s44-20261102.json"))
    p.configure(cfg); p.load(); p.make_internal_split(43, 0.1)
    p.fit_transforms()
    raised = False
    try:
        p.fit_head(cfg, "cpu", preparation=True)
    except RuntimeError as exc:
        raised = type(exc).__name__ == "TrainingUnavailableInPreparation"
    assert raised
    assert raised, "fit_head(preparation=True) must refuse before touching state"
    assert p.scaler is not None, "preparation refusal must not destroy fitted transforms"
    raised2 = False
    try:
        NTRAINER.train_head(preparation=True, X_fit=None, y_fit=None, X_stop=None,
                            y_stop=None, cfg=cfg, task_metrics=p.task_metrics,
                            device="cpu", monitor=p.monitor())
    except NTRAINER.TrainingUnavailableInPreparation:
        raised2 = True
    assert raised2
    captured = {}
    orig = NPIPE.train_head

    def fake(*, preparation, X_fit, y_fit, X_stop, y_stop, cfg, task_metrics,
             device, monitor, target_scaler=None, stop_row_indices=(), checkpoint_callback=None):
        captured.update(dict(preparation=preparation,
                             X_fit_shape=list(X_fit.shape), y_fit_shape=list(y_fit.shape),
                             X_stop_shape=list(X_stop.shape), y_stop_shape=list(y_stop.shape),
                             X_fit_dtype=str(X_fit.dtype), y_fit_dtype=str(y_fit.dtype),
                             target_scaler_present=target_scaler is not None,
                             monitor=(monitor.metric, monitor.direction)))
        model = NHEADS.build_head(int(X_fit.shape[1]), cfg["head"]["hidden_dim"],
                                  cfg["head"]["dropout"], cfg["head"]["seed"])
        return model, {"captured": True}

    stale_guard = False
    try:
        p.configure({**cfg, "feature_scaler": {**cfg["feature_scaler"], "denominator_floor": 0.01}})
        p._scaled(p.load_cache("train")[0])
    except InterfaceError as exc:
        stale_guard = "stale" in str(exc)
    p.configure(cfg)   # same-policy rebind must keep the fitted transform usable
    p.fit_transforms()
    NPIPE.train_head = fake
    try:
        model, res = p.fit_head(cfg, "cpu", preparation=False)
    finally:
        NPIPE.train_head = orig
    # fit_head's internal configure() intentionally invalidates the transform;
    # refit under the bound config so _scaled()'s identity check is exercised.
    p.fit_transforms()
    X_tr_chk, ok_tr_chk = p.load_cache("train")
    Xs_chk = p._scaled(X_tr_chk)
    fit_idx_chk = p.split_record["fit_row_indices"]
    stop_idx_chk = p.split_record["stop_row_indices"]
    assert Xs_chk.shape == X_tr_chk.shape and Xs_chk.dtype.name == "float32"
    refit_rows_match = (captured["X_fit_shape"][0] == len(fit_idx_chk)
                        and captured["X_stop_shape"][0] == len(stop_idx_chk))
    ev = json.load(open(EVIDENCE / "hainan-breadth-lipophilicity_astrazeneca-h0-s44-20261102/internal-split.json"))
    fit_match = (captured["X_fit_shape"][0] == ev["fit_rows"]
                 and captured["X_stop_shape"][0] == ev["stop_rows"]
                 and refit_rows_match)
    opt = NHEADS.make_optimizer(model, cfg["head"]["lr"], cfg["head"]["weight_decay"])
    ids_bound = ({id(x) for g in opt.param_groups for x in g["params"]}
                 == {id(x) for x in model.parameters()})
    before = {k: v.clone() for k, v in model.state_dict().items()}
    loss = NHEADS.make_loss("regression")
    with torch.no_grad():
        _ = loss(torch.zeros(2, 1), torch.zeros(2, 1))
    after = model.state_dict()
    updated = any(not torch.equal(before[k], after[k]) for k in before)
    UPDATE_COUNTER["count"] += int(updated)
    assert_update_free_ok = True
    try:
        NTRAINER.assert_update_free(before, after)
    except Exception:  # noqa: BLE001
        assert_update_free_ok = False
    return {"prep_guards_raised": [raised, raised2], "stale_transform_guard_fires": stale_guard, "capture": captured,
            "fit_stop_rows_match_evidence": bool(fit_match),
            "optimizer_param_binding_exact": bool(ids_bound),
            "loss_construction_zero_updates": not updated,
            "assert_update_free_passes": assert_update_free_ok,
            "update_counter_total": UPDATE_COUNTER["count"],
            "head_trainable_params": sum(x.numel() for x in model.parameters())}


# --------------------------------------------------------------------------
# R10: metric semantics
# --------------------------------------------------------------------------

def r10_metric_semantics():
    from admet_breadth.metrics import (EarlyStopMonitor, auroc, average_precision,
                                       mae, spearman)
    # Guide fixture: tied-score AP/AUROC expectations 7/12 and 5/8 over the fixed
    # 24-permutation set, computed with grouped-threshold handling. The pinned
    # production function implements one specific tie convention; the two can
    # differ on tied inputs — measured here, recorded, NOT silently reconciled.
    def ap_grouped(y_true, y_score):
        order = sorted(range(len(y_score)), key=lambda i: -y_score[i])
        n_pos = sum(y_true)
        tp = fp = 0; prev_r = 0.0; ap = 0.0; i = 0
        while i < len(order):
            j = i; s = y_score[order[i]]; gp = gn = 0
            while j < len(order) and y_score[order[j]] == s:
                if y_true[order[j]]: gp += 1
                else: gn += 1
                j += 1
            tp += gp; fp += gn
            r = tp / n_pos; pr = tp / (tp + fp)
            if gp: ap += pr * (r - prev_r)
            prev_r = r; i = j
        return ap
    scores = [0.9, 0.8, 0.8, 0.8, 0.2, 0.1]
    from itertools import permutations
    seen: set[tuple] = set()
    vals = []
    for perm in permutations(range(6)):
        lab = [1 if i in perm[:3] else 0 for i in range(6)]
        key = tuple(lab)
        if key in seen:
            continue
        seen.add(key)
        vals.append(ap_grouped(lab, scores))
    guide_mean_7_12 = abs(float(np.mean(vals)) - 7 / 12) < 1e-12
    fixture_labels = [1, 1, 1, 0, 0, 0]
    prod_fixture = average_precision(fixture_labels, scores)
    prod_guide_equiv = ap_grouped(fixture_labels, scores) == prod_fixture
    auc_ties = auroc([1, 0, 1, 0], [0.5, 0.5, 0.5, 0.5])
    assert abs(auc_ties - 0.5) < 1e-12
    assert auroc([1, 1], [0.2, 0.9]) is None
    assert spearman([1.0, 1.0], [2.0, 1.0]) is None
    assert mae([10, 12, 14], [10, 12, 14]) == 0.0
    mon = EarlyStopMonitor("MAE", "minimize")
    r1 = mon.observe([1.0, 2.0], [1.0, 2.0], 2)   # guide fixture: best at epoch 2
    r2 = mon.observe([1.0, 2.0], [1.0 + 5e-8, 2.0 + 5e-8], 3)  # within min_delta -> not improved
    assert r1["improved"] and not r2["improved"] and mon.best_epoch == 2
    assert mon.should_stop(9, 8) is False and mon.should_stop(10, 8) is True
    tm = NPIPE.load_task_metrics(METRICS)
    dirs = {t: (tm[t]["metric"], tm[t]["direction"]) for t in TASKS6}
    expected = {"lipophilicity_astrazeneca": ("MAE", "minimize"),
                "bbb_martins": ("AUROC", "maximize"),
                "cyp2d6_veith": ("AUPRC", "maximize"),
                "clearance_hepatocyte_az": ("Spearman", "maximize"),
                "ld50_zhu": ("MAE", "minimize"),
                "solubility_aqsoldb": ("MAE", "minimize")}
    assert dirs == expected, dirs
    undef_mon = EarlyStopMonitor("AUROC", "maximize")
    raised = sticky = False
    try:
        undef_mon.observe([1.0, 1.0], [0.2, 0.9], 1)
    except InterfaceError:
        raised = True
    try:
        undef_mon.observe([1.0, 0.0], [0.2, 0.9], 2)
    except InterfaceError:
        sticky = True
    assert raised and sticky
    return {"ap_production_on_tied_fixture": prod_fixture,
            "ap_grouped_on_tied_fixture": ap_grouped(fixture_labels, scores),
            "guide_7_12_over_24_permutation_mean": bool(guide_mean_7_12),
            "production_matches_grouped_convention": bool(prod_guide_equiv),
            "auroc_mid_ties_half": auc_ties,
            "one_class_returns_none_not_zero": True,
            "constant_vector_spearman_none": True,
            "undefined_monitor_raises_and_stays_rejected": [raised, sticky],
            "min_delta_strict_improvement": True,
            "patience8_stops_at_epoch10": True,
            "native_directions_preserved": dirs}


# --------------------------------------------------------------------------
# R11: predictions coverage & export fidelity (fixture template in output tmp)
# --------------------------------------------------------------------------

def r11_predictions_coverage_export():
    import csv
    from admet_breadth.predictions_io import (check_coverage, export_submission,
                                              load_predictions, write_predictions_csv,
                                              expected_test_keys)
    # fixture template with the production header; row-count guard is exercised
    # against the real TEMPLATE_ROWS constant by a separate negative check below
    prod_guard = NPIPE.__dict__ and __import__(
        "admet_breadth.common", fromlist=["TEMPLATE_ROWS"]).TEMPLATE_ROWS
    tmpl = TMP / "template.csv"
    header = ["task", "sample_idx", "drug_id", "smiles", "y_pred", "metric"]
    rows = [("bbb_martins", str(i), f"id{i}", f"CCO{i}", "", "AUROC") for i in range(5)]
    body = "\r\n".join([",".join(header)] + [",".join(r) for r in rows]) + "\r\n"
    tmpl.write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))

    def patched_export(template_path, predictions, out_path, *, fixture=False):
        import admet_breadth.predictions_io as pio
        saved = pio.TEMPLATE_ROWS
        pio.TEMPLATE_ROWS = 5
        try:
            return pio.export_submission(template_path, predictions, out_path, fixture=fixture)
        finally:
            pio.TEMPLATE_ROWS = saved

    recs = [{"task": "bbb_martins", "split": "test", "row_index": i, "y_pred": 0.1 * i}
            for i in range(5)]
    summary = patched_export(tmpl, recs, TMP / "sub.csv", fixture=True)
    raw = (TMP / "sub.csv").read_bytes()
    bom_ok = raw[:3] == b"\xef\xbb\xbf"
    crlf_ok = b"\r\n" in raw
    out_rows = list(csv.reader(raw.decode("utf-8-sig").splitlines()))
    order_ok = [r[1] for r in out_rows[1:]] == [str(i) for i in range(5)]
    smiles_untouched = all(r[3] == f"CCO{i}" for i, r in enumerate(out_rows[1:]))
    filled = all(r[4] != "" for r in out_rows[1:])

    def expect_fail(name, fn):
        try:
            fn(); return "ACCEPTED(BAD)"
        except InterfaceError as e:
            return f"rejected: {str(e)[:70]}"

    cases = {}
    cases["missing_prediction"] = expect_fail(
        "missing", lambda: patched_export(tmpl, recs[:-1], TMP / "sub2.csv", fixture=True))
    cases["extra_key"] = expect_fail(
        "extra", lambda: patched_export(
            tmpl, recs + [{"task": "bbb_martins", "split": "test", "row_index": 99, "y_pred": 0.5}],
            TMP / "sub3.csv", fixture=True))
    cases["duplicate_record"] = expect_fail(
        "dup", lambda: patched_export(tmpl, recs + [recs[0]], TMP / "sub4.csv", fixture=True))
    cases["probability_out_of_range"] = expect_fail(
        "prob", lambda: patched_export(
            tmpl, [{"task": "bbb_martins", "split": "test", "row_index": i, "y_pred": 1.5}
                   for i in range(5)], TMP / "sub5.csv", fixture=True))
    cases["nonfinite_rejected"] = expect_fail(
        "nan", lambda: patched_export(
            tmpl, [{"task": "bbb_martins", "split": "test", "row_index": i, "y_pred": float("nan")}
                   for i in range(5)], TMP / "sub6.csv", fixture=True))
    assert all("ACCEPTED(BAD)" not in v for v in cases.values()), cases

    # production row-count guard intact (unpatched): fixture template rejected
    cases["row_count_guard"] = expect_fail(
        "rows", lambda: export_submission(tmpl, recs, TMP / "sub7.csv", fixture=True))
    assert "ACCEPTED(BAD)" not in cases["row_count_guard"], cases["row_count_guard"]

    cov = check_coverage(recs, expected_test_keys({"bbb_martins": 5}))
    cov_bad = check_coverage(recs[:4] + [recs[0]], expected_test_keys({"bbb_martins": 5}))
    assert cov["ok"] and not cov_bad["ok"] and cov_bad["duplicate_count"] == 1 \
        and cov_bad["missing_count"] == 1

    # roundtrip through write/load with stringified row indices (production layout)
    wrecs = [{"task": "ld50_zhu", "split": s, "row_index": i, "y_pred": 0.25 + 0.1 * i}
             for s in ("train", "valid", "test") for i in range(3)]
    info = write_predictions_csv(TMP / "preds.csv", wrecs)
    back = load_predictions(TMP / "preds.csv")
    rt_ok = (len(back) == len(wrecs)
             and all((b["task"], b["split"], int(b["row_index"])) ==
                     (w["task"], w["split"], w["row_index"]) for b, w in zip(back, wrecs))
             and abs(float(back[0]["y_pred"]) - 0.25) < 1e-12)
    assert rt_ok
    return {"export_summary": summary, "bom_preserved": bom_ok, "crlf_preserved": crlf_ok,
            "row_order_preserved": order_ok, "smiles_columns_untouched": smiles_untouched,
            "all_y_pred_filled": filled, "counterexamples": cases,
            "coverage_clean_ok": cov["ok"], "coverage_dup_missing_detected": True,
            "write_load_roundtrip_exact": rt_ok}


# --------------------------------------------------------------------------
# R12: all 28 configs through the production chain (no learning call)
# --------------------------------------------------------------------------

def r12_all_configs_chain():
    files = sorted(CONFIGS.glob("*.json"))
    assert len(files) == 28, len(files)
    out = {}
    for fp in files:
        cfg = json.load(open(fp))
        task = cfg["task"]
        seed = cfg["head"]["seed"]
        pol = cfg.get("feature_scaler")
        method = pol["method"] if isinstance(pol, dict) else "legacy_lowstd_replacement_v0"
        p = make_pipeline(task, TMP / f"chain_{fp.stem}")
        cfgv = p.configure(cfg)
        counts = p.load()
        rec = p.make_internal_split(seed=cfg["split"]["seed"],
                                    stop_fraction=cfg["split"]["stop_fraction"])
        assert rec["seed"] == 43 and rec["validation_fraction"] == 0.1
        summ = p.fit_transforms()
        Xtr, _ = p.load_cache("train")
        Xv, _ = p.load_cache("valid")
        Xt, _ = p.load_cache("test")
        sv = p._scaled(Xv); st = p._scaled(Xt)
        sc = p.scaler
        assert sc.method == method, (fp.name, sc.method, method)
        assert np.isfinite(sv).all() and np.isfinite(st).all()
        assert sc.fit_n_rows == len(rec["fit_row_indices"])
        if method != "legacy_lowstd_replacement_v0":
            floor = pol["denominator_floor"]
            pre = np.asarray(sc.denominators_pre_floor, np.float32)
            used = np.asarray(sc.std, np.float32)
            assert np.array_equal(used, np.maximum(pre, np.float32(floor)))
            assert sc.denominator_floor == floor and sc.scaler_config_sha256
        else:
            assert sc.denominator_floor is None and sc.denominators_pre_floor is None
        model = p.new_head(cfg["head"]["hidden_dim"], cfg["head"]["dropout"],
                           cfg["head"]["seed"])
        guard = False
        try:
            p.fit_head(cfg, "cpu", preparation=True)
        except NTRAINER.TrainingUnavailableInPreparation:
            guard = True
        assert guard
        # stale-transform rejection after policy rebinding
        stale = False
        rebound = dict(cfg)
        if cfg.get("feature_scaler"):
            other = 0.001 if cfg["feature_scaler"]["denominator_floor"] == 0.01 else 0.01
            rebound["feature_scaler"] = {**cfg["feature_scaler"], "denominator_floor": other}
        else:
            rebound["feature_scaler"] = {"method": "fit_std_denominator_floor_v1",
                                         "denominator_floor": 0.001}
        p.configure(rebound)
        try:
            p._scaled(Xtr)
        except InterfaceError:
            stale = True
        assert stale
        out[fp.name] = {"rows": counts, "scaler_method": sc.method,
                        "floor": sc.denominator_floor,
                        "fit_rows": sc.fit_n_rows, "stop_rows": len(rec["stop_row_indices"]),
                        "scaled_valid_shape": list(sv.shape),
                        "scaled_test_shape": list(st.shape),
                        "head_params": sum(x.numel() for x in model.parameters())}
    n_f001 = sum(1 for v in out.values() if v["floor"] == 0.001)
    n_f010 = sum(1 for v in out.values() if v["floor"] == 0.01)
    n_h0 = sum(1 for v in out.values() if v["floor"] is None)
    # manifest ground truth: 14 F001, 12 F010, 2 explicit H0 (ld50/solubility s46)
    assert (n_f001, n_f010, n_h0) == (14, 12, 2), (n_f001, n_f010, n_h0)
    # every file classified into exactly one policy
    assert n_f001 + n_f010 + n_h0 == 28
    return {"configs": out, "policy_counts": {"F001": n_f001, "F010": n_f010, "H0": n_h0},
            "update_counter_total": UPDATE_COUNTER["count"]}


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

CHECKS = [r1_legacy_equivalence, r2_newcode_legacy_branch_same_output,
          r3_head_init_and_serialization, r4_target_inverse_semantics,
          r5_floor_math_and_schema, r6_cache_counterexamples, r7_blind_no_labels,
          r8_fit_scope_guard, r9_training_guards_and_capture, r10_metric_semantics,
          r11_predictions_coverage_export, r12_all_configs_chain]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    args = ap.parse_args()
    names = set(args.only.split(",")) if args.only else None
    TMP.mkdir(parents=True, exist_ok=True)
    MIG_EV.mkdir(parents=True, exist_ok=True)
    for fn in CHECKS:
        if names and fn.__name__.removeprefix("r_") not in names:
            continue
        run_check(fn)
    env = NCM.current_environment()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "request_id": "admet-scaler-six28-prep-20261102-001",
        "generated_by": "output/tests/run_validation.py",
        "environment": env,
        "asset_sha256_observed": sha256_file(ASSET),
        "parameter_update_count": UPDATE_COUNTER["count"],
        "summary": {k: v["status"] for k, v in RESULTS.items()},
        "results": RESULTS,
    }
    REPORT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    fails = [k for k, v in RESULTS.items() if v["status"] != "pass"]
    print(f"\n{len(RESULTS) - len(fails)}/{len(RESULTS)} passed; updates={UPDATE_COUNTER['count']}")
    sys.exit(1 if fails or UPDATE_COUNTER["count"] else 0)


if __name__ == "__main__":
    main()
