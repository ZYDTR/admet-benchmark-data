"""Shared contracts for ADMET data-eval preparation (stdlib only).

Identity rules (from TASK.md):
  prediction key = (task, split, row_index)
  split in {train, test, valid}
  row_index = zero-based data-row position in that split's original CSV

Task schema is derived from the official submission template plus per-task
metric/kind.  We do NOT trust inferred declarations blindly: every run
re-derives the schema from the template and refuses if it disagrees with the
checked-in schema file.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
from typing import Dict, Iterable, List, Tuple

TASK_SCHEMA_SCHEMA_VERSION = 1
PRED_SCHEMA_VERSION = 1
LABELS_SCHEMA_VERSION = 1

SPLITS = ("train", "test", "valid")
REQUIRED_TEMPLATE_FIELDS = ("task", "sample_idx", "drug_id", "smiles", "y_pred", "metric")

# Metric -> kind.  Source: competition/task_schema.json (kind/metric) which is
# itself reconciled with the template `metric` column.  Classification metrics
# emit P(Y=1); regression metrics emit the original Y scale.
METRIC_KIND = {
    "AUROC": "classification",
    "AUPRC": "classification",
    "MAE": "regression",
    "Spearman": "regression",
}
TEMPLATE_METRIC_TO_LOCAL = {"AUPRC": "AP"}  # local metric label for output only

PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DEFAULT_OFFICIAL_BASE = os.path.join(PACKAGE_ROOT, "input/data/official")
DEFAULT_BLIND_BASE = os.path.join(PACKAGE_ROOT, "input/data/blind_validation")


class ContractError(Exception):
    """Structured, explicit failure.  CLI maps this to exit status 2."""

    def __init__(self, code: str, message: str, **context):
        super().__init__(message)
        self.code = code
        self.message = message
        self.context = context

    def to_dict(self) -> dict:
        return {"error": self.code, "message": self.message, "context": self.context}


# --------------------------------------------------------------------------
# Hashing / file IO
# --------------------------------------------------------------------------
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def decode_utf8_sig(raw: bytes, path: str) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:  # pragma: no cover - explicit failure
        raise ContractError("DECODE_ERROR", f"cannot decode {path} as UTF-8: {exc}",
                            path=path) from exc


def sniff_format(raw: bytes) -> dict:
    return {
        "utf8_bom": raw.startswith(b"\xef\xbb\xbf"),
        "crlf_count": raw.count(b"\r\n"),
        "lf_count": raw.count(b"\n"),
    }


def load_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise ContractError("FILE_MISSING", f"missing file: {path}", path=path) from exc
    except json.JSONDecodeError as exc:
        raise ContractError("JSON_INVALID", f"invalid JSON in {path}: {exc}",
                            path=path) from exc


# --------------------------------------------------------------------------
# CSV parsing
# --------------------------------------------------------------------------
def parse_csv(raw: bytes, path: str) -> Tuple[List[str], List[List[str]]]:
    """Return (header, rows) as raw strings.  No coercion, no cleaning."""
    text = decode_utf8_sig(raw, path)
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise ContractError("EMPTY_CSV", f"empty CSV: {path}", path=path) from exc
    rows = []
    for lineno, row in enumerate(reader, start=2):
        rows.append(row)
    return header, rows


def csv_rows_as_dicts(header: List[str], rows: List[List[str]], path: str) -> List[dict]:
    out = []
    n = len(header)
    for i, row in enumerate(rows):
        if len(row) != n:
            raise ContractError("CSV_BAD_COLCOUNT",
                                f"{path}: row {i} has {len(row)} fields, expected {n}",
                                path=path, row_index=i)
        out.append(dict(zip(header, row)))
    return out


def is_finite_number(value) -> bool:
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


# --------------------------------------------------------------------------
# Task schema
# --------------------------------------------------------------------------
def build_schema_from_template(template_path: str) -> dict:
    """Derive the task set + per-task metrics purely from the template bytes."""
    raw = read_bytes(template_path)
    header, rows = parse_csv(raw, template_path)
    if header != list(REQUIRED_TEMPLATE_FIELDS):
        raise ContractError("TEMPLATE_HEADER",
                            f"template header mismatch: {header}", header=header)
    task_order: List[str] = []
    task_rows: Dict[str, int] = {}
    task_metric: Dict[str, str] = {}
    for i, row in enumerate(rows):
        rec = dict(zip(header, row))
        task = rec["task"]
        metric = rec["metric"]
        if task not in task_rows:
            task_order.append(task)
            task_rows[task] = 0
            task_metric[task] = metric
        elif task_metric[task] != metric:
            raise ContractError("TEMPLATE_METRIC_INCONSISTENT",
                                f"task {task} has mixed metrics", task=task)
        task_rows[task] += 1
    tasks = []
    for task in task_order:
        metric = task_metric[task]
        if metric not in METRIC_KIND:
            raise ContractError("TEMPLATE_UNKNOWN_METRIC",
                                f"unknown metric {metric} for task {task}", task=task)
        tasks.append({
            "task": task,
            "metric": metric,
            "kind": METRIC_KIND[metric],
            "template_rows": task_rows[task],
        })
    return {
        "schema_version": TASK_SCHEMA_SCHEMA_VERSION,
        "source_template_sha256": hashlib.sha256(raw).hexdigest(),
        "template_rows": len(rows),
        "tasks": tasks,
    }


def load_and_check_schema(schema_path: str, template_path: str) -> dict:
    """Load a schema file and cross-check it against the live template."""
    declared = load_json(schema_path)
    if declared.get("schema_version") != TASK_SCHEMA_SCHEMA_VERSION:
        raise ContractError("SCHEMA_VERSION", "task schema_version mismatch",
                            got=declared.get("schema_version"))
    derived = build_schema_from_template(template_path)
    d_tasks = {t["task"]: t for t in declared.get("tasks", [])}
    r_tasks = {t["task"]: t for t in derived["tasks"]}
    if set(d_tasks) != set(r_tasks):
        raise ContractError("SCHEMA_TASK_SET",
                            "task set differs between schema file and template",
                            only_in_file=sorted(set(d_tasks) - set(r_tasks)),
                            only_in_template=sorted(set(r_tasks) - set(d_tasks)))
    for task, rt in r_tasks.items():
        dt = d_tasks[task]
        for key in ("metric", "kind", "template_rows"):
            if dt.get(key) != rt[key]:
                raise ContractError("SCHEMA_MISMATCH",
                                    f"task {task} field {key} differs",
                                    task=task, key=key,
                                    file=dt.get(key), template=rt[key])
    if declared.get("source_template_sha256") != derived["source_template_sha256"]:
        raise ContractError("SCHEMA_TEMPLATE_HASH",
                            "schema was not built from this template hash",
                            file=declared.get("source_template_sha256"),
                            actual=derived["source_template_sha256"])
    return declared


# --------------------------------------------------------------------------
# Split files
# --------------------------------------------------------------------------
def split_path(split: str, task: str, official_base: str, blind_base: str) -> str:
    if split == "train":
        return os.path.join(official_base, "data_benchmark", task, "train.csv")
    if split == "test":
        return os.path.join(official_base, "data_benchmark", task, "test.csv")
    if split == "valid":
        return os.path.join(blind_base, task, "valid.csv")
    raise ContractError("UNKNOWN_SPLIT", f"unknown split {split!r}", split=split)


def read_split(split: str, task: str, official_base: str, blind_base: str) -> dict:
    """Read one split CSV and return identity + integrity summary.

    Never drops rows.  Duplicate SMILES / blank Drug_ID are preserved and
    counted, not rejected.
    """
    path = split_path(split, task, official_base, blind_base)
    raw = read_bytes(path)
    header, rows = parse_csv(raw, path)
    expect = ["Drug_ID", "Drug", "Y"] if split == "train" else ["Drug_ID", "Drug"]
    if header != expect:
        raise ContractError("SPLIT_HEADER", f"{path}: header {header} != {expect}",
                            path=path, header=header)
    return {
        "split": split,
        "task": task,
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "format": sniff_format(raw),
        "header": header,
        "rows": rows,
        "n_rows": len(rows),
        "row_index_sha256": _row_index_digest(rows),
    }


def _row_index_digest(rows: List[List[str]]) -> str:
    """Digest of the ordered identity columns (Drug_ID, Drug) per row."""
    h = hashlib.sha256()
    for row in rows:
        h.update(row[0].encode("utf-8"))
        h.update(b"\x1f")
        h.update(row[1].encode("utf-8"))
        h.update(b"\x1e")
    return h.hexdigest()


def split_identity_digest(task: str, split: str, sha: str, n_rows: int,
                          row_index_sha: str) -> str:
    h = hashlib.sha256()
    h.update(f"{task}\x1f{split}\x1f{sha}\x1f{n_rows}\x1f{row_index_sha}".encode("utf-8"))
    return h.hexdigest()


# --------------------------------------------------------------------------
# Labels (external, explicit) and prediction files
# --------------------------------------------------------------------------
def load_label_file(path: str, expected_tasks: Iterable[str],
                    expected_tasks_by_split: Dict[str, Iterable[str]]) -> Dict[Tuple[str, str, int], object]:
    """Load an explicitly-passed label file (split-labelled).

    Format: JSON {schema_version, split_id, labels: [{task, split, row_index, y}]}
    Also accepts the raw official validation CSV (Drug_ID,Drug,Y) via the
    `--labels-csv` convenience in score.py, which converts it here.

    Each of (task, split) must be in expected_tasks_by_split.  y must be a
    finite JSON number (or null => excluded, not scored).  Classification 0/1
    is enforced later by the metric layer, per task kind, so a bad label is
    attributed to the right task.
    """
    doc = load_json(path)
    if doc.get("schema_version") != LABELS_SCHEMA_VERSION:
        raise ContractError("LABELS_VERSION", "labels schema_version mismatch",
                            got=doc.get("schema_version"))
    labels = doc.get("labels")
    if not isinstance(labels, list):
        raise ContractError("LABELS_SHAPE", "labels must be a list")
    out: Dict[Tuple[str, str, int], object] = {}
    dups = []
    unknown = []
    bad_split = []
    for i, rec in enumerate(labels):
        try:
            task = rec["task"]
            split = rec["split"]
            row_index = rec["row_index"]
            y = rec["y"]
        except (KeyError, TypeError) as exc:
            raise ContractError("LABELS_RECORD", f"labels[{i}] missing fields: {exc}")
        if split not in SPLITS:
            bad_split.append((task, split))
            continue
        if task not in expected_tasks_by_split.get(split, set()):
            unknown.append((task, split))
            continue
        if isinstance(row_index, bool) or not isinstance(row_index, int) or row_index < 0:
            raise ContractError("LABELS_ROW_INDEX",
                                f"labels[{i}] invalid row_index {row_index!r}")
        if y is not None and not is_finite_number(y):
            raise ContractError("LABELS_NONFINITE",
                                f"labels[{i}] y is not a finite number: {y!r}",
                                task=task, split=split, row_index=row_index)
        key = (task, split, row_index)
        if key in out:
            dups.append(key)
        out[key] = y
    if unknown:
        raise ContractError("LABELS_UNKNOWN_TASK",
                            "label file has task/split combos not requested or unknown split",
                            examples=unknown[:10], count=len(unknown))
    if bad_split:
        raise ContractError("LABELS_BAD_SPLIT", "label records use invalid split",
                            examples=bad_split[:10])
    if dups:
        raise ContractError("LABELS_DUPLICATE", "duplicate label keys",
                            examples=dups[:10], count=len(dups))
    return out


def load_predictions(path: str, expected_keys: Dict[str, set]) -> Dict[Tuple[str, str, int], float]:
    """Load predictions and enforce the *complete* expected key set.

    expected_keys: {split: {(task, row_index), ...}} derived from the inputs we
    were explicitly asked to cover.  Raises on missing, extra, duplicate, or
    non-finite.  No dict-overwrite, no intersection scoring.
    """
    doc = load_json(path)
    if doc.get("schema_version") != PRED_SCHEMA_VERSION:
        raise ContractError("PRED_VERSION", "prediction schema_version mismatch",
                            got=doc.get("schema_version"))
    preds = doc.get("predictions")
    if not isinstance(preds, list):
        raise ContractError("PRED_SHAPE", "predictions must be a list")
    out: Dict[Tuple[str, str, int], float] = {}
    dups = []
    for i, rec in enumerate(preds):
        if not isinstance(rec, dict):
            raise ContractError("PRED_RECORD", f"predictions[{i}] not an object")
        try:
            task = rec["task"]
            split = rec["split"]
            row_index = rec["row_index"]
            y_pred = rec["y_pred"]
        except KeyError as exc:
            raise ContractError("PRED_RECORD", f"predictions[{i}] missing {exc}")
        if split not in SPLITS:
            raise ContractError("PRED_BAD_SPLIT", f"predictions[{i}] bad split {split!r}",
                                task=task, split=split)
        if isinstance(row_index, bool) or not isinstance(row_index, int) or row_index < 0:
            raise ContractError("PRED_ROW_INDEX",
                                f"predictions[{i}] invalid row_index {row_index!r}",
                                task=task, split=split)
        if not is_finite_number(y_pred):
            raise ContractError("PRED_NONFINITE",
                                f"predictions[{i}] y_pred not finite number: {y_pred!r}",
                                task=task, split=split, row_index=row_index)
        key = (task, split, row_index)
        if key in out:
            dups.append(key)
        out[key] = float(y_pred)
    if dups:
        raise ContractError("PRED_DUPLICATE", "duplicate prediction keys",
                            examples=dups[:10], count=len(dups))
    # Build union of expected keys and require exact match.
    expected = set()
    for split, keys in expected_keys.items():
        for task, ri in keys:
            expected.add((task, split, ri))
    missing = expected - set(out)
    extra = set(out) - expected
    if missing or extra:
        raise ContractError(
            "PRED_KEY_SET",
            "prediction key set does not match expected inputs",
            missing_count=len(missing), extra_count=len(extra),
            missing_examples=sorted(missing)[:10],
            extra_examples=sorted(extra)[:10],
        )
    return out