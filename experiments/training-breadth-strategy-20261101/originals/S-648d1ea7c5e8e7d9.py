"""Data-contract checks on SYNTHETIC small packs + read-only checks on the real pack.

Run with:  python3 -m unittest discover -s tests -v   (from output/, stdlib only)

The real-pack checks only read; they verify identity/coverage facts (row counts,
template join, repeated molecules retained, header rules) without needing torch.
"""

import os
import shutil
import tempfile
import unittest

import helpers  # noqa: F401  (sets sys.path)

from dataio import (
    TEMPLATE_ROWS,
    input_digest,
    list_tasks,
    read_split,
    read_template,
    verify_template_mapping,
)
from errors import InputContractError, LabelError

REAL_ROOT = helpers.REPO_INPUT_DATA


class SyntheticPackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ocprep_", dir=helpers.WORK_TMP)
        self.root = self.tmp
        self.tasks, self.sizes = helpers.make_synthetic_root(self.root)
        helpers.make_template(self.root, self.tasks, n_test=self.sizes["test"])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_row_identity_and_no_dedup(self):
        tab = read_split(self.root, "ames", "train")
        self.assertEqual([r["row_index"] for r in tab["rows"]], list(range(self.sizes["train"])))
        self.assertEqual(len(tab["labels"]), self.sizes["train"])
        # Duplicated (Drug_ID, Drug) pair with different Y: both rows must survive.
        helpers.write_csv(
            os.path.join(self.root, "official", "data_benchmark", "ames", "train.csv"),
            ["Drug_ID", "Drug", "Y"],
            [["D1", "CC", 0], ["D1", "CC", 1], ["D2", "CCC", 0]],
        )
        tab = read_split(self.root, "ames", "train")
        self.assertEqual(tab["n_rows"], 3)
        self.assertEqual(tab["labels"], [0.0, 1.0, 0.0])
        self.assertEqual([r["row_index"] for r in tab["rows"]], [0, 1, 2])

    def test_rejects_bad_header_and_label_in_blind_split(self):
        bad = os.path.join(self.root, "official", "data_benchmark", "ames", "train.csv")
        helpers.write_csv(bad, ["Drug_ID", "SMILES", "Y"], [["a", "CC", 0]])
        with self.assertRaises(InputContractError):
            read_split(self.root, "ames", "train")
        helpers.write_csv(
            os.path.join(self.root, "official", "data_benchmark", "ames", "test.csv"),
            ["Drug_ID", "Drug", "Y"],
            [["a", "CC", 0]],
        )
        with self.assertRaises(InputContractError):
            read_split(self.root, "ames", "test")

    def test_rejects_non_numeric_or_nonfinite_train_label(self):
        bad = os.path.join(self.root, "official", "data_benchmark", "ames", "train.csv")
        helpers.write_csv(bad, ["Drug_ID", "Drug", "Y"], [["a", "CC", "nan"]])
        with self.assertRaises(LabelError):
            read_split(self.root, "ames", "train")
        helpers.write_csv(bad, ["Drug_ID", "Drug", "Y"], [["a", "CC", "oops"]])
        with self.assertRaises(LabelError):
            read_split(self.root, "ames", "train")

    def test_template_mapping_ok_and_rejects_mismatch(self):
        tests = {t: read_split(self.root, t, "test") for t in self.tasks}
        tpl = read_template(self.root, expected_rows=2 * self.sizes["test"])
        self.assertTrue(verify_template_mapping(tpl, tests))
        tpl2 = read_template(self.root, expected_rows=2 * self.sizes["test"])
        tpl2["rows"][1]["sample_idx"] = "99"
        with self.assertRaises(InputContractError):
            verify_template_mapping(tpl2, tests)
        tpl3 = read_template(self.root, expected_rows=2 * self.sizes["test"])
        tpl3["rows"][2]["smiles"] = "XX"
        with self.assertRaises(InputContractError):
            verify_template_mapping(tpl3, tests)
        tpl4 = read_template(self.root, expected_rows=2 * self.sizes["test"])
        tpl4["rows"] = tpl4["rows"][:-1]
        with self.assertRaises(InputContractError):
            verify_template_mapping(tpl4, tests)

    def test_input_digest_is_row_order_sensitive(self):
        a = read_split(self.root, "ames", "train")
        b = read_split(self.root, "ames", "train")
        self.assertEqual(input_digest([("train", a)])["digest_sha256"],
                         input_digest([("train", b)])["digest_sha256"])
        c = dict(a)
        c["rows"] = list(reversed(a["rows"]))
        self.assertNotEqual(input_digest([("train", a)])["digest_sha256"],
                            input_digest([("train", c)])["digest_sha256"])


class RealPackReadOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = list_tasks(REAL_ROOT)

    def test_all_22_tasks_present(self):
        self.assertEqual(len(self.tasks), 22)

    def test_template_identity_join_all_tasks(self):
        tpl = read_template(REAL_ROOT)
        self.assertEqual(len(tpl["rows"]), TEMPLATE_ROWS)
        tests = {t: read_split(REAL_ROOT, t, "test") for t in self.tasks}
        self.assertTrue(verify_template_mapping(tpl, tests))
        self.assertEqual(sum(t["n_rows"] for t in tests.values()), TEMPLATE_ROWS)

    def test_blind_splits_carry_no_labels(self):
        for t in self.tasks:
            for split in ("valid", "test"):
                tab = read_split(REAL_ROOT, t, split)
                self.assertFalse(tab["header_has_label"], f"{t}/{split} has Y")
                self.assertIsNone(tab["labels"])

    def test_repeated_smiles_retained_in_ppbr(self):
        from collections import Counter

        tab = read_split(REAL_ROOT, "ppbr_az", "train")
        counts = Counter(tab["smiles"])
        self.assertTrue(any(c > 1 for c in counts.values()))
        self.assertEqual(tab["n_rows"], len(tab["rows"]))

    def test_empty_drug_id_kept_as_string(self):
        tab = read_split(REAL_ROOT, "herg", "train")
        self.assertTrue(any(d == "" for d in tab["drug_ids"]))

    def test_train_label_counts_match_profile(self):
        # From input/research/data-profile.md (counts only, no labels inspected).
        expected = {"ames": 4684, "ld50_zhu": 3970, "solubility_aqsoldb": 5045,
                    "cyp2d6_veith": 9191, "dili": 331}
        for task, n in expected.items():
            self.assertEqual(read_split(REAL_ROOT, task, "train")["n_rows"], n)


if __name__ == "__main__":
    unittest.main()