"""Preparation-only synthetic checks for the monitor-MAE cycle (no training, no parameter updates).

Runs with numpy alone; torch-dependent restore/reload tests skip cleanly when torch is absent and
are recorded as unverified in the handoff. Every test calls the production entry points from
``training_science`` / ``train_remote_v4`` directly — no local re-implementations. The selection
test drives the *verbatim* epoch-loop tail extracted from main() via AST (statements 302..323),
with the batch-training statements excluded, so nothing touches backward or optimizer.step.
"""
from __future__ import annotations

import copy
import collections
import csv
import hashlib
import json
import math
import random
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[1]          # output/
TASK = OUT.parent                                   # preparation/
sys.path.insert(0, str(OUT))
import training_science as science                  # noqa: E402  (production module)

CONFIG = json.loads((OUT / "config.json").read_text(encoding="utf-8"))
REF_CONFIG = json.loads((TASK / "input/config.json").read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(path, existing=False):
    if existing and not path.exists():
        raise ValueError("missing input")
    return path


try:
    import torch
    HAVE_TORCH = True
except ImportError:
    torch = None
    HAVE_TORCH = False


class _TensorLike:
    """Stand-in exposing only .detach().clone(); never a real parameter, never updated."""
    def __init__(self, tag):
        self.tag = tag
    def detach(self):
        return self
    def clone(self):
        return _TensorLike(self.tag)
    def __eq__(self, other):
        return isinstance(other, _TensorLike) and other.tag == self.tag


class _HeadStub:
    def __init__(self, epoch):
        self.epoch = epoch
    def state_dict(self):
        return {"0.weight": _TensorLike("w"), "4.bias": _TensorLike(f"b{self.epoch}")}


class Sim:
    """Feeds the extracted production tail per-epoch values; performs no model work."""

    def __init__(self, maes, epochs, patience):
        self.monitor = science.MONITOR_RAW_MAE
        self.monitor_key = "internal_validation_raw_mae"
        self.hc = {"epochs": epochs, "patience": patience}
        self.history = []
        self.best = float("inf")
        self.best_epoch = -1
        self.best_state = None
        self.steps = 0
        self._maes = maes
        self.tr = list(range(len(maes)))
        self.grad_max = 1.0
        self.head = _HeadStub(-1)
        self.enc = types.SimpleNamespace(model=types.SimpleNamespace(training=False))

    def epoch_update(self):
        # stands in for the excluded batch-loop statements (randperm/zero_grad/backward/opt.step);
        # only advances the cumulative update counter, touches no parameters.
        self.steps += 5
        self.head = _HeadStub(self.steps // 5 - 1)

    def eval_epoch(self, epoch):
        # NaN injected into the stop-side tuple only: reproduces production's guard that the
        # early-stop metric must equal the logged stop MSE before any monitor value is accepted.
        self.head = _HeadStub(epoch)
        mae = self._maes[epoch]
        mse = mae * mae
        if mae != mae:
            # inconsistent stop MSE vs val -> production's logged-stop guard fires
            return 4.0, (4.0, {"mae": float("nan"), "mse": 16.0}), (16.0, {"mae": float("nan"), "mse": 16.0})
        scale = {"mae": mae, "mse": mse}
        return mse, (float(mse), dict(scale)), (float(mse), dict(scale))


def build_tail_driver():
    """Extract train_remote_v4.main's epoch-loop tail (lines 302..323) verbatim into a driver.

    Included unmodified: stop-MSE assertion, monitor_value selection, history.append, phase print,
    best/patience if. Excluded: encoder guard, head.train(), randperm, the inner batch loop with
    loss.backward()/opt.step(), lr readback and the head.eval()/no_grad block — replaced by calls
    to Sim.epoch_update (counter only) and Sim.eval_epoch (same-shaped tuple, no model object).
    """
    import ast
    src = (OUT / "train_remote_v4.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    main_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    loop = next(n for n in ast.walk(main_node)
                if isinstance(n, ast.For) and getattr(n.target, "id", "") == "epoch"
                and "epochs" in ast.dump(n.iter))
    tail = [copy.deepcopy(st) for st in loop.body if 302 <= st.lineno <= 322]
    assert [type(t).__name__ for t in tail] == ["Assert", "Assign", "Expr", "Expr", "If"], \
        [ast.unparse(t)[:60] for t in tail]
    assert "MIN_DELTA" in ast.unparse(tail[-1]) and "history.append" in ast.unparse(tail[2])
    prelude = ast.parse("""
best = sim.best; best_epoch = sim.best_epoch; best_state = sim.best_state
steps = sim.steps; history = sim.history
enc = sim.enc
sim.epoch_update(); steps = sim.steps; steps_before = sim.steps
head = sim.head
train_loss = 4.0 * len(sim.tr); epoch_start = time.monotonic(); lr_now = [0.0005]
""").body
    epilogue = ast.parse("""
val, (fit_std, fit_scale), (stop_std, stop_scale) = sim.eval_epoch(epoch)
last_state = {"simulated": True}
""").body
    sync = ast.parse("""
sim.best, sim.best_epoch, sim.best_state = best, best_epoch, best_state
sim.steps, sim.history = steps, history
steps_before = steps
""").body
    grad_assert = ast.parse(
        "assert not enc.model.training and torch.is_grad_enabled() == sim_grad_enabled").body
    fn = ast.FunctionDef(name="drive_selection_tail", args=ast.arguments(
        posonlyargs=[], args=[], vararg=None, kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[ast.For(target=loop.target, iter=loop.iter, orelse=[],
                      body=prelude + grad_assert + epilogue + tail + sync)],
        decorator_list=[], type_params=[])
    mod = ast.Module(body=[fn], type_ignores=[])
    ast.fix_missing_locations(mod)
    import train_remote_v4 as production
    ns = {"json": json, "time": time, "MIN_DELTA": science.MIN_DELTA,
          "select_monitor_value": production.select_monitor_value,
          "monitor_metric_key": production.monitor_metric_key,
          "torch": type("T", (), {"is_grad_enabled": staticmethod(lambda: False)})()}
    exec(compile(mod, "<extracted-selection-tail>", "exec"), ns)
    drive = ns["drive_selection_tail"]
    def runner(sim):
        ns["sim"] = sim
        ns["sim_grad_enabled"] = False
        for name in ("hc", "monitor", "monitor_key", "tr", "grad_max"):
            ns[name] = getattr(sim, name)
        drive()
    return runner


class MonitorConfig(unittest.TestCase):
    def test_accepts_both_registered_monitors(self):
        for mon in science.ALLOWED_MONITORS:
            cfg = copy.deepcopy(REF_CONFIG)
            cfg["monitor"] = mon
            self.assertIs(science.validate_config(cfg), cfg)

    def test_rejects_unknown_or_missing_monitor(self):
        for bad in ["internal_validation_raw_mse", "internal_validation_standardized_mae", "", None, 43]:
            cfg = copy.deepcopy(REF_CONFIG)
            cfg["monitor"] = bad
            with self.assertRaises(science.PreparationError, msg=repr(bad)):
                science.validate_config(cfg)
        cfg = copy.deepcopy(REF_CONFIG)
        del cfg["monitor"]
        with self.assertRaises(science.PreparationError):
            science.validate_config(cfg)

    def test_output_config_equals_input_and_declares_new_run(self):
        self.assertEqual(CONFIG, REF_CONFIG)
        self.assertEqual(CONFIG["monitor"], "internal_validation_raw_mae")
        self.assertEqual(CONFIG["run_id"], "hainan-mae-monitor-20261101")
        self.assertEqual(CONFIG["head_config"]["hidden_dims"], [256])
        self.assertEqual(CONFIG["head_config"]["lr"], 0.0005)
        self.assertEqual(CONFIG["head_config"]["seed"], 43)
        self.assertEqual(CONFIG["split_config"]["seed"], 43)
        self.assertEqual(CONFIG["head_config"]["patience"], 8)


class MonitorSelection(unittest.TestCase):
    def test_select_value_uses_declared_sources(self):
        self.assertEqual(science.select_monitor_value(science.MONITOR_STANDARDIZED_MSE, 0.25, {"mae": 0.5}), 0.25)
        self.assertEqual(science.select_monitor_value(science.MONITOR_RAW_MAE, 0.25, {"mae": 0.5}), 0.5)
        with self.assertRaises(science.PreparationError):
            science.select_monitor_value("internal_validation_raw_rmse", 0.25, {"mae": 0.5})
        for bad in (float("nan"), float("inf"), -float("inf")):
            with self.assertRaises(science.PreparationError):
                science.select_monitor_value(science.MONITOR_RAW_MAE, 0.25, {"mae": bad})
            with self.assertRaises(science.PreparationError):
                science.select_monitor_value(science.MONITOR_STANDARDIZED_MSE, bad, {"mae": 0.5})
        with self.assertRaises(science.PreparationError):
            science.select_monitor_value(science.MONITOR_RAW_MAE, 0.25, {"mse": 1.0})

    def test_scale_metrics_rejects_non_finite_and_mismatched(self):
        for bad in (float("nan"), float("inf")):
            with self.assertRaises(science.PreparationError):
                science.scale_metrics(np.array([bad, 1.0]), np.array([1.0, 2.0]))
            with self.assertRaises(science.PreparationError):
                science.scale_metrics(np.array([1.0, 2.0]), np.array([bad, 1.0]))
        with self.assertRaises(science.PreparationError):
            science.scale_metrics(np.array([1.0]), np.array([]))


class SelectionLoop(unittest.TestCase):
    def test_mae_minimal_epoch_wins_when_mse_minimizes_later(self):
        # MSE column minimized at epoch 4, MAE column minimized at epoch 2 (failure ref: best steps).
        mse = [4.0, 2.0, 3.0, 1.0]
        mae = [4.0, 1.0, 2.0, 3.0]
        history = [dict(epoch=i + 1, steps=(i + 1) * 5,
                        internal_validation_standardized_mse=mse[i], internal_validation_raw_mae=mae[i],
                        monitor=science.MONITOR_RAW_MAE, monitor_key="internal_validation_raw_mae",
                        monitor_value=mae[i]) for i in range(4)]
        best = science.checkpoint_identity(history, 1)
        last = science.checkpoint_identity(history, 3)
        self.assertEqual((best["epoch"], best["steps"], best["monitor_value"], best["best_monitor_value"]),
                         (2, 10, 1.0, 1.0))
        self.assertEqual((last["epoch"], last["steps"], last["monitor_value"]), (4, 20, 3.0))
        self.assertEqual(last["best_monitor_value"], 1.0)   # last references the actual best, not itself
        self.assertEqual(best["internal_validation_standardized_mse"], 2.0)  # legacy field keeps true-MSE semantics
        self.assertEqual(last["internal_validation_standardized_mse"], 1.0)
        mse_history = [dict(r, monitor=science.MONITOR_STANDARDIZED_MSE,
                            monitor_key="internal_validation_standardized_mse",
                            monitor_value=r["internal_validation_standardized_mse"]) for r in history]
        b2 = science.checkpoint_identity(mse_history, 3)
        self.assertEqual((b2["epoch"], b2["best_monitor_value"]), (4, 1.0))
        with self.assertRaises(science.PreparationError):
            science.checkpoint_identity(history, 4)

    def test_extracted_production_tail_best_last_patience_tie_nan(self):
        drive = build_tail_driver()
        sim = Sim([4.0, 1.0, 2.0, 3.0], 4, 8)
        drive(sim)
        self.assertEqual([r["steps"] for r in sim.history], [5, 10, 15, 20])
        self.assertEqual(sim.best_epoch, 1)                 # MAE-best epoch index -> epoch 2
        self.assertEqual(sim.best, 1.0)
        self.assertEqual(sim.best_state["4.bias"].tag, "b1")  # snapshot taken at epoch 2, not final
        best = science.checkpoint_identity(sim.history, sim.best_epoch)
        last = science.checkpoint_identity(sim.history, len(sim.history) - 1)
        self.assertEqual((best["epoch"], best["steps"], best["monitor_value"]), (2, 10, 1.0))
        self.assertEqual((last["epoch"], last["steps"], last["monitor_value"]), (4, 20, 3.0))
        self.assertEqual(last["best_monitor_value"], 1.0)

        sim = Sim([4.0, 1.0, 2.0, 2.5, 2.6, 2.7, 2.8, 9.9], 8, 2)
        drive(sim)
        self.assertEqual(len(sim.history), 4)               # patience stops at epoch 4, best stays epoch 2
        self.assertEqual(sim.best_epoch, 1)

        sim = Sim([2.0, 2.0, 2.0 - 1e-8], 3, 8)             # improvement below MIN_DELTA keeps earlier best
        drive(sim)
        self.assertEqual(sim.best_epoch, 0)

        # (a) stop/logged-MSE inconsistency is caught by the production guard before selection.
        sim = Sim([2.0, float("nan")], 2, 8)
        with self.assertRaises(AssertionError):
            drive(sim)
        self.assertEqual(len(sim.history), 1)
        # (b) consistent NaN raw MAE reaches select_monitor_value and raises PreparationError.
        class NanMaeSim(Sim):
            def eval_epoch(self, epoch):
                mse, fit, stop = super().eval_epoch(epoch)
                if epoch == 1:
                    stop = (mse, {"mae": float("nan"), "mse": mse})
                    fit = (fit[0], {"mae": float("nan"), "mse": fit[1]["mse"]})
                return mse, fit, stop
        sim = NanMaeSim([2.0, float("nan")], 2, 8)
        with self.assertRaises(science.PreparationError):
            drive(sim)
        self.assertEqual(len(sim.history), 1)

    def test_history_consistency_failures(self):
        good = [{"epoch": 1, "steps": 5, "internal_validation_standardized_mse": 4.0,
                 "internal_validation_raw_mae": 4.0, "monitor": science.MONITOR_RAW_MAE,
                 "monitor_key": "internal_validation_raw_mae", "monitor_value": 4.0},
                {"epoch": 2, "steps": 10, "internal_validation_standardized_mse": 1.0,
                 "internal_validation_raw_mae": 1.0, "monitor": science.MONITOR_RAW_MAE,
                 "monitor_key": "internal_validation_raw_mae", "monitor_value": 1.0}]
        science.checkpoint_identity(good, 1)
        for mutation in (
            lambda h: h[0].update(internal_validation_raw_mae=9.0),           # monitor_value mismatch
            lambda h: h[1].update(steps=0),                                    # non-positive steps
            lambda h: h[0].update(epoch=7),                                    # bad epoch identity
            lambda h: h[1].update(internal_validation_raw_mae=float("nan")),   # NaN metric
            lambda h: h[0].update(monitor="internal_validation_raw_rmse"),     # unknown monitor
            lambda h: h[0].pop("internal_validation_standardized_mse"),        # missing retained metric
        ):
            bad = copy.deepcopy(good)
            mutation(bad)
            with self.assertRaises(science.PreparationError):
                science.checkpoint_identity(bad, 1)


class IdentityBoundary(unittest.TestCase):
    def test_real_blind_inputs_load_without_label_request(self):
        rows, hashes, audits = science.load_input_tables(CONFIG, TASK / "input", safe, digest)
        self.assertEqual([len(rows[s]) for s in ("train", "valid", "test")], [637, 91, 182])
        self.assertTrue(all("Y" not in r for s in ("valid", "test") for r in rows[s]))
        for split, role in (("train", "train"), ("valid", "validation"), ("test", "test")):
            item = next(i for i in CONFIG["inputs"] if i["role"] == role)
            self.assertEqual(hashes[role], item["sha256"])
            with (TASK / "input/data" / f"{split}.csv").open(newline="", encoding="utf-8-sig") as f:
                self.assertEqual(rows[split], list(csv.DictReader(f)))
        self.assertEqual(set(audits["valid"]["duplicate_drug_ids"]), {"14", "22"})
        self.assertEqual(set(audits["test"]["duplicate_drug_ids"]), {"1", "3", "25", "PNU200969"})
        for s in ("valid", "test"):
            full = collections.Counter((r["Drug_ID"], r["Drug"]) for r in rows[s])
            self.assertTrue(all(v == 1 for v in full.values()))  # no duplicate complete row keys
            dup = set(audits[s]["duplicate_drug_ids"])
            for rid in dup:
                drugs = {r["Drug"] for r in rows[s] if r["Drug_ID"] == rid}
                self.assertGreater(len(drugs), 1)                # repeated ID -> distinct Drugs, all rows kept

    def test_synthetic_empty_and_duplicate_ids_every_split(self):
        with tempfile.TemporaryDirectory(dir=OUT / "raw/tmp") as temporary:
            root = Path(temporary)
            (root / "data").mkdir()
            cfg = copy.deepcopy(CONFIG)
            table = [{"Drug_ID": "", "Drug": "C"}, {"Drug_ID": "same", "Drug": "CC"},
                     {"Drug_ID": "same", "Drug": "CCO"}]
            for item in cfg["inputs"]:
                fields = ["Drug_ID", "Drug"] + (["Y"] if item["role"] == "train" else [])
                rows = [dict(r) for r in table]
                if item["role"] == "train":
                    for r in rows:
                        r["Y"] = "1.25"
                with (root / item["path"]).open("w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=fields)
                    w.writeheader()
                    w.writerows(rows)
                item["rows"] = len(rows)
                item["sha256"] = digest(root / item["path"])
            loaded, _, audits = science.load_input_tables(cfg, root, safe, digest)
            for split in loaded:
                self.assertEqual([x["Drug_ID"] for x in loaded[split]], ["", "same", "same"])
                self.assertEqual(audits[split]["blank_drug_id_rows"], [0])
                self.assertEqual(audits[split]["duplicate_drug_ids"], ["same"])

    def test_duplicate_complete_train_rows_rejected_by_split(self):
        rows = [{"Drug_ID": "dup", "Drug": "CC", "Y": "1.0"},
                {"Drug_ID": "dup", "Drug": "CC", "Y": "1.0"},
                {"Drug_ID": "other", "Drug": "CCC", "Y": "2.0"}]
        audit = science.check_rows_identity(rows, require_y=True, label="train")
        self.assertEqual(audit["multi_row_raw_drugs"], ["CC"])
        with self.assertRaises(science.PreparationError):
            science.split_train_stop_groups(rows[:2], 43, 0.1)  # single-group split empties the fit set

    def test_blind_split_run_does_not_depend_on_other_outputs(self):
        with tempfile.TemporaryDirectory(dir=OUT / "raw/tmp") as temporary:
            root = Path(temporary)
            (root / "data").mkdir()
            cfg = copy.deepcopy(CONFIG)
            cfg["inputs"] = [i for i in cfg["inputs"] if i["role"] == "validation"]
            dst = root / "data/valid.csv"
            dst.write_bytes((TASK / "input/data/valid.csv").read_bytes())
            for item in cfg["inputs"]:
                item["sha256"] = digest(dst)
            rows, _, _ = science.load_input_tables(cfg, root, safe, digest)
            self.assertEqual(list(rows), ["valid"])
            self.assertEqual(len(rows["valid"]), 91)

    def test_split_record_integrity_and_independent_rng(self):
        rows, _, _ = science.load_input_tables(CONFIG, TASK / "input", safe, digest)
        rec = science.split_train_stop_groups(rows["train"], CONFIG["split_config"]["seed"],
                                              CONFIG["split_config"]["validation_fraction"])
        without = {k: v for k, v in rec.items() if k != "split_record_sha256"}
        self.assertEqual(rec["split_record_sha256"], science.sha256_hex(science.canonical_json_bytes(without)))
        self.assertEqual(sorted(rec["fit_row_indices"] + rec["stop_row_indices"]), list(range(637)))
        r20 = [{"Drug_ID": "" if i % 2 else "same", "Drug": "C" * (i // 2 + 1), "Y": "1"} for i in range(20)]
        original = copy.deepcopy(r20)
        random.seed(1)
        a = science.split_train_stop_groups(r20, 43, .1)
        random.seed(72)
        random.random()
        b = science.split_train_stop_groups(r20, 43, .1)
        self.assertEqual(a, b)
        self.assertEqual(r20, original)


@unittest.skipUnless(HAVE_TORCH, "torch unavailable in preparation env — host must run")
class TorchState(unittest.TestCase):
    def test_optimizer_tensor_roundtrip_no_step(self):
        p = torch.nn.Parameter(torch.tensor([1.0, 2.0]))
        opt = torch.optim.AdamW([p], lr=0.0005)
        opt.state[p] = {"step": torch.tensor(7.0), "exp_avg": torch.tensor([0.1, 0.2]),
                        "exp_avg_sq": torch.tensor([0.01, 0.04])}
        before = p.detach().clone()
        saved = science.optimizer_payload(opt.state_dict())
        with tempfile.TemporaryDirectory(dir=OUT / "raw/tmp") as temporary:
            path = Path(temporary) / "state.pt"
            torch.save(saved, path)
            loaded = torch.load(path, weights_only=True, map_location="cpu")
            q = torch.nn.Parameter(torch.tensor([1.0, 2.0]))
            other = torch.optim.AdamW([q], lr=0.1)
            other.load_state_dict(loaded)
            self.assertTrue(science.state_equal(science.optimizer_payload(other.state_dict()), saved))
        self.assertTrue(torch.equal(p.detach(), before))
        self.assertIn("exp_avg", saved["state"][0])
        self.assertIsInstance(saved["param_groups"][0], dict)

    def test_rng_sources_roundtrip_no_training(self):
        random.seed(43)
        np.random.seed(43)
        torch.manual_seed(43)
        sampler = torch.Generator().manual_seed(43)
        state = science.capture_training_rng(43, sampler)
        def draw():
            return [random.random(), np.random.random(3).tolist(), torch.rand(3),
                    torch.randperm(17, generator=sampler)]
        a = draw()
        science.restore_training_rng(state, sampler)
        b = draw()
        self.assertTrue(science.state_equal(a, b))


class ConsumerLink(unittest.TestCase):
    def _stage(self, stage: Path):
        for name in ("test_host_science.py", "config.json", "training_science.py"):
            src = (TASK / "input/reference" / name) if name == "test_host_science.py" else OUT / name
            shutil.copyfile(src, stage / name)
        (stage / "input").symlink_to(TASK / "input", target_is_directory=True)

    @unittest.skipUnless(HAVE_TORCH, "reference suite imports torch at module level")
    def test_reference_host_suite_against_new_module(self):
        with tempfile.TemporaryDirectory(dir=OUT / "raw/tmp") as temporary:
            stage = Path(temporary)
            self._stage(stage)
            proc = subprocess.run([sys.executable, "-m", "unittest", "-v", "test_host_science"],
                                  cwd=stage, capture_output=True, text=True)
            print(proc.stderr[-4000:])
            self.assertEqual(proc.returncode, 0, "reference host suite must pass against new module")

    def test_reference_host_suite_nontorch_cases_standalone(self):
        # Execute the torch-free case bodies of the reference suite against the new production
        # module without importing the reference file itself (module-level torch import fails here).
        with tempfile.TemporaryDirectory(dir=OUT / "raw/tmp") as temporary:
            stage = Path(temporary)
            self._stage(stage)
            ref_cfg = json.loads((stage / "config.json").read_text())
            rows, _, audits = science.load_input_tables(ref_cfg, TASK / "input", safe, digest)
            self.assertEqual([len(rows[s]) for s in ("train", "valid", "test")], [637, 91, 182])
            self.assertEqual([len(audits[s]["duplicate_drug_ids"]) for s in ("valid", "test")], [2, 4])
            self.assertTrue(all("Y" not in r for s in ("valid", "test") for r in rows[s]))
            science.validate_config(ref_cfg)
            for key, value in [("optimizer", "SGD"), ("lr", float("nan")), ("batch_size", True)]:
                bad = copy.deepcopy(ref_cfg)
                bad["head_config"][key] = value
                with self.assertRaises(science.PreparationError):
                    science.validate_config(bad)
            bad = copy.deepcopy(ref_cfg)
            bad["inputs"][1]["task"] = "other"
            with self.assertRaises(science.PreparationError):
                science.validate_config(bad)
            frows = [{"Drug_ID": "same", "Drug": "C"}, {"Drug_ID": "same", "Drug": "CC"}]
            feats = np.array([[1., 2.], [3., 4.]], dtype=np.float32)
            mask = np.array([True, True])
            ia = science.feature_identity(feats, mask, frows, {"version": "fixed"}, 2, "a" * 64)
            ib = science.feature_identity(feats[::-1], mask, frows, {"version": "fixed"}, 2, "a" * 64)
            ic = science.feature_identity(feats, mask, frows[::-1], {"version": "fixed"}, 2, "a" * 64)
            self.assertNotEqual(ia["identity_sha256"], ib["identity_sha256"])
            self.assertNotEqual(ia["identity_sha256"], ic["identity_sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
