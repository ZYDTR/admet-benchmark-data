"""Array abstraction: uses NumPy when present, else a minimal stdlib fallback.

Both backends expose ``shape``, ``dtype``, ``all_finite()``, ``[i, j]`` indexing,
and a ``save``/``load`` pair.  The on-disk format for the fallback is ``.npyf``
(raw little-endian float32 + a JSON sidecar), and the format name is written into
the cache manifest so a NumPy-written cache is never silently read by the fallback
(or vice versa).  This is for the prep checks only; real runs use NumPy.
"""

import json
import os

try:  # pragma: no cover - depends on environment
    import numpy as _np

    HAS_NUMPY = True
except Exception:  # pragma: no cover
    _np = None
    HAS_NUMPY = False

from mini_linalg import FeatureArray as _Fallback


class Array:
    def __init__(self, obj):
        self.obj = obj

    @property
    def shape(self):
        return tuple(int(x) for x in (self.obj.shape if HAS_NUMPY else self.obj.shape))

    @property
    def dtype(self):
        if HAS_NUMPY:
            return str(self.obj.dtype)
        return self.obj.dtype

    def all_finite(self):
        return bool(_np.all(_np.isfinite(self.obj))) if HAS_NUMPY else self.obj.all_finite()

    def __getitem__(self, idx):
        return self.obj[idx] if HAS_NUMPY else self.obj[idx]

    def __setitem__(self, idx, val):
        if HAS_NUMPY:
            self.obj[idx] = val
        else:
            self.obj[idx] = val

    def zeros(self, n_rows, n_cols):
        if HAS_NUMPY:
            return Array(_np.zeros((n_rows, n_cols), dtype=_np.float32))
        return Array(_Fallback.zeros(n_rows, n_cols))

    def astype_f32(self):
        if HAS_NUMPY:
            return Array(_np.asarray(self.obj, dtype=_np.float32))
        return Array(_Fallback(self.obj.to_rows(), self.obj.shape[1]))

    # ---- persistence -------------------------------------------------------
    def save(self, path):
        """Save; writes ``path`` (+ sidecar ``path + '.json'`` for the fallback)."""
        if HAS_NUMPY:
            _np.save(path, _np.asarray(self.obj, dtype=_np.float32), allow_pickle=False)
            return "npy"
        with open(path, "wb") as fh:
            fh.write(self.obj._data_bytes() if hasattr(self.obj, "_data_bytes")
                     else _pack(self.obj))
        with open(path + ".json", "w", encoding="utf-8") as fh:
            json.dump({"format": "npyf", "shape": list(self.obj.shape)}, fh)
        return "npyf"

    def load(self, path):
        if HAS_NUMPY:
            arr = _np.load(path, allow_pickle=False)
            self.obj = arr
            return self
        sidecar = path + ".json"
        if not os.path.isfile(sidecar):
            raise ValueError(f"missing fallback sidecar {sidecar}")
        with open(sidecar, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        n_rows, n_cols = meta["shape"]
        with open(path, "rb") as fh:
            blob = fh.read()
        from mini_linalg import unpack_f32

        self.obj = unpack_f32(blob, n_rows, n_cols)
        return self


def _pack(arr):
    from mini_linalg import pack_f32

    return pack_f32(arr)


def zeros(n_rows, n_cols):
    if HAS_NUMPY:
        return Array(_np.zeros((n_rows, n_cols), dtype=_np.float32))
    return Array(_Fallback.zeros(n_rows, n_cols))


def synthetic(n_rows, n_cols, seed=0):
    if HAS_NUMPY:
        rng = _np.random.default_rng(seed)
        return Array(rng.standard_normal((n_rows, n_cols)).astype(_np.float32))
    from mini_linalg import synthetic_matrix

    return Array(synthetic_matrix(n_rows, n_cols, seed))


def same(a, b):
    """Compare two Array values with exact equality."""
    if HAS_NUMPY:
        return bool(_np.array_equal(a.obj, b.obj))
    return a.obj._data == b.obj._data


def format_name():
    return "npy" if HAS_NUMPY else "npyf"