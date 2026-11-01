"""Content-addressed feature cache bound to input rows, encoder, weights, deps.

Cache layout (all inside a caller-specified ``cache_dir``)::

    <cache_dir>/<split>/<task>/<key>/features.
        npy   (NumPy arrays, real runs)   or
        npyf  (stdlib fallback, prep checks; with a .json sidecar)
    <cache_dir>/<split>/<task>/<key>/manifest.json
    <cache_dir>/<split>/<task>/<key>/failures.json

``key`` is the SHA256 of a canonical JSON manifest built from:

* every raw row used: ``(task, split, row_index, drug_id, smiles)`` in file order
  (so the same molecule with a different index/drug_id is a different key, and a
  reordered/edited CSV changes the key);
* the raw file's SHA256 and row count;
* the encoder id, Chemprop code commit, weight size/MD5/SHA256;
* featurizer configuration string, batch size, feature dim, array format
  (``npy`` vs ``npyf`` so a NumPy-written cache is never read by the stdlib path);
* versions of torch / chemprop / rdkit / numpy.

On reuse the cache is *re-verified*, never trusted on file existence alone:

1. manifest must exist and its key must equal the requested key;
2. full row identity + file digest + encoder/weights/deps must still match;
3. array digest must equal the manifest's recorded digest;
4. array shape/dtype/finiteness checked;
5. persisted ``failures.json`` row set must equal the manifest's failure set, and
   ``features`` ∪ ``failures`` must partition every source row exactly.

Any mismatch raises ``CacheError`` (the caller may rebuild explicitly with
``force=True``); nothing is silently reused or silently overwritten.
"""

import hashlib
import json
import os

import feature_array as fa
from errors import CacheError

CACHE_FORMAT_VERSION = 1
FEATURIZER_CONFIG = "SimpleMoleculeMolGraphFeaturizer(default v2 atom/bond multi-hot)"
ARRAY_FILENAME = "features"


def _json_digest(obj):
    blob = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def build_manifest(table, encoder_meta, deps, batch_size):
    """Build the canonical manifest dict for one (task, split) table."""
    rows = [
        [r["task"], r["split"], r["row_index"], r["drug_id"], r["smiles"]]
        for r in table["rows"]
    ]
    manifest = {
        "cache_format_version": CACHE_FORMAT_VERSION,
        "task": table["task"],
        "split": table["split"],
        "source": {
            "path": os.path.basename(table["path"]),
            "file_sha256": table["sha256"],
            "n_rows": table["n_rows"],
        },
        "rows_sha256": _json_digest(rows),
        "encoder": {
            "id": encoder_meta["id"],
            "code_commit": encoder_meta["code_commit"],
            "featurizer": FEATURIZER_CONFIG,
            "feature_dim": int(encoder_meta["feature_dim"]),
            "hyper_parameters": encoder_meta.get("hyper_parameters"),
        },
        "weights": {
            "size": int(encoder_meta["weights"]["size"]),
            "md5": encoder_meta["weights"]["md5"],
            "sha256": encoder_meta["weights"]["sha256"],
        },
        "deps": dict(sorted(deps.items())),
        "batch_size": int(batch_size),
        "array_format": fa.format_name(),
    }
    manifest["key"] = _json_digest(manifest)
    return manifest


def expected_vs_actual_diff(expected, actual):
    """Return a list of human-readable field mismatches between two manifests."""
    diffs = []

    def walk(a, b, prefix=""):
        if isinstance(a, dict) and isinstance(b, dict):
            for k in sorted(set(a) | set(b)):
                if k not in a:
                    diffs.append(f"{prefix}{k}: missing in requested manifest")
                elif k not in b:
                    diffs.append(f"{prefix}{k}: missing in cached manifest")
                else:
                    walk(a[k], b[k], f"{prefix}{k}.")
        elif a != b:
            diffs.append(f"{prefix[:-1]}: cached={b!r} requested={a!r}")

    walk(expected, actual)
    return diffs


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def cache_entry_dir(cache_dir, task, split, key):
    return os.path.join(cache_dir, split, task, key)


def _array_path(entry):
    ext = fa.format_name()
    return os.path.join(entry, f"{ARRAY_FILENAME}.{ext}")


def save_cache(cache_dir, manifest, features, kept_row_indices, failures):
    """Write features + manifest + failures for one (task, split).

    ``features`` is a ``feature_array.Array``.  Validation happens before any
    write so a bad array never leaves a half-written entry.
    """
    if features.dtype not in ("float32", "float64") and str(features.dtype) != "float32":
        # The legacy FeatureArray reports "float32"; NumPy reports "float32".
        pass
    if len(features.shape) != 2 or features.shape[1] != manifest["encoder"]["feature_dim"]:
        raise CacheError(f"features shape {features.shape} inconsistent with manifest")
    if features.shape[0] != len(kept_row_indices):
        raise CacheError("features rows != kept_row_indices length")
    if not features.all_finite():
        raise CacheError("refusing to save non-finite features")
    n_rows = manifest["source"]["n_rows"]
    fail_idx = [int(f["row_index"]) for f in failures]
    if set(fail_idx) & set(int(i) for i in kept_row_indices):
        raise CacheError("row appears in both features and failures")
    if set(fail_idx) | set(int(i) for i in kept_row_indices) != set(range(n_rows)):
        raise CacheError("features+failures do not cover every source row exactly")

    os.makedirs(cache_entry_dir(cache_dir, manifest["task"], manifest["split"],
                                manifest["key"]), exist_ok=True)
    entry = cache_entry_dir(cache_dir, manifest["task"], manifest["split"], manifest["key"])
    path = _array_path(entry)
    features.save(path)
    manifest = dict(manifest)
    manifest["features_sha256"] = _sha256_file(path)
    manifest["feature_shape"] = list(features.shape)
    manifest["feature_dtype"] = str(features.dtype)
    manifest["kept_row_indices"] = [int(i) for i in kept_row_indices]
    manifest["failures"] = list(failures)
    with open(os.path.join(entry, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2, sort_keys=True)
    with open(os.path.join(entry, "failures.json"), "w", encoding="utf-8") as fh:
        json.dump(failures, fh, ensure_ascii=False, indent=2)
    return entry


def load_cache(cache_dir, expected_manifest, verify=True):
    """Load and re-verify a cache entry for the requested manifest.

    Returns ``(features, manifest)``.  Raises ``CacheError`` on any inconsistency.
    """
    key = expected_manifest["key"]
    entry = cache_entry_dir(cache_dir, expected_manifest["task"], expected_manifest["split"], key)
    mp = os.path.join(entry, "manifest.json")
    if not os.path.isfile(mp):
        raise CacheError(f"cache miss: no manifest at {mp}")
    with open(mp, "r", encoding="utf-8") as fh:
        cached = json.load(fh)
    if cached.get("key") != key:
        raise CacheError(f"cache key mismatch at {mp}: {cached.get('key')} != {key}")
    skip = {"key", "features_sha256", "feature_shape", "feature_dtype",
            "kept_row_indices", "failures"}
    exp_cmp = {k: v for k, v in expected_manifest.items() if k not in skip}
    act_cmp = {k: v for k, v in cached.items() if k not in skip}
    diffs = expected_vs_actual_diff(exp_cmp, act_cmp)
    if diffs:
        raise CacheError("cache identity mismatch: " + "; ".join(diffs))
    path = _array_path(entry)
    if not os.path.isfile(path):
        raise CacheError(f"cache missing {os.path.basename(path)} in {entry}")
    if verify and _sha256_file(path) != cached.get("features_sha256"):
        raise CacheError(f"{os.path.basename(path)} digest mismatch in {entry} (corrupted)")
    feats = fa.Array(None).load(path)
    if str(feats.dtype) != cached.get("feature_dtype"):
        raise CacheError(f"cached array dtype {feats.dtype} != manifest {cached.get('feature_dtype')}")
    if list(feats.shape) != list(cached.get("feature_shape", [])):
        raise CacheError(f"cached array shape {feats.shape} != manifest shape")
    if not feats.all_finite():
        raise CacheError(f"cached array contains non-finite values in {entry}")
    kept = [int(i) for i in cached.get("kept_row_indices", [])]
    if len(kept) != feats.shape[0]:
        raise CacheError("kept_row_indices length != feature rows")
    failures = cached.get("failures", [])
    fail_idx = [int(f["row_index"]) for f in failures]
    if set(fail_idx) & set(kept):
        raise CacheError("row appears in both features and failures")
    all_rows = set(range(expected_manifest["source"]["n_rows"]))
    if set(fail_idx) | set(kept) != all_rows:
        raise CacheError("features+failures do not cover every source row exactly")
    fpath_fail = os.path.join(entry, "failures.json")
    if os.path.isfile(fpath_fail):
        with open(fpath_fail, "r", encoding="utf-8") as fh:
            persisted = json.load(fh)
        if persisted != failures:
            raise CacheError("failures.json disagrees with manifest failures")
    return feats, cached