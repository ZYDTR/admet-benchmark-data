"""只测文本封口和错误拒绝，合成值不用于真实Chat。"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
DESIGN = SKILL.parents[1] / "design/chat_gateway_20261031"
SCRIPT = SKILL / "scripts/render_chat_prompt.py"
spec = importlib.util.spec_from_file_location("prompt_renderer", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PromptBindingTests(unittest.TestCase):
    def setUp(self):
        self.template = (DESIGN / "CHAT_PROMPT.md").read_bytes()
        self.contract = (DESIGN / "prompt_contract.json").read_bytes()
        self.values = {}
        for key, rule in json.loads(self.contract)["fields"].items():
            value = "synthetic-only"
            if rule["type"] == "string_array":
                value = ["synthetic-run-1", "synthetic-run-2"]
            elif rule.get("format") == "sha256":
                value = "a" * 64
            elif rule.get("format") == "pinned_github_uri":
                value = "https://github.com/example/synthetic/tree/" + "b" * 40 + "/" + key
            self.values[key] = value
        self.values["request_id"] = "synthetic-never-send"

    def encode(self, values=None):
        return json.dumps(values or self.values, ensure_ascii=False).encode()

    def binding(self, values=None):
        return {"request_id": self.values["request_id"], "template_sha256": module.digest(self.template),
                "contract_sha256": module.digest(self.contract), "values_sha256": module.digest(self.encode(values))}

    def render(self, values=None):
        return module.render(self.template, self.contract, self.encode(values), self.binding(values))

    def test_valid_body_and_final_marker(self):
        prompt, receipt = self.render()
        self.assertEqual(receipt["prompt_sha256"], module.digest(prompt))
        self.assertNotIn(b"{{", prompt)
        self.assertIn(("REVIEW_COMPLETE synthetic-never-send " + "a" * 64).encode(), prompt)
        self.assertEqual(prompt.count(b"synthetic-never-send"), 2)
        for fixed in ("参数和 buffer 必须冻结", "渐进式索引实读", "批量研究与实验安排", "next_experiments.json"):
            self.assertIn(fixed.encode(), prompt)

    def test_unapproved_template_values_or_contract_change(self):
        for index in range(3):
            args = [self.template, self.contract, self.encode(), self.binding()]
            args[index] += b" "
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, "SHA256 differs"):
                module.render(*args)

    def test_missing_extra_and_wrong_type(self):
        values = copy.deepcopy(self.values)
        del values["research_question"]
        with self.assertRaises(ValueError): self.render(values)
        values = {**self.values, "override_rules": "bad"}
        with self.assertRaises(ValueError): self.render(values)
        values = {**self.values, "run_ids": "not-an-array"}
        with self.assertRaises(ValueError): self.render(values)

    def test_unpinned_and_mixed_commit_links(self):
        for replacement in ("main", "c" * 40):
            values = copy.deepcopy(self.values)
            values["current_batch_uri"] = values["current_batch_uri"].replace("b" * 40, replacement)
            with self.subTest(replacement=replacement), self.assertRaises(ValueError): self.render(values)

    def test_bad_hash_and_placeholder_value(self):
        for key, bad in (("manifest_sha256", "not-a-digest"), ("research_question", "{{evaluation_scope}}")):
            with self.subTest(key=key), self.assertRaises(ValueError): self.render({**self.values, key: bad})

    def test_duplicate_json_and_wrong_request(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            module.parse('{"request_id":"a","request_id":"b"}')
        binding = self.binding()
        binding["request_id"] = "wrong-request"
        with self.assertRaisesRegex(ValueError, "request identity"):
            module.render(self.template, self.contract, self.encode(), binding)

    def test_cli_verify_rejects_tamper_and_render_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            contents = {"template": self.template, "contract": self.contract, "values": self.encode(),
                        "binding": json.dumps(self.binding()).encode()}
            args = []
            for name, data in contents.items():
                path = root / name
                path.write_bytes(data)
                args += ["--" + name, str(path)]
            args += ["--out", str(root / "rendered")]
            def run(mode):
                return subprocess.run([sys.executable, "-B", str(SCRIPT), mode, *args], capture_output=True)
            self.assertEqual(run("render").returncode, 0)
            self.assertEqual(run("verify").returncode, 0)
            self.assertNotEqual(run("render").returncode, 0)
            prompt = root / "rendered/prompt.txt"
            prompt.write_bytes(prompt.read_bytes() + b"unauthorized-change")
            failure = run("verify")
            self.assertNotEqual(failure.returncode, 0)
            self.assertIn(b"prompt differs", failure.stderr)


if __name__ == "__main__":
    unittest.main()
