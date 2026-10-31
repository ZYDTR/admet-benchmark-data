# Fixed Caco2 official-valid result

| Run | Hidden width | LR | Seed / internal split | Epochs / best / steps | Official-valid MAE (lower) |
|---|---:|---:|---:|---|---:|
| hainan-frozen-training-20261031 | 512 | 0.001 | 42 | 14 / 6 / 70 | 0.378625135989 |
| hainan-skill-follow-20261031 | 256 | 0.0005 | 43 | 19 / 11 / 95 | 0.389188593978 |

91/91 valid identities per run passed. No truth/residual rows are included. Metric is the exact reviewed host MAE function; independent controller Decimal50 recomputation passed. See comparison.md for confounding, original record gaps and valid reuse limits.

Independent verification: [controller check](independent-controller-check.json). The first 22 synthetic checks preceded first authorized truth access; repeated selector checks in attempt 2 preceded that attempt only, after the failed newline precheck already read the authorized truth.
