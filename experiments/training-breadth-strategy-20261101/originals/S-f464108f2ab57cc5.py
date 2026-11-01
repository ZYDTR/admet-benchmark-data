"""主控检查真实生产helper与真实Tensor存取；无参数更新、编码或私有评分。"""
import copy
import csv
import hashlib
import json
import random
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
import training_science as science

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(path, existing=False):
    if existing and not path.exists(): raise ValueError("missing input")
    return path


class HostChecks(unittest.TestCase):
    def test_real_production_input_boundary(self):
        rows, _, audits = science.load_input_tables(CONFIG, ROOT.parent / "input", safe, digest)
        self.assertEqual([len(rows[s]) for s in ("train", "valid", "test")], [637, 91, 182])
        self.assertEqual([len(audits[s]["duplicate_drug_ids"]) for s in ("valid", "test")], [2, 4])
        self.assertTrue(all("Y" not in r for s in ("valid", "test") for r in rows[s]))
        for s in rows:
            with (ROOT.parent / "input/data" / (s + ".csv")).open(newline="", encoding="utf-8-sig") as f:
                self.assertEqual(rows[s], list(csv.DictReader(f)))

    def test_synthetic_csv_empty_duplicate_ids_every_split(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            root = Path(temporary); (root / "data").mkdir()
            cfg = copy.deepcopy(CONFIG)
            for item in cfg["inputs"]:
                fields = ["Drug_ID", "Drug"] + (["Y"] if item["role"] == "train" else [])
                table = [{"Drug_ID": "", "Drug": "C"}, {"Drug_ID": "same", "Drug": "CC"}, {"Drug_ID": "same", "Drug": "CC"}]
                if item["role"] == "train":
                    for row in table: row["Y"] = "1.25"
                with (root / item["path"]).open("w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(table)
                item["rows"] = len(table); item["sha256"] = digest(root / item["path"])
            loaded, _, _ = science.load_input_tables(cfg, root, safe, digest)
            for split in loaded:
                self.assertEqual([x["Drug_ID"] for x in loaded[split]], ["", "same", "same"])
            bad = copy.deepcopy(cfg); bad["inputs"][0]["sha256"] = "0" * 64
            with self.assertRaises(science.PreparationError): science.load_input_tables(bad, root, safe, digest)
            valid = root / "data/valid.csv"; valid.write_text("Drug_ID,Drug,Y\nx,C,0\n")
            cfg["inputs"][1]["sha256"] = digest(valid); cfg["inputs"][1]["rows"] = 1
            with self.assertRaises(science.PreparationError): science.load_input_tables(cfg, root, safe, digest)

    def test_split_identity_coverage_and_independent_rng(self):
        rows = [{"Drug_ID": "" if i % 2 else "same", "Drug": "C" * (i // 2 + 1), "Y": "1"} for i in range(20)]
        original = copy.deepcopy(rows)
        random.seed(1); a = science.split_train_stop_groups(rows, 43, .1)
        random.seed(72); random.random(); b = science.split_train_stop_groups(rows, 43, .1)
        self.assertEqual(a, b); self.assertEqual(rows, original)
        fit, stop = a["fit_row_indices"], a["stop_row_indices"]
        self.assertEqual(sorted(fit + stop), list(range(20)))
        self.assertFalse({rows[i]["Drug"] for i in fit} & {rows[i]["Drug"] for i in stop})
        self.assertEqual(a["split_record_sha256"], science.sha256_hex(science.canonical_json_bytes({k:v for k,v in a.items() if k != "split_record_sha256"})))
        with self.assertRaises(science.PreparationError): science.split_train_stop_groups([rows[0]] * 3, 43, .1)

    def test_complete_tensor_optimizer_roundtrip_without_step(self):
        p = torch.nn.Parameter(torch.tensor([1., 2.]))
        opt = torch.optim.AdamW([p], lr=.0005)
        opt.state[p] = {"step": torch.tensor(7.), "exp_avg": torch.tensor([.1, .2]), "exp_avg_sq": torch.tensor([.01, .04])}
        before_parameter = p.detach().clone()
        saved = science.optimizer_payload(opt.state_dict())
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / "state.pt"
            torch.save(saved, path)
            loaded = torch.load(path, weights_only=True, map_location="cpu")
            q = torch.nn.Parameter(torch.tensor([1., 2.]))
            other = torch.optim.AdamW([q], lr=.1)
            other.load_state_dict(loaded)
            self.assertTrue(science.state_equal(science.optimizer_payload(other.state_dict()), saved))
        self.assertTrue(torch.equal(p.detach(), before_parameter))
        self.assertTrue(torch.equal(q.detach(), before_parameter))
        self.assertIn("exp_avg", saved["state"][0]); self.assertIsInstance(saved["param_groups"][0], dict)

    def test_rng_actual_sources_roundtrip_without_training(self):
        random.seed(43); np.random.seed(43); torch.manual_seed(43)
        sampler = torch.Generator().manual_seed(43)
        state = science.capture_training_rng(43, sampler)
        def draw(): return [random.random(), np.random.random(3).tolist(), torch.rand(3), torch.randperm(17, generator=sampler)]
        a = draw(); science.restore_training_rng(state, sampler); b = draw()
        self.assertTrue(science.state_equal(a, b))
        science.restore_training_rng(state, sampler)
        self.assertTrue(science.state_equal(state, science.capture_training_rng(43, sampler)))
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / "rng.pt"; torch.save(state, path)
            loaded = torch.load(path, weights_only=True)
            science.restore_training_rng(loaded, sampler)
            self.assertTrue(science.state_equal(state, loaded))

    def test_best_and_last_have_different_step_identity(self):
        history = [{"epoch":i+1,"steps":(i+1)*5,"internal_validation_standardized_mse":value}
                   for i,value in enumerate([4., 1., 2., 3.])]
        best = science.checkpoint_identity(history, 1); last = science.checkpoint_identity(history, 3)
        self.assertEqual((best["epoch"], best["steps"], best["monitor_value"]), (2, 10, 1.))
        self.assertEqual((last["epoch"], last["steps"], last["monitor_value"]), (4, 20, 3.))
        with self.assertRaises(science.PreparationError): science.checkpoint_identity(history, 4)

    def test_explicit_registered_optimizer_and_bad_config(self):
        science.validate_config(CONFIG)
        for key, value in [("optimizer", "SGD"), ("lr", float("nan")), ("batch_size", True)]:
            bad = copy.deepcopy(CONFIG); bad["head_config"][key] = value
            with self.assertRaises(science.PreparationError): science.validate_config(bad)
        bad = copy.deepcopy(CONFIG); bad["inputs"][1]["task"] = "other"
        with self.assertRaises(science.PreparationError): science.validate_config(bad)

    def test_feature_identity_changes_with_content_and_order(self):
        rows = [{"Drug_ID":"same","Drug":"C"},{"Drug_ID":"same","Drug":"CC"}]
        features = np.array([[1., 2.], [3., 4.]], dtype=np.float32); mask = np.array([True, True])
        a = science.feature_identity(features, mask, rows, {"version":"fixed"}, 2, "a"*64)
        b = science.feature_identity(features[::-1], mask, rows, {"version":"fixed"}, 2, "a"*64)
        c = science.feature_identity(features, mask, rows[::-1], {"version":"fixed"}, 2, "a"*64)
        self.assertNotEqual(a["identity_sha256"], b["identity_sha256"])
        self.assertNotEqual(a["identity_sha256"], c["identity_sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
