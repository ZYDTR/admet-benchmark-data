"""Cross-check a candidate against local, completed prediction/training records."""
from __future__ import annotations

import csv
from pathlib import Path
import re

from .common import HarnessError, read_json, resolve_inside, sha256_file
from .submission import validate_submission


def _path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise HarnessError("CANDIDATE_SCHEMA", "Evidence path must be a nonempty string")
    path = Path(value)
    if path.is_absolute():
        try:
            path = path.relative_to(root.resolve())
        except ValueError as exc:
            raise HarnessError("PATH_OUTSIDE_PROJECT", "Candidate evidence is outside this project", {"path": value}) from exc
    return resolve_inside(root, path)


def _object(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise HarnessError("CANDIDATE_SCHEMA", f"{label} must be an object")
    return value


def _record(root: Path, run_id: object, phase: str) -> tuple[Path, dict]:
    if not isinstance(run_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", run_id):
        raise HarnessError("CANDIDATE_RUN_ID", "Invalid run identifier")
    directory = resolve_inside(root, f"runs/{run_id}")
    record = _object(read_json(directory / "run.json"), "run")
    if record.get("run_id") != run_id or record.get("phase") != phase or record.get("status") != "completed":
        raise HarnessError("CANDIDATE_RUN_INCOMPLETE", "Candidate needs a matching completed run", {"run_id": run_id, "phase": phase})
    return directory, record


def _artifact(directory: Path, record: dict, path: Path, kind: str) -> str:
    try:
        relative = path.relative_to(directory).as_posix()
    except ValueError as exc:
        raise HarnessError("CANDIDATE_ARTIFACT", "Artifact belongs to a different run") from exc
    artifacts = record.get("artifacts")
    if not isinstance(artifacts, list) or not all(isinstance(x, dict) for x in artifacts):
        raise HarnessError("CANDIDATE_SCHEMA", "Run artifact list is malformed")
    matches = [x for x in artifacts if x.get("path") == relative and x.get("kind") == kind]
    digest = sha256_file(path)
    if len(matches) != 1 or matches[0].get("sha256") != digest:
        raise HarnessError("CANDIDATE_ARTIFACT", "Artifact bytes do not match its completed run", {"path": relative, "kind": kind})
    return digest


def _snapshot(directory: Path, record: dict, relative: str) -> Path:
    snapshots = record.get("snapshots")
    if not isinstance(snapshots, list) or not all(isinstance(x, dict) for x in snapshots):
        raise HarnessError("CANDIDATE_SNAPSHOT_UNVERIFIED", "Prediction run must record its frozen inputs")
    matches = [x for x in snapshots if x.get("path") == relative]
    path = resolve_inside(directory, relative)
    if len(matches) != 1 or sha256_file(path) != matches[0].get("sha256"):
        raise HarnessError("CANDIDATE_SNAPSHOT_CHANGED", "Frozen prediction evidence differs from its run record", {"path": relative})
    return path


def _template_in_frozen_inputs(directory: Path, record: dict, template_hash: str) -> str:
    control = _object(read_json(_snapshot(directory, record, "snapshot/control/inputs.json")), "frozen inputs")
    manifest_path = _snapshot(directory, record, "snapshot/manifest.json")
    manifest = _object(read_json(manifest_path), "frozen manifest")
    if manifest.get("status") != "approved" or record.get("data_manifest_sha256") != sha256_file(manifest_path):
        raise HarnessError("CANDIDATE_SNAPSHOT_UNVERIFIED", "Frozen manifest is not the one admitted by this prediction run")
    control_files, manifest_files = control.get("files"), manifest.get("files")
    if not isinstance(control_files, list) or not isinstance(manifest_files, list):
        raise HarnessError("CANDIDATE_SCHEMA", "Frozen input lists are malformed")
    matches = [x for x in control_files if isinstance(x, dict) and x.get("role") in {"test", "submission_template"} and x.get("sha256") == template_hash]
    for item in matches:
        container_path = item.get("path")
        if not isinstance(container_path, str) or not container_path.startswith("/inputs/"):
            raise HarnessError("CANDIDATE_SCHEMA", "Frozen input path must point into /inputs/")
        relative = "snapshot/inputs/" + container_path[len("/inputs/"):]
        frozen = _snapshot(directory, record, relative)
        parents = [x for x in manifest_files if isinstance(x, dict) and x.get("id") == item.get("id") and
                   x.get("role") == item.get("role") and x.get("sha256") == template_hash and
                   x.get("source_kind") == "competition_official"]
        if len(parents) == 1 and sha256_file(frozen) == template_hash:
            return item["id"]
    raise HarnessError("CANDIDATE_TEMPLATE_UNREGISTERED", "Candidate template was not among the hash-verified frozen prediction inputs")


def verify_candidate(root: Path, submission_path: Path) -> dict:
    root = root.resolve()
    submission = _path(root, str(submission_path))
    sidecar_path = _path(root, str(submission) + ".provenance.json")
    sidecar = _object(read_json(sidecar_path), "provenance")
    actual = sha256_file(submission)
    declared_submission = _object(sidecar.get("submission"), "submission")
    if declared_submission.get("sha256") != actual:
        raise HarnessError("CANDIDATE_CHANGED", "Candidate CSV changed since export")
    template_info = _object(sidecar.get("template"), "template")
    records_info = _object(sidecar.get("prediction_records"), "prediction_records")
    template = _path(root, template_info.get("path"))
    predictions = _path(root, records_info.get("path"))
    if sha256_file(template) != template_info.get("sha256") or sha256_file(predictions) != records_info.get("sha256"):
        raise HarnessError("CANDIDATE_SOURCE_CHANGED", "Template or prediction records changed since export")
    validation = validate_submission(template, submission, sidecar.get("prediction_kind", "score"))
    predict_dir, predict_record = _record(root, sidecar.get("run_id"), "predict")
    _artifact(predict_dir, predict_record, predictions, "predictions")
    checkpoint = _object(predict_record.get("checkpoint"), "checkpoint")
    train_dir, train_record = _record(root, checkpoint.get("run_id"), "train")
    weight_path = _path(root, checkpoint.get("path"))
    weight_hash = _artifact(train_dir, train_record, weight_path, "checkpoint")
    if checkpoint.get("sha256") != weight_hash or sidecar.get("model_artifact_sha256") != weight_hash:
        raise HarnessError("CANDIDATE_MODEL_MISMATCH", "Declared model differs from the actual training artifact")
    if checkpoint.get("training_record_sha256") != sha256_file(train_dir / "run.json"):
        raise HarnessError("CANDIDATE_TRAIN_RECORD_CHANGED", "Parent training record changed after prediction was planned")
    frozen_template_id = _template_in_frozen_inputs(predict_dir, predict_record, template_info.get("sha256"))
    plan = _object(read_json(predict_dir / "plan.json"), "prediction plan")
    if plan.get("run_id") != predict_record["run_id"] or plan.get("phase") != "predict":
        raise HarnessError("CANDIDATE_PLAN_MISMATCH", "Prediction plan identity differs from the completed run")
    plan_data = _object(plan.get("data"), "plan.data")
    files = plan_data.get("files")
    if not isinstance(files, list) or not any(isinstance(x, dict) and x.get("id") == frozen_template_id and x.get("role") in {"test", "submission_template"} and x.get("sha256") == template_info.get("sha256") for x in files):
        raise HarnessError("CANDIDATE_TEMPLATE_UNREGISTERED", "Template is not among this prediction run's reviewed inputs")
    source = _object(read_json(predictions), "predictions")
    source_hash = source.get("model_artifact_sha256")
    if source.get("run_id") != sidecar.get("run_id") or not isinstance(source_hash, str) or source_hash.lower() != weight_hash:
        raise HarnessError("CANDIDATE_RECORD_IDENTITY", "Prediction payload identifies a different run or model")
    try:
        rows = source["predictions"]
        mapping = {(x["task"], x["sample_idx"]): x["y_pred"] for x in rows}
        if len(mapping) != len(rows):
            raise ValueError("duplicate prediction keys")
        with submission.open(encoding="utf-8-sig", newline="") as stream:
            output_rows = list(csv.DictReader(stream))
        if len(mapping) != len(output_rows):
            raise ValueError("coverage differs")
        for row in output_rows:
            expected = mapping[(row["task"], row["sample_idx"])]
            # Export normalizes JSON numeric values through float(); verify the
            # same representation instead of comparing a float to an exact int.
            if type(expected) not in (int, float) or float(row["y_pred"]) != float(expected):
                raise ValueError(f"prediction changed for {(row['task'], row['sample_idx'])}")
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise HarnessError("CANDIDATE_VALUES_DIFFER", "CSV must contain the recorded model outputs", {"reason": str(exc)}) from exc
    return {"ok": True, "submission_sha256": actual, "prediction_run": predict_record["run_id"],
            "training_run": train_record["run_id"], "model_artifact_sha256": weight_hash,
            "row_count": validation["row_count"], "local_lineage_consistent": True,
            "historical_external_data_use_proven": False, "official_acceptance": "not_checked",
            "scope": "Local records and bytes are consistent; independent source/model review remains necessary."}
