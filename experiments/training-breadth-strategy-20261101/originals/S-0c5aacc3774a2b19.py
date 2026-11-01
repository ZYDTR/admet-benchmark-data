"""Frozen CheMeleon asset registry: pinned versions, download URL, integrity checks.

Facts pinned (verified 2026-10-30 against the sources listed in
``input/research/candidate-evidence.md`` and ``input/research/source-index.md``):

* code: github.com/JacksonBurns/chemeleon @ b5e5bd88a7070c3f278e7e65e85b792617bf125c
* weights: Zenodo record 15460715, file ``chemeleon_mp.pt``

  - size 34,859,448 bytes
  - publisher MD5 6a80b54fdb7de37ef0374d302f01e8ce (Zenodo API /files endpoint)
  - license: MIT (record metadata)

The publisher ships only MD5; SHA256 is recorded by the operator after the
download and written into ``assets.lock.json`` (see HANDOFF for the command).
Weights are never fetched implicitly by the training/eval code: the path must be
given explicitly and must match the lock.
"""

import hashlib
import json
import os

from errors import InputContractError

CHEMELEON_ZENODO_RECORD = 15460715
CHEMELEON_ZENODO_DOI = "10.5281/zenodo.15460715"
CHEMELEON_FILENAME = "chemeleon_mp.pt"
CHEMELEON_SIZE = 34859448
CHEMELEON_MD5 = "6a80b54fdb7de37ef0374d302f01e8ce"
CHEMELEON_LICENSE = "MIT"
CHEMELEON_CODE_COMMIT = "b5e5bd88a7070c3f278e7e65e85b792617bf125c"
CHEMELEON_DOWNLOAD_URL = (
    f"https://zenodo.org/records/{CHEMELEON_ZENODO_RECORD}/files/{CHEMELEON_FILENAME}?download=1"
)

# Dependencies that must be pinned for a reproducible feature cache.  The exact
# versions come from the operator's environment lock (see requirements-lock.txt
# in HANDOFF); these are the package names whose *presence and version* are
# required, not pinned values, so a missing package is reported, not guessed.
REQUIRED_PACKAGES = ("torch", "chemprop", "rdkit", "numpy", "pandas")


def file_md5(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def file_sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def verify_weights_file(path, expected_sha256=None):
    """Check size + publisher MD5 (+ optional operator SHA256) of the checkpoint.

    Raises ``InputContractError`` on any mismatch.  Returns the observed digests.
    """
    if not os.path.isfile(path):
        raise InputContractError(
            f"CheMeleon weights not found at {path!r}. Download explicitly with: "
            f"curl -L -o {path} '{CHEMELEON_DOWNLOAD_URL}' (then record sha256)."
        )
    size = os.path.getsize(path)
    if size != CHEMELEON_SIZE:
        raise InputContractError(
            f"weights size {size} != expected {CHEMELEON_SIZE} for {path}"
        )
    md5 = file_md5(path)
    if md5 != CHEMELEON_MD5:
        raise InputContractError(f"weights md5 {md5} != publisher {CHEMELEON_MD5}")
    sha256 = file_sha256(path)
    if expected_sha256 is not None and sha256 != expected_sha256:
        raise InputContractError(
            f"weights sha256 {sha256} != locked {expected_sha256}"
        )
    return {"path": os.path.abspath(path), "size": size, "md5": md5, "sha256": sha256}


def load_lock(lock_path):
    """Read ``assets.lock.json`` (written by the operator after download)."""
    if not os.path.isfile(lock_path):
        raise InputContractError(
            f"asset lock not found: {lock_path}. Create it after downloading weights "
            "(see HANDOFF.md 'Asset lock' section)."
        )
    with open(lock_path, "r", encoding="utf-8") as fh:
        lock = json.load(fh)
    for key in ("weights_sha256", "weights_md5", "weights_size", "code_commit"):
        if key not in lock:
            raise InputContractError(f"{lock_path}: missing key {key!r}")
    if lock["weights_md5"] != CHEMELEON_MD5 or lock["weights_size"] != CHEMELEON_SIZE:
        raise InputContractError(f"{lock_path}: lock disagrees with pinned publisher digests")
    if lock["code_commit"] != CHEMELEON_CODE_COMMIT:
        raise InputContractError(f"{lock_path}: code commit != pinned {CHEMELEON_CODE_COMMIT}")
    return lock


def package_versions(names=REQUIRED_PACKAGES):
    """Best-effort ``{name: version|None}`` for the packages the cache depends on.

    Uses importlib.metadata so a missing package reports ``None`` instead of
    raising; the caller decides whether that is fatal.
    """
    from importlib import metadata

    out = {}
    for name in names:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out