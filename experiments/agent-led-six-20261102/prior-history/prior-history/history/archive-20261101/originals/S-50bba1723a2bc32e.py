"""Per-task small MLP head on top of frozen CheMeleon features.

The encoder is *never* imported for gradients here: this module only consumes the
float32 feature matrix produced by ``feature_cache``/``chemeleon_encoder``.  It is
kept deliberately separable so that ``train_heads.py`` can be reviewed and run
without touching the graph model, and so that a head can be loaded/evaluated with
only torch.

Regression targets are z-scored with train statistics and predictions are
inverse-transformed back to the original Y scale before they leave this module.
"""

import json
import math
import os

try:  # pragma: no cover
    import numpy as np
except Exception:  # pragma: no cover
    np = None

# Reference "small MLP" configuration (frozen for the first version; no search).
HEAD_CONFIG = {
    "hidden_dim": 256,
    "num_layers": 1,          # 1 hidden layer + output layer
    "dropout": 0.1,
    "activation": "relu",
    "optimizer": "adamw",
    "lr": 1e-3,
    "weight_decay": 1e-4,
    "batch_size": 64,
    "max_epochs": 200,
    "early_stopping_patience": 20,
    "early_stopping_metric": "val_loss",  # on the *train-internal* holdout, never blind valid
    "seed": 0,
}


def _torch():
    import torch

    return torch


def build_head(input_dim, task_kind, cfg=None):
    """Construct the MLP: ``in -> hidden -> out`` with dropout + activation."""
    torch = _torch()
    cfg = dict(HEAD_CONFIG if cfg is None else cfg)
    if task_kind not in ("classification", "regression"):
        raise ValueError(f"unknown task_kind {task_kind!r}")
    act = {"relu": torch.nn.ReLU, "gelu": torch.nn.GELU}[cfg["activation"]]
    layers = []
    d = input_dim
    for _ in range(int(cfg["num_layers"])):
        layers += [torch.nn.Linear(d, cfg["hidden_dim"]), act(), torch.nn.Dropout(cfg["dropout"])]
        d = cfg["hidden_dim"]
    out_dim = 1
    layers.append(torch.nn.Linear(d, out_dim))
    head = torch.nn.Sequential(*layers)
    return head, out_dim, cfg


class TargetScaler:
    """Per-task target standardisation fitted ONLY on the train table."""

    def __init__(self, mean, std):
        self.mean = float(mean)
        self.std = float(std)

    @classmethod
    def fit(cls, y):
        vals = [float(v) for v in y]
        if not vals:
            raise ValueError("cannot fit scaler on empty labels")
        mean = sum(vals) / len(vals)
        std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
        if not (math.isfinite(mean) and math.isfinite(std)):
            raise ValueError("non-finite scaler statistics")
        if std == 0.0:
            std = 1.0  # constant target: identity, no variance inflation
        return cls(mean, std)

    def transform(self, y):
        if np is not None:
            return (np.asarray(y, dtype=np.float64) - self.mean) / self.std
        return [(float(v) - self.mean) / self.std for v in y]

    def inverse(self, z):
        if np is not None:
            return np.asarray(z, dtype=np.float64) * self.std + self.mean
        return [float(v) * self.std + self.mean for v in z]

    def to_dict(self):
        return {"mean": self.mean, "std": self.std}

    @classmethod
    def from_dict(cls, d):
        return cls(d["mean"], d["std"])


def save_head(head, path, task, task_kind, scaler, header_params, extra=None):
    """Save a head to a single restricted-format ``torch.save`` file.

    ``header_params`` should capture every fixed head/optimiser/training choice
    so the artifact is self-describing.  ``extra`` carries non-portable
    provenance (input digest, cache key, encoder digest) recorded as metadata.
    """
    torch = _torch()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    payload = {
        "task": task,
        "task_kind": task_kind,
        "state_dict": {k: v.detach().cpu() for k, v in head.state_dict().items()},
        "scaler": scaler.to_dict() if scaler is not None else None,
        "head_params": header_params,
        "header": HEAD_CONFIG if not header_params else header_params,
        "extra": extra or {},
    }
    torch.save(payload, path)


def load_head(path, expect_task=None):
    """Load a head with ``weights_only=True`` and return ``(head, payload)``."""
    torch = _torch()
    if not os.path.isfile(path):
        raise FileNotFoundError(f"head artifact not found: {path}")
    payload = torch.load(path, map_location="cpu", weights_only=True)
    for key in ("task", "task_kind", "state_dict", "head_params"):
        if key not in payload:
            raise ValueError(f"{path}: missing {key!r}")
    if expect_task is not None and payload["task"] != expect_task:
        raise ValueError(f"{path}: task {payload['task']!r} != expected {expect_task!r}")
    params = payload["head_params"]
    input_dim = _infer_input_dim(payload["state_dict"])
    head, _, _ = build_head(input_dim, payload["task_kind"], params)
    head.load_state_dict(payload["state_dict"], strict=True)
    head.eval()
    scaler = TargetScaler.from_dict(payload["scaler"]) if payload.get("scaler") else None
    return head, {"task": payload["task"], "task_kind": payload["task_kind"],
                  "scaler": scaler, "params": params, "extra": payload.get("extra", {})}


def _infer_input_dim(state_dict):
    for name, tensor in state_dict.items():
        if name.endswith("weight") and tensor.ndim == 2:
            return int(tensor.shape[1])
    raise ValueError("cannot infer input dim from state dict")


def predict(head, features, task_kind, scaler=None):
    """Forward pass in eval mode; regression output is de-standardised to Y scale."""
    torch = _torch()
    head.eval()
    import numpy as _np

    with torch.no_grad():
        tensor = torch.as_tensor(_np.asarray(features, dtype=_np.float32))
        raw = head(tensor).numpy(force=True)
    raw = raw.reshape(-1)
    if task_kind == "regression":
        if scaler is None:
            raise ValueError("regression head requires its fitted scaler")
        return scaler.inverse(raw)
    # classification: return the single logit (probabilities computed at export)
    return raw


def export_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2, sort_keys=True)