"""Synthetic fixtures for the ADMET data-eval prep tests.

ALL values here are synthetic (fixed constants, no randomness) and are used
only to exercise CLI contracts.  They are NOT model predictions, NOT official
labels, and are not evaluation results.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.abspath(os.path.join(HERE, ".."))
PACKAGE = os.path.abspath(os.path.join(OUTPUT, ".."))
sys.path.insert(0, OUTPUT)

from admet_eval import common as C  # noqa: E402

OFFICIAL = os.path.join(PACKAGE, "input/data/official")
BLIND = os.path.join(PACKAGE, "input/data/blind_validation")
TEMPLATE = os.path.join(OFFICIAL, "submission_template.csv")
SCHEMA = os.path.join(OUTPUT, "admet_eval/task_schema.json")
FIXTURES = os.path.join(OUTPUT, "tests/fixtures")
SYNTHETIC = "SYNTHETIC"

# Deterministic synthetic value generator: small, finite, in-range.
def synth_value(task: str, kind: str, split: str, row_index: int) -> float:
    h = hashlib.sha256(f"{SYNTHETIC}|{task}|{split}|{row_index}".encode()).digest()
    u = int.from_bytes(h[:8], "big") / 2**64  # [0,1)
    if kind == "classification":
        return round(u, 6)  # score in [0,1)
    return round(u * 10.0 - 5.0, 6)


def synthetic_label(task: str, kind: str, row_index: int):
    if kind == "classification":
        return int(row_index % 3 == 0)  # deterministic 0/1 mix
    return round((row_index % 7) * 1.25 - 2.0, 6)


def write_predictions(path, splits=("test",)):
    """Full-coverage synthetic predictions for the requested splits."""
    schema = json.load(open(SCHEMA, encoding="utf-8"))
    tasks = schema["tasks"]
    preds = []
    for split in splits:
        for t in tasks:
            rows = C.read_split(split, t["task"], OFFICIAL, BLIND)["n_rows"]
            for ri in range(rows):
                preds.append({
                    "task": t["task"], "split": split, "row_index": ri,
                    "y_pred": synth_value(t["task"], t["kind"], split, ri),
                })
    doc = {"schema_version": 1, "predictions": preds}
    _dump(path, doc)
    return doc


def write_labels(path, splits=("valid",), tasks=None, drop=None):
    schema = json.load(open(SCHEMA, encoding="utf-8"))
    labels = []
    for split in splits:
        for t in schema["tasks"]:
            if tasks is not None and t["task"] not in tasks:
                continue
            rows = C.read_split(split, t["task"], OFFICIAL, BLIND)["n_rows"]
            for ri in range(rows):
                key = (t["task"], split, ri)
                if drop and key in drop:
                    continue
                labels.append({
                    "task": t["task"], "split": split, "row_index": ri,
                    "y": synthetic_label(t["task"], t["kind"], ri),
                })
    doc = {"schema_version": 1, "split_id": ",".join(splits), "labels": labels}
    _dump(path, doc)
    return doc


def _dump(path, doc):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
        fh.write("\n")


def split_inputs_path():
    return os.path.join(OUTPUT, "reports/split_inputs.json")