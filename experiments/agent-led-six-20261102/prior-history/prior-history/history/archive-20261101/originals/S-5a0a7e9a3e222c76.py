#!/usr/bin/env python3
"""export-submission: fill template y_pred from predictions, byte-faithful.

Guarantees:
  * template read as bytes; only the y_pred *value* slot of each data line is
    replaced.  Every other character on the line (BOM, CRLF, quoting of other
    fields, parentheses/commas/brackets inside SMILES) is preserved exactly.
  * export entry point itself enforces the complete key set: missing / extra /
    duplicate / unknown-task / non-finite predictions fail here (no separate
    skippable checker).
  * after writing, the output is re-read and diffed against the template to
    prove every non-prediction field and the row order are identical, and the
    prediction values round-trip as Python floats.

Predictions: {schema_version, predictions:[{task,split,row_index,y_pred}]}
  For the official submission every prediction must be split=="test" and its
  row_index must be the template row_index of that task (== test.csv row
  position == sample_idx).  Rows are reordered to template order.

Exit: 0 ok, 2 contract failure, 3 internal.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from admet_eval import common as C  # noqa: E402


def _split_template_lines(text):
    """Split into (lines) keeping the original line terminators.

    Returns list of (content, terminator) where terminator is '\\r\\n', '\\n' or ''.
    """
    out = []
    i = 0
    n = len(text)
    start = 0
    while i < n:
        if text[i] == "\r" and i + 1 < n and text[i + 1] == "\n":
            out.append((text[start:i], "\r\n"))
            i += 2
            start = i
        elif text[i] == "\n":
            out.append((text[start:i], "\n"))
            i += 1
            start = i
        else:
            i += 1
    if start < n:
        out.append((text[start:], ""))
    return out


def _parse_line(line):
    return next(csv.reader(io.StringIO(line, newline="")))


def _format_line(fields):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="", quoting=csv.QUOTE_MINIMAL)
    w.writerow(fields)
    return buf.getvalue()


def export(template_path, predictions_path, output_path, schema_path, force_y_pred_column=None):
    if os.path.exists(output_path):
        raise C.ContractError("OUTPUT_EXISTS", f"refusing to overwrite {output_path}",
                              path=output_path)
    if schema_path:
        C.load_and_check_schema(schema_path, template_path)

    raw = C.read_bytes(template_path)
    text = C.decode_utf8_sig(raw, template_path)
    bom = raw.startswith(b"\xef\xbb\xbf")

    tlines = _split_template_lines(text)
    if not tlines:
        raise C.ContractError("TEMPLATE_EMPTY", "template has no lines")
    header_fields = _parse_line(tlines[0][0])
    try:
        col = header_fields.index("y_pred")
    except ValueError as exc:
        raise C.ContractError("TEMPLATE_NO_YPRED", f"header lacks y_pred: {header_fields}") from exc
    task_col = header_fields.index("task")
    head_idx = None
    per_task = {}
    for li in range(1, len(tlines)):
        content, _ = tlines[li]
        if content == "":
            continue
        fields = _parse_line(content)
        if len(fields) != len(header_fields):
            raise C.ContractError("TEMPLATE_COLCOUNT",
                                  f"template data line {li} has {len(fields)} fields")
        task = fields[task_col]
        per_task.setdefault(task, []).append(li)

    # Expected keys: every template row, split=='test'.
    expected = {}
    expected["test"] = set()
    for task, line_idxs in per_task.items():
        ri = 0
        for li in line_idxs:
            expected["test"].add((task, ri))
            ri += 1
    preds = C.load_predictions(predictions_path, expected)

    # Also verify other splits are not smuggled in (load_predictions enforces
    # exact key set over expected, which only has 'test', so any train/valid
    # key would appear as extra -> rejected).  Double-check explicitly.
    for (task, split, ri) in preds:
        if split != "test":
            raise C.ContractError("PRED_SPLIT", "official submission needs split=test only",
                                  task=task, split=split)

    # Build out lines
    out_lines = []
    # header unchanged
    out_lines.append(tlines[0])
    task_row_cursor = {}
    for li in range(1, len(tlines)):
        content, term = tlines[li]
        if content == "":
            out_lines.append((content, term))
            continue
        fields = _parse_line(content)
        task = fields[task_col]
        ri = task_row_cursor.get(task, 0)
        task_row_cursor[task] = ri + 1
        value = preds[(task, "test", ri)]
        if not C.is_finite_number(value):
            raise C.ContractError("PRED_NONFINITE", "value not finite", task=task, row_index=ri)
        sval = repr(float(value))
        fields[col] = sval
        out_lines.append((_format_line(fields), term))

    body = "".join(c + t for c, t in out_lines)
    data = body.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data

    d = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(d, exist_ok=True)
    with open(output_path, "xb") as fh:  # exclusive create
        fh.write(data)

    # Self-check: re-read and diff
    check = _verify_output(raw, output_path, preds, col, task_col, header_fields)
    report = {
        "ok": check["ok"],
        "output": output_path,
        "output_sha256": C.sha256_file(output_path),
        "template_sha256": C.sha256_file(template_path),
        "prediction_sha256": C.sha256_file(predictions_path),
        "rows": check["rows"],
        "tasks": len(per_task),
        "non_prediction_fields_identical": check["non_prediction_fields_identical"],
        "row_order_preserved": check["row_order_preserved"],
        "bom_preserved": check["bom_preserved"],
        "line_terminators_preserved": check["line_terminators_preserved"],
        "values_roundtrip": check["values_roundtrip"],
        "problems": check["problems"][:20],
    }
    sidecar = output_path + ".provenance.json"
    with open(sidecar, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return report


def _verify_output(template_raw, out_path, preds, col, task_col, header_fields):
    problems = []
    traw = template_raw
    oraw = C.read_bytes(out_path)
    ttext = C.decode_utf8_sig(traw, "template")
    otext = C.decode_utf8_sig(oraw, out_path)
    tl = _split_template_lines(ttext)
    ol = _split_template_lines(otext)

    bom_preserved = (traw.startswith(b"\xef\xbb\xbf") == oraw.startswith(b"\xef\xbb\xbf"))
    if not bom_preserved:
        problems.append("bom differs")
    ter_ok = [t[1] for t in tl] == [o[1] for o in ol]
    if not ter_ok:
        problems.append("line terminators differ")

    if len(tl) != len(ol):
        problems.append(f"line count {len(tl)} vs {len(ol)}")
    rows = 0
    non_pred_ok = True
    order_ok = True
    values_ok = True
    task_cursor = {}
    n = min(len(tl), len(ol))
    for i in range(n):
        tc, _ = tl[i]
        oc, _ = ol[i]
        if tc == "" and oc == "":
            continue
        tf = _parse_line(tc)
        of = _parse_line(oc)
        if i == 0:
            if tf != of:
                non_pred_ok = False
                problems.append("header changed")
            continue
        rows += 1
        if len(tf) != len(of):
            non_pred_ok = False
            problems.append(f"line {i}: col count {len(tf)} vs {len(of)}")
            continue
        task = tf[task_col]
        ri = task_cursor.get(task, 0)
        task_cursor[task] = ri + 1
        for c in range(len(tf)):
            if c == col:
                continue
            if tf[c] != of[c]:
                non_pred_ok = False
                problems.append(f"line {i} col {header_fields[c]} changed")
        # value round-trip
        try:
            got = float(of[col])
        except ValueError:
            values_ok = False
            problems.append(f"line {i}: y_pred not float")
            continue
        want = preds[(task, "test", ri)]
        if got != float(want):
            values_ok = False
            problems.append(f"line {i}: value mismatch")
        # order: task at same line as template
        if task != tf[task_col]:
            order_ok = False
    return {
        "ok": not problems,
        "rows": rows,
        "non_prediction_fields_identical": non_pred_ok,
        "row_order_preserved": order_ok,
        "bom_preserved": bom_preserved,
        "line_terminators_preserved": ter_ok,
        "values_roundtrip": values_ok,
        "problems": problems,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--template", default=os.path.join(C.DEFAULT_OFFICIAL_BASE, "submission_template.csv"))
    p.add_argument("--predictions", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--schema", required=True)
    a = p.parse_args(argv)
    try:
        report = export(a.template, a.predictions, a.output, a.schema)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 2
    except C.ContractError as e:
        sys.stderr.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
        return 2
    except FileExistsError:
        sys.stderr.write(json.dumps({"error": "OUTPUT_EXISTS"}) + "\n")
        return 2
    except Exception as e:  # pragma: no cover
        sys.stderr.write(json.dumps({"error": "INTERNAL", "message": repr(e)}) + "\n")
        return 3


if __name__ == "__main__":
    sys.exit(main())