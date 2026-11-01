"""CSV input reading that preserves row identity and raw strings.

Only the Python standard library is used here so that data-side checks run in
any environment. test.csv files in this snapshot carry a UTF-8 BOM while
train/valid do not; utf-8-sig decoding handles both cases.

Row identity is (task, split, row_index) with row_index = 0-based position of
the data row (header excluded). Drug_ID may be empty or duplicated and SMILES
may repeat with different labels; rows are never merged or filtered here.
"""

from __future__ import annotations

import csv
import hashlib
import math
from pathlib import Path

TRAIN_HEADER = ["Drug_ID", "Drug", "Y"]
UNLABELED_HEADER = ["Drug_ID", "Drug"]

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data"


def split_path(data_root: str | Path, task: str, split: str) -> Path:
    if split == "train":
        return Path(data_root) / "official" / "data_benchmark" / task / "train.csv"
    if split == "valid":
        return Path(data_root) / "blind_validation" / task / "valid.csv"
    if split == "test":
        return Path(data_root) / "official" / "data_benchmark" / task / "test.csv"
    raise ValueError(f"unknown split {split!r}")


def read_rows(path: str | Path, expect_y: bool) -> list[dict]:
    """Read one task CSV into ordered row dicts.

    expect_y=True enforces the (Drug_ID, Drug, Y) header and parses Y as a
    finite float; expect_y=False enforces (Drug_ID, Drug). SMILES and Drug_ID
    are kept as raw strings, exactly as written in the file.
    """
    path = Path(path)
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"{path}: empty file, no header") from None
        expected = TRAIN_HEADER if expect_y else UNLABELED_HEADER
        if header != expected:
            raise ValueError(f"{path}: header {header!r}, expected {expected!r}")
        rows: list[dict] = []
        for i, rec in enumerate(reader):
            if len(rec) != len(header):
                raise ValueError(f"{path}: data row {i} has {len(rec)} fields, expected {len(header)}")
            row = {"row_index": i, "drug_id": rec[0], "smiles": rec[1]}
            if expect_y:
                try:
                    y = float(rec[2])
                except ValueError:
                    raise ValueError(f"{path}: data row {i} has non-numeric Y {rec[2]!r}") from None
                if not math.isfinite(y):
                    raise ValueError(f"{path}: data row {i} has non-finite Y {rec[2]!r}")
                row["y"] = y
            rows.append(row)
    return rows


def smiles_sha(smiles: str) -> str:
    """Stable cache key: SHA-256 hex of the exact raw SMILES string (UTF-8)."""
    return hashlib.sha256(smiles.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
