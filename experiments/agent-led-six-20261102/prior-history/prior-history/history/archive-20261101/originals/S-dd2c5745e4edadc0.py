"""Light self-checks. No training, no parameter updates, no network, no writes
outside the directory you pass with --report.

Subcommands:

  data       (stdlib only) Input snapshot integrity: headers, row counts vs
             tasks.json, Y finiteness/binary check, unique-SMILES counts vs the
             audited snapshot, template (task, sample_idx) alignment with
             test.csv, presence of the documented exception rows. Runnable in
             the preparation environment (was run there on 2026-10-30).

  cache      (needs numpy) Internal consistency of a features cache: files
             present, keys/uncoded disjoint, matrix shape, fallback finite,
             metadata coverage totals add up.

  encoder    (needs torch+chemprop+rdkit) Frozen-load smoke test: verify the
             weights file against the publisher size/MD5, build the frozen
             encoder, run fingerprints for ["C", "CC", "CCC"], check shape/
             finiteness, and prove the parameter digest is identical before and
             after. Also reports (does not assert) what happens to the two
             documented solubility exception strings. No optimizer, no
             backward, no .step() anywhere.

  artifacts  (stdlib only) Prediction file audit: for each task/split, the
             prediction file covers row_index 0..n-1 exactly once, y_pred is
             finite, classification predictions are within [0,1].

Exit code 0 = all checks passed; 2 = failures (also written to --report JSON).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

from .data_io import read_rows, split_path
from .tasks import SPLITS, load_registry, load_tasks


def check_data(data_root: Path, report: dict) -> list[str]:
    reg = load_registry()
    tasks = load_tasks()
    expected_unique = reg["expected_unique_smiles"]
    failures: list[str] = []

    uniq: dict[str, set[str]] = {"train": set(), "valid": set(), "test": set()}
    for t in tasks:
        for split in SPLITS:
            try:
                rows = read_rows(split_path(data_root, t["task"], split), expect_y=(split == "train"))
            except Exception as e:  # noqa: BLE001
                failures.append(f"{t['task']}/{split}: read failed: {e}")
                continue
            if len(rows) != t["rows"][split]:
                failures.append(
                    f"{t['task']}/{split}: {len(rows)} rows, tasks.json expects {t['rows'][split]}"
                )
            for r in rows:
                uniq[split].add(r["smiles"])
            if split == "train" and t["kind"] == "classification":
                bad = sorted({r["y"] for r in rows} - {0.0, 1.0})
                if bad:
                    failures.append(f"{t['task']}: classification train Y not binary: {bad[:5]}")

    report["unique_smiles"] = {k: len(v) for k, v in uniq.items()}
    for split in SPLITS:
        if len(uniq[split]) != expected_unique[split]:
            failures.append(
                f"unique SMILES {split}: {len(uniq[split])} != audited {expected_unique[split]}"
            )
    n_all = len(uniq["train"] | uniq["valid"] | uniq["test"])
    if n_all != expected_unique["all"]:
        failures.append(f"unique SMILES all: {n_all} != audited {expected_unique['all']}")

    # documented exception rows must be exactly where the audit says they are
    for exc in reg["known_input_exceptions"]:
        try:
            rows = read_rows(split_path(data_root, exc["task"], exc["split"]), expect_y=False)
        except Exception as e:  # noqa: BLE001
            failures.append(f"exception row check read failed: {e}")
            continue
        got = rows[exc["row_index"]]["smiles"]
        if got != exc["smiles"]:
            failures.append(
                f"{exc['task']}/{exc['split']} row {exc['row_index']}: smiles changed vs audit anchor"
            )

    # template alignment: (task, sample_idx) == test.csv row_index, with identical drug_id+smiles
    tpl_path = data_root / "official" / "submission_template.csv"
    tpl = list(csv.DictReader(tpl_path.open("r", newline="", encoding="utf-8-sig")))
    total_test = sum(t["rows"]["test"] for t in tasks)
    if len(tpl) != total_test:
        failures.append(f"template has {len(tpl)} rows, test rows total {total_test}")
    by_task: dict[str, list[dict]] = {}
    for r in tpl:
        by_task.setdefault(r["task"], []).append(r)
    if set(by_task) != {t["task"] for t in tasks}:
        failures.append("template task set differs from tasks.json")
    for t in tasks:
        rs = by_task.get(t["task"], [])
        if [int(r["sample_idx"]) for r in rs] != list(range(len(rs))):
            failures.append(f"{t['task']}: template sample_idx not 0..n-1 in file order")
            continue
        test_rows = list(csv.reader(split_path(data_root, t["task"], "test").open("r", newline="", encoding="utf-8-sig")))[1:]
        for r in rs:
            si = int(r["sample_idx"])
            if si >= len(test_rows) or r["smiles"] != test_rows[si][1] or r["drug_id"] != test_rows[si][0]:
                failures.append(f"{t['task']}: template/test mismatch at sample_idx {si}")
                break

    report["checks"] = {
        "tasks": len(tasks),
        "template_rows": len(tpl),
        "template_alignment": "task,sample_idx <-> test.csv row_index identical for all rows" if not failures else "see failures",
    }
    return failures


def check_cache(cache_dir: Path, report: dict) -> list[str]:
    failures: list[str] = []
    try:
        import numpy as np
    except ImportError:
        return ["numpy is required for cache checks"]

    required = ["fingerprints.npy", "keys.json", "uncoded.json", "fallback_vector.npy", "metadata.json"]
    for name in required:
        if not (cache_dir / name).is_file():
            failures.append(f"missing cache file: {name}")
    if failures:
        return failures

    meta = json.loads((cache_dir / "metadata.json").read_text(encoding="utf-8"))
    if meta.get("partial"):
        failures.append("cache is marked partial")
    keys = json.loads((cache_dir / "keys.json").read_text(encoding="utf-8"))
    uncoded = json.loads((cache_dir / "uncoded.json").read_text(encoding="utf-8"))
    matrix = np.load(cache_dir / "fingerprints.npy")
    fallback = np.load(cache_dir / "fallback_vector.npy")

    if set(keys) & set(uncoded):
        failures.append(f"keys/uncoded overlap: {len(set(keys) & set(uncoded))} hashes")
    if matrix.ndim != 2:
        failures.append(f"matrix ndim {matrix.ndim}")
    if matrix.shape[0] != len(keys):
        failures.append(f"matrix rows {matrix.shape[0]} != keys {len(keys)}")
    if fallback.shape != (matrix.shape[1],):
        failures.append(f"fallback shape {fallback.shape} != ({matrix.shape[1]},)")
    if not np.all(np.isfinite(matrix)):
        failures.append("non-finite entries in fingerprint matrix")
    if not np.all(np.isfinite(fallback)):
        failures.append("non-finite fallback vector")
    cov = meta.get("coverage", {})
    if cov.get("rows_missing", -1) != 0:
        failures.append(f"metadata coverage rows_missing = {cov.get('rows_missing')}")
    if cov.get("rows_encoded", -1) + cov.get("rows_fallback", -2) != cov.get("rows_total", -3):
        failures.append("coverage totals do not add up")
    if meta.get("n_encoded", -1) != len(keys):
        failures.append("metadata n_encoded != len(keys)")
    if meta.get("n_uncoded", -1) != len(uncoded):
        failures.append("metadata n_uncoded != len(uncoded)")

    report["cache"] = {
        "dir": str(cache_dir),
        "dim": int(matrix.shape[1]) if matrix.ndim == 2 else None,
        "n_encoded": len(keys),
        "n_uncoded": len(uncoded),
        "weights_sha256": meta.get("weights", {}).get("sha256"),
        "encoder_parameter_digest": meta.get("encoder_parameter_digest"),
        "versions": meta.get("versions"),
    }
    return failures


def check_encoder(weights: str, report: dict) -> list[str]:
    failures: list[str] = []
    try:
        import numpy as np
        from rdkit.Chem import MolFromSmiles
    except ImportError:
        return ["numpy and rdkit are required for encoder checks"]

    from .encoder import CheMeleonFrozen

    try:
        enc = CheMeleonFrozen(weights, device="cpu")
    except Exception as e:  # noqa: BLE001
        return [f"encoder load failed: {type(e).__name__}: {e}"]
    enc.assert_frozen()
    digest_before = enc.parameter_digest()
    mols = [MolFromSmiles(s) for s in ("C", "CC", "CCC")]
    if any(m is None for m in mols):
        failures.append("unexpected: simple alkanes failed to parse")
        return failures
    fps = enc.fingerprint_graphs([enc.featurize(m) for m in mols])
    if fps.shape != (3, enc.fingerprint_dim):
        failures.append(f"fingerprint shape {fps.shape} != (3, {enc.fingerprint_dim})")
    if not np.all(np.isfinite(fps)):
        failures.append("non-finite fingerprints for simple alkanes")
    digest_after = enc.parameter_digest()
    if digest_after != digest_before:
        failures.append("encoder parameter digest changed during the smoke call")
    enc.assert_frozen()

    # documented exception strings: report status, do not assert
    reg = load_registry()
    exceptions = []
    for exc in reg["known_input_exceptions"]:
        mol = MolFromSmiles(exc["smiles"])
        if mol is None:
            status = "rdkit_parse_failed"
        else:
            try:
                vec = enc.fingerprint_graphs([enc.featurize(mol)])[0]
                status = "encodes" if np.all(np.isfinite(vec)) else "nonfinite"
            except Exception as e:  # noqa: BLE001
                status = f"fingerprint_failed:{type(e).__name__}"
        exceptions.append({"task": exc["task"], "row_index": exc["row_index"], "status": status})

    import chemprop
    import rdkit
    import torch

    report["encoder"] = {
        "weights": {
            "size_bytes": enc.weights_hashes["size_bytes"],
            "md5": enc.weights_hashes["md5"],
            "sha256": enc.weights_hashes["sha256"],
            "publisher_md5_verified": True,
        },
        "fingerprint_dim": enc.fingerprint_dim,
        "parameter_digest": digest_before,
        "versions": {
            "torch": torch.__version__,
            "chemprop": getattr(chemprop, "__version__", "unknown"),
            "rdkit": rdkit.__version__,
            "numpy": np.__version__,
        },
        "exception_strings": exceptions,
    }
    return failures


def check_artifacts(data_root: Path, pred_dir: Path, report: dict) -> list[str]:
    failures: list[str] = []
    tasks = load_tasks()
    for split in ("valid", "test"):
        path = pred_dir / f"{split}_predictions.csv"
        if not path.is_file():
            failures.append(f"missing prediction file: {path}")
            continue
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            if header != ["task", "split", "row_index", "y_pred"]:
                failures.append(f"{path}: header {header}")
                continue
            rows = list(reader)
        per_task: dict[str, list[int]] = {}
        preds: dict[str, list[float]] = {}
        for i, rec in enumerate(rows):
            if len(rec) != 4 or rec[1] != split:
                failures.append(f"{path}: row {i} malformed or wrong split: {rec[:2]}")
                continue
            try:
                ri = int(rec[2])
                p = float(rec[3])
            except ValueError:
                failures.append(f"{path}: row {i} unparseable row_index/y_pred")
                continue
            if not math.isfinite(p):
                failures.append(f"{path}: row {i} non-finite y_pred")
            per_task.setdefault(rec[0], []).append(ri)
            preds.setdefault(rec[0], []).append(p)
        for t in tasks:
            got = sorted(per_task.get(t["task"], []))
            want = list(range(t["rows"][split]))
            if got != want:
                failures.append(
                    f"{t['task']}/{split}: coverage mismatch (got {len(got)}, want {len(want)})"
                )
            if t["kind"] == "classification":
                ps = preds.get(t["task"], [])
                if ps and (min(ps) < 0.0 or max(ps) > 1.0):
                    failures.append(f"{t['task']}/{split}: classification y_pred outside [0,1]")
        report.setdefault("artifacts", {})[split] = {
            "file": str(path),
            "rows": len(rows),
            "tasks_present": len(per_task),
        }
    return failures


def main(argv: list[str] | None = None) -> int:
    from .data_io import DEFAULT_DATA_ROOT

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["data", "cache", "encoder", "artifacts"])
    ap.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT))
    ap.add_argument("--features", default=None, help="cache dir (cache mode)")
    ap.add_argument("--weights", default=None, help="chemeleon_mp.pt path (encoder mode)")
    ap.add_argument("--predictions", default=None, help="predictions dir (artifacts mode)")
    ap.add_argument("--report", default=None, help="optional JSON report path")
    args = ap.parse_args(argv)

    report: dict = {"mode": args.mode, "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    if args.mode == "data":
        failures = check_data(Path(args.data_root), report)
    elif args.mode == "cache":
        if not args.features:
            print("cache mode requires --features", file=sys.stderr)
            return 2
        failures = check_cache(Path(args.features), report)
    elif args.mode == "encoder":
        if not args.weights:
            print("encoder mode requires --weights", file=sys.stderr)
            return 2
        failures = check_encoder(args.weights, report)
    else:
        if not args.predictions:
            print("artifacts mode requires --predictions", file=sys.stderr)
            return 2
        failures = check_artifacts(Path(args.data_root), Path(args.predictions), report)

    report["failures"] = failures
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "failures"}, indent=1))
    if failures:
        print(f"FAIL ({len(failures)} problems):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 2
    print("OK: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
