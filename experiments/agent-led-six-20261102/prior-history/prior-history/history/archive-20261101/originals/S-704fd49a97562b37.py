"""Reviewed inputs, immutable run snapshots and a deliberately narrow Docker runner.

Review records are attestations by the team, not authentication or a security
boundary against a caller that can edit this repository or invoke Docker itself.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
from typing import Any
from urllib.parse import urlparse

from .common import HarnessError, read_json, resolve_inside, sha256_file, write_json

HEX = re.compile(r"^[0-9a-f]{64}$")
RUN_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
ROLES = {"train", "validation", "test", "submission_template"}
CONFIG_KEYS = {"schema_version", "run_id", "phase", "manifest", "task_schema",
               "adapter_dir", "adapter_sha256", "adapter_review", "image",
               "image_review", "seed", "model", "initialization", "checkpoint",
               "limits", "gpus"}
ADAPTER_SUFFIXES = {".py", ".json", ".toml", ".yaml", ".yml", ".txt", ".md"}
SECRET_KEYS = {"password", "secret", "api_key", "access_token", "authorization",
               "credentials", "private_key", "client_secret"}


def _fail(code: str, message: str, **details: Any) -> None:
    raise HarnessError(code, message, details or None)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _object(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        _fail("INVALID_SCHEMA", f"{name} must be an object")
    return value


def _only(value: dict, allowed: set[str], name: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        _fail("UNKNOWN_FIELDS", f"Unknown fields in {name}; options are not silently ignored", fields=unknown)


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail("INVALID_SCHEMA", f"{name} must be a nonempty string")
    return value


def _digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or not HEX.fullmatch(value):
        _fail("INVALID_HASH", f"{name} must be a lowercase SHA-256 digest")
    return value


def _path(root: Path, value: str | Path, exists: bool = True) -> Path:
    """API callers may pass resolved paths; paths *inside JSON* use resolve_inside."""
    root = Path(root).resolve()
    p = Path(value)
    if p.is_absolute():
        try:
            p = p.relative_to(root)
        except ValueError:
            _fail("PATH_OUTSIDE_PROJECT", "Path must be inside this project", path=str(value))
    return resolve_inside(root, p, must_exist=exists)


def _regular(path: Path) -> None:
    if not path.is_file() or path.is_symlink():
        _fail("NOT_REGULAR_FILE", "Expected a regular non-symlink file", path=str(path))
    if path.stat().st_nlink != 1:
        _fail("HARDLINK_REJECTED", "Input or artifact must not be a hard link", path=str(path))


def _review(root: Path, value: Any, name: str, dated: bool = False) -> dict:
    value = _object(value, name)
    _only(value, {"reviewer", "reviewed_at", "evidence"}, name)
    _text(value.get("reviewer"), f"{name}.reviewer")
    if dated:
        _text(value.get("reviewed_at"), f"{name}.reviewed_at")
    evidence = resolve_inside(root, _text(value.get("evidence"), f"{name}.evidence"))
    _regular(evidence)
    if not evidence.stat().st_size:
        _fail("EMPTY_EVIDENCE", "Review evidence cannot be empty", path=str(evidence))
    return value


def _check_manifest(root: Path, manifest_path: str | Path, roles: set[str] | None) -> dict:
    path = _path(root, manifest_path)
    manifest = _object(read_json(path), "manifest")
    _only(manifest, {"schema_version", "dataset_id", "status", "review", "files"}, "manifest")
    if manifest.get("schema_version") != 1:
        _fail("SCHEMA_VERSION", "Manifest schema_version must be 1")
    if manifest.get("status") != "approved":
        _fail("DATA_NOT_APPROVED", "Official data has not been received and reviewed", status=manifest.get("status"))
    _text(manifest.get("dataset_id"), "dataset_id")
    _review(root, manifest.get("review"), "manifest.review", dated=True)
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        _fail("DATA_MISSING", "No official input files have been registered")
    ids, paths, accepted = set(), set(), []
    for i, raw in enumerate(files):
        item = _object(raw, f"files[{i}]")
        _only(item, {"id", "path", "role", "sha256", "source_kind", "source_url", "evidence"}, f"files[{i}]")
        file_id = _text(item.get("id"), "file.id")
        relative = _text(item.get("path"), "file.path")
        canonical = resolve_inside(root, relative, must_exist=False)
        role = item.get("role")
        if file_id in ids or canonical in paths:
            _fail("DUPLICATE_INPUT", "Input IDs and resolved paths must be unique across roles", id=file_id)
        ids.add(file_id)
        paths.add(canonical)
        if role not in ROLES:
            _fail("INVALID_INPUT_ROLE", "Unknown official input role", role=role)
        if item.get("source_kind") != "competition_official":
            _fail("EXTERNAL_DATA_REJECTED", "Only reviewed official raw inputs are admitted", id=file_id)
        url = urlparse(_text(item.get("source_url"), "file.source_url"))
        if url.scheme not in {"http", "https"} or url.hostname not in {"www.aiinnovation.com.cn", "aiinnovation.com.cn"} or url.username:
            _fail("UNCONFIRMED_SOURCE", "Record the official competition source; a URL alone does not prove origin", id=file_id)
        if not canonical.is_relative_to(root / "data" / "official"):
            _fail("INPUT_LOCATION", "Official inputs must be under data/official/", path=relative)
        expected = _digest(item.get("sha256"), "file.sha256")
        # Validate metadata for every row, but don't require unused test files at train time.
        if roles is not None and role not in roles:
            continue
        evidence = resolve_inside(root, _text(item.get("evidence"), "file.evidence"))
        _regular(evidence)
        actual_path = resolve_inside(root, relative)
        _regular(actual_path)
        actual = sha256_file(actual_path)
        if actual != expected:
            _fail("INPUT_HASH_MISMATCH", "Official input changed after registration", id=file_id, expected=expected, actual=actual)
        accepted.append({**item, "path": canonical.relative_to(root).as_posix(), "size_bytes": actual_path.stat().st_size})
    if not accepted:
        _fail("DATA_MISSING", "No registered inputs match this phase", roles=sorted(roles or ROLES))
    return {"ok": True, "dataset_id": manifest["dataset_id"], "manifest": path.relative_to(root).as_posix(),
            "manifest_sha256": sha256_file(path), "files": accepted,
            "review_is_team_attestation": True}


def check_data(root: Path, manifest_path: Path) -> dict:
    """Check all files in an approved raw official-input manifest."""
    return _check_manifest(Path(root).resolve(), manifest_path, None)


def adapter_digest(root: Path, adapter_dir: str | Path) -> dict:
    """Digest canonical JSON of sorted {path, sha256, size_bytes} code records."""
    root = Path(root).resolve()
    directory = _path(root, adapter_dir)
    if not directory.is_dir():
        _fail("ADAPTER_MISSING", "adapter_dir must be a directory")
    files = []
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        if path.is_symlink():
            _fail("SYMLINK_REJECTED", "Adapter cannot contain symlinks", path=str(relative))
        if path.is_dir():
            continue
        _regular(path)
        if any(part.startswith(".") or part == "__pycache__" for part in relative.parts) or path.suffix not in ADAPTER_SUFFIXES:
            _fail("ADAPTER_ASSET_REJECTED", "Keep model weights, caches, credentials and datasets out of the code-only adapter", path=str(relative))
        files.append({"path": relative.as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    if not files:
        _fail("ADAPTER_MISSING", "Adapter directory contains no reviewed code")
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {"sha256": hashlib.sha256(encoded).hexdigest(), "files": files}


def _task_contract(root: Path, value: str) -> tuple[Path, dict]:
    path = resolve_inside(root, value)
    contract = _object(read_json(path), "task_schema")
    if contract.get("label_contract_status") != "confirmed":
        _fail("LABEL_CONTRACT_UNCONFIRMED", "Training label meaning, units, transforms and missing-value rules must be confirmed from official material")
    tasks = contract.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        _fail("INVALID_TASK_SCHEMA", "Confirmed tasks must be a nonempty list")
    seen = set()
    for task in tasks:
        task = _object(task, "task")
        name = _text(task.get("task"), "task.task")
        if name in seen:
            _fail("INVALID_TASK_SCHEMA", "Duplicate task", task=name)
        seen.add(name)
        kind, metric = task.get("kind"), task.get("metric")
        if (kind == "classification" and metric not in {"AUROC", "AUPRC"}) or (kind == "regression" and metric not in {"MAE", "Spearman"}) or kind not in {"classification", "regression"}:
            _fail("INVALID_TASK_SCHEMA", "Task kind and metric are inconsistent", task=name)
        if task.get("label_status") != "confirmed":
            _fail("LABEL_CONTRACT_UNCONFIRMED", "Every selected task needs a confirmed label contract", task=name)
        for field in ("unit", "transform", "missing_encoding"):
            # 'dimensionless', 'identity', and 'none' are explicit valid values; null is unknown.
            value = task.get(field)
            if not isinstance(value, str) or not value.strip():
                _fail("LABEL_CONTRACT_UNCONFIRMED", f"Task {field} must be an explicit nonempty string", task=name)
        if kind == "classification":
            positive = task.get("positive_class")
            if not isinstance(positive, str) or not positive.strip():
                _fail("LABEL_CONTRACT_UNCONFIRMED", "Positive-class semantics must be an explicit nonempty string", task=name)
        evidence = resolve_inside(root, _text(task.get("evidence"), "task.evidence"))
        _regular(evidence)
    return path, contract


def _no_credentials(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.lower().replace("-", "_") in SECRET_KEYS:
                _fail("CREDENTIAL_FIELD_REJECTED", "Credentials do not belong in experiment configuration", field=key)
            _no_credentials(nested)
    elif isinstance(value, list):
        for nested in value:
            _no_credentials(nested)


def _checkpoint(root: Path, value: Any) -> dict:
    value = _object(value, "checkpoint")
    _only(value, {"run_id", "path", "sha256"}, "checkpoint")
    run_id = _text(value.get("run_id"), "checkpoint.run_id")
    if not RUN_ID.fullmatch(run_id):
        _fail("INVALID_RUN_ID", "Invalid checkpoint run_id")
    run_dir = resolve_inside(root, f"runs/{run_id}")
    record_path = resolve_inside(root, f"runs/{run_id}/run.json")
    record = _object(read_json(record_path), "training run")
    if record.get("run_id") != run_id or record.get("phase") != "train" or record.get("status") != "completed":
        _fail("CHECKPOINT_UNVERIFIED", "Checkpoint must come from a completed training run")
    path = resolve_inside(root, _text(value.get("path"), "checkpoint.path"))
    if not path.is_relative_to(run_dir / "artifacts"):
        _fail("CHECKPOINT_UNVERIFIED", "Checkpoint must be an artifact of its claimed training run")
    _regular(path)
    relative = path.relative_to(run_dir).as_posix()
    matches = [item for item in record.get("artifacts", []) if item.get("path") == relative and item.get("kind") == "checkpoint"]
    expected = _digest(value.get("sha256"), "checkpoint.sha256")
    if len(matches) != 1 or matches[0].get("sha256") != expected or sha256_file(path) != expected:
        _fail("CHECKPOINT_HASH_MISMATCH", "Checkpoint does not match the completed training record")
    return {**value, "training_record_sha256": sha256_file(record_path)}


def _limit(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        _fail("INVALID_LIMIT", f"{name} must be an integer between {low} and {high}")
    return value


def plan_run(root: Path, config_path: Path) -> dict:
    """Validate and describe an immutable run. No files or containers are created."""
    root = Path(root).resolve()
    path = _path(root, config_path)
    config = _object(read_json(path), "run config")
    _only(config, CONFIG_KEYS, "run config")
    if config.get("schema_version") != 1:
        _fail("SCHEMA_VERSION", "Run config schema_version must be 1")
    run_id = _text(config.get("run_id"), "run_id")
    if not RUN_ID.fullmatch(run_id):
        _fail("INVALID_RUN_ID", "Use lowercase letters, digits, hyphens or underscores, at most 64 characters")
    phase = config.get("phase")
    if phase not in {"train", "predict"}:
        _fail("INVALID_PHASE", "phase must be train or predict")
    out = resolve_inside(root, f"runs/{run_id}", must_exist=False)
    if out.exists():
        _fail("RUN_EXISTS", "A run_id is immutable; choose a new ID rather than overwrite", run_id=run_id)
    manifest_path = resolve_inside(root, _text(config.get("manifest"), "manifest"))
    roles = {"train", "validation"} if phase == "train" else {"test", "submission_template"}
    data = _check_manifest(root, manifest_path, roles)
    actual_roles = {row["role"] for row in data["files"]}
    if phase == "train" and not {"train", "validation"} <= actual_roles:
        _fail("TRAIN_VALIDATION_REQUIRED", "Formal training requires registered train and validation inputs")
    if phase == "predict" and not actual_roles & {"test", "submission_template"}:
        _fail("TEST_INPUT_REQUIRED", "Prediction requires registered official test/template input")
    task_path, _ = _task_contract(root, _text(config.get("task_schema"), "task_schema"))
    adapter_path = resolve_inside(root, _text(config.get("adapter_dir"), "adapter_dir"))
    code = adapter_digest(root, adapter_path)
    if code["sha256"] != _digest(config.get("adapter_sha256"), "adapter_sha256"):
        _fail("ADAPTER_HASH_MISMATCH", "Adapter changed after review", actual=code["sha256"])
    entry = adapter_path / f"{phase}.py"
    _regular(entry)
    _review(root, config.get("adapter_review"), "adapter_review")
    image = _text(config.get("image"), "image")
    if not image.startswith("sha256:") or not HEX.fullmatch(image[7:]):
        _fail("IMAGE_NOT_PINNED", "Use an already-built local image ID: sha256:<64 lowercase hex>")
    _review(root, config.get("image_review"), "image_review")
    if config.get("initialization") != "random":
        _fail("INITIALIZATION_REJECTED", "Current team policy requires random-initialized training; external weights need a reviewed policy change")
    if phase == "train" and config.get("checkpoint") is not None:
        _fail("INITIALIZATION_REJECTED", "Training must start without a checkpoint under current policy")
    checkpoint = _checkpoint(root, config.get("checkpoint")) if phase == "predict" else None
    seed = _limit(config.get("seed"), "seed", 0, 2**32 - 1)
    model = _object(config.get("model"), "model")
    _no_credentials(model)
    limits = _object(config.get("limits", {}), "limits")
    _only(limits, {"cpus", "memory_mb", "pids", "timeout_seconds"}, "limits")
    bounded = {"cpus": _limit(limits.get("cpus", 2), "cpus", 1, 128),
               "memory_mb": _limit(limits.get("memory_mb", 4096), "memory_mb", 256, 1048576),
               "pids": _limit(limits.get("pids", 256), "pids", 16, 4096),
               "timeout_seconds": _limit(limits.get("timeout_seconds", 3600), "timeout_seconds", 1, 604800)}
    gpus = _limit(config.get("gpus", 0), "gpus", 0, 8)
    uid = os.getuid() if hasattr(os, "getuid") and os.getuid() != 0 else 65532
    gid = os.getgid() if uid != 65532 and hasattr(os, "getgid") else 65532
    snapshot, artifacts = out / "snapshot", out / "artifacts"
    mounts = [{"source": str(snapshot / "adapter"), "target": "/adapter", "readonly": True},
              {"source": str(snapshot / "inputs"), "target": "/inputs", "readonly": True},
              {"source": str(snapshot / "control"), "target": "/control", "readonly": True},
              {"source": str(artifacts), "target": "/output", "readonly": False}]
    if checkpoint:
        mounts.append({"source": str(snapshot / "checkpoint"), "target": "/checkpoint", "readonly": True})
    command = ["docker", "run", "--rm", "--name", f"admet-{run_id}", "--pull", "never", "--network", "none", "--read-only",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--user", f"{uid}:{gid}",
               "--cpus", str(bounded["cpus"]), "--memory", f"{bounded['memory_mb']}m", "--pids-limit", str(bounded["pids"]),
               "--tmpfs", "/tmp:rw,nosuid,nodev,size=512m,mode=1777", "--workdir", "/adapter",
               "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "HF_HUB_OFFLINE=1", "--env", "TRANSFORMERS_OFFLINE=1",
               "--env", "HF_HUB_CACHE=/tmp/cache/huggingface", "--env", "TORCH_HOME=/tmp/cache/torch",
               "--env", "XDG_CACHE_HOME=/tmp/cache", "--env", "PYTHONHASHSEED=" + str(seed)]
    if gpus:
        command.extend(["--gpus", str(gpus)])
    for mount in mounts:
        if "," in mount["source"] or "\n" in mount["source"]:
            _fail("UNSUPPORTED_PATH", "Docker bind sources cannot contain comma or newline")
        spec = f"type=bind,src={mount['source']},dst={mount['target']}" + (",readonly" if mount["readonly"] else "")
        command.extend(["--mount", spec])
    command.extend(["--entrypoint", "python3", image, f"/adapter/{phase}.py", "--inputs", "/control/inputs.json",
                    "--config", "/control/model.json", "--output", "/output"])
    if checkpoint:
        command.extend(["--checkpoint", "/checkpoint/model"])
    return {"ok": True, "run_id": run_id, "phase": phase, "run_dir": out.relative_to(root).as_posix(),
            "config": path.relative_to(root).as_posix(), "config_sha256": sha256_file(path), "data": data,
            "task_schema": task_path.relative_to(root).as_posix(), "task_schema_sha256": sha256_file(task_path),
            "adapter": {"path": adapter_path.relative_to(root).as_posix(), **code}, "image": image,
            "checkpoint": checkpoint, "seed": seed, "limits": bounded, "uid": uid, "gid": gid,
            "mounts": mounts, "command": command, "isolation_runtime_tested": False,
            "review_is_team_attestation": True, "host_agent_permissions_enforced": False}


def _copy_checked(source: Path, destination: Path, expected: str) -> None:
    _regular(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if sha256_file(destination) != expected:
        _fail("SNAPSHOT_HASH_MISMATCH", "Input changed while creating run snapshot", path=str(source))
    destination.chmod(0o444)


def _snapshots(root: Path, plan: dict, run_dir: Path) -> list[dict]:
    snap = run_dir / "snapshot"
    for folder in ("adapter", "inputs", "control"):
        (snap / folder).mkdir(parents=True)
    for key, target in (("config", "config.json"), ("task_schema", "task_schema.json")):
        _copy_checked(root / plan[key], snap / target, plan[f"{key}_sha256"])
    # Parse only the already-verified frozen bytes, never a second mutable source read.
    config = _object(read_json(snap / "config.json"), "frozen config")
    _copy_checked(root / plan["data"]["manifest"], snap / "manifest.json", plan["data"]["manifest_sha256"])
    for item in plan["adapter"]["files"]:
        _copy_checked(root / plan["adapter"]["path"] / item["path"], snap / "adapter" / item["path"], item["sha256"])
    inputs = []
    for i, item in enumerate(plan["data"]["files"]):
        name = f"{i:03d}_{item['role']}{Path(item['path']).suffix}"
        _copy_checked(root / item["path"], snap / "inputs" / name, item["sha256"])
        inputs.append({"id": item["id"], "role": item["role"], "path": f"/inputs/{name}", "sha256": item["sha256"]})
    write_json(snap / "control" / "inputs.json", {"schema_version": 1, "dataset_id": plan["data"]["dataset_id"], "files": inputs})
    write_json(snap / "control" / "model.json", {"schema_version": 1, "run_id": plan["run_id"], "phase": plan["phase"],
               "seed": plan["seed"], "model": config["model"], "task_schema": read_json(snap / "task_schema.json")})
    if plan["checkpoint"]:
        _copy_checked(root / plan["checkpoint"]["path"], snap / "checkpoint" / "model", plan["checkpoint"]["sha256"])
    # Host umask may be 077 and host UID may be 0, while the worker is non-root.
    # Every directory visible through the read-only binds must be traversable.
    snap.chmod(0o755)
    records = []
    for path in sorted(snap.rglob("*")):
        if path.is_dir():
            path.chmod(0o755)
        elif path.is_file():
            path.chmod(0o444)
            records.append({"path": path.relative_to(run_dir).as_posix(), "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return records


def _collect_outputs(run_dir: Path, phase: str) -> list[dict]:
    artifacts = run_dir / "artifacts"
    result_path = resolve_inside(artifacts, "result.json")
    _regular(result_path)
    result = _object(read_json(result_path), "adapter result")
    fields = {"checkpoint", "metrics"} if phase == "train" else {"predictions"}
    _only(result, {"schema_version", "phase"} | fields, "adapter result")
    if result.get("schema_version") != 1 or result.get("phase") != phase:
        _fail("INVALID_ADAPTER_RESULT", "Result phase/schema_version must match this run")
    records = [{"path": "artifacts/result.json", "kind": "result", "sha256": sha256_file(result_path), "size_bytes": result_path.stat().st_size}]
    used = {result_path}
    for kind in sorted(fields):
        name = _text(result.get(kind), f"result.{kind}")
        path = resolve_inside(artifacts, name)
        if path in used:
            _fail("INVALID_ADAPTER_RESULT", "Declared output paths must resolve to distinct files")
        used.add(path)
        _regular(path)
        if not path.stat().st_size:
            _fail("EMPTY_ARTIFACT", "Model outputs cannot be empty", artifact=name)
        if kind == "metrics":
            _object(read_json(path), "metrics")
        if kind == "predictions" and path.suffix != ".json":
            _fail("INVALID_ADAPTER_RESULT", "Prediction adapter must emit a JSON records file")
        records.append({"path": path.relative_to(run_dir).as_posix(), "kind": kind, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return records


def _remove_container(run_id: str) -> dict:
    try:
        result = subprocess.run(["docker", "rm", "--force", f"admet-{run_id}"], capture_output=True, text=True, timeout=30, check=False)
        return {"attempted": True, "exit_code": result.returncode, "stderr": result.stderr[-2000:]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"attempted": True, "error": str(exc), "exception_type": type(exc).__name__}


def execute_run(root: Path, config_path: Path) -> dict:
    root = Path(root).resolve()
    plan = plan_run(root, config_path)
    if shutil.which("docker") is None:
        _fail("DOCKER_UNAVAILABLE", "Docker is required for formal runs; no host-shell fallback is permitted")
    try:
        inspected = subprocess.run(["docker", "image", "inspect", plan["image"]], capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        _fail("DOCKER_UNAVAILABLE", str(exc), exception_type=type(exc).__name__)
    if inspected.returncode:
        _fail("IMAGE_UNAVAILABLE", "Reviewed local image cannot be inspected; no image pull is attempted", exit_code=inspected.returncode, stderr=inspected.stderr[-8000:])
    try:
        inspected_image = json.loads(inspected.stdout)[0]
        if inspected_image["Id"] != plan["image"]:
            _fail("IMAGE_ID_MISMATCH", "Docker image ID does not match the reviewed image")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        _fail("IMAGE_INSPECT_INVALID", "Docker image inspection returned an invalid response", exception_type=type(exc).__name__)
    run_dir = root / plan["run_dir"]
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        _fail("RUN_EXISTS", "Another process claimed this run_id")
    record = {"schema_version": 1, "run_id": plan["run_id"], "phase": plan["phase"], "status": "preparing",
              "started_at": _now(), "image": plan["image"], "image_created": inspected_image.get("Created"),
              "config_sha256": plan["config_sha256"], "data_manifest_sha256": plan["data"]["manifest_sha256"],
              "adapter_sha256": plan["adapter"]["sha256"], "checkpoint": plan["checkpoint"],
              "snapshots": [], "artifacts": [], "isolation_runtime_tested": False,
              "host_agent_permissions_enforced": False}
    write_json(run_dir / "run.json", record)
    try:
        write_json(run_dir / "plan.json", plan)
        record["snapshots"] = _snapshots(root, plan, run_dir)
        output = run_dir / "artifacts"
        output.mkdir(mode=0o700)
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            try:
                os.chown(output, plan["uid"], plan["gid"])
            except OSError as exc:
                _fail("OUTPUT_OWNERSHIP_UNAVAILABLE", "Cannot give the non-root worker its private output directory; use a supported local filesystem or a non-root host account", exception_type=type(exc).__name__, errno=exc.errno)
        (run_dir / "logs").mkdir()
        record["status"] = "running"
        write_json(run_dir / "run.json", record)
        with (run_dir / "logs" / "stdout.log").open("wb") as stdout, (run_dir / "logs" / "stderr.log").open("wb") as stderr:
            try:
                process = subprocess.run(plan["command"], stdout=stdout, stderr=stderr, timeout=plan["limits"]["timeout_seconds"], check=False)
            except subprocess.TimeoutExpired as exc:
                # Killing the Docker client alone does not guarantee the container stopped.
                cleanup = _remove_container(plan["run_id"])
                _fail("RUN_TIMEOUT", "Run exceeded timeout; inspect container cleanup result", cleanup=cleanup, timeout_seconds=exc.timeout)
            except KeyboardInterrupt:
                cleanup = _remove_container(plan["run_id"])
                _fail("RUN_CANCELLED", "Run was interrupted; inspect container cleanup result", cleanup=cleanup)
        record["exit_code"] = process.returncode
        if process.returncode:
            _fail("ADAPTER_FAILED", "Container adapter exited nonzero; inspect run logs", exit_code=process.returncode, logs=f"{plan['run_dir']}/logs")
        record["artifacts"] = _collect_outputs(run_dir, plan["phase"])
        record["status"] = "completed"
        record["completed_at"] = _now()
        # A successful launch is not an independent network-isolation penetration test.
        record["docker_execution_completed"] = True
        write_json(run_dir / "run.json", record)
    except Exception as exc:
        record["status"] = "failed"
        record["completed_at"] = _now()
        record["error"] = exc.as_dict() if isinstance(exc, HarnessError) else {"code": "RUNTIME_ERROR", "message": str(exc), "exception_type": type(exc).__name__}
        write_json(run_dir / "run.json", record)
        if isinstance(exc, HarnessError):
            raise
        raise HarnessError("RUNTIME_ERROR", str(exc), {"exception_type": type(exc).__name__, "run_dir": plan["run_dir"]}) from exc
    return {"ok": True, "run_id": plan["run_id"], "run_dir": plan["run_dir"], "status": record["status"], "artifacts": record["artifacts"], "isolation_runtime_tested": False}


def bundle_run(root: Path, run_dir: Path, output_path: Path) -> dict:
    """Create a local audit archive of recorded code/control/output files, never raw inputs."""
    root = Path(root).resolve()
    directory = _path(root, run_dir)
    if directory.parent != root / "runs" or not RUN_ID.fullmatch(directory.name):
        _fail("INVALID_RUN_LOCATION", "Bundle exactly one runs/<run_id> directory")
    record = _object(read_json(directory / "run.json"), "run record")
    if record.get("status") != "completed" or record.get("run_id") != directory.name:
        _fail("RUN_NOT_COMPLETED", "Only completed, consistently identified runs can be bundled")
    output = _path(root, output_path, exists=False)
    if not output.is_relative_to(root / "deliverables") or not output.name.endswith(".tar.gz"):
        _fail("INVALID_BUNDLE_PATH", "Use a new deliverables/*.tar.gz path")
    if output.exists():
        _fail("OUTPUT_EXISTS", "Will not overwrite an existing audit bundle")
    snapshots = record.get("snapshots")
    artifacts = record.get("artifacts")
    if not isinstance(snapshots, list) or not snapshots or not isinstance(artifacts, list) or not artifacts:
        _fail("INCOMPLETE_RUN_RECORD", "Run needs recorded snapshots and output artifacts")
    files: dict[str, Path] = {}
    for item in snapshots + artifacts:
        item = _object(item, "recorded file")
        relative = _text(item.get("path"), "recorded path")
        p = Path(relative)
        allowed_control = relative in {"snapshot/config.json", "snapshot/manifest.json", "snapshot/task_schema.json", "snapshot/control/inputs.json", "snapshot/control/model.json"}
        allowed_code = p.is_relative_to("snapshot/adapter") and p.suffix in ADAPTER_SUFFIXES and not any(part.startswith(".") for part in p.parts)
        allowed_artifact = item in artifacts and p.is_relative_to("artifacts") and item.get("kind") in {"result", "checkpoint", "metrics", "predictions"}
        # Input and parent-checkpoint bytes are deliberately not copied to an audit archive.
        raw_input = p.is_relative_to("snapshot/inputs") or p.is_relative_to("snapshot/checkpoint")
        path = resolve_inside(directory, relative)
        _regular(path)
        if sha256_file(path) != _digest(item.get("sha256"), "recorded sha256"):
            _fail("ARTIFACT_HASH_MISMATCH", "Recorded run bytes changed", path=relative)
        if raw_input:
            continue
        if not (allowed_control or allowed_code or allowed_artifact):
            _fail("BUNDLE_FILE_REJECTED", "Record attempts to include a file outside the audit allowlist", path=relative)
        files[relative] = path
    for relative in ("run.json", "plan.json", "logs/stdout.log", "logs/stderr.log"):
        path = resolve_inside(directory, relative)
        _regular(path)
        files[relative] = path
    index = [{"path": name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size} for name, path in sorted(files.items())]
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        stream = output.open("xb")
    except FileExistsError:
        _fail("OUTPUT_EXISTS", "Another process created this audit bundle; it was left untouched")
    try:
        with stream, tarfile.open(fileobj=stream, mode="w:gz") as archive:
            import io
            index_bytes = (json.dumps({"schema_version": 1, "run_id": directory.name, "files": index,
                                      "raw_inputs_included": False, "is_official_required_format": False}, ensure_ascii=False, indent=2) + "\n").encode()
            info = tarfile.TarInfo("BUNDLE_INDEX.json")
            info.size, info.mode = len(index_bytes), 0o644
            archive.addfile(info, io.BytesIO(index_bytes))
            for name, path in sorted(files.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mode = path.stat().st_size, 0o644
                with path.open("rb") as source:
                    archive.addfile(info, source)
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return {"ok": True, "path": output.relative_to(root).as_posix(), "sha256": sha256_file(output),
            "file_count": len(index) + 1, "raw_inputs_included": False,
            "is_official_required_format": False, "training_reproduced": False}
