"""Negative admission tests. Real admitted CSVs are read only; no training."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parents[1]
spec = importlib.util.spec_from_file_location('plan_checks', PROJECT / 'src/plan_checks.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((PROJECT / 'runs/hainan-skill-pilot-20261030/PLAN.json').read_text())

    def check(self, plan):
        return module.check(plan, WORKSPACE / 'adhoc_jobs/admet_frozen_baseline_20261030',
                            PROJECT / 'policy.json', WORKSPACE / 'rules/skills/hainan-compute-access/SKILL.md')

    def test_admitted_plan(self):
        self.assertTrue(self.check(self.plan)['passed'])

    def test_policy_counterexamples(self):
        for key, value in [('pretrained_backbone_frozen', False), ('pretrained_backbone_frozen', 1),
                           ('validation_labels_allowed', True), ('external_labels_allowed', True),
                           ('test_fitting_allowed', True), ('official_upload_allowed', True),
                           ('max_concurrent_jobs', 2), ('device', 'cpu'),
                           ('remote_directory', '<PRIVATE_RUNTIME_PATH>'),
                           ('remote_directory', '<AUTHORIZED_PROJECT_ROOT>/../Other')]:
            with self.subTest(key=key, value=value):
                changed = copy.deepcopy(self.plan)
                changed[key] = value
                with self.assertRaises(ValueError):
                    self.check(changed)

    def test_tampered_input_hash(self):
        self.plan['inputs'][0]['sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.check(self.plan)

    def test_missing_role(self):
        self.plan['inputs'].pop()
        with self.assertRaises(ValueError):
            self.check(self.plan)

    def test_link_rejected(self):
        with tempfile.TemporaryDirectory(dir=PROJECT / 'runs') as name:
            root = Path(name)
            file = root / 'file'
            file.write_text('synthetic')
            link = root / 'link'
            link.symlink_to(file)
            with self.assertRaises(ValueError):
                module.regular_inside(link, root)

    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):
            module.regular_inside(PROJECT / 'policy.json', PROJECT / 'runs')


if __name__ == '__main__':
    unittest.main()
