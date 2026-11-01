"""Progressive context discovery and compare-and-swap task handoffs."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import unquote

from .common import HarnessError, read_json, resolve_inside, sha256_file, write_json

SLUG = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _links(path: Path) -> list[str]:
    text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
    return MARKDOWN_LINK.findall(text)


def _skills(root: Path) -> dict[str, Path]:
    return {p.parent.name: p for p in (root / "skills").glob("*/SKILL.md")}


def status(root: Path) -> dict:
    state = read_json(root / "context/state.json")
    tasks = []
    for path in sorted((root / "context/tasks").glob("*.json")):
        value = read_json(path)
        tasks.append({key: value.get(key) for key in ("task_id", "revision", "owner", "status", "goal", "next_action", "blockers")})
    return {"ok": True, "state": state, "tasks": tasks,
            "note": "Persisted context, not a fresh data or runtime audit. Use doctor/check-data before running."}


def get_context(root: Path, skill: str) -> dict:
    paths = _skills(root)
    if skill not in paths:
        raise HarnessError("UNKNOWN_SKILL", "Choose a skill from skills/INDEX.md", {"requested": skill, "available": sorted(paths)})
    path = paths[skill]
    index = (root / "skills/INDEX.md").read_text(encoding="utf-8")
    if f"{skill}/SKILL.md" not in index:
        raise HarnessError("UNINDEXED_SKILL", "Skill exists but is not discoverable in the index", {"skill": skill})
    resources = []
    for target in _links(path):
        if re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith("#"):
            continue
        resolved = (path.parent / unquote(target.split("#")[0])).resolve()
        if resolved.is_relative_to(root.resolve()):
            resources.append(resolved.relative_to(root.resolve()).as_posix())
    return {"ok": True, "skill": skill, "path": path.relative_to(root).as_posix(),
            "content": path.read_text(encoding="utf-8"), "on_demand_resources": resources,
            "selection": "Agent chooses by intent; no keyword classifier or automatic bulk loading."}


def check_context(root: Path) -> dict:
    errors = []
    budgets = {}
    for relative, limit in (("AGENTS.md", 4000), ("skills/INDEX.md", 6500)):
        path = root / relative
        if not path.is_file():
            errors.append(f"Missing {relative}")
            continue
        size = path.stat().st_size
        budgets[relative] = {"bytes": size, "limit_bytes": limit, "lines": len(path.read_text(encoding='utf-8').splitlines())}
        if size > limit:
            errors.append(f"{relative}: {size} bytes exceeds {limit}")
    index_path = root / "skills/INDEX.md"
    index = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    skills = _skills(root)
    for slug, path in skills.items():
        content = path.read_text(encoding="utf-8")
        if f"{slug}/SKILL.md" not in index:
            errors.append(f"Orphan skill: {slug}")
        frontmatter = re.match(r"^---\nname: ([^\n]+)\ndescription: ([^\n]+)\n---\n", content)
        if not frontmatter or frontmatter.group(1).strip() != slug or not SLUG.fullmatch(slug):
            errors.append(f"Invalid skill metadata: {slug}")
        for heading in ("## 目标", "## 验收标准", "## 资源与边界", "## 输出"):
            if heading not in content:
                errors.append(f"{slug} missing {heading}")
        if len(content.encode("utf-8")) > 8500:
            errors.append(f"Skill too large for focused loading: {slug}")
    checked = 0
    for path in root.rglob("*.md"):
        if any(part in {".git", "runs", "local", "deliverables", ".venv"} for part in path.relative_to(root).parts):
            continue
        checked += 1
        for target in _links(path):
            if re.match(r"^[a-zA-Z][\w+.-]*:", target) or target.startswith("#"):
                continue
            raw = unquote(target.split("#")[0]).strip("<>")
            destination = (path.parent / raw).resolve()
            if not destination.is_relative_to(root.resolve()) or not destination.exists():
                errors.append(f"Broken/outside link: {path.relative_to(root)} -> {target}")
    agents = (root / "AGENTS.md").read_text(encoding="utf-8") if (root / "AGENTS.md").exists() else ""
    if "skills/INDEX.md" not in agents or "context/state.json" not in agents:
        errors.append("Entry must route to skill index and persistent state")
    result = {"ok": not errors, "skill_count": len(skills), "markdown_files_checked": checked,
              "entry_budget": budgets, "errors": errors,
              "scope": "Static discoverability; fresh-context behavior is evaluated separately."}
    if errors:
        raise HarnessError("CONTEXT_INVALID", "Context graph failed checks", result)
    return result


def save_handoff(root: Path, input_path: Path, expected_revision: int) -> dict:
    value = read_json(input_path)
    required = {"task_id", "owner", "status", "goal", "summary", "next_action", "blockers", "evidence", "decisions"}
    if not isinstance(value, dict) or set(value) != required:
        raise HarnessError("HANDOFF_SCHEMA", "Handoff fields must match the documented contract", {"required": sorted(required)})
    if not isinstance(value["task_id"], str) or not SLUG.fullmatch(value["task_id"]):
        raise HarnessError("HANDOFF_SCHEMA", "task_id must be a lowercase slug")
    for key in ("owner", "goal", "summary", "next_action"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise HarnessError("HANDOFF_SCHEMA", f"{key} must be nonempty text")
    if value["status"] not in {"ready", "in_progress", "blocked", "done"}:
        raise HarnessError("HANDOFF_SCHEMA", "Unknown task status")
    for key in ("blockers", "evidence", "decisions"):
        if not isinstance(value[key], list) or not all(isinstance(x, str) for x in value[key]):
            raise HarnessError("HANDOFF_SCHEMA", f"{key} must be a string list")
    if value["status"] == "blocked" and not value["blockers"]:
        raise HarnessError("HANDOFF_SCHEMA", "A blocked task must name its blocker")
    if value["status"] == "done" and (value["blockers"] or not value["evidence"]):
        raise HarnessError("HANDOFF_SCHEMA", "Done requires evidence and no unresolved blockers")
    evidence = []
    for relative in value["evidence"]:
        path = resolve_inside(root, relative)
        if not path.is_file():
            raise HarnessError("HANDOFF_SCHEMA", "Evidence must identify a file", {"path": relative})
        evidence.append({"path": relative, "sha256": sha256_file(path)})
    destination = resolve_inside(root, f"context/tasks/{value['task_id']}.json", must_exist=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock_path = destination.with_suffix(".lock")
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise HarnessError("HANDOFF_BUSY", "Another writer holds this task; inspect owner before removing a stale lock", {"task_id": value["task_id"]}) from exc
    try:
        os.close(lock_fd)
        previous = read_json(destination) if destination.exists() else None
        actual = previous.get("revision", 0) if previous else 0
        if actual != expected_revision:
            raise HarnessError("REVISION_CONFLICT", "Read the latest task and merge; do not overwrite another teammate", {"expected": expected_revision, "actual": actual})
        result = dict(value, schema_version=1, revision=actual + 1,
                      updated_at=datetime.now(timezone.utc).isoformat(), evidence_hashes=evidence)
        history = resolve_inside(root, f"context/history/{value['task_id']}/{actual+1:04d}.json", must_exist=False)
        if history.exists():
            raise HarnessError("HISTORY_CONFLICT", "History already exists; inspect interrupted previous write", {"path": str(history)})
        write_json(history, result)
        write_json(destination, result)
        return {"ok": True, "task": result, "path": destination.relative_to(root).as_posix()}
    finally:
        lock_path.unlink(missing_ok=True)


def doctor(root: Path) -> dict:
    from .runtime import check_data
    checks = {"python": {"version": sys.version.split()[0], "supported": sys.version_info >= (3, 11)},
              "docker": {"available": shutil.which("docker") is not None, "container_integration_tested": False}}
    try:
        checks["data"] = check_data(root, root / "config/data_manifest.json")
    except HarnessError as exc:
        checks["data"] = {"ok": False, "error": exc.as_dict()}
    schema = read_json(root / "competition/task_schema.json")
    checks["labels"] = {"status": schema.get("label_contract_status"),
                        "confirmed": schema.get("label_contract_status") == "confirmed"}
    ready = checks["docker"]["available"] and checks["data"].get("ok", False) and checks["labels"]["confirmed"]
    return {"ok": True, "training_prerequisites_ready": ready, "checks": checks,
            "note": "CLI availability is not a successful container isolation test. Image/adapter and plan checks are still required."}
