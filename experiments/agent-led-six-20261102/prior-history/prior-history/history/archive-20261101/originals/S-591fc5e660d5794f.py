"""CheMeleon frozen-encoder + per-task small MLP head baseline (preparation only).

Prepared by the A-path leaf session on 2026-10-30. All training and full-batch
feature computation is executed by the main Codex session; this package only
provides the runnable code, the asset/dependency list, and non-training
self-checks. See ../HANDOFF.md and ../README.md.

Subcommands (run from output/model/):

    python -m chemeleon_baseline.features  --weights <chemeleon_mp.pt> --out <dir> ...
    python -m chemeleon_baseline.train     --features <dir> --out <dir> ...
    python -m chemeleon_baseline.predict   --features <dir> --heads <dir> --out <dir> ...
    python -m chemeleon_baseline.selfcheck {data|cache|encoder|artifacts} ...

Shared conventions:
- Row identity is (task, split, row_index); row_index is the 0-based position of
  the CSV data row (header excluded). Rows are never dropped, merged, or reordered.
- Prediction files contain exactly the columns: task, split, row_index, y_pred.
- The CheMeleon encoder is frozen end-to-end: explicit local weights, verified
  publisher size+MD5, requires_grad_(False), eval mode, torch.no_grad() on every
  call, and a parameter digest recorded for before/after comparison.
- Any fitted transform (input standardization, Y standardization, fallback mean
  vector) is fitted on train rows of the selected tasks only.
"""

__version__ = "1.0.0"
