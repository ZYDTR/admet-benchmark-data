"""End-to-end smoke test for the data-eval toolkit. Standard library only.

Runs in a temp dir using the real official template plus synthetic predictions:
  1. metrics self-test (test_metrics.py)
  2. coverage check passes on full synthetic test predictions
  3. export preserves BOM/CRLF/16379 rows and only changes y_pred
  4. export rejects missing/duplicate/extra/non-finite/wrong-split predictions
  5. scorer runs against synthetic external labels

Exits non-zero on any failure. Does NOT train anything and writes only to a
temp directory (never to inputs or the deliverables tree).
"""

import csv
import io
import json
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TEMPLATE = os.path.join(ROOT, "data", "official", "submission_template.csv")


def run(args, expect_ok=True):
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True)
    if expect_ok and p.returncode != 0:
        print(p.stdout)
        print(p.stderr)
        raise SystemExit(f"command failed: {args}")
    return p


def main():
    fails = 0

    def check(name, cond, detail=""):
        nonlocal fails
        print(f"[{'ok' if cond else 'FAIL'}] {name} {detail}")
        if not cond:
            fails += 1

    # 1. metrics
    p = run([os.path.join(HERE, "test_metrics.py")])
    check("metrics self-test", "All metric self-tests passed" in p.stdout)

    with open(TEMPLATE, "rb") as fh:
        text = fh.read().decode("utf-8-sig")
    trows = list(csv.DictReader(io.StringIO(text, newline="")))
    check("template has 16379 rows", len(trows) == 16379, f"({len(trows)})")

    tmp = tempfile.mkdtemp(prefix="admet_smoke_")
    pred_path = os.path.join(tmp, "test_preds.csv")
    random.seed(0)
    with open(pred_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "split", "row_index", "y_pred"])
        for r in trows:
            v = random.random() if r["metric"] in ("AUROC", "AUPRC") else random.gauss(0, 1)
            w.writerow([r["task"], "test", r["sample_idx"], v])

    # 2. coverage
    p = run([os.path.join(HERE, "check_coverage.py"),
             "--predictions", pred_path, "--template", TEMPLATE])
    check("coverage passes on full predictions", p.returncode == 0)

    # 3. export preserves format
    out_path = os.path.join(tmp, "submission.csv")
    run([os.path.join(HERE, "export_submission.py"), "--template", TEMPLATE,
         "--predictions", pred_path, "--out", out_path])
    with open(out_path, "rb") as fh:
        ob = fh.read()
    check("export has BOM", ob[:3] == b"\xef\xbb\xbf")
    check("export uses CRLF", ob.count(b"\r\n") == ob.count(b"\n") and ob.count(b"\r\n") == 16380)
    tpl = list(csv.reader(io.StringIO(text, newline="")))
    out = list(csv.reader(io.StringIO(ob.decode("utf-8-sig"), newline="")))
    check("export row count", len(out) == len(tpl))
    check("export header identical", out[0] == tpl[0])
    bad = sum(1 for a, b in zip(tpl[1:], out[1:]) if a[:4] != b[:4] or a[5] != b[5] or b[4] == "")
    check("export preserves non-y_pred, fills y_pred", bad == 0, f"({bad} bad)")

    # 4. export rejects bad inputs
    def expect_fail(name, rows):
        pth = os.path.join(tmp, f"bad_{name}.csv")
        with open(pth, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["task", "split", "row_index", "y_pred"])
            w.writerows(rows)
        p = run([os.path.join(HERE, "export_submission.py"), "--template", TEMPLATE,
                 "--predictions", pth, "--out", os.path.join(tmp, "x.csv")],
                expect_ok=False)
        check(f"export rejects {name}", p.returncode != 0)

    base = [[r["task"], "test", r["sample_idx"], 0.5] for r in trows]
    expect_fail("missing", base[:-1])
    expect_fail("duplicate", base + [base[0]])
    expect_fail("extra", base + [["ames", "test", 999999, 0.5]])
    nf = [list(x) for x in base]; nf[0][3] = "nan"
    expect_fail("non-finite", nf)
    ws = [list(x) for x in base]; ws[0][1] = "valid"
    expect_fail("wrong-split", ws)

    # 5. scorer with synthetic external labels
    labels_dir = os.path.join(tmp, "labels")
    os.makedirs(labels_dir, exist_ok=True)
    valid_pred = os.path.join(tmp, "valid_preds.csv")
    with open(valid_pred, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "split", "row_index", "y_pred"])
        for task in sorted(set(r["task"] for r in trows)):
            vp = os.path.join(ROOT, "data", "blind_validation", task, "valid.csv")
            with open(vp, "rb") as fh:
                vrows = list(csv.DictReader(io.StringIO(fh.read().decode("utf-8-sig"), newline="")))
            lab = []
            for i, vr in enumerate(vrows):
                y = random.randint(0, 1) if task in ("ames", "bbb_martins", "bioavailability_ma",
                    "cyp2c9_substrate_carbonmangels", "cyp2c9_veith", "cyp2d6_substrate_carbonmangels",
                    "cyp2d6_veith", "cyp3a4_substrate_carbonmangels", "cyp3a4_veith", "dili",
                    "herg", "hia_hou", "pgp_broccatelli") else random.gauss(0, 1)
                lab.append(y)
                w.writerow([task, "valid", i, random.random() if y in (0, 1) and isinstance(y, int) else random.gauss(0, 1)])
            with open(os.path.join(labels_dir, task + ".csv"), "w", newline="") as lf:
                lw = csv.writer(lf); lw.writerow(["Drug_ID", "Drug", "Y"])
                for i, vr in enumerate(vrows):
                    lw.writerow([vr["Drug_ID"], vr["Drug"], lab[i]])
    p = run([os.path.join(HERE, "score.py"), "--predictions", valid_pred,
             "--labels-dir", labels_dir, "--template", TEMPLATE])
    check("scorer runs on synthetic labels", p.returncode == 0 and "AUROC" in p.stdout)

    print(f"\n{'ALL SMOKE TESTS PASSED' if fails == 0 else str(fails) + ' FAILURES'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())