"""Pure, import-safe training-science helpers for the fixed Caco2 / frozen-CheMeleon run.

This module is the single tested source of split, config-validation, metrics, feature-identity
and RNG-state logic. ``train_remote_v4.py`` imports and calls these functions directly (no test
dupes). It only uses the standard library plus numpy: importing it never starts training, never
touches torch/chemprop/CUDA, and never opens files.

Determinism contract for the group split:
* groups are keyed by the *raw* ``Drug`` string (no canonicalization, no dedup, no row edits);
* group keys are sorted with C-locale byte order (``codepoint`` sort of the raw str);
* permutation comes from a dedicated ``random.Random(seed)`` instance (Mersenne Twister,
  ``random.Random.shuffle`` algorithm documented in ``split_train_stop_groups``), so global
  ``random.*`` state changes cannot influence it;
* seed must differ from the model-init seed usage elsewhere only in the sense that this RNG is
  created and used before any model construction and is never re-seeded afterwards.
"""

from __future__ import annotations

import hashlib
import csv
import json
import math
import random
import zlib
from typing import Any, Iterable, Mapping, Sequence

try:  # numpy is required for numeric checks; fail loudly, do not silently degrade.
    import numpy as np
except ImportError as exc:  # pragma: no cover - environment guard
    raise ImportError("training_science requires numpy in the preparation/host environment") from exc

SCHEMA_VERSION = "admet-progressive-cycle-20261031-v4"


class PreparationError(ValueError):
    """Raised for invalid configuration or invalid grouping inputs."""


# ---------------------------------------------------------------------------
# hashing / serialization helpers (kept here so production and tests share one impl)
# ---------------------------------------------------------------------------

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def float10g(value: float) -> str:
    return format(float(value), ".10g")


# ---------------------------------------------------------------------------
# configuration validation
# ---------------------------------------------------------------------------

_REQUIRED_TOP_KEYS = (
    "run_id", "task", "pretrained_sha256", "head_config", "split_config",
    "preprocessing", "monitor", "training_only_new_head", "inputs",
)
_REQUIRED_HEAD_KEYS = {
    "hidden_dims": list, "dropout": float, "lr": float, "weight_decay": float,
    "batch_size": int, "epochs": int, "patience": int,
    "val_fraction_from_train": float, "seed": int, "optimizer": str,
}
_REQUIRED_SPLIT_KEYS = {"method": str, "seed": int, "validation_fraction": float}
_INPUT_ROLES = ("train", "validation", "test")


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def validate_config(cfg: Any) -> dict:
    """Validate the registered single-run configuration and return it unchanged.

    Any deviation (missing key, wrong type, out-of-range value, non-unique row identity,
    missing train Y column, duplicate input role/path) raises ``PreparationError``. Nothing is
    hardcoded to a previous run's identity beyond what the config itself declares.
    """
    if not isinstance(cfg, dict):
        raise PreparationError(f"config must be an object, got {type(cfg).__name__}")
    missing = [k for k in _REQUIRED_TOP_KEYS if k not in cfg]
    if missing:
        raise PreparationError(f"config missing required keys: {missing}")
    if not isinstance(cfg["run_id"], str) or not cfg["run_id"].strip():
        raise PreparationError("config.run_id must be a non-empty string")
    if not isinstance(cfg["task"], str) or not cfg["task"].strip():
        raise PreparationError("config.task must be a non-empty string")
    digest = cfg["pretrained_sha256"]
    if not (isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)):
        raise PreparationError("config.pretrained_sha256 must be a 64-char lowercase hex digest")
    if cfg["preprocessing"] != "legacy_z_train_fit":
        raise PreparationError(f"unsupported preprocessing: {cfg['preprocessing']!r}")
    if cfg["monitor"] != "internal_validation_standardized_mse":
        raise PreparationError(f"unsupported monitor: {cfg['monitor']!r}")
    if cfg["training_only_new_head"] is not True:
        raise PreparationError("training_only_new_head must be true for this registered run")

    hc = cfg["head_config"]
    if not isinstance(hc, dict):
        raise PreparationError("head_config must be an object")
    extra = sorted(set(hc) - set(_REQUIRED_HEAD_KEYS))
    if extra:
        raise PreparationError(f"unexpected head_config keys: {extra}")
    for key, typ in _REQUIRED_HEAD_KEYS.items():
        if key not in hc:
            raise PreparationError(f"head_config missing '{key}'")
        val = hc[key]
        if typ is int and (not isinstance(val, int) or isinstance(val, bool)):
            raise PreparationError(f"head_config.{key} must be an int, got {val!r}")
        if typ is float and not _is_number(val):
            raise PreparationError(f"head_config.{key} must be a finite number, got {val!r}")
        if typ is list and not isinstance(val, list):
            raise PreparationError(f"head_config.{key} must be a list, got {val!r}")
        if typ is str and not isinstance(val, str):
            raise PreparationError(f"head_config.{key} must be a string, got {val!r}")
    if hc["optimizer"] != "AdamW":
        raise PreparationError("only the registered AdamW optimizer is admitted")
    hidden = hc["hidden_dims"]
    if (not hidden or not all(isinstance(w, int) and not isinstance(w, bool) and w > 0 for w in hidden)
            or len(hidden) != 1):
        raise PreparationError(f"head_config.hidden_dims must be a single positive int layer, got {hidden!r}")
    if hc["lr"] <= 0:
        raise PreparationError("head_config.lr must be > 0")
    if hc["weight_decay"] < 0:
        raise PreparationError("head_config.weight_decay must be >= 0")
    if not 0 <= hc["dropout"] < 1:
        raise PreparationError("head_config.dropout must be in [0, 1)")
    if hc["batch_size"] <= 0 or hc["epochs"] <= 0 or hc["patience"] <= 0:
        raise PreparationError("batch_size, epochs and patience must be positive ints")
    if hc["seed"] < 0:
        raise PreparationError("head_config.seed must be a non-negative int")

    sc = cfg["split_config"]
    if not isinstance(sc, dict):
        raise PreparationError("split_config must be an object")
    extra = sorted(set(sc) - set(_REQUIRED_SPLIT_KEYS))
    if extra:
        raise PreparationError(f"unexpected split_config keys: {extra}")
    for key, typ in _REQUIRED_SPLIT_KEYS.items():
        if key not in sc:
            raise PreparationError(f"split_config missing '{key}'")
        if typ is int and (not isinstance(sc[key], int) or isinstance(sc[key], bool)):
            raise PreparationError(f"split_config.{key} must be an int")
        if typ is float and not _is_number(sc[key]):
            raise PreparationError(f"split_config.{key} must be a finite number")
        if typ is str and not isinstance(sc[key], str):
            raise PreparationError(f"split_config.{key} must be a string")
    if sc["method"] != "raw_smiles_group_shuffle":
        raise PreparationError(f"unsupported split method: {sc['method']!r}")
    if sc["seed"] < 0:
        raise PreparationError("split_config.seed must be a non-negative int")
    if not 0 < sc["validation_fraction"] < 1:
        raise PreparationError("split_config.validation_fraction must be in (0, 1)")
    if abs(sc["validation_fraction"] - hc["val_fraction_from_train"]) > 1e-12:
        raise PreparationError("split_config.validation_fraction and head_config.val_fraction_from_train disagree")

    inputs = cfg["inputs"]
    if not isinstance(inputs, list) or len(inputs) != 3:
        raise PreparationError("config.inputs must list exactly train/validation/test")
    roles = [i.get("role") for i in inputs if isinstance(i, dict)]
    if sorted(map(str, roles)) != sorted(_INPUT_ROLES):
        raise PreparationError(f"input roles must be exactly {list(_INPUT_ROLES)}, got {roles}")
    paths = [i.get("path") for i in inputs]
    if len(set(map(str, paths))) != len(paths):
        raise PreparationError("input paths must be unique")
    for item in inputs:
        if not isinstance(item, dict):
            raise PreparationError("each input entry must be an object")
        for key in ("role", "task", "sha256", "rows", "path"):
            if key not in item:
                raise PreparationError(f"input entry missing '{key}': {item}")
        if not isinstance(item["task"], str) or not item["task"].strip():
            raise PreparationError("input task must be a non-empty string")
        if item["task"] != cfg["task"]:
            raise PreparationError("input task differs from registered task")
        d = item["sha256"]
        if not (isinstance(d, str) and len(d) == 64 and all(c in "0123456789abcdef" for c in d)):
            raise PreparationError(f"input sha256 must be 64-char lowercase hex: {item['path']}")
        if not isinstance(item["rows"], int) or isinstance(item["rows"], bool) or item["rows"] <= 0:
            raise PreparationError(f"input rows must be a positive int: {item['path']}")
        if not isinstance(item["path"], str) or not item["path"].strip():
            raise PreparationError("input path must be a non-empty string")
    return cfg


# ---------------------------------------------------------------------------
# row loading and identity checks
# ---------------------------------------------------------------------------

def check_rows_identity(rows: Sequence[Mapping[str, str]], *, require_y: bool, label: str,
                        allow_duplicate_drug_id: bool = True) -> dict[str, Any]:
    """Validate row identity fields. Row *position* is the authoritative line identity; Drug_ID is
    an attribute that legitimately repeats or is blank in every split. Never replace rows by ID.
    Missing fields fail; raw string contents stay unchanged and parsing is the encoder's job.
    When require_y, every Y must parse to a finite float; blind rows cannot contain Y.
    Returns an audit record of duplicates and multi-line raw Drug groups.
    """
    if len(rows) == 0:
        raise PreparationError(f"{label}: zero rows")
    ids: list[str] = []
    for pos, row in enumerate(rows):
        rid = row.get("Drug_ID")
        smi = row.get("Drug")
        if not isinstance(rid, str):
            raise PreparationError(f"{label}: missing/non-string Drug_ID at row index {pos}")
        if not isinstance(smi, str):
            raise PreparationError(f"{label}: missing/non-string Drug at row index {pos}")
        if not require_y and "Y" in row:
            raise PreparationError(f"{label}: blind input must not contain Y")
        ids.append(rid)
        if require_y:
            y = row.get("Y")
            try:
                v = float(y)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                raise PreparationError(f"{label}: invalid Y at row index {pos}: {y!r}") from None
            if not math.isfinite(v):
                raise PreparationError(f"{label}: non-finite Y at row index {pos}: {y!r}")
    counts = {i: ids.count(i) for i in set(ids)}
    dupes = sorted(k for k, v in counts.items() if v > 1)
    if allow_duplicate_drug_id is not True:
        raise PreparationError("this contract requires empty and repeated IDs in every split")
    drug_counts = build_drug_groups(rows)
    return {
        "rows": len(rows),
        "duplicate_drug_ids": dupes,
        "blank_drug_id_rows": [i for i, rid in enumerate(ids) if rid == ""],
        "multi_row_raw_drugs": sorted(k for k, v in drug_counts.items() if len(v) > 1),
    }


# ---------------------------------------------------------------------------
# deterministic group split
# ---------------------------------------------------------------------------

SHUFFLE_ALGORITHM = "CPython random.Random(seed).shuffle(seq) (Fisher-Yates via _randbelow) over codepoint-sorted group keys"


def load_input_tables(cfg, root, safe, file_sha):
    """The production CSV boundary; preserves every original row and permits blank/repeated IDs."""
    rows, hashes, audits = {}, {}, {}
    for item in cfg["inputs"]:
        path = safe(root / item["path"], True)
        digest = file_sha(path)
        if digest != item["sha256"]:
            raise PreparationError("input hash mismatch: " + item["role"])
        split = {"train": "train", "validation": "valid", "test": "test"}[item["role"]]
        expected = {"Drug_ID", "Drug", "Y"} if split == "train" else {"Drug_ID", "Drug"}
        with path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or len(reader.fieldnames) != len(expected) or set(reader.fieldnames) != expected:
                raise PreparationError("incorrect input columns: " + split)
            table = list(reader)
        if len(table) != item["rows"] or any(set(row) != expected for row in table):
            raise PreparationError("incorrect input row count or malformed row: " + split)
        audits[split] = check_rows_identity(table, require_y=(split == "train"), label=split)
        rows[split] = table
        hashes[item["role"]] = digest
    return rows, hashes, audits


def build_drug_groups(rows: Sequence[Mapping[str, str]]) -> dict[str, list[int]]:
    """Map each raw Drug string to its ordered original row indices. No dedup/canonicalization."""
    groups: dict[str, list[int]] = {}
    for idx, row in enumerate(rows):
        groups.setdefault(row["Drug"], []).append(idx)
    return groups


def assign_internal_stop(total_rows: int, validation_fraction: float) -> int:
    """Target stop-group size: round(fraction * total), at least 1, strictly below total."""
    if total_rows <= 0:
        raise PreparationError("total_rows must be positive")
    if not 0 < validation_fraction < 1:
        raise PreparationError("validation_fraction must be in (0, 1)")
    target = max(1, int(round(total_rows * validation_fraction)))
    if target >= total_rows:
        raise PreparationError("stop selection would leave the fit set empty")
    return target


def select_stop_groups(group_order: Sequence[str], group_sizes: Mapping[str, int],
                       total_rows: int, target_rows: int) -> list[str]:
    """Walk the shuffled group order, taking whole groups until the target row count is reached.

    Stops as soon as cumulative rows >= target, but never consumes every group (fit stays
    non-empty). Deterministic given (group_order, group_sizes, total_rows, target_rows).
    """
    if not group_order:
        raise PreparationError("no groups to select from")
    if len(set(group_order)) != len(group_order):
        raise PreparationError("group_order contains duplicate keys")
    if total(group_sizes, group_order) != total_rows:
        raise PreparationError("group sizes do not sum to total_rows")
    stop: list[str] = []
    taken = 0
    for key in group_order:
        if taken >= target_rows and stop:
            break
        if len(stop) + 1 == len(group_order):  # last group must stay in fit
            break
        stop.append(key)
        taken += int(group_sizes[key])
    if not stop or len(stop) == len(group_order):
        raise PreparationError("could not select a non-empty, non-exhaustive stop set")
    return stop


def total(group_sizes: Mapping[str, int], keys: Iterable[str]) -> int:
    return sum(int(group_sizes[k]) for k in keys)


def split_train_stop_groups(rows: Sequence[Mapping[str, str]], seed: int,
                            validation_fraction: float) -> dict[str, Any]:
    """Deterministic raw-SMILES-group split of the official train table into fit / internal-stop.

    Returns a JSON-serializable record with every original row index, source hashes, group audit
    and the exact algorithm description. Uses only a local random.Random instance.
    """
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise PreparationError(f"split seed must be a non-negative int, got {seed!r}")
    audit = check_rows_identity(rows, require_y=True, label="train", allow_duplicate_drug_id=True)
    groups = build_drug_groups(rows)
    ordered_keys = sorted(groups)  # C-locale-equivalent codepoint sort of raw strings
    sizes = {k: len(groups[k]) for k in ordered_keys}
    n = len(rows)
    target = assign_internal_stop(n, validation_fraction)
    rng = random.Random(seed)
    shuffled = list(ordered_keys)
    rng.shuffle(shuffled)
    stop_keys = select_stop_groups(shuffled, sizes, n, target)
    stop_set = set(stop_keys)
    fit_indices: list[int] = []
    stop_indices: list[int] = []
    for key, idxs in groups.items():
        (stop_indices if key in stop_set else fit_indices).extend(idxs)
    fit_indices.sort()
    stop_indices.sort()
    if not fit_indices or not stop_indices:
        raise PreparationError("split produced an empty fit or stop set")
    overlap = set(fit_indices) & set(stop_indices)
    if overlap:
        raise PreparationError(f"fit/stop overlap: {sorted(overlap)[:10]}")
    if sorted(fit_indices + stop_indices) != list(range(n)):
        raise PreparationError("fit+stop does not cover every original row exactly once")
    cross = {rows[i]["Drug"] for i in fit_indices} & {rows[i]["Drug"] for i in stop_indices}
    if cross:
        raise PreparationError(f"raw Drug strings cross fit/stop boundary: {sorted(cross)[:5]}")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "method": "raw_smiles_group_shuffle",
        "seed": seed,
        "validation_fraction": validation_fraction,
        "shuffle_algorithm": SHUFFLE_ALGORITHM,
        "python_random_engine": "random.Random (Mersenne Twister MT19937)",
        "total_rows": n,
        "distinct_raw_drugs": len(groups),
        "duplicate_raw_drug_groups": sorted((k for k in ordered_keys if sizes[k] > 1)),
        "drug_id_audit": {
            "allow_duplicate_drug_id": True,
            "duplicate_drug_ids": audit["duplicate_drug_ids"],
            "note": "row position is the authoritative line identity; Drug_ID repeats legitimately in this dataset",
        },
        "target_stop_rows": target,
        "stop_group_count": len(stop_keys),
        "fit_rows": len(fit_indices),
        "stop_rows": len(stop_indices),
        "stop_drug_keys": stop_keys,
        "fit_row_indices": fit_indices,
        "stop_row_indices": stop_indices,
        "groups": {k: groups[k] for k in ordered_keys},
    }
    payload["split_record_sha256"] = sha256_hex(canonical_json_bytes(payload))
    return payload


# ---------------------------------------------------------------------------
# feature identity (content-bound, not existence/count-bound)
# ---------------------------------------------------------------------------

def array_digest(arr: np.ndarray) -> dict[str, Any]:
    a = np.asarray(arr)
    raw = a.tobytes(order="C")
    return {
        "shape": list(a.shape),
        "dtype": str(a.dtype),
        "c_contiguous": bool(a.flags["C_CONTIGUOUS"]),
        "bytes": len(raw),
        "sha256": sha256_hex(raw),
        "crc32": format(zlib.crc32(raw) & 0xFFFFFFFF, "08x"),
        "nan_count": int(np.isnan(a).sum()) if np.issubdtype(a.dtype, np.floating) else 0,
        "inf_count": int(np.isinf(a).sum()) if np.issubdtype(a.dtype, np.floating) else 0,
    }


def feature_identity(features: np.ndarray, parse_mask: np.ndarray, rows: Sequence[Mapping[str, str]],
                     encoder_meta: Mapping[str, Any], expected_dim: int,
                     source_sha256: str | None = None) -> dict[str, Any]:
    """Bind an extracted feature matrix to input content + per-row identity + encoder version."""
    f = np.asarray(features)
    m = np.asarray(parse_mask)
    n = len(rows)
    if f.ndim != 2 or f.shape[0] != n or f.shape[1] != int(expected_dim):
        raise PreparationError(f"feature shape {f.shape} incompatible with {n} rows x dim {expected_dim}")
    if m.shape != (n,):
        raise PreparationError(f"parse mask shape {m.shape} != ({n},)")
    if str(f.dtype) != "float32":
        raise PreparationError(f"features dtype must be float32, got {f.dtype}")
    if m.dtype != np.bool_:
        raise PreparationError(f"parse mask dtype must be bool, got {m.dtype}")
    id_digest = sha256_hex(canonical_json_bytes([[r["Drug_ID"], r["Drug"]] for r in rows]))
    payload = {
        "encoder": dict(encoder_meta),
        "input_rows": n,
        "input_identity_sha256": id_digest,
        "input_csv_sha256": source_sha256,
        "features": array_digest(f),
        "parse_mask": array_digest(m),
        "parsed_true_count": int(m.sum()),
    }
    payload["identity_sha256"] = sha256_hex(canonical_json_bytes(payload))
    return payload


# ---------------------------------------------------------------------------
# evaluation metrics (fit/stop per-round logging, train predictions export)
# ---------------------------------------------------------------------------

def standardized_mse(pred: np.ndarray, target_std: np.ndarray) -> float:
    p = np.asarray(pred, dtype=np.float64).reshape(-1)
    t = np.asarray(target_std, dtype=np.float64).reshape(-1)
    if p.shape != t.shape or p.size == 0:
        raise PreparationError("standardized_mse needs matching non-empty 1-D arrays")
    if not (np.isfinite(p).all() and np.isfinite(t).all()):
        raise PreparationError("standardized_mse received non-finite values")
    return float(np.mean((p - t) ** 2))


def scale_metrics(pred_orig: np.ndarray, y_orig: np.ndarray) -> dict[str, float]:
    p = np.asarray(pred_orig, dtype=np.float64).reshape(-1)
    t = np.asarray(y_orig, dtype=np.float64).reshape(-1)
    if p.shape != t.shape or p.size == 0:
        raise PreparationError("scale metrics need matching non-empty 1-D arrays")
    if not (np.isfinite(p).all() and np.isfinite(t).all()):
        raise PreparationError("scale metrics received non-finite values")
    d = p - t
    return {"mae": float(np.mean(np.abs(d))), "mse": float(np.mean(d * d))}


# ---------------------------------------------------------------------------
# safe CPU-side RNG state snapshots (weights_only-loadable primitives only)
# ---------------------------------------------------------------------------

def _as_plain(x: Any) -> Any:
    if isinstance(x, tuple):
        return tuple(_as_plain(i) for i in x)
    if isinstance(x, list):
        return [_as_plain(i) for i in x]
    if isinstance(x, dict):
        return {str(k): _as_plain(v) for k, v in x.items()}
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    return x


def capture_cpu_rng_state(seed: int) -> dict[str, Any]:
    """Snapshot Python/numpy CPU RNG states as plain containers (safe for weights_only load)."""
    bitgen, arr, pos, has_gauss, cached = np.random.get_state()
    payload = {"algorithm": "python random.getstate + numpy legacy RandomState.get_state",
               "seed_declared_for_replay": int(seed),
               "python_state": _as_plain(random.getstate()),
               "numpy_state": {"bit_generator": str(bitgen), "array": [int(x) for x in arr.tolist()],
                                "pos": int(pos), "has_gauss": int(has_gauss),
                                "cached_gaussian": float(cached)}}
    payload["state_sha256"] = sha256_hex(canonical_json_bytes(payload))
    return payload


def restore_cpu_rng_state(state: Mapping[str, Any]) -> None:
    random.setstate(tuple(state["python_state"]))
    ns = state["numpy_state"]
    if ns["bit_generator"] != "MT19937":
        raise PreparationError(f"unsupported numpy bit generator: {ns['bit_generator']}")
    arr = np.asarray(ns["array"], dtype=np.uint32)
    if arr.shape != (624,):
        raise PreparationError(f"unexpected MT19937 state size: {arr.shape}")
    np.random.set_state(("MT19937", arr, int(ns["pos"]), int(ns["has_gauss"]), float(ns["cached_gaussian"])))


def optimizer_payload(opt_state: Mapping[str, Any]) -> dict[str, Any]:
    """Clone the full actual optimizer state, retaining Tensor values and integer keys."""
    if set(opt_state) != {"state", "param_groups"} or not isinstance(opt_state["param_groups"], list):
        raise PreparationError("invalid optimizer state_dict structure")
    return cpu_tensor_tree(dict(opt_state))


def cpu_tensor_tree(value):
    import torch
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, dict):
        if not all(type(k) in (str, int) for k in value):
            raise PreparationError("unsupported state key")
        return {k: cpu_tensor_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [cpu_tensor_tree(v) for v in value]
    if isinstance(value, tuple):
        return tuple(cpu_tensor_tree(v) for v in value)
    if value is None or type(value) in (str, int, bool, float):
        if type(value) is float and not math.isfinite(value):
            raise PreparationError("nonfinite state scalar")
        return value
    raise PreparationError("unsupported state value: " + type(value).__name__)


def state_equal(a, b):
    import torch
    if isinstance(a, torch.Tensor):
        return (isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape
                and torch.equal(a.detach().cpu(), b.detach().cpu()))
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(state_equal(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(state_equal(x, y) for x, y in zip(a, b))
    return a == b


def capture_training_rng(seed, generator):
    import torch
    return {"cpu_rng": capture_cpu_rng_state(seed), "torch_cpu": torch.get_rng_state().clone(),
            "torch_cuda": [x.cpu().clone() for x in torch.cuda.get_rng_state_all()] if torch.cuda.is_available() else [],
            "sampler": generator.get_state().clone(), "sampler_device": str(generator.device)}


def restore_training_rng(state, generator):
    import torch
    count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    if len(state["torch_cuda"]) != count or state["sampler_device"] != str(generator.device):
        raise PreparationError("RNG device identity mismatch")
    restore_cpu_rng_state(state["cpu_rng"])
    torch.set_rng_state(state["torch_cpu"])
    if count:
        torch.cuda.set_rng_state_all(state["torch_cuda"])
    generator.set_state(state["sampler"])


def checkpoint_identity(history, index):
    if type(index) is not int or not 0 <= index < len(history):
        raise PreparationError("invalid checkpoint epoch")
    row = history[index]
    if row["epoch"] != index + 1 or row["steps"] <= 0:
        raise PreparationError("invalid checkpoint step identity")
    return {"epoch": row["epoch"], "steps": row["steps"],
            "monitor_value": row["internal_validation_standardized_mse"],
            "best": min(x["internal_validation_standardized_mse"] for x in history[:index + 1])}
