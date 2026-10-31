# Comparison limits and recorded gaps

Both runs use the same 637 original train rows, 91 blind valid and 182 blind test inputs and the same frozen CheMeleon asset/hash. Both use 2048-wide features, a single new hidden head, dropout 0.1, Adam weight decay 0.0001, batch 128, patience 8 and an internal 573/64 split. Head width, learning rate AND random seed differ, and the random seed also changes the internal validation partition. This is a confounded two-run comparison; an observed score difference cannot be assigned to width or LR alone and two seeds do not establish uncertainty or statistical superiority. Internal standardized-MSE curves use different internal samples and fitted target transforms, so their raw values are not directly interchangeable across runs.

These fixed official-valid scores are analysis/model-selection feedback, not an independent final generalization certificate. No official all-task aggregate is calculated. No new configuration, inference, training, HPO or test scoring was performed.

Existing scientific material includes full executed scientific/runtime source, exact inputs, disjoint internal split/normalization arrays, both initial and best heads, all existing cached features/parse masks, all 273-row blind predictions, epoch curves, aggregate gradient/update evidence, frozen before/after state hashes, runtime logs and resource series. Per-batch loss/gradient/LR time series, train predictions, per-epoch/last-unselected heads, optimizer moment checkpoints and full RNG snapshots were not recorded by the original writer. Seeds and split indices are retained; no missing record was regenerated.

Fresh follow run current source inventory is complete and stable. Frozen run uses 51 accepted local original files (65,619,331 bytes), not a new remote inventory; no claim is made that its entire current remote root or later caches were rechecked. The external backbone is referenced by original source and SHA. Current 78-package environment metadata is a dated current snapshot with matching historical metadata/interpretation hashes, not a copied full venv or proof that all implementation files equal the training-time bytes.

Historical follow-run training artifacts passed independent training-delivery checks, but strict Skill compliance failed: an environment check failed and deployment/preflight continued before that gate was properly enforced. The full historical scientific acceptance is included. This trial does not repair or retroactively relabel that execution. Other known historical issues include previously unhealthy GPU candidates and a joblib shared-memory side effect in an older failed run; those were identified before the successful fixed configurations and are not evidence of new training here. NVIDIA driver device-link unlink attempts were denied, not silently absent.

Full syscall traces are preserved locally by their SHA but excluded from the public packet because they expose infrastructure/process/file context. Independent audit summaries and scientifically relevant failures are included. The public packet is a declared derivative evidence package, not every raw byte of the local archive. No claim is made that Chat read binary tensors, unlinked raw traces or the full dependency image.

Local scoring attempt 1 stopped before any metric call because the wrapper's projection recreation defaulted to CRLF whereas the original blind input uses LF. Original hash and ordered row checks stayed in force. The LF writer convention was restored and both runs were scored once. No input or prediction bytes were modified, and the failed attempt remains local.

| Run | Hidden width | LR | Seed / internal split | Epochs / best / steps | Official-valid MAE (lower) |
|---|---:|---:|---:|---|---:|
| hainan-frozen-training-20261031 | 512 | 0.001 | 42 | 14 / 6 / 70 | 0.378625135989 |
| hainan-skill-follow-20261031 | 256 | 0.0005 | 43 | 19 / 11 / 95 | 0.389188593978 |
