"""Read-only cache provenance anchored outside the mutable cache itself.

The expected manifest SHA must come from the controller's frozen task, never
from hashing an untrusted manifest and accepting that same value as authority.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType

from .common import InterfaceError, sha256_file


class CacheTrust:
    def __init__(self, manifest_path, expected_sha256,
                 prefix="input/legacy/cache/chemeleon_mp/"):
        path = Path(manifest_path)
        if sha256_file(path) != expected_sha256:
            raise InterfaceError("trusted manifest digest mismatch")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        entries = {}
        for row in manifest["files"]:
            name = row["path"]
            if name.startswith(prefix):
                relative = name[len(prefix):]
                if relative in entries or ".." in Path(relative).parts:
                    raise InterfaceError("invalid trusted cache manifest member")
                entries[relative] = (row["sha256"], row["bytes"])
        if not entries:
            raise InterfaceError("trusted cache manifest has no cache entries")
        self.entries = MappingProxyType(entries)
        self.manifest_sha256 = expected_sha256

    def verify(self, root, task, split):
        for name in (f"raw_{split}.npy", f"mask_{split}.npy",
                     f"raw_{split}.meta.json"):
            key = f"{task}/{name}"
            if key not in self.entries:
                raise InterfaceError(f"trusted cache entry missing: {key}")
            path = Path(root) / key
            expected_sha, expected_bytes = self.entries[key]
            if not path.is_file():
                raise InterfaceError(f"trusted cache file missing: {key}")
            if path.stat().st_size != expected_bytes or sha256_file(path) != expected_sha:
                raise InterfaceError(f"trusted cache digest mismatch: {key}")
        return self.manifest_sha256
