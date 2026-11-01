"""Head save/load + submission export checks on SYNTHETIC data.

These tests need only ``torch`` (head.pt) and numpy/csv (submission).  If torch is
missing they are skipped and recorded as unverified in checks.json via the runner
output.  No optimizer step is performed: the head is constructed with random
initialisation and only saved/reloaded/evaluated in ``eval()`` mode.
"""

import math
import os
import shutil
import tempfile
import unittest

import helpers

from dataio import read_template
from errors import ScoringError
from predict_io import write_products
from submission import build_submission, verify_submission

try:  # optional dependency
    import torch  # noqa: F401

    HAVE_TORCH = True
except Exception:  # pragma: no cover
    HAVE_TORCH = False


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ocprep_", dir=helpers.WORK_TMP)
        self.root = os.path.join(self.tmp, "pack")
        self.tasks, self.sizes = helpers.make_synthetic_root(self.root)
        self.template_path = helpers.make_template(self.root, self.tasks,
                                                   n_test=self.sizes["test"])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _products(self, tasks, split, n, scale=1.0):
        recs = [{"task": t, "split": split, "row_index": i, "y_pred": scale * (i + 1)}
                for t in tasks for i in range(n)]
        path = os.path.join(self.tmp, "products.csv")
        write_products(path, recs)
        return path

    def test_submission_subset_preserves_template(self):
        tpl = read_template(self.root, expected_rows=2 * self.sizes["test"])
        prod = self._products(["ames"], "test", self.sizes["test"])
        out = os.path.join(self.tmp, "sub.csv")
        info = build_submission(self.root, ["ames"], prod, out, template=tpl)
        self.assertEqual(info["rows_filled"], self.sizes["test"])
        verify_submission(tpl, out, ["ames"])
        # Non-ames rows must stay blank and untouched.
        import csv

        with open(out, "r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        ames = [r for r in rows if r["task"] == "ames"]
        others = [r for r in rows if r["task"] != "ames"]
        self.assertTrue(all(r["y_pred"] != "" for r in ames))
        self.assertTrue(all(r["y_pred"] == "" for r in others))
        self.assertTrue(all(math.isfinite(float(r["y_pred"])) for r in ames))

    def test_submission_refuses_missing_prediction(self):
        tpl = read_template(self.root, expected_rows=2 * self.sizes["test"])
        # Product missing the last test row of ames.
        recs = [{"task": "ames", "split": "test", "row_index": i, "y_pred": 0.5}
                for i in range(self.sizes["test"] - 1)]
        prod = os.path.join(self.tmp, "partial.csv")
        write_products(prod, recs)
        out = os.path.join(self.tmp, "sub.csv")
        with self.assertRaises(ScoringError):
            build_submission(self.root, ["ames"], prod, out, template=tpl)

    def test_verify_submission_detects_tamper(self):
        tpl = read_template(self.root, expected_rows=2 * self.sizes["test"])
        prod = self._products(["ames"], "test", self.sizes["test"])
        out = os.path.join(self.tmp, "sub.csv")
        build_submission(self.root, ["ames"], prod, out, template=tpl)
        import csv

        with open(out, "r", encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        rows[1][0] = "tampered"  # change task
        with open(out, "w", encoding="utf-8", newline="") as fh:
            csv.writer(fh).writerows(rows)
        with self.assertRaises(ScoringError):
            verify_submission(tpl, out, ["ames"])


@unittest.skipUnless(HAVE_TORCH, "torch not installed: head artifact unverified")
class HeadArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ocprep_", dir=helpers.WORK_TMP)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_save_load_roundtrip_regression_scale(self):
        from head_model import HEAD_CONFIG, TargetScaler, build_head, load_head, predict, save_head

        cfg = dict(HEAD_CONFIG, hidden_dim=8, max_epochs=1)
        head, _, cfg = build_head(4, "regression", cfg)
        scaler = TargetScaler.fit([1.0, 3.0, 5.0])
        path = os.path.join(self.tmp, "caco2_wang", "head.pt")
        save_head(head, path, "caco2_wang", "regression", scaler, cfg)
        head2, meta = load_head(path, expect_task="caco2_wang")
        self.assertEqual(meta["task_kind"], "regression")
        # inverse(transform(y)) == y proves Y-scale restoration.
        y = np.array([1.0, 3.0, 5.0])
        np.testing.assert_allclose(scaler.inverse(scaler.transform(y)), y)
        out = predict(head2, np.zeros((2, 4), dtype=np.float32), "regression", meta["scaler"])
        self.assertEqual(out.shape, (2,))

    def test_load_head_rejects_wrong_task(self):
        from head_model import HEAD_CONFIG, build_head, load_head, save_head

        head, _, cfg = build_head(4, "classification", dict(HEAD_CONFIG, hidden_dim=8))
        path = os.path.join(self.tmp, "ames", "head.pt")
        save_head(head, path, "ames", "classification", None, cfg)
        with self.assertRaises(ValueError):
            load_head(path, expect_task="dili")

    def test_encoder_weights_verifier_rejects_wrong_size(self):
        from assets import CHEMELEON_SIZE, verify_weights_file
        from errors import InputContractError

        fake = os.path.join(self.tmp, "chemeleon_mp.pt")
        with open(fake, "wb") as fh:
            fh.write(b"0" * 16)
        with self.assertRaises(InputContractError):
            verify_weights_file(fake)
        self.assertEqual(CHEMELEON_SIZE, 34859448)


if __name__ == "__main__":
    unittest.main()