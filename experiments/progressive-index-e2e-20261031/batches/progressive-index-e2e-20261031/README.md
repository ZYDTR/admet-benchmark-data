# progressive-index-e2e-20261031

Accepted current run: hainan-index-cycle-20261031. V1 outer exit125 preserved; CUDA worker returned0 but outer monitor failed before learning. Missing VmRSS in a terminal process is a reproduced explanation; original failing PID/state was not captured, so it is not asserted as the unique on-site cause. V2 has the sole learning job, 26 epochs/130 updates. Actual terminal-state race fix was hit on the real run; active/unknown missing-field cases remain strict.

Read full originals in this order:

- [actual configuration](../../runs/hainan-index-cycle-20261031/source/config.json)
- [complete science implementation](../../runs/hainan-index-cycle-20261031/source/training_science.py)
- [independently retrieved encoder source](../../runs/hainan-index-cycle-20261031/encoder.py)
- [273 blind predictions](../../runs/hainan-index-cycle-20261031/artifacts/predictions.csv)
- [637 train/internal-stop predictions](../../runs/hainan-index-cycle-20261031/artifacts/train-predictions.csv)
- [full epoch/process/gradient/freeze evidence](../../runs/hainan-index-cycle-20261031/artifacts/training-evidence.json)
- [v1 failure status](../../runs/hainan-index-cycle-20261031/raw/preflight/status.json)
- [v1 pipeline original](../../runs/hainan-index-cycle-20261031/raw/pipeline-exit.json)
- [v2 pipeline original](../../runs/hainan-index-cycle-20261031/raw/attempt-v2/pipeline-exit.json)
- [full v2 own-process events](../../runs/hainan-index-cycle-20261031/raw/attempt-v2/train/events.jsonl)
- [single fixed-score result](aggregate-scores.json)
- [full role and phase timings](training-timing.json)

[delta](delta.json) · [current coverage and explicit limits](coverage-contract.json) · [all retrieval dispositions](../../public-dispositions.json)

Legacy_z preprocessing is retained as an explicit control. Reload evidence establishes saved-state roundtrip, not exact resumed trajectory. New score remains subject to controller independent acceptance. Public delivery and new Pro real reading have not occurred.
