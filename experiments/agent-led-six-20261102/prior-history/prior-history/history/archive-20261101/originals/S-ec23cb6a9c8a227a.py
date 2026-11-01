"""Synthetic unit tests for metric definitions (stdlib unittest).

All inputs are fixed synthetic constants; results are known analytic values.
"""
from __future__ import annotations

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from admet_eval import metrics as M  # noqa: E402


class TestAverageRanks(unittest.TestCase):
    def test_ties_get_mean_rank(self):
        self.assertEqual(M.average_ranks([10, 20, 20, 30]), [1.0, 2.5, 2.5, 4.0])

    def test_all_tied(self):
        self.assertEqual(M.average_ranks([5, 5, 5]), [2.0, 2.0, 2.0])


class TestMAE(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(M.mae([1.0, 2.0, 3.0], [2.0, 2.0, 1.0]), (1 + 0 + 2) / 3)

    def test_empty_undefined(self):
        with self.assertRaises(M.MetricUndefined):
            M.mae([], [])

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            M.mae([1.0, float("nan")], [1.0, 1.0])


class TestSpearman(unittest.TestCase):
    def test_perfect_monotonic(self):
        self.assertAlmostEqual(M.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)

    def test_reverse(self):
        self.assertAlmostEqual(M.spearman([1, 2, 3, 4], [40, 30, 20, 10]), -1.0)

    def test_ties_use_average_rank(self):
        # true [1,2,2,3] vs pred [1,2,3,4]: average ranks 1,2.5,2.5,4 vs 1,2,3,4
        x = M.average_ranks([1, 2, 2, 3])
        y = M.average_ranks([1, 2, 3, 4])
        self.assertAlmostEqual(M.spearman([1, 2, 2, 3], [1, 2, 3, 4]), M._pearson(x, y))
        # sanity: value is in (0.9, 1); average ranks must be used (they are)
        self.assertTrue(0.9 < M.spearman([1, 2, 2, 3], [1, 2, 3, 4]) < 1.0)

    def test_constant_true_undefined(self):
        with self.assertRaises(M.MetricUndefined) as cm:
            M.spearman([1, 1, 1], [1, 2, 3])
        self.assertEqual(cm.exception.reason, "constant_true")

    def test_constant_pred_undefined(self):
        with self.assertRaises(M.MetricUndefined) as cm:
            M.spearman([1, 2, 3], [5, 5, 5])
        self.assertEqual(cm.exception.reason, "constant_pred")

    def test_single_sample_undefined(self):
        with self.assertRaises(M.MetricUndefined):
            M.spearman([1], [1])


class TestAUROC(unittest.TestCase):
    def test_perfect_separation(self):
        self.assertAlmostEqual(M.auroc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]), 1.0)

    def test_reversed_is_zero(self):
        self.assertAlmostEqual(M.auroc([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1]), 0.0)

    def test_all_tied_is_half(self):
        self.assertAlmostEqual(M.auroc([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5]), 0.5)

    def test_partial_tie(self):
        # pos scores [0.5,0.9], neg [0.5,0.1]
        # pairs: 0.5 vs 0.5 tie=0.5; 0.5 vs 0.1 win; 0.9 vs both win => (0.5+1+2)/4
        self.assertAlmostEqual(M.auroc([0, 1, 0, 1], [0.5, 0.5, 0.1, 0.9]), (0.5 + 1 + 2) / 4)

    def test_one_class_undefined(self):
        with self.assertRaises(M.MetricUndefined) as cm:
            M.auroc([1, 1, 1], [0.1, 0.2, 0.3])
        self.assertEqual(cm.exception.reason, "one_class")


class TestAveragePrecision(unittest.TestCase):
    def test_doc_example_5_over_6(self):
        # labels [1,0,1], scores [0.9,0.8,0.7] -> AP=5/6 (not trapezoid 19/24)
        self.assertAlmostEqual(M.average_precision([1, 0, 1], [0.9, 0.8, 0.7]), 5 / 6)
        self.assertNotAlmostEqual(M.average_precision([1, 0, 1], [0.9, 0.8, 0.7]), 19 / 24)

    def test_perfect(self):
        self.assertAlmostEqual(M.average_precision([1, 1, 0], [0.9, 0.8, 0.1]), 1.0)

    def test_tie_merged(self):
        # scores tie [0.5,0.5], labels [1,0]; merged threshold => precision 0.5, recall jump 1 => 0.5
        self.assertAlmostEqual(M.average_precision([1, 0], [0.5, 0.5]), 0.5)

    def test_one_class_undefined(self):
        with self.assertRaises(M.MetricUndefined) as cm:
            M.average_precision([0, 0, 0], [0.1, 0.2, 0.3])
        self.assertEqual(cm.exception.reason, "one_class")

    def test_sklearn_reference_hand_computed(self):
        # scores [0.4,0.35,0.8,0.1], labels [1,0,1,0]
        # order desc: 0.8(1) tp=1 p=1 r=0.5; 0.4(1) tp=2 p=1 r=1; 0.35(0);0.1(0)
        # AP = 0.5*1 + 0.5*1 = 1.0
        self.assertAlmostEqual(M.average_precision([1, 0, 1, 0], [0.4, 0.35, 0.8, 0.1]), 1.0)
        # a harder case: labels [0,1,0,1], scores [0.1,0.2,0.3,0.4]
        # desc: 0.4(1) tp1 p1 r.5; 0.3(0); 0.2(1) tp2 p 2/3 r1; 0.1(0)
        # AP = .5*1 + .5*(2/3) = .5 + .3333 = .83333
        self.assertAlmostEqual(M.average_precision([0, 1, 0, 1], [0.1, 0.2, 0.3, 0.4]),
                               0.5 + 0.5 * (2 / 3))


class TestDispatch(unittest.TestCase):
    def test_reject_nonbinary(self):
        with self.assertRaises(ValueError):
            M.compute("AUROC", "classification", [0, 2], [0.1, 0.2])

    def test_boolean_labels_rejected(self):
        with self.assertRaises(ValueError):
            M.compute("AUROC", "classification", [True, False], [0.1, 0.2])


if __name__ == "__main__":
    unittest.main(verbosity=2)