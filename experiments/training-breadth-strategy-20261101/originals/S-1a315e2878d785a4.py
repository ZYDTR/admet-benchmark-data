"""Frozen CheMeleon encoder adapter (Chemprop D-MPNN, descriptors-pretrained).

Mirrors the author's ``CheMeleonFingerprint`` (chemeleon_fingerprint.py @
b5e5bd88a7070c3f278e7e65e85b792617bf125c) with two deliberate changes required
by the task:

1. No implicit download. ``__init__`` takes an explicit weights path and verifies
   size+MD5(+locked SHA256) *before* loading. Loading uses
   ``torch.load(..., map_location="cpu", weights_only=True)`` (restricted format).
2. No silent featurization loss. ``encode_smiles`` returns
   ``(features, failures)`` where ``features`` is an ``(n_ok, D)`` float32 array
   aligned to the *kept* row indices supplied, and ``failures`` lists every
   dropped row as ``{row_index, smiles, error}``.  The caller (feature cache) is
   responsible for persisting them and refusing silent truncation.

The featurizer is ``SimpleMoleculeMolGraphFeaturizer`` (Chemprop default =
``MultiHotAtomFeaturizer.v2`` + ``MultiHotBondFeaturizer``), the same one used by
the author script. Element coverage is fixed by the frozen checkpoint
(atomic numbers 1-36 + 53); any other element maps to the "unknown" bucket, which
does not raise but loses information. We do not change featurizer settings.

Everything here is inference-only: parameters are frozen, ``eval()`` is set, and
all calls run under ``torch.no_grad()``.
"""

import numpy as np

DEFAULT_BATCH_SIZE = 128


class EncoderUnavailable(RuntimeError):
    """Raised when torch/chemprop/rdkit are not importable in this environment."""


def _imports():
    try:
        import torch  # noqa: F401
        from chemprop import featurizers, nn
        from chemprop.data import BatchMolGraph
        from chemprop.models import MPNN
        from chemprop.nn import RegressionFFN
        from rdkit import Chem
    except Exception as exc:  # pragma: no cover - depends on environment
        raise EncoderUnavailable(f"cannot import torch/chemprop/rdkit: {exc!r}") from exc
    return torch, featurizers, nn, BatchMolGraph, MPNN, RegressionFFN, Chem


class FrozenCheMeleonEncoder:
    def __init__(self, weights_path, device="cpu", expected_sha256=None):
        self.device_arg = device
        self.weights_path = weights_path
        self.expected_sha256 = expected_sha256
        torch, featurizers, nn, BatchMolGraph, MPNN, RegressionFFN, Chem = _imports()
        metadata = self._precheck(weights_path, expected_sha256)
        self.weight_metadata = metadata
        ckpt = torch.load(weights_path, map_location="cpu", weights_only=True)
        if not isinstance(ckpt, dict) or "hyper_parameters" not in ckpt or "state_dict" not in ckpt:
            raise ValueError(f"{weights_path}: unexpected checkpoint layout")
        mp = nn.BondMessagePassing(**ckpt["hyper_parameters"])
        mp.load_state_dict(ckpt["state_dict"], strict=True)
        model = MPNN(
            message_passing=mp,
            agg=nn.MeanAggregation(),
            predictor=RegressionFFN(input_dim=mp.output_dim),
        )
        for p in model.parameters():
            p.requires_grad_(False)
        model.eval()
        self.torch = torch
        self.featurizer = featurizers.SimpleMoleculeMolGraphFeaturizer()
        self.BatchMolGraph = BatchMolGraph
        self.Chem = Chem
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.feature_dim = int(mp.output_dim)
        self.hyper_parameters = dict(ckpt["hyper_parameters"])

    @staticmethod
    def _precheck(path, expected_sha256):
        from assets import verify_weights_file

        return verify_weights_file(path, expected_sha256)

    def _parse(self, smiles):
        mol = self.Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, "rdkit MolFromSmiles returned None"
        if mol.GetNumAtoms() == 0:
            return None, "molecule has zero atoms"
        return mol, None

    def encode_smiles(self, smiles, row_indices=None, batch_size=DEFAULT_BATCH_SIZE):
        """Encode SMILES to frozen graph descriptors.

        Parameters
        ----------
        smiles : list[str]
        row_indices : list[int] | None
            Original ``row_index`` for each SMILES; defaults to ``0..n-1``.
            Returned features align to the *non-failed* subset of these.
        batch_size : int

        Returns
        -------
        features : np.ndarray  (n_ok, feature_dim), float32
        kept_row_indices : list[int]
        failures : list[dict]
        """
        if row_indices is None:
            row_indices = list(range(len(smiles)))
        if len(row_indices) != len(smiles):
            raise ValueError("row_indices and smiles length differ")
        mols, kept, failures = [], [], []
        for ridx, smi in zip(row_indices, smiles):
            mol, err = self._parse(smi)
            if mol is None:
                failures.append({"row_index": int(ridx), "smiles": smi, "error": err})
            else:
                mols.append(mol)
                kept.append(int(ridx))
        chunks = []
        with self.torch.no_grad():
            for start in range(0, len(mols), batch_size):
                batch = mols[start:start + batch_size]
                bmg = self.BatchMolGraph([self.featurizer(m) for m in batch])
                bmg.to(device=self.device)
                fp = self.model.fingerprint(bmg)
                chunks.append(fp.detach().cpu().numpy().astype(np.float32, copy=False))
        if chunks:
            features = np.concatenate(chunks, axis=0)
        else:
            features = np.zeros((0, self.feature_dim), dtype=np.float32)
        if features.shape != (len(kept), self.feature_dim):
            raise RuntimeError(
                f"encoder produced {features.shape}, expected ({len(kept)}, {self.feature_dim})"
            )
        return features, kept, failures