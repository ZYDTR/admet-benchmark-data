"""Data loading and row-identity contract for the competition-159 ADMET pack.

Raw input contract (never cleaned, never de-duplicated):

* ``<root>/official/data_benchmark/<task>/train.csv`` -> ``Drug_ID,Drug,Y``
* ``<root>/official/data_benchmark/<task>/test.csv``  -> ``Drug_ID,Drug``
* ``<root>/official/blind_validation/<task>/valid.csv`` -> ``Drug_ID,Drug``
* ``<root>/official/submission_template.csv`` -> ``task,sample_idx,drug_id,smiles,y_pred,metric``

Row identity is ``(task, split, row_index)`` where ``row_index`` is the 0-based
data-record position in that raw CSV (header excluded).  Repeated molecules stay
as separate rows: the same ``(Drug, Y)`` can appear many times and each keeps its
own index.
"""

import csv
import hashlib
import json
import os

from errors import InputContractError, LabelError

SPLITS = ("train", "valid", "test")
TASK_KEYS_TRAIN = ("Drug_ID", "Drug", "Y")
TASK_KEYS_NOLABEL = ("Drug_ID", "Drug")
TEMPLATE_KEYS = ("task", "sample_idx", "drug_id", "smiles", "y_pred", "metric")
TEMPLATE_ROWS = 16379
TEMPLATE_SHA256 = "8ee41589d2c98e7b93081c058b3f928ac09bea4b3ffc899fa13677051e9baa20"


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _read_raw(path):
    if not os.path.isfile(path):
        raise InputContractError(f"missing input file: {path}")
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))





def split_path(root, task, split):
    if split == "train":
        return os.path.join(root, "official", "data_benchmark", task, "train.csv")
    if split == "test":
        return os.path.join(root, "official", "data_benchmark", task, "test.csv")
    if split == "valid":
        for base in ("blind_validation", os.path.join("official", "blind_validation")):
            p = os.path.join(root, base, task, "valid.csv")
            if os.path.isfile(p):
                return p
        return os.path.join(root, "official", "blind_validation", task, "valid.csv")
    raise InputContractError(f"unknown split {split!r}")


def template_path(root):
    return os.path.join(root, "official", "submission_template.csv")


def list_tasks(root):
    bench = os.path.join(root, "official", "data_benchmark")
    blind = os.path.join(root, "blind_validation")
    if not os.path.isdir(blind):
        blind = os.path.join(root, "official", "blind_validation")
    if not os.path.isdir(bench):
        raise InputContractError(f"missing benchmark dir: {bench}")
    tasks = sorted(
        d for d in os.listdir(bench) if os.path.isfile(os.path.join(bench, d, "train.csv"))
    )
    if not tasks:
        raise InputContractError(f"no tasks under {bench}")
    for t in tasks:
        if not os.path.isfile(os.path.join(blind, t, "valid.csv")):
            raise InputContractError(f"task {t} has no blind valid.csv")
    return tasks


def read_split(root, task, split, require_labels=None):
    """Load one (task, split) table with full row identity.

    Returns ``{"task","split","path","sha256","n_rows","rows",
    "drug_ids","smiles","labels"}`` where ``rows`` is a list of dicts carrying
    ``task, split, row_index, drug_id, smiles`` (+ ``label`` when present).

    ``require_labels`` defaults to ``True`` for train and ``False`` otherwise.
    A present ``Y`` column is parsed for *every* split; non-numeric or
    non-finite values raise; a missing ``Y`` raises when ``require_labels`` is
    true.  Blind splits must not carry a ``Y`` column at all.
    """
    path = split_path(root, task, split)
    if require_labels is None:
        require_labels = split == "train"
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        header = tuple(next(csv.reader(fh), ()))
    if split == "train":
        if header != TASK_KEYS_TRAIN:
            raise InputContractError(f"{path}: header {header} != {list(TASK_KEYS_TRAIN)}")
    else:
        # test/valid files must NOT carry a Y column.
        if header not in (TASK_KEYS_NOLABEL, TASK_KEYS_TRAIN):
            raise InputContractError(f"{path}: header {header} not in {TASK_KEYS_NOLABEL}")
        if "Y" in header:
            raise InputContractError(f"{path}: label column present in split {split!r}")
    rows = _read_raw(path)

    out = []
    labels = []
    has_label = "Y" in header
    for idx, r in enumerate(rows):
        rec = {
            "task": task,
            "split": split,
            "row_index": idx,
            "drug_id": r["Drug_ID"],
            "smiles": r["Drug"],
        }
        if has_label:
            raw = r["Y"]
            try:
                val = float(raw)
            except (TypeError, ValueError):
                raise LabelError(f"{path}: row {idx} non-numeric Y {raw!r}")
            if not (val == val and val not in (float("inf"), float("-inf"))):
                raise LabelError(f"{path}: row {idx} non-finite Y {raw!r}")
            rec["label"] = val
            labels.append(val)
        elif require_labels:
            raise LabelError(f"{path}: labels required but Y column absent")
        out.append(rec)

    return {
        "task": task,
        "split": split,
        "path": path,
        "sha256": sha256_file(path),
        "n_rows": len(out),
        "rows": out,
        "drug_ids": [r["drug_id"] for r in out],
        "smiles": [r["smiles"] for r in out],
        "labels": labels if has_label else None,
        "header_has_label": has_label,
    }


def input_digest(tables):
    """Stable content digest of the exact rows used, for provenance output.

    ``tables`` is an iterable of ``(split, table_dict)``.  The digest covers the
    file sha256, row count, per-row (task, split, row_index, drug_id, smiles) and,
    when labels are present, the label values.  Repeated rows contribute each
    occurrence.
    """
    h = hashlib.sha256()
    summary = []
    for split, tab in sorted(tables, key=lambda kv: kv[0]):
        body = json.dumps(
            [
                [r["task"], r["split"], r["row_index"], r["drug_id"], r["smiles"],
                 r.get("label")]
                for r in tab["rows"]
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        h.update(split.encode())
        h.update(tab["sha256"].encode())
        h.update(body.encode())
        summary.append(
            {"split": split, "path": tab["path"], "sha256": tab["sha256"],
             "n_rows": tab["n_rows"]}
        )
    return {"digest_sha256": h.hexdigest(), "files": summary}


def read_template(root, expected_rows=TEMPLATE_ROWS):
    """Load the submission template and enforce the *caller's* expected row count.

    ``expected_rows`` defaults to the pinned competition value 16,379; synthetic
    fixtures pass their own count.  There is no bypass: the row count and the
    per-row identity join are always checked against the supplied test tables.
    """
    path = template_path(root)
    rows = _read_raw(path)
    if not rows:
        raise InputContractError(f"{path}: empty template")
    if tuple(rows[0].keys()) != TEMPLATE_KEYS:
        raise InputContractError(f"{path}: template header {tuple(rows[0].keys())}")
    if len(rows) != expected_rows:
        raise InputContractError(f"{path}: {len(rows)} rows != expected {expected_rows}")
    return {"path": path, "sha256": sha256_file(path), "rows": rows}


def template_index(template):
    """Map ``(task, sample_idx) -> template row position`` and verify uniqueness."""
    pos = {}
    for i, r in enumerate(template["rows"]):
        key = (r["task"], int(r["sample_idx"]))
        if key in pos:
            raise InputContractError(f"template duplicate key {key}")
        pos[key] = i
    return pos


def verify_template_mapping(template, test_tables):
    """Verify the template reproduces the test files row-for-row.

    ``test_tables`` maps ``task -> read_split(..., 'test')``.  The template must
    contain exactly the union of test rows and, within each task, must list
    ``sample_idx == row_index`` in file order with identical ``drug_id`` and
    ``smiles`` strings.  This is how template order is recovered from full
    identity rather than assumed from ``sample_idx`` alone.
    """
    tasks = sorted(test_tables)
    tpos = {}
    counts = {}
    for i, r in enumerate(template["rows"]):
        if r["task"] not in test_tables:
            raise InputContractError(f"template has unexpected task {r['task']!r}")
        counts[r["task"]] = counts.get(r["task"], 0) + 1
        tpos.setdefault(r["task"], []).append(i)
    missing = tasks and set(tasks) - set(counts)
    if missing:
        raise InputContractError(f"template missing tasks {sorted(missing)}")
    extra = set(counts) - set(tasks)
    if extra:
        raise InputContractError(f"template has tasks not requested {sorted(extra)}")
    for t in tasks:
        tab = test_tables[t]
        positions = tpos.get(t, [])
        if len(positions) != tab["n_rows"]:
            raise InputContractError(
                f"template task {t} rows {len(positions)} != test rows {tab['n_rows']}"
            )
        for j, pos in enumerate(positions):
            tr = template["rows"][pos]
            src = tab["rows"][j]
            if int(tr["sample_idx"]) != src["row_index"]:
                raise InputContractError(
                    f"task {t}: template sample_idx {tr['sample_idx']} at slot {j} "
                    f"!= test row_index {src['row_index']}"
                )
            if tr["drug_id"] != src["drug_id"]:
                raise InputContractError(f"task {t} row {j}: drug_id mismatch")
            if tr["smiles"] != src["smiles"]:
                raise InputContractError(f"task {t} row {j}: smiles mismatch")
    return True