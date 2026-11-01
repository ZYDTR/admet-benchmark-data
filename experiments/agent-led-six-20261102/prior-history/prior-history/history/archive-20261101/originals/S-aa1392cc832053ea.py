"""Explicit failure types for the frozen-CheMeleon ADMET pipeline.

Every contract violation raises one of these instead of silently dropping,
overwriting, or intersecting rows.
"""


class ContractError(Exception):
    """Base class for all data/asset/cache contract violations."""


class InputContractError(ContractError):
    """Input CSV header, split, task, or row identity is not what the task requires."""


class LabelError(ContractError):
    """Label column missing, non-numeric, or non-finite where labels are required."""


class FeaturizationError(ContractError):
    """A SMILES could not be parsed/featurized; carries the exact row identities."""

    def __init__(self, message, failures=None):
        super().__init__(message)
        self.failures = list(failures or [])


class CacheError(ContractError):
    """Cache manifest missing, mismatched, corrupted, or not bound to the requested identity."""


class ScoringError(ContractError):
    """Prediction/product file violates the key set, coverage, or value rules."""


class UndefinedMetric(ContractError):
    """A metric is mathematically undefined for the given labels (recorded, not imputed)."""