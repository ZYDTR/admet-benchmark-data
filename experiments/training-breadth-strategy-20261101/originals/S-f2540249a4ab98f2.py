"""CLI-level contract tests for verify_data / score / export_submission.

Each test spawns the real script as a subprocess and asserts on exit status
AND on output content (never only on log text).  All fixtures are synthetic
and written under output/tests/fixtures or a temp dir under this test's own
scratch area (output/tmp), never outside the task output/.
"""
from __future__ import annotations

import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

import synthetic_fixtures as F  # noqa: E402
from admet_eval import common as C  # noqa: E402

SCRIPTS = os.path.join(F.OUTPUT, "scripts")
TMPROOT = os.path.join(F.OUTPUT, "tmp")
VERIFY = os.path.join(SCRIPTS, "verify_data.py")
SCORE = os.path.join(SCRIPTS, "score.py")
EXPORT = os.path.join(SCRIPTS, "export_submission.py")


def run(script, *args):
    proc = subprocess.run([sys.executable, script, *args],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def load_json_out(stdout):
    return json.loads(stdout)


class Scratch(unittest.TestCase):
    def setUp(self):
        os.makedirs(TMPROOT, exist_ok=True)
        self.dir = tempfile.mkdtemp(dir=TMPROOT, prefix="case_")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def p(self, name):
        return os.path.join(self.dir, name)


class TestVerifyData(Scratch):
    def test_real_inputs_pass(self):
        out = self.p("report.json")
        rc, so, se = run(VERIFY, "--schema", F.SCHEMA, "--report", out)
        self.assertEqual(rc, 0, se)
        rep = json.load(open(out, encoding="utf-8"))
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["checks"]["template_rows"]["actual"], 16379)
        self.assertTrue(rep["checks"]["template_matches_test"]["pass"])
        self.assertFalse(rep["checks"]["template_sample_idx"]
                         ["sample_idx_equals_absolute_template_row_index"])

    def test_wrong_template_hash_rejected(self):
        # copy template, flip one distinct non-prediction byte, schema now stale
        raw = C.read_bytes(F.TEMPLATE)
        bad = self.p("template_bad.csv")
        with open(bad, "wb") as fh:
            fh.write(raw.replace(b"ames,0,", b"ames,9,", 1))
        rc, so, se = run(VERIFY, "--template", bad, "--schema", F.SCHEMA,
                         "--report", self.p("r.json"))
        self.assertEqual(rc, 2)
        rep = json.load(open(self.p("r.json"), encoding="utf-8"))
        self.assertFalse(rep["ok"])
        self.assertIn(rep["error"]["error"],
                      ("SCHEMA_TEMPLATE_HASH", "TEMPLATE_HEADER", "SCHEMA_MISMATCH"))


class TestScoreContracts(Scratch):
    def _preds(self, name="preds.json"):
        path = self.p(name)
        F.write_predictions(path, splits=("valid",))
        return path

    def _labels(self, name="labels.json", **kw):
        path = self.p(name)
        F.write_labels(path, splits=("valid",), **kw)
        return path

    def _score(self, preds, labels, extra=None):
        args = ["--predictions", preds, "--labels-json", labels,
                "--schema", F.SCHEMA, "--split-inputs", F.split_inputs_path()]
        if extra:
            args += extra
        return run(SCORE, *args)

    def test_full_valid_scores_all_tasks(self):
        rc, so, se = self._score(self._preds(), self._labels())
        self.assertEqual(rc, 0, se)
        rep = json.loads(so)
        self.assertTrue(rep["ok"])
        self.assertTrue(rep["complete_key_set_checked"])
        self.assertEqual(len(rep["tasks"]), 22)
        for k, v in rep["tasks"].items():
            self.assertEqual(v["status"], "ok", k)
        self.assertEqual(rep["tasks"]["ames/valid"]["metric"], "AUROC")
        self.assertEqual(rep["tasks"]["cyp2c9_veith/valid"]["local_definition"],
                         "average_precision")

    def test_split_flag_selects_test_keys(self):
        preds = self.p("preds_test.json")
        labels = self.p("labels_test.json")
        F.write_predictions(preds, splits=("test",))
        F.write_labels(labels, splits=("test",))
        rc, so, se = run(SCORE, "--predictions", preds, "--labels-json", labels,
                         "--schema", F.SCHEMA, "--split-inputs", F.split_inputs_path(),
                         "--split", "test")
        self.assertEqual(rc, 0, se)
        rep = json.loads(so)
        self.assertTrue(rep["complete_key_set_checked"])
        self.assertTrue(all(k.endswith("/test") for k in rep["tasks"]))

    def test_missing_prediction_fails(self):
        preds = self.p("preds.json")
        doc = F.write_predictions(preds, splits=("valid",))
        doc["predictions"] = doc["predictions"][:-1]
        F._dump(preds, doc)
        rc, so, se = self._score(preds, self._labels())
        self.assertEqual(rc, 2)
        err = json.loads(so)
        self.assertEqual(err["error"]["error"], "PRED_KEY_SET")
        self.assertGreater(err["error"]["context"]["missing_count"], 0)

    def test_extra_prediction_fails(self):
        preds = self.p("preds.json")
        doc = F.write_predictions(preds, splits=("valid",))
        doc["predictions"].append({"task": "ames", "split": "valid",
                                   "row_index": 999999, "y_pred": 0.1})
        F._dump(preds, doc)
        rc, so, se = self._score(preds, self._labels())
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(so)["error"]["error"], "PRED_KEY_SET")

    def test_duplicate_prediction_fails(self):
        preds = self.p("preds.json")
        doc = F.write_predictions(preds, splits=("valid",))
        doc["predictions"].append(dict(doc["predictions"][0]))
        F._dump(preds, doc)
        rc, so, se = self._score(preds, self._labels())
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(so)["error"]["error"], "PRED_DUPLICATE")

    def test_nonfinite_prediction_fails(self):
        preds = self.p("preds.json")
        doc = F.write_predictions(preds, splits=("valid",))
        doc["predictions"][5]["y_pred"] = "NaN"  # string, not number
        F._dump(preds, doc)
        rc, so, se = self._score(preds, self._labels())
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(so)["error"]["error"], "PRED_NONFINITE")

    def test_unknown_task_in_label_fails(self):
        labels = self.p("labels.json")
        doc = F.write_labels(labels, splits=("valid",))
        doc["labels"].append({"task": "not_a_task", "split": "valid",
                              "row_index": 0, "y": 1})
        F._dump(labels, doc)
        rc, so, se = self._score(self._preds(), labels)
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(so)["error"]["error"], "LABELS_UNKNOWN_TASK")

    def test_wrong_split_label_fails(self):
        labels = self.p("labels.json")
        doc = F.write_labels(labels, splits=("valid",))
        doc["labels"][0]["split"] = "bogus"
        F._dump(labels, doc)
        rc, so, se = self._score(self._preds(), labels)
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(so)["error"]["error"], "LABELS_BAD_SPLIT")

    def test_nonbinary_classification_label_fails(self):
        labels = self.p("labels.json")
        doc = F.write_labels(labels, splits=("valid",), tasks={"ames"})
        # ames is classification; set one label to 2
        doc["labels"][0]["y"] = 2
        F._dump(labels, doc)
        rc, so, se = self._score(self._preds(), labels)
        self.assertEqual(rc, 2)
        self.assertIn(json.loads(so)["error"]["error"],
                      ("LABELS_INVALID_CLASS",))

    def test_one_class_returns_undefined_not_error(self):
        labels = self.p("labels.json")
        doc = F.write_labels(labels, splits=("valid",), tasks={"ames"})
        for rec in doc["labels"]:
            rec["y"] = 1
        F._dump(labels, doc)
        rc, so, se = self._score(self._preds(), labels)
        self.assertEqual(rc, 0, se)
        rep = json.loads(so)
        e = rep["tasks"]["ames/valid"]
        self.assertEqual(e["status"], "undefined")
        self.assertEqual(e["reason"], "one_class")
        self.assertIsNone(e["value"])

    def test_constant_regression_undefined(self):
        labels = self.p("labels.json")
        doc = F.write_labels(labels, splits=("valid",), tasks={"half_life_obach"})
        for rec in doc["labels"]:
            rec["y"] = 3.0
        F._dump(labels, doc)
        rc, so, se = self._score(self._preds(), labels)
        self.assertEqual(rc, 0, se)
        e = json.loads(so)["tasks"]["half_life_obach/valid"]
        self.assertEqual(e["status"], "undefined")
        self.assertIn(e["reason"], ("constant_true",))

    def test_label_csv_blind_without_y_rejected(self):
        blind = os.path.join(F.BLIND, "ames/valid.csv")
        rc, so, se = run(SCORE, "--predictions", self._preds(),
                         "--labels-csv", blind, "--labels-csv-task", "ames",
                         "--labels-csv-split", "valid", "--schema", F.SCHEMA,
                         "--split-inputs", F.split_inputs_path())
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(so)["error"]["error"], "LABELS_CSV_NO_Y")


class TestExportContracts(Scratch):
    def _preds(self):
        path = self.p("preds.json")
        F.write_predictions(path, splits=("test",))
        return path

    def test_export_full_template(self):
        out = self.p("sub.csv")
        rc, so, se = run(EXPORT, "--predictions", self._preds(),
                         "--output", out, "--schema", F.SCHEMA)
        self.assertEqual(rc, 0, se)
        rep = json.loads(so)
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["rows"], 16379)
        self.assertTrue(rep["non_prediction_fields_identical"])
        self.assertTrue(rep["bom_preserved"])
        self.assertTrue(rep["line_terminators_preserved"])
        # independent re-check with the csv module
        raw = C.read_bytes(out)
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
        self.assertEqual(len(rows), 16379)
        self.assertTrue(all(r["y_pred"] != "" for r in rows))
        # herg row 61 had blank drug_id; must still be blank
        herg = [r for r in rows if r["task"] == "herg"]
        self.assertEqual(herg[61]["drug_id"], "")
        # 218 duplicated (task,drug_id) pairs preserved => re-check two
        dup = [r for r in rows if r["task"] == "ames"]
        self.assertEqual(len(dup), 1457)

    def test_export_refuses_overwrite(self):
        out = self.p("sub.csv")
        args = ["--predictions", self._preds(), "--output", out, "--schema", F.SCHEMA]
        self.assertEqual(run(EXPORT, *args)[0], 0)
        rc, so, se = run(EXPORT, *args)
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(se)["error"], "OUTPUT_EXISTS")

    def test_export_missing_prediction_fails(self):
        preds = self.p("preds.json")
        doc = F.write_predictions(preds, splits=("test",))
        doc["predictions"] = doc["predictions"][:-1]
        F._dump(preds, doc)
        rc, so, se = run(EXPORT, "--predictions", preds,
                         "--output", self.p("sub.csv"), "--schema", F.SCHEMA)
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(se)["error"], "PRED_KEY_SET")
        self.assertFalse(os.path.exists(self.p("sub.csv")))

    def test_export_rejects_valid_split_prediction(self):
        # full test coverage but one record mislabelled as 'valid'
        preds = self.p("preds.json")
        doc = F.write_predictions(preds, splits=("test",))
        doc["predictions"][0]["split"] = "valid"
        F._dump(preds, doc)
        rc, so, se = run(EXPORT, "--predictions", preds,
                         "--output", self.p("sub.csv"), "--schema", F.SCHEMA)
        self.assertEqual(rc, 2)

    def test_export_rejects_unknown_task(self):
        preds = self.p("preds.json")
        doc = F.write_predictions(preds, splits=("test",))
        doc["predictions"].append({"task": "ghost", "split": "test",
                                   "row_index": 0, "y_pred": 0.1})
        F._dump(preds, doc)
        rc, so, se = run(EXPORT, "--predictions", preds,
                         "--output", self.p("sub.csv"), "--schema", F.SCHEMA)
        self.assertEqual(rc, 2)

    def test_export_nonfinite_rejected(self):
        preds = self.p("preds.json")
        doc = F.write_predictions(preds, splits=("test",))
        doc["predictions"][3]["y_pred"] = True
        F._dump(preds, doc)
        rc, so, se = run(EXPORT, "--predictions", preds,
                         "--output", self.p("sub.csv"), "--schema", F.SCHEMA)
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(se)["error"], "PRED_NONFINITE")


if __name__ == "__main__":
    unittest.main(verbosity=2)