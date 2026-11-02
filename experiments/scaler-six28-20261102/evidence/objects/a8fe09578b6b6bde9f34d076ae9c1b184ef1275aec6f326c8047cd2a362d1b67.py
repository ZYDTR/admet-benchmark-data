"""Explicit legacy(v1) -> representation(v2) raw-cache migration evidence.

Changing the scaler implementation changes cache.py/heads.py module hashes, and
the legacy v1 contract embedded those hashes in the raw representation key. That
coupling must not be resolved by deleting hash checks or faking environment
versions. This module proves equivalence per (task, split):

  * live input CSV sha256 == v1 contract source_csv_sha256
  * full ordered row identity (Drug_ID, Drug) == v1 row_identity_sha256
  * n_rows / feature_dim / fill_value match
  * encoder checkpoint sha256 == v1 encoder_checkpoint_sha256
  * current encoder.py module sha256 == v1 implementation_sha256['encoder.py']
    (the ONLY module hash that is representation identity; a changed encoder
    invalidates reuse and requires separately authorized re-encoding)
  * array/mask/metadata bytes match the controller-anchored manifest, then
    array/mask file digests and content digests are internally consistent
  * generation environment recorded verbatim from the v1 meta; consumption
    environment snapshot recorded alongside — differences are reported, never
    overwritten onto the original metadata.

The migration verdict is written to an independent evidence file; the original
meta.json is never modified.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .cache import cache_paths, current_environment
from .common import (CHEMELEON_SHA256, FEATURE_DIM, GLOBAL_FILL_VALUE,
                     InterfaceError, array_digest, row_identity_sha256,
                     sha256_file, write_json)


def verify_legacy_migration(cache_root: Path, task: str, split: str,
                            rows: Sequence[Mapping[str, str]], source_sha256: str,
                            evidence_path: Path | None = None, *, cache_trust=None) -> dict[str, Any]:
    """Return an evidence record or raise InterfaceError; never mutate inputs."""
    import numpy as np

    cache_root = Path(cache_root)
    if cache_trust is None:
        raise InterfaceError("legacy cache requires a controller-anchored trusted manifest")
    anchor_sha = cache_trust.verify(cache_root, task, split)
    arr_p, mask_p, meta_p = cache_paths(cache_root, task, split)
    for p in (arr_p, mask_p, meta_p):
        if not p.is_file():
            raise InterfaceError(f"migration: cache missing: {p}")
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    c = meta.get("contract", {})
    if c.get("version") != 1:
        raise InterfaceError("migration: not a legacy v1 cache entry")

    checks: list[tuple[str, bool]] = []

    def chk(name: str, cond: bool):
        checks.append((name, bool(cond)))
        return cond

    chk("source_csv_sha256", c.get("source_csv_sha256") == source_sha256)
    chk("row_identity", c.get("row_identity_sha256") == row_identity_sha256(rows))
    chk("n_rows", c.get("n_rows") == len(rows))
    chk("feature_dim", c.get("feature_dim") == FEATURE_DIM)
    chk("fill_value", c.get("fill_value") == GLOBAL_FILL_VALUE)
    chk("task_split", c.get("task") == task and c.get("split") == split)
    chk("encoder_checkpoint", c.get("encoder_checkpoint_sha256") == CHEMELEON_SHA256)

    cur_env = current_environment()
    gen_impl = c.get("implementation_sha256", {})
    chk("encoder_module_sha256",
        gen_impl.get("encoder.py") == cur_env["implementation_sha256"].get("encoder.py"))

    chk("file_digest_arr", meta["files"]["arr"] == sha256_file(arr_p))
    chk("file_digest_mask", meta["files"]["mask"] == sha256_file(mask_p))
    X = np.load(arr_p, allow_pickle=False)
    ok = np.load(mask_p, allow_pickle=False)
    chk("array_shape_dtype",
        X.shape == (len(rows), FEATURE_DIM) and str(X.dtype) == "float32")
    chk("mask_shape_dtype", ok.shape == (len(rows),) and ok.dtype == np.bool_)
    chk("array_content_digest",
        array_digest(X)["sha256"] == meta["identity"]["features"]["sha256"])
    chk("mask_content_digest",
        array_digest(ok)["sha256"] == meta["identity"]["parse_mask"]["sha256"])
    chk("finiteness", bool(np.isfinite(X).all()))
    chk("zero_fill_consistency",
        int(ok.sum()) == meta["identity"]["parsed_true_count"]
        and list(np.nonzero(~ok)[0]) == meta["identity"]["unparsed_row_indices"]
        and bool((X[~ok] == GLOBAL_FILL_VALUE).all()))

    failed = [name for name, passed in checks if not passed]
    record = {
        "format": "admet_breadth_cache_migration_v1_to_v2",
        "trusted_input_manifest_sha256": anchor_sha,
        "task": task, "split": split,
        "legacy_contract": c,
        "representation_identity": {
            "encoder_checkpoint_sha256": c.get("encoder_checkpoint_sha256"),
            "encoder_module_sha256": gen_impl.get("encoder.py"),
            "source_csv_sha256": c.get("source_csv_sha256"),
            "row_identity_sha256": c.get("row_identity_sha256"),
            "features_sha256": meta["identity"]["features"]["sha256"],
            "mask_sha256": meta["identity"]["parse_mask"]["sha256"],
        },
        "generation_environment": {"packages": c.get("packages", {}),
                                   "implementation_sha256": gen_impl},
        "consumption_environment": cur_env,
        "checks": dict(checks),
        "ok": not failed,
        "failed_checks": failed,
    }
    if evidence_path is not None:
        write_json(Path(evidence_path), record)
    if failed:
        raise InterfaceError(
            f"legacy->v2 migration rejected for {task}/{split}: {failed}")
    return record


def rewrite_contract_to_v2(legacy_meta: Mapping[str, Any], task: str, split: str,
                           rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    """Derive the v2 representation contract from a verified v1 record.

    Pure function used by importers; does not touch disk. Callers must only use
    this AFTER verify_legacy_migration succeeded for the same identities.
    """
    c = legacy_meta["contract"]
    return {
        "version": 2,
        "task": task,
        "split": split,
        "feature_dim": c["feature_dim"],
        "fill_value": c["fill_value"],
        "encoder_checkpoint_sha256": c["encoder_checkpoint_sha256"],
        "encoder_module_sha256": c["implementation_sha256"]["encoder.py"],
        "source_csv_sha256": c["source_csv_sha256"],
        "n_rows": len(rows),
        "row_identity_sha256": row_identity_sha256(rows),
    }
