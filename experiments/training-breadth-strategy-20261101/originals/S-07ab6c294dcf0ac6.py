"""Dependency-free numeric fallbacks (Python standard library only).

Used *only* when ``numpy`` is unavailable, so that the pure-Python parts of the
pipeline (cache validation, metric checks, scaler arithmetic) can still be
exercised in a bare interpreter for the prep-session checks.  Every algorithm here
is deliberately simple and auditable:

* ``FeatureArray`` — a minimal 2-D float32 array with shape/dtype/order,
  ``all_finite()`` and ``[i, j]`` indexing.  It is NOT a NumPy replacement and is
  only produced/consumed by the fallback cache path (``allow_pickle.py`` files
  written by ``npy_shim``).
* ``mean`` / ``pstd`` / ``abs_diff_mean`` — descriptive statistics.
* ``corr_of_ranks`` — Spearman via mid-rank Pearson.

The operator environment will use NumPy for real feature arrays; these helpers
exist so the review checks do not silently become "unverified" purely because a
package is missing.
"""

import math
import struct


class FeatureArray:
    __slots__ = ("_data", "shape", "dtype")

    def __init__(self, rows, n_cols, dtype="float32"):
        """``rows`` is a list of lists (or flat list) of Python floats."""
        flat = []
        for r in rows:
            if isinstance(r, (list, tuple)):
                if len(r) != n_cols:
                    raise ValueError("row width mismatch")
                flat.extend(float(x) for x in r)
            else:
                flat.append(float(r))
        if len(flat) != len(rows) * n_cols:
            raise ValueError(f"flat length {len(flat)} != {len(rows)}x{n_cols}")
        self._data = flat
        self.shape = (len(rows), n_cols)
        self.dtype = dtype

    @classmethod
    def zeros(cls, n_rows, n_cols, dtype="float32"):
        return cls([[0.0] * n_cols for _ in range(n_rows)], n_cols, dtype)

    def __getitem__(self, idx):
        i, j = idx
        return self._data[i * self.shape[1] + j]

    def __setitem__(self, idx, val):
        i, j = idx
        self._data[i * self.shape[1] + j] = float(val)

    def all_finite(self):
        return all(math.isfinite(v) for v in self._data)

    def to_rows(self):
        n_cols = self.shape[1]
        return [self._data[i * n_cols:(i + 1) * n_cols] for i in range(self.shape[0])]


def mean(xs):
    xs = [float(x) for x in xs]
    if not xs:
        raise ValueError("mean of empty sequence")
    return sum(xs) / len(xs)


def pstd(xs):
    xs = [float(x) for x in xs]
    m = mean(xs) if xs else 0.0
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)) if xs else 0.0


def abs_diff_mean(a, b):
    if len(a) != len(b):
        raise ValueError("length mismatch")
    if not a:
        raise ValueError("empty input")
    return sum(abs(float(x) - float(y)) for x, y in zip(a, b)) / len(a)


def _midranks(xs):
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def corr_of_ranks(a, b):
    if len(a) != len(b) or len(a) < 2:
        raise ValueError("need >=2 paired samples")
    ra, rb = _midranks([float(x) for x in a]), _midranks([float(x) for x in b])
    ma, mb = mean(ra), mean(rb)
    sa = math.sqrt(sum((x - ma) ** 2 for x in ra))
    sb = math.sqrt(sum((x - mb) ** 2 for x in rb))
    if sa == 0 or sb == 0:
        raise ZeroDivisionError("constant vector")
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    return cov / (sa * sb)


def _rand(seed):
    """Deterministic Lehmer-style PRNG for synthetic fixtures (stdlib only)."""
    state = [seed % 2147483647 or 1]

    def nxt():
        state[0] = (state[0] * 48271) % 2147483647
        return state[0] / 2147483647.0

    return nxt


def synthetic_matrix(n_rows, n_cols, seed=0, dtype="float32"):
    nxt = _rand(seed + 12345)
    return FeatureArray(
        [[nxt() * 2.0 - 1.0 for _ in range(n_cols)] for _ in range(n_rows)], n_cols, dtype
    )


def pack_f32(arr):
    return struct.pack(f"<{len(arr._data)}f", *arr._data)


def unpack_f32(blob, n_rows, n_cols):
    n = n_rows * n_cols
    vals = struct.unpack(f"<{n}f", blob)
    return FeatureArray([list(vals[i * n_cols:(i + 1) * n_cols]) for i in range(n_rows)],
                        n_cols)