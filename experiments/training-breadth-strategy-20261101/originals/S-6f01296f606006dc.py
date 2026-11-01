"""Shared constants and file helpers for the frozen CheMeleon + per-task MLP baseline.

No training, no parameter updates here. Everything operates on the read-only
official CSVs described in ../../TASK.md.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

TASKS = [
    "ames",
    "bbb_martins",
    "bioavailability_ma",
    "caco2_wang",
    "clearance_hepatocyte_az",
    "clearance_microsome_az",
    "cyp2c9_substrate_carbonmangels",
    "cyp2c9_veith",
    "cyp2d6_substrate_carbonmangels",
    "cyp2d6_veith",
    "cyp3a4_substrate_carbonmangels",
    "cyp3a4_veith",
    "dili",
    "half_life_obach",
    "herg",
    "hia_hou",
    "ld50_zhu",
    "lipophilicity_astrazeneca",
    "pgp_broccatelli",
    "ppbr_az",
    "solubility_aqsoldb",
    "vdss_lombardo",
]

CLASSIFICATION_TASKS = {
    "ames",
    "bbb_martins",
    "bioavailability_ma",
    "cyp2c9_substrate_carbonmangels",
    "cyp2c9_veith",
    "cyp2d6_substrate_carbonmangels",
    "cyp2d6_veith",
    "cyp3a4_substrate_carbonmangels",
    "cyp3a4_veith",
    "dili",
    "herg",
    "hia_hou",
    "pgp_broccatelli",
}

# Fill value for embeddings that could not be computed (invalid SMILES).
# Chosen so the MLP sees a clearly out-of-distribution constant row;
# documented in HANDOFF.md as the auditable complete-coverage scheme.
GLOBAL_FILL_VALUE = 0.0

TRAIN_REL = "data/official/data_benchmark/{task}/train.csv"
VALID_REL = "data/blind_validation/{task}/valid.csv"
TEST_REL = "data/official/data_benchmark/{task}/test.csv"
TEMPLATE_REL = "data/official/submission_template.csv"


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve(rel: str) -> Path:
    return project_root() / rel


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def read_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def task_kind(task: str) -> str:
    return "classification" if task in CLASSIFICATION_TASKS else "regression"


def iter_split_smiles(task: str, split: str) -> list[str]:
    rel = {"train": TRAIN_REL, "valid": VALID_REL, "test": TEST_REL}[split]
    rows = read_csv_rows(resolve(rel.format(task=task)))
    return [r["Drug"] for r in rows]