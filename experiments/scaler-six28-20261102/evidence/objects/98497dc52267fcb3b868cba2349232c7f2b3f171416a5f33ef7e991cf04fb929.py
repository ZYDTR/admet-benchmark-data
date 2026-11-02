"""Raw embedding cache and fit-only transforms (two separate layers).

Layer 1 — raw representation cache: frozen-encoder output per (task, split), bound
to a *representation* identity record (checkpoint sha256, encoder-module sha256,
source CSV sha256, full ordered row identity, feature dim, dtype, finiteness
digests, parse mask) plus the recorded *generation environment* (the packages
and non-encoder modules in effect when the arrays were produced). The consumer
environment is verified separately and recorded; it is never required to equal
the generation environment for mathematically unchanged read-only consumption.
Non-encoder module hashes (cache/data_io/heads) are NOT representation identity:
changing transform code must not invalidate content-verified raw arrays, but any
reuse of a legacy-format cache requires an explicit, evidence-backed migration
(see migration.py) instead of silently relaxing hash checks.

Layer 2 — fit transform: feature standardization whose statistics are fitted ONLY
on the official-train fit partition (never internal-stop rows, never valid/test).
Two policies exist:
  * legacy: d = 1 if population std < 1e-8 else std                (H0 branch)
  * fit_std_denominator_floor_v1:
        d0 = same legacy denominator; d = max(d0, denominator_floor)
    Constant dimensions keep d = 1 (legacy replacement happens BEFORE the floor).
Both policies carry their full parameter identity inside the serialized scaler;
a saved transform cannot be consumed under a different configuration.
Regression target standardization likewise fits on the fit partition only.

Unparseable rows keep their position, get the documented constant zero raw fill
before scaling, and remain visible through the parse mask. No cleaning happens.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .common import (CHEMELEON_SHA256, FEATURE_DIM, GLOBAL_FILL_VALUE,
                     InterfaceError, array_digest, canonical_json_bytes,
                     row_identity_sha256, sha256_hex, sha256_file, write_json)

LEGACY_METHOD = "legacy_lowstd_replacement_v0"
FLOOR_METHOD = "fit_std_denominator_floor_v1"
SCALER_CONFIG_KEYS = ("method", "denominator_floor", "legacy_epsilon",
                      "legacy_low_std_replacement", "fit_statistic_dtype",
                      "ddof", "transform_dtype", "fit_scope")

# Documentation-only field admitted from run configs and verified verbatim so it
# cannot silently disagree with the executed policy.
FLOOR_FORMULA_TEXT = ("legacy_d = 1 if fit_std < 1e-8 else fit_std; "
                      "d = max(legacy_d, denominator_floor); z = (x-fit_mean)/d")


def _module_sha256() -> dict[str, str]:
    base = Path(__file__).resolve().parent
    out = {}
    for name in ("encoder.py", "cache.py", "data_io.py", "heads.py"):
        p = base / name
        out[name] = sha256_file(p) if p.is_file() else "absent"
    return out


def current_environment() -> dict[str, Any]:
    """Consumer environment snapshot: package versions + this checkout's modules.

    Recorded for auditing only. Raw representation identity binds the ENCODER
    module and checkpoint; other module hashes here document which code produced
    or consumed a cache, so differences are visible rather than faked.
    """
    from importlib.metadata import version as _pkg_version
    pkgs = {}
    for pkg in ("chemprop", "rdkit", "torch", "numpy"):
        try:
            pkgs[pkg] = _pkg_version(pkg)
        except Exception:
            pkgs[pkg] = "absent"
    return {"packages": pkgs, "implementation_sha256": _module_sha256()}


def representation_contract(task: str, split: str, source_sha256: str,
                            rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    """Identity binding a raw cache entry to data + encoder implementation + row order."""
    env = current_environment()
    return {
        "version": 2,
        "task": task,
        "split": split,
        "feature_dim": FEATURE_DIM,
        "fill_value": GLOBAL_FILL_VALUE,
        "encoder_checkpoint_sha256": CHEMELEON_SHA256,
        "encoder_module_sha256": env["implementation_sha256"]["encoder.py"],
        "source_csv_sha256": source_sha256,
        "n_rows": len(rows),
        "row_identity_sha256": row_identity_sha256(rows),
    }


def cache_paths(cache_root: Path, task: str, split: str):
    d = cache_root / task
    return (d / f"raw_{split}.npy", d / f"mask_{split}.npy",
            d / f"raw_{split}.meta.json")


def build_raw_cache(embedder, task: str, split: str, rows: Sequence[Mapping[str, str]],
                    source_sha256: str, cache_root: Path,
                    contract: dict[str, Any] | None = None) -> dict[str, Any]:
    """Encode every row of one split (deduplicating identical SMILES strings within
    the split, broadcasting back to each original row index) and persist the cache.

    Returns the identity record. Caller must supply rows already loaded unchanged.
    """
    import numpy as np

    smiles = [r["Drug"] for r in rows]
    uniq = list(dict.fromkeys(smiles))
    u_emb, u_ok = embedder.embed(uniq)
    pos = {s: i for i, s in enumerate(uniq)}
    take = np.asarray([pos[s] for s in smiles], dtype=np.int64)
    emb, ok = u_emb[take], u_ok[take]
    if emb.shape != (len(rows), embedder.feature_dim):
        raise InterfaceError(f"{task}/{split}: unexpected embedding shape {emb.shape}")
    if embedder.feature_dim != FEATURE_DIM or ok.shape != (len(rows),) or ok.dtype != np.bool_:
        raise InterfaceError("encoder dimension/parse mask does not match cache contract")
    if not np.isfinite(emb[ok]).all():
        raise InterfaceError("non-finite output on a parsed row must not be zero-filled")
    filled = np.asarray(emb, dtype=np.float32).copy()
    filled[~ok] = np.float32(GLOBAL_FILL_VALUE)
    arr_p, mask_p, meta_p = cache_paths(cache_root, task, split)
    arr_p.parent.mkdir(parents=True, exist_ok=True)
    np.save(arr_p, np.ascontiguousarray(filled))
    np.save(mask_p, ok)
    contract = contract or representation_contract(task, split, source_sha256, rows)
    meta = {
        "contract": contract,
        "generation_environment": current_environment(),
        "consumption_environment_at_build": current_environment(),
        "files": {"arr": sha256_file(arr_p), "mask": sha256_file(mask_p)},
        "identity": {
            "features": array_digest(filled),
            "parse_mask": array_digest(ok),
            "parsed_true_count": int(ok.sum()),
            "unparsed_row_indices": [int(i) for i in np.nonzero(~ok)[0]],
        },
    }
    write_json(meta_p, meta)
    load_raw_cache(cache_root, task, split, rows, source_sha256)
    return meta


def _verify_v2_meta(meta: Mapping[str, Any], expected_contract: Mapping[str, Any]):
    if meta["contract"] != dict(expected_contract):
        diff = sorted(k for k in expected_contract
                      if meta["contract"].get(k) != expected_contract[k])
        raise InterfaceError(f"stale/corrupt cache representation for: {diff}")


def load_raw_cache(cache_root: Path, task: str, split: str,
                   rows: Sequence[Mapping[str, str]], source_sha256: str,
                   *, allow_migrated_legacy: bool = False, cache_trust=None):
    """Validate-and-load a raw cache entry against live input identity.

    Accepts v2 contracts directly. A v1 (legacy) contract is accepted ONLY when
    ``allow_migrated_legacy=True`` AND migration.verify_legacy_migration proves
    the representation identity equivalent (encoder module, checkpoint, data,
    row order, array bytes). Never falls back to silent acceptance.
    """
    import numpy as np

    arr_p, mask_p, meta_p = cache_paths(Path(cache_root), task, split)
    for p in (arr_p, mask_p, meta_p):
        if not p.is_file():
            raise InterfaceError(f"cache missing: {p}")
    if allow_migrated_legacy or cache_trust is not None:
        if cache_trust is None:
            raise InterfaceError("legacy cache requires a controller-anchored trusted manifest")
        cache_trust.verify(cache_root, task, split)
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    version = meta.get("contract", {}).get("version")
    if version == 1:
        if not allow_migrated_legacy:
            raise InterfaceError(
                f"legacy v1 cache for {task}/{split}: reuse requires explicit "
                "migration verification (migration.verify_legacy_migration); "
                "refusing to bypass or silently relax identity checks")
        from .migration import verify_legacy_migration
        verify_legacy_migration(Path(cache_root), task, split, rows, source_sha256,
                                cache_trust=cache_trust)
    elif version == 2:
        _verify_v2_meta(meta, representation_contract(task, split, source_sha256, rows))
    else:
        raise InterfaceError(f"unsupported cache contract version: {version!r}")
    if meta["files"]["arr"] != sha256_file(arr_p) or meta["files"]["mask"] != sha256_file(mask_p):
        raise InterfaceError(f"cache file digest mismatch for {task}/{split}")
    X = np.load(arr_p, allow_pickle=False)
    ok = np.load(mask_p, allow_pickle=False)
    if X.shape != (len(rows), FEATURE_DIM) or str(X.dtype) != "float32":
        raise InterfaceError(f"cache array shape/dtype invalid: {X.shape} {X.dtype}")
    if ok.shape != (len(rows),) or ok.dtype != np.bool_:
        raise InterfaceError(f"cache mask shape/dtype invalid: {ok.shape} {ok.dtype}")
    if array_digest(X)["sha256"] != meta["identity"]["features"]["sha256"]:
        raise InterfaceError(f"cache content digest mismatch (reordered/tampered?): {task}/{split}")
    if not np.isfinite(X).all():
        raise InterfaceError(f"cache contains non-finite values: {task}/{split}")
    if int(ok.sum()) != meta["identity"]["parsed_true_count"]:
        raise InterfaceError(f"parse mask population changed: {task}/{split}")
    if (array_digest(ok) != meta["identity"]["parse_mask"]
            or list(np.nonzero(~ok)[0]) != meta["identity"]["unparsed_row_indices"]
            or not (X[~ok] == GLOBAL_FILL_VALUE).all()):
        raise InterfaceError("parse mask/zero-fill identity mismatch")
    return X, ok


def validate_scaler_config(cfg: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Strict schema check for the config 'feature_scaler' field.

    None means the legacy H0 branch. Absent keys fall back to defaults; present
    keys must match the admitted values exactly — no aliasing, no partial override.
    """
    import math
    if cfg is None:
        return None
    if not isinstance(cfg, dict):
        raise InterfaceError("feature_scaler must be an object or absent")
    doc_only = {k: v for k, v in cfg.items() if k == "formula"}
    unknown = sorted(set(cfg) - set(SCALER_CONFIG_KEYS) - {"formula"})
    if unknown:
        raise InterfaceError(f"feature_scaler unknown keys: {unknown}")
    if "formula" in doc_only and doc_only["formula"] != FLOOR_FORMULA_TEXT:
        raise InterfaceError("feature_scaler.formula text differs from the canonical "
                             "floor-v1 definition")
    method = cfg.get("method", LEGACY_METHOD)
    if method not in (LEGACY_METHOD, FLOOR_METHOD):
        raise InterfaceError(f"feature_scaler.method not implemented: {method!r}")
    if method == LEGACY_METHOD and "denominator_floor" in cfg \
            and cfg["denominator_floor"] is not None:
        # An explicit null carries no floor; only a present value contradicts H0.
        raise InterfaceError("legacy scaler must not carry a denominator_floor")
    floor = cfg.get("denominator_floor")
    if method == FLOOR_METHOD:
        if floor not in (0.001, 0.01):
            raise InterfaceError(f"denominator_floor must be 0.001 or 0.01, got {floor!r}")
    elif floor is not None:
        raise InterfaceError("legacy scaler must not carry a denominator_floor")
    eps = cfg.get("legacy_epsilon", 1e-8)
    if eps != 1e-8:
        raise InterfaceError("legacy_epsilon is fixed at 1e-8")
    rep = cfg.get("legacy_low_std_replacement", 1.0)
    if rep != 1.0:
        raise InterfaceError("legacy_low_std_replacement is fixed at 1.0")
    if cfg.get("fit_statistic_dtype", "float32") != "float32":
        raise InterfaceError("fit_statistic_dtype must be float32")
    if cfg.get("ddof", 0) != 0:
        raise InterfaceError("ddof must be 0 (population std)")
    if cfg.get("transform_dtype", "float32") != "float32":
        raise InterfaceError("transform_dtype must be float32")
    if cfg.get("fit_scope", "internal_fit_only") != "internal_fit_only":
        raise InterfaceError("fit_scope must be internal_fit_only")
    if floor is not None and (not isinstance(floor, float) or not math.isfinite(floor)):
        raise InterfaceError("denominator_floor must be finite")
    return {"method": method, "denominator_floor": floor, "legacy_epsilon": 1e-8,
            "legacy_low_std_replacement": 1.0, "fit_statistic_dtype": "float32",
            "ddof": 0, "transform_dtype": "float32", "fit_scope": "internal_fit_only"}


def legacy_denominator(sd, epsilon: float = 1e-8, replacement: float = 1.0):
    """Original production denominator: where(std < eps, replacement, std)."""
    import numpy as np
    return np.where(sd < epsilon, np.float32(replacement), sd)


@dataclass
class FeatureScaler:
    """Fit-only feature standardization with explicit fit-partition and policy identity.

    Legacy instances carry method='legacy_lowstd_replacement_v0' and serialize
    EXACTLY the v1 dict (same keys, same semantics), so previously saved heads
    load unchanged. Floor instances additionally bind method/floor/config and the
    pre-floor denominators, making cross-policy misuse detectable.
    """

    mean: Any            # np.ndarray float32 [d]
    std: Any             # np.ndarray float32 [d] — denominator actually used
    fit_partition: str   # always "official_train.fit_subset"
    fit_row_indices_sha256: str
    fit_n_rows: int
    epsilon: float = 1e-8
    method: str = LEGACY_METHOD
    denominator_floor: float | None = None
    scaler_config_sha256: str | None = None
    denominators_pre_floor: Any = None   # np.ndarray float32 [d] (floor policy only)

    def apply(self, X):
        import numpy as np
        A = np.asarray(X, dtype=np.float32)
        if A.ndim != 2 or A.shape[1] != self.mean.shape[0]:
            raise InterfaceError(f"scaler.apply shape invalid: {A.shape}")
        if not np.isfinite(A).all():
            raise InterfaceError("scaler.apply received non-finite raw features; "
                                 "fill unparseable rows first (fill_raw)")
        return ((A - self.mean) / self.std).astype(np.float32)

    def assert_matches_config(self, cfg: Mapping[str, Any] | None) -> None:
        """Reject a cached/fitted transform that does not implement ``cfg``."""
        want = validate_scaler_config(cfg) if cfg is not None else None
        got = {"method": self.method, "denominator_floor": self.denominator_floor}
        # A null config means "no policy stated" == legacy H0; the fitted method
        # must itself be legacy in that case.
        want_got = ({"method": LEGACY_METHOD, "denominator_floor": None}
                    if want is None else
                    {"method": want["method"], "denominator_floor": want["denominator_floor"]})
        if got != want_got:
            raise InterfaceError(f"fitted scaler policy {got} != config policy {want_got}")
        if want is not None and want.get("ddof", 0) != 0:
            raise InterfaceError("ddof mismatch")

    def to_dict(self) -> dict[str, Any]:
        import numpy as np
        d = {
            "kind": "feature_standardize_fit_only",
            "fit_partition": self.fit_partition,
            "fit_row_indices_sha256": self.fit_row_indices_sha256,
            "fit_n_rows": self.fit_n_rows,
            "epsilon": self.epsilon,
            "mean": np.asarray(self.mean).tolist(),
            "std": np.asarray(self.std).tolist(),
        }
        if self.method != LEGACY_METHOD:
            d.update({
                "method": self.method,
                "denominator_floor": self.denominator_floor,
                "scaler_config_sha256": self.scaler_config_sha256,
                "denominators_pre_floor": np.asarray(self.denominators_pre_floor).tolist(),
            })
        return d

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "FeatureScaler":
        import numpy as np
        if d.get("kind") != "feature_standardize_fit_only":
            raise InterfaceError("unknown scaler kind")
        method = d.get("method", LEGACY_METHOD)
        if method not in (LEGACY_METHOD, FLOOR_METHOD):
            raise InterfaceError(f"unknown scaler method in payload: {method!r}")
        if method == FLOOR_METHOD:
            for k in ("denominator_floor", "scaler_config_sha256", "denominators_pre_floor"):
                if k not in d:
                    raise InterfaceError(f"floor scaler payload missing '{k}'")
        result = FeatureScaler(
            mean=np.asarray(d["mean"], dtype=np.float32),
            std=np.asarray(d["std"], dtype=np.float32),
            fit_partition=d["fit_partition"],
            fit_row_indices_sha256=d["fit_row_indices_sha256"],
            fit_n_rows=int(d["fit_n_rows"]),
            epsilon=float(d["epsilon"]),
            method=method,
            denominator_floor=(None if method == LEGACY_METHOD
                               else float(d["denominator_floor"])),
            scaler_config_sha256=(None if method == LEGACY_METHOD
                                  else str(d["scaler_config_sha256"])),
            denominators_pre_floor=(None if method == LEGACY_METHOD
                                    else np.asarray(d["denominators_pre_floor"], dtype=np.float32)),
        )

        if (result.mean.ndim != 1 or result.std.shape != result.mean.shape
                or not np.isfinite(result.mean).all() or not np.isfinite(result.std).all()
                or not (result.std > 0).all() or result.epsilon != 1e-8
                or result.fit_partition != "official_train.fit_subset"
                or result.fit_n_rows <= 0):
            raise InterfaceError("invalid saved feature scaler statistics")
        if method == FLOOR_METHOD:
            cfg = validate_scaler_config({"method": method,
                                          "denominator_floor": result.denominator_floor})
            expected_sha = sha256_hex(canonical_json_bytes(cfg))
            pre = result.denominators_pre_floor
            if (result.scaler_config_sha256 != expected_sha or pre.shape != result.std.shape
                    or not np.isfinite(pre).all() or not (pre > 0).all()
                    or not np.array_equal(result.std,
                                          np.maximum(pre, np.float32(result.denominator_floor)))):
                raise InterfaceError("saved floor scaler policy/denominator mismatch")
        return result


def fill_raw(X):
    """Accept already filled, validated raw cache; never hide corrupt finite rows."""
    import numpy as np
    A = np.asarray(X, dtype=np.float32)
    if not np.isfinite(A).all():
        raise InterfaceError("raw cache must be finite; parse-mask fill occurs at encoding")
    return A


def fit_feature_scaler(X_filled_fit, fit_row_indices: Sequence[int],
                       scaler_config: Mapping[str, Any] | None = None) -> FeatureScaler:
    """Standardize columns using ONLY the given fit-partition rows of official train.

    ``scaler_config=None`` reproduces the legacy denominator bit-for-bit. The
    floor policy first computes the legacy denominator d0 (constant dims -> 1)
    and then applies d = max(d0, floor); nothing else changes.
    """
    import numpy as np
    cfg = validate_scaler_config(scaler_config)
    if cfg is None:
        cfg = validate_scaler_config({"method": LEGACY_METHOD})
    A = np.asarray(X_filled_fit, dtype=np.float32)
    if A.ndim != 2 or A.shape[0] == 0:
        raise InterfaceError("fit_feature_scaler needs a non-empty 2-D fit matrix")
    if len(fit_row_indices) != len(A) or len(set(fit_row_indices)) != len(A):
        raise InterfaceError("fit matrix rows must match distinct fit row indices")
    if not np.isfinite(A).all():
        raise InterfaceError("fit matrix has non-finite values; fill before fitting")
    mu = A.mean(axis=0)
    sd = A.std(axis=0)
    eps = 1e-8
    d0 = legacy_denominator(sd, eps, 1.0).astype(np.float32)
    if cfg["method"] == LEGACY_METHOD:
        denom = d0
        floor = None
    else:
        floor = np.float32(cfg["denominator_floor"])
        denom = np.maximum(d0, floor).astype(np.float32)
    idx_sha = sha256_hex(canonical_json_bytes([int(i) for i in sorted(fit_row_indices)]))
    cfg_sha = sha256_hex(canonical_json_bytes(cfg)) if cfg["method"] != LEGACY_METHOD else None
    return FeatureScaler(
        mean=mu.astype(np.float32), std=denom.astype(np.float32),
        fit_partition="official_train.fit_subset",
        fit_row_indices_sha256=idx_sha,
        fit_n_rows=A.shape[0], epsilon=eps,
        method=cfg["method"], denominator_floor=cfg["denominator_floor"],
        scaler_config_sha256=cfg_sha,
        denominators_pre_floor=(None if cfg["method"] == LEGACY_METHOD else d0),
    )


@dataclass
class TargetScaler:
    """Regression-target standardization fitted on the fit partition only."""

    mean: float
    std: float

    def transform(self, y):
        import numpy as np
        return (np.asarray(y, dtype=np.float64) - self.mean) / self.std

    def transform_f32(self, y):
        """float32 view for feeding torch training space (loss/MSE in float32)."""
        import numpy as np
        return self.transform(y).astype(np.float32)

    def inverse(self, z):
        import numpy as np
        return np.asarray(z, dtype=np.float64) * self.std + self.mean

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "target_standardize_fit_only", "mean": float(self.mean),
                "std": float(self.std)}

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "TargetScaler":
        if d.get("kind") != "target_standardize_fit_only":
            raise InterfaceError("unknown target scaler kind")
        mean, std = float(d["mean"]), float(d["std"])
        import math
        if not math.isfinite(mean) or not math.isfinite(std) or std <= 0:
            raise InterfaceError("invalid target std")
        return TargetScaler(mean=mean, std=std)


def fit_target_scaler(y_fit) -> TargetScaler:
    import numpy as np
    y = np.asarray(y_fit, dtype=np.float64)
    if y.size == 0 or not np.isfinite(y).all():
        raise InterfaceError("fit targets must be non-empty and finite")
    std = float(y.std())
    return TargetScaler(mean=float(y.mean()), std=(std if std > 0 else 1.0))
