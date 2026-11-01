"""Inspect official templates and build traceable candidate submissions.

This module checks structure and records declared provenance.  It cannot prove
that predictions came from a model or that a training run used allowed inputs.
It never uploads a file or changes predictions to improve a competition score.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common import HarnessError, sha256_file


COLUMNS = ("task", "sample_idx", "drug_id", "smiles", "y_pred", "metric")
KEY_COLUMNS = ("task", "sample_idx")
CLASSIFICATION_METRICS = frozenset({"AUROC", "AUPRC"})
REGRESSION_METRICS = frozenset({"MAE", "Spearman"})
KNOWN_METRICS = CLASSIFICATION_METRICS | REGRESSION_METRICS
PREDICTION_KINDS = frozenset({"score", "probability"})


def _path(value: Any, argument: str) -> Path:
    try:
        return Path(value)
    except (TypeError, ValueError) as exc:
        raise HarnessError(
            "INVALID_PATH", f"{argument} must be a filesystem path.",
            {"argument": argument},
        ) from exc


def _read_bytes(path: Path) -> tuple[bytes, str]:
    try:
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if sha256_file(path) != digest:
            raise HarnessError(
                "SOURCE_CHANGED", "The input changed while it was being read.",
                {"path": str(path)},
            )
        return payload, digest
    except (OSError, ValueError) as exc:
        raise HarnessError(
            "INPUT_READ_ERROR", f"Cannot read input: {exc}",
            {"path": str(path)},
        ) from exc


def _text(payload: bytes, path: Path) -> str:
    try:
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HarnessError(
            "INVALID_UTF8", "Input must be UTF-8; a UTF-8 BOM is accepted.",
            {"path": str(path), "byte_offset": exc.start},
        ) from exc


def _read_csv(path: Path) -> tuple[list[dict[str, str]], str, list[int]]:
    payload, digest = _read_bytes(path)
    reader = csv.reader(io.StringIO(_text(payload, path), newline=""), strict=True)
    rows: list[dict[str, str]] = []
    line_numbers: list[int] = []
    keys: dict[tuple[str, str], int] = {}
    task_metrics: dict[str, str] = {}
    try:
        header = next(reader, None)
        if header != list(COLUMNS):
            raise HarnessError(
                "CSV_HEADER_MISMATCH", "CSV columns must exactly match the official order.",
                {"path": str(path), "line_number": 1,
                 "expected": list(COLUMNS), "actual": header},
            )
        for record_number, values in enumerate(reader, start=1):
            location = {"path": str(path), "record_number": record_number,
                        "line_number": reader.line_num}
            if len(values) != len(COLUMNS):
                raise HarnessError(
                    "CSV_COLUMN_COUNT", "CSV row has the wrong number of fields.",
                    {**location, "expected": len(COLUMNS), "actual": len(values)},
                )
            row = dict(zip(COLUMNS, values))
            for field in ("task", "sample_idx", "smiles", "metric"):
                if not row[field].strip():
                    raise HarnessError(
                        "CSV_REQUIRED_FIELD_EMPTY", "Required metadata is empty.",
                        {**location, "field": field},
                    )
            # drug_id is deliberately allowed to be empty: the official
            # reference template itself contains an empty identifier.
            if row["metric"] not in KNOWN_METRICS:
                raise HarnessError(
                    "UNKNOWN_METRIC", "Metric is not in the verified contest contract.",
                    {**location, "task": row["task"], "metric": row["metric"]},
                )
            prior_metric = task_metrics.setdefault(row["task"], row["metric"])
            if prior_metric != row["metric"]:
                raise HarnessError(
                    "TASK_METRIC_CONFLICT", "A task has inconsistent metric names.",
                    {**location, "task": row["task"],
                     "expected": prior_metric, "actual": row["metric"]},
                )
            key = (row["task"], row["sample_idx"])
            if key in keys:
                raise HarnessError(
                    "DUPLICATE_ROW_KEY", "The (task, sample_idx) key must be unique.",
                    {**location, "key": list(key), "first_line_number": keys[key]},
                )
            keys[key] = reader.line_num
            rows.append(row)
            line_numbers.append(reader.line_num)
    except csv.Error as exc:
        raise HarnessError(
            "MALFORMED_CSV", f"CSV could not be parsed: {exc}",
            {"path": str(path), "line_number": reader.line_num},
        ) from exc
    if not rows:
        raise HarnessError("EMPTY_CSV", "CSV contains no data rows.", {"path": str(path)})
    return rows, digest, line_numbers


def _check_kind(prediction_kind: str) -> None:
    if not isinstance(prediction_kind, str) or prediction_kind not in PREDICTION_KINDS:
        raise HarnessError(
            "INVALID_PREDICTION_KIND", "prediction_kind must be score or probability.",
            {"allowed": sorted(PREDICTION_KINDS)},
        )


def _prediction(value: Any, metric: str, prediction_kind: str,
                location: dict[str, Any], *, json_number: bool = False) -> float:
    if json_number and (isinstance(value, bool) or not isinstance(value, (int, float))):
        raise HarnessError(
            "PREDICTION_NOT_NUMBER", "JSON y_pred must be a number, not a string or boolean.",
            location,
        )
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise HarnessError(
            "PREDICTION_NOT_NUMBER", "y_pred must contain a numeric value.", location,
        ) from exc
    if not math.isfinite(number):
        raise HarnessError(
            "PREDICTION_NOT_FINITE", "y_pred must be finite; NaN and infinity are invalid.",
            location,
        )
    if (prediction_kind == "probability" and metric in CLASSIFICATION_METRICS
            and not 0.0 <= number <= 1.0):
        raise HarnessError(
            "PROBABILITY_OUT_OF_RANGE", "Classification probability must be within [0, 1].",
            {**location, "value": number},
        )
    return number


def _task_summary(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for row in rows:
        task = tasks.setdefault(row["task"], {
            "metric": row["metric"],
            "kind": "classification" if row["metric"] in CLASSIFICATION_METRICS else "regression",
            "rows": 0,
        })
        task["rows"] += 1
    return tasks


def inspect_template(path: Path) -> dict[str, Any]:
    """Inspect a reference template without inventing label semantics or units."""
    path = _path(path, "path")
    rows, digest, _ = _read_csv(path)
    tasks = _task_summary(rows)
    task_drug_counts = Counter((row["task"], row["drug_id"]) for row in rows)
    return {
        "ok": True, "template_path": str(path), "template_sha256": digest,
        "columns": list(COLUMNS), "key_columns": list(KEY_COLUMNS),
        "row_count": len(rows), "task_count": len(tasks), "tasks": tasks,
        "blank_drug_id_count": sum(row["drug_id"] == "" for row in rows),
        "duplicate_task_drug_id_count": sum(count - 1 for count in task_drug_counts.values()),
        "scope": "template_structure_only",
    }


def validate_submission(template_path: Path, submission_path: Path,
                        prediction_kind: str = "score") -> dict[str, Any]:
    """Check exact metadata alignment and finite model-score formatting."""
    _check_kind(prediction_kind)
    template_path = _path(template_path, "template_path")
    submission_path = _path(submission_path, "submission_path")
    template, template_digest, _ = _read_csv(template_path)
    candidate, candidate_digest, lines = _read_csv(submission_path)
    if len(candidate) != len(template):
        raise HarnessError(
            "SUBMISSION_ROW_COUNT", "Submission row count differs from the template.",
            {"path": str(submission_path), "expected": len(template), "actual": len(candidate)},
        )
    for index, (expected, actual) in enumerate(zip(template, candidate)):
        location = {"path": str(submission_path), "record_number": index + 1,
                    "line_number": lines[index],
                    "key": [expected["task"], expected["sample_idx"]]}
        for field in COLUMNS:
            if field != "y_pred" and expected[field] != actual[field]:
                raise HarnessError(
                    "SUBMISSION_METADATA_CHANGED", "Only y_pred may differ from the template.",
                    {**location, "field": field,
                     "expected": expected[field], "actual": actual[field]},
                )
        _prediction(actual["y_pred"], expected["metric"], prediction_kind, location)
    return {
        "ok": True, "template_path": str(template_path), "template_sha256": template_digest,
        "submission_path": str(submission_path), "submission_sha256": candidate_digest,
        "row_count": len(candidate), "task_count": len(_task_summary(template)),
        "prediction_kind": prediction_kind, "provenance_verified": False,
        "scope": "format_and_template_alignment_only",
    }


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HarnessError("JSON_DUPLICATE_FIELD", "Duplicate JSON object field.", {"field": key})
        result[key] = value
    return result


def _read_records(path: Path) -> tuple[dict[str, Any], str]:
    payload, digest = _read_bytes(path)
    try:
        data = json.loads(_text(payload, path), object_pairs_hook=_unique_object)
    except HarnessError as exc:
        details = {"path": str(path)}
        if isinstance(exc.details, dict):
            details.update(exc.details)
        raise HarnessError(exc.code, exc.message, details) from exc
    except json.JSONDecodeError as exc:
        raise HarnessError(
            "INVALID_PREDICTION_JSON", f"Prediction records are not valid JSON: {exc.msg}",
            {"path": str(path), "line_number": exc.lineno, "column_number": exc.colno},
        ) from exc
    except (ValueError, RecursionError) as exc:
        raise HarnessError(
            "INVALID_PREDICTION_JSON", f"Prediction records could not be decoded: {exc}",
            {"path": str(path)},
        ) from exc
    if not isinstance(data, dict):
        raise HarnessError("PREDICTION_RECORDS_SHAPE", "Prediction records must be a JSON object.",
                           {"path": str(path)})
    expected = {"schema_version", "run_id", "model_artifact_sha256", "predictions"}
    if set(data) != expected:
        raise HarnessError(
            "PREDICTION_RECORDS_FIELDS", "Prediction records must contain exactly the documented fields.",
            {"path": str(path), "missing": sorted(expected - set(data)),
             "unknown": sorted(set(data) - expected)},
        )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise HarnessError("PREDICTION_SCHEMA_VERSION", "Only schema_version 1 is supported.",
                           {"path": str(path)})
    if not isinstance(data["run_id"], str) or not data["run_id"].strip():
        raise HarnessError("PREDICTION_RUN_ID", "run_id must be a nonempty string.",
                           {"path": str(path)})
    weight_hash = data["model_artifact_sha256"]
    if not isinstance(weight_hash, str) or re.fullmatch(r"[0-9a-fA-F]{64}", weight_hash) is None:
        raise HarnessError("PREDICTION_MODEL_HASH", "model_artifact_sha256 must be 64 hexadecimal characters.",
                           {"path": str(path)})
    if not isinstance(data["predictions"], list):
        raise HarnessError("PREDICTION_LIST_SHAPE", "predictions must be a JSON array.",
                           {"path": str(path)})
    return data, digest


def _prediction_map(data: dict[str, Any], path: Path, template: list[dict[str, str]],
                    prediction_kind: str) -> dict[tuple[str, str], float]:
    template_map = {(row["task"], row["sample_idx"]): row for row in template}
    result: dict[tuple[str, str], float] = {}
    first_indices: dict[tuple[str, str], int] = {}
    for index, record in enumerate(data["predictions"]):
        location = {"path": str(path), "prediction_index": index}
        if not isinstance(record, dict):
            raise HarnessError("PREDICTION_ITEM_SHAPE", "Each prediction must be a JSON object.", location)
        expected = {"task", "sample_idx", "y_pred"}
        if set(record) != expected:
            raise HarnessError(
                "PREDICTION_ITEM_FIELDS", "Prediction must contain task, sample_idx and y_pred only.",
                {**location, "missing": sorted(expected - set(record)),
                 "unknown": sorted(set(record) - expected)},
            )
        for field in KEY_COLUMNS:
            if not isinstance(record[field], str) or not record[field].strip():
                raise HarnessError(
                    "PREDICTION_KEY_TYPE", "Prediction keys must be the original nonempty strings.",
                    {**location, "field": field},
                )
        key = (record["task"], record["sample_idx"])
        location["key"] = list(key)
        if key in result:
            raise HarnessError(
                "DUPLICATE_PREDICTION_KEY", "Prediction key appears more than once.",
                {**location, "first_prediction_index": first_indices[key]},
            )
        if key not in template_map:
            raise HarnessError("UNKNOWN_PREDICTION_KEY", "Prediction key does not occur in the template.", location)
        result[key] = _prediction(record["y_pred"], template_map[key]["metric"],
                                  prediction_kind, location, json_number=True)
        first_indices[key] = index
    missing = [list(key) for key in template_map if key not in result]
    if missing:
        raise HarnessError(
            "MISSING_PREDICTIONS", "Predictions do not cover every template row.",
            {"path": str(path), "missing_count": len(missing), "missing_keys": missing[:20]},
        )
    return result


def export_submission(template_path: Path, prediction_records_path: Path, output_path: Path,
                      prediction_kind: str = "score") -> dict[str, Any]:
    """Export a candidate and a sidecar recording *declared*, unverified lineage.

    Neither output is overwritten.  Prediction records must cover every
    (task, sample_idx) exactly once; their order need not match the template.
    """
    _check_kind(prediction_kind)
    template_path = _path(template_path, "template_path")
    prediction_records_path = _path(prediction_records_path, "prediction_records_path")
    output_path = _path(output_path, "output_path")
    sidecar_path = Path(str(output_path) + ".provenance.json")
    try:
        if output_path.resolve() in {template_path.resolve(), prediction_records_path.resolve()}:
            raise HarnessError("OUTPUT_INPUT_COLLISION", "Output must not replace an input file.",
                               {"path": str(output_path)})
        for target in (output_path, sidecar_path):
            if os.path.lexists(target):
                raise HarnessError("OUTPUT_EXISTS", "Refusing to overwrite an existing output.",
                                   {"path": str(target)})
    except (OSError, ValueError, RuntimeError) as exc:
        raise HarnessError("OUTPUT_PATH_ERROR", f"Cannot resolve output path: {exc}",
                           {"path": str(output_path)}) from exc
    template, template_digest, _ = _read_csv(template_path)
    data, records_digest = _read_records(prediction_records_path)
    predictions = _prediction_map(data, prediction_records_path, template, prediction_kind)
    text = io.StringIO(newline="")
    writer = csv.writer(text, lineterminator="\r\n")
    writer.writerow(COLUMNS)
    for row in template:
        values = dict(row)
        values["y_pred"] = repr(predictions[(row["task"], row["sample_idx"])])
        writer.writerow([values[field] for field in COLUMNS])
    payload = text.getvalue().encode("utf-8-sig")
    output_digest = hashlib.sha256(payload).hexdigest()
    provenance = {
        "schema_version": 1, "kind": "candidate_submission_provenance",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_id": data["run_id"],
        "model_artifact_sha256": data["model_artifact_sha256"].lower(),
        "prediction_kind": prediction_kind,
        "template": {"path": str(template_path), "sha256": template_digest},
        "prediction_records": {"path": str(prediction_records_path), "sha256": records_digest},
        "submission": {"path": str(output_path), "sha256": output_digest, "row_count": len(template)},
        "provenance_status": "declared_not_verified",
        "scope": "Records supplied identifiers and file hashes; does not verify model authenticity, "
                 "training provenance, external-data compliance or official acceptance.",
    }
    created: list[Path] = []
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation protects both files even if another process creates
        # a target after the preliminary existence check.
        with output_path.open("xb") as output:
            created.append(output_path)
            with sidecar_path.open("x", encoding="utf-8", newline="\n") as sidecar:
                created.append(sidecar_path)
                output.write(payload)
                sidecar.write(json.dumps(provenance, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    except (OSError, ValueError) as exc:
        cleanup_failures = []
        for target in reversed(created):
            try:
                target.unlink()
            except OSError as cleanup_error:
                cleanup_failures.append({"path": str(target), "error": str(cleanup_error)})
        raise HarnessError(
            "OUTPUT_WRITE_ERROR", f"Cannot write candidate submission and sidecar: {exc}",
            {"path": str(output_path), "sidecar_path": str(sidecar_path),
             "cleanup_failures": cleanup_failures},
        ) from exc
    return {
        "ok": True, "submission_path": str(output_path), "submission_sha256": output_digest,
        "provenance_path": str(sidecar_path), "row_count": len(template),
        "task_count": len(_task_summary(template)), "run_id": data["run_id"],
        "prediction_kind": prediction_kind, "provenance_verified": False,
        "scope": "candidate_export_only",
    }
