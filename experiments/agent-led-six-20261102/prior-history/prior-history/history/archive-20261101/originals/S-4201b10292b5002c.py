"""Local metric implementations for per-task scoring.

Definitions fixed for this project (local; the official competition
implementation and total-score aggregation are unconfirmed):
- AUROC: tie-aware P(score_pos > score_neg) + 0.5 * P(score_pos == score_neg).
- AUPRC: average precision with the step definition
  sum_k (R_k - R_{k-1}) * P_k over distinct score thresholds
  (the sklearn average_precision_score convention, not the trapezoid variant).
- MAE: mean absolute error on the supplied Y scale.
- Spearman: Pearson correlation of mid-rank (average) ranks.

Every function returns (value, reason). value is None when the metric is
undefined for the inputs, with an explicit reason. ValueError is raised on
contract violations (length mismatch, non-finite values, non-binary labels
where binary labels are required).
"""
from __future__ import annotations

import math


def _pairs(y_true, y_score):
    if len(y_true) != len(y_score):
        raise ValueError('length mismatch: %d true vs %d pred' % (len(y_true), len(y_score)))
    out = []
    for t, s in zip(y_true, y_score):
        t = float(t)
        s = float(s)
        if not math.isfinite(t) or not math.isfinite(s):
            raise ValueError('non-finite input value')
        out.append((s, t))
    return out


def _binary_counts(pairs):
    n_pos = 0
    n_neg = 0
    for _s, t in pairs:
        if t == 1.0:
            n_pos += 1
        elif t == 0.0:
            n_neg += 1
        else:
            raise ValueError('non-binary label %r; classification tasks require Y in {0,1}' % (t,))
    return n_pos, n_neg


def auroc(y_true, y_score):
    pairs = _pairs(y_true, y_score)
    n_pos, n_neg = _binary_counts(pairs)
    if n_pos == 0 or n_neg == 0:
        return None, 'undefined: AUROC requires both classes (n_pos=%d, n_neg=%d)' % (n_pos, n_neg)
    pairs.sort()
    n = len(pairs)
    total = 0.0
    cum_neg = 0
    i = 0
    while i < n:
        j = i
        s0 = pairs[i][0]
        while j < n and pairs[j][0] == s0:
            j += 1
        grp_pos = 0
        for _s, t in pairs[i:j]:
            if t == 1.0:
                grp_pos += 1
        grp_neg = (j - i) - grp_pos
        total += grp_pos * cum_neg + 0.5 * grp_pos * grp_neg
        cum_neg += grp_neg
        i = j
    return total / (n_pos * n_neg), None


def average_precision(y_true, y_score):
    pairs = _pairs(y_true, y_score)
    n_pos, _n_neg = _binary_counts(pairs)
    if n_pos == 0:
        return None, 'undefined: AUPRC (local AP) requires at least one positive label'
    pairs.sort(key=lambda p: (-p[0], p[1]))
    n = len(pairs)
    ap = 0.0
    prev_recall = 0.0
    tp = 0
    fp = 0
    i = 0
    while i < n:
        j = i
        s0 = pairs[i][0]
        while j < n and pairs[j][0] == s0:
            j += 1
        for _s, t in pairs[i:j]:
            if t == 1.0:
                tp += 1
            else:
                fp += 1
        recall = tp / n_pos
        precision = tp / (tp + fp)
        ap += (recall - prev_recall) * precision
        prev_recall = recall
        i = j
    return ap, None


def mae(y_true, y_pred):
    pairs = _pairs(y_true, y_pred)
    n = len(pairs)
    if n == 0:
        return None, 'undefined: no samples'
    total = 0.0
    for s, t in pairs:
        total += abs(t - s)
    return total / n, None


def midranks(values):
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        v = values[order[i]]
        while j < n and values[order[j]] == v:
            j += 1
        mid = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = mid
        i = j
    return ranks


def spearman(x, y):
    if len(x) != len(y):
        raise ValueError('length mismatch: %d vs %d' % (len(x), len(y)))
    n = len(x)
    if n < 2:
        return None, 'undefined: n<2'
    xf = []
    yf = []
    for a, b in zip(x, y):
        a = float(a)
        b = float(b)
        if not (math.isfinite(a) and math.isfinite(b)):
            raise ValueError('non-finite input value')
        xf.append(a)
        yf.append(b)
    rx = midranks(xf)
    ry = midranks(yf)
    mx = sum(rx) / n
    my = sum(ry) / n
    cov = 0.0
    vx = 0.0
    vy = 0.0
    for a, b in zip(rx, ry):
        da = a - mx
        db = b - my
        cov += da * db
        vx += da * da
        vy += db * db
    if vx == 0.0 or vy == 0.0:
        return None, 'undefined: zero rank variance (constant input)'
    return cov / math.sqrt(vx * vy), None


KNOWN_METRICS = ('AUROC', 'AUPRC', 'MAE', 'Spearman')


def compute_metric(metric, y_true, y_pred):
    if metric == 'AUROC':
        return auroc(y_true, y_pred)
    if metric == 'AUPRC':
        return average_precision(y_true, y_pred)
    if metric == 'MAE':
        return mae(y_true, y_pred)
    if metric == 'Spearman':
        return spearman(y_true, y_pred)
    raise ValueError('unknown metric %r (known: %s)' % (metric, list(KNOWN_METRICS)))
