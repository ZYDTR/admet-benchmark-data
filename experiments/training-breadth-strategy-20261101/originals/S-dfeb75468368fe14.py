"""Product/score refusal checks on SYNTHETIC data. No training, stdlib only."""

import os
import shutil
import tempfile
import unittest

import helpers

from errors import ScoringError
from metrics import score
from predict_io import read_products, write_products


def _keys(tasks, split, n):
    return {(t, split, i): None for t in tasks for i in range(n)}


class ProductTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ocprep_", dir=helpers.WORK_TMP)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _recs(self, tasks, split, n):
        return [{"task": t, "split": split, "row_index": i, "y_pred": float(i) + 0.5}
                for t in tasks for i in range(n)]

    def test_roundtrip_ok(self):
        path = os.path.join(self.tmp, "ok.csv")
        write_products(path, self._recs(["ames"], "valid", 3))
        out = read_products(path, _keys(["ames"], "valid", 3), splits=("valid",))
        self.assertEqual(set(out), set(_keys(["ames"], "valid", 3)))
        self.assertAlmostEqual(out[("ames", "valid", 2)], 2.5)

    def test_refuses_empty_expected(self):
        path = os.path.join(self.tmp, "ok.csv")
        write_products(path, self._recs(["ames"], "valid", 1))
        with self.assertRaises(ScoringError):
            read_products(path, {}, splits=("valid",))

    def test_refuses_missing_and_extra(self):
        path = os.path.join(self.tmp, "p.csv")
        write_products(path, self._recs(["ames"], "valid", 2))
        with self.assertRaises(ScoringError):
            read_products(path, _keys(["ames"], "valid", 3), splits=("valid",))
        write_products(path, self._recs(["ames"], "valid", 3))
        with self.assertRaises(ScoringError):
            read_products(path, _keys(["ames"], "valid", 2), splits=("valid",))

    def test_refuses_duplicate_key(self):
        path = os.path.join(self.tmp, "dup.csv")
        write_products(path, self._recs(["ames"], "valid", 2) + self._recs(["ames"], "valid", 1))
        with self.assertRaises(ScoringError):
            read_products(path, _keys(["ames"], "valid", 2), splits=("valid",))

    def test_refuses_wrong_split_and_nonfinite(self):
        path = os.path.join(self.tmp, "s.csv")
        write_products(path, self._recs(["ames"], "test", 2))
        with self.assertRaises(ScoringError):
            read_products(path, _keys(["ames"], "valid", 2), splits=("valid",))
        path2 = os.path.join(self.tmp, "nan.csv")
        with open(path2, "w", encoding="utf-8") as fh:
            fh.write("task,split,row_index,y_pred\names,valid,0,nan\n")
        with self.assertRaises(ScoringError):
            read_products(path2, _keys(["ames"], "valid", 1), splits=("valid",))

    def test_refuses_wrong_header(self):
        path = os.path.join(self.tmp, "hdr.csv")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("task,split,index,y_pred\names,valid,0,0.5\n")
        with self.assertRaises(ScoringError):
            read_products(path, _keys(["ames"], "valid", 1), splits=("valid",))

    def test_write_refuses_nonfinite(self):
        path = os.path.join(self.tmp, "inf.csv")
        with self.assertRaises(ScoringError):
            write_products(path, [{"task": "ames", "split": "valid", "row_index": 0,
                                   "y_pred": float("inf")}])


class MetricsSyntheticTests(unittest.TestCase):
    def test_metrics_on_synthetic_labels(self):
        y = [0, 1, 0, 1]
        s = [0.1, 0.9, 0.2, 0.8]
        r = score("AUROC", y, s)
        self.assertTrue(r["defined"])
        self.assertAlmostEqual(r["value"], 1.0)
        a = score("AUPRC", y, s)
        self.assertTrue(a["defined"])
        self.assertGreater(a["value"], 0.5)
        self.assertAlmostEqual(score("MAE", y, y)["value"], 0.0)
        sp = score("Spearman", [1, 2, 3], [10, 20, 30])
        self.assertTrue(sp["defined"])
        self.assertAlmostEqual(sp["value"], 1.0)
        sp2 = score("Spearman", [1, 2, 3, 4], [4, 3, 2, 1])
        self.assertAlmostEqual(sp2["value"], -1.0)

    def test_undefined_cases_recorded_not_fabricated(self):
        self.assertFalse(score("AUROC", [1, 1, 1], [0.1, 0.2, 0.3])["defined"])
        self.assertFalse(score("AUROC", [], [])["defined"])
        self.assertFalse(score("Spearman", [1, 1, 1], [0.1, 0.2, 0.3])["defined"])
        self.assertFalse(score("AUROC", [0, 2], [0.1, 0.2])["defined"])
        with self.assertRaises(ValueError):
            score("MAE", [], [])


class AssetGuardTests(unittest.TestCase):
    """These need no torch: the digest guard runs before any weight loading."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ocprep_", dir=helpers.WORK_TMP)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_wrong_size_weights_refused(self):
        from assets import verify_weights_file
        from errors import InputContractError

        fake = os.path.join(self.tmp, "chemeleon_mp.pt")
        with open(fake, "wb") as fh:
            fh.write(b"0" * 16)
        with self.assertRaises(InputContractError):
            verify_weights_file(fake)

    def test_right_size_wrong_md5_refused(self):
        from assets import CHEMELEON_SIZE, verify_weights_file
        from errors import InputContractError

        fake = os.path.join(self.tmp, "chemeleon_mp.pt")
        with open(fake, "wb") as fh:
            fh.write(b"\0" * CHEMELEON_SIZE)
        with self.assertRaises(InputContractError):
            verify_weights_file(fake)

    def test_asset_lock_missing_and_mismatch_refused(self):
        import json

        from assets import CHEMELEON_CODE_COMMIT, CHEMELEON_MD5, CHEMELEON_SIZE, load_lock
        from errors import InputContractError

        with self.assertRaises(InputContractError):
            load_lock(os.path.join(self.tmp, "absent.json"))
        good = {"weights_sha256": "a" * 64, "weights_md5": CHEMELEON_MD5,
                "weights_size": CHEMELEON_SIZE, "code_commit": CHEMELEON_CODE_COMMIT}
        path = os.path.join(self.tmp, "lock.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(good, fh)
        self.assertEqual(load_lock(path)["weights_sha256"], "a" * 64)
        for key, bad in (("weights_md5", "0" * 32), ("weights_size", 1),
                         ("code_commit", "0" * 40)):
            broken = dict(good, **{key: bad})
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(broken, fh)
            with self.assertRaises(InputContractError):
                load_lock(path)


if __name__ == "__main__":
    unittest.main()