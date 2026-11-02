"""End-to-end orchestration API for one task: load -> split -> cache -> train(host)
-> predict -> export. Import-safe; nothing executes on import.

The host drives real training by calling ``TaskPipeline.fit_head`` (which wraps
trainer.train_head with preparation=False). In the preparation session use
``preparation=True`` paths only: data, identity, split, cache validation, scaler
fitting on synthetic/official-train statistics, head construction and serialization
checks — never parameter updates.

Scaler-aware additions (six28 prep):
  * ``configure(cfg)`` binds a validated run configuration to the pipeline; the
    feature-scaler policy is consumed by ``fit_transforms`` and re-checked at
    every transform application, so changing the scaler config after fitting
    invalidates the cached transform instead of silently reusing old statistics.
  * ``load_cache`` accepts legacy v1 entries only through explicit migration
    verification (see migration.py); representation identity stays separate from
    the per-split transform identity.
"""

from __future__ import annotations

import math
import copy
from pathlib import Path
from typing import Any, Mapping, Sequence

from .common import (CLASSIFICATION_TASKS, CHEMELEON_SHA256, FEATURE_DIM,
                     InterfaceError, TASKS, sha256_file, task_kind, write_json)
from .cache import (LEGACY_METHOD, build_raw_cache, fill_raw, fit_feature_scaler,
                    fit_target_scaler, load_raw_cache, validate_scaler_config)
from .data_io import (load_split_table, split_train_stop_groups, train_labels)
from .heads import build_head, load_head, make_loss, make_optimizer, postprocess, save_head
from .metrics import EarlyStopMonitor, METRIC_FUNCS, load_task_metrics
from .predictions_io import export_submission, write_predictions_csv
from .trainer import train_head, validate_config


class TaskPipeline:
    """One task's production interface bundle. All file outputs live under work_root."""

    def __init__(self, task: str, data_root: Path | str, work_root: Path | str,
                 metrics_contract: Path | str, *,
                 allow_migrated_legacy_cache: bool = False,
                 migration_evidence_dir: Path | str | None = None,
                 cache_trust=None, raw_cache_root: Path | str | None = None):
        if task not in TASKS:
            raise InterfaceError(f"unknown task: {task!r}")
        self.task = task
        self.kind = task_kind(task)
        self.data_root = Path(data_root)
        self.work_root = Path(work_root)
        self.metrics_contract_path = Path(metrics_contract)
        self.task_metrics = load_task_metrics(self.metrics_contract_path)
        self.metrics = self.task_metrics[task]
        self.rows: dict[str, list[dict[str, str]]] = {}
        self.source_sha: dict[str, str] = {}
        self.split_record: dict[str, Any] | None = None
        self.scaler = None
        self.target_scaler = None
        self.transform_identity = None
        self.config: dict[str, Any] | None = None
        self.scaler_policy: dict[str, Any] | None = None
        self.cache_trust = cache_trust
        self.raw_cache_root = Path(raw_cache_root) if raw_cache_root is not None else None
        self.allow_migrated_legacy_cache = bool(allow_migrated_legacy_cache)
        self.migration_evidence_dir = (Path(migration_evidence_dir)
                                        if migration_evidence_dir else
                                        self.work_root / "migration-evidence")
        self.migration_evidence: dict[str, Any] = {}

    # ---- run configuration -------------------------------------------------
    def configure(self, cfg: Mapping[str, Any]) -> dict[str, Any]:
        """Validate and bind one run configuration; its feature_scaler field is
        the policy actually consumed downstream (never an unconsumed key)."""
        merged = copy.deepcopy(dict(cfg))
        merged.setdefault("task", self.task)
        merged.setdefault("kind", self.kind)
        cfgv = validate_config(merged, self.task_metrics)
        if cfgv["task"] != self.task or cfgv["kind"] != self.kind:
            raise InterfaceError("configuration task does not match pipeline")
        self.config = cfgv
        self.scaler_policy = validate_scaler_config(cfgv.get("feature_scaler"))
        if self.scaler_policy is None:
            self.scaler_policy = validate_scaler_config({"method": LEGACY_METHOD})
        # Rebinding a config invalidates any previously fitted transform whose
        # identity no longer matches. A same-policy rebind keeps the transform
        # usable (the training entry re-binds the run config after fitting).
        if self.transform_identity is not None:
            prev = self.transform_identity
            still_valid = (prev[2] == self.scaler_policy["method"]
                           and prev[3] == self.scaler_policy["denominator_floor"])
            if not still_valid:
                self.transform_identity = None
                self.scaler = None
                self.target_scaler = None
        return cfgv

    def _require_config(self):
        if self.config is None:
            # Legacy transform-only callers never needed a training config.
            # Actual training still validates the complete config in fit_head.
            self.scaler_policy = validate_scaler_config({"method": LEGACY_METHOD})

    # ---- data & identity ---------------------------------------------------
    def load(self) -> dict[str, int]:
        counts = {}
        for split in ("train", "valid", "test"):
            rows = load_split_table(self.data_root, self.task, split)
            self.rows[split] = rows
            self.source_sha[split] = sha256_file(self.data_root / self.task / f"{split}.csv")
            counts[split] = len(rows)
        return counts

    def make_internal_split(self, seed: int = 43, stop_fraction: float = 0.1) -> dict[str, Any]:
        rec = split_train_stop_groups(self.rows["train"], seed=seed,
                                      validation_fraction=stop_fraction)
        self.split_record = rec
        return rec

    # ---- raw cache -------------------------------------------------------
    def cache_dir(self) -> Path:
        return self.raw_cache_root if self.raw_cache_root is not None else self.work_root / "cache" / "chemeleon_mp"

    def build_cache(self, embedder) -> dict[str, Any]:
        out = {}
        for split in ("train", "valid", "test"):
            meta = build_raw_cache(embedder, self.task, split, self.rows[split],
                                   self.source_sha[split], self.cache_dir())
            out[split] = {"contract_row_identity": meta["contract"]["row_identity_sha256"],
                          "features_sha256": meta["identity"]["features"]["sha256"],
                          "parsed_true_count": meta["identity"]["parsed_true_count"]}
        return out

    def load_cache(self, split: str):
        X, ok = load_raw_cache(self.cache_dir(), self.task, split,
                               self.rows[split], self.source_sha[split],
                               allow_migrated_legacy=self.allow_migrated_legacy_cache,
                               cache_trust=self.cache_trust)
        if self.allow_migrated_legacy_cache:
            from .migration import verify_legacy_migration
            ev_p = self.migration_evidence_dir / f"{self.task}_{split}.json"
            self.migration_evidence[split] = verify_legacy_migration(
                self.cache_dir(), self.task, split, self.rows[split],
                self.source_sha[split], evidence_path=ev_p, cache_trust=self.cache_trust)
        return X, ok

    # ---- fit-only transforms --------------------------------------------
    def _checked_split(self):
        if self.split_record is None:
            raise InterfaceError("make_internal_split must precede transforms/training")
        expected = split_train_stop_groups(
            self.rows["train"], seed=self.split_record["seed"],
            validation_fraction=self.split_record["validation_fraction"])
        if self.split_record != expected:
            raise InterfaceError("split record differs from actual train rows and split identity")
        return expected

    def fit_transforms(self):
        """Load the identity-checked full train cache, then select fit rows here.

        No caller-supplied matrix: a fit-row hash cannot prove that an arbitrary
        matrix excludes stop rows. Refit after changing the train input/split.
        The scaler policy comes from the bound configuration and is embedded in
        the fitted transform's identity.
        """
        self._require_config()
        rec = self._checked_split()
        X_train, _ = self.load_cache("train")
        idx = rec["fit_row_indices"]
        self.scaler = fit_feature_scaler(X_train[idx], idx, self.scaler_policy)
        self.transform_identity = (self.source_sha["train"], rec["split_record_sha256"],
                                  self.scaler_policy["method"],
                                  self.scaler_policy["denominator_floor"])
        if self.kind == "regression":
            y = train_labels(self.rows["train"], self.task)
            idx = self.split_record["fit_row_indices"]
            self.target_scaler = fit_target_scaler([y[i] for i in idx])
        else:
            self.target_scaler = None
        return {"feature_scaler": {k: v for k, v in self.scaler.to_dict().items()
                                   if k not in ("mean", "std", "denominators_pre_floor")},
                "target_scaler": None if self.target_scaler is None else self.target_scaler.to_dict()}

    def _scaled(self, X):
        """Apply the fitted transform ONLY when its identity matches the current
        train source, split record and configured scaler policy."""
        if self.scaler is None or self.transform_identity is None:
            raise InterfaceError("transforms absent: call fit_transforms first")
        self._checked_split()
        want = (self.source_sha["train"], self.split_record["split_record_sha256"],
                self.scaler_policy["method"], self.scaler_policy["denominator_floor"])
        if self.transform_identity != want:
            raise InterfaceError("fitted transform stale for current train/split/scaler "
                                 "configuration — refit required")
        self.scaler.assert_matches_config(self.config.get("feature_scaler")
                                          if self.config else None)
        return self.scaler.apply(fill_raw(X))

    # ---- head (construction is update-free) ------------------------------
    def new_head(self, hidden_dim: int, dropout: float, seed: int):
        model = build_head(FEATURE_DIM, hidden_dim, dropout, seed)
        return model

    def monitor(self) -> EarlyStopMonitor:
        return EarlyStopMonitor(self.metrics["metric"], self.metrics["direction"])

    def loss_fn(self):
        return make_loss(self.kind)

    # ---- training entry (host-only) --------------------------------------
    def fit_head(self, cfg: Mapping[str, Any], device: str, *, preparation: bool = True, checkpoint_callback=None):
        """Authorized training entry. preparation=True refuses to update parameters."""
        if preparation:
            from .trainer import TrainingUnavailableInPreparation
            raise TrainingUnavailableInPreparation(
                "fit_head(preparation=True) never updates parameters; host calls with "
                "preparation=False during authorized training runs")
        self.configure(cfg)
        rec = self._checked_split()
        if (cfg["split"]["seed"] != rec["seed"]
                or cfg["split"]["stop_fraction"] != rec["validation_fraction"]):
            raise InterfaceError("configuration split differs from actual split")
        X_tr, ok_tr = self.load_cache("train")
        Xs = self._scaled(X_tr)
        fit_idx = self.split_record["fit_row_indices"]
        stop_idx = self.split_record["stop_row_indices"]
        y_all = train_labels(self.rows["train"], self.task)
        import numpy as np
        if self.kind == "classification":
            y_fit = np.asarray(y_all, dtype=np.float32)[fit_idx]
            y_stop_eval = np.asarray(y_all, dtype=np.float64)[stop_idx]
        else:
            y_fit = self.target_scaler.transform_f32(np.asarray(y_all, dtype=np.float64)[fit_idx])
            y_stop_eval = np.asarray(y_all, dtype=np.float64)[stop_idx]
        model, result = train_head(
            preparation=False,
            X_fit=Xs[fit_idx], y_fit=y_fit,
            X_stop=Xs[stop_idx], y_stop=y_stop_eval,
            cfg=self.config, task_metrics=self.task_metrics, device=device, monitor=self.monitor(),
            target_scaler=self.target_scaler, stop_row_indices=stop_idx, checkpoint_callback=checkpoint_callback)
        return model, result

    # ---- prediction -------------------------------------------------------
    def predict_split(self, model, split: str, device: str):
        X, ok = self.load_cache(split)
        Xs = self._scaled(X)
        from .heads import forward_logits
        z = forward_logits(model, Xs, device)
        y = postprocess(self.kind, z, self.target_scaler)
        records = [{"task": self.task, "split": split, "row_index": i, "y_pred": float(v)}
                   for i, v in enumerate(y)]
        return records

    def export_test(self, records: Sequence[Mapping[str, Any]], template_path: Path | str,
                    out_path: Path | str, fixture: bool = False) -> dict[str, Any]:
        return export_submission(template_path, records, out_path, fixture=fixture)
