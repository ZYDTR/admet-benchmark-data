import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from admet_harness.common import HarnessError, read_json, resolve_inside, sha256_file, write_json
from admet_harness.context import check_context, get_context, save_handoff


class ContextTests(unittest.TestCase):
    def test_project_discovery_graph_has_no_orphan_or_broken_link(self):
        report = check_context(ROOT)
        self.assertGreater(report["skill_count"], 0)
        self.assertTrue(report["ok"])

    def test_a_focused_context_does_not_expand_linked_resources(self):
        result = get_context(ROOT, "submission")
        self.assertIn("docs/submission.md", result["on_demand_resources"])
        self.assertNotIn("## 预测记录", result["content"])
        with self.assertRaises(HarnessError):
            get_context(ROOT, "not-a-skill")

    def test_an_unindexed_skill_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "skills/orphan").mkdir(parents=True)
            (root / "skills/INDEX.md").write_text("# Empty index\n")
            (root / "skills/orphan/SKILL.md").write_text("unreachable")
            with self.assertRaises(HarnessError) as error:
                get_context(root, "orphan")
            self.assertEqual(error.exception.code, "UNINDEXED_SKILL")

    def test_handoff_keeps_evidence_and_rejects_stale_writer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "evidence.txt").write_text("observed result")
            payload = {"task_id": "sample-task", "owner": "A", "status": "in_progress", "goal": "check behavior",
                       "summary": "verified one result", "next_action": "review remaining item", "blockers": [],
                       "evidence": ["evidence.txt"], "decisions": []}
            write_json(root / "handoff.json", payload)
            first = save_handoff(root, root / "handoff.json", 0)
            self.assertEqual(first["task"]["revision"], 1)
            self.assertEqual(first["task"]["evidence_hashes"][0]["sha256"], sha256_file(root / "evidence.txt"))
            with self.assertRaises(HarnessError) as error:
                save_handoff(root, root / "handoff.json", 0)
            self.assertEqual(error.exception.code, "REVISION_CONFLICT")
            self.assertEqual(read_json(root / "context/tasks/sample-task.json")["revision"], 1)
            self.assertTrue((root / "context/history/sample-task/0001.json").is_file())

    def test_done_requires_evidence_and_no_blocker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = {"task_id": "sample-task", "owner": "B", "status": "done", "goal": "done",
                       "summary": "claimed", "next_action": "handoff", "blockers": [], "evidence": [], "decisions": []}
            write_json(root / "handoff.json", payload)
            with self.assertRaises(HarnessError) as error:
                save_handoff(root, root / "handoff.json", 0)
            self.assertEqual(error.exception.code, "HANDOFF_SCHEMA")

    def test_paths_cannot_escape_or_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "source.txt").write_text("content")
            (root / "alias.txt").symlink_to(root / "source.txt")
            for path in ("../outside", "alias.txt", str(root / "source.txt")):
                with self.subTest(path=path), self.assertRaises(HarnessError):
                    resolve_inside(root, path)

    def test_duplicate_json_fields_are_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ambiguous.json"
            path.write_text('{"status":"pending","status":"approved"}')
            with self.assertRaises(HarnessError):
                read_json(path)


if __name__ == "__main__":
    unittest.main()
