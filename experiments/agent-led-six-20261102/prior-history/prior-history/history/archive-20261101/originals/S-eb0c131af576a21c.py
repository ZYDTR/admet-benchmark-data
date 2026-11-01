"""Small, dependency-free I/O contracts shared by every command."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


class HarnessError(Exception):
    def __init__(self, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details

    def as_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise HarnessError("FILE_READ_ERROR", str(exc), {"path": str(path)}) from exc
    return digest.hexdigest()


def _invalid_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=_invalid_constant, object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, ValueError) as exc:
        raise HarnessError("JSON_READ_ERROR", str(exc), {"path": str(path)}) from exc


def write_json(path: Path, value: Any) -> None:
    path = Path(path)
    try:
        payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    except (OSError, ValueError, TypeError) as exc:
        raise HarnessError("JSON_WRITE_ERROR", str(exc), {"path": str(path)}) from exc


def resolve_inside(root: Path, value: str | Path, must_exist: bool = True) -> Path:
    root = Path(root).resolve()
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise HarnessError("INVALID_PATH", "Expected a nonempty project-relative path")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise HarnessError("PATH_OUTSIDE_PROJECT", "Use a project-relative path without '..'", {"path": str(value)})
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise HarnessError("SYMLINK_REJECTED", "Symlinks are not admitted as run inputs", {"path": str(value)})
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise HarnessError("PATH_OUTSIDE_PROJECT", "Path escapes project", {"path": str(value)})
    if must_exist and not resolved.exists():
        raise HarnessError("FILE_MISSING", "Required project path does not exist", {"path": str(value)})
    return resolved
