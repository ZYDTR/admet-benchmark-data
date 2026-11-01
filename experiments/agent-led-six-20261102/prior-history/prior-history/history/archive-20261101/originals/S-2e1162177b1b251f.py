"""Behavior tests with synthetic temporary files; no competition training data."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from admet_harness.common import HarnessError, read_json, sha256_file, write_json
from admet_harness.runtime import adapter_digest, bundle_run, check_data, execute_run, plan_run


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Process/ownership operations are mocked; these tests do not claim Docker isolation.
        self.chown_patch = patch("admet_harness.runtime.os.chown")
        self.chown_mock = self.chown_patch.start()
        self.addCleanup(self.chown_patch.stop)
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        (self.root / "docs/evidence.md").write_text("Synthetic unit-test evidence. Not an official-data approval.")
        official = self.root / "data/official"
        official.mkdir(parents=True)
        self.files = []
        for role in ("train", "validation", "test"):
            path = official / f"{role}.csv"
            path.write_text("synthetic_feature,label\n1,0\n2,1\n")
            self.files.append({"id": role, "path": f"data/official/{role}.csv", "role": role,
                               "sha256": sha256_file(path), "source_kind": "competition_official",
                               "source_url": "http://www.aiinnovation.com.cn/web/#/trackDetail?id=159",
                               "evidence": "docs/evidence.md"})
        self.manifest = {"schema_version": 1, "dataset_id": "SYNTHETIC-UNIT-TEST-ONLY", "status": "approved",
                         "review": {"reviewer": "test-fixture", "reviewed_at": "2026-10-28", "evidence": "docs/evidence.md"},
                         "files": self.files}
        write_json(self.root / "config/manifest.json", self.manifest)
        schema = {"schema_version": 1, "label_contract_status": "confirmed", "tasks": [
            {"task": "synthetic_task", "kind": "classification", "metric": "AUROC", "label_status": "confirmed",
             "positive_class": "synthetic positive", "unit": "dimensionless", "transform": "identity",
             "missing_encoding": "none", "evidence": "docs/evidence.md"}]}
        write_json(self.root / "config/tasks.json", schema)
        adapter = self.root / "adapters/test"
        adapter.mkdir(parents=True)
        for phase in ("train", "predict"):
            (adapter / f"{phase}.py").write_text("# Synthetic test adapter; not a competition model.\n")
        self.config = {"schema_version": 1, "run_id": "unit-train", "phase": "train",
                       "manifest": "config/manifest.json", "task_schema": "config/tasks.json",
                       "adapter_dir": "adapters/test", "adapter_sha256": adapter_digest(self.root, "adapters/test")["sha256"],
                       "adapter_review": {"reviewer": "test-fixture", "evidence": "docs/evidence.md"},
                       "image": "sha256:" + "a" * 64,
                       "image_review": {"reviewer": "test-fixture", "evidence": "docs/evidence.md"},
                       "seed": 42, "model": {"hidden_dim": 8}, "initialization": "random", "checkpoint": None,
                       "limits": {"cpus": 1, "memory_mb": 256, "pids": 32, "timeout_seconds": 2}}
        self.save_config()

    def save_config(self):
        write_json(self.root / "config/run.json", self.config)

    def assert_code(self, expected, function, *args):
        with self.assertRaises(HarnessError) as caught:
            function(*args)
        self.assertEqual(caught.exception.code, expected, str(caught.exception))

    def docker_success(self, command, **kwargs):
        if command[1:3] == ["image", "inspect"]:
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps([{"Id": self.config["image"], "Created": "test"}]), stderr="")
        out = self.root / "runs" / self.config["run_id"] / "artifacts"
        if self.config["phase"] == "train":
            (out / "model.pt").write_bytes(b"synthetic checkpoint")
            write_json(out / "metrics.json", {"synthetic_task": {"AUROC": 0.5}, "is_official_score": False})
            write_json(out / "result.json", {"schema_version": 1, "phase": "train", "checkpoint": "model.pt", "metrics": "metrics.json"})
        else:
            write_json(out / "predictions.json", [{"task": "synthetic_task", "sample_idx": "0", "y_pred": 0.5}])
            write_json(out / "result.json", {"schema_version": 1, "phase": "predict", "predictions": "predictions.json"})
        return subprocess.CompletedProcess(command, 0)

    def complete_training(self):
        with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=self.docker_success):
            return execute_run(self.root, self.root / "config/run.json")

    def test_pending_manifest_fails_before_training(self):
        self.manifest["status"] = "pending"
        write_json(self.root / "config/manifest.json", self.manifest)
        self.assert_code("DATA_NOT_APPROVED", plan_run, self.root, Path("config/run.json"))
        self.assertFalse((self.root / "runs").exists())

    def test_hash_change_and_external_source_rejected(self):
        (self.root / "data/official/train.csv").write_text("changed")
        self.assert_code("INPUT_HASH_MISMATCH", check_data, self.root, Path("config/manifest.json"))
        self.manifest["files"][0]["source_kind"] = "external"
        write_json(self.root / "config/manifest.json", self.manifest)
        self.assert_code("EXTERNAL_DATA_REJECTED", check_data, self.root, Path("config/manifest.json"))

    def test_file_symlink_is_rejected(self):
        path = self.root / "data/official/train.csv"
        path.unlink()
        path.symlink_to(self.root / "data/official/validation.csv")
        self.assert_code("SYMLINK_REJECTED", check_data, self.root, Path("config/manifest.json"))

    def test_training_does_not_require_or_mount_test_inputs(self):
        (self.root / "data/official/test.csv").unlink()
        plan = plan_run(self.root, self.root / "config/run.json")
        self.assertEqual({f["role"] for f in plan["data"]["files"]}, {"train", "validation"})
        self.assertFalse((self.root / "runs").exists(), "Planning must be read-only")
        command = plan["command"]
        for option, value in (("--network", "none"), ("--pull", "never"), ("--cap-drop", "ALL")):
            self.assertEqual(command[command.index(option) + 1], value)
        self.assertIn("--read-only", command)
        self.assertNotEqual(command[command.index("--user") + 1].split(":")[0], "0")
        self.assertEqual([m["target"] for m in plan["mounts"]], ["/adapter", "/inputs", "/control", "/output"])
        self.assert_code("FILE_MISSING", check_data, self.root, Path("config/manifest.json"))

    def test_declared_confirmation_without_label_fields_is_rejected(self):
        schema = read_json(self.root / "config/tasks.json")
        schema["tasks"][0]["transform"] = None
        write_json(self.root / "config/tasks.json", schema)
        self.assert_code("LABEL_CONTRACT_UNCONFIRMED", plan_run, self.root, Path("config/run.json"))

    def test_arbitrary_runtime_options_and_external_weights_are_rejected(self):
        self.config["network"] = "host"
        self.save_config()
        self.assert_code("UNKNOWN_FIELDS", plan_run, self.root, Path("config/run.json"))
        del self.config["network"]
        self.config["initialization"] = "pretrained"
        self.save_config()
        self.assert_code("INITIALIZATION_REJECTED", plan_run, self.root, Path("config/run.json"))

    def test_cached_weights_cannot_hide_inside_adapter_directory(self):
        (self.root / "adapters/test/model.pt").write_bytes(b"not admitted")
        self.assert_code("ADAPTER_ASSET_REJECTED", adapter_digest, self.root, Path("adapters/test"))

    def test_adapter_change_requires_new_review_digest(self):
        (self.root / "adapters/test/train.py").write_text("# changed code\n")
        self.assert_code("ADAPTER_HASH_MISMATCH", plan_run, self.root, Path("config/run.json"))

    def test_missing_docker_has_no_host_execution_fallback(self):
        with patch("admet_harness.runtime.shutil.which", return_value=None), patch("admet_harness.runtime.subprocess.run") as process:
            self.assert_code("DOCKER_UNAVAILABLE", execute_run, self.root, Path("config/run.json"))
            process.assert_not_called()
        self.assertFalse((self.root / "runs").exists())

    def test_missing_local_image_does_not_trigger_pull(self):
        with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", return_value=subprocess.CompletedProcess([], 1, stdout="", stderr="No such image")) as process:
            self.assert_code("IMAGE_UNAVAILABLE", execute_run, self.root, Path("config/run.json"))
            self.assertEqual(process.call_count, 1)
            self.assertEqual(process.call_args.args[0][1:3], ["image", "inspect"])

    def test_mock_execution_creates_traceable_snapshots_and_prevents_overwrite(self):
        result = self.complete_training()
        self.assertEqual(result["status"], "completed")
        record = read_json(self.root / "runs/unit-train/run.json")
        self.assertEqual(record["status"], "completed")
        self.assertFalse(record["isolation_runtime_tested"])
        inputs = read_json(self.root / "runs/unit-train/snapshot/control/inputs.json")
        self.assertEqual({f["role"] for f in inputs["files"]}, {"train", "validation"})
        for item in record["snapshots"] + record["artifacts"]:
            self.assertEqual(sha256_file(self.root / "runs/unit-train" / item["path"]), item["sha256"])
        self.assert_code("RUN_EXISTS", plan_run, self.root, Path("config/run.json"))

    def test_predict_requires_real_parent_checkpoint_record_and_hash(self):
        self.complete_training()
        checkpoint = self.root / "runs/unit-train/artifacts/model.pt"
        self.config.update(run_id="unit-predict", phase="predict", checkpoint={"run_id": "unit-train", "path": "runs/unit-train/artifacts/model.pt", "sha256": sha256_file(checkpoint)})
        self.save_config()
        plan = plan_run(self.root, Path("config/run.json"))
        self.assertEqual({f["role"] for f in plan["data"]["files"]}, {"test"})
        self.assertIn("--checkpoint", plan["command"])
        checkpoint.write_bytes(b"replaced after training")
        self.assert_code("CHECKPOINT_HASH_MISMATCH", plan_run, self.root, Path("config/run.json"))

    def test_unrecorded_checkpoint_is_not_accepted(self):
        self.complete_training()
        unrecorded = self.root / "runs/unit-train/artifacts/other.pt"
        unrecorded.write_bytes(b"not in the run record")
        self.config.update(run_id="unit-predict", phase="predict", checkpoint={"run_id": "unit-train", "path": "runs/unit-train/artifacts/other.pt", "sha256": sha256_file(unrecorded)})
        self.save_config()
        self.assert_code("CHECKPOINT_HASH_MISMATCH", plan_run, self.root, Path("config/run.json"))

    def test_bundle_contains_reproducibility_material_but_no_raw_inputs(self):
        self.complete_training()
        result = bundle_run(self.root, self.root / "runs/unit-train", self.root / "deliverables/audit.tar.gz")
        self.assertFalse(result["raw_inputs_included"])
        self.assertFalse(result["training_reproduced"])
        with tarfile.open(self.root / result["path"]) as archive:
            names = archive.getnames()
            self.assertIn("BUNDLE_INDEX.json", names)
            self.assertIn("artifacts/model.pt", names)
            self.assertIn("snapshot/adapter/train.py", names)
            self.assertFalse(any(name.startswith("snapshot/inputs/") for name in names))
            self.assertTrue(all(member.isfile() for member in archive.getmembers()))
        self.assert_code("OUTPUT_EXISTS", bundle_run, self.root, Path("runs/unit-train"), Path("deliverables/audit.tar.gz"))

    def test_bundle_rejects_changed_model_bytes(self):
        self.complete_training()
        (self.root / "runs/unit-train/artifacts/model.pt").write_bytes(b"tampered")
        self.assert_code("ARTIFACT_HASH_MISMATCH", bundle_run, self.root, Path("runs/unit-train"), Path("deliverables/audit.tar.gz"))

    def test_failed_container_is_recorded_and_not_bundled(self):
        def failure(command, **kwargs):
            if command[1:3] == ["image", "inspect"]:
                return self.docker_success(command, **kwargs)
            return subprocess.CompletedProcess(command, 7)
        with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=failure):
            self.assert_code("ADAPTER_FAILED", execute_run, self.root, Path("config/run.json"))
        record = read_json(self.root / "runs/unit-train/run.json")
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["exit_code"], 7)
        self.assert_code("RUN_NOT_COMPLETED", bundle_run, self.root, Path("runs/unit-train"), Path("deliverables/audit.tar.gz"))

    def test_output_path_escape_is_rejected_after_container_success(self):
        def bad_output(command, **kwargs):
            response = self.docker_success(command, **kwargs)
            if command[1] == "run":
                write_json(self.root / "runs/unit-train/artifacts/result.json", {"schema_version": 1, "phase": "train", "checkpoint": "../../../../docs/evidence.md", "metrics": "metrics.json"})
            return response
        with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=bad_output):
            self.assert_code("PATH_OUTSIDE_PROJECT", execute_run, self.root, Path("config/run.json"))
        self.assertEqual(read_json(self.root / "runs/unit-train/run.json")["status"], "failed")

    def test_timeout_attempts_container_removal(self):
        calls = []
        def timeout(command, **kwargs):
            calls.append(command)
            if command[1:3] == ["image", "inspect"]:
                return self.docker_success(command, **kwargs)
            if command[1] == "run":
                raise subprocess.TimeoutExpired(command, 2)
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=timeout):
            self.assert_code("RUN_TIMEOUT", execute_run, self.root, Path("config/run.json"))
        self.assertEqual(calls[-1], ["docker", "rm", "--force", "admet-unit-train"])
        self.assertEqual(read_json(self.root / "runs/unit-train/run.json")["status"], "failed")

    def test_output_ownership_failure_is_explicit_and_keeps_run_failed(self):
        self.chown_mock.side_effect = OSError(22, "Synthetic unsupported ownership")
        with patch("admet_harness.runtime.os.geteuid", return_value=0), patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=self.docker_success):
            self.assert_code("OUTPUT_OWNERSHIP_UNAVAILABLE", execute_run, self.root, Path("config/run.json"))
        self.assertEqual(read_json(self.root / "runs/unit-train/run.json")["status"], "failed")

    def test_config_changed_between_planning_and_snapshot_is_rejected(self):
        def change_config(command, **kwargs):
            response = self.docker_success(command, **kwargs)
            if command[1:3] == ["image", "inspect"]:
                self.config["model"]["hidden_dim"] = 16
                self.save_config()
            return response
        with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=change_config):
            self.assert_code("SNAPSHOT_HASH_MISMATCH", execute_run, self.root, Path("config/run.json"))

    def test_bundle_creation_race_does_not_delete_another_process_file(self):
        self.complete_training()
        output = self.root / "deliverables/audit.tar.gz"
        original_open = Path.open
        def race(path, mode="r", *args, **kwargs):
            if path == output and mode == "xb":
                with original_open(path, "wb") as other:
                    other.write(b"other process output")
                raise FileExistsError(str(path))
            return original_open(path, mode, *args, **kwargs)
        with patch.object(Path, "open", race):
            self.assert_code("OUTPUT_EXISTS", bundle_run, self.root, Path("runs/unit-train"), Path("deliverables/audit.tar.gz"))
        self.assertEqual(output.read_bytes(), b"other process output")

    def test_input_path_alias_cannot_reuse_training_data_as_validation(self):
        self.manifest["files"][1]["path"] = "data/official/./train.csv"
        self.manifest["files"][1]["sha256"] = self.manifest["files"][0]["sha256"]
        write_json(self.root / "config/manifest.json", self.manifest)
        self.assert_code("DUPLICATE_INPUT", plan_run, self.root, Path("config/run.json"))

    def test_output_path_alias_cannot_reuse_metrics_as_checkpoint(self):
        def aliases(command, **kwargs):
            response = self.docker_success(command, **kwargs)
            if command[1] == "run":
                write_json(self.root / "runs/unit-train/artifacts/result.json", {"schema_version": 1, "phase": "train", "checkpoint": "metrics.json", "metrics": "./metrics.json"})
            return response
        with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=aliases):
            self.assert_code("INVALID_ADAPTER_RESULT", execute_run, self.root, Path("config/run.json"))
        self.assertEqual(read_json(self.root / "runs/unit-train/run.json")["status"], "failed")

    def test_result_json_alias_cannot_be_declared_as_a_model_output(self):
        def aliases(command, **kwargs):
            response = self.docker_success(command, **kwargs)
            if command[1] == "run":
                write_json(self.root / "runs/unit-train/artifacts/result.json", {"schema_version": 1, "phase": "train", "checkpoint": "./result.json", "metrics": "metrics.json"})
            return response
        with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=aliases):
            self.assert_code("INVALID_ADAPTER_RESULT", execute_run, self.root, Path("config/run.json"))

    def test_invalid_config_after_image_inspection_leaves_a_failed_record(self):
        def corrupt_config(command, **kwargs):
            response = self.docker_success(command, **kwargs)
            if command[1:3] == ["image", "inspect"]:
                (self.root / "config/run.json").write_text("{invalid json")
            return response
        with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=corrupt_config):
            self.assert_code("SNAPSHOT_HASH_MISMATCH", execute_run, self.root, Path("config/run.json"))
        record = read_json(self.root / "runs/unit-train/run.json")
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["error"]["code"], "SNAPSHOT_HASH_MISMATCH")

    def test_empty_label_definition_containers_are_not_confirmation(self):
        original = read_json(self.root / "config/tasks.json")
        for field in ("unit", "transform", "missing_encoding", "positive_class"):
            for invalid in ([], {}, "   ", False, 0):
                with self.subTest(field=field, invalid=invalid):
                    schema = json.loads(json.dumps(original))
                    schema["tasks"][0][field] = invalid
                    write_json(self.root / "config/tasks.json", schema)
                    self.assert_code("LABEL_CONTRACT_UNCONFIRMED", plan_run, self.root, Path("config/run.json"))

    def test_restrictive_umask_does_not_make_worker_snapshots_unreadable(self):
        nested = self.root / "adapters/test/package"
        nested.mkdir()
        (nested / "helper.py").write_text("# synthetic nested adapter module\n")
        self.config["adapter_sha256"] = adapter_digest(self.root, "adapters/test")["sha256"]
        self.save_config()
        previous_umask = os.umask(0o077)
        try:
            self.complete_training()
            checkpoint = self.root / "runs/unit-train/artifacts/model.pt"
            self.config.update(run_id="unit-predict", phase="predict", checkpoint={"run_id": "unit-train", "path": "runs/unit-train/artifacts/model.pt", "sha256": sha256_file(checkpoint)})
            self.save_config()
            with patch("admet_harness.runtime.shutil.which", return_value="/fake/docker"), patch("admet_harness.runtime.subprocess.run", side_effect=self.docker_success):
                execute_run(self.root, Path("config/run.json"))
        finally:
            os.umask(previous_umask)
        for run in ("unit-train", "unit-predict"):
            snapshot = self.root / "runs" / run / "snapshot"
            for path in [snapshot, *snapshot.rglob("*")]:
                with self.subTest(path=path.relative_to(self.root)):
                    expected = 0o755 if path.is_dir() else 0o444
                    self.assertEqual(path.stat().st_mode & 0o777, expected)
        self.assertTrue((self.root / "runs/unit-predict/snapshot/checkpoint/model").is_file())


if __name__ == "__main__":
    unittest.main()
