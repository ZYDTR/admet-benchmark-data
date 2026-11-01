"""Synthetic, offline behavioral counterexamples. No ADMET labels or network."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import stat
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from check_gateway import (FILES, ITEMS, LAYERS, KINDS, ContractError, check_bundle,
                           inspect_zip, strict_json, validate_dispatch_gate)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    expected = {"request_id": "SYNTHETIC-request", "round_id": "SYNTHETIC-round",
                "manifest_sha256": "b" * 64}
    commit = "a" * 40
    plan = {"fixture_only": True, "repository": "https://github.com/ZYDTR/admet-benchmark-data",
            "source_commit": commit, "entries": []}
    for layer in LAYERS:
        plan["entries"].append({"entry_id": "fixture-" + layer, "layer": layer,
                               "uri": "https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/"
                                      + commit + "/fixture/" + layer + ".txt",
                               "source_version": commit, "required_read_mode": "original"})
    checks = []
    oracle = {**expected, "source_commit": commit, "fixture_only": True, "checks": []}
    answers = [{"rule": "SYNTHETIC rule", "source": "fixture-rule-v1"},
               ["fixture-event-1", "fixture-event-2"], "1.250000000"]
    for index, kind in enumerate(KINDS):
        check_id = "fixture-check-" + str(index + 1)
        checks.append({"check_id": check_id, "kind": kind, "answer": answers[index],
                       "input_locator": "fixture-only:" + str(index),
                       "method": "synthetic exact observation, not an actual research result",
                       "evidence_refs": ["fixture-only"]})
        oracle["checks"].append({"check_id": check_id, "kind": kind,
                                "comparison": "decimal" if index == 2 else "exact_json",
                                "expected": "1.25" if index == 2 else answers[index],
                                "absolute_tolerance": "0"})
    review = {**expected, "schema_version": 1, "fixture_only": True, "status": "inconclusive",
              "read_receipt": [{**item, "read_mode": "original",
                                "evidence_locator": "fixture:line-1",
                                "observed_fact": "SYNTHETIC fact; no real source was read",
                                "limitation": "fixture only"}
                               for item in plan["entries"]],
              "read_checks": checks, "findings": [], "missing_evidence": [],
              "not_assessed": ["all real science"], "comparison_groups": [], "stop_reasons": []}
    for name in FILES:
        if name == "review.json":
            write_json(root / name, review)
        elif name in ITEMS:
            container, id_key, fields = ITEMS[name]
            item = {key: [] for key in fields}
            item[id_key] = "fixture-" + id_key
            write_json(root / name, {**expected, "fixture_only": True, container: [item]})
        else:
            text = "# SYNTHETIC fixture only\nNo real scientific claim.\n"
            if name == "next_batch_guide.md":
                text += "\n".join(field + ": fixture-only" for field in
                                  "work_item_id issue_ids goal model_and_asset_versions input_contract output_contract implementation_scope frozen_components preparation_steps dependencies acceptance_checks priority budget blocked_fallback".split())
            (root / name).write_text(text + "\n")
    manifest = {**expected, "scientific_status": "inconclusive", "files": []}
    for name in FILES:
        raw = (root / name).read_bytes()
        manifest["files"].append({"path": name, "bytes": len(raw),
                                  "sha256": hashlib.sha256(raw).hexdigest()})
    write_json(root / "delivery-manifest.json", manifest)
    return expected, plan, oracle


class GatewayCounterexamples(unittest.TestCase):
    def setUp(self):
        tmp = ROOT / "tests/tmp"
        tmp.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=tmp)
        self.root = Path(self.temp.name)
        self.expected, self.plan, self.oracle = fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def run_check(self, oracle=True):
        return check_bundle(self.root, self.expected, self.plan, self.oracle if oracle else None)

    def mutate_review(self, change):
        data = strict_json((self.root / "review.json").read_bytes())
        change(data)
        write_json(self.root / "review.json", data)
        self.refresh_hash("review.json")

    def refresh_hash(self, name):
        manifest = strict_json((self.root / "delivery-manifest.json").read_bytes())
        raw = (self.root / name).read_bytes()
        row = next(x for x in manifest["files"] if x["path"] == name)
        row.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        write_json(self.root / "delivery-manifest.json", manifest)

    def rejected(self, fragment):
        result = self.run_check()
        self.assertEqual(result["status"], "rejected", result)
        self.assertTrue(any(fragment in e for e in result["errors"]), result)
        self.assertIs(result["fresh_chat_read_verified"], False)
        return result

    def test_positive_preserves_separate_states(self):
        result = self.run_check()
        self.assertEqual(result["status"], "eligible_for_controller_review")
        self.assertEqual(result["artifact_state"], "verified")
        self.assertEqual(result["scientific_status"], "inconclusive")
        self.assertEqual(result["chat_terminal_state"], "unknown")
        self.assertIs(result["fresh_chat_read_verified"], False)

    def test_missing_mandatory_layer_in_plan(self):
        self.plan["entries"] = [x for x in self.plan["entries"] if x["layer"] != "history"]
        self.rejected("missing_required_layer")

    def test_missing_mandatory_receipt(self):
        self.mutate_review(lambda d: d["read_receipt"].pop())
        self.rejected("missing_mandatory_entry")

    def test_hash_only_cannot_impersonate_original(self):
        self.mutate_review(lambda d: d["read_receipt"][1].update(read_mode="hash_only"))
        result = self.rejected("mandatory_not_original")
        self.assertEqual(result["artifact_state"], "verified")

    def test_summary_cannot_impersonate_original(self):
        self.mutate_review(lambda d: d["read_receipt"][0].update(read_mode="summary"))
        self.rejected("mandatory_not_original")

    def test_read_numeric_value_mismatch(self):
        self.mutate_review(lambda d: d["read_checks"][2].update(answer="9.5"))
        self.rejected("independent_value_mismatch")

    def test_historical_chain_wrong_order(self):
        self.mutate_review(lambda d: d["read_checks"][1].update(
            answer=["fixture-event-2", "fixture-event-1"]))
        self.rejected("independent_value_mismatch")

    def test_wrong_rule_source(self):
        self.mutate_review(lambda d: d["read_checks"][0].update(
            answer={"rule": "SYNTHETIC rule", "source": "wrong-source"}))
        self.rejected("independent_value_mismatch")

    def test_unpinned_main_link(self):
        self.plan["entries"][0]["uri"] = self.plan["entries"][0]["uri"].replace("a" * 40, "main")
        self.rejected("mutable_or_wrong_repository_uri")

    def test_mixed_receipt_commit(self):
        self.mutate_review(lambda d: d["read_receipt"][2].update(source_version="c" * 40))
        self.rejected("receipt_plan_mismatch")

    def add_external_scope_entry(self):
        entry = {"entry_id": "fixture-approved-external", "layer": "related_originals",
                 "uri": "https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/"
                        + "c" * 40 + "/fixture/approved.csv",
                 "source_version": "c" * 40, "source_sha256": "d" * 64,
                 "scope_id": "fixture-evaluation-scope", "required_read_mode": "original"}
        self.plan["evaluation_scope_id"] = entry["scope_id"]
        self.plan["approved_external_sources"] = [{
            k: entry[k] for k in ("uri", "source_version", "source_sha256", "scope_id")}]
        self.plan["entries"].append(entry)
        self.mutate_review(lambda d: d["read_receipt"].append(
            {**entry, "read_mode": "original", "evidence_locator": "fixture-only:all",
             "observed_fact": "synthetic approved source", "limitation": "fixture only"}))
        return entry

    def test_scope_explicit_pinned_external_original_allowed(self):
        self.add_external_scope_entry()
        result = self.run_check()
        self.assertEqual(result["status"], "eligible_for_controller_review")
        self.assertFalse(result["fresh_chat_read_verified"])

    def test_scope_external_without_approval_rejected(self):
        self.add_external_scope_entry()
        self.plan["approved_external_sources"] = []
        self.rejected("unapproved_external_version")

    def test_scope_external_hash_binding_must_match(self):
        entry = self.add_external_scope_entry()
        entry["source_sha256"] = "e" * 64
        self.rejected("external_binding_mismatch")

    def test_scope_external_cannot_replace_context_commit(self):
        entry = self.add_external_scope_entry()
        entry["layer"] = "context"
        self.rejected("external_source_not_related_original")

    def test_corrupted_file_bytes(self):
        with (self.root / "analysis.md").open("a") as f:
            f.write("unexpected mutation")
        self.rejected("artifact_hash_or_size")

    def test_stale_reply_identity_even_with_updated_hash(self):
        self.mutate_review(lambda d: d.update(request_id="wrong-request"))
        self.rejected("artifact_identity")

    def test_duplicate_json_key(self):
        raw = (self.root / "review.json").read_text()
        (self.root / "review.json").write_text('{"request_id":"duplicate",' + raw[1:])
        self.refresh_hash("review.json")
        self.rejected("duplicate_json_key")

    def test_json_exponent_overflow_rejected(self):
        for token in ("1e9999", "-1e9999", "1.7976931348623159e308"):
            with self.subTest(token=token):
                with self.assertRaisesRegex(ContractError, "nonfinite_json_number"):
                    strict_json('{"value":' + token + "}")

    def test_nested_json_exponent_overflow_rejected(self):
        with self.assertRaisesRegex(ContractError, "nonfinite_json_number"):
            strict_json('{"rows":[{"nested":{"value":1e9999}}]}')

    def test_extreme_finite_json_numbers_accepted(self):
        parsed = strict_json('{"positive":1e308,"negative":-1e308,"ordinary":1.25}')
        self.assertTrue(all(math.isfinite(v) for v in parsed.values()))
        self.assertEqual(parsed["ordinary"], 1.25)

    def test_nonstandard_json_numbers_still_rejected(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                with self.assertRaisesRegex(ContractError, "nonfinite_json"):
                    strict_json('{"value":' + token + "}")

    def test_bundle_overflow_rejected_even_with_matching_file_hash(self):
        f = self.root / "review.json"
        f.write_text('{"overflow":1e9999,' + f.read_text()[1:])
        self.refresh_hash("review.json")
        self.rejected("nonfinite_json_number")

    def test_missing_file(self):
        (self.root / "issues.json").unlink()
        self.rejected("missing_file")

    def test_symlink_artifact(self):
        f = self.root / "analysis.md"
        f.rename(self.root / "other.txt")
        f.symlink_to("other.txt")
        self.rejected("symlink_path")

    def test_missing_oracle_remains_structure_only(self):
        result = self.run_check(oracle=False)
        self.assertEqual(result["status"], "structure_only_pending_oracle")
        self.assertIs(result["fresh_chat_read_verified"], False)

    def test_zip_traversal(self):
        path = self.root / "bad.zip"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("../outside.txt", b"bad")
        with self.assertRaisesRegex(ContractError, "unsafe_path"):
            inspect_zip(path)

    def test_zip_duplicate_member(self):
        path = self.root / "bad.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("same.txt", b"a")
                z.writestr("same.txt", b"b")
        with self.assertRaisesRegex(ContractError, "duplicate_zip_member"):
            inspect_zip(path)

    def test_zip_crc_corruption(self):
        path = self.root / "bad.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as z:
            z.writestr("fixture.txt", b"UNIQUE-fixture-payload")
        data = path.read_bytes()
        path.write_bytes(data.replace(b"UNIQUE-fixture-payload", b"BROKEN-fixture-payload", 1))
        with self.assertRaises((ContractError, zipfile.BadZipFile)):
            inspect_zip(path)

    def test_zip_rejects_unix_special_member_types(self):
        for file_type in (stat.S_IFCHR, stat.S_IFBLK, stat.S_IFIFO, stat.S_IFSOCK,
                          stat.S_IFLNK, 0o170000):
            with self.subTest(file_type=oct(file_type)):
                path = self.root / ("special-" + str(file_type) + ".zip")
                with zipfile.ZipFile(path, "w") as z:
                    info = zipfile.ZipInfo("special")
                    info.create_system = 3
                    info.external_attr = (file_type | 0o600) << 16
                    z.writestr(info, b"")
                with self.assertRaisesRegex(ContractError, "zip_special_file_type|zip_symlink"):
                    inspect_zip(path)

    def test_zip_accepts_regular_directories_and_compatible_missing_modes(self):
        path = self.root / "ordinary.zip"
        cases = [("regular.txt", 3, (stat.S_IFREG | 0o644) << 16, b"data"),
                 ("unix-dir/", 3, ((stat.S_IFDIR | 0o755) << 16) | 0x10, b""),
                 ("permission-only.txt", 3, 0o600 << 16, b"data"),
                 ("dos-file.txt", 0, 0x20, b"data"),
                 ("dos-dir/", 0, 0x10, b"")]
        with zipfile.ZipFile(path, "w") as z:
            for name, system, attrs, data in cases:
                info = zipfile.ZipInfo(name)
                info.create_system = system
                info.external_attr = attrs
                z.writestr(info, data)
        result = inspect_zip(path)
        self.assertEqual(result["state"], "verified")
        self.assertEqual(result["member_type_counts"],
                         {"regular_files": 3, "directories": 2, "missing_unix_type_compatible": 3})

    def test_zip_rejects_file_type_name_conflicts(self):
        for name, attrs in (("dir/", (stat.S_IFREG | 0o644) << 16),
                            ("file", (stat.S_IFDIR | 0o755) << 16), ("dos-file", 0x10)):
            with self.subTest(name=name):
                path = self.root / "conflict.zip"
                with zipfile.ZipFile(path, "w") as z:
                    info = zipfile.ZipInfo(name)
                    info.create_system = 3
                    info.external_attr = attrs
                    z.writestr(info, b"")
                with self.assertRaisesRegex(ContractError, "zip_type_name_mismatch|zip_dos_directory"):
                    inspect_zip(path)

    def test_zip_rejects_directory_payload(self):
        path = self.root / "directory-payload.zip"
        with zipfile.ZipFile(path, "w") as z:
            info = zipfile.ZipInfo("dir/")
            info.create_system = 3
            info.external_attr = ((stat.S_IFDIR | 0o755) << 16) | 0x10
            z.writestr(info, b"not a regular directory")
        with self.assertRaisesRegex(ContractError, "zip_directory_payload"):
            inspect_zip(path)

    def creation_gate(self):
        text = "SYNTHETIC complete formal request with sealed evidence."
        return {"creation_mode": "create_new_once_after_packet_acceptance",
                "maximum_analysis_requests": 1, "scope": "analysis_product_chat_only",
                "cycle_id": "fixture-cycle", "request_id": "fixture-new",
                "creation_key": "fixture-cycle:fixture-new", "old_request_id": "fixture-old",
                "old_terminal_state": "unknown", "new_request_send_state": "not_sent",
                "send_attempts_started": 0, "actual_chat_id": None,
                "controller_packet_accepted": True, "controller_acceptance_evidence": "fixture-only",
                "pro_observed": True, "empty_history_observed": True,
                "frozen_prompt": text, "prompt_sha256": hashlib.sha256(text.encode()).hexdigest()}

    def test_new_once_preserves_unknown_old_terminal(self):
        result = validate_dispatch_gate(self.creation_gate())
        self.assertEqual(result["state"], "declared_preconditions_passed")
        self.assertEqual(result["old_terminal_state_preserved"], "unknown")
        self.assertFalse(result["creates_chat"])

    def test_new_once_rejects_unknown_new_send(self):
        gate = self.creation_gate()
        gate["new_request_send_state"] = "unknown"
        with self.assertRaisesRegex(ContractError, "new_send_unknown"):
            validate_dispatch_gate(gate)

    def test_new_once_rejects_second_slot_claim(self):
        gate = self.creation_gate()
        gate["send_attempts_started"] = 1
        with self.assertRaisesRegex(ContractError, "creation_slot_already_claimed"):
            validate_dispatch_gate(gate)

    def test_new_once_waits_for_packet_acceptance(self):
        gate = self.creation_gate()
        gate["controller_packet_accepted"] = False
        with self.assertRaisesRegex(ContractError, "packet_not_accepted"):
            validate_dispatch_gate(gate)

    def test_new_once_rejects_placeholder_prompt(self):
        gate = self.creation_gate()
        gate["frozen_prompt"] = "{{pending_packet}}"
        with self.assertRaisesRegex(ContractError, "unresolved_or_placeholder"):
            validate_dispatch_gate(gate)

    def test_new_once_requires_actual_pro_and_empty_history(self):
        for field in ("pro_observed", "empty_history_observed"):
            with self.subTest(field=field):
                gate = self.creation_gate()
                gate[field] = False
                with self.assertRaisesRegex(ContractError, "actual_pro_or_blank"):
                    validate_dispatch_gate(gate)

    def test_new_once_rejects_codex_executor_scope(self):
        gate = self.creation_gate()
        gate["scope"] = "codex_executor_thread"
        with self.assertRaisesRegex(ContractError, "executor_creation_not_allowed"):
            validate_dispatch_gate(gate)

    def test_new_once_cannot_recreate_old_request(self):
        gate = self.creation_gate()
        gate["old_request_id"] = gate["request_id"]
        with self.assertRaisesRegex(ContractError, "old_request_cannot_be_recreated"):
            validate_dispatch_gate(gate)


class RecordedResult(unittest.TextTestResult):
    def startTestRun(self):
        super().startTestRun()
        self.cases = []

    def addSuccess(self, test):
        self.cases.append({"case": test.id().split(".")[-1], "result": "PASS"})
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.cases.append({"case": test.id().split(".")[-1], "result": "FAIL"})
        super().addFailure(test, err)

    def addError(self, test, err):
        self.cases.append({"case": test.id().split(".")[-1], "result": "ERROR"})
        super().addError(test, err)


if __name__ == "__main__":
    positive = ROOT / "fixtures/positive"
    expected, plan, oracle = fixture(positive)
    write_json(positive.parent / "expected.json", expected)
    write_json(positive.parent / "read-plan.json", plan)
    write_json(positive.parent / "synthetic-oracle.json", oracle)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GatewayCounterexamples)
    runner = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult)
    result = runner.run(suite)
    report = {"fixture_only": True, "tests_run": result.testsRun,
              "passed": result.wasSuccessful(), "failures": len(result.failures),
              "errors": len(result.errors), "real_network_or_private_labels_used": False,
              "fresh_chat_read_verified_by_tests": False, "cases": result.cases}
    write_json(ROOT / "test-results.json", report)
    raise SystemExit(0 if result.wasSuccessful() else 1)
