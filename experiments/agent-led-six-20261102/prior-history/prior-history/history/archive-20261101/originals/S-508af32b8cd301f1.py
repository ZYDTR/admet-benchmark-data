"""Hand-calculated, synthetic metric cases; no competition labels are used."""

from __future__ import annotations

import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from admet_harness.common import HarnessError
from admet_harness.evaluation import evaluate_records


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.schema_path = self.root / "schema.json"
        self.records_path = self.root / "records.json"
        self.schema = {"label_contract_status": "unconfirmed", "tasks": [
            {"task": "mae_fixture", "kind": "regression", "metric": "MAE"},
            {"task": "rho_fixture", "kind": "regression", "metric": "Spearman"},
            {"task": "roc_fixture", "kind": "classification", "metric": "AUROC"},
            {"task": "ap_fixture", "kind": "classification", "metric": "AUPRC"},
        ]}
        self.save_schema()

    def save_schema(self) -> None:
        self.schema_path.write_text(json.dumps(self.schema), encoding="utf-8")

    @staticmethod
    def rows(task: str, truths: list, predictions: list) -> list[dict]:
        return [{"task": task, "sample_id": str(i), "y_true": truth, "y_pred": prediction}
                for i, (truth, prediction) in enumerate(zip(truths, predictions))]

    def evaluate(self, rows: list) -> dict:
        self.records_path.write_text(json.dumps({"schema_version": 1,
                                                "split_id": "synthetic-validation", "records": rows}), encoding="utf-8")
        return evaluate_records(self.schema_path, self.records_path)

    def assert_error(self, code: str, rows: list) -> HarnessError:
        with self.assertRaises(HarnessError) as caught:
            self.evaluate(rows)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_hand_calculated_metrics_include_ties(self) -> None:
        rows = (self.rows("mae_fixture", [1, 3, -2], [2, 1, 0])
                + self.rows("rho_fixture", [1, 1, 2], [1, 2, 3])
                + self.rows("roc_fixture", [1, 0, 1, 0], [0.8, 0.8, 0.3, 0.1])
                + self.rows("ap_fixture", [1, 0, 1], [0.9, 0.9, 0.1]))
        result = self.evaluate(rows)
        expected = {"mae_fixture": 5 / 3, "rho_fixture": math.sqrt(3) / 2,
                    "roc_fixture": 5 / 8, "ap_fixture": 7 / 12}
        for name, value in expected.items():
            self.assertEqual(result["tasks"][name]["status"], "ok")
            self.assertAlmostEqual(result["tasks"][name]["value"], value)
        self.assertEqual(result["tasks"]["ap_fixture"]["local_definition"], "average_precision")
        self.assertEqual(result["tasks"]["ap_fixture"]["official_equivalence"], "unconfirmed")
        self.assertNotIn("total_score", result)
        self.assertNotIn("official_score", result)

    def test_average_precision_is_not_trapezoid_and_ties_ignore_input_order(self) -> None:
        rows = self.rows("ap_fixture", [1, 0, 1], [0.9, 0.8, 0.7])
        value = self.evaluate(rows)["tasks"]["ap_fixture"]["value"]
        self.assertAlmostEqual(value, 5 / 6)
        self.assertNotAlmostEqual(value, 19 / 24)  # PR trapezoidal area for this example.
        tied = self.rows("ap_fixture", [1, 0, 1], [0.9, 0.9, 0.1])
        first = self.evaluate(tied)["tasks"]["ap_fixture"]["value"]
        second = self.evaluate([tied[1], tied[0], tied[2]])["tasks"]["ap_fixture"]["value"]
        self.assertEqual(first, second)

    def test_all_schema_tasks_reported_for_missing_and_absent_records(self) -> None:
        result = self.evaluate(self.rows("mae_fixture", [None, None], [3, 4]))
        self.assertEqual(set(result["tasks"]), {task["task"] for task in self.schema["tasks"]})
        mae = result["tasks"]["mae_fixture"]
        self.assertEqual((mae["n"], mae["missing"], mae["records"]), (0, 2, 2))
        self.assertEqual((mae["status"], mae["reason"], mae["value"]),
                         ("undefined", "no_labeled_records", None))
        self.assertEqual(result["tasks"]["roc_fixture"]["reason"], "no_records")
        empty = self.evaluate([])
        self.assertTrue(all(task["reason"] == "no_records" for task in empty["tasks"].values()))

    def test_missing_labels_do_not_change_denominator(self) -> None:
        result = self.evaluate(self.rows("mae_fixture", [1, None, 5], [2, 900, 2]))
        task = result["tasks"]["mae_fixture"]
        self.assertEqual((task["n"], task["missing"]), (2, 1))
        self.assertEqual(task["value"], 2.0)

    def test_one_class_policy_for_roc_and_local_ap(self) -> None:
        for task in ("roc_fixture", "ap_fixture"):
            for label in (0, 1):
                with self.subTest(task=task, label=label):
                    result = self.evaluate(self.rows(task, [label, label], [-3, 9]))["tasks"][task]
                    self.assertEqual(result["status"], "undefined")
                    self.assertEqual(result["reason"], "one_class")
                    self.assertIsNone(result["value"])

    def test_spearman_constant_and_insufficient_cases(self) -> None:
        for truths, predictions, reason in [
            ([1], [2], "insufficient_samples"),
            ([1, 1], [1, 2], "constant_true"),
            ([1, 2], [3, 3], "constant_prediction"),
            ([1, 1], [3, 3], "constant_true_and_prediction"),
        ]:
            result = self.evaluate(self.rows("rho_fixture", truths, predictions))["tasks"]["rho_fixture"]
            self.assertEqual(result["reason"], reason)
            self.assertIsNone(result["value"])

    def test_constant_classification_scores_handle_ties(self) -> None:
        rows = (self.rows("roc_fixture", [1, 0, 0, 0], [7, 7, 7, 7])
                + self.rows("ap_fixture", [1, 0, 0, 0], [7, 7, 7, 7]))
        tasks = self.evaluate(rows)["tasks"]
        self.assertEqual(tasks["roc_fixture"]["value"], 0.5)
        self.assertEqual(tasks["ap_fixture"]["value"], 0.25)

    def test_duplicate_ids_unknown_tasks_and_invalid_labels_fail(self) -> None:
        row = self.rows("roc_fixture", [1], [0.5])[0]
        error = self.assert_error("EVALUATION_DUPLICATE_SAMPLE", [row, copy.deepcopy(row)])
        self.assertEqual(error.details["record_index"], 1)
        self.assertEqual(error.details["first_record_index"], 0)
        self.assert_error("EVALUATION_UNKNOWN_TASK", self.rows("unknown", [1], [1]))
        self.assert_error("EVALUATION_BINARY_LABEL", self.rows("roc_fixture", [2], [1]))
        self.assert_error("EVALUATION_BINARY_LABEL", self.rows("ap_fixture", [0.5], [1]))
        self.assert_error("EVALUATION_NOT_NUMBER", self.rows("roc_fixture", [True], [1]))
        self.assert_error("EVALUATION_NOT_NUMBER", self.rows("mae_fixture", [1], ["0.3"]))

    def test_nonfinite_values_are_errors_even_when_label_is_missing(self) -> None:
        for field in ("y_true", "y_pred"):
            for number in (float("nan"), float("inf"), float("-inf")):
                row = self.rows("mae_fixture", [None], [1])[0]
                row[field] = number
                self.assert_error("EVALUATION_NONFINITE_JSON", [row])
        self.records_path.write_text(
            '{"schema_version":1,"split_id":"s","records":[{"task":"mae_fixture",'
            '"sample_id":"0","y_true":null,"y_pred":1e999}]}', encoding="utf-8")
        with self.assertRaises(HarnessError) as caught:
            evaluate_records(self.schema_path, self.records_path)
        self.assertEqual(caught.exception.code, "EVALUATION_NOT_FINITE")

    def test_malformed_shapes_and_json_never_escape_as_tracebacks(self) -> None:
        cases = [None, [], {}, {"schema_version": True, "split_id": "s", "records": []},
                 {"schema_version": 1, "split_id": " ", "records": []},
                 {"schema_version": 1, "split_id": "s", "records": {}},
                 {"schema_version": 1, "split_id": "s", "records": [None]},
                 {"schema_version": 1, "split_id": "s", "records": [{}]}]
        for data in cases:
            with self.subTest(data=data):
                self.records_path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaises(HarnessError):
                    evaluate_records(self.schema_path, self.records_path)
        for raw, code in [('{"schema_version":', "EVALUATION_INVALID_JSON"),
                          ('{"split_id":"a","split_id":"b"}', "EVALUATION_DUPLICATE_JSON_FIELD")]:
            self.records_path.write_text(raw, encoding="utf-8")
            with self.assertRaises(HarnessError) as caught:
                evaluate_records(self.schema_path, self.records_path)
            self.assertEqual(caught.exception.code, code)
            self.assertEqual(caught.exception.details["path"], str(self.records_path))

    def test_schema_validation_and_label_warning(self) -> None:
        result = self.evaluate([])
        warning = next(item for item in result["warnings"] if item["code"] == "LABEL_CONTRACT_UNCONFIRMED")
        self.assertEqual(warning["label_contract_status"], "unconfirmed")
        for mutation, code in [
            ({"task": "x", "kind": "classification", "metric": "MAE"}, "EVALUATION_TASK_KIND"),
            ({"task": "x", "kind": "regression", "metric": "RMSE"}, "EVALUATION_UNKNOWN_METRIC"),
            ({"task": [], "kind": "regression", "metric": "MAE"}, "EVALUATION_TASK_FIELD"),
        ]:
            self.schema["tasks"] = [mutation]
            self.save_schema()
            with self.assertRaises(HarnessError) as caught:
                self.evaluate([])
            self.assertEqual(caught.exception.code, code)

    def test_large_finite_mae_does_not_overflow_sum_and_extreme_result_errors(self) -> None:
        task = self.evaluate(self.rows("mae_fixture", [1e308, 1e308], [0, 0]))["tasks"]["mae_fixture"]
        self.assertEqual(task["value"], 1e308)
        self.assert_error("EVALUATION_NUMERIC_ERROR", self.rows("mae_fixture", [1e308], [-1e308]))


if __name__ == "__main__":
    unittest.main()
