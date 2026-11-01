"""验证证据索引在坏输入上拒绝，以及推翻记录没有被投影覆盖。"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('catalog_builder', HERE.parent / 'scripts/build_index.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='index-test-', dir=HERE)
        self.root = Path(self.tmp.name)
        (self.root / 'evidence.txt').write_text('真实原件，不能改写\n')
        self.original = (self.root / 'evidence.txt').read_bytes()
        self.data = {
            'schema_version': 1, 'catalog_id': 'demo', 'as_of': '2026-10-31',
            'scope': '一成功、一失败以及一个反证案例', 'history_coverage': 'partial',
            'history_gaps': ['其他历史尚未导入'], 'current_batch': 'B1',
            'sources': [{'id': 'S1', 'path': 'evidence.txt', 'sha256': hashlib.sha256(self.original).hexdigest(), 'title': '原件'}],
            'context_source_ids': ['S1'],
            'runs': [{'id': i, 'task': 'synthetic', 'state': state, 'comparison_group': 'G1', 'source_ids': ['S1']}
                     for i, state in [('R1', 'completed'), ('R2', 'failed')]],
            'issues': [{'id': 'I1', 'state': 'open', 'statement': '仍待解决', 'source_ids': ['S1']}],
            'batches': [{'id': 'B1', 'run_ids': ['R1', 'R2'], 'source_ids': ['S1'], 'delta': ['新反证'], 'missing_evidence': ['后续复验']}],
            'claim_events': [dict(event_id='E1', claim_id='C1', supersedes_event_id=None, occurred_at=None,
                                  time_precision='historical_order_only', status='proposed', statement='原假设',
                                  reason='待检查', source_ids=['S1'], reviewer='controller', scope='合成测试', affected_proposals=['P1']),
                             dict(event_id='E2', claim_id='C1', supersedes_event_id='E1', occurred_at=None,
                                  time_precision='historical_order_only', status='refuted', statement='原假设',
                                  reason='发现反例', source_ids=['S1'], reviewer='controller', scope='合成测试', affected_proposals=['P1'])]}

    def tearDown(self):
        self.tmp.cleanup()

    def build(self):
        return module.build(self.data, self.root / 'output', self.root)

    def rejects(self, text):
        with self.assertRaisesRegex(module.CatalogError, text):
            self.build()
        self.assertFalse((self.root / 'output').exists())

    def test_reversal_preserves_original_and_failure(self):
        result = self.build()
        self.assertEqual((self.root / 'evidence.txt').read_bytes(), self.original)
        events = (self.root / 'output/history/claims/events.jsonl').read_text().splitlines()
        self.assertEqual(len(events), 2)
        current = json.loads((self.root / 'output/history/claims/current.json').read_text())
        self.assertEqual(current['C1']['status'], 'refuted')
        self.assertIn('failed', (self.root / 'output/history/README.md').read_text())
        self.assertIn('partial', (self.root / 'output/README.md').read_text())
        for item in result['files']:
            p = self.root / 'output' / item['path']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), item['sha256'])

    def test_wrong_hash(self):
        self.data['sources'][0]['sha256'] = '0' * 64
        self.rejects('hash mismatch')

    def test_dangling_reference(self):
        self.data['batches'][0]['run_ids'].append('unknown')
        self.rejects('dangling reference')

    def test_duplicate_id(self):
        self.data['runs'].append(copy.deepcopy(self.data['runs'][0]))
        self.rejects('duplicate id')

    def test_broken_reversal_chain(self):
        self.data['claim_events'][1]['supersedes_event_id'] = 'unrelated'
        self.rejects('broken supersedes')

    def test_cannot_redefine_claim(self):
        self.data['claim_events'][1]['statement'] = '偷换成另一个命题'
        self.rejects('meaning changed')

    def test_supported_without_evidence(self):
        self.data['claim_events'][1]['source_ids'] = []
        self.rejects('missing evidence')

    def test_false_complete_history(self):
        self.data['history_coverage'] = 'complete'
        self.rejects('coverage and gaps conflict')

    def test_source_path_escape(self):
        self.data['sources'][0]['path'] = '../evidence.txt'
        self.rejects('escapes root')

    def test_source_symlink(self):
        (self.root / 'linked').symlink_to(self.root / 'evidence.txt')
        self.data['sources'][0]['path'] = 'linked'
        self.rejects('symlink source')

    def test_old_snapshot_not_overwritten(self):
        self.build()
        before = (self.root / 'output/manifest.json').read_bytes()
        with self.assertRaisesRegex(module.CatalogError, 'output must be new'):
            self.build()
        self.assertEqual(before, (self.root / 'output/manifest.json').read_bytes())

    def test_history_cannot_silently_disappear(self):
        previous = copy.deepcopy(self.data)
        self.data['claim_events'] = self.data['claim_events'][:1]
        with self.assertRaisesRegex(module.CatalogError, 'historical claim events'):
            module.build(self.data, self.root / 'output', self.root, previous)
        self.assertFalse((self.root / 'output').exists())

    def test_new_snapshot_preserves_old_source_bytes(self):
        self.build()
        manifest = json.loads((self.root / 'output/source-manifest.json').read_text())
        snapshot = self.root / 'output' / manifest[0]['snapshot_path']
        (self.root / 'evidence.txt').write_text('未来版本发生变化')
        self.assertEqual(snapshot.read_bytes(), self.original)

    def test_failed_run_cannot_drop_from_next_history(self):
        previous = copy.deepcopy(self.data)
        self.data['runs'] = self.data['runs'][:1]
        self.data['batches'][0]['run_ids'] = ['R1']
        with self.assertRaisesRegex(module.CatalogError, 'historical runs entry removed'):
            module.build(self.data, self.root / 'output', self.root, previous)


if __name__ == '__main__':
    unittest.main()
