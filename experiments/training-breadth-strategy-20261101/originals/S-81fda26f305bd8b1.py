import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        result = subprocess.run([sys.executable, "scripts/harness.py", *arguments], cwd=ROOT,
                                capture_output=True, text=True, check=False)
        return result, json.loads(result.stdout)

    def test_status_restores_tasks_without_inventing_completed_runs(self):
        process, value = self.run_cli("status")
        self.assertEqual(process.returncode, 0)
        self.assertGreaterEqual(len(value["tasks"]), 3)
        self.assertIn("state", value)

    def test_pending_data_blocks_formal_run_with_actionable_error(self):
        process, value = self.run_cli("run", "--config", "config/run.example.json")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(value["error"]["code"], "DATA_NOT_APPROVED")
        run_id = json.loads((ROOT / "config/run.example.json").read_text())["run_id"]
        self.assertFalse((ROOT / "runs" / run_id).exists())

    def test_unknown_skill_and_outside_path_are_structured_errors(self):
        process, value = self.run_cli("context", "--skill", "unknown")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(value["error"]["code"], "UNKNOWN_SKILL")
        process, value = self.run_cli("inspect-template", "--template", "../research/submission_template.csv")
        self.assertEqual(process.returncode, 2)
        self.assertEqual(value["error"]["code"], "PATH_OUTSIDE_PROJECT")


if __name__ == "__main__":
    unittest.main()
