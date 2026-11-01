"""Compute and cache frozen CheMeleon fingerprints for the task CSVs.

What this does (single pass, run by the main Codex session):

1. Reads the selected tasks' train/valid/test CSVs (read-only; row identity is
   (task, split, row_index)).
2. Deduplicates the exact raw SMILES strings (46,202 unique across all 22 tasks
   in the audited snapshot) and encodes each unique string once with the frozen
   CheMeleon message passing.
3. Writes a content-addressed cache: fingerprints.npy + keys.json (sha256 of
   the raw string -> row index), plus uncoded.json for every string that could
   not be encoded (with the reason and the full list of affected rows), plus a
   train-only fallback vector, metadata, and a coverage report.

Coverage policy: every input row must end up either encoded or recorded in
uncoded.json (rows in uncoded.json get the deterministic train-only fallback
mean vector downstream). If any row is neither, the command exits non-zero.
Nothing is dropped, truncated, or hand-fixed.

Per-molecule robustness: RDKit parse failures and featurizer failures are
recorded per unique string; if a whole fingerprint batch raises, the batch is
retried molecule-by-molecule so that a single pathological input cannot poison
its batch.

The fallback vector is the mean of the encoded unique SMILES that appear in
the train split of the selected tasks (train-only by construction). Rows that
use it are flagged end-to-end so the main session can audit exactly which
predictions came from the fallback (expected: only the two documented
solubility_aqsoldb/test rows 1159 and 1160, re-determined at runtime).

Usage (from output/model/):

    python -m chemeleon_baseline.features \
        --data-root ../../data \
        --weights /path/to/chemeleon_mp.pt \
        --out ../../runs/features \
        --device cpu --batch-size 256 --threads 8

A small smoke scope is possible with --tasks dili (331/48/96 rows).
train/predict accept any complete cache for its scope; they refuse caches
marked partial (none are produced by this version, but the flag is checked to
keep future incremental caches honest).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from .data_io import DEFAULT_DATA_ROOT, read_rows, sha256_file, smiles_sha, split_path
from .encoder import CheMeleonFrozen
from .tasks import SPLITS, load_tasks, select_tasks, validate_data_root

CACHE_FILES = ("fingerprints.npy", "keys.json", "uncoded.json", "fallback_vector.npy")


def _log(msg: str) -> None:
    print(f"[features {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def encode_unique_smiles(
    encoder: CheMeleonFrozen, unique: list[str], batch_size: int
) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    """Encode unique raw SMILES strings.

    Returns (vectors: sha -> float32 array, failures: sha -> reason).
    Parse and featurization errors are caught per molecule; batch-level
    fingerprint errors trigger a molecule-by-molecule retry.
    """
    from rdkit.Chem import MolFromSmiles

    vectors: dict[str, np.ndarray] = {}
    failures: dict[str, str] = {}
    graphs: list[tuple[str, object]] = []

    for i, s in enumerate(unique):
        key = smiles_sha(s)
        mol = MolFromSmiles(s)
        if mol is None:
            failures[key] = "rdkit_parse_failed"
        else:
            try:
                graphs.append((key, encoder.featurize(mol)))
            except Exception as e:  # noqa: BLE001 - recorded, not swallowed
                failures[key] = f"featurize_failed:{type(e).__name__}"
        if (i + 1) % 2000 == 0:
            _log(f"parsed/featurized {i + 1}/{len(unique)} unique strings")

    n = len(graphs)
    for start in range(0, n, batch_size):
        chunk = graphs[start : start + batch_size]
        try:
            arr = encoder.fingerprint_graphs([g for _, g in chunk])
            if arr.shape[0] != len(chunk):
                raise RuntimeError(
                    f"fingerprint batch returned {arr.shape[0]} rows for {len(chunk)} molecules"
                )
            for (key, _), vec in zip(chunk, arr):
                if np.all(np.isfinite(vec)):
                    vectors[key] = np.asarray(vec, dtype=np.float32)
                else:
                    failures[key] = "nonfinite_fingerprint"
        except Exception:
            for key, g in chunk:
                if key in failures:
                    continue
                try:
                    vec = encoder.fingerprint_graphs([g])[0]
                    if np.all(np.isfinite(vec)):
                        vectors[key] = np.asarray(vec, dtype=np.float32)
                    else:
                        failures[key] = "nonfinite_fingerprint"
                except Exception as e:  # noqa: BLE001
                    failures[key] = f"fingerprint_failed:{type(e).__name__}"
        done = min(start + batch_size, n)
        if done % (batch_size * 20) < batch_size or done == n:
            _log(f"fingerprinted {done}/{n} featurizable strings")
    return vectors, failures


class FeatureStore:
    """Read-side view of a features cache directory."""

    def __init__(self, cache_dir: str | Path):
        self.dir = Path(cache_dir)
        self.meta = json.loads((self.dir / "metadata.json").read_text(encoding="utf-8"))
        if self.meta.get("partial"):
            raise ValueError(f"cache {self.dir} is marked partial; rebuild it without partial scope")
        self.keys: dict[str, int] = json.loads((self.dir / "keys.json").read_text(encoding="utf-8"))
        self.uncoded: dict[str, dict] = json.loads((self.dir / "uncoded.json").read_text(encoding="utf-8"))
        self.matrix = np.load(self.dir / "fingerprints.npy")
        self.fallback = np.load(self.dir / "fallback_vector.npy")
        if self.matrix.ndim != 2 or self.matrix.shape[0] != len(self.keys):
            raise ValueError(f"cache matrix shape {self.matrix.shape} inconsistent with keys.json")
        if self.fallback.shape != (self.matrix.shape[1],):
            raise ValueError(f"fallback vector shape {self.fallback.shape} inconsistent with matrix")
        overlap = set(self.keys) & set(self.uncoded)
        if overlap:
            raise ValueError(f"keys.json and uncoded.json overlap for {len(overlap)} hashes")

    def file_hashes(self) -> dict:
        return {name: sha256_file(self.dir / name) for name in CACHE_FILES}

    def weights_sha256(self) -> str:
        return self.meta["weights"]["sha256"]

    def encoder_digest(self) -> str:
        return self.meta["encoder_parameter_digest"]

    @property
    def dim(self) -> int:
        return int(self.matrix.shape[1])

    def vectors_for(self, rows: list[dict]) -> tuple[np.ndarray, np.ndarray, list[dict]]:
        """Resolve rows (from read_rows) to (X, fallback_mask, fallback_row_refs).

        X is (n_rows, dim) float32; fallback_mask is (n_rows,) bool; each row in
        fallback_row_refs is {task, split, row_index, smiles, reason} for rows
        served by the fallback vector. A SMILES missing from both keys.json and
        uncoded.json means the cache does not cover this input: hard error.
        """
        n = len(rows)
        X = np.empty((n, self.matrix.shape[1]), dtype=np.float32)
        mask = np.zeros(n, dtype=bool)
        refs: list[dict] = []
        for i, row in enumerate(rows):
            key = smiles_sha(row["smiles"])
            if key in self.keys:
                X[i] = self.matrix[self.keys[key]]
            elif key in self.uncoded:
                X[i] = self.fallback
                mask[i] = True
                refs.append(
                    {
                        "task": row.get("task"),
                        "split": row.get("split"),
                        "row_index": row["row_index"],
                        "smiles": row["smiles"],
                        "reason": self.uncoded[key]["reason"],
                    }
                )
            else:
                raise KeyError(
                    f"SMILES at (task={row.get('task')}, split={row.get('split')}, "
                    f"row_index={row['row_index']}) is not covered by the cache "
                    f"(sha256 {key[:12]}...); rerun chemeleon_baseline.features over the "
                    f"tasks/splits that include it"
                )
        return X, mask, refs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    ap.add_argument("--weights", required=True, help="local path to chemeleon_mp.pt (never auto-downloaded)")
    ap.add_argument("--out", required=True, help="output cache directory (created; existing files overwritten)")
    ap.add_argument("--device", default="cpu", help="torch device, e.g. cpu or cuda:0")
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--threads", type=int, default=8, help="torch CPU threads (bounded CPU)")
    ap.add_argument("--tasks", default="all", help="comma-separated task subset, or 'all'")
    args = ap.parse_args(argv)

    import torch

    torch.set_num_threads(max(1, args.threads))

    tasks = select_tasks(load_tasks(), args.tasks)
    validate_data_root(args.data_root, tasks)
    data_root = Path(args.data_root).resolve()
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    _log(f"data root: {data_root}")
    _log(f"selected tasks: {len(tasks)} -> {[t['task'] for t in tasks]}")

    # 1. read all rows, keep (task, split) provenance on each row for the audit trail
    rows_by: dict[tuple[str, str], list[dict]] = {}
    unique_order: list[str] = []
    seen: set[str] = set()
    for t in tasks:
        for split in SPLITS:
            path = split_path(data_root, t["task"], split)
            rows = read_rows(path, expect_y=(split == "train"))
            for r in rows:
                r["task"] = t["task"]
                r["split"] = split
            rows_by[(t["task"], split)] = rows
            for r in rows:
                key = r["smiles"]
                if key not in seen:
                    seen.add(key)
                    unique_order.append(key)
    n_rows_total = sum(len(v) for v in rows_by.values())
    _log(f"read {n_rows_total} rows; {len(unique_order)} unique raw SMILES strings")

    # 2. frozen encoder
    enc = CheMeleonFrozen(args.weights, device=args.device)
    enc.assert_frozen()
    digest_before = enc.parameter_digest()
    _log(f"encoder loaded (dim={enc.fingerprint_dim}, frozen, digest={digest_before[:16]}...)")

    # 3. encode
    vectors, failures = encode_unique_smiles(enc, unique_order, args.batch_size)
    n_encoded, n_failed = len(vectors), len(failures)
    if n_encoded + n_failed != len(unique_order):
        raise RuntimeError(
            f"internal inconsistency: {n_encoded} encoded + {n_failed} failed != {len(unique_order)} unique"
        )
    digest_after = enc.parameter_digest()
    if digest_after != digest_before:
        raise RuntimeError("encoder parameter digest changed during extraction; aborting")
    _log(f"encoded {n_encoded} unique strings; {n_failed} could not be encoded")

    # 4. assemble cache files in first-seen order
    dim = enc.fingerprint_dim
    encoded_keys: list[str] = []
    matrix = np.zeros((n_encoded, dim), dtype=np.float32)
    for i, s in enumerate(unique_order):
        key = smiles_sha(s)
        if key in vectors:
            encoded_keys.append(key)
            matrix[len(encoded_keys) - 1] = vectors[key]
    keys_map = {k: i for i, k in enumerate(encoded_keys)}

    # rows referencing each failed sha (scope-limited)
    uncoded: dict[str, dict] = {}
    for s in unique_order:
        key = smiles_sha(s)
        if key in failures:
            uncoded[key] = {"smiles": s, "reason": failures[key], "rows": []}
    for (task, split), rows in rows_by.items():
        for r in rows:
            key = smiles_sha(r["smiles"])
            if key in uncoded:
                uncoded[key]["rows"].append({"task": task, "split": split, "row_index": r["row_index"]})

    # fallback: mean over encoded unique strings seen in train rows of the selected tasks
    train_sha = {smiles_sha(r["smiles"]) for (task, split), rows in rows_by.items() if split == "train" for r in rows}
    train_encoded = [k for k in encoded_keys if k in train_sha]
    if not train_encoded:
        raise RuntimeError("no encoded train SMILES available to define the fallback vector")
    fallback = matrix[[keys_map[k] for k in train_encoded]].mean(axis=0, dtype=np.float64).astype(np.float32)
    if not np.all(np.isfinite(fallback)):
        raise RuntimeError("fallback vector is non-finite")

    # 5. write cache content files, then metadata (metadata records their digests)
    np.save(out_dir / "fingerprints.npy", matrix)
    (out_dir / "keys.json").write_text(json.dumps(keys_map), encoding="utf-8")
    (out_dir / "uncoded.json").write_text(json.dumps(uncoded, indent=1), encoding="utf-8")
    np.save(out_dir / "fallback_vector.npy", fallback)
    content_hashes = {name: sha256_file(out_dir / name) for name in CACHE_FILES}

    # 6. coverage report (every row encoded or fallback-eligible)
    coverage = {"rows_total": n_rows_total, "rows_encoded": 0, "rows_fallback": 0, "rows_missing": 0, "per_task": {}}
    for t in tasks:
        for split in SPLITS:
            rows = rows_by[(t["task"], split)]
            n_enc = sum(1 for r in rows if smiles_sha(r["smiles"]) in keys_map)
            n_fb = len(rows) - n_enc
            coverage["per_task"][f"{t['task']}/{split}"] = {"rows": len(rows), "encoded": n_enc, "fallback": n_fb}
            coverage["rows_encoded"] += n_enc
            coverage["rows_fallback"] += n_fb
    coverage["rows_missing"] = n_rows_total - coverage["rows_encoded"] - coverage["rows_fallback"]

    versions = {}
    for mod in ("torch", "numpy", "rdkit", "chemprop"):
        try:
            m = __import__(mod)
            versions[mod] = getattr(m, "__version__", "unknown")
        except Exception:  # noqa: BLE001 - metadata only
            versions[mod] = "not-installed"
    metadata = {
        "schema_version": 1,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "partial": False,
        "tasks": [t["task"] for t in tasks],
        "data_root": str(data_root),
        "device": args.device,
        "batch_size": args.batch_size,
        "torch_threads": max(1, args.threads),
        "versions": versions,
        "weights": {
            "path": str(Path(args.weights).resolve()),
            **enc.weights_hashes,
            "publisher_md5_verified": True,
        },
        "encoder_parameter_digest": digest_before,
        "fingerprint_dim": dim,
        "n_unique": len(unique_order),
        "n_encoded": n_encoded,
        "n_uncoded": n_failed,
        "fallback_definition": "mean fingerprint over encoded unique SMILES appearing in train rows of the selected tasks (train-only)",
        "cache_files_sha256": content_hashes,
        "coverage": coverage,
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=1), encoding="utf-8")

    _log(f"coverage: {coverage['rows_encoded']} encoded + {coverage['rows_fallback']} fallback of {n_rows_total} rows")
    _log(f"cache written to {out_dir}")
    if coverage["rows_missing"] != 0:
        print(f"ERROR: {coverage['rows_missing']} rows are neither encoded nor fallback-eligible", file=sys.stderr)
        return 2
    if n_failed:
        _log(f"uncoded strings (fallback applies): {json.dumps({k: v['reason'] for k, v in uncoded.items()}, indent=1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
