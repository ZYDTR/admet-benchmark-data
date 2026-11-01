"""材料身份反例；不联网、不调用模型或训练。"""
import json
from pathlib import Path
import tempfile
import unittest
from preparation_packet import prepare, verify


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name).resolve()
        self.task = self.project / "adhoc_jobs/prep-test"
        self.task.mkdir(parents=True)
        (self.task / "TASK.md").write_text("合成材料读回测试；不派发模型。\n")
        (self.task / "input-manifest.json").write_text('{"files":[]}\n')

    def tearDown(self):
        self.temp.cleanup()

    def stage(self):
        return prepare(self.task, self.project, "synthetic-preparation-001")

    def test_actual_packet_and_prompt_paths(self):
        receipt = self.stage()
        self.assertEqual(receipt["state"], "local_packet_verified")
        self.assertEqual(len(receipt["files"]), 6)
        prompt = (self.task / "dispatch-prompt.txt").read_text()
        self.assertIn("adhoc_jobs/prep-test/input/rules/PREPARATION_SKILL.md", prompt)
        self.assertIn("skill-use.json", prompt)
        self.assertFalse(receipt["actual_agent_read_proven"])

    def test_changed_skill_rejected(self):
        self.stage()
        (self.task / "input/rules/PREPARATION_SKILL.md").write_text("changed")
        with self.assertRaisesRegex(ValueError, "identity mismatch"): verify(self.task, self.project)

    def test_changed_task_rejected(self):
        self.stage(); (self.task / "TASK.md").write_text("changed")
        with self.assertRaisesRegex(ValueError, "identity mismatch"): verify(self.task, self.project)

    def test_missing_reference_rejected(self):
        self.stage(); (self.task / "input/rules/references/observed-failures.md").unlink()
        with self.assertRaisesRegex(ValueError, "missing packet file"): verify(self.task, self.project)

    def test_no_existing_packet_rewrite(self):
        self.stage()
        with self.assertRaisesRegex(ValueError, "existing frozen packet"): self.stage()

    def test_no_existing_dispatch_rewrite(self):
        (self.task / "dispatch.json").write_text('{}')
        with self.assertRaisesRegex(ValueError, "existing dispatch"): self.stage()

    def test_no_active_outputs(self):
        (self.task / "output").mkdir(); (self.task / "output/code.py").write_text('pass')
        with self.assertRaisesRegex(ValueError, "existing output"): self.stage()

    def test_wrong_target_project_rejected(self):
        self.stage()
        with self.assertRaisesRegex(ValueError, "target project"): verify(self.task, self.project, target=True)

    def test_path_escape_rejected(self):
        self.stage()
        p = self.task / "input/rules/PACKET.json"
        data = json.loads(p.read_text()); data["files"][0]["path"] = "../outside"
        p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "unsafe path"): verify(self.task, self.project)

    def test_symbolic_link_rejected(self):
        (self.task / "input").symlink_to(self.project)
        with self.assertRaisesRegex(ValueError, "symlink"): self.stage()


if __name__ == "__main__":
    unittest.main(verbosity=2)
