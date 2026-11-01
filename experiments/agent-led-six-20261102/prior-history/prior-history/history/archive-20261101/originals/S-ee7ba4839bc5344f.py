"""Per-task small MLP head, fixed v1 training configuration, checkpoint IO.

The head is a plain PyTorch MLP consuming frozen CheMeleon fingerprints. It is
small on purpose (~2.2e5 parameters at dim=300) and every task gets its own
independently initialized and trained head: this is representation reuse, not
multi-task learning.

FIXED CONFIGURATION (v1) - no search, per the task brief. Changing any value
below is a new experiment, not a tuning step inside this run.

    hidden_sizes = (512, 128)
    dropout      = 0.1
    epochs       = 100
    batch_size   = 256
    optimizer    = AdamW(lr=1e-3, weight_decay=1e-4)
    loss         = classification: BCEWithLogitsLoss(pos_weight=n_neg/n_pos)
                   regression:  SmoothL1Loss(beta=1.0) on train-z-scored Y
    seed         = 42

Only train rows of the task are used for fitting (input standardization, Y
standardization, pos_weight). The blind validation split has no labels and is
never read by training. There is no early stopping and no label-based model
selection: the model saved is the state after the last fixed epoch.

Checkpoint format (single .pt per task, torch.save of a plain dict with only
tensors and primitives so torch.load(weights_only=True) works):

    format, task, kind, d_in, head_config, state_dict,
    input_mean (tensor), input_std (tensor), y_mean (float), y_std (float),
    pos_weight (float or None), n_train_rows, n_train_fallback_rows,
    final_train_loss, features_identity (cache binding), versions
"""

from __future__ import annotations

import torch
from torch import nn

HEAD_FORMAT = "chemeleon-baseline-head-v1"

HEAD_CONFIG = {
    "hidden_sizes": [512, 128],
    "dropout": 0.1,
    "epochs": 100,
    "batch_size": 256,
    "lr": 1e-3,
    "weight_decay": 1e-4,
    "seed": 42,
    "loss": "BCEWithLogits(pos_weight=n_neg/n_pos) | SmoothL1(beta=1.0) on z-scored Y",
}


class MLPHead(nn.Module):
    """Linear(d_in->512) ReLU Dropout Linear(512->128) ReLU Dropout Linear(128->1)."""

    def __init__(self, d_in: int, hidden_sizes: tuple[int, ...] = (512, 128), dropout: float = 0.1):
        super().__init__()
        layers: list[nn.Module] = []
        d = int(d_in)
        for h in hidden_sizes:
            layers += [nn.Linear(d, int(h)), nn.ReLU(), nn.Dropout(dropout)]
            d = int(h)
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)

    def n_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters())


def stable_sigmoid_np(logits: "np.ndarray") -> "np.ndarray":
    """Numerically stable sigmoid on numpy arrays (no scipy)."""
    import numpy as np

    out = np.empty_like(logits, dtype=np.float64)
    pos = logits >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-logits[pos]))
    e = np.exp(logits[~pos])
    out[~pos] = e / (1.0 + e)
    return out


def load_head(path, device: str = "cpu") -> tuple[MLPHead, dict]:
    """Load a head checkpoint: returns (eval-mode head on device, metadata dict).

    The checkpoint is loaded to CPU first (so meta["input_mean"]/["input_std"]
    stay CPU tensors that can be converted to numpy); only the head module is
    then moved to the requested device.
    """
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    if ckpt.get("format") != HEAD_FORMAT:
        raise ValueError(f"{path}: unexpected checkpoint format {ckpt.get('format')!r}")
    head = MLPHead(int(ckpt["d_in"]), tuple(ckpt["head_config"]["hidden_sizes"]), float(ckpt["head_config"]["dropout"]))
    head.load_state_dict(ckpt["state_dict"])
    head.to(device)
    head.eval()
    meta = {k: v for k, v in ckpt.items() if k != "state_dict"}
    return head, meta
