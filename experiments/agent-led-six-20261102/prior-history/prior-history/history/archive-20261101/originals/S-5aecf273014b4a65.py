"""Prediction CSV I/O: valid/test products use the shared ``(task,split,row_index)`` key.

Product schema (exactly)::

    task,split,row_index,y_pred

``predict_valid`` writes this for one or more tasks (split=valid).
``predict_test`` writes this per task (split=test) *and* can additionally build the
competition submission template by full-identity join (see ``submission.py``).

Readers validate the whole expected key set *before* returning anything: missing
rows, duplicate keys, unexpected tasks/splits, and non-finite ``y_pred`` all raise
``ScoringError``.  Empty expected sets raise.  Consumers never silently
intersect or let later rows overwrite earlier ones.
"""

import csv
import math
import os

from errors import ScoringError

PRODUCT_FIELDS = ("task", "split", "row_index", "y_pred")


def write_products(path, records):
    """Write ``records`` (iterable of dict with the 4 product fields) atomically.

    ``records`` must already be in the caller's intended order; keys are checked
    for duplicates/coverage by the caller.  Values are formatted with ``repr``
    precision (17 significant digits) so regression magnitudes survive the round
    trip.
    """
    for rec in records:
        if tuple(rec.keys()) != PRODUCT_FIELDS and set(rec) != set(PRODUCT_FIELDS):
            raise ScoringError(f"product record has wrong fields: {sorted(rec)}")
        val = float(rec["y_pred"])
        if not math.isfinite(val):
            raise ScoringError(f"non-finite y_pred for {rec['task']}/{rec['row_index']}")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(PRODUCT_FIELDS)
        for rec in records:
            w.writerow([rec["task"], rec["split"], int(rec["row_index"]),
                        repr(float(rec["y_pred"]))])
    os.replace(tmp, path)
    return path


def read_products(path, expected_keys, splits=("valid", "test")):
    """Read and validate a product CSV against ``expected_keys``.

    ``expected_keys`` is the *complete* set of ``(task, split, row_index)`` that
    must be present, each mapping to nothing (membership only).  Returns
    ``{(task, split, row_index): float}``.
    """
    if not os.path.isfile(path):
        raise ScoringError(f"product file not found: {path}")
    if not expected_keys:
        raise ScoringError("expected key set is empty; refusing to score nothing")
    out = {}
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = tuple(next(reader, ()))
        if header != PRODUCT_FIELDS:
            raise ScoringError(f"{path}: header {header} != {list(PRODUCT_FIELDS)}")
        for lineno, row in enumerate(reader, start=2):
            if len(row) != 4:
                raise ScoringError(f"{path}:{lineno}: expected 4 fields, got {len(row)}")
            task, split, row_index, y_pred = row
            if split not in splits:
                raise ScoringError(f"{path}:{lineno}: unexpected split {split!r}")
            try:
                ridx = int(row_index)
            except ValueError:
                raise ScoringError(f"{path}:{lineno}: non-integer row_index {row_index!r}")
            key = (task, split, ridx)
            if key in out:
                raise ScoringError(f"{path}:{lineno}: duplicate key {key}")
            try:
                val = float(y_pred)
            except ValueError:
                raise ScoringError(f"{path}:{lineno}: non-numeric y_pred {y_pred!r}")
            if not math.isfinite(val):
                raise ScoringError(f"{path}:{lineno}: non-finite y_pred {y_pred!r}")
            out[key] = val
    missing = set(expected_keys) - set(out)
    extra = set(out) - set(expected_keys)
    if missing:
        sample = sorted(missing)[:5]
        raise ScoringError(f"{path}: {len(missing)} missing keys, e.g. {sample}")
    if extra:
        sample = sorted(extra)[:5]
        raise ScoringError(f"{path}: {len(extra)} unexpected keys, e.g. {sample}")
    return out


def records_from_predictions(task, split, features_rows, scores, kept_row_indices):
    """Pair cached feature rows with scores back to original row identities.

    ``kept_row_indices`` are the original ``row_index`` values aligned with
    ``scores``; every source row must be represented (features or failures),
    and failures must be supplied separately by the caller.  This function only
    maps the successfully featurized rows; ``encoder_cover`` partitions the full
    set.
    """
    if len(kept_row_indices) != len(scores):
        raise ScoringError("kept_row_indices and scores length differ")
    recs = []
    for ridx, score in zip(kept_row_indices, scores):
        recs.append({"task": task, "split": split, "row_index": int(ridx),
                     "y_pred": float(score)})
    return recs