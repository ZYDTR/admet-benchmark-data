#!/usr/bin/env python3
"""score: score predictions against an explicitly-passed label file.

This scorer ONLY reads label files the caller passes explicitly.  It never
discovers or guesses labels, and it is the *only* entry point needed to score
(a caller cannot skip a prior checker: key-set completeness, duplicate keys,
unknown/invalid tasks, bad splits, non-finite and non-0/1 values are all
enforced here).

Label file formats
  --labels-json  {schema_version, split_id, labels:[{task,split,row_index,y}]}
  --labels-csv   a CSV with header Drug_ID,Drug,Y  (+ --labels-csv-task TASK
                 --labels-csv-split valid)  -- converts to the JSON contract.

Predictions  {schema_version, predictions:[{task,split,row_index,y_pred}]}

Expected keys are derived from the *inputs* passed via --split-inputs (a JSON
map of split -> {task: n_rows}), which the caller must supply alongside the
label file so completeness is checked against the real split files, not only
the labels present.  If --split-inputs is omitted, expected keys fall back to
the union of the label file rows AND the prediction rows (weak); the CLI warns
loudly and this is marked in the output.

Scoring only covers classification labels (strict 0/1) and regression labels
(finite).  AP below is local average precision; official AUPRC and the official
total-score aggregation are NOT confirmed and are not produced.

Exit codes: 0 ok, 2 explicit contract/metric failure (undefined is *not* an
error: it yields status=undefined with reason and exit 0), 3 internal error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from admet_eval import common as C  # noqa: E402
from admet_eval import metrics as M  # noqa: E402


DEFAULT_SPLIT_OF_INTEREST = "valid"


def _labels_from_csv(path, task, split):
    raw = C.read_bytes(path)
    header, rows = C.parse_csv(raw, path)
    if header not in (["Drug_ID", "Drug", "Y"], ["Drug_ID", "Drug"]):
        raise C.ContractError("LABELS_CSV_HEADER",
                              f"{path}: unexpected header {header}", header=header)
    if "Y" not in header:
        raise C.ContractError("LABELS_CSV_NO_Y",
                              f"{path}: label CSV has no Y column (this is a blind file)")
    labels = []
    for ri, row in enumerate(rows):
        y = row[2]
        if y.strip() == "":
            labels.append({"task": task, "split": split, "row_index": ri, "y": None})
            continue
        try:
            v = float(y)
        except ValueError as exc:
            raise C.ContractError("LABELS_CSV_VALUE",
                                  f"{path}: row {ri} Y not a number: {y!r}",
                                  row_index=ri) from exc
        labels.append({"task": task, "split": split, "row_index": ri, "y": v})
    return {"schema_version": C.LABELS_SCHEMA_VERSION,
            "split_id": f"{task}/{split}", "labels": labels}


def score(labels_json, labels_csv, labels_csv_task, labels_csv_split,
          predictions_path, schema_path, template_path, split_inputs_path,
          split=None):
    schema = C.load_and_check_schema(schema_path, template_path)
    meta = {t["task"]: t for t in schema["tasks"]}
    tasks_by_split = {s: set(meta) for s in C.SPLITS}
    split_to_check = split or (labels_csv_split if labels_csv else None) \
        or DEFAULT_SPLIT_OF_INTEREST
    if split is not None and split not in C.SPLITS:
        raise C.ContractError("ARGS", f"--split must be one of {list(C.SPLITS)}")

    # expected keys
    if split_inputs_path:
        si = C.load_json(split_inputs_path)
        expected_keys = {}
        for split, per_task in si["splits"].items():
            if split != split_to_check:
                continue
            expected_keys[split] = set()
            for task, n in per_task.items():
                if split not in C.SPLITS:
                    raise C.ContractError("SPLIT_INPUTS_SPLIT", f"bad split {split}")
                if task not in meta:
                    raise C.ContractError("SPLIT_INPUTS_TASK", f"unknown task {task}")
                for ri in range(n):
                    expected_keys[split].add((task, ri))
        weak = False
    else:
        expected_keys = None
        weak = True

    preds = C.load_predictions(
        predictions_path,
        expected_keys if expected_keys is not None else _keys_from_preds_only(predictions_path),
    )

    if labels_json and labels_csv:
        raise C.ContractError("ARGS", "pass only one of --labels-json / --labels-csv")
    if labels_csv:
        if not labels_csv_task or not labels_csv_split:
            raise C.ContractError("ARGS", "--labels-csv needs --labels-csv-task and --labels-csv-split")
        doc = _labels_from_csv(labels_csv, labels_csv_task, labels_csv_split)
        lbl_path = None
    elif labels_json:
        doc = C.load_json(labels_json)
        lbl_path = labels_json
    else:
        raise C.ContractError("ARGS", "one of --labels-json / --labels-csv is required")

    label_map = _load_labels_doc(doc, tasks_by_split)

    if weak:
        expected_keys = {}
        for (task, split, ri) in label_map:
            expected_keys.setdefault(split, set()).add((task, ri))

    # re-validate keys against expected (when split_inputs supplied); labels may
    # be a strict subset (nulls excluded) but must not introduce unknown keys.
    extra_labels = set(label_map) - set(preds)
    if extra_labels:
        raise C.ContractError("LABELS_EXTRA_KEYS",
                              "label file contains keys absent from predictions",
                              count=len(extra_labels),
                              examples=sorted(extra_labels)[:10])

    report = {
        "schema_version": 1,
        "scoring_mode": "local_metrics",
        "label_source": {"path": lbl_path or labels_csv,
                         "sha256": C.sha256_file(lbl_path or labels_csv)},
        "prediction_sha256": C.sha256_file(predictions_path),
        "complete_key_set_checked": not weak,
        "warnings": [],
        "tasks": {},
    }
    if weak:
        report["warnings"].append(
            "NO_SPLIT_INPUTS: expected key set derived from labels+predictions only; "
            "pass --split-inputs to verify completeness against real split files")

    # Group and compute
    index = {}
    for (task, split, ri), yp in preds.items():
        index.setdefault((task, split), {})[ri] = yp

    for (task, split) in sorted(index):
        tmeta = meta[task]
        metric = tmeta["metric"]
        kind = tmeta["kind"]
        entry = {"task": task, "split": split, "metric": metric, "kind": kind}
        if metric == "AUPRC":
            entry["local_definition"] = "average_precision"
            entry["official_equivalence"] = "unconfirmed"
        pred_by_ri = index[(task, split)]
        y_true = []
        y_pred = []
        missing = 0
        labeled = 0
        invalid = []
        for ri, yp in sorted(pred_by_ri.items()):
            key = (task, split, ri)
            if key not in label_map:
                missing += 1
                continue
            y = label_map[key]
            if y is None:
                missing += 1
                continue
            if kind == "classification":
                if isinstance(y, bool) or y not in (0, 1):
                    invalid.append({"row_index": ri, "y": y})
                    continue
            y_true.append(y)
            y_pred.append(yp)
            labeled += 1
        entry["records"] = len(pred_by_ri)
        entry["labeled"] = labeled
        entry["missing_labels"] = missing
        if invalid:
            raise C.ContractError("LABELS_INVALID_CLASS",
                                  f"{task}/{split}: classification labels not strictly 0/1",
                                  examples=invalid[:10], count=len(invalid))
        if labeled == 0:
            entry.update({"value": None, "status": "undefined", "reason": "no_labeled_records"})
            report["tasks"][f"{task}/{split}"] = entry
            continue
        try:
            value = M.compute(metric, kind, y_true, y_pred)
            entry.update({"value": value, "status": "ok", "reason": None})
        except M.MetricUndefined as exc:
            entry.update({"value": None, "status": "undefined", "reason": exc.reason})
        except ValueError as exc:
            raise C.ContractError("METRIC_INPUT", f"{task}/{split}: {exc}") from exc
        if kind == "classification":
            entry["positives"] = sum(1 for t in y_true if t == 1)
            entry["negatives"] = sum(1 for t in y_true if t == 0)
        report["tasks"][f"{task}/{split}"] = entry

    report["ok"] = True
    return report


def _keys_from_preds_only(path):
    doc = C.load_json(path)
    keys = {}
    for rec in doc.get("predictions", []):
        keys.setdefault(rec["split"], set()).add((rec["task"], rec["row_index"]))
    return keys


def _load_labels_doc(doc, tasks_by_split):
    """Validate a label document without extra temp files.

    Mirrors C.load_label_file but operates on an in-memory doc (used for both
    --labels-json already-loaded and --labels-csv converted docs).
    """
    if doc.get("schema_version") != C.LABELS_SCHEMA_VERSION:
        raise C.ContractError("LABELS_VERSION", "labels schema_version mismatch",
                              got=doc.get("schema_version"))
    labels = doc.get("labels")
    if not isinstance(labels, list):
        raise C.ContractError("LABELS_SHAPE", "labels must be a list")
    out = {}
    dups = []
    unknown = []
    bad_split = []
    for i, rec in enumerate(labels):
        if not isinstance(rec, dict):
            raise C.ContractError("LABELS_RECORD", f"labels[{i}] not an object")
        try:
            task = rec["task"]
            split = rec["split"]
            row_index = rec["row_index"]
            y = rec["y"]
        except KeyError as exc:
            raise C.ContractError("LABELS_RECORD", f"labels[{i}] missing {exc}")
        if split not in C.SPLITS:
            bad_split.append((task, split))
            continue
        if task not in tasks_by_split.get(split, set()):
            unknown.append((task, split))
            continue
        if isinstance(row_index, bool) or not isinstance(row_index, int) or row_index < 0:
            raise C.ContractError("LABELS_ROW_INDEX",
                                  f"labels[{i}] invalid row_index {row_index!r}")
        if y is not None and not C.is_finite_number(y):
            raise C.ContractError("LABELS_NONFINITE",
                                  f"labels[{i}] y is not a finite number: {y!r}",
                                  task=task, split=split, row_index=row_index)
        key = (task, split, row_index)
        if key in out:
            dups.append(key)
        out[key] = y
    if bad_split:
        raise C.ContractError("LABELS_BAD_SPLIT", "label records use invalid split",
                              examples=bad_split[:10])
    if unknown:
        raise C.ContractError("LABELS_UNKNOWN_TASK",
                              "label file has task combos not requested",
                              examples=unknown[:10], count=len(unknown))
    if dups:
        raise C.ContractError("LABELS_DUPLICATE", "duplicate label keys",
                              examples=dups[:10], count=len(dups))
    return out


def _emit(report, out):
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if out:
        d = os.path.dirname(os.path.abspath(out))
        os.makedirs(d, exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--labels-json")
    p.add_argument("--labels-csv")
    p.add_argument("--labels-csv-task")
    p.add_argument("--labels-csv-split", default="valid")
    p.add_argument("--predictions", required=True)
    p.add_argument("--schema", required=True)
    p.add_argument("--template", default=os.path.join(C.DEFAULT_OFFICIAL_BASE, "submission_template.csv"))
    p.add_argument("--split-inputs", default=None,
                   help="JSON {splits:{split:{task:n_rows}}} for completeness check")
    p.add_argument("--split", default=None,
                   help="split the predictions cover (default: labels-csv split, else 'valid')")
    p.add_argument("--out", default=None)
    a = p.parse_args(argv)
    try:
        report = score(a.labels_json, a.labels_csv, a.labels_csv_task, a.labels_csv_split,
                       a.predictions, a.schema, a.template, a.split_inputs, a.split)
        _emit(report, a.out)
        return 0
    except C.ContractError as e:
        _emit({"ok": False, "error": e.to_dict()}, a.out or None)
        sys.stderr.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
        return 2
    except SystemExit:
        raise
    except Exception as e:  # pragma: no cover
        sys.stderr.write(json.dumps({"error": "INTERNAL", "message": repr(e)}) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())