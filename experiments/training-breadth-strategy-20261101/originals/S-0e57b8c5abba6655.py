"""Local lineage tests use simulated records, not trained competition models."""
import csv
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from admet_harness.candidate import verify_candidate
from admet_harness.common import HarnessError, read_json, sha256_file, write_json
from admet_harness.submission import export_submission


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.train = self.root / "runs/train-one"
        self.predict = self.root / "runs/predict-one"
        for path in (self.train / "artifacts", self.predict / "artifacts", self.root / "data/official"):
            path.mkdir(parents=True)
        self.weight = self.train / "artifacts/model.bin"
        self.weight.write_bytes(b"SYNTHETIC TEST CHECKPOINT")
        self.weight_hash = sha256_file(self.weight)
        write_json(self.train / "run.json", {"run_id": "train-one", "phase": "train", "status": "completed",
            "artifacts": [{"path": "artifacts/model.bin", "kind": "checkpoint", "sha256": self.weight_hash}]})
        self.template = self.root / "data/official/template.csv"
        with self.template.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["task", "sample_idx", "drug_id", "smiles", "y_pred", "metric"])
            writer.writerow(["fake-task", "0", "001", "C", "", "AUROC"])
        self.records = self.predict / "artifacts/predictions.json"
        write_json(self.records, {"schema_version": 1, "run_id": "predict-one", "model_artifact_sha256": self.weight_hash,
            "predictions": [{"task": "fake-task", "sample_idx": "0", "y_pred": 0.7}]})
        input_item = {"id": "template-one", "role": "submission_template", "sha256": sha256_file(self.template), "source_kind": "competition_official"}
        (self.predict / "snapshot/inputs").mkdir(parents=True)
        shutil.copyfile(self.template, self.predict / "snapshot/inputs/template.csv")
        write_json(self.predict / "snapshot/control/inputs.json", {"files": [{**input_item, "path": "/inputs/template.csv"}]})
        write_json(self.predict / "snapshot/manifest.json", {"status": "approved", "files": [input_item]})
        snapshots = [{"path": p.relative_to(self.predict).as_posix(), "sha256": sha256_file(p)} for p in (self.predict / "snapshot").rglob("*") if p.is_file()]
        write_json(self.predict / "run.json", {"run_id": "predict-one", "phase": "predict", "status": "completed",
            "snapshots": snapshots, "data_manifest_sha256": sha256_file(self.predict / "snapshot/manifest.json"),
            "checkpoint": {"run_id": "train-one", "path": "runs/train-one/artifacts/model.bin", "sha256": self.weight_hash,
                           "training_record_sha256": sha256_file(self.train / "run.json")},
            "artifacts": [{"path": "artifacts/predictions.json", "kind": "predictions", "sha256": sha256_file(self.records)}]})
        write_json(self.predict / "plan.json", {"run_id": "predict-one", "phase": "predict", "data": {"files": [input_item]}})
        self.submission = self.root / "deliverables/candidate.csv"
        export_submission(self.template, self.records, self.submission)
        self.sidecar = Path(str(self.submission) + ".provenance.json")

    def test_valid_local_chain_is_narrowly_reported(self):
        result = verify_candidate(self.root, self.submission)
        self.assertTrue(result["local_lineage_consistent"])
        self.assertFalse(result["historical_external_data_use_proven"])
        self.assertEqual(result["official_acceptance"], "not_checked")

    def test_edited_csv_fails_even_if_sidecar_hash_is_updated(self):
        text = self.submission.read_text(encoding="utf-8-sig").replace("0.7", "0.9")
        self.submission.write_text(text, encoding="utf-8-sig")
        sidecar = read_json(self.sidecar)
        sidecar["submission"]["sha256"] = sha256_file(self.submission)
        write_json(self.sidecar, sidecar)
        with self.assertRaises(HarnessError) as error:
            verify_candidate(self.root, self.submission)
        self.assertEqual(error.exception.code, "CANDIDATE_VALUES_DIFFER")

    def test_a_declared_run_without_completed_training_is_rejected(self):
        record = read_json(self.train / "run.json")
        record["status"] = "failed"
        write_json(self.train / "run.json", record)
        with self.assertRaises(HarnessError) as error:
            verify_candidate(self.root, self.submission)
        self.assertEqual(error.exception.code, "CANDIDATE_RUN_INCOMPLETE")

    def test_weight_tampering_is_rejected(self):
        self.weight.write_bytes(b"different weight")
        with self.assertRaises(HarnessError) as error:
            verify_candidate(self.root, self.submission)
        self.assertEqual(error.exception.code, "CANDIDATE_ARTIFACT")

    def test_template_must_have_been_registered_in_prediction_plan(self):
        write_json(self.predict / "plan.json", {"run_id": "predict-one", "phase": "predict", "data": {"files": []}})
        with self.assertRaises(HarnessError) as error:
            verify_candidate(self.root, self.submission)
        self.assertEqual(error.exception.code, "CANDIDATE_TEMPLATE_UNREGISTERED")

    def test_verifier_uses_the_exporters_float_normalization(self):
        records = read_json(self.records)
        records["predictions"][0]["y_pred"] = 9007199254740993
        write_json(self.records, records)
        run = read_json(self.predict / "run.json")
        run["artifacts"][0]["sha256"] = sha256_file(self.records)
        write_json(self.predict / "run.json", run)
        candidate = self.root / "deliverables/large-number.csv"
        export_submission(self.template, self.records, candidate)
        self.assertTrue(verify_candidate(self.root, candidate)["local_lineage_consistent"])

    def test_changed_plan_cannot_certify_a_different_molecule_template(self):
        replacement = self.root / "data/official/replacement.csv"
        replacement.write_text(self.template.read_text(encoding="utf-8-sig").replace(",C,", ",N,"), encoding="utf-8-sig")
        plan = read_json(self.predict / "plan.json")
        plan["data"]["files"][0]["sha256"] = sha256_file(replacement)
        write_json(self.predict / "plan.json", plan)
        candidate = self.root / "deliverables/replaced-template.csv"
        export_submission(replacement, self.records, candidate)
        with self.assertRaises(HarnessError) as error:
            verify_candidate(self.root, candidate)
        self.assertEqual(error.exception.code, "CANDIDATE_TEMPLATE_UNREGISTERED")

    def test_frozen_input_control_must_match_the_recorded_hash(self):
        write_json(self.predict / "snapshot/control/inputs.json", {"files": []})
        with self.assertRaises(HarnessError) as error:
            verify_candidate(self.root, self.submission)
        self.assertEqual(error.exception.code, "CANDIDATE_SNAPSHOT_CHANGED")


if __name__ == "__main__":
    unittest.main()
