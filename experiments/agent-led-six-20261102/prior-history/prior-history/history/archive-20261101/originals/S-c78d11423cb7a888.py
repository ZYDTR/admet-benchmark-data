"""Feature cache: frozen CheMeleon embeddings for train/valid/test, per task.

Output layout per cache dir:
    <cache>/manifest.json
    <cache>/<task>/__<split>.npy        float32 [n_rows, 2048] (NaN where unparseable)
    <cache>/<task>/__<split>.ok.npy      bool  [n_rows] RDKit parse success
    <cache>/<task>/__<split>.rows.json   [{drug_id, smiles, row_index, parse_ok}]

Identical SMILES strings are encoded once per split and broadcast back to every row, so
duplicate measurements each keep their own row_index. No labels are read or stored here.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (TASKS, TEST_REL, TRAIN_REL, VALID_REL, project_root,  # noqa: E402
                    read_csv_rows, resolve, write_json)

SPLITS = ("train", "valid", "test")
SPLIT_REL = {"train": TRAIN_REL, "valid": VALID_REL, "test": TEST_REL}


def cache_paths(cache_root: Path, task: str, split: str):
    d = cache_root / task
    return (d / f"__{split}.npy", d / f"__{split}.ok.npy", d / f"__{split}.rows.json")


def split_is_complete(cache_root: Path, task: str, split: str, expected_n: int) -> bool:
    arr_p, ok_p, rows_p = cache_paths(cache_root, task, split)
    if not (arr_p.is_file() and ok_p.is_file() and rows_p.is_file()):
        return False
    with open(rows_p, encoding="utf-8") as fh:
        rows = json.load(fh)
    return len(rows) == expected_n and all(r["row_index"] == i for i, r in enumerate(rows))


def load_split(cache_root: Path, task: str, split: str):
    import numpy as np

    arr_p, ok_p, rows_p = cache_paths(cache_root, task, split)
    if not arr_p.is_file():
        raise FileNotFoundError(f"missing feature cache {arr_p}; run build_features.py first")
    X = np.load(arr_p)
    ok = np.load(ok_p)
    with open(rows_p, encoding="utf-8") as fh:
        rows = json.load(fh)
    return X, ok, rows


def build_task_split(embedder, task: str, split: str, cache_root: Path,
                     overwrite: bool = False) -> dict:
    import numpy as np

    rows = read_csv_rows(resolve(SPLIT_REL[split].format(task=task)))
    arr_p, ok_p, rows_p = cache_paths(cache_root, task, split)
    if split_is_complete(cache_root, task, split, len(rows)) and not overwrite:
        return {"task": task, "split": split, "status": "cached", "rows": len(rows)}

    smiles = [r["Drug"] for r in rows]
    # Deduplicate identical SMILES strings within this split: encode each unique string
    # once and broadcast. Duplicate measurements keep their own row_index below.
    uniq = list(dict.fromkeys(smiles))
    u_emb, u_ok = embedder.embed(uniq)
    pos = {s: i for i, s in enumerate(uniq)}
    take = np.asarray([pos[s] for s in smiles], dtype=np.int64)
    emb, ok = u_emb[take], u_ok[take]
    assert emb.shape[0] == len(rows)
    assert emb.shape[1] == embedder.feature_dim
    arr_p.parent.mkdir(parents=True, exist_ok=True)
    np.save(arr_p, emb)
    np.save(ok_p, ok)
    write_json(rows_p, [
        {"row_index": i, "drug_id": r["Drug_ID"], "smiles": r["Drug"],
         "parse_ok": bool(ok[i])}
        for i, r in enumerate(rows)
    ])
    return {
        "task": task, "split": split, "status": "built", "rows": len(rows),
        "n_unparseable": int((~ok).sum()),
        "unparseable": [
            {"row_index": int(i), "drug_id": rows[i]["Drug_ID"], "smiles": rows[i]["Drug"]}
            for i in np.nonzero(~ok)[0]
        ],
        "shape": list(emb.shape),
    }


def build_coverage_report(cache_root: Path, checkpoint_meta: dict) -> dict:
    import numpy as np

    per_task = {}
    total_rows = total_bad = 0
    for task in TASKS:
        task_info = {}
        for split in SPLITS:
            X, ok, rows = load_split(cache_root, task, split)
            bad = int((~ok).sum())
            task_info[split] = {
                "rows": len(rows),
                "dim": int(X.shape[1]),
                "n_unparseable": bad,
                "unparseable_rows": [int(r["row_index"]) for r in rows if not r["parse_ok"]],
                "all_finite_after_fill": bool(np.isfinite(np.nan_to_num(X, nan=0.0)).all()),
            }
            total_rows += len(rows)
            total_bad += bad
        per_task[task] = task_info
    return {
        "encoder": "chemeleon_mp",
        "checkpoint": checkpoint_meta,
        "total_rows": total_rows,
        "total_unparseable_rows": total_bad,
        "fill_policy": "constant GLOBAL_FILL_VALUE row for unparseable rows; "
                       "row kept, prediction still produced",
        "per_task": per_task,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chemeleon", required=True, type=Path,
                    help="path to chemeleon_mp.pt (pinned)")
    ap.add_argument("--cache", type=Path, default=project_root() / "output/model/cache/chemeleon_mp",
                    help="feature cache directory")
    ap.add_argument("--tasks", nargs="*", default=None)
    ap.add_argument("--splits", nargs="*", default=list(SPLITS))
    ap.add_argument("--device", default=None, help="cpu | cuda | cuda:0 ...")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--report", action="store_true",
                    help="also rebuild coverage.json from all cached splits (requires every split)")
    args = ap.parse_args()

    from encoder import CheMeleonEmbedder

    tasks = args.tasks or TASKS
    embedder = CheMeleonEmbedder(args.chemeleon, args.device, args.batch_size)
    embedder.assert_frozen()
    meta, device = embedder.checkpoint_meta, embedder.device

    results = []
    t0 = time.time()
    for task in tasks:
        for split in args.splits:
            info = build_task_split(embedder, task, split, args.cache, args.overwrite)
            extra = (f" unparseable={info.get('n_unparseable', 0)}"
                     if info["status"] == "built" else "")
            done = sum(r["rows"] for r in results) + info["rows"]
            print(f"[{info['status']}] {task}/{split} rows={info['rows']}{extra} "
                  f"(total {done} rows, {time.time()-t0:.1f}s)", flush=True)
            results.append(info)

    coverage = build_coverage_report(args.cache, meta) if args.report else None
    manifest = {
        "encoder": "chemeleon_mp",
        "checkpoint": meta,
        "feature_dim": embedder.feature_dim,
        "device": device,
        "tasks": sorted({r["task"] for r in results}),
        "splits": args.splits,
        "runs": results,
    }
    write_json(args.cache / "manifest.json", manifest)
    if coverage is not None:
        write_json(args.cache / "coverage.json", coverage)
        print(f"coverage: {coverage['total_unparseable_rows']} unparseable / "
              f"{coverage['total_rows']} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())