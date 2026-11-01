"""Frozen CheMeleon encoder (D-MPNN message passing, publisher weights).

This is a faithful re-implementation of the publisher's chemeleon_fingerprint.py
at commit b5e5bd88a7070c3f278e7e65e85b792617bf125c (MIT license,
https://github.com/JacksonBurns/chemeleon). Two deliberate changes only:

1. The weights file must be passed explicitly as a local path. The publisher's
   automatic download (urlretrieve into ~/.chemprop) is removed so that the
   exact reviewed asset is always used.
2. The frozen state is enforced and is externally verifiable: all parameters
   get requires_grad_(False), the module stays in eval mode, every fingerprint
   call runs under torch.no_grad(), and parameter_digest() gives a SHA-256 over
   the message-passing state so any caller can prove the weights did not change
   across a run.

The predictor head constructed below is a randomly initialized placeholder
required by chemprop's MPNN container. It is never used by fingerprint(): the
official code marks it the same way. The digest therefore covers only
self.mp (the actual CheMeleon checkpoint content).

Requires: chemprop>=2.2.0 (2.2.1 pinned in requirements.txt), torch, rdkit.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import torch

PUBLISHER_ASSET = {
    "name": "CheMeleon Foundation Model",
    "record": "https://zenodo.org/records/15460715",
    "api": "https://zenodo.org/api/records/15460715",
    "download_url": "https://zenodo.org/records/15460715/files/chemeleon_mp.pt",
    "doi": "10.5281/zenodo.15460715",
    "file": "chemeleon_mp.pt",
    "size_bytes": 34_859_448,
    "md5": "6a80b54fdb7de37ef0374d302f01e8ce",
    "license": "MIT (metadata.license.id = 'mit-license' on the Zenodo record)",
    "publication_date": "2025-05-18",
    "code_commit": "b5e5bd88a7070c3f278e7e65e85b792617bf125c",
    "code_entry": "chemeleon_fingerprint.py",
    "sha256_publisher": None,  # publisher publishes MD5 only; SHA-256 is computed locally after download
}


def file_hashes(path: str | Path) -> dict:
    path = Path(path)
    md5 = hashlib.md5()
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            md5.update(chunk)
            sha.update(chunk)
    return {
        "size_bytes": path.stat().st_size,
        "md5": md5.hexdigest(),
        "sha256": sha.hexdigest(),
    }


class CheMeleonFrozen:
    """Load and query the frozen CheMeleon message-passing encoder."""

    def __init__(self, weights_path: str | Path, device: str = "cpu"):
        weights_path = Path(weights_path)
        if not weights_path.is_file():
            raise FileNotFoundError(
                f"weights file not found: {weights_path}. Download it explicitly from "
                f"{PUBLISHER_ASSET['download_url']} (see HANDOFF.md); this code never downloads."
            )
        self.weights_hashes = file_hashes(weights_path)
        if self.weights_hashes["size_bytes"] != PUBLISHER_ASSET["size_bytes"]:
            raise ValueError(
                f"{weights_path}: size {self.weights_hashes['size_bytes']} != publisher "
                f"{PUBLISHER_ASSET['size_bytes']}"
            )
        if self.weights_hashes["md5"] != PUBLISHER_ASSET["md5"]:
            raise ValueError(
                f"{weights_path}: MD5 {self.weights_hashes['md5']} != publisher "
                f"{PUBLISHER_ASSET['md5']}"
            )

        # Imports kept inside __init__ so stdlib-only callers can import this
        # module's metadata without a chemprop installation.
        from chemprop import featurizers, nn
        from chemprop.data import BatchMolGraph
        from chemprop.models import MPNN
        from chemprop.nn import RegressionFFN

        self.featurizer = featurizers.SimpleMoleculeMolGraphFeaturizer()
        self._BatchMolGraph = BatchMolGraph

        ckpt = torch.load(weights_path, weights_only=True)
        self.mp = nn.BondMessagePassing(**ckpt["hyper_parameters"])
        self.mp.load_state_dict(ckpt["state_dict"])  # strict=True: load must be complete
        self.model = MPNN(
            message_passing=self.mp,
            agg=nn.MeanAggregation(),
            predictor=RegressionFFN(input_dim=self.mp.output_dim),  # placeholder, never used
        )
        self.model.eval()
        self.model.requires_grad_(False)
        self.model.to(device=torch.device(device))
        self.fingerprint_dim = int(self.mp.output_dim)
        self.assert_frozen()

    def assert_frozen(self) -> None:
        """Raise if any parameter could still receive updates or gradients."""
        for name, p in self.model.named_parameters():
            if p.requires_grad:
                raise RuntimeError(f"encoder parameter {name} has requires_grad=True")
            if p.grad is not None:
                raise RuntimeError(f"encoder parameter {name} has a gradient")

    def parameter_digest(self) -> str:
        """SHA-256 over the message-passing state (keys + tensor bytes).

        Compare this value before/after any run to prove the frozen encoder was
        not modified. Tensor order is canonicalized by sorting state_dict keys.
        """
        h = hashlib.sha256()
        sd = self.mp.state_dict()
        for key in sorted(sd):
            t = sd[key].detach().to("cpu").contiguous()
            h.update(key.encode("utf-8"))
            h.update(str(tuple(t.shape)).encode("utf-8"))
            h.update(str(t.dtype).encode("utf-8"))
            h.update(t.numpy().tobytes())
        return h.hexdigest()

    def featurize(self, mol) -> object:
        """RDKit Mol -> chemprop MolGraph (publisher default featurizer)."""
        return self.featurizer(mol)

    def fingerprint_graphs(self, graphs: list) -> np.ndarray:
        """MolGraph list -> (n, fingerprint_dim) float32 numpy array.

        graph list must be non-empty. Runs in eval mode under no_grad.
        """
        if not graphs:
            raise ValueError("fingerprint_graphs called with an empty list")
        bmg = self._BatchMolGraph(graphs)
        bmg.to(device=self.model.device)
        with torch.no_grad():
            out = self.model.fingerprint(bmg)
        return out.detach().to("cpu").numpy().astype(np.float32, copy=False)

    def fingerprints(self, molecules: list) -> np.ndarray:
        """Publisher-equivalent convenience path: RDKit Mols -> fingerprints.

        Parse failures (MolFromSmiles -> None) raise here; production callers
        should use featurize()/fingerprint_graphs() with per-molecule error
        handling (see features.py).
        """
        graphs = [self.featurizer(m) for m in molecules]
        return self.fingerprint_graphs(graphs)
