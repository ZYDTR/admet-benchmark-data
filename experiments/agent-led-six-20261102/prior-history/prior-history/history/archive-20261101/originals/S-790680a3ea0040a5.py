"""Skill-style metric helpers: only for *synthetic* checks in this prep session.

The blind valid/test files carry no labels, so nothing here is run against real
labels during preparation.  The functions exist so the training/eval code and the
refusal paths can be reviewed and exercised on fixed synthetic numerics.

Rules:

* Classification metrics return ``{"defined": False, "reason": ...}`` for empty
  input or single-class labels (AP/AUROC undefined), never a fabricated number.
* MAE is defined for any non-empty finite input; empty raises.
* Spearman for a constant vector is undefined (zero variance) -> explicit record.

No labels are invented for real rows anywhere.  Uses NumPy when available and a
stdlib fallback otherwise (same mid-rank formulas).
"""

import math

try:  # pragma: no cover - depends on environment
    import numpy as np
except Exception:  # pragma: no cover
    np = None
    import mini_linalg as _ml


def _flatten(xs):
    if np is not None:
        return np.asarray(xs, dtype=np.float64).reshape(-1).tolist()
    return [float(x) for x in xs]


def _check_finite(name, vals):
    out = _flatten(vals)
    for v in out:
        if not math.isfinite(v):
            raise ValueError(f"{name} contains non-finite values")
    return out


def _ap(y_true, scores):
    """Average precision (step-wise, sklearn ``average_precision_score`` style)."""
    order = sorted(range(len(scores)), key=lambda i: -scores[i])  # stable sort
    y = [y_true[i] for i in order]
    tp = fp = 0
    ap = 0.0
    n_pos = sum(1 for v in y if v == 1)
    if n_pos == 0:
        return None
    for v in y:
        if v == 1:
            tp += 1
            ap += tp / (tp + fp)
        else:
            fp += 1
    return ap / n_pos


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _auroc(y_true, scores):
    """Rank-based AUROC (Mann-Whitney U with mid-ranks for ties)."""
    n_pos = sum(1 for v in y_true if v == 1)
    n_neg = sum(1 for v in y_true if v == 0)
    if n_pos == 0 or n_neg == 0:
        return None
    ranks = _ranks(scores)
    rank_sum_pos = sum(r for r, v in zip(ranks, y_true) if v == 1)
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def spearman(y_true, y_pred):
    yt = _check_finite("y_true", y_true)
    yp = _check_finite("y_pred", y_pred)
    if len(yt) != len(yp):
        raise ValueError("length mismatch")
    if len(yt) < 2:
        return {"defined": False, "reason": "fewer than 2 samples"}
    rt, rp = _ranks(yt), _ranks(yp)
    mt = sum(rt) / len(rt)
    mp = sum(rp) / len(rp)
    ct = sum((r - mt) ** 2 for r in rt)
    cp = sum((r - mp) ** 2 for r in rp)
    if ct == 0 or cp == 0:
        return {"defined": False, "reason": "constant vector has zero variance"}
    cov = sum((a - mt) * (b - mp) for a, b in zip(rt, rp))
    return {"defined": True, "value": cov / math.sqrt(ct * cp)}


def mae(y_true, y_pred):
    yt = _check_finite("y_true", y_true)
    yp = _check_finite("y_pred", y_pred)
    if len(yt) != len(yp):
        raise ValueError("length mismatch")
    if len(yt) == 0:
        raise ValueError("empty input")
    return {"defined": True, "value": sum(abs(a - b) for a, b in zip(yt, yp)) / len(yt)}


def classification(metric, y_true, scores):
    yt = _check_finite("y_true", y_true)
    sc = _check_finite("scores", scores)
    if len(yt) != len(sc):
        raise ValueError("length mismatch")
    if len(yt) == 0:
        return {"defined": False, "metric": metric, "reason": "empty input"}
    classes = sorted(set(yt))
    if not set(classes) <= {0.0, 1.0}:
        return {"defined": False, "metric": metric,
                "reason": f"labels not binary: {classes}"}
    if len(classes) < 2:
        return {"defined": False, "metric": metric, "reason": "single class present"}
    if metric == "AUROC":
        return {"defined": True, "metric": metric, "value": _auroc([int(v) for v in yt], sc)}
    if metric == "AUPRC":
        return {"defined": True, "metric": metric, "value": _ap([int(v) for v in yt], sc)}
    raise ValueError(f"unsupported classification metric {metric!r}")


def score(metric, y_true, y_pred):
    if metric in ("AUROC", "AUPRC"):
        return classification(metric, y_true, y_pred)
    if metric == "MAE":
        return {"defined": True, "metric": "MAE", **mae(y_true, y_pred)}
    if metric == "Spearman":
        r = spearman(y_true, y_pred)
        return {"metric": "Spearman", **r}
    raise ValueError(f"unsupported metric {metric!r}")


def check_finite_or_raise(vals, name="values"):
    for v in vals:
        if not math.isfinite(float(v)):
            raise ValueError(f"{name}: non-finite value {v!r}")
    return True