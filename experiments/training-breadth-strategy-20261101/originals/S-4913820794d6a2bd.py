"""Build the competition submission CSV from per-task test predictions.

Joint procedure (this is what makes the template join provably complete):

1. Load the *pinned* template (16379 rows) and the test tables for the tasks to
   be exported.  Verify the template reproduces every test row exactly:
   per task, template ``sample_idx == row_index`` in file order, identical
   ``drug_id`` and ``smiles`` strings (``dataio.verify_template_mapping``).
2. Read the test product CSV and validate it against the *complete* expected key
   set ``{(task,'test',row_index)}`` (missing/extra/duplicate/non-finite fail).
3. Re-walk the template: for each row, look up its full identity
   ``(task, sample_idx, drug_id, smiles)`` in the test table; the identity must
   resolve to exactly one test row and that row must have a prediction.
4. Copy the template verbatim (byte-for-byte for every non-``y_pred`` field and
   column order), writing only ``y_pred``.

The pack's template ``sample_idx`` currently equals the test ``row_index`` in
file order for every task; this is *verified at run time*, not assumed.  When the
caller only exports a subset of tasks, every non-submitted row keeps its blank
``y_pred`` (never invented) and the function reports that.
"""

import csv
import os

from dataio import read_template, verify_template_mapping
from errors import ScoringError
from predict_io import read_products


def _template_identity(tab):
    return {(r["row_index"]): r for r in tab["rows"]}


def build_submission(root, tasks, test_products_path, out_path, template=None):
    from dataio import read_split

    tasks = sorted(tasks)
    template = template or read_template(root)
    test_tables = {t: read_split(root, t, "test") for t in tasks}
    mapping_tables = test_tables
    if template is not None and len({r["task"] for r in template["rows"]}) != len(tasks):
        # A caller-supplied template may cover a superset of ``tasks``; mapping is
        # still verified against every task the template claims, read from disk.
        mapping_tables = {t: test_tables.get(t) or read_split(root, t, "test")
                          for t in sorted({r["task"] for r in template["rows"]})}

    # Validate the product file before touching the template.
    expected = {}
    for t, tab in test_tables.items():
        for r in tab["rows"]:
            expected[(t, "test", r["row_index"])] = None
    preds = read_products(test_products_path, expected, splits=("test",))
    # Every prediction must be a test row we loaded (read_products already
    # guarantees the reverse direction).
    verify_template_mapping(template, mapping_tables)

    # Build identity -> prediction resolver per task.
    by_task = {}
    for t, tab in test_tables.items():
        ident = {}
        for r in tab["rows"]:
            ident[(r["drug_id"], r["smiles"])] = r["row_index"]
        by_task[t] = ident

    filled = 0
    out_rows = []
    for pos, tr in enumerate(template["rows"]):
        task = tr["task"]
        if task in by_task:
            ridx = by_task[task].get((tr["drug_id"], tr["smiles"]))
            if ridx is None:
                raise ScoringError(
                    f"template row {pos} ({task}) has no matching test row by (drug_id, smiles)"
                )
            if int(tr["sample_idx"]) != ridx:
                raise ScoringError(
                    f"template row {pos} ({task}): sample_idx {tr['sample_idx']} != resolved "
                    f"row_index {ridx}"
                )
            key = (task, "test", ridx)
            if key not in preds:
                raise ScoringError(f"no prediction for template row {pos} key {key}")
            new = dict(tr)
            new["y_pred"] = repr(float(preds[key]))
            out_rows.append(new)
            filled += 1
        else:
            out_rows.append(dict(tr))

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(template["rows"][0].keys()), lineterminator="\r\n")
        w.writeheader()
        for r in out_rows:
            w.writerow(r)
    os.replace(tmp, out_path)
    return {
        "out_path": out_path,
        "template_rows": len(out_rows),
        "tasks_exported": tasks,
        "rows_filled": filled,
        "rows_left_blank": len(out_rows) - filled,
        "template_sha256": template["sha256"],
    }


def verify_submission(template, submission_path, tasks):
    """Re-read a produced submission and assert template fidelity.

    Checks: same row count, same column order, identical non-``y_pred`` fields,
    ``y_pred`` non-empty and finite exactly for rows in ``tasks`` and blank
    elsewhere.
    """
    import math

    tasks = set(tasks)
    with open(submission_path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        header = tuple(next(reader, ()))
        rows = list(reader)
    theader = tuple(template["rows"][0].keys())
    if header != theader:
        raise ScoringError(f"submission header {header} != template {theader}")
    if len(rows) != len(template["rows"]):
        raise ScoringError(f"submission rows {len(rows)} != template {len(template['rows'])}")
    ycol = theader.index("y_pred")
    taskcol = theader.index("task")
    for i, (orig, new) in enumerate(zip(template["rows"], rows)):
        o = tuple(orig.values())
        if len(new) != len(o):
            raise ScoringError(f"row {i}: field count differs")
        for j, (a, b) in enumerate(zip(o, new)):
            if j == ycol:
                continue
            if a != b:
                raise ScoringError(f"row {i} col {theader[j]}: {b!r} != template {a!r}")
        in_scope = new[taskcol] in tasks
        blank = new[ycol] == ""
        if in_scope:
            if blank:
                raise ScoringError(f"row {i}: y_pred missing for exported task {new[taskcol]}")
            if not math.isfinite(float(new[ycol])):
                raise ScoringError(f"row {i}: non-finite y_pred {new[ycol]!r}")
        elif not blank:
            raise ScoringError(f"row {i}: y_pred written for unexported task {new[taskcol]}")
    return {"rows": len(rows), "tasks": sorted(tasks)}