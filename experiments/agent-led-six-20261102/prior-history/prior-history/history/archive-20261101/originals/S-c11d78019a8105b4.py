"""Shared helpers for prep-session checks. All data here is SYNTHETIC."""

import csv
import os
import sys
import tempfile

OUTPUT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (OUTPUT_DIR, _TESTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

WORK_TMP = os.path.join(OUTPUT_DIR, "tmp")
REPO_INPUT_DATA = os.path.realpath(os.path.join(OUTPUT_DIR, "..", "input", "data"))
pristine = True
if not os.path.isdir(WORK_TMP):
    pristine = False
    try:
        os.makedirs(WORK_TMP, exist_ok=True)
    except OSError:  # pragma: no cover - read-only output tree
        pristine = False
        WORK_TMP = tempfile.mkdtemp(prefix="ocprep_")

import atexit


@atexit.register
def _cleanup_work_tmp():
    """Leave the output tree as found: tests must not litter deliverables."""
    if pristine:
        return
    import shutil

    if WORK_TMP.startswith(tempfile.gettempdir()) or os.path.basename(WORK_TMP) == "tmp":
        shutil.rmtree(WORK_TMP, ignore_errors=True)

TASKS = ("ames", "caco2_wang")  # one classification, one regression (SYNTHETIC)


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def make_synthetic_root(root, n_train=6, n_valid=3, n_test=4, n_tasks=2):
    """Create a minimal pack mimicking the real layout with SYNTHETIC content.

    Returns ``(tasks, sizes)``.  Caco2 labels are floats; ames labels are 0/1.
    """
    tasks = list(TASKS)[:n_tasks]
    for task in tasks:
        is_reg = task.endswith("_wang")
        train = []
        for i in range(n_train):
            smi = f"C{'C' * i}O"
            y = round(1.5 + 0.25 * i, 4) if is_reg else (i % 2)
            train.append([f"Drug {i}", smi, y])
        write_csv(os.path.join(root, "official", "data_benchmark", task, "train.csv"),
                  ["Drug_ID", "Drug", "Y"], train)
        test = [[f"DrugT {i}", f"N{'C' * i}"] for i in range(n_test)]
        write_csv(os.path.join(root, "official", "data_benchmark", task, "test.csv"),
                  ["Drug_ID", "Drug"], test)
        valid = [[f"DrugV {i}", f"O{'C' * i}"] for i in range(n_valid)]
        write_csv(os.path.join(root, "official", "blind_validation", task, "valid.csv"),
                  ["Drug_ID", "Drug"], valid)
    return tasks, {"train": n_train, "valid": n_valid, "test": n_test}


def make_template(root, tasks, n_test=4, metric=("AUROC", "MAE")):
    """Build a SYNTHETIC submission template matching the layout (not 16379 rows)."""
    rows = []
    for ti, task in enumerate(tasks):
        for i in range(n_test):
            rows.append([task, i, f"DrugT {i}", f"N{'C' * i}", "", metric[ti % len(metric)]])
    path = os.path.join(root, "official", "submission_template.csv")
    write_csv(path, ["task", "sample_idx", "drug_id", "smiles", "y_pred", "metric"], rows)
    return path