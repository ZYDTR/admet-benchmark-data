# monitor-mae-e2e-20261101

Science is independently accepted,15 epochs/75 updates,raw-MAE selected epoch7. Worker0 and supervisor/OS125 are separate facts. Missing VmRSS was reported for PID1297236; fault-time stat/status was not saved. Root cause is unknown, including whether Z-state behavior explains this instance. No relaunch, lock cleanup or new learning is authorized.

Current MAE 0.40302117308791197 vs existing prior MSE-monitor 0.42147216141758237. Inputs/split/initial head match,raw features differ by at most2.384185791015625e-7. This single pair does not attribute causality solely to monitor.

Read complete current originals/projections:

- [actual-config](../../runs/hainan-mae-monitor-20261101/source/config.json)
- [actual-science-interface](../../runs/hainan-mae-monitor-20261101/source/training_science.py)
- [actual-science-implementation](../../runs/hainan-mae-monitor-20261101/source/train_remote_v4.py)
- [encoder](../../runs/hainan-mae-monitor-20261101/encoder.py)
- [blind-predictions](../../runs/hainan-mae-monitor-20261101/artifacts/predictions.csv)
- [train-internal-predictions](../../runs/hainan-mae-monitor-20261101/artifacts/train-predictions.csv)
- [full-training-process](../../runs/hainan-mae-monitor-20261101/artifacts/training-evidence.json)
- [internal-split](../../runs/hainan-mae-monitor-20261101/artifacts/internal-split.json)
- [worker-complete](../../runs/hainan-mae-monitor-20261101/raw/attempt-01/train/adapter-complete.json)
- [supervisor125](../../runs/hainan-mae-monitor-20261101/raw/attempt-01/train/status.json)
- [pipeline125](../../runs/hainan-mae-monitor-20261101/raw/attempt-01/pipeline-exit.json)
- [actual-os-exit125](../../runs/hainan-mae-monitor-20261101/raw/job-wait-exit.json)
- [freeze-before](../../runs/hainan-mae-monitor-20261101/artifacts/encoder-before.json)
- [freeze-after](../../runs/hainan-mae-monitor-20261101/artifacts/encoder-after.json)
- [full-own-process-events](../../runs/hainan-mae-monitor-20261101/raw/attempt-01/train/events.jsonl)
- [main-science-acceptance](../../evidence/main-acceptance/report.md.txt)
- [main-score-acceptance](../../evidence/main-scoring-acceptance.json)
- [current-score](aggregate-scores.json)
- [score-provenance](scoring-summary.json)
- [monitor-comparison](monitor-comparison.json)
- [feature-comparison](feature-comparison.json)
- [curated-feedback](preparation-feedback.json)

[Delta](delta.json) · [coverage and missing records](coverage.json). Binary heads/state/cache are complete optional materials under the run artifacts; do not mark them original-read based on hash/summary. Main independently verified the score; candidate review, actual publication/readback and Pro reading/returns remain separate gates. Original score-time pending fields are historical and are superseded only by the separate main verification record.
