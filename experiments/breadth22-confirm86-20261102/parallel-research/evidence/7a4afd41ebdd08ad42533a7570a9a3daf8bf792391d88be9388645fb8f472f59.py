"""Mini22 frozen-cache bridge: admit the historical Mini22 ``__split.npy``
partitions (chemprop 2.2.1 / RDKit 2025.9.6 era, encoder code =
input/mini22-encoder.py) into the current TaskPipeline consumption boundary
without re-encoding and without claiming the two encoder implementations are
bit-equivalent.

Trust chain (controller-anchored, never self-generated from content under test):

  1. TASK.json ``cache_source.manifest_sha256`` pins input/MINI22_CACHE_MANIFEST.json
     (the anchor; hashing an untrusted manifest and accepting that same value as
     authority is refused at construction).
  2. That manifest pins the sha256/bytes of all 192 Mini22 cache files; each
     admission re-verifies the four files of the requested partition.
  3. The partition's rows.json is mapped POSITIONALLY onto the live packet CSV
     rows (row_index == position, drug_id == Drug_ID, smiles == Drug). Blank or
     repeated Drug_ID values are preserved, never used as keys.
  4. The original meta.json contract is preserved verbatim as SOURCE provenance
     (original source CSV sha256, mini22 encoder code sha256, chemprop/rdkit
     versions, CheMeleon checkpoint sha256) and is cross-checked against the
     anchored file digests. It is never rewritten to claim the current encoder
     module or the current package set.

Consumption identity (kept separate from the source chain): the live packet CSV
sha256, the row-identity digest over the live rows, and the n_rows seen by the
pipeline. Whether the live CSV bytes equal the historical source bytes is
reported as an observed fact; a byte difference alone never changes data and a
true row misordering is never ignored.

Zero re-encoding: arrays are loaded from the manifest-anchored files, checked
for shape/dtype/finiteness/parse-mask/zero-fill consistency, and handed to the
pipeline unchanged. No encoder is loaded; no forward call is made here.

Import-safe: numpy is imported lazily inside functions; importing this module
performs no I/O beyond stdlib imports.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from admet_breadth.cache import current_environment
from admet_breadth.common import (CHEMELEON_SHA256, FEATURE_DIM, InterfaceError,
                                  array_digest, row_identity_sha256, sha256_file)
from admet_breadth.pipeline import TaskPipeline

MINI22_CACHE_FORMAT = "mini22_frozen_cache_v1"
MINI22_FILE_SUFFIXES = (".npy", ".ok.npy", ".rows.json", ".meta.json")

# The two encoder implementations are different historical artifacts; this
# module records both identities and never asserts equality between them.
MINI22_ENCODER_NOTE = ("Mini22 partitions were produced by the historical "
                       "mini22-encoder.py under chemprop 2.2.1 / RDKit 2025.9.6. "
                       "The current accepted-src encoder.py is a different "
                       "implementation of the same frozen CheMeleon checkpoint. "
                       "No re-encoding was performed and no bit-level equality "
                       "between the two implementations is claimed.")


def mini22_partition_paths(root, task: str, split: str):
    d = Path(root) / task
    return (d / f"__{split}.npy", d / f"__{split}.ok.npy",
            d / f"__{split}.rows.json", d / f"__{split}.meta.json")


class Mini22Trust:
    """Controller-anchored trust over the frozen Mini22 cache manifest."""

    def __init__(self, manifest_path, expected_sha256: str):
        path = Path(manifest_path)
        if not path.is_file():
            raise InterfaceError(f"mini22 manifest missing: {path}")
        actual = sha256_file(path)
        if actual != expected_sha256:
            raise InterfaceError(
                "mini22 trusted manifest digest mismatch: "
                f"{actual} != controller anchor {expected_sha256}")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        entries: dict[str, tuple[str, int]] = {}
        for row in manifest["files"]:
            name = row["path"]
            parts = Path(name).parts
            if len(parts) != 2 or ".." in parts or parts[0] in ("", "."):
                raise InterfaceError(f"invalid mini22 manifest member: {name!r}")
            if name in entries:
                raise InterfaceError(f"duplicate mini22 manifest member: {name!r}")
            entries[name] = (str(row["sha256"]), int(row["bytes"]))
        if not entries:
            raise InterfaceError("trusted mini22 manifest has no entries")
        self.entries: Mapping[str, tuple[str, int]] = MappingProxyType(entries)
        self.manifest_sha256 = expected_sha256
        self.manifest_path = str(path)

    def verify_partition_files(self, root, task: str, split: str) -> dict[str, Any]:
        """Verify the four Mini22 files of one partition against anchored digests."""
        root = Path(root)
        out: dict[str, Any] = {}
        for suffix in MINI22_FILE_SUFFIXES:
            name = f"{task}/__{split}{suffix}"
            if name not in self.entries:
                raise InterfaceError(f"mini22 manifest entry missing: {name}")
            exp_sha, exp_bytes = self.entries[name]
            p = root / name
            if not p.is_file():
                raise InterfaceError(f"mini22 cache file missing: {p}")
            size = p.stat().st_size
            if size != exp_bytes:
                raise InterfaceError(
                    f"mini22 cache size mismatch for {name}: {size} != {exp_bytes}")
            actual = sha256_file(p)
            if actual != exp_sha:
                raise InterfaceError(
                    f"mini22 cache digest mismatch for {name}: {actual} != {exp_sha}")
            out[name] = {"bytes": size, "sha256": actual}
        return out


def validate_partition(X, ok, rows_json: Sequence[Mapping[str, Any]],
                       *, feature_dim: int = FEATURE_DIM) -> dict[str, Any]:
    """Structural contract of one Mini22 partition (pure function, no I/O).

    Row position is authoritative: rows_json[i]['row_index'] must equal i for
    every i, so a reordered or truncated row table is rejected here. parse_ok
    must agree with the boolean mask row-by-row, the array must be finite, and
    unparseable rows must carry the documented zero fill.
    """
    import numpy as np

    n = len(rows_json)
    if n == 0:
        raise InterfaceError("mini22 partition has zero rows")
    X = np.asarray(X)
    ok = np.asarray(ok)
    if X.shape != (n, feature_dim) or str(X.dtype) != "float32":
        raise InterfaceError(
            f"mini22 array shape/dtype invalid: {X.shape} {X.dtype} for n={n}")
    if ok.shape != (n,) or ok.dtype != np.bool_:
        raise InterfaceError(f"mini22 mask shape/dtype invalid: {ok.shape} {ok.dtype}")
    for i, r in enumerate(rows_json):
        if set(r.keys()) != {"row_index", "drug_id", "smiles", "parse_ok"}:
            raise InterfaceError(
                f"mini22 rows.json schema mismatch at position {i}: {sorted(r.keys())}")
        if r["row_index"] != i:
            raise InterfaceError(
                f"mini22 row order mismatch at position {i}: row_index "
                f"{r['row_index']!r} != {i} (row position is authoritative)")
        if not isinstance(r["drug_id"], str) or not isinstance(r["smiles"], str):
            raise InterfaceError(f"mini22 rows.json non-string identity at position {i}")
        if not isinstance(r["parse_ok"], bool):
            raise InterfaceError(f"mini22 rows.json parse_ok not boolean at position {i}")
        if bool(r["parse_ok"]) != bool(ok[i]):
            raise InterfaceError(
                f"mini22 parse_ok/mask disagreement at position {i}: rows.json "
                f"{r['parse_ok']} != mask {bool(ok[i])}")
    if not np.isfinite(X).all():
        raise InterfaceError("mini22 array contains non-finite values")
    unparsed = [int(i) for i in np.nonzero(~ok)[0]]
    if unparsed and not (X[~ok] == 0.0).all():
        raise InterfaceError(
            f"mini22 zero-fill violation on unparseable rows: {unparsed[:10]}")
    return {
        "n_rows": n,
        "parsed_true_count": int(ok.sum()),
        "unparsed_row_indices": unparsed,
        "array_content_digest": array_digest(X),
        "mask_content_digest": array_digest(ok),
    }


def map_rows_to_live(rows_json: Sequence[Mapping[str, Any]],
                     live_rows: Sequence[Mapping[str, str]],
                     task: str, split: str) -> dict[str, Any]:
    """Positional identity mapping of rows.json onto the live packet CSV rows.

    Duplicate or blank Drug_ID values pass (they are attributes, not keys);
    any drug_id/smiles disagreement with the live table is a hard rejection
    naming the exact position.
    """
    if len(rows_json) != len(live_rows):
        raise InterfaceError(
            f"mini22 row count mismatch for {task}/{split}: cache {len(rows_json)} "
            f"!= live csv {len(live_rows)}")
    for i, (r, lr) in enumerate(zip(rows_json, live_rows)):
        if r["drug_id"] != lr["Drug_ID"] or r["smiles"] != lr["Drug"]:
            raise InterfaceError(
                f"mini22 row mapping mismatch at {task}/{split} row {i}: cache "
                f"(drug_id={r['drug_id']!r}, smiles={r['smiles']!r}) != live "
                f"(Drug_ID={lr['Drug_ID']!r}, Drug={lr['Drug']!r})")
    return {
        "mapping": "positional row_index / Drug_ID / Drug exact match",
        "n_rows": len(live_rows),
        "duplicate_or_blank_drug_id_preserved": True,
    }


def verify_meta_contract(meta: Mapping[str, Any], task: str, split: str,
                         anchored_files: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Check the ORIGINAL Mini22 meta contract (provenance; never rewritten).

    The contract's task/split/feature_dim/checkpoint must match the requested
    partition, and its recorded per-file digests must equal the anchored
    (manifest-verified) digests of the same files.
    """
    c = meta.get("contract")
    if not isinstance(c, dict):
        raise InterfaceError("mini22 meta.json has no contract object")
    for key in ("task", "split", "feature_dim", "encoder_sha256",
                "encoder_code_sha256", "source_sha256", "chemprop", "rdkit"):
        if key not in c:
            raise InterfaceError(f"mini22 meta contract missing '{key}'")
    if c["task"] != task or c["split"] != split:
        raise InterfaceError(
            f"mini22 meta contract task/split mismatch: {c['task']}/{c['split']} "
            f"!= requested {task}/{split}")
    if int(c["feature_dim"]) != FEATURE_DIM:
        raise InterfaceError(f"mini22 meta feature_dim invalid: {c['feature_dim']!r}")
    if c["encoder_sha256"] != CHEMELEON_SHA256:
        raise InterfaceError("mini22 meta encoder checkpoint differs from the approved CheMeleon")
    meta_files = meta.get("files")
    if not isinstance(meta_files, dict):
        raise InterfaceError("mini22 meta.json has no files digest record")
    for suffix in (".npy", ".ok.npy", ".rows.json"):
        name = f"{task}/__{split}{suffix}"
        key = f"__{split}{suffix}"
        if key not in meta_files:
            raise InterfaceError(f"mini22 meta files record missing '{key}'")
        if meta_files[key] != anchored_files[name]["sha256"]:
            raise InterfaceError(
                f"mini22 meta file digest disagrees with anchored digest for {name}")
    return dict(c)


def load_mini22_partition(trust: Mini22Trust, root, task: str, split: str,
                          live_rows: Sequence[Mapping[str, str]],
                          live_source_sha256: str) -> tuple[Any, Any, dict[str, Any]]:
    """Full admission chain for one Mini22 partition; returns (X, ok, evidence).

    The evidence record keeps the source chain (anchor + verbatim meta) and the
    consumption identity (live CSV binding) as separate sections.
    """
    import numpy as np

    anchored = trust.verify_partition_files(root, task, split)
    arr_p, ok_p, rows_p, meta_p = mini22_partition_paths(root, task, split)
    X = np.load(arr_p, allow_pickle=False)
    ok = np.load(ok_p, allow_pickle=False)
    rows_json = json.loads(rows_p.read_text(encoding="utf-8"))
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    structural = validate_partition(X, ok, rows_json)
    contract = verify_meta_contract(meta, task, split, anchored)
    mapping = map_rows_to_live(rows_json, live_rows, task, split)
    env = current_environment()
    evidence = {
        "format": MINI22_CACHE_FORMAT,
        "task": task,
        "split": split,
        "trust": {
            "manifest_path": trust.manifest_path,
            "manifest_sha256": trust.manifest_sha256,
            "verified_files": anchored,
        },
        "source_provenance": {
            "meta_contract_verbatim": contract,
            "generation_packages": {"chemprop": contract["chemprop"],
                                    "rdkit": contract["rdkit"]},
            "encoder_identity": {
                "mini22_encoder_code_sha256": contract["encoder_code_sha256"],
                "current_encoder_module_sha256": env["implementation_sha256"].get("encoder.py"),
                "implementations_equal": (contract["encoder_code_sha256"]
                                          == env["implementation_sha256"].get("encoder.py")),
                "note": MINI22_ENCODER_NOTE,
            },
            "original_source_csv_sha256": contract["source_sha256"],
            "reencoded": False,
            "encoder_forward_calls": 0,
        },
        "consumption_identity": {
            "source_csv_sha256": live_source_sha256,
            "csv_bytes_equal_historical_source": (live_source_sha256 == contract["source_sha256"]),
            "row_identity_sha256": row_identity_sha256(live_rows),
            "n_rows": len(live_rows),
            "mapping": mapping,
        },
        "partition": structural,
    }
    return X, ok, evidence


class Mini22TaskPipeline(TaskPipeline):
    """TaskPipeline bound to the Mini22 frozen cache admission chain.

    Subclasses :class:`admet_breadth.pipeline.TaskPipeline` and overrides ONLY
    the cache admission route (``load_cache``): every other production entry
    (configure / make_internal_split / fit_transforms / _scaled / fit_head /
    predict_split / export_test) is the accepted, already-verified interface
    inherited unchanged, and because this is a real subclass the inherited
    entries call back into this override. The legacy raw_*.npy cache route is
    not used here and would correctly report "cache missing" for these 16
    tasks (their only caches are the Mini22 __*.npy partitions).
    """

    def __init__(self, task: str, data_root, work_root, metrics_contract, *,
                 mini22_root, mini22_manifest, mini22_manifest_sha256):
        super().__init__(task, data_root, work_root, metrics_contract)
        self.mini22_root = Path(mini22_root)
        self.mini22_trust = Mini22Trust(mini22_manifest, mini22_manifest_sha256)
        self.mini22_evidence: dict[str, Any] = {}

    def load_cache(self, split: str):
        """Mini22 admission: verify anchor/digests/rows against the LIVE table."""
        if split not in self.rows or not self.rows.get(split):
            raise InterfaceError("pipeline.load() must precede load_cache()")
        X, ok, ev = load_mini22_partition(
            self.mini22_trust, self.mini22_root, self.task, split,
            self.rows[split], self.source_sha[split])
        self.mini22_evidence[split] = ev
        return X, ok
