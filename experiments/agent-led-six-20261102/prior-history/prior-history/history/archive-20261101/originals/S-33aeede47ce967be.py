"""Batch feature extraction with content-addressed cache (run by the MAIN process).

NOT executed in this preparation session. Whole-batch encoding is training-stage
work; only the cache logic is exercised here with synthetic arrays.

Usage (main control, after installing deps and downloading weights)::

    python encode_features.py --data-root ../input/data \
        --weights /abs/path/chemeleon_mp.pt --asset-lock assets.lock.json \
        --cache .work/features --device cpu \
        --tasks ames caco2_wang --splits train valid test

For every (task, split):

* build the identity manifest, look up the cache; on a verified hit, reuse it;
* otherwise encode the raw SMILES, persist features + ``failures.json`` + the
  manifest, and print a coverage summary.

Failure policy (programmatic, complete coverage): rows that RDKit cannot parse are
recorded in ``failures.json`` with ``row_index``/``smiles``/``error`` and are
excluded from the feature matrix. Any downstream predictor MUST handle them by an
explicit fallback to be defined later by main control (e.g. predict the train-mean
or a fixed constant) so that every ``(task, split, row_index)`` still yields a
``y_pred``. Encoding itself never silently drops a row — the partition is written
to disk and asserted.
"""

import argparse
import json
import os
import sys

from assets import CHEMELEON_CODE_COMMIT, load_lock, package_versions
from dataio import list_tasks, read_split
from feature_cache import build_manifest, load_cache, save_cache
from errors import CacheError, FeaturizationError


def _encoder_meta(encoder, weights_meta):
    return {
        "id": "chemeleon_mp",
        "code_commit": CHEMELEON_CODE_COMMIT,
        "feature_dim": encoder.feature_dim,
        "hyper_parameters": encoder.hyper_parameters,
        "weights": weights_meta,
    }


def encode_table(encoder, table, cache_dir, deps, batch_size, force=False):
    meta = _encoder_meta(encoder, encoder.weight_metadata)
    manifest = build_manifest(table, meta, deps, batch_size)
    if not force:
        try:
            feats, cached = load_cache(cache_dir, manifest)
            print(f"[cache hit] {table['task']}/{table['split']} rows={table['n_rows']} "
                  f"failures={len(cached.get('failures', []))} key={manifest['key'][:12]}")
            return feats, cached
        except CacheError as exc:
            print(f"[cache miss] {table['task']}/{table['split']}: {exc}")
    feats, kept, failures = encoder.encode_smiles(table["smiles"], batch_size=batch_size)
    if failures:
        print(f"[featurization] {table['task']}/{table['split']}: {len(failures)} row(s) "
              f"could not be encoded; row_index: {[f['row_index'] for f in failures]}")
    entry = save_cache(cache_dir, manifest, feats, kept, failures)
    manifest_path = os.path.join(entry, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as fh:
        cached = json.load(fh)
    print(f"[cache write] {table['task']}/{table['split']} -> {entry}")
    return feats, cached


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--asset-lock", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--tasks", nargs="*", default=None,
                    help="default: all tasks under the pack")
    ap.add_argument("--splits", nargs="*", default=["train", "valid", "test"])
    ap.add_argument("--force", action="store_true", help="rebuild even on cache hit")
    args = ap.parse_args(argv)

    lock = load_lock(args.asset_lock)
    deps = package_versions()
    missing = [k for k, v in deps.items() if v is None]
    if missing:
        print(f"[deps] missing packages: {missing}", file=sys.stderr)
        return 2

    from chemeleon_encoder import FrozenCheMeleonEncoder

    encoder = FrozenCheMeleonEncoder(
        args.weights, device=args.device, expected_sha256=lock["weights_sha256"]
    )
    tasks = args.tasks or list_tasks(args.data_root)
    summary = []
    for task in tasks:
        for split in args.splits:
            table = read_split(args.data_root, task, split)
            feats, cached = encode_table(
                encoder, table, args.cache, deps, args.batch_size, force=args.force
            )
            summary.append({
                "task": task, "split": split, "n_rows": table["n_rows"],
                "n_features": int(feats.shape[0]),
                "n_failures": len(cached.get("failures", [])),
                "key": cached["key"],
            })
    print(json.dumps({"summary": summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())