"""Numerical metric implementations (stdlib only, rank-based).

Definitions (per TASK.md local metric convention):
  MAE        mean absolute error, lower better
  Spearman   average-rank tie handling, then Pearson correlation of ranks;
             undefined when n<2 or either side is constant
  AUROC      Mann-Whitney form with average ranks for tied scores;
             undefined for a single label class
  AP         average precision: tie-merged thresholds; sum of
             (recall increment * precision at threshold); NO trapezoid.
             local only, official AUPRC equivalence unconfirmed.
             undefined for a single label class (project convention).

These are pure functions over already-validated numeric arrays; NaN/Inf and
boolean/string inputs must be rejected before reaching them by the CLI layer,
but the functions also guard defensively.
"""
from __future__ import annotations

import math
from typing import List, Sequence


class MetricUndefined(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _check_finite(values: Sequence[float], name: str) -> None:
    for i, v in enumerate(values):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise TypeError(f"{name}[{i}] is not a number: {v!r}")
        if not math.isfinite(v):
            raise ValueError(f"{name}[{i}] is not finite: {v!r}")


def mae(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    _check_finite(y_true, "y_true")
    _check_finite(y_pred, "y_pred")
    if len(y_true) != len(y_pred):
        raise ValueError("length mismatch")
    if not y_true:
        raise MetricUndefined("no_samples")
    return sum(abs(a - b) for a, b in zip(y_true, y_pred)) / len(y_true)


def average_ranks(values: Sequence[float]) -> List[float]:
    """1-based average ranks; ties receive their mean rank."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0  # mean of 1-based positions i+1..j+1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(x: Sequence[float], y: Sequence[float]) -> float:
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    sx = 0.0
    sy = 0.0
    sxy = 0.0
    for a, b in zip(x, y):
        da = a - mx
        db = b - my
        sx += da * da
        sy += db * db
        sxy += da * db
    if sx == 0.0 or sy == 0.0:
        raise MetricUndefined("constant_input")
    return sxy / math.sqrt(sx * sy)


def spearman(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    _check_finite(y_true, "y_true")
    _check_finite(y_pred, "y_pred")
    if len(y_true) != len(y_pred):
        raise ValueError("length mismatch")
    if len(y_true) < 2:
        raise MetricUndefined("fewer_than_two_samples")
    if len(set(y_true)) == 1:
        raise MetricUndefined("constant_true")
    if len(set(y_pred)) == 1:
        raise MetricUndefined("constant_pred")
    return _pearson(average_ranks(y_true), average_ranks(y_pred))


def auroc(y_true: Sequence[int], y_score: Sequence[float]) -> float:
    """Mann-Whitney AUROC.  y_true must be 0/1."""
    _check_finite(y_score, "y_score")
    if len(y_true) != len(y_score):
        raise ValueError("length mismatch")
    n_pos = sum(1 for t in y_true if t == 1)
    n_neg = sum(1 for t in y_true if t == 0)
    if n_pos + n_neg != len(y_true):
        raise ValueError("labels must be 0/1")
    if n_pos == 0 or n_neg == 0:
        raise MetricUndefined("one_class")
    ranks = average_ranks(y_score)
    rank_sum_pos = sum(r for r, t in zip(ranks, y_true) if t == 1)
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def average_precision(y_true: Sequence[int], y_score: Sequence[float]) -> float:
    """AP with tie-merged thresholds (sklearn-style step sum)."""
    _check_finite(y_score, "y_score")
    if len(y_true) != len(y_score):
        raise ValueError("length mismatch")
    n_pos = sum(1 for t in y_true if t == 1)
    n_neg = sum(1 for t in y_true if t == 0)
    if n_pos + n_neg != len(y_true):
        raise ValueError("labels must be 0/1")
    if n_pos == 0 or n_neg == 0:
        raise MetricUndefined("one_class")
    # sort desc by score, grouping ties
    order = sorted(range(len(y_score)), key=lambda i: y_score[i], reverse=True)
    tp = 0
    fp = 0
    prev_recall = 0.0
    ap = 0.0
    i = 0
    n = len(order)
    while i < n:
        j = i
        while j + 1 < n and y_score[order[j + 1]] == y_score[order[i]]:
            j += 1
        for k in range(i, j + 1):
            if y_true[order[k]] == 1:
                tp += 1
            else:
                fp += 1
        recall = tp / n_pos
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        ap += (recall - prev_recall) * precision
        prev_recall = recall
        i = j + 1
    return ap


def compute(metric: str, kind: str, y_true: Sequence, y_pred: Sequence) -> float:
    """Dispatch on (metric, kind).  Returns value or raises MetricUndefined."""
    if kind == "classification":
        for t in y_true:
            if isinstance(t, bool) or t not in (0, 1):
                raise ValueError(f"classification label not in {{0,1}}: {t!r}")
        labels = [int(t) for t in y_true]
        if metric == "AUROC":
            return auroc(labels, y_pred)
        if metric in ("AUPRC", "AP"):
            return average_precision(labels, y_pred)
        raise ValueError(f"unknown classification metric {metric}")
    if kind == "regression":
        if metric == "MAE":
            return mae(y_true, y_pred)
        if metric == "Spearman":
            return spearman(y_true, y_pred)
        raise ValueError(f"unknown regression metric {metric}")
    raise ValueError(f"unknown kind {kind}")