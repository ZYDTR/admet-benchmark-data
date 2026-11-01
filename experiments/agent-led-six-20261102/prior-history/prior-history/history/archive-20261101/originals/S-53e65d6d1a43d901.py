"""Pure-standard-library metrics for ADMET frozen-baseline evaluation.

No third-party dependencies (no numpy/sklearn) so the scorer runs in a bare
container. Every function takes plain Python lists and returns a float or None
when a metric is undefined for the given inputs (documented per function).

Metric choices (see research/data-profile.md section 7):
  - classification: AUROC and AUPRC, where AUPRC is Average Precision (AP),
    the step-wise area used by scikit-learn's average_precision_score and by
    the TDC evaluator's pr-auc. The official competition aggregation and the
    exact AUPRC definition are UNCONFIRMED (contract U04); we report local AP.
  - regression: MAE (absolute error on the official Y scale) and Spearman
    rank correlation (average ranks for ties).

Tie handling:
  - AUROC uses the rank-based Mann-Whitney U formulation with average ranks,
    which equals the trapezoidal ROC-AUC under tied scores.
  - AP follows the scikit-learn definition: precision at each threshold where
    a positive sample is added, weighted by the fraction of positives, i.e.
    sum over positives of precision-at-rank(positive) divided by n_positive.
    Ties are broken by grouping equal scores so a tied group contributes its
    points at the end of the group (scikit-learn behaviour).
"""

from __future__ import annotations

import math


def _check_pairs(y_true, y_score):
    if len(y_true) != len(y_score):
        raise ValueError(
            f"length mismatch: y_true={len(y_true)} y_score={len(y_score)}"
        )
    if not y_true:
        raise ValueError("empty input")
    for v in y_score:
        if not math.isfinite(float(v)):
            raise ValueError(f"non-finite score: {v!r}")


def _average_ranks(values):
    """Return average ranks (1-based) for values, assigning mean rank to ties."""
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        if j > i:
            avg = (i + 1 + j + 1) / 2.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg
        else:
            ranks[order[i]] = float(i + 1)
        i = j + 1
    return ranks


def auroc(y_true, y_score):
    """Area under the ROC curve via Mann-Whitney U with average ranks.

    Returns None when y_true contains only one class (AUROC undefined).
    """
    _check_pairs(y_true, y_score)
    labels = [int(round(float(y))) for y in y_true]
    for lab in labels:
        if lab not in (0, 1):
            raise ValueError(f"AUROC requires binary labels, got {lab}")
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return None
    ranks = _average_ranks([float(s) for s in y_score])
    sum_ranks_pos = sum(r for r, lab in zip(ranks, labels) if lab == 1)
    return (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def average_precision(y_true, y_score):
    """Average Precision (step-wise PR area) matching scikit-learn.

    Returns None when there are no positive samples (AP undefined).
    """
    _check_pairs(y_true, y_score)
    labels = [int(round(float(y))) for y in y_true]
    for lab in labels:
        if lab not in (0, 1):
            raise ValueError(f"AP requires binary labels, got {lab}")
    n = len(labels)
    n_pos = sum(labels)
    if n_pos == 0:
        return None
    # Sort by descending score; ties grouped. Average precision = sum over each
    # positive of precision at the rank where that positive is included.
    order = sorted(range(n), key=lambda i: -float(y_score[i]))
    tp = 0
    fp = 0
    prev_recall = 0.0
    ap = 0.0
    i = 0
    while i < n:
        j = i
        score = float(y_score[order[i]])
        group_pos = 0
        group_neg = 0
        while j < n and float(y_score[order[j]]) == score:
            if labels[order[j]] == 1:
                group_pos += 1
            else:
                group_neg += 1
            j += 1
        tp += group_pos
        fp += group_neg
        recall = tp / n_pos
        precision = tp / (tp + fp)
        # scikit-learn: add precision * dRecall for the group (recall increases
        # only if the group contains positives).
        if group_pos:
            ap += precision * (recall - prev_recall)
        prev_recall = recall
        i = j
    return ap


def mae(y_true, y_pred):
    """Mean absolute error. Returns None on empty input."""
    _check_pairs(y_true, y_pred)
    total = 0.0
    for yt, yp in zip(y_true, y_pred):
        total += abs(float(yt) - float(yp))
    return total / len(y_true)


def spearman(y_true, y_pred):
    """Spearman rank correlation with average ranks for ties.

    Returns None when either vector is constant (correlation undefined).
    """
    _check_pairs(y_true, y_pred)
    n = len(y_true)
    if n < 2:
        return None
    rx = _average_ranks([float(v) for v in y_true])
    ry = _average_ranks([float(v) for v in y_pred])
    mean_x = sum(rx) / n
    mean_y = sum(ry) / n
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry))
    var_x = sum((a - mean_x) ** 2 for a in rx)
    var_y = sum((b - mean_y) ** 2 for b in ry)
    if var_x == 0.0 or var_y == 0.0:
        return None
    return cov / math.sqrt(var_x * var_y)


METRIC_FUNCS = {
    "AUROC": auroc,
    "AUPRC": average_precision,
    "AP": average_precision,
    "MAE": mae,
    "Spearman": spearman,
}