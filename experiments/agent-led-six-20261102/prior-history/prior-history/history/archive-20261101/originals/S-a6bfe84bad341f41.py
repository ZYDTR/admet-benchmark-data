"""Dependency-free local per-task metrics with explicit undefined results.

No official leaderboard aggregate is inferred here.  In particular, the local
AUPRC implementation is non-interpolated average precision, whose equivalence
to the competition evaluator has not been established.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .common import HarnessError, sha256_file


METRICS = {
    "MAE": ("regression", "mean_absolute_error", "minimize"),
    "Spearman": ("regression", "pearson_correlation_of_average_ranks", "maximize"),
    "AUROC": ("classification", "mann_whitney_average_ranks", "maximize"),
    "AUPRC": ("classification", "average_precision", "maximize"),
}


def _reject_constant(value: str) -> None:
    raise HarnessError("EVALUATION_NONFINITE_JSON", "Non-finite JSON constants are not accepted.",
                       {"constant": value})


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HarnessError("EVALUATION_DUPLICATE_JSON_FIELD", "Duplicate JSON object field.",
                               {"field": key})
        result[key] = value
    return result


def _load(path: Path) -> tuple[Any, str]:
    try:
        path = Path(path)
    except (TypeError, ValueError) as exc:
        raise HarnessError("EVALUATION_INVALID_PATH", "Expected a filesystem path.") from exc
    try:
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if sha256_file(path) != digest:
            raise HarnessError("EVALUATION_SOURCE_CHANGED", "Input changed while being read.")
        data = json.loads(payload.decode("utf-8-sig"), parse_constant=_reject_constant,
                          object_pairs_hook=_unique_object)
        return data, digest
    except HarnessError as exc:
        details = {"path": str(path)}
        if isinstance(exc.details, dict):
            details.update(exc.details)
        raise HarnessError(exc.code, exc.message, details) from exc
    except json.JSONDecodeError as exc:
        raise HarnessError("EVALUATION_INVALID_JSON", exc.msg,
                           {"path": str(path), "line_number": exc.lineno,
                            "column_number": exc.colno}) from exc
    except (OSError, ValueError, RecursionError) as exc:
        raise HarnessError("EVALUATION_INPUT_READ_ERROR", str(exc), {"path": str(path)}) from exc


def _schema(data: Any) -> tuple[dict[str, dict[str, str]], str]:
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list) or not data["tasks"]:
        raise HarnessError("EVALUATION_SCHEMA_SHAPE", "Task schema must contain a nonempty tasks array.")
    if "schema_version" in data and (type(data["schema_version"]) is not int
                                     or data["schema_version"] != 1):
        raise HarnessError("EVALUATION_SCHEMA_VERSION", "Only task schema version 1 is supported.")
    label_status = data.get("label_contract_status", "unconfirmed")
    if not isinstance(label_status, str) or not label_status.strip():
        raise HarnessError("EVALUATION_LABEL_STATUS", "label_contract_status must be a nonempty string.")
    tasks: dict[str, dict[str, str]] = {}
    for index, item in enumerate(data["tasks"]):
        location = {"task_index": index}
        if not isinstance(item, dict):
            raise HarnessError("EVALUATION_TASK_SHAPE", "Each task definition must be an object.", location)
        for field in ("task", "kind", "metric"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise HarnessError("EVALUATION_TASK_FIELD", "Task, kind and metric must be nonempty strings.",
                                   {**location, "field": field})
        name, metric, kind = item["task"], item["metric"], item["kind"]
        if name in tasks:
            raise HarnessError("EVALUATION_DUPLICATE_TASK", "Task schema repeats a task name.",
                               {**location, "task": name})
        if metric not in METRICS:
            raise HarnessError("EVALUATION_UNKNOWN_METRIC", "Unsupported local metric.",
                               {**location, "task": name, "metric": metric})
        if kind != METRICS[metric][0]:
            raise HarnessError("EVALUATION_TASK_KIND", "Task kind does not match its metric.",
                               {**location, "task": name, "kind": kind, "metric": metric})
        task_label_status = item.get("label_status", label_status)
        if not isinstance(task_label_status, str) or not task_label_status.strip():
            raise HarnessError("EVALUATION_LABEL_STATUS", "label_status must be a nonempty string.",
                               {**location, "task": name})
        tasks[name] = {"kind": kind, "metric": metric, "label_contract_status": task_label_status}
    return tasks, label_status


def _number(value: Any, location: dict[str, Any]) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise HarnessError("EVALUATION_NOT_NUMBER", "Labels and predictions must be JSON numbers.", location)
    try:
        number = float(value)
    except (ValueError, OverflowError) as exc:
        raise HarnessError("EVALUATION_NOT_FINITE", "Number cannot be represented as a finite float.", location) from exc
    if not math.isfinite(number):
        raise HarnessError("EVALUATION_NOT_FINITE", "NaN and infinity are not accepted.", location)
    return number


def _records(data: Any, tasks: dict[str, dict[str, str]]) -> tuple[str, dict[str, list[tuple[float, float]]], dict[str, int]]:
    if not isinstance(data, dict):
        raise HarnessError("EVALUATION_RECORDS_SHAPE", "Evaluation input must be a JSON object.")
    expected = {"schema_version", "split_id", "records"}
    if set(data) != expected:
        raise HarnessError("EVALUATION_RECORDS_FIELDS", "Evaluation input has missing or unknown fields.",
                           {"missing": sorted(expected - set(data)), "unknown": sorted(set(data) - expected)})
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise HarnessError("EVALUATION_RECORDS_VERSION", "Only evaluation schema_version 1 is supported.")
    if not isinstance(data["split_id"], str) or not data["split_id"].strip():
        raise HarnessError("EVALUATION_SPLIT_ID", "split_id must be a nonempty string.")
    if not isinstance(data["records"], list):
        raise HarnessError("EVALUATION_RECORD_LIST", "records must be a JSON array.")
    pairs: dict[str, list[tuple[float, float]]] = {name: [] for name in tasks}
    missing = {name: 0 for name in tasks}
    seen: dict[tuple[str, str], int] = {}
    for index, record in enumerate(data["records"]):
        location = {"record_index": index}
        if not isinstance(record, dict):
            raise HarnessError("EVALUATION_RECORD_SHAPE", "Each record must be a JSON object.", location)
        fields = {"task", "sample_id", "y_true", "y_pred"}
        if set(record) != fields:
            raise HarnessError("EVALUATION_RECORD_FIELDS", "Record has missing or unknown fields.",
                               {**location, "missing": sorted(fields - set(record)),
                                "unknown": sorted(set(record) - fields)})
        for field in ("task", "sample_id"):
            if not isinstance(record[field], str) or not record[field].strip():
                raise HarnessError("EVALUATION_RECORD_ID", "Task and sample_id must be nonempty strings.",
                                   {**location, "field": field})
        name, sample_id = record["task"], record["sample_id"]
        location.update({"task": name, "sample_id": sample_id})
        if name not in tasks:
            raise HarnessError("EVALUATION_UNKNOWN_TASK", "Record task is absent from the supplied schema.", location)
        key = (name, sample_id)
        if key in seen:
            raise HarnessError("EVALUATION_DUPLICATE_SAMPLE", "The (task, sample_id) key must be unique.",
                               {**location, "first_record_index": seen[key]})
        seen[key] = index
        prediction = _number(record["y_pred"], {**location, "field": "y_pred"})
        if record["y_true"] is None:
            missing[name] += 1
            continue
        truth = _number(record["y_true"], {**location, "field": "y_true"})
        if tasks[name]["kind"] == "classification" and truth not in (0.0, 1.0):
            raise HarnessError("EVALUATION_BINARY_LABEL", "Classification labels must be 0 or 1; missing is null.",
                               {**location, "field": "y_true", "value": truth})
        pairs[name].append((truth, prediction))
    return data["split_id"], pairs, missing


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        stop = start + 1
        while stop < len(order) and values[order[stop]] == values[order[start]]:
            stop += 1
        rank = (start + 1 + stop) / 2.0
        for position in range(start, stop):
            ranks[order[position]] = rank
        start = stop
    return ranks


def _mae(pairs: list[tuple[float, float]]) -> float:
    errors = [abs(truth - prediction) for truth, prediction in pairs]
    if all(math.isfinite(error) for error in errors):
        scale = max(errors)
        return 0.0 if scale == 0.0 else scale * (math.fsum(error / scale for error in errors) / len(errors))
    # Finite operands can overflow on subtraction. Scale first in that case;
    # an unrepresentable final result is rejected by the caller.
    scale = max(abs(value) for pair in pairs for value in pair)
    return scale * (math.fsum(abs(truth / scale - prediction / scale)
                             for truth, prediction in pairs) / len(pairs))


def _spearman(pairs: list[tuple[float, float]]) -> float:
    left = _average_ranks([truth for truth, _ in pairs])
    right = _average_ranks([prediction for _, prediction in pairs])
    mean = (len(pairs) + 1) / 2.0
    left = [value - mean for value in left]
    right = [value - mean for value in right]
    covariance = math.fsum(x * y for x, y in zip(left, right))
    result = covariance / math.sqrt(math.fsum(x * x for x in left)) / math.sqrt(math.fsum(y * y for y in right))
    return max(-1.0, min(1.0, result))


def _auroc(pairs: list[tuple[float, float]]) -> float:
    positive = sum(truth == 1.0 for truth, _ in pairs)
    negative = len(pairs) - positive
    ranks = _average_ranks([prediction for _, prediction in pairs])
    rank_sum = math.fsum(rank for rank, (truth, _) in zip(ranks, pairs) if truth == 1.0)
    return (rank_sum - positive * (positive + 1) / 2.0) / (positive * negative)


def _average_precision(pairs: list[tuple[float, float]]) -> float:
    ordered = sorted(pairs, key=lambda pair: pair[1], reverse=True)
    positives = sum(truth == 1.0 for truth, _ in pairs)
    start = cumulative_positive = 0
    terms = []
    while start < len(ordered):
        stop = start + 1
        while stop < len(ordered) and ordered[stop][1] == ordered[start][1]:
            stop += 1
        group_positive = sum(truth == 1.0 for truth, _ in ordered[start:stop])
        cumulative_positive += group_positive
        terms.append((group_positive / positives) * (cumulative_positive / stop))
        start = stop
    return math.fsum(terms)


def _task_result(task: dict[str, str], pairs: list[tuple[float, float]], missing: int) -> dict[str, Any]:
    metric = task["metric"]
    result: dict[str, Any] = {
        "kind": task["kind"], "metric": metric, "n": len(pairs), "missing": missing,
        "records": len(pairs) + missing, "status": "undefined", "value": None, "reason": None,
        "local_definition": METRICS[metric][1], "direction": METRICS[metric][2],
        "official_equivalence": "unconfirmed", "label_contract_status": task["label_contract_status"],
    }
    if task["kind"] == "classification":
        result["n_positive"] = sum(truth == 1.0 for truth, _ in pairs)
        result["n_negative"] = len(pairs) - result["n_positive"]
        result["one_class_policy"] = "undefined_for_local_model_comparison"
    if not pairs:
        result["reason"] = "no_labeled_records" if missing else "no_records"
        return result
    if task["kind"] == "classification" and (result["n_positive"] == 0 or result["n_negative"] == 0):
        result["reason"] = "one_class"
        return result
    if metric == "Spearman":
        if len(pairs) < 2:
            result["reason"] = "insufficient_samples"
            return result
        constant_true = len({truth for truth, _ in pairs}) == 1
        constant_pred = len({prediction for _, prediction in pairs}) == 1
        if constant_true or constant_pred:
            result["reason"] = ("constant_true_and_prediction" if constant_true and constant_pred
                                else "constant_true" if constant_true else "constant_prediction")
            return result
    function = {"MAE": _mae, "Spearman": _spearman, "AUROC": _auroc, "AUPRC": _average_precision}[metric]
    try:
        value = function(pairs)
    except (OverflowError, ZeroDivisionError) as exc:
        raise HarnessError("EVALUATION_NUMERIC_ERROR", "Metric could not be computed as a finite number.",
                           {"metric": metric}) from exc
    if not math.isfinite(value):
        raise HarnessError("EVALUATION_NUMERIC_ERROR", "Metric result exceeds finite floating-point range.",
                           {"metric": metric})
    result.update({"status": "ok", "value": value})
    return result


def evaluate_records(task_schema_path: Path, records_path: Path) -> dict[str, Any]:
    """Evaluate supplied local labels; never infer label semantics or total score."""
    schema_data, schema_digest = _load(task_schema_path)
    input_data, records_digest = _load(records_path)
    try:
        tasks, label_status = _schema(schema_data)
    except HarnessError as exc:
        raise HarnessError(exc.code, exc.message,
                           {"path": str(task_schema_path), **(exc.details or {})}) from exc
    try:
        split_id, pairs, missing = _records(input_data, tasks)
    except HarnessError as exc:
        raise HarnessError(exc.code, exc.message,
                           {"path": str(records_path), **(exc.details or {})}) from exc
    results = {}
    for name, task in tasks.items():
        try:
            results[name] = _task_result(task, pairs[name], missing[name])
        except HarnessError as exc:
            raise HarnessError(exc.code, exc.message,
                               {"path": str(records_path), "task": name, **(exc.details or {})}) from exc
    warnings = []
    unconfirmed = [name for name, task in tasks.items() if task["label_contract_status"] != "confirmed"]
    if label_status != "confirmed" or unconfirmed:
        warnings.append({
            "code": "LABEL_CONTRACT_UNCONFIRMED", "label_contract_status": label_status,
            "tasks": unconfirmed,
            "message": "Only supplied numeric records were evaluated. Label meanings, units and transforms "
                       "have not all been confirmed; this does not authorize training.",
        })
    ap_tasks = [name for name, task in tasks.items() if task["metric"] == "AUPRC"]
    if ap_tasks:
        warnings.append({
            "code": "AUPRC_OFFICIAL_DEFINITION_UNCONFIRMED", "tasks": ap_tasks,
            "local_definition": "average_precision", "official_equivalence": "unconfirmed",
            "message": "Local AP groups equal scores at the same threshold and uses no trapezoidal interpolation.",
        })
    return {
        "ok": True, "schema_version": 1, "scope": "local_per_task_metrics_only",
        "split_id": split_id, "label_contract_status": label_status,
        "official_equivalence": "unconfirmed", "record_count": len(input_data["records"]),
        "task_count": len(tasks), "tasks": results, "warnings": warnings,
        "task_schema": {"path": str(task_schema_path), "sha256": schema_digest},
        "records_source": {"path": str(records_path), "sha256": records_digest},
    }
