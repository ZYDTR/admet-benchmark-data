"""Frozen per-task MLP head.

`build_head`/`make_optimizer`/`predict_logits` are the production torch path.
`build_np_head`/`np_forward`/`np_train_epoch` are a dependency-free NumPy mirror used only
by ``selftest_tiny.py`` to exercise the training/inference wiring without torch. The NumPy
weights are never written to the real checkpoint format; they use a separate small file.
"""

from __future__ import annotations

import numpy as np


def build_head(in_dim: int, out_dim: int, hidden_dims: list[int], dropout: float,
               seed: int):
    """Return a torch MLP module (out_dim=1).

    Structure is fixed: for each h in hidden_dims -> Linear, ReLU, (Dropout);
    then a final Linear(out_dim). Dropout is always included when dropout > 0 so the
    Sequential indices (and therefore state_dict keys) never depend on the flag value.
    """
    import torch
    from torch import nn

    torch.manual_seed(seed)
    layers: list[nn.Module] = []
    prev = in_dim
    for h in hidden_dims:
        layers += [nn.Linear(prev, h), nn.ReLU(), nn.Dropout(dropout)]
        prev = h
    layers.append(nn.Linear(prev, out_dim))
    return nn.Sequential(*layers)


def make_optimizer(model, lr: float, weight_decay: float):
    import torch

    return torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)


def predict_logits(model, X: np.ndarray, device: str, batch_size: int = 4096):
    import torch

    model.eval()
    out = []
    with torch.no_grad():
        for start in range(0, len(X), batch_size):
            xb = torch.as_tensor(X[start:start + batch_size], dtype=torch.float32,
                                 device=device)
            out.append(model(xb).detach().cpu().numpy())
    return np.concatenate(out, axis=0).reshape(-1)


# ---------------------------------------------------------------------------
# NumPy reference mirror (self-test only; single hidden layer, no dropout)
# ---------------------------------------------------------------------------

NP_INPUT_DIM = 16


def build_np_head(in_dim: int, hidden: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    return {
        "in_dim": int(in_dim),
        "W1": rng.normal(0, np.sqrt(2.0 / in_dim), (in_dim, hidden)).astype(np.float32),
        "b1": np.zeros(hidden, dtype=np.float32),
        "W2": rng.normal(0, np.sqrt(1.0 / hidden), (hidden, 1)).astype(np.float32),
        "b2": np.zeros(1, dtype=np.float32),
    }


def compress_features(X: np.ndarray, dim: int = NP_INPUT_DIM) -> np.ndarray:
    """Deterministic projection used only by the NumPy self-test to keep it CPU-cheap."""
    X = np.where(np.isfinite(X), X, 0.0).astype(np.float64)
    out = np.zeros((len(X), dim), dtype=np.float64)
    for j in range(len(X)):
        for i, v in enumerate(X[j]):
            out[j, i % dim] += v
    return (out / dim).astype(np.float32)


def np_forward(p: dict, X: np.ndarray) -> np.ndarray:
    H = np.maximum(X @ p["W1"] + p["b1"], 0.0)
    return (H @ p["W2"] + p["b2"]).reshape(-1)


def np_train_epoch(p: dict, X: np.ndarray, y: np.ndarray, kind: str, lr: float,
                   batch_size: int, rng: np.random.Generator) -> float:
    """One Adam-free SGD pass; returns mean loss. Training-free for production use."""
    n = len(X)
    perm = rng.permutation(n)
    loss_sum = 0.0
    for start in range(0, n, batch_size):
        sel = perm[start:start + batch_size]
        xb, yb = X[sel], y[sel]
        H = np.maximum(xb @ p["W1"] + p["b1"], 0.0)
        z = (H @ p["W2"] + p["b2"]).reshape(-1)
        if kind == "classification":
            prob = 1.0 / (1.0 + np.exp(-z))
            loss = float(np.mean(np.maximum(z, 0) - z * yb + np.log1p(np.exp(-np.abs(z)))))
            dz = (prob - yb) / len(sel)
        else:
            diff = z - yb
            loss = float(np.mean(diff ** 2))
            dz = (2.0 * diff / len(sel))
        dW2 = H.T @ dz.reshape(-1, 1)
        db2 = np.array([dz.sum()], dtype=np.float32)
        dH = dz.reshape(-1, 1) @ p["W2"].T
        dH[H <= 0] = 0.0
        dW1 = xb.T @ dH
        db1 = dH.sum(axis=0)
        p["W1"] -= lr * dW1
        p["b1"] -= lr * db1
        p["W2"] -= lr * dW2
        p["b2"] -= lr * db2
        loss_sum += loss * len(sel)
    return loss_sum / n