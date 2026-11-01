"""Task registry: the 22 ADMET tasks with kind, metric, and audited row counts.

tasks.json is generated from the verified 2026-10-30 snapshot (see its
provenance field). The registry is shipped as a frozen artifact so that task
kinds never have to be inferred from Y values; at runtime the task names are
cross-checked against the data directory listing.
"""

from __future__ import annotations

import json
from pathlib import Path

TASKS_JSON = Path(__file__).resolve().parent.parent / "tasks.json"
SPLITS = ("train", "valid", "test")
KINDS = ("classification", "regression")


def load_tasks(tasks_json: str | Path = TASKS_JSON) -> list[dict]:
    data = json.loads(Path(tasks_json).read_text(encoding="utf-8"))
    tasks = data["tasks"]
    names = [t["task"] for t in tasks]
    if len(names) != len(set(names)):
        raise ValueError("duplicate task names in tasks.json")
    for t in tasks:
        if set(t) != {"task", "kind", "metric", "rows"}:
            raise ValueError(f"unexpected fields in task entry: {sorted(t)}")
        if t["kind"] not in KINDS:
            raise ValueError(f"unknown kind {t['kind']!r} for {t['task']}")
        if set(t["rows"]) != set(SPLITS):
            raise ValueError(f"rows must have {SPLITS} for {t['task']}")
        for v in t["rows"].values():
            if not isinstance(v, int) or v <= 0:
                raise ValueError(f"bad row count for {t['task']}")
    return tasks


def load_registry(tasks_json: str | Path = TASKS_JSON) -> dict:
    return json.loads(Path(tasks_json).read_text(encoding="utf-8"))


def select_tasks(tasks: list[dict], names: str | None) -> list[dict]:
    """names: comma-separated task list, or None/'' /'all' for every task."""
    if not names or names.strip().lower() == "all":
        return tasks
    wanted = [x.strip() for x in names.split(",") if x.strip()]
    known = {t["task"] for t in tasks}
    unknown = [x for x in wanted if x not in known]
    if unknown:
        raise ValueError(f"unknown task(s): {unknown}")
    if len(wanted) != len(set(wanted)):
        raise ValueError("duplicate task in --tasks")
    return [t for t in tasks if t["task"] in set(wanted)]


def validate_data_root(data_root: str | Path, tasks: list[dict]) -> None:
    """Fail early if any expected input CSV is missing for the selected tasks."""
    from .data_io import split_path

    data_root = Path(data_root)
    if not data_root.is_dir():
        raise FileNotFoundError(f"data root not found: {data_root}")
    for t in tasks:
        for split in SPLITS:
            p = split_path(data_root, t["task"], split)
            if not p.is_file():
                raise FileNotFoundError(f"missing input file: {p}")
