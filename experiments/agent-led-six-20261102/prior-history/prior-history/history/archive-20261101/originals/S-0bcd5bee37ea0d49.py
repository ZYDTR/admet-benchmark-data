"""Shared loader for prediction files (.csv or .jsonl / .json) and coverage checks.

Prediction record contract (from TASK.md):
  Each inference output file contains the columns/keys: task, split, row_index, y_pred.
    - task: task name string (must match template task names)
    - split: "test" or "valid"
    - row_index: 0-based data-row position within that task/split CSV
    - y_pred: finite JSON number (not string, not bool)

Files may be:
  * CSV with header task,split,row_index,y_pred (extra columns ignored)
  * JSONL: one JSON object per line with those keys
  * JSON: a top-level list of such objects

This module only reads and validates. It does not compute metrics.
"""

import csv
import io
import json
import math


class PredictionError(Exception):
    pass


def _validate_record(rec, source, lineno):
    for key in ("task", "split", "row_index", "y_pred"):
        if key not in rec:
            raise PredictionError(f"{source}:{lineno}: missing key {key!r}")
    task = rec["task"]
    split = rec["split"]
    if not isinstance(task, str) or not task:
        raise PredictionError(f"{source}:{lineno}: task must be non-empty string")
    if split not in ("test", "valid"):
        raise PredictionError(f"{source}:{lineno}: split must be 'test' or 'valid', got {split!r}")
    ri = rec["row_index"]
    if isinstance(ri, bool) or not isinstance(ri, int):
        # allow string digits -> int
        if isinstance(ri, str) and ri.strip().lstrip("-").isdigit():
            ri = int(ri.strip())
        else:
            raise PredictionError(f"{source}:{lineno}: row_index must be integer, got {ri!r}")
    yp = rec["y_pred"]
    if isinstance(yp, bool) or not isinstance(yp, (int, float)):
        raise PredictionError(f"{source}:{lineno}: y_pred must be a JSON number, got {yp!r}")
    yp = float(yp)
    if not math.isfinite(yp):
        raise PredictionError(f"{source}:{lineno}: y_pred not finite ({yp!r})")
    return {"task": task, "split": split, "row_index": ri, "y_pred": yp}


def load_predictions(path):
    """Load prediction records from a csv/jsonl/json path. Returns list of dicts."""
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8-sig")
    stripped = text.lstrip()
    records = []
    if path.endswith(".json") or stripped.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise PredictionError(f"{path}: JSON predictions must be a list")
        for i, rec in enumerate(data):
            if not isinstance(rec, dict):
                raise PredictionError(f"{path}: item {i} not an object")
            records.append(_validate_record(rec, path, f"item{i}"))
        return records

    if path.endswith(".jsonl"):
        for lineno, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise PredictionError(f"{path}:{lineno}: invalid JSON ({e})")
            records.append(_validate_record(rec, path, lineno))
        return records

    # CSV
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None:
        raise PredictionError(f"{path}: empty CSV")
    for lineno, row in enumerate(reader, 2):
        rec = {
            "task": row.get("task", ""),
            "split": row.get("split", ""),
            "row_index": row.get("row_index", ""),
            "y_pred": row.get("y_pred", ""),
        }
        # Coerce CSV string y_pred to float if valid
        try:
            rec["y_pred"] = float(str(rec["y_pred"]).strip())
        except (TypeError, ValueError):
            raise PredictionError(f"{path}:{lineno}: y_pred not numeric ({rec['y_pred']!r})")
        rec["row_index"] = str(rec["row_index"]).strip()
        records.append(_validate_record(rec, path, lineno))
    return records


def build_expected_index(task_rows):
    """Expected key set from template rows: {(task, 'test', row_index)}.

    task_rows: dict task -> list of template row dicts (each has sample_idx).
    """
    expected = {}
    for task, rows in task_rows.items():
        for r in rows:
            expected[(task, "test", int(r["sample_idx"]))] = True
    return expected


def check_coverage(records, expected):
    """Check records against expected test-key set.

    Returns dict with:
      missing: list of keys expected but absent (sorted)
      extra:   list of keys present but not expected (sorted)
      duplicates: dict key -> count where count>1
      ok: bool
    """
    seen = {}
    for rec in records:
        if rec["split"] != "test":
            continue
        key = (rec["task"], rec["split"], rec["row_index"])
        seen[key] = seen.get(key, 0) + 1
    missing = sorted(k for k in expected if k not in seen)
    extra = sorted(k for k in seen if k not in expected)
    duplicates = {k: c for k, c in seen.items() if c > 1}
    ok = not missing and not extra and not duplicates
    return {
        "n_records": len(records),
        "n_test_records": sum(seen.values()),
        "n_expected": len(expected),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "duplicate_count": len(duplicates),
        "missing_head": missing[:20],
        "extra_head": extra[:20],
        "duplicates_head": list(duplicates.items())[:20],
        "ok": ok,
    }