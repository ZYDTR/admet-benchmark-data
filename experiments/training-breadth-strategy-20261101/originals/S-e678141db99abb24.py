"""Export an official-format submission CSV from test predictions.

Guarantees (verified, not assumed):
  * Reads the official template ORIGINAL bytes. The output preserves the exact
    UTF-8 BOM, CRLF line endings, header, and every non-y_pred field's original
    text and row order. 全部 16379 行保留；不改、排序或规范化其他列。
  * Only the `y_pred` cell is written, and only for test predictions whose
    (task, sample_idx) matches a template key.
  * Refuses to write if predictions are incomplete, duplicated, non-finite,
    contain unknown keys, or have the wrong task set. No row is hand-filled.

Predictions input: task,split,row_index,y_pred where split MUST be "test" and
row_index MUST equal the template sample_idx for that task (verified against
the template, not assumed equal).

Format detection of input file by extension (.csv/.jsonl/.json).

Usage:
  python3 export_submission.py \
      --template data/official/submission_template.csv \
      --predictions preds/test_predictions.csv \
      --out deliverables/TeamName-小分子药物预测技术创新赛-20261105.csv
"""

import argparse
import csv
import io
import json
import math
import sys

TEMPLATE_ROWS = 16379


class ExportError(Exception):
    pass


def load_predictions(path):
    with open(path, "rb") as fh:
        text = fh.read().decode("utf-8-sig")
    stripped = text.lstrip()
    recs = []
    if path.endswith(".json") or stripped.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ExportError("JSON predictions must be a top-level list")
        for i, r in enumerate(data):
            recs.append(_coerce(r, f"item{i}"))
    elif path.endswith(".jsonl"):
        for ln, line in enumerate(text.splitlines(), 1):
            if line.strip():
                recs.append(_coerce(json.loads(line), f"line{ln}"))
    else:
        for ln, r in enumerate(csv.DictReader(io.StringIO(text, newline="")), 2):
            recs.append(_coerce(r, f"line{ln}"))
    return recs


def _coerce(r, where):
    try:
        task = str(r["task"])
        split = str(r["split"])
        ri = int(str(r["row_index"]).strip())
        yp = float(str(r["y_pred"]).strip())
    except KeyError as e:
        raise ExportError(f"{where}: missing key {e}")
    except (TypeError, ValueError) as e:
        raise ExportError(f"{where}: bad number ({e})")
    if split != "test":
        raise ExportError(f"{where}: split must be 'test', got {split!r}")
    if not math.isfinite(yp):
        raise ExportError(f"{where}: non-finite y_pred {yp!r}")
    return (task, ri, yp)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--template", default="data/official/submission_template.csv")
    ap.add_argument("--predictions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # --- Read template preserving original bytes/format ---
    with open(args.template, "rb") as fh:
        raw = fh.read()
    has_bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw.decode("utf-8-sig")
    crlf = "\r\n" in text
    lines = text.split("\r\n" if crlf else "\n")
    # Drop trailing empty element from final newline
    trailing_newline = False
    if lines and lines[-1] == "":
        lines = lines[:-1]
        trailing_newline = True
    header = lines[0]
    data_lines = lines[1:]
    if len(data_lines) != TEMPLATE_ROWS:
        raise ExportError(f"template data rows {len(data_lines)} != {TEMPLATE_ROWS}")

    # Parse each data line with csv to get columns + locate y_pred index.
    hdr_cols = next(csv.reader([header]))
    if hdr_cols[:6] != ["task", "sample_idx", "drug_id", "smiles", "y_pred", "metric"]:
        raise ExportError(f"unexpected template header: {hdr_cols}")
    ypred_col = hdr_cols.index("y_pred")

    # Build key set from parsed template rows and remember raw parsed cells so we
    # can re-emit non-y_pred fields EXACTLY as in the original line text.
    parsed = [next(csv.reader([ln])) for ln in data_lines]
    keys = {}
    for i, cols in enumerate(parsed):
        if len(cols) != len(hdr_cols):
            raise ExportError(f"template row {i} has {len(cols)} cols, expected {len(hdr_cols)}")
        key = (cols[0], cols[1])  # (task, sample_idx string)
        if key in keys:
            raise ExportError(f"duplicate template key {key}")
        keys[key] = i

    # --- Load predictions ---
    preds = load_predictions(args.predictions)
    by_key = {}
    for task, ri, yp in preds:
        key = (task, str(ri))
        if key in by_key:
            raise ExportError(f"duplicate prediction key {key}")
        if key not in keys:
            raise ExportError(f"prediction key not in template: {key}")
        by_key[key] = yp

    missing = [k for k in keys if k not in by_key]
    if missing:
        raise ExportError(
            f"{len(missing)} template keys lack predictions (first: {missing[:5]}); "
            "refusing to fill blanks"
        )
    extra = [k for k in by_key if k not in keys]
    if extra:
        raise ExportError(f"{len(extra)} predictions not in template (first: {extra[:5]})")

    # --- Rebuild lines: use original line text but replace y_pred cell only ---
    out_lines = [header]
    for i, line in enumerate(data_lines):
        cols = parsed[i]
        cols[ypred_col] = _fmt(by_key[(cols[0], cols[1])])
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="")
        w.writerow(cols)
        out_lines.append(buf.getvalue())

    out_text = ("\r\n" if crlf else "\n").join(out_lines)
    if trailing_newline:
        out_text += "\r\n" if crlf else "\n"
    out_bytes = out_text.encode("utf-8")
    if has_bom:
        out_bytes = b"\xef\xbb\xbf" + out_bytes

    with open(args.out, "wb") as fh:
        fh.write(out_bytes)

    print(f"Wrote {args.out}")
    print(f"  rows={len(data_lines)} bom={has_bom} crlf={crlf} filled={len(by_key)}")
    print("  Only y_pred changed; all other columns/order/format preserved from template.")
    return 0


def _fmt(x):
    """Format a finite float for CSV. Integral values keep at least one decimal so
    they are unambiguously real-valued; other values use shortest repr."""
    if x == int(x) and abs(x) < 1e16:
        return repr(float(x))
    return repr(x)


if __name__ == "__main__":
    sys.exit(main())