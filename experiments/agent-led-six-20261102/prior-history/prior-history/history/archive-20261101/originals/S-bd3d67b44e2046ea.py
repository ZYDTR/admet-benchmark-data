"""Synthetic structure tests; none of these values are contest predictions."""

from __future__ import annotations

import copy
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from admet_harness.common import HarnessError, sha256_file
from admet_harness.submission import (
    COLUMNS, export_submission, inspect_template, validate_submission,
)


class SubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.template = self.root / "template.csv"
        self.records = self.root / "predictions.json"
        self.output = self.root / "candidate.csv"
        # Fictional tasks and molecules; intentionally retain an empty drug ID,
        # a leading-zero ID and a repeated (task, drug_id) like the real format.
        self.rows = [
            ["synthetic_class", "0", "001-fixture", "C", "", "AUROC"],
            ["synthetic_class", "1", "", "CC", "", "AUROC"],
            ["synthetic_class", "2", "001-fixture", "CCC", "", "AUROC"],
            ["synthetic_reg", "0", "002-fixture", "O", "", "MAE"],
        ]
        self.data = {
            "schema_version": 1, "run_id": "synthetic-test-only",
            "model_artifact_sha256": "a" * 64,
            "predictions": [
                {"task": "synthetic_reg", "sample_idx": "0", "y_pred": -9.0},
                {"task": "synthetic_class", "sample_idx": "2", "y_pred": 4.2},
                {"task": "synthetic_class", "sample_idx": "0", "y_pred": -0.7},
                {"task": "synthetic_class", "sample_idx": "1", "y_pred": 0.2},
            ],
        }
        self.write_csv(self.template, self.rows)
        self.write_records(self.data)

    @staticmethod
    def write_csv(path: Path, rows: list[list[str]], header=COLUMNS) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\r\n")
            writer.writerow(header)
            writer.writerows(rows)

    def write_records(self, data: object) -> None:
        self.records.write_text(json.dumps(data), encoding="utf-8")

    def candidate_rows(self) -> list[list[str]]:
        rows = copy.deepcopy(self.rows)
        for index, value in enumerate(("-0.7", "0.2", "4.2", "-9.0")):
            rows[index][4] = value
        return rows

    def assert_error(self, code: str, function, *args, **kwargs) -> HarnessError:
        with self.assertRaises(HarnessError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_template_inspection_keeps_empty_and_duplicate_drug_ids(self) -> None:
        result = inspect_template(self.template)
        self.assertEqual(result["row_count"], 4)
        self.assertEqual(result["task_count"], 2)
        self.assertEqual(result["blank_drug_id_count"], 1)
        self.assertEqual(result["duplicate_task_drug_id_count"], 1)
        self.assertEqual(result["tasks"]["synthetic_class"]["kind"], "classification")

    def test_export_restores_order_and_preserves_all_metadata(self) -> None:
        result = export_submission(self.template, self.records, self.output)
        payload = self.output.read_bytes()
        self.assertTrue(payload.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(payload.count(b"\n"), payload.count(b"\r\n"))
        actual = list(csv.reader(io.StringIO(payload.decode("utf-8-sig"), newline="")))
        self.assertEqual(actual[0], list(COLUMNS))
        for expected, exported in zip(self.rows, actual[1:]):
            self.assertEqual(expected[:4] + expected[5:], exported[:4] + exported[5:])
        self.assertEqual([float(row[4]) for row in actual[1:]], [-0.7, 0.2, 4.2, -9.0])
        self.assertTrue(validate_submission(self.template, self.output)["ok"])
        self.assertFalse(result["provenance_verified"])
        sidecar = json.loads(Path(result["provenance_path"]).read_text())
        self.assertEqual(sidecar["provenance_status"], "declared_not_verified")
        self.assertEqual(sidecar["submission"]["sha256"], sha256_file(self.output))
        self.assertEqual(sidecar["prediction_records"]["sha256"], sha256_file(self.records))
        self.assertEqual(sidecar["template"]["sha256"], sha256_file(self.template))
        self.assertEqual(sidecar["run_id"], "synthetic-test-only")

    def test_probability_checks_classification_only(self) -> None:
        self.assert_error("PROBABILITY_OUT_OF_RANGE", export_submission,
                          self.template, self.records, self.output, "probability")
        self.assertFalse(self.output.exists())
        for record in self.data["predictions"]:
            if record["task"] == "synthetic_class":
                record["y_pred"] = 0.5
        self.write_records(self.data)
        export_submission(self.template, self.records, self.output, "probability")
        self.assertTrue(validate_submission(self.template, self.output, "probability")["ok"])

    def test_row_reordering_and_changed_metadata_are_rejected_with_location(self) -> None:
        variants = []
        rows = self.candidate_rows()
        rows[0], rows[1] = rows[1], rows[0]
        variants.append(rows)
        rows = self.candidate_rows()
        rows[1][2] = "NA"
        variants.append(rows)
        rows = self.candidate_rows()
        rows[0][2] = "1-fixture"
        variants.append(rows)
        for rows in variants:
            with self.subTest(rows=rows):
                self.write_csv(self.output, rows)
                error = self.assert_error("SUBMISSION_METADATA_CHANGED", validate_submission,
                                          self.template, self.output)
                self.assertIn("line_number", error.details)
                self.assertIn("field", error.details)

    def test_missing_and_extra_rows_are_rejected(self) -> None:
        for rows in (self.candidate_rows()[:-1], self.candidate_rows() + [
                ["synthetic_reg", "1", "extra", "N", "1", "MAE"]]):
            self.write_csv(self.output, rows)
            self.assert_error("SUBMISSION_ROW_COUNT", validate_submission, self.template, self.output)

    def test_empty_nan_infinite_and_text_predictions_are_rejected(self) -> None:
        for value, expected in [("", "PREDICTION_NOT_NUMBER"), ("NaN", "PREDICTION_NOT_FINITE"),
                                ("Inf", "PREDICTION_NOT_FINITE"), ("-inf", "PREDICTION_NOT_FINITE"),
                                ("1e999", "PREDICTION_NOT_FINITE"), ("label", "PREDICTION_NOT_NUMBER")]:
            with self.subTest(value=value):
                rows = self.candidate_rows()
                rows[0][4] = value
                self.write_csv(self.output, rows)
                error = self.assert_error(expected, validate_submission, self.template, self.output)
                self.assertEqual(error.details["line_number"], 2)

    def test_unknown_metric_and_duplicate_template_key_are_rejected(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[0][5] = "RMSE"
        self.write_csv(self.template, rows)
        self.assert_error("UNKNOWN_METRIC", inspect_template, self.template)
        rows = copy.deepcopy(self.rows)
        rows[1][1] = "0"
        self.write_csv(self.template, rows)
        error = self.assert_error("DUPLICATE_ROW_KEY", inspect_template, self.template)
        self.assertEqual(error.details["first_line_number"], 2)
        self.assertEqual(error.details["line_number"], 3)

    def test_headers_column_width_csv_syntax_and_encoding_are_checked(self) -> None:
        self.write_csv(self.output, self.candidate_rows(), tuple(reversed(COLUMNS)))
        self.assert_error("CSV_HEADER_MISMATCH", validate_submission, self.template, self.output)
        rows = self.candidate_rows()
        rows[0].append("extra")
        self.write_csv(self.output, rows)
        self.assert_error("CSV_COLUMN_COUNT", validate_submission, self.template, self.output)
        self.output.write_text(",".join(COLUMNS) + '\n"unterminated', encoding="utf-8")
        self.assert_error("MALFORMED_CSV", validate_submission, self.template, self.output)
        self.output.write_bytes(b"\xff\xfe")
        self.assert_error("INVALID_UTF8", validate_submission, self.template, self.output)

    def test_wrong_record_shapes_are_harness_errors_and_leave_no_outputs(self) -> None:
        cases = [(None, "PREDICTION_RECORDS_SHAPE"), ([], "PREDICTION_RECORDS_SHAPE"),
                 ({}, "PREDICTION_RECORDS_FIELDS")]
        for field, value, code in [
            ("schema_version", True, "PREDICTION_SCHEMA_VERSION"),
            ("schema_version", 1.0, "PREDICTION_SCHEMA_VERSION"),
            ("run_id", " ", "PREDICTION_RUN_ID"),
            ("run_id", [], "PREDICTION_RUN_ID"),
            ("model_artifact_sha256", "bad", "PREDICTION_MODEL_HASH"),
            ("model_artifact_sha256", None, "PREDICTION_MODEL_HASH"),
            ("predictions", {}, "PREDICTION_LIST_SHAPE"),
            ("predictions", [None], "PREDICTION_ITEM_SHAPE"),
            ("predictions", [{}], "PREDICTION_ITEM_FIELDS"),
        ]:
            data = copy.deepcopy(self.data)
            data[field] = value
            cases.append((data, code))
        for data, code in cases:
            with self.subTest(code=code, data=data):
                self.write_records(data)
                self.assert_error(code, export_submission, self.template, self.records, self.output)
                self.assertFalse(self.output.exists())
                self.assertFalse(Path(str(self.output) + ".provenance.json").exists())

    def test_bad_prediction_items_are_not_coerced(self) -> None:
        cases = [
            ("sample_idx", 0, "PREDICTION_KEY_TYPE"),
            ("task", None, "PREDICTION_KEY_TYPE"),
            ("y_pred", "0.3", "PREDICTION_NOT_NUMBER"),
            ("y_pred", True, "PREDICTION_NOT_NUMBER"),
            ("y_pred", None, "PREDICTION_NOT_NUMBER"),
            ("y_pred", [], "PREDICTION_NOT_NUMBER"),
            ("y_pred", float("nan"), "PREDICTION_NOT_FINITE"),
            ("y_pred", float("inf"), "PREDICTION_NOT_FINITE"),
        ]
        for field, value, code in cases:
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                data["predictions"][0][field] = value
                self.write_records(data)
                error = self.assert_error(code, export_submission, self.template, self.records, self.output)
                self.assertEqual(error.details["prediction_index"], 0)

    def test_prediction_coverage_duplicate_and_unknown_keys(self) -> None:
        data = copy.deepcopy(self.data)
        data["predictions"].pop()
        self.write_records(data)
        self.assert_error("MISSING_PREDICTIONS", export_submission, self.template, self.records, self.output)
        data = copy.deepcopy(self.data)
        data["predictions"].append(copy.deepcopy(data["predictions"][0]))
        self.write_records(data)
        self.assert_error("DUPLICATE_PREDICTION_KEY", export_submission, self.template, self.records, self.output)
        data = copy.deepcopy(self.data)
        data["predictions"][0]["sample_idx"] = "not-in-template"
        self.write_records(data)
        self.assert_error("UNKNOWN_PREDICTION_KEY", export_submission, self.template, self.records, self.output)

    def test_no_clobber_and_no_input_replacement(self) -> None:
        self.output.write_text("keep me", encoding="utf-8")
        self.assert_error("OUTPUT_EXISTS", export_submission, self.template, self.records, self.output)
        self.assertEqual(self.output.read_text(), "keep me")
        self.output.unlink()
        sidecar = Path(str(self.output) + ".provenance.json")
        sidecar.write_text("keep sidecar", encoding="utf-8")
        self.assert_error("OUTPUT_EXISTS", export_submission, self.template, self.records, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(sidecar.read_text(), "keep sidecar")
        self.assert_error("OUTPUT_INPUT_COLLISION", export_submission, self.template, self.records, self.template)

    def test_malformed_json_and_duplicate_json_fields(self) -> None:
        self.records.write_text('{"schema_version":', encoding="utf-8")
        error = self.assert_error("INVALID_PREDICTION_JSON", export_submission,
                                  self.template, self.records, self.output)
        self.assertEqual(error.details["line_number"], 1)
        self.records.write_text('{"run_id":"a","run_id":"b"}', encoding="utf-8")
        error = self.assert_error("JSON_DUPLICATE_FIELD", export_submission,
                                  self.template, self.records, self.output)
        self.assertEqual(error.details["path"], str(self.records))
        self.assertEqual(error.details["field"], "run_id")

    def test_missing_files_bad_paths_and_invalid_modes_are_harness_errors(self) -> None:
        self.assert_error("INPUT_READ_ERROR", inspect_template, self.root / "missing.csv")
        self.assert_error("INVALID_PATH", inspect_template, None)
        self.assert_error("INVALID_PREDICTION_KIND", validate_submission,
                          self.template, self.output, "logit")
        self.assert_error("INVALID_PREDICTION_KIND", export_submission,
                          self.template, self.records, self.output, [])


if __name__ == "__main__":
    unittest.main()
