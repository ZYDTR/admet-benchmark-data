"""No-label diagnostics; prediction identity is checked before association."""
from __future__ import annotations

import math
from .common import InterfaceError
from .metrics import spearman


def checked_predictions(records, rows, task, split, parse_mask=None):
    if len(records) != len(rows):
        raise InterfaceError("diagnostic prediction row count mismatch")
    values = []
    for index, (pred, row) in enumerate(zip(records, rows)):
        expected = (task, split, str(index), row["Drug_ID"], row["Drug"])
        actual = tuple(str(pred.get(key, "")) for key in
                       ("task", "split", "row_index", "Drug_ID", "Drug"))
        if actual != expected:
            raise InterfaceError(f"diagnostic row identity mismatch at {index}")
        if parse_mask is not None:
            parsed = str(pred.get("parse_ok", "")).lower()
            if parsed not in ("true", "false") or (parsed == "true") != bool(parse_mask[index]):
                raise InterfaceError(f"diagnostic parse mask mismatch at {index}")
        value = float(pred["y_pred"])
        if not math.isfinite(value):
            raise InterfaceError("nonfinite diagnostic prediction")
        values.append(value)
    return values


def raw_statistics(features):
    import numpy as np
    x = np.asarray(features, dtype=np.float32)
    sd32 = x.std(axis=0, ddof=0)
    sd64 = x.astype(np.float64).std(axis=0, ddof=0)
    return {
        "raw_std32_min": float(sd32.min()),
        "raw_std64_min": float(sd64.min()),
        "exact_constant_dimensions": int(np.all(x == x[0], axis=0).sum()),
        "low_std32_dimensions": int((sd32 < 1e-8).sum()),
        "low_std64_dimensions": int((sd64 < 1e-8).sum()),
    }


def pearson(a, b):
    import numpy as np
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    if len(a) != len(b) or len(a) < 2 or not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise InterfaceError("invalid association inputs")
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def association(magnitude, prediction):
    import numpy as np
    m = np.asarray(magnitude, np.float64)
    p = np.asarray(prediction, np.float64)
    absolute = np.abs(p)
    deviation = np.abs(p - np.median(p))
    return {name: {"pearson": pearson(m, value),
                   "spearman_average_ranks": spearman(m.tolist(), value.tolist())}
            for name, value in [("prediction", p), ("absolute_prediction", absolute),
                                ("prediction_deviation_from_median", deviation)]}
