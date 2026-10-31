# Caco2 frozen-CheMeleon two-run analysis evidence

Candidate packet for experiments/public-repo-20261031 in ZYDTR/admet-benchmark-data. It has not been pushed. Controller review must bind the exact local candidate manifest before publication. All future links must use the resulting immutable commit, not a mutable branch.

Start with ANALYSIS_BUNDLE.md, comparison.md, rules/CURRENT_RULES.md and scoring/validation-report.md. The bundle embeds the complete scientific training/encoder code, effective rules, score table and epoch curves. Read individual files for complete full-size numeric transforms, predictions, detailed logs, current metadata and source dispositions. manifest.json hashes all other public files. source-map.json accounts for original material by published/redacted/referenced/excluded status. A summary is not a claim to have read unlinked originals.

No private original-valid copy, labeled score records or row residuals are included. Scores and aggregate diagnostics are deliberately public under user authorization. Preparation/training roles must not read this analysis feedback; public access itself provides no technical secrecy. Do not execute pickle, torch.load, native libraries or model code when reviewing. Use binary-structure.json for model/NPZ structure; binary heads/features are evidence assets, not required to execute.

Rules hierarchy and confounding are explicit. This is two fixed completed runs, not a new sweep or a 22-task submission. Publication uploaded/read-back phases and Chat actual-read status remain unmeasured until the respective roles finish them.

## Effective rules

# Applicable rules and source hierarchy

Official source: http://www.aiinnovation.com.cn/web/#/trackDetail?id=159 . The archived official snapshot was verified 2026-10-29 and says it was updated 2026-10-26. No new live rule verification or competition submission is performed in this publication trial.

The snapshot official R01–R10 remain the evidence for external-data restriction, deep-learning training and model-generated predictions, submission template/format, reproducibility review and participation/open-source licensing. Valid-based tuning is allowed by the official text. Numeric Y is the current learning/scoring target; its physical unit and biological transformation are not fully confirmed.

Current user-confirmed exception: external pretrained weights may be used while remaining frozen. This comes from the user's reported organizer confirmation, not from an invented quotation of the archived web page. Keep requires_grad false, eval/no-grad, optimizer exclusion, and before/after parameter AND buffer identity evidence. New heads may train. Frozen permission does not automatically admit external fitted normalization, teacher labels, extra samples, or test fitting.

Current local role boundary: training/preparation receive train Y plus blind valid/test; this designated retrieval role scores only registered official-valid rows locally with a fixed MAE implementation. Analysis receives declared scores/aggregate diagnostics. Preparation/training must not read the public analysis scores, private labels or row residuals. Public publishing is not technical secrecy. The retrieval, publication and training-execution roles do not receive permission for new training, HPO, external labels, official uploads, service operations or agent/thread/CLI-model delegation. The user explicitly authorizes the independent analysis Chat Pro to use its own subagents for read-only research and cross-checks; this is an analysis-role exception, not permission to train, access servers, score new data, publish or delegate execution. Retrieval/publication still remain single leaf executors.

Historical snapshot T03 random initialization, local Docker/SAP/fixed-image restrictions and old no-scoring/private-only defaults are historical executor choices; they are not current competition rules. The pretrained-weight part of old U02 is resolved only by user confirmation; other external fitted assets, official global aggregation, exact AUPRC convention and reproduction tolerance remain unresolved. The raw snapshot and old source-map wording are retained with this override rather than retroactively changed.

## Fixed results and comparison limits

| Run | Hidden width | LR | Seed / internal split | Epochs / best / steps | Official-valid MAE (lower) |
|---|---:|---:|---:|---|---:|
| hainan-frozen-training-20261031 | 512 | 0.001 | 42 | 14 / 6 / 70 | 0.378625135989 |
| hainan-skill-follow-20261031 | 256 | 0.0005 | 43 | 19 / 11 / 95 | 0.389188593978 |

# Comparison limits and recorded gaps

Both runs use the same 637 original train rows, 91 blind valid and 182 blind test inputs and the same frozen CheMeleon asset/hash. Both use 2048-wide features, a single new hidden head, dropout 0.1, Adam weight decay 0.0001, batch 128, patience 8 and an internal 573/64 split. Head width, learning rate AND random seed differ, and the random seed also changes the internal validation partition. This is a confounded two-run comparison; an observed score difference cannot be assigned to width or LR alone and two seeds do not establish uncertainty or statistical superiority. Internal standardized-MSE curves use different internal samples and fitted target transforms, so their raw values are not directly interchangeable across runs.

These fixed official-valid scores are analysis/model-selection feedback, not an independent final generalization certificate. No official all-task aggregate is calculated. No new configuration, inference, training, HPO or test scoring was performed.

Existing scientific material includes full executed scientific/runtime source, exact inputs, disjoint internal split/normalization arrays, both initial and best heads, all existing cached features/parse masks, all 273-row blind predictions, epoch curves, aggregate gradient/update evidence, frozen before/after state hashes, runtime logs and resource series. Per-batch loss/gradient/LR time series, train predictions, per-epoch/last-unselected heads, optimizer moment checkpoints and full RNG snapshots were not recorded by the original writer. Seeds and split indices are retained; no missing record was regenerated.

Fresh follow run current source inventory is complete and stable. Frozen run uses 51 accepted local original files (65,619,331 bytes), not a new remote inventory; no claim is made that its entire current remote root or later caches were rechecked. The external backbone is referenced by original source and SHA. Current 78-package environment metadata is a dated current snapshot with matching historical metadata/interpretation hashes, not a copied full venv or proof that all implementation files equal the training-time bytes.

Historical follow-run training artifacts passed independent training-delivery checks, but strict Skill compliance failed: an environment check failed and deployment/preflight continued before that gate was properly enforced. The full historical scientific acceptance is included. This trial does not repair or retroactively relabel that execution. Other known historical issues include previously unhealthy GPU candidates and a joblib shared-memory side effect in an older failed run; those were identified before the successful fixed configurations and are not evidence of new training here. NVIDIA driver device-link unlink attempts were denied, not silently absent.

Full syscall traces are preserved locally by their SHA but excluded from the public packet because they expose infrastructure/process/file context. Independent audit summaries and scientifically relevant failures are included. The public packet is a declared derivative evidence package, not every raw byte of the local archive. No claim is made that Chat read binary tensors, unlinked raw traces or the full dependency image.

Local scoring attempt 1 stopped before any metric call because the wrapper's projection recreation defaulted to CRLF whereas the original blind input uses LF. Original hash and ordered row checks stayed in force. The LF writer convention was restored and both runs were scored once. No input or prediction bytes were modified, and the failed attempt remains local.

## Approved public input provenance

```json
{
  "repository": "ZYDTR/admet-benchmark-data",
  "commit": "0275588ac7a5d3df032ec7dc0794cab21dfcfeeb",
  "repository_url": "https://github.com/ZYDTR/admet-benchmark-data/tree/0275588ac7a5d3df032ec7dc0794cab21dfcfeeb",
  "train_url": "https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/0275588ac7a5d3df032ec7dc0794cab21dfcfeeb/data_benchmark/caco2_wang/train.csv",
  "test_url": "https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/0275588ac7a5d3df032ec7dc0794cab21dfcfeeb/data_benchmark/caco2_wang/test.csv",
  "note": "The user already published this dataset. This experiment packet includes exact train and blind valid/test inputs. It does not include its private original-valid copy or labeled scoring work files."
}
```

## Fixed scoring identity and aggregate diagnostics

```json
{
  "task": "caco2_wang",
  "split": "official_valid",
  "rows": 91,
  "metric": "MAE",
  "direction": "minimize",
  "truth_sha256": "63328bf307b850a4a0986165d0800bae5aa737c41bd63f1026d16114d8560bb4",
  "blind_projection_sha256": "41370e87d89a96a7481425dae1bf7c45184bd116b353e96719b2afcd0a8a5ca3",
  "source_scorer_sha256": "c94fa86659ec5ed33edb5b5a5b6526f860bde80055dd3c047d2e6169fd541c76",
  "fixed_mae_sha256": "6c8a2b4be4a9d4a1258a70f7f7e56789478a86faef0e407946e00af5fad3ee22",
  "strict_wrapper_sha256": "6410d987eb602f6258fe5a0f22a1f569c80ebc49aa54ef9f8cc8bd65e699cdda",
  "function": "evaluation._mae exact AST excerpt",
  "allowed_public_fields": [
    "run_id",
    "task",
    "split",
    "n",
    "metric",
    "direction",
    "value",
    "status",
    "definition",
    "diagnostic_aggregates",
    "prediction_sha256",
    "valid_selection_sha256",
    "truth_sha256",
    "blind_projection_sha256",
    "scorer_sha256"
  ],
  "scoring_calls_per_run": 1,
  "prior_host_scoring_history": "Not globally audited; this trial performs one call per run. Valid score is not an untouched final generalization test.",
  "runs": [
    {
      "run_id": "hainan-frozen-training-20261031",
      "prediction_sha256": "e674439f83d55a17703e2a0d59bc3142874b4ad956d9f6fbb7a3377b40675993",
      "valid_selection_sha256": "06381ae71dcbb13801a024366cb62c0a76b24d2dee0247c6b79fdded3eb5b2c8",
      "primary_input_rows": 273,
      "scored_rows": 91,
      "score_call_seconds": 0.000249625
    },
    {
      "run_id": "hainan-skill-follow-20261031",
      "prediction_sha256": "aa33ca53bc0e1570aba6cf6d4ec1e82f41e126dc0fd57715cd52c32d2ee29bfb",
      "valid_selection_sha256": "c9296e72863f65952d11b1554776cf81986ca3c52f7f5271b69e34d667efd8c6",
      "primary_input_rows": 273,
      "scored_rows": 91,
      "score_call_seconds": 0.000233875
    }
  ]
}
```

```json
{
  "task": "caco2_wang",
  "split": "official_valid",
  "scores": [
    {
      "task": "caco2_wang",
      "split": "official_valid",
      "n": 91,
      "metric": "MAE",
      "direction": "minimize",
      "value": 0.37862513598901104,
      "status": "ok",
      "definition": "mean(abs(supplied_numeric_Y - y_pred))",
      "official_aggregate_score": null,
      "diagnostic_aggregates": {
        "rmse": 0.523504782149424,
        "signed_mean_error": -0.0265676674835165,
        "median_absolute_error": 0.29335550700000024,
        "p90_absolute_error": 0.6765756839999986,
        "p95_absolute_error": 0.9585247319999999,
        "absolute_error_bin_counts": {
          "lt_0.25": 38,
          "0.25_to_lt_0.5": 29,
          "0.5_to_lt_1": 20,
          "ge_1": 4
        }
      },
      "run_id": "hainan-frozen-training-20261031",
      "prediction_sha256": "e674439f83d55a17703e2a0d59bc3142874b4ad956d9f6fbb7a3377b40675993",
      "valid_selection_sha256": "06381ae71dcbb13801a024366cb62c0a76b24d2dee0247c6b79fdded3eb5b2c8",
      "truth_sha256": "63328bf307b850a4a0986165d0800bae5aa737c41bd63f1026d16114d8560bb4",
      "blind_projection_sha256": "41370e87d89a96a7481425dae1bf7c45184bd116b353e96719b2afcd0a8a5ca3",
      "scorer_sha256": "6c8a2b4be4a9d4a1258a70f7f7e56789478a86faef0e407946e00af5fad3ee22"
    },
    {
      "task": "caco2_wang",
      "split": "official_valid",
      "n": 91,
      "metric": "MAE",
      "direction": "minimize",
      "value": 0.3891885939780218,
      "status": "ok",
      "definition": "mean(abs(supplied_numeric_Y - y_pred))",
      "official_aggregate_score": null,
      "diagnostic_aggregates": {
        "rmse": 0.5205062573960939,
        "signed_mean_error": 0.01051667096703301,
        "median_absolute_error": 0.31335976,
        "p90_absolute_error": 0.6993980689999999,
        "p95_absolute_error": 1.1308307859999998,
        "absolute_error_bin_counts": {
          "lt_0.25": 36,
          "0.25_to_lt_0.5": 30,
          "0.5_to_lt_1": 20,
          "ge_1": 5
        }
      },
      "run_id": "hainan-skill-follow-20261031",
      "prediction_sha256": "aa33ca53bc0e1570aba6cf6d4ec1e82f41e126dc0fd57715cd52c32d2ee29bfb",
      "valid_selection_sha256": "c9296e72863f65952d11b1554776cf81986ca3c52f7f5271b69e34d667efd8c6",
      "truth_sha256": "63328bf307b850a4a0986165d0800bae5aa737c41bd63f1026d16114d8560bb4",
      "blind_projection_sha256": "41370e87d89a96a7481425dae1bf7c45184bd116b353e96719b2afcd0a8a5ca3",
      "scorer_sha256": "6c8a2b4be4a9d4a1258a70f7f7e56789478a86faef0e407946e00af5fad3ee22"
    }
  ],
  "no_official_aggregate": true,
  "feedback_usage": "Public analysis aggregates only; no new tuning or training authorized."
}
```

## hainan-frozen-training-20261031


### hainan-frozen-training-20261031/source/config.json

```json
{
  "run_id": "hainan-frozen-training-20261031",
  "task": "caco2_wang",
  "head_config": {
    "hidden_dims": [
      512
    ],
    "dropout": 0.1,
    "lr": 0.001,
    "weight_decay": 0.0001,
    "batch_size": 128,
    "epochs": 50,
    "patience": 8,
    "val_fraction_from_train": 0.1,
    "seed": 42
  },
  "inputs": [
    {
      "role": "train",
      "task": "caco2_wang",
      "path": "input/train.csv",
      "sha256": "3061c58d3601d081e5459a2de03dc1d189243c4b5683d1b7288577a29fed4d6f",
      "rows": 637
    },
    {
      "role": "validation",
      "task": "caco2_wang",
      "path": "input/valid.csv",
      "sha256": "41370e87d89a96a7481425dae1bf7c45184bd116b353e96719b2afcd0a8a5ca3",
      "rows": 91
    },
    {
      "role": "test",
      "task": "caco2_wang",
      "path": "input/test.csv",
      "sha256": "d87dac944bedcefb216bce57ba5a8de93d3781172c66653b937e5065b9c2579c",
      "rows": 182
    }
  ],
  "pretrained_sha256": "c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651",
  "resource_budget": {
    "gpu_count": 1,
    "gpu_peak_target_mib": 4096,
    "cpu_threads": 2,
    "dataloader_workers": 0,
    "ram_target_gib": 8,
    "training_timeout_seconds": 900,
    "setup_budget_seconds": 2700,
    "dependency_download_budget_gib": 0,
    "result_budget_gib": 1,
    "limits_are_targets_until_enforcement_verified": true
  }
}

```

### hainan-frozen-training-20261031/learning-curve.csv

```csv
epoch,train_standardized_mse,internal_validation_standardized_mse,steps
1,1.1985344693298738,4.300019264221191,5
2,0.770889424320707,2.3230578899383545,10
3,0.41718955038937805,1.126440167427063,15
4,0.2465629292096143,1.2210471630096436,20
5,0.17993207840187178,1.3206332921981812,25
6,0.1322655007373184,0.9620532989501953,30
7,0.09957844280291603,1.0480252504348755,35
8,0.07209010981348381,1.466370940208435,40
9,0.06404326884742391,1.4176759719848633,45
10,0.05011763339813467,1.1557974815368652,50
11,0.04544707985812665,1.3395774364471436,55
12,0.03797432977257599,1.5515352487564087,60
13,0.03443480024267034,1.238293170928955,65
14,0.03283619697987513,1.1682392358779907,70

```

### hainan-frozen-training-20261031/artifacts/training-evidence.json

```json
{
  "started_at": "2026-10-30T16:48:43.477262+00:00",
  "completed_at": "2026-10-30T16:48:47.288324+00:00",
  "device": "cuda:0",
  "gpu_uuid": "<SELECTED_GPU_UUID>",
  "encoder_forward_events": [
    {
      "output_shapes": [
        [
          2128,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1944,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          2080,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          2096,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1738,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1908,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1936,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1382,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1646,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1549,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1931,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          860,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          2051,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1874,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1599,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    }
  ],
  "encoder_state_unchanged": true,
  "encoder_gradients_none": true,
  "encoder_eval": true,
  "encoder_parameters_frozen": true,
  "encoder_checkpoint_sha256_unchanged": true,
  "optimizer_separation": {
    "optimizer_param_count": 4,
    "head_param_count": 4,
    "encoder_param_count": 8,
    "optimizer_exactly_head": true,
    "optimizer_encoder_intersection": 0,
    "encoder_requires_grad_count": 0,
    "encoder_training": false
  },
  "head_output_devices": [
    "cuda:0"
  ],
  "head_initial_sha256": "c87310b53b6bf6ddb972403c8495629de70d344a40edba8f9fde1968ce9f3271",
  "head_final_sha256": "5ad5dd8833a3f66cec10db8bdf03457d6a90e5657b71811c0cd7cc38ddc07edf",
  "head_changed_max_abs_by_tensor": {
    "0.weight": 0.022298229858279228,
    "0.bias": 0.019051190465688705,
    "3.weight": 0.020340465009212494,
    "3.bias": 0.003042895346879959
  },
  "optimizer_steps": 70,
  "nonzero_gradient_steps": 70,
  "maximum_gradient_l1": 6705.454290270805,
  "epochs_run": 14,
  "best_epoch_1_based": 6,
  "history": [
    {
      "epoch": 1,
      "train_standardized_mse": 1.1985344693298738,
      "internal_validation_standardized_mse": 4.300019264221191,
      "steps": 5
    },
    {
      "epoch": 2,
      "train_standardized_mse": 0.770889424320707,
      "internal_validation_standardized_mse": 2.3230578899383545,
      "steps": 10
    },
    {
      "epoch": 3,
      "train_standardized_mse": 0.41718955038937805,
      "internal_validation_standardized_mse": 1.126440167427063,
      "steps": 15
    },
    {
      "epoch": 4,
      "train_standardized_mse": 0.2465629292096143,
      "internal_validation_standardized_mse": 1.2210471630096436,
      "steps": 20
    },
    {
      "epoch": 5,
      "train_standardized_mse": 0.17993207840187178,
      "internal_validation_standardized_mse": 1.3206332921981812,
      "steps": 25
    },
    {
      "epoch": 6,
      "train_standardized_mse": 0.1322655007373184,
      "internal_validation_standardized_mse": 0.9620532989501953,
      "steps": 30
    },
    {
      "epoch": 7,
      "train_standardized_mse": 0.09957844280291603,
      "internal_validation_standardized_mse": 1.0480252504348755,
      "steps": 35
    },
    {
      "epoch": 8,
      "train_standardized_mse": 0.07209010981348381,
      "internal_validation_standardized_mse": 1.466370940208435,
      "steps": 40
    },
    {
      "epoch": 9,
      "train_standardized_mse": 0.06404326884742391,
      "internal_validation_standardized_mse": 1.4176759719848633,
      "steps": 45
    },
    {
      "epoch": 10,
      "train_standardized_mse": 0.05011763339813467,
      "internal_validation_standardized_mse": 1.1557974815368652,
      "steps": 50
    },
    {
      "epoch": 11,
      "train_standardized_mse": 0.04544707985812665,
      "internal_validation_standardized_mse": 1.3395774364471436,
      "steps": 55
    },
    {
      "epoch": 12,
      "train_standardized_mse": 0.03797432977257599,
      "internal_validation_standardized_mse": 1.5515352487564087,
      "steps": 60
    },
    {
      "epoch": 13,
      "train_standardized_mse": 0.03443480024267034,
      "internal_validation_standardized_mse": 1.238293170928955,
      "steps": 65
    },
    {
      "epoch": 14,
      "train_standardized_mse": 0.03283619697987513,
      "internal_validation_standardized_mse": 1.1682392358779907,
      "steps": 70
    }
  ],
  "fit_rows": 573,
  "internal_validation_rows": 64,
  "parse_counts": {
    "train": {
      "rows": 637,
      "parsed": 637
    },
    "valid": {
      "rows": 91,
      "parsed": 91
    },
    "test": {
      "rows": 182,
      "parsed": 182
    }
  },
  "reload_checks": {
    "valid": {
      "rows": 91,
      "max_abs_prediction_difference": 4.76837158203125e-07,
      "allclose_rtol": 1e-05,
      "allclose_atol": 1e-05
    },
    "test": {
      "rows": 182,
      "max_abs_prediction_difference": 9.5367431640625e-07,
      "allclose_rtol": 1e-05,
      "allclose_atol": 1e-05
    }
  },
  "official_validation_scoring": false,
  "test_fitting": false,
  "cuda_peak_allocated_bytes": 457361408,
  "cuda_peak_reserved_bytes": 507510784,
  "elapsed_seconds": 4.812793065328151,
  "maximum_rss_kib": 1579572
}

```

### hainan-frozen-training-20261031/source/train_remote_v3.py

```python
"""One genuine Caco2 GPU run: frozen CheMeleon plus a new 512-unit head.
Only the three allowlisted CSV files and fixed checkpoint are opened as model/data inputs.
"""
import csv,hashlib,json,os,sys,time,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common_guarded import ROOT,GPU_UUID,environment,now,safe,sha,write_json
os.chdir(safe(ROOT,True));os.environ.clear();os.environ.update(environment())
import numpy as np
import torch
from torch import nn
from encoder import CheMeleonEmbedder
from chemprop import nn as chemprop_nn
from chemprop.models import MPNN
from chemprop.nn import RegressionFFN
cfg=json.loads((ROOT/'source/config.json').read_text());hc=cfg['head_config'];start=time.monotonic()
assert torch.cuda.is_available() and torch.cuda.device_count()==1,'Single explicit CUDA device required'
torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.manual_seed(hc['seed']);np.random.seed(hc['seed'])
torch.cuda.set_device(0);props=torch.cuda.get_device_properties(0)
torch.cuda.set_per_process_memory_fraction((4096*1024**2)/props.total_memory,0)
device='cuda:0'
write_json(ROOT/'raw/train-runtime.json',{'at':now(),'pid':os.getpid(),'pgid':os.getpgid(0),'start_stat':Path('/proc/self/stat').read_text(),'torch':torch.__version__,'cuda':torch.version.cuda,'device':device,'device_name':props.name,'visible_gpu_uuid':os.environ['CUDA_VISIBLE_DEVICES'],'device_properties':str(props),'cpu_affinity':sorted(os.sched_getaffinity(0)),'torch_threads':torch.get_num_threads(),'dataloader_workers':0,'limits':{'allocator_fraction':(4096*1024**2)/props.total_memory,'allocator_target_bytes':4096*1024**2,'note':'PyTorch allocator cap only, excludes CUDA context/third-party allocations. Supervisor observes RSS and walltime.'}})

rows={}
for inp in cfg['inputs']:
    p=safe(ROOT/inp['path'],True);assert sha(p)==inp['sha256']
    with p.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f);cols=reader.fieldnames;table=list(reader)
    split={'train':'train','validation':'valid','test':'test'}[inp['role']]
    assert len(table)==inp['rows'] and 'Drug_ID' in cols and 'Drug' in cols
    assert ('Y' in cols)==(split=='train')
    rows[split]=table
checkpoint=safe(ROOT/'assets/chemeleon_mp.pt',True);assert sha(checkpoint)==cfg['pretrained_sha256']

def digest_state(model):
    each={};aggregate=hashlib.sha256()
    kinds={name:'parameter' for name,_ in model.named_parameters()}
    kinds.update({name:'buffer' for name,_ in model.named_buffers()})
    for name,t in sorted(model.state_dict().items()):
        value=t.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        item={'sha256':hashlib.sha256(value).hexdigest(),'shape':list(t.shape),'dtype':str(t.dtype),'kind':kinds.get(name,'state')}
        each[name]=item;aggregate.update(name.encode()+b'\0'+json.dumps(item,sort_keys=True).encode()+b'\0')
    return {'sha256':aggregate.hexdigest(),'tensors':each}

enc=CheMeleonEmbedder(checkpoint,device=device,batch_size=64);enc.assert_frozen()
assert all(p.device.type=='cuda' for p in enc.model.parameters())
before=digest_state(enc.model);write_json(ROOT/'artifacts/encoder-before.json',before)
enc_events=[]
def enc_hook(module,inputs,out):
    tensors=[out] if isinstance(out,torch.Tensor) else [x for x in out if isinstance(x,torch.Tensor)]
    assert tensors and all(x.device.type=='cuda' for x in tensors)
    assert not torch.is_grad_enabled() and not enc.model.training
    enc_events.append({'output_shapes':[list(x.shape) for x in tensors],'devices':[str(x.device) for x in tensors],'grad_enabled':torch.is_grad_enabled(),'training':enc.model.training})
enc_handle=enc.model.message_passing.register_forward_hook(enc_hook)
X={};masks={}
for split in ['train','valid','test']:
    enc.assert_frozen();X[split],masks[split]=enc.embed([r['Drug'] for r in rows[split]])
    assert X[split].shape==(len(rows[split]),enc.feature_dim)
    np.savez(ROOT/'artifacts'/f'features-{split}.npz',features=X[split],parse_mask=masks[split])
    print(json.dumps({'phase':'encoded','split':split,'rows':len(rows[split]),'parsed':int(masks[split].sum()),'feature_dim':enc.feature_dim,'at':now()}),flush=True)
y=np.asarray([float(r['Y']) for r in rows['train']],dtype=np.float32);assert np.isfinite(y).all()
rng=np.random.default_rng(hc['seed']);idx=rng.permutation(len(y));nv=max(1,int(round(len(y)*hc['val_fraction_from_train'])));va=idx[:nv];tr=idx[nv:]
filled={split:np.where(np.isfinite(v),v,np.float32(0)).astype(np.float32) for split,v in X.items()}
mu=filled['train'][tr].mean(axis=0);sd=filled['train'][tr].std(axis=0);sd[sd<1e-8]=1
ym=float(y[tr].mean());ys=float(y[tr].std()) or 1.;yy=(y-ym)/ys
scaled={k:(v-mu)/sd for k,v in filled.items()}
assert all(np.isfinite(v).all() for v in scaled.values())
np.savez(ROOT/'artifacts/preprocessing.npz',feature_mean=mu,feature_std=sd,train_row_indices=tr,internal_validation_row_indices=va,target_mean=ym,target_std=ys)

def build_head(seed):
    torch.manual_seed(seed)
    return nn.Sequential(nn.Linear(enc.feature_dim,512),nn.ReLU(),nn.Dropout(hc['dropout']),nn.Linear(512,1)).to(device)
head=build_head(hc['seed']);initial={k:v.detach().cpu().clone() for k,v in head.state_dict().items()};initial_digest=digest_state(head)
torch.save({'state_dict':initial,'seed':hc['seed']},ROOT/'artifacts/head-initial.pt')
opt=torch.optim.AdamW(head.parameters(),lr=hc['lr'],weight_decay=hc['weight_decay'])
eids={id(p) for p in enc.model.parameters()};hids={id(p) for p in head.parameters()};oids={id(p) for g in opt.param_groups for p in g['params']}
assert oids==hids and oids.isdisjoint(eids)
optimizer_check={'optimizer_param_count':len(oids),'head_param_count':len(hids),'encoder_param_count':len(eids),'optimizer_exactly_head':oids==hids,'optimizer_encoder_intersection':len(oids & eids),'encoder_requires_grad_count':sum(p.requires_grad for p in enc.model.parameters()),'encoder_training':enc.model.training}
write_json(ROOT/'artifacts/optimizer-separation.json',optimizer_check)
Xt=torch.as_tensor(np.ascontiguousarray(scaled['train'][tr]),device=device);yt=torch.as_tensor(yy[tr],device=device).reshape(-1,1)
Xv=torch.as_tensor(np.ascontiguousarray(scaled['train'][va]),device=device);yv=torch.as_tensor(yy[va],device=device).reshape(-1,1)
loss_fn=nn.MSELoss();gen=torch.Generator(device='cpu').manual_seed(hc['seed']);best=float('inf');best_epoch=-1;best_state=None;steps=0;nonzero_steps=0;grad_max=0.;history=[];head_devices=set()
for epoch in range(hc['epochs']):
    enc.assert_frozen();head.train();perm=torch.randperm(len(tr),generator=gen);train_loss=0.
    for s in range(0,len(tr),hc['batch_size']):
        sel=perm[s:s+hc['batch_size']].to(device);opt.zero_grad(set_to_none=True);out=head(Xt[sel]);assert out.device.type=='cuda';head_devices.add(str(out.device));loss=loss_fn(out,yt[sel]);assert torch.isfinite(loss)
        loss.backward();grad=sum(float(p.grad.detach().abs().sum()) for p in head.parameters() if p.grad is not None)
        assert np.isfinite(grad) and grad>0 and all(p.grad is None or p.grad.device.type=='cuda' for p in head.parameters())
        nonzero_steps+=1;grad_max=max(grad_max,grad);opt.step();steps+=1;train_loss+=float(loss)*len(sel)
        assert all(p.grad is None for p in enc.model.parameters())
    head.eval()
    with torch.no_grad():val=float(loss_fn(head(Xv),yv))
    history.append({'epoch':epoch+1,'train_standardized_mse':train_loss/len(tr),'internal_validation_standardized_mse':val,'steps':steps})
    print(json.dumps({'phase':'head_training',**history[-1]}),flush=True)
    if val<best-1e-7:
        best=val;best_epoch=epoch;best_state={k:v.detach().clone() for k,v in head.state_dict().items()}
    elif epoch-best_epoch>=hc['patience']:break
assert best_state is not None and steps>0 and nonzero_steps>0
head.load_state_dict(best_state);head.eval();final_digest=digest_state(head)
changed={k:float((v.detach().cpu()-initial[k]).abs().max()) for k,v in head.state_dict().items()}
assert any(v>0 for v in changed.values()) and final_digest['sha256']!=initial_digest['sha256']
ck={'format':'hainan_caco2_chemeleon_head_v1','run_id':cfg['run_id'],'task':'caco2_wang','encoder_sha256':cfg['pretrained_sha256'],'head_config':hc,'feature_dim':enc.feature_dim,'state_dict':{k:v.detach().cpu() for k,v in head.state_dict().items()},'feature_mean':mu.tolist(),'feature_std':sd.tolist(),'target_mean':ym,'target_std':ys,'fill_value':0.,'fit_row_indices':tr.tolist(),'internal_validation_row_indices':va.tolist()}
torch.save(ck,ROOT/'artifacts/caco2_wang-head.pt')

def predict(model,features,mean,std,ym,ys):
    a=np.where(np.isfinite(features),features,np.float32(0));a=(a-mean)/std
    out=[]
    with torch.no_grad():
        for s in range(0,len(a),128):
            yhat=model(torch.as_tensor(np.ascontiguousarray(a[s:s+128]),dtype=torch.float32,device=device));assert yhat.device.type=='cuda';out.append(yhat.cpu().numpy().reshape(-1))
    result=np.concatenate(out)*ys+ym;assert np.isfinite(result).all();return result
pred={s:predict(head,X[s],mu,sd,ym,ys) for s in ['valid','test']}
after=digest_state(enc.model);assert before==after and all(p.grad is None for p in enc.model.parameters());enc.assert_frozen();enc_handle.remove()
# Reload our saved head and a fresh fixed encoder, then repeat blind inference on CUDA.
loaded=torch.load(ROOT/'artifacts/caco2_wang-head.pt',map_location='cpu',weights_only=True)
reloaded=build_head(0);reloaded.load_state_dict(loaded['state_dict']);reloaded.eval();assert digest_state(reloaded)==final_digest
torch.manual_seed(hc['seed'])  # Reproduce the frozen, unused MPNN predictor initialization too.
enc2=CheMeleonEmbedder(checkpoint,device=device,batch_size=64);enc2.assert_frozen();assert digest_state(enc2.model)==before
reload_checks={};pred_rows=[]
for split in ['valid','test']:
    xx,ok=enc2.embed([r['Drug'] for r in rows[split]]);assert np.array_equal(ok,masks[split])
    pp=predict(reloaded,xx,np.asarray(loaded['feature_mean'],dtype=np.float32),np.asarray(loaded['feature_std'],dtype=np.float32),loaded['target_mean'],loaded['target_std'])
    delta=float(np.max(np.abs(pred[split]-pp)));assert np.allclose(pred[split],pp,rtol=1e-5,atol=1e-5)
    reload_checks[split]={'rows':len(pp),'max_abs_prediction_difference':delta,'allclose_rtol':1e-5,'allclose_atol':1e-5}
    for i,(row,v) in enumerate(zip(rows[split],pp)):
        pred_rows.append({'task':'caco2_wang','split':split,'row_index':i,'Drug_ID':row['Drug_ID'],'Drug':row['Drug'],'y_pred':format(float(v),'.10g')})
assert digest_state(enc.model)==before and digest_state(enc2.model)==before
assert sha(checkpoint)==cfg['pretrained_sha256']
with (ROOT/'artifacts/predictions.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['task','split','row_index','Drug_ID','Drug','y_pred']);writer.writeheader();writer.writerows(pred_rows)
write_json(ROOT/'artifacts/encoder-after.json',after)
write_json(ROOT/'artifacts/training-evidence.json',{'started_at':json.loads((ROOT/'raw/train-runtime.json').read_text())['at'],'completed_at':now(),'device':device,'gpu_uuid':GPU_UUID,'encoder_forward_events':enc_events,'encoder_state_unchanged':before==after,'encoder_gradients_none':all(p.grad is None for p in enc.model.parameters()),'encoder_eval':not enc.model.training,'encoder_parameters_frozen':all(not p.requires_grad for p in enc.model.parameters()),'encoder_checkpoint_sha256_unchanged':sha(checkpoint)==cfg['pretrained_sha256'],'optimizer_separation':optimizer_check,'head_output_devices':sorted(head_devices),'head_initial_sha256':initial_digest['sha256'],'head_final_sha256':final_digest['sha256'],'head_changed_max_abs_by_tensor':changed,'optimizer_steps':steps,'nonzero_gradient_steps':nonzero_steps,'maximum_gradient_l1':grad_max,'epochs_run':len(history),'best_epoch_1_based':best_epoch+1,'history':history,'fit_rows':len(tr),'internal_validation_rows':len(va),'parse_counts':{s:{'rows':len(v),'parsed':int(masks[s].sum())} for s,v in rows.items()},'reload_checks':reload_checks,'official_validation_scoring':False,'test_fitting':False,'cuda_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'cuda_peak_reserved_bytes':torch.cuda.max_memory_reserved(),'elapsed_seconds':time.monotonic()-start,'maximum_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
write_json(ROOT/'raw/train-complete.json',{'status':'success','at':now(),'optimizer_steps':steps,'prediction_rows':len(pred_rows),'encoder_frozen':True})
print(json.dumps({'status':'success','optimizer_steps':steps,'rows':len(pred_rows),'elapsed_seconds':time.monotonic()-start}),flush=True)

```

### hainan-frozen-training-20261031/source/encoder.py

```python
"""Signature-verified, no-download extractor for the CheMeleon fingerprint embedding.

This is the *only* place that turns SMILES into encoder vectors. It is deliberately separate
from the training code so the frozen part is easy to audit:

* ``CheMeleonEmbedder`` loads the pinned ``chemeleon_mp.pt`` (size + MD5 checked), builds
  chemprop ``BondMessagePassing`` from the checkpoint's own hyper-parameters, wraps it in an
  ``MPNN`` with the author-published ``MeanAggregation``, sets ``eval()``, disables grads and
  never exposes the encoder to an optimizer.
* ``embed`` returns an ``(n, d)`` float32 matrix plus a boolean parse mask. Rows that RDKit
  cannot parse come back as NaN and must be filled by the caller under a documented policy.

The torch/chemprop imports are lazy so the module can be imported and statically checked
without the scientific stack present.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

CHEMELEON_SIZE = 34859448
CHEMELEON_MD5 = "6a80b54fdb7de37ef0374d302f01e8ce"
CHEMELEON_URL = "https://zenodo.org/records/15460715/files/chemeleon_mp.pt"


class EncoderError(RuntimeError):
    pass


def verify_checkpoint(path: Path) -> dict:
    """Raise ``EncoderError`` unless ``path`` is exactly the pinned CheMeleon weight file."""
    path = Path(path)
    if not path.is_file():
        raise EncoderError(
            f"missing CheMeleon checkpoint: {path}\n"
            f"download it from {CHEMELEON_URL} and pass --chemeleon"
        )
    size = path.stat().st_size
    if size != CHEMELEON_SIZE:
        raise EncoderError(f"size mismatch: {size} != {CHEMELEON_SIZE} for {path}")
    md5 = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            md5.update(chunk)
    digest = md5.hexdigest()
    if digest != CHEMELEON_MD5:
        raise EncoderError(f"md5 mismatch: {digest} != {CHEMELEON_MD5} for {path}")
    return {"path": str(path), "size": size, "md5": digest}


class CheMeleonEmbedder:
    """Frozen, gradient-disabled CheMeleon fingerprint extractor."""

    def __init__(self, checkpoint: Path, device: str | None = None,
                 batch_size: int = 64):
        import torch
        from chemprop import nn
        from chemprop.models import MPNN
        from chemprop.nn import RegressionFFN

        self.checkpoint_meta = verify_checkpoint(checkpoint)
        if device != "cuda:0" or not torch.cuda.is_available():
            raise EncoderError("This run requires explicit cuda:0; no CPU fallback")
        self.device = device
        self.batch_size = batch_size

        self.asserted_checkpoint_sha256 = hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()
        if self.asserted_checkpoint_sha256 != "c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651":
            raise EncoderError("SHA256 mismatch")
        raw = torch.load(checkpoint, map_location="cpu", weights_only=True)
        for key in ("hyper_parameters", "state_dict"):
            if key not in raw:
                raise EncoderError(f"checkpoint missing '{key}'")
        mp = nn.BondMessagePassing(**raw["hyper_parameters"])
        mp.load_state_dict(raw["state_dict"], strict=True)
        model = MPNN(
            message_passing=mp,
            agg=nn.MeanAggregation(),
            predictor=RegressionFFN(input_dim=mp.output_dim),  # unused
        )
        model.eval()
        model.to(device)
        for p in model.parameters():
            p.requires_grad_(False)
        self.model = model
        self.feature_dim = int(mp.output_dim)

    def assert_frozen(self) -> None:
        """Guard called before any downstream training to assert encoder immutability."""
        if self.model.training:
            raise EncoderError("encoder is not in eval() mode")
        trainable = [n for n, p in self.model.named_parameters() if p.requires_grad]
        if trainable:
            raise EncoderError(f"encoder has trainable params: {trainable[:5]}")

    def embed(self, smiles: list[str]):
        """Return (float32 [n, d] with NaN on unparseable rows, bool [n] parse mask)."""
        import numpy as np
        import torch
        from chemprop import featurizers
        from chemprop.data import BatchMolGraph
        from rdkit import Chem, RDLogger

        RDLogger.DisableLog("rdApp.*")
        featurizer = featurizers.SimpleMoleculeMolGraphFeaturizer()

        n = len(smiles)
        out = np.full((n, self.feature_dim), np.nan, dtype=np.float32)
        ok = np.zeros(n, dtype=bool)
        with torch.no_grad():
            for start in range(0, n, self.batch_size):
                chunk = smiles[start:start + self.batch_size]
                mols, idx = [], []
                for i, smi in enumerate(chunk):
                    mol = Chem.MolFromSmiles(smi)
                    if mol is not None:
                        mols.append(mol)
                        idx.append(start + i)
                if not mols:
                    continue
                bmg = BatchMolGraph([featurizer(m) for m in mols])
                bmg.to(device=self.model.device)
                out[idx] = self.model.fingerprint(bmg).numpy(force=True).astype(np.float32)
                ok[idx] = True
        return out, ok
```

### hainan-frozen-training-20261031/source/common_remote.py

```python
"""Task-only paths and clean subprocess environment. No target credential handling."""
import datetime,hashlib,json,os,stat
from pathlib import Path
ROOT=Path('<RUN_ROOT>')
VENV=Path('<ENV_ROOT>')
GPU_UUID='<SELECTED_GPU_UUID>'

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def safe(p,existing=False):
    p=Path(p);assert p==ROOT or ROOT in p.parents
    assert p.resolve(strict=existing)==p
    for a in [p,*p.parents]:
        if a.exists():
            st=a.lstat();assert not stat.S_ISLNK(st.st_mode)
            if stat.S_ISREG(st.st_mode):assert st.st_nlink==1
        if a==Path('/'):break
    mounts=[line.split()[4] for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    assert not any(Path(m)!=Path('/mnt/data') and (Path(m)==ROOT or ROOT in Path(m).parents) for m in mounts)
    return p

def write_json(p,v):
    p=safe(p);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def environment():
    d={'PATH':str(VENV/'bin')+':/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(ROOT/'home'),'TMPDIR':str(ROOT/'tmp'),'TMP':str(ROOT/'tmp'),'TEMP':str(ROOT/'tmp'),'XDG_CACHE_HOME':str(ROOT/'cache/xdg'),'XDG_CONFIG_HOME':str(ROOT/'config'),'XDG_DATA_HOME':str(ROOT/'datahome'),'XDG_STATE_HOME':str(ROOT/'state'),'PIP_CACHE_DIR':str(ROOT/'cache/pip'),'PIP_CONFIG_FILE':'/dev/null','PIP_DISABLE_PIP_VERSION_CHECK':'1','PIP_NO_INPUT':'1','PIP_KEYRING_PROVIDER':'disabled','HF_HOME':str(ROOT/'cache/hf'),'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TORCH_HOME':str(ROOT/'cache/torch'),'TORCH_EXTENSIONS_DIR':str(ROOT/'cache/extensions'),'TORCHINDUCTOR_CACHE_DIR':str(ROOT/'cache/inductor'),'TRITON_CACHE_DIR':str(ROOT/'cache/triton'),'CUDA_CACHE_PATH':str(ROOT/'cache/cuda'),'NUMBA_CACHE_DIR':str(ROOT/'cache/numba'),'MPLCONFIGDIR':str(ROOT/'cache/matplotlib'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','NUMEXPR_NUM_THREADS':'2','VECLIB_MAXIMUM_THREADS':'2','CUDA_VISIBLE_DEVICES':GPU_UUID,'CUDA_DEVICE_ORDER':'PCI_BUS_ID','WANDB_MODE':'disabled','WANDB_DIR':str(ROOT/'cache/wandb'),'WANDB_DISABLED':'true','CUBLAS_WORKSPACE_CONFIG':':4096:8'}
    for v in d.values():
        if v.startswith(str(ROOT)) and ':' not in v:safe(Path(v))
    return d

```

### hainan-frozen-training-20261031/source/common_guarded.py

```python
"""Task-local correction after observed joblib semaphore side effect. No policy/Skill edits."""
from common_remote import ROOT,GPU_UUID,now,safe,sha,write_json
from common_remote import environment as original_environment

def environment():
    env=original_environment()
    env.update({'JOBLIB_MULTIPROCESSING':'0','JOBLIB_TEMP_FOLDER':str(ROOT/'tmp/joblib')})
    return env

```

### Historical scientific acceptance

Historical independent training acceptance. It predates this trial fixed-valid scoring; old statements about no scoring describe that original run.

# 海南冻结底座训练：修复与实际验收

2026-10-31（北京时间）。结论：**本次单作业路径通过，已完成真实 GPU 编码、新头训练、盲输入预测与主控验收。** 不包含共享/并行分支、其他底座、官方 valid 评分或赛事上传。

## 问题与修复

旧试验没有完成训练。它遗漏选卡健康检查；GPU4 末次状态要求 Reset，原先没有健康原件，不能认定全部旧失败均由该硬件状态引起。准备阶段首次 joblib 导入还创建过一个 `/dev/shm` 信号量；后续写入限制与 CUDA 的线程命名行为存在兼容问题。

本轮主控亲自处理，未新派 Thread。保留旧 run，单独使用 `hainan-frozen-training-20261031`。当前查询排除了 GPU4/7（Reset），选 GPU3（无恢复要求、0 ECC、无待处理行重映射、空闲），每阶段启动前又采样三次。没有执行 GPU reset、驱动/系统重启或对他人的任务做任何停止操作。

复用旧 run 已安装的自有私有 venv，未重新安装或下载依赖；只读核验其 Python 与 78 项发行包元数据。所有新 HOME、缓存、临时目录和结果指向新 run。首次导入前设置 `JOBLIB_MULTIPROCESSING=0`，保留 Landlock 写入限制。复用经过审读的兼容库，只把本进程可选线程命名写入转到 `/dev/null`；不修改 CUDA 计算、不扩大目录写权限。

先执行完整依赖导入与真实 CUDA 矩阵计算，退出0；取回该阶段轨迹并独立确认无成功越界写入后，启动同一已登记 Caco2 配置。未进行参数搜索，没有读取或传输私有 valid 标签。

## 实际训练与产物

- 主机 <TRAINING_HOST>，<ACCOUNT> UID/GID<REDACTED>；经已登记 Windows 中转和两层固定 ED25519 主机密钥。
- GPU3 / `<SELECTED_GPU_UUID>`；训练实际 PID707301，CUDA 编码及新头输出均为 `cuda:0`。
- 官方 train637行，内部拆分573/64；无标签 valid91行、test182行。输入摘要与既有批准原件一致，全部分子解析成功，未删行、去重或清洗。
- CheMeleon 冻结编码，特征2048维；新头512单元，固定 seed42、lr0.001、dropout0.1、batch128等原计划参数。
- 训练14 epoch，70次优化更新和70次非零梯度；早停，保存第6 epoch的最佳新头。CPU仅2个核心、数据加载workers0。
- 模型代码约4.81秒；含依赖导入、健康采样与系统调用记录的正式阶段28.92秒。预检查另32.55秒；不包括本地审查、网络取回、文档工作。
- PyTorch峰值分配436.17MiB、保留484MiB；nvidia-smi采样峰值1169MiB（约1.14GiB，包含上下文）。进程树RSS采样峰值1,591,902,208字节（约1.48GiB）。4GiB仅是PyTorch分配器上限，不等于整卡硬配额；RAM/时长/总输出是监督检查，非内核RAM配额。
- 底座完整state_dict的11项状态（8项参数、3项buffer）前后完全相同，聚合SHA256为 `cbf2c91ab6ca8196091df49cda7104dbe5e505f3720489c9429507175a27428f`。原始checkpoint SHA256仍为 `c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651`。
- 优化器只有4个新头参数张量，和编码器参数集合交集为0；主控直接比较两个checkpoint ZIP内原始浮点张量存储，4项均发生实际变化，不执行pickle。
- 导出273行带task/split/原行号/ID/原SMILES的有限预测；重新加载新头及固定编码器后，valid/test最大绝对误差分别约4.77e-7/9.54e-7。

交付文件在 `../artifacts/`：`caco2_wang-head.pt`、`preprocessing.npz`、`predictions.csv`、冻结前后摘要、训练证据和逐文件manifest。这是一个任务的模型与预测，不是全22任务的赛事提交包。预测表现未用官方valid标签评价。

## 边界与独立验收

51份远端原件（65,619,331字节）均按逐文件SHA256核验；上传源代码、配置和辅助库与取回原件相同。主控审读 `source/supervisor.py`、`guard_exec_v3.py`、`train_remote_v3.py`、`encoder.py`、路径环境和兼容库源码，检查实际调用、数据读取、优化器构造、冻结断言及重载路径。

两个完整strace由独立离线解析器审查，成功的项目文件写入都在本run，目录外成功文件改动0，未解析/未配对项0，未出现joblib共享信号量。NVIDIA驱动每阶段尝试57次删除 `/dev/char/*` 设备链接，均被拒绝，未成功删除；此原始现象保留，不能将“被拒绝”写成“没有尝试”。已有NVIDIA字符设备及 `/dev/null` 的必要设备IO单列，不冒充普通产物文件。没有为兼容放开目录外权限。

写入限制只约束本进程树相关文件系统操作，读、设备ioctl及部分元数据操作不是完整隔离；同时依赖审阅的代码与轨迹。驱动枚举会打开其他GPU设备节点，不能据CUDA_VISIBLE_DEVICES声称物理设备隔离。实际GPU进程采样只有所选卡出现本作业PID，没有把他人的资源视作本次所有。

独立末次只读检查：6个登记的监督/跟踪/工作进程全部消失，GPU3恢复到0MiB/0%，健康仍为None；4个输入/权重摘要和源代码摘要一致。标准调度命令squeue/sinfo/qstat未发现；没有宣称资源被技术锁定，也没有读取同事项目以寻找预约。本轮使用空闲卡，未行使共享分支。

17项离线测试通过：9项计划准入，8项产物验收（包括篡改buffer、0训练步、行号错位、越界写证据、未解析轨迹、未释放进程、GPU要求Reset的反例）。这些测试只改本地临时副本，无新增训练或标签读取。

## 可复用交付与优化

新入口为 `rules/skills/admet-frozen-training/SKILL.md`，接到项目AGENTS和全局Skill索引；其中提供结果标准、边界、已验证参考和只读证据检查器。连接安全仍由海南Skill唯一管理，赛事/冻结条件仍由ADMET宿主入口管理，避免重复维护多份规则。

本任务计算很小，优先优化环境和特征复用：以后可复用已核验私有环境；同一固定编码器和输入/行序/配置可复用有完整身份的特征缓存，避免每个新头重新编码。改缓存身份、新模型或特征版本需要重新核验，不能把旧缓存当万能输入。批量参数搜索或共享并行须按届时授权与实时资源独立验证，本轮没有扩展执行。

证据入口：`result.json`、`evidence-check.json`、`audit-final-fetch.json`、`postcheck.json`、`../raw/final-fetch/fetch-manifest.json`。运行时所用海南Skill原件保存在 `skill-sources/hainan-SKILL-used.md`；后续仅补实测事实，不回写历史PLAN摘要。本轮没有创建心跳；此前试验心跳已停止。


## hainan-skill-follow-20261031


### hainan-skill-follow-20261031/source/config.json

```json
{
  "run_id": "hainan-skill-follow-20261031",
  "task": "caco2_wang",
  "gpu_index": 3,
  "gpu_uuid": "<SELECTED_GPU_UUID>",
  "head_config": {
    "hidden_dims": [
      256
    ],
    "dropout": 0.1,
    "lr": 0.0005,
    "weight_decay": 0.0001,
    "batch_size": 128,
    "epochs": 50,
    "patience": 8,
    "val_fraction_from_train": 0.1,
    "seed": 43
  },
  "inputs": [
    {
      "role": "train",
      "task": "caco2_wang",
      "path": "input/train.csv",
      "sha256": "3061c58d3601d081e5459a2de03dc1d189243c4b5683d1b7288577a29fed4d6f",
      "rows": 637
    },
    {
      "role": "validation",
      "task": "caco2_wang",
      "path": "input/valid.csv",
      "sha256": "41370e87d89a96a7481425dae1bf7c45184bd116b353e96719b2afcd0a8a5ca3",
      "rows": 91
    },
    {
      "role": "test",
      "task": "caco2_wang",
      "path": "input/test.csv",
      "sha256": "d87dac944bedcefb216bce57ba5a8de93d3781172c66653b937e5065b9c2579c",
      "rows": 182
    }
  ],
  "pretrained_sha256": "c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651",
  "resource_budget": {
    "gpu_count": 1,
    "gpu_peak_target_mib": 4096,
    "cpu_threads": 2,
    "dataloader_workers": 0,
    "ram_target_gib": 8,
    "training_timeout_seconds": 900,
    "setup_budget_seconds": 2700,
    "dependency_download_budget_gib": 0,
    "result_budget_gib": 1,
    "limits_are_targets_until_enforcement_verified": true
  }
}

```

### hainan-skill-follow-20261031/learning-curve.csv

```csv
epoch,train_standardized_mse,internal_validation_standardized_mse,steps
1,0.6882476571030641,3.0261993408203125,5
2,0.40610989142878934,2.3219480514526367,10
3,0.22144546241452348,3.197662353515625,15
4,0.17562783846264318,3.1713802814483643,20
5,0.11514225266678794,2.321878433227539,25
6,0.09995735599212413,2.0297861099243164,30
7,0.08082326626434376,2.123359441757202,35
8,0.06489891747425572,1.901146411895752,40
9,0.0524291963061321,1.770197868347168,45
10,0.0521300599746159,1.7413930892944336,50
11,0.04500136365155067,1.5905420780181885,55
12,0.04111166698224258,1.7465925216674805,60
13,0.03379084377258652,1.963202953338623,65
14,0.03591767015231426,2.26147723197937,70
15,0.03109112785995839,2.5181281566619873,75
16,0.029656947234460197,2.158698797225952,80
17,0.02762104495449632,2.0980396270751953,85
18,0.0255494985215847,2.711383819580078,90
19,0.024395994377203845,3.0219812393188477,95

```

### hainan-skill-follow-20261031/artifacts/training-evidence.json

```json
{
  "started_at": "2026-10-30T17:21:06.213953+00:00",
  "completed_at": "2026-10-30T17:21:08.762588+00:00",
  "device": "cuda:0",
  "gpu_uuid": "<SELECTED_GPU_UUID>",
  "encoder_forward_events": [
    {
      "output_shapes": [
        [
          2128,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1944,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          2080,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          2096,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1738,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1908,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1936,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1382,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1646,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1549,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1931,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          860,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          2051,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1874,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    },
    {
      "output_shapes": [
        [
          1599,
          2048
        ]
      ],
      "devices": [
        "cuda:0"
      ],
      "grad_enabled": false,
      "training": false
    }
  ],
  "encoder_state_unchanged": true,
  "encoder_gradients_none": true,
  "encoder_eval": true,
  "encoder_parameters_frozen": true,
  "encoder_checkpoint_sha256_unchanged": true,
  "optimizer_separation": {
    "optimizer_param_count": 4,
    "head_param_count": 4,
    "encoder_param_count": 8,
    "optimizer_exactly_head": true,
    "optimizer_encoder_intersection": 0,
    "encoder_requires_grad_count": 0,
    "encoder_training": false
  },
  "head_output_devices": [
    "cuda:0"
  ],
  "head_initial_sha256": "ee76b6bfbb7b0b1476f4b9a26c815c14d0c5d08578f2c858a341180d3475d062",
  "head_final_sha256": "2d032f8a2427e7ec56250b46b27011349c35ada5d471a7f9716848b49115425d",
  "head_changed_max_abs_by_tensor": {
    "0.weight": 0.014782390557229519,
    "0.bias": 0.009866665117442608,
    "3.weight": 0.010463228449225426,
    "3.bias": 0.0011578276753425598
  },
  "head_config": {
    "hidden_dims": [
      256
    ],
    "dropout": 0.1,
    "lr": 0.0005,
    "weight_decay": 0.0001,
    "batch_size": 128,
    "epochs": 50,
    "patience": 8,
    "val_fraction_from_train": 0.1,
    "seed": 43
  },
  "head_parameter_shapes": {
    "0.weight": [
      256,
      2048
    ],
    "0.bias": [
      256
    ],
    "3.weight": [
      1,
      256
    ],
    "3.bias": [
      1
    ]
  },
  "optimizer_config": [
    {
      "lr": 0.0005,
      "weight_decay": 0.0001
    }
  ],
  "optimizer_steps": 95,
  "nonzero_gradient_steps": 95,
  "maximum_gradient_l1": 2547.7726187705994,
  "epochs_run": 19,
  "best_epoch_1_based": 11,
  "history": [
    {
      "epoch": 1,
      "train_standardized_mse": 0.6882476571030641,
      "internal_validation_standardized_mse": 3.0261993408203125,
      "steps": 5
    },
    {
      "epoch": 2,
      "train_standardized_mse": 0.40610989142878934,
      "internal_validation_standardized_mse": 2.3219480514526367,
      "steps": 10
    },
    {
      "epoch": 3,
      "train_standardized_mse": 0.22144546241452348,
      "internal_validation_standardized_mse": 3.197662353515625,
      "steps": 15
    },
    {
      "epoch": 4,
      "train_standardized_mse": 0.17562783846264318,
      "internal_validation_standardized_mse": 3.1713802814483643,
      "steps": 20
    },
    {
      "epoch": 5,
      "train_standardized_mse": 0.11514225266678794,
      "internal_validation_standardized_mse": 2.321878433227539,
      "steps": 25
    },
    {
      "epoch": 6,
      "train_standardized_mse": 0.09995735599212413,
      "internal_validation_standardized_mse": 2.0297861099243164,
      "steps": 30
    },
    {
      "epoch": 7,
      "train_standardized_mse": 0.08082326626434376,
      "internal_validation_standardized_mse": 2.123359441757202,
      "steps": 35
    },
    {
      "epoch": 8,
      "train_standardized_mse": 0.06489891747425572,
      "internal_validation_standardized_mse": 1.901146411895752,
      "steps": 40
    },
    {
      "epoch": 9,
      "train_standardized_mse": 0.0524291963061321,
      "internal_validation_standardized_mse": 1.770197868347168,
      "steps": 45
    },
    {
      "epoch": 10,
      "train_standardized_mse": 0.0521300599746159,
      "internal_validation_standardized_mse": 1.7413930892944336,
      "steps": 50
    },
    {
      "epoch": 11,
      "train_standardized_mse": 0.04500136365155067,
      "internal_validation_standardized_mse": 1.5905420780181885,
      "steps": 55
    },
    {
      "epoch": 12,
      "train_standardized_mse": 0.04111166698224258,
      "internal_validation_standardized_mse": 1.7465925216674805,
      "steps": 60
    },
    {
      "epoch": 13,
      "train_standardized_mse": 0.03379084377258652,
      "internal_validation_standardized_mse": 1.963202953338623,
      "steps": 65
    },
    {
      "epoch": 14,
      "train_standardized_mse": 0.03591767015231426,
      "internal_validation_standardized_mse": 2.26147723197937,
      "steps": 70
    },
    {
      "epoch": 15,
      "train_standardized_mse": 0.03109112785995839,
      "internal_validation_standardized_mse": 2.5181281566619873,
      "steps": 75
    },
    {
      "epoch": 16,
      "train_standardized_mse": 0.029656947234460197,
      "internal_validation_standardized_mse": 2.158698797225952,
      "steps": 80
    },
    {
      "epoch": 17,
      "train_standardized_mse": 0.02762104495449632,
      "internal_validation_standardized_mse": 2.0980396270751953,
      "steps": 85
    },
    {
      "epoch": 18,
      "train_standardized_mse": 0.0255494985215847,
      "internal_validation_standardized_mse": 2.711383819580078,
      "steps": 90
    },
    {
      "epoch": 19,
      "train_standardized_mse": 0.024395994377203845,
      "internal_validation_standardized_mse": 3.0219812393188477,
      "steps": 95
    }
  ],
  "fit_rows": 573,
  "internal_validation_rows": 64,
  "parse_counts": {
    "train": {
      "rows": 637,
      "parsed": 637
    },
    "valid": {
      "rows": 91,
      "parsed": 91
    },
    "test": {
      "rows": 182,
      "parsed": 182
    }
  },
  "reload_checks": {
    "valid": {
      "rows": 91,
      "max_abs_prediction_difference": 9.5367431640625e-07,
      "allclose_rtol": 1e-05,
      "allclose_atol": 1e-05
    },
    "test": {
      "rows": 182,
      "max_abs_prediction_difference": 9.5367431640625e-07,
      "allclose_rtol": 1e-05,
      "allclose_atol": 1e-05
    }
  },
  "official_validation_scoring": false,
  "test_fitting": false,
  "cuda_peak_allocated_bytes": 444438528,
  "cuda_peak_reserved_bytes": 505413632,
  "elapsed_seconds": 3.562362622935325,
  "maximum_rss_kib": 1554656
}

```

### hainan-skill-follow-20261031/source/train_remote_v3.py

```python
"""One genuine Caco2 GPU run: frozen CheMeleon plus a new 256-unit head.
Only the three allowlisted CSV files and fixed checkpoint are opened as model/data inputs.
"""
import csv,hashlib,json,os,sys,time,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common_guarded import ROOT,GPU_UUID,environment,now,safe,sha,write_json
os.chdir(safe(ROOT,True));os.environ.clear();os.environ.update(environment())
import numpy as np
import torch
from torch import nn
from encoder import CheMeleonEmbedder
from chemprop import nn as chemprop_nn
from chemprop.models import MPNN
from chemprop.nn import RegressionFFN
cfg=json.loads((ROOT/'source/config.json').read_text());hc=cfg['head_config'];start=time.monotonic()
assert hc['hidden_dims']==[256] and hc['lr']==0.0005 and hc['seed']==43
assert torch.cuda.is_available() and torch.cuda.device_count()==1,'Single explicit CUDA device required'
torch.set_num_threads(2);torch.set_num_interop_threads(1);torch.manual_seed(hc['seed']);np.random.seed(hc['seed'])
torch.cuda.set_device(0);props=torch.cuda.get_device_properties(0)
torch.cuda.set_per_process_memory_fraction((4096*1024**2)/props.total_memory,0)
device='cuda:0'
write_json(ROOT/'raw/train-runtime.json',{'at':now(),'pid':os.getpid(),'pgid':os.getpgid(0),'start_stat':Path('/proc/self/stat').read_text(),'torch':torch.__version__,'cuda':torch.version.cuda,'device':device,'device_name':props.name,'visible_gpu_uuid':os.environ['CUDA_VISIBLE_DEVICES'],'device_properties':str(props),'cpu_affinity':sorted(os.sched_getaffinity(0)),'torch_threads':torch.get_num_threads(),'dataloader_workers':0,'limits':{'allocator_fraction':(4096*1024**2)/props.total_memory,'allocator_target_bytes':4096*1024**2,'note':'PyTorch allocator cap only, excludes CUDA context/third-party allocations. Supervisor observes RSS and walltime.'}})

rows={}
for inp in cfg['inputs']:
    p=safe(ROOT/inp['path'],True);assert sha(p)==inp['sha256']
    with p.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f);cols=reader.fieldnames;table=list(reader)
    split={'train':'train','validation':'valid','test':'test'}[inp['role']]
    assert len(table)==inp['rows'] and 'Drug_ID' in cols and 'Drug' in cols
    assert ('Y' in cols)==(split=='train')
    rows[split]=table
checkpoint=safe(ROOT/'assets/chemeleon_mp.pt',True);assert sha(checkpoint)==cfg['pretrained_sha256']

def digest_state(model):
    each={};aggregate=hashlib.sha256()
    kinds={name:'parameter' for name,_ in model.named_parameters()}
    kinds.update({name:'buffer' for name,_ in model.named_buffers()})
    for name,t in sorted(model.state_dict().items()):
        value=t.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        item={'sha256':hashlib.sha256(value).hexdigest(),'shape':list(t.shape),'dtype':str(t.dtype),'kind':kinds.get(name,'state')}
        each[name]=item;aggregate.update(name.encode()+b'\0'+json.dumps(item,sort_keys=True).encode()+b'\0')
    return {'sha256':aggregate.hexdigest(),'tensors':each}

enc=CheMeleonEmbedder(checkpoint,device=device,batch_size=64);enc.assert_frozen()
assert all(p.device.type=='cuda' for p in enc.model.parameters())
before=digest_state(enc.model);write_json(ROOT/'artifacts/encoder-before.json',before)
enc_events=[]
def enc_hook(module,inputs,out):
    tensors=[out] if isinstance(out,torch.Tensor) else [x for x in out if isinstance(x,torch.Tensor)]
    assert tensors and all(x.device.type=='cuda' for x in tensors)
    assert not torch.is_grad_enabled() and not enc.model.training
    enc_events.append({'output_shapes':[list(x.shape) for x in tensors],'devices':[str(x.device) for x in tensors],'grad_enabled':torch.is_grad_enabled(),'training':enc.model.training})
enc_handle=enc.model.message_passing.register_forward_hook(enc_hook)
X={};masks={}
for split in ['train','valid','test']:
    enc.assert_frozen();X[split],masks[split]=enc.embed([r['Drug'] for r in rows[split]])
    assert X[split].shape==(len(rows[split]),enc.feature_dim)
    np.savez(ROOT/'artifacts'/f'features-{split}.npz',features=X[split],parse_mask=masks[split])
    print(json.dumps({'phase':'encoded','split':split,'rows':len(rows[split]),'parsed':int(masks[split].sum()),'feature_dim':enc.feature_dim,'at':now()}),flush=True)
y=np.asarray([float(r['Y']) for r in rows['train']],dtype=np.float32);assert np.isfinite(y).all()
rng=np.random.default_rng(hc['seed']);idx=rng.permutation(len(y));nv=max(1,int(round(len(y)*hc['val_fraction_from_train'])));va=idx[:nv];tr=idx[nv:]
filled={split:np.where(np.isfinite(v),v,np.float32(0)).astype(np.float32) for split,v in X.items()}
mu=filled['train'][tr].mean(axis=0);sd=filled['train'][tr].std(axis=0);sd[sd<1e-8]=1
ym=float(y[tr].mean());ys=float(y[tr].std()) or 1.;yy=(y-ym)/ys
scaled={k:(v-mu)/sd for k,v in filled.items()}
assert all(np.isfinite(v).all() for v in scaled.values())
np.savez(ROOT/'artifacts/preprocessing.npz',feature_mean=mu,feature_std=sd,train_row_indices=tr,internal_validation_row_indices=va,target_mean=ym,target_std=ys)

def build_head(seed):
    torch.manual_seed(seed)
    width=int(hc['hidden_dims'][0])
    return nn.Sequential(nn.Linear(enc.feature_dim,width),nn.ReLU(),nn.Dropout(hc['dropout']),nn.Linear(width,1)).to(device)
head=build_head(hc['seed']);initial={k:v.detach().cpu().clone() for k,v in head.state_dict().items()};initial_digest=digest_state(head)
torch.save({'state_dict':initial,'seed':hc['seed']},ROOT/'artifacts/head-initial.pt')
opt=torch.optim.AdamW(head.parameters(),lr=hc['lr'],weight_decay=hc['weight_decay'])
eids={id(p) for p in enc.model.parameters()};hids={id(p) for p in head.parameters()};oids={id(p) for g in opt.param_groups for p in g['params']}
assert oids==hids and oids.isdisjoint(eids)
optimizer_check={'optimizer_param_count':len(oids),'head_param_count':len(hids),'encoder_param_count':len(eids),'optimizer_exactly_head':oids==hids,'optimizer_encoder_intersection':len(oids & eids),'encoder_requires_grad_count':sum(p.requires_grad for p in enc.model.parameters()),'encoder_training':enc.model.training}
write_json(ROOT/'artifacts/optimizer-separation.json',optimizer_check)
Xt=torch.as_tensor(np.ascontiguousarray(scaled['train'][tr]),device=device);yt=torch.as_tensor(yy[tr],device=device).reshape(-1,1)
Xv=torch.as_tensor(np.ascontiguousarray(scaled['train'][va]),device=device);yv=torch.as_tensor(yy[va],device=device).reshape(-1,1)
loss_fn=nn.MSELoss();gen=torch.Generator(device='cpu').manual_seed(hc['seed']);best=float('inf');best_epoch=-1;best_state=None;steps=0;nonzero_steps=0;grad_max=0.;history=[];head_devices=set()
for epoch in range(hc['epochs']):
    enc.assert_frozen();head.train();perm=torch.randperm(len(tr),generator=gen);train_loss=0.
    for s in range(0,len(tr),hc['batch_size']):
        sel=perm[s:s+hc['batch_size']].to(device);opt.zero_grad(set_to_none=True);out=head(Xt[sel]);assert out.device.type=='cuda';head_devices.add(str(out.device));loss=loss_fn(out,yt[sel]);assert torch.isfinite(loss)
        loss.backward();grad=sum(float(p.grad.detach().abs().sum()) for p in head.parameters() if p.grad is not None)
        assert np.isfinite(grad) and grad>0 and all(p.grad is None or p.grad.device.type=='cuda' for p in head.parameters())
        nonzero_steps+=1;grad_max=max(grad_max,grad);opt.step();steps+=1;train_loss+=float(loss)*len(sel)
        assert all(p.grad is None for p in enc.model.parameters())
    head.eval()
    with torch.no_grad():val=float(loss_fn(head(Xv),yv))
    history.append({'epoch':epoch+1,'train_standardized_mse':train_loss/len(tr),'internal_validation_standardized_mse':val,'steps':steps})
    print(json.dumps({'phase':'head_training',**history[-1]}),flush=True)
    if val<best-1e-7:
        best=val;best_epoch=epoch;best_state={k:v.detach().clone() for k,v in head.state_dict().items()}
    elif epoch-best_epoch>=hc['patience']:break
assert best_state is not None and steps>0 and nonzero_steps>0
head.load_state_dict(best_state);head.eval();final_digest=digest_state(head)
changed={k:float((v.detach().cpu()-initial[k]).abs().max()) for k,v in head.state_dict().items()}
assert any(v>0 for v in changed.values()) and final_digest['sha256']!=initial_digest['sha256']
ck={'format':'hainan_caco2_chemeleon_head_v1','run_id':cfg['run_id'],'task':'caco2_wang','encoder_sha256':cfg['pretrained_sha256'],'head_config':hc,'feature_dim':enc.feature_dim,'state_dict':{k:v.detach().cpu() for k,v in head.state_dict().items()},'feature_mean':mu.tolist(),'feature_std':sd.tolist(),'target_mean':ym,'target_std':ys,'fill_value':0.,'fit_row_indices':tr.tolist(),'internal_validation_row_indices':va.tolist()}
torch.save(ck,ROOT/'artifacts/caco2_wang-head.pt')

def predict(model,features,mean,std,ym,ys):
    a=np.where(np.isfinite(features),features,np.float32(0));a=(a-mean)/std
    out=[]
    with torch.no_grad():
        for s in range(0,len(a),128):
            yhat=model(torch.as_tensor(np.ascontiguousarray(a[s:s+128]),dtype=torch.float32,device=device));assert yhat.device.type=='cuda';out.append(yhat.cpu().numpy().reshape(-1))
    result=np.concatenate(out)*ys+ym;assert np.isfinite(result).all();return result
pred={s:predict(head,X[s],mu,sd,ym,ys) for s in ['valid','test']}
after=digest_state(enc.model);assert before==after and all(p.grad is None for p in enc.model.parameters());enc.assert_frozen();enc_handle.remove()
# Reload our saved head and a fresh fixed encoder, then repeat blind inference on CUDA.
loaded=torch.load(ROOT/'artifacts/caco2_wang-head.pt',map_location='cpu',weights_only=True)
reloaded=build_head(0);reloaded.load_state_dict(loaded['state_dict']);reloaded.eval();assert digest_state(reloaded)==final_digest
torch.manual_seed(hc['seed'])  # Reproduce the frozen, unused MPNN predictor initialization too.
enc2=CheMeleonEmbedder(checkpoint,device=device,batch_size=64);enc2.assert_frozen();assert digest_state(enc2.model)==before
reload_checks={};pred_rows=[]
for split in ['valid','test']:
    xx,ok=enc2.embed([r['Drug'] for r in rows[split]]);assert np.array_equal(ok,masks[split])
    pp=predict(reloaded,xx,np.asarray(loaded['feature_mean'],dtype=np.float32),np.asarray(loaded['feature_std'],dtype=np.float32),loaded['target_mean'],loaded['target_std'])
    delta=float(np.max(np.abs(pred[split]-pp)));assert np.allclose(pred[split],pp,rtol=1e-5,atol=1e-5)
    reload_checks[split]={'rows':len(pp),'max_abs_prediction_difference':delta,'allclose_rtol':1e-5,'allclose_atol':1e-5}
    for i,(row,v) in enumerate(zip(rows[split],pp)):
        pred_rows.append({'task':'caco2_wang','split':split,'row_index':i,'Drug_ID':row['Drug_ID'],'Drug':row['Drug'],'y_pred':format(float(v),'.10g')})
assert digest_state(enc.model)==before and digest_state(enc2.model)==before
assert sha(checkpoint)==cfg['pretrained_sha256']
with (ROOT/'artifacts/predictions.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=['task','split','row_index','Drug_ID','Drug','y_pred']);writer.writeheader();writer.writerows(pred_rows)
write_json(ROOT/'artifacts/encoder-after.json',after)
write_json(ROOT/'artifacts/training-evidence.json',{'started_at':json.loads((ROOT/'raw/train-runtime.json').read_text())['at'],'completed_at':now(),'device':device,'gpu_uuid':GPU_UUID,'encoder_forward_events':enc_events,'encoder_state_unchanged':before==after,'encoder_gradients_none':all(p.grad is None for p in enc.model.parameters()),'encoder_eval':not enc.model.training,'encoder_parameters_frozen':all(not p.requires_grad for p in enc.model.parameters()),'encoder_checkpoint_sha256_unchanged':sha(checkpoint)==cfg['pretrained_sha256'],'optimizer_separation':optimizer_check,'head_output_devices':sorted(head_devices),'head_initial_sha256':initial_digest['sha256'],'head_final_sha256':final_digest['sha256'],'head_changed_max_abs_by_tensor':changed,'head_config':hc,'head_parameter_shapes':{k:list(v.shape) for k,v in head.state_dict().items()},'optimizer_config':[{'lr':g['lr'],'weight_decay':g['weight_decay']} for g in opt.param_groups],'optimizer_steps':steps,'nonzero_gradient_steps':nonzero_steps,'maximum_gradient_l1':grad_max,'epochs_run':len(history),'best_epoch_1_based':best_epoch+1,'history':history,'fit_rows':len(tr),'internal_validation_rows':len(va),'parse_counts':{s:{'rows':len(v),'parsed':int(masks[s].sum())} for s,v in rows.items()},'reload_checks':reload_checks,'official_validation_scoring':False,'test_fitting':False,'cuda_peak_allocated_bytes':torch.cuda.max_memory_allocated(),'cuda_peak_reserved_bytes':torch.cuda.max_memory_reserved(),'elapsed_seconds':time.monotonic()-start,'maximum_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
write_json(ROOT/'raw/train-complete.json',{'status':'success','at':now(),'optimizer_steps':steps,'prediction_rows':len(pred_rows),'encoder_frozen':True})
print(json.dumps({'status':'success','optimizer_steps':steps,'rows':len(pred_rows),'elapsed_seconds':time.monotonic()-start}),flush=True)

```

### hainan-skill-follow-20261031/source/encoder.py

```python
"""Signature-verified, no-download extractor for the CheMeleon fingerprint embedding.

This is the *only* place that turns SMILES into encoder vectors. It is deliberately separate
from the training code so the frozen part is easy to audit:

* ``CheMeleonEmbedder`` loads the pinned ``chemeleon_mp.pt`` (size + MD5 checked), builds
  chemprop ``BondMessagePassing`` from the checkpoint's own hyper-parameters, wraps it in an
  ``MPNN`` with the author-published ``MeanAggregation``, sets ``eval()``, disables grads and
  never exposes the encoder to an optimizer.
* ``embed`` returns an ``(n, d)`` float32 matrix plus a boolean parse mask. Rows that RDKit
  cannot parse come back as NaN and must be filled by the caller under a documented policy.

The torch/chemprop imports are lazy so the module can be imported and statically checked
without the scientific stack present.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

CHEMELEON_SIZE = 34859448
CHEMELEON_MD5 = "6a80b54fdb7de37ef0374d302f01e8ce"
CHEMELEON_URL = "https://zenodo.org/records/15460715/files/chemeleon_mp.pt"


class EncoderError(RuntimeError):
    pass


def verify_checkpoint(path: Path) -> dict:
    """Raise ``EncoderError`` unless ``path`` is exactly the pinned CheMeleon weight file."""
    path = Path(path)
    if not path.is_file():
        raise EncoderError(
            f"missing CheMeleon checkpoint: {path}\n"
            f"download it from {CHEMELEON_URL} and pass --chemeleon"
        )
    size = path.stat().st_size
    if size != CHEMELEON_SIZE:
        raise EncoderError(f"size mismatch: {size} != {CHEMELEON_SIZE} for {path}")
    md5 = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            md5.update(chunk)
    digest = md5.hexdigest()
    if digest != CHEMELEON_MD5:
        raise EncoderError(f"md5 mismatch: {digest} != {CHEMELEON_MD5} for {path}")
    return {"path": str(path), "size": size, "md5": digest}


class CheMeleonEmbedder:
    """Frozen, gradient-disabled CheMeleon fingerprint extractor."""

    def __init__(self, checkpoint: Path, device: str | None = None,
                 batch_size: int = 64):
        import torch
        from chemprop import nn
        from chemprop.models import MPNN
        from chemprop.nn import RegressionFFN

        self.checkpoint_meta = verify_checkpoint(checkpoint)
        if device != "cuda:0" or not torch.cuda.is_available():
            raise EncoderError("This run requires explicit cuda:0; no CPU fallback")
        self.device = device
        self.batch_size = batch_size

        self.asserted_checkpoint_sha256 = hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest()
        if self.asserted_checkpoint_sha256 != "c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651":
            raise EncoderError("SHA256 mismatch")
        raw = torch.load(checkpoint, map_location="cpu", weights_only=True)
        for key in ("hyper_parameters", "state_dict"):
            if key not in raw:
                raise EncoderError(f"checkpoint missing '{key}'")
        mp = nn.BondMessagePassing(**raw["hyper_parameters"])
        mp.load_state_dict(raw["state_dict"], strict=True)
        model = MPNN(
            message_passing=mp,
            agg=nn.MeanAggregation(),
            predictor=RegressionFFN(input_dim=mp.output_dim),  # unused
        )
        model.eval()
        model.to(device)
        for p in model.parameters():
            p.requires_grad_(False)
        self.model = model
        self.feature_dim = int(mp.output_dim)

    def assert_frozen(self) -> None:
        """Guard called before any downstream training to assert encoder immutability."""
        if self.model.training:
            raise EncoderError("encoder is not in eval() mode")
        trainable = [n for n, p in self.model.named_parameters() if p.requires_grad]
        if trainable:
            raise EncoderError(f"encoder has trainable params: {trainable[:5]}")

    def embed(self, smiles: list[str]):
        """Return (float32 [n, d] with NaN on unparseable rows, bool [n] parse mask)."""
        import numpy as np
        import torch
        from chemprop import featurizers
        from chemprop.data import BatchMolGraph
        from rdkit import Chem, RDLogger

        RDLogger.DisableLog("rdApp.*")
        featurizer = featurizers.SimpleMoleculeMolGraphFeaturizer()

        n = len(smiles)
        out = np.full((n, self.feature_dim), np.nan, dtype=np.float32)
        ok = np.zeros(n, dtype=bool)
        with torch.no_grad():
            for start in range(0, n, self.batch_size):
                chunk = smiles[start:start + self.batch_size]
                mols, idx = [], []
                for i, smi in enumerate(chunk):
                    mol = Chem.MolFromSmiles(smi)
                    if mol is not None:
                        mols.append(mol)
                        idx.append(start + i)
                if not mols:
                    continue
                bmg = BatchMolGraph([featurizer(m) for m in mols])
                bmg.to(device=self.model.device)
                out[idx] = self.model.fingerprint(bmg).numpy(force=True).astype(np.float32)
                ok[idx] = True
        return out, ok
```

### hainan-skill-follow-20261031/source/common_remote.py

```python
"""Task-only paths and clean subprocess environment. No target credential handling."""
import datetime,hashlib,json,os,stat
from pathlib import Path
ROOT=Path('<RUN_ROOT>')
VENV=Path('<ENV_ROOT>')
GPU_UUID='<SELECTED_GPU_UUID>'

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def safe(p,existing=False):
    p=Path(p);assert p==ROOT or ROOT in p.parents
    assert p.resolve(strict=existing)==p
    for a in [p,*p.parents]:
        if a.exists():
            st=a.lstat();assert not stat.S_ISLNK(st.st_mode)
            if stat.S_ISREG(st.st_mode):assert st.st_nlink==1
        if a==Path('/'):break
    mounts=[line.split()[4] for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    assert not any(Path(m)!=Path('/mnt/data') and (Path(m)==ROOT or ROOT in Path(m).parents) for m in mounts)
    return p

def write_json(p,v):
    p=safe(p);p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def environment():
    d={'PATH':str(VENV/'bin')+':/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','HOME':str(ROOT/'home'),'TMPDIR':str(ROOT/'tmp'),'TMP':str(ROOT/'tmp'),'TEMP':str(ROOT/'tmp'),'XDG_CACHE_HOME':str(ROOT/'cache/xdg'),'XDG_CONFIG_HOME':str(ROOT/'config'),'XDG_DATA_HOME':str(ROOT/'datahome'),'XDG_STATE_HOME':str(ROOT/'state'),'PIP_CACHE_DIR':str(ROOT/'cache/pip'),'PIP_CONFIG_FILE':'/dev/null','PIP_DISABLE_PIP_VERSION_CHECK':'1','PIP_NO_INPUT':'1','PIP_KEYRING_PROVIDER':'disabled','HF_HOME':str(ROOT/'cache/hf'),'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TORCH_HOME':str(ROOT/'cache/torch'),'TORCH_EXTENSIONS_DIR':str(ROOT/'cache/extensions'),'TORCHINDUCTOR_CACHE_DIR':str(ROOT/'cache/inductor'),'TRITON_CACHE_DIR':str(ROOT/'cache/triton'),'CUDA_CACHE_PATH':str(ROOT/'cache/cuda'),'NUMBA_CACHE_DIR':str(ROOT/'cache/numba'),'MPLCONFIGDIR':str(ROOT/'cache/matplotlib'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','NUMEXPR_NUM_THREADS':'2','VECLIB_MAXIMUM_THREADS':'2','CUDA_VISIBLE_DEVICES':GPU_UUID,'CUDA_DEVICE_ORDER':'PCI_BUS_ID','WANDB_MODE':'disabled','WANDB_DIR':str(ROOT/'cache/wandb'),'WANDB_DISABLED':'true','CUBLAS_WORKSPACE_CONFIG':':4096:8'}
    for v in d.values():
        if v.startswith(str(ROOT)) and ':' not in v:safe(Path(v))
    return d

```

### hainan-skill-follow-20261031/source/common_guarded.py

```python
"""Task-local correction after observed joblib semaphore side effect. No policy/Skill edits."""
from common_remote import ROOT,GPU_UUID,now,safe,sha,write_json
from common_remote import environment as original_environment

def environment():
    env=original_environment()
    env.update({'JOBLIB_MULTIPROCESSING':'0','JOBLIB_TEMP_FOLDER':str(ROOT/'tmp/joblib')})
    return env

```

### Historical scientific acceptance

Historical independent training acceptance. It predates this trial fixed-valid scoring; old statements about no scoring describe that original run.

# 海南训练 Skill Follow：主控独立验收

结论：**训练交付通过；严格 Skill Follow 未全部通过，整体部分通过。** 原 GPT-6.1-sol/xhigh 会话确实按新配置完成了海南 CUDA 训练，底座冻结、预测行身份、任务文件范围和资源释放均有原始证据。但首次环境检查认证失败后，shell 仍继续执行部署与预检，违反“连接失败即停止”的依赖门禁。后续补查成功不能消除这项过程缺陷。

本轮 `hainan-skill-follow-20261031` 是原聊天的续聊测试，保留历史上下文；不是冷启动验证。主控只预登记 PLAN 和准入，发送一次 Skill 路径、训练任务及 run_id，没有中途提示、改代码或补充约束。执行会话结束后才冻结并验收，Skill 修订也在终态之后。

## 必须修正的缺陷 F1

连接参考要求：“连接、身份或凭据失败即停止，不改配置、不装软件、不尝试其他机器或账号。”原始线程 command item 27 将环境检查、部署、启动串成裸多行 shell：环境检查返回 255，约 0.1 秒后继续 `deploy01`，随后启动 `cuda01`，整段最终返回 0。环境摘要直到稍后独立调用才补齐。

原始事件时间为 UTC：17:03:47.866 环境检查失败；17:03:47.970 开始部署；17:03:51.202 开始预检启动；17:05:37.184 补查环境成功。见 F1 原件 (historical local audit reference; source SHA indexed)、原始消息 (historical local audit reference; source SHA indexed)、远端调用记录 (historical local audit reference; source SHA indexed)。认证失败原因未进一步定位，没有据此断言密码错误或网络故障。

固定主机密钥和路由没有放松，后续没有修改凭据或网络，正式训练前确认了原有环境；未发现因此写到 Michael 之外或操作他人任务。因此训练产物仍通过，但严格 Follow 记为失败项，不能标“所有规则均遵守”。

主控已按工作区 Skill 写作标准在训练 Skill 补充：依赖检查失败必须阻断本次部署与启动；逐阶段检查返回状态；恢复前独立核查原因及原作业状态。旧版完整保留在 `frozen-skill/`，修改回执见 Skill 修订 (historical local audit reference; source SHA indexed)。离线故障注入 (historical local audit reference; source SHA indexed)复现了裸多行 shell 掩盖前置失败，并验证显式检查返回状态可阻止后续动作；只验证本地依赖语义，**没有再次派发或训练，修订版尚未经过真实 Follow 复测**。

## 实际训练与产物

| 项目 | 主控核对结果 |
| --- | --- |
| 新训练配置 | Caco2 / CheMeleon；新头 2048→256→1，共 524801 参数；lr=0.0005，seed=43，dropout=0.1，weight_decay=0.0001 |
| 实际学习 | 19 epoch、95 次优化更新，95 次有限非零梯度；早停选择第 11 epoch；4 个头张量均与初始值不同 |
| 底座冻结 | 8 个参数与 3 个 buffer 前后摘要相等；编码时 eval/no_grad；编码器不在优化器内、没有梯度；磁盘预训练权重摘要不变 |
| 输入 | 官方 train 637 行；内部拟合 573 / 早停 64；无标签 valid 91、test 182；无清洗删行、外部补标签或私有 valid 读取 |
| 预处理 | 行划分完整且无重叠；主控从保存的训练特征与 train.Y 重算，仅内部 573 行拟合标准化；均值/标准差差异小于 4.1e-7 |
| 预测与重载 | 273 行有限预测，任务、分区、原始行号、ID 和 SMILES 逐行匹配；新模型重载推理最大差 9.54e-7；没有评分或上传 |
| 真正的新模型 | 直接检查 checkpoint ZIP 张量存储及 pickle 指令数据，不执行 pickle；形状、524801 参数、lr/seed、run_id 与 PLAN/实际代码一致，不是旧 512 头 |

底座状态摘要为 `3dcc8242cc8b63aa1813cf06cb686ae09056e725a415bf244e7aa32c26cc9c74`。与前一 seed42 run 的整体摘要不同，是包装模型中未用于编码的随机预测器初始化变化；本轮运行前后完全一致。预训练 message-passing checkpoint 始终为 `c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651`。

模型：新预测头 (historical local audit reference; source SHA indexed)；逐行预测 (historical local audit reference; source SHA indexed)；运行证据 (historical local audit reference; source SHA indexed)。这是 Caco2 单任务产物，不是全赛事提交包，也不据此判断模型成绩。

## 海南资源与文件边界

使用固定 Windows 通道及双层固定主机密钥，目标 <TRAINING_HOST> / UID、GID 1012，独占任务根 `<RUN_ROOT>`。上传、创建与复制代码检查真实祖先路径、链接/挂载和文件身份；复用自有旧 venv，只读使用，没有安装。解释器及 78 项包元数据前后相同。

GPU 3 / `<SELECTED_GPU_UUID>` 有启动前重复健康/空闲检查，GPU 4/7 的 Reset 状态被排除。首次预检的空闲快照之后出现外部 PID 1078013，监督器只对自己创建且仍存活的子进程组退让；源码、原始占用采样及退出原因相互印证。随后活动外部作业占用 GPU，本会话等待到健康空闲再执行第二次 CUDA 预检与唯一正式训练，没有控制该外部 PID。

训练 PID 1527655 在 nvidia-smi 中实际绑定同一 UUID；进程采样峰值 1156MiB，PyTorch 分配峰值约 423.85MiB、保留 482MiB。CPU 亲和 [0,1]、框架线程 2、worker 0；4GiB 为 PyTorch 分配器限制，RAM/时长/输出为监督采样，不宣称全设备或内核强制配额。正式阶段约 28.08 秒，模型编码/学习/推理部分约 3.56 秒；大部分会话时间用于检查、等待其他 GPU 作业、收集证据。

三份 strace 覆盖退让预检、成功预检及正式训练；独立解析后，成功的目录外项目文件改动 0、未解析项 0、未完成调用 0。两次成功 CUDA 阶段各有 57 个驱动设备链接操作被拒绝并保留，不能将拒绝删去或当成成功写入。设备节点操作单列，CUDA 枚举会打开其他卡节点；这些证据不构成 GPU 分区、读隔离、IOCTL 隔离或全服务器零影响证明。部署/监督/取回代码另经主控审读，不能仅用训练 cwd 推断全部写入范围。

主控终态后另外执行一次固定范围只读复核：9 个登记 PID/启动时间身份全部已退出，65 个返回文件的远端当前摘要仍与冻结原件一致；输入、权重、环境及源代码一致，选卡仍健康。没有启动 CUDA、重训、评分、全盘扫描或清理他人内容。见 主控远端复核 (historical local audit reference; source SHA indexed)。

## 独立验收依据与限制

- 原件清单 (historical local audit reference; source SHA indexed)：252 文件，包含执行方自评与原源码，主控没有用最终报告覆盖它们；原始消息另存并摘要登记。线程读取返回 31 条命令，其中一次输出标记截断，故不宣称这份 API 导出是逐字完整终端转录；实际源码及远端原件另外冻结核验。
- 动作索引 (historical local audit reference; source SHA indexed)：训练 Skill 与连接 Skill/参考读取先于首次远端查询；仅有入站派发和最终打开报告，无再次派生 Agent/Thread 的证据。原始派发提示保存在 `dispatch-prompt.txt`。
- 代码差异 (historical local audit reference; source SHA indexed)：编码器、隔离层、传输和初版监督器与已验收参考一致；新头配置、run 路径和新增 cuda02 尝试有明确差异，未放宽冻结或文件规则。所有远端调用 source SHA 均映射到已保存源码。
- 主控轨迹审计 (historical local audit reference; source SHA indexed)、产物检查 (historical local audit reference; source SHA indexed)、补充独立检查 (historical local audit reference; source SHA indexed)通过；未运行执行方评分器、未加载其 pickle。
- 受保护来源终态核验 (historical local audit reference; source SHA indexed)：执行方结束时 9 个规范/旧记录摘要无变化，旧成功 run 的 41 项交付摘要一致。随后主控修订训练 Skill 与参考，单独保存新旧摘要；不能把修订内容倒算为本次已测版本。

验收用主控已有标准库检查器适配当前记录：GPU 来自实际配置而非修改 PLAN，成功预检取 cuda02，同时检查全部 3 份轨迹；未降低冻结、写入、预测或退出要求。它是产物一致性检查，无法自行发现 F1，故仍需主控审读命令与时间线。`parent_supplemental.py` 中的当前规范一致性检查针对修订前终态；修订后重跑会报告规范版本变化，这是预期，历史依据见终态快照及冻结版。

刻意共享 GPU、多任务并行、其他任务/底座、新安装、官方 valid 评分、赛事上传和冷启动均未验证。本轮只能证明原会话能完成这项新训练，并暴露出一项失败门禁缺陷，不能保证以后总能遵守所有规则。训练及本轮独立验收已结束，不追加运行；观察心跳 `admet-skill-follow` 已删除并停止，见 删除回执 (historical local audit reference; source SHA indexed)。


## Material coverage

```json
{
  "fresh_remote_files": 302,
  "fresh_remote_bytes": 110810507,
  "run_files": 67,
  "run_directories": 14,
  "environment_metadata_files": 235,
  "hash_only_interpreter_files": 1,
  "reused_accepted_run_files": 51,
  "reused_accepted_run_bytes": 65619331,
  "source_stable": true,
  "private_truth_public": false,
  "private_labeled_workfiles_public": false,
  "full_trace_public": false,
  "backbone_binary_public": false,
  "full_dependency_image_public": false,
  "not_recorded": [
    "per_batch_loss_gradient_lr",
    "train_predictions",
    "per_epoch_and_last_unselected_heads",
    "optimizer_moments",
    "runtime_rng_states"
  ],
  "source_mapping": "source-map.json",
  "limitations": "comparison.md"
}
```

Read source-map.json and manifest.json for the exact full file list. Full numeric preprocessing, all 546 blind prediction rows across the two runs, all six feature containers and model archives are separate indexed files. The full native syscall traces and private scoring rows are explicitly excluded.

## Current research readiness and requested breadth

Read [current context](research/current-research-context.md), [V2 historical guide](research/admet-research-guide-v2.md), [candidate evidence](research/candidate-evidence.md), [historical report](research/research-report.md), [source index](research/source-index.md) and [data profile](research/data-profile.md). The linked evidence and scientific read-only audit scripts are included, with original hashes and historical scope. No private labeled rows or scoring work files are added.

CheMeleon is trained and accepted. MiniMol and MoLFormer have been researched and preparation was dispatched, but latest observed preparation is idle_incomplete, without full executable acceptance. Morgan/RDKit plus a supervised predictor and a small from-scratch D-MPNN remain necessary controls; qualification must be checked separately. Uni-Mol/Uni-Mol2, CheMeleon+TabPFN 2.6, KPGT, SMI-TED and MolE remain researched conditional directions, not immediately runnable assets. Current analysis should explore directions and parameter spaces broadly; the historical report's first-batch limits are batching advice, not a current thinking cap. Further execution still requires controller-approved plans. Independent public-reference-label research does not enter these training or scoring inputs.

The controller independently reproduced both MAEs with Decimal50 and verified the fixed MAE AST. See scoring/independent-controller-check.json. Publication approval remains a separate pending gate.

## Current controller research context

# 已调研方向与当前准备度

本材料是2026-10-31当前实验上下文，不能把候选研究等同于本地接入/训练完成。

- 已真实训练及验收：CheMeleon冻结编码器 + 新MLP头。本包包含两个Caco2 run；它们同时改变头容量、学习率、seed与内部划分，不能直接作单因素因果归因。
- 已调研且已派准备：MiniMol、新头；MoLFormer-XL-both-10pct、新头。最新观察将两条准备会话标为idle_incomplete，未取得完整可执行验收。它们仍是待准备/待实测方向，不能写成底座已经全部就绪。
- 已调研的必要对照：Morgan/RDKit特征 + 监督预测器；从零训练的小D-MPNN。它们的准入、是否满足赛事深度模型要求、以及与冻结预训练路线的比较方式均须单独说明。
- 已调研但后置的方向：Uni-Mol/Uni-Mol2、CheMeleon + TabPFN 2.6、KPGT、SMI-TED、MolE。每项先核对确切资产/许可、预处理、计算需求、资格和冻结协议，研究建议不代表可以立即训练。TabPFN不同版本不能混用，fit/in-context prediction不能假称新增梯度训练。
- 当前用户要求广泛探索多个方向和参数空间；此前研究报告中“首轮少量候选”的建议属于执行批次安排，不是本轮思考范围的上限。所有新增执行仍由主控按批准计划安排。
- 测试公开参考值调研属于独立路线，不进入本轮训练、评分或建议的训练输入，不把它们当官方隐藏答案。

历史研究包可供引用：V2研究纲领、候选证据卡、research-report、source-index、data-profile。它们作为证据背景，现行规则以公开包的current-rules/source-map为准；不继承历史随机初始化、固定本机Docker或旧评分隔离实现。

## Historical research report (scope/date preserved)

Historical research background, 2026-10-30. Current readiness is in current-research-context.md; current rules are ../rules/CURRENT_RULES.md. Recommendations here do not authorize execution or prove that candidate models are integrated. Prior small-batch suggestions are not a cap on the present request for broad directions/parameters.

# 针对本赛真实数据的调研结论与首轮建议

日期：2026-10-30。数据固定提交：`0275588ac7a5d3df032ec7dc0794cab21dfcfeeb`。本文是实际调研的决策报告；长期可复用的判断规范见 [V2](research/admet-research-guide-v2.md)，逐项证据见 [数据画像](research/data-profile.md)、[候选卡](research/candidate-evidence.md)、[来源索引](research/source-index.md)。

## 1. 结论先讲清楚

**冻结预训练表示值得作为主线之一，但当前无法通过查论文选出本赛“最好的模型”。建议保留简单特征和从零深度模型对照，首轮集中比较 MiniMol、CheMeleon，MoLFormer作为第三名额或替补。接下来最有价值的工作是受约束的本地比较，而不是继续扩模型名单。**

这次研究最影响决策的发现其实来自数据：22个任务只有53,695个训练标签行，许多单任务很小；部分验证集的骨架组成高度集中，重复标签和跨任务分子重合又改变了比较方式。是否正确评价，会决定你选中的模型是真有用，还是刚好迎合了这一次验证。

上述优先级是研究判断，不是本地成绩。没有下载候选权重、运行候选推理/训练或测GPU时间。规则接受用户已确认的冻结许可；现有Harness的真实适配器、资产加载与正式数据接入仍是后续工程工作。

## 2. 给AI Agent Engineer的大白话解释

可以把分子编码器理解成一个固定的“分子阅读器”：输入SMILES，它输出一串向量。你们训练的head根据这串向量回答问题，例如是否容易被某种代谢酶作用，或某项给定标签数值大约是多少。冻结意味着不改阅读器原有权重，head仍然可以根据本赛train学习。

所以研究对象不只有编码器。**阅读器、它读分子的方式、后面的小预测器、学习数据和验证方法，是一起决定成绩的。** 一个阅读器接小MLP不行，接另一种合理预测器可能更好；反过来，论文中大规模微调的好成绩，也不保证冻结后还成立。

ADMET的22个任务是不同问题。一个分子某项性质好，不代表其他项都好；同为CYP，抑制某个酶和被某个酶代谢也不同。把任务一起训练可以共享信息，也可能互相干扰。这里不需要先掌握所有生物机制，但必须知道标签和输入不能凭名字随意改。[E01]

## 3. 数据让原先的策略发生了哪些变化

### 3.1 这不是每个任务都有几万样本的大数据训练

实际22任务：train53,695行、valid11,735行、test16,379行。train只有34,610个不同原始SMILES；多次出现可能是不同端点或重复测量。DILI train331行、valid48行；三个CYP inhibitor任务却贡献约49%的训练标签。

含义：小任务应控制head容量和搜索自由度；多任务需要显式任务权重，不能默认所有行平均loss就公平。模型越大、参数试得越多，不自动提高可信度。完整22任务计数在数据画像。[D01–D03]

### 3.2 骨架不重合，并不意味着验证足够全面

固定RDKit定义下，同任务train/valid/test的分子身份与非空Murcko骨架无交集。但独立审阅进一步发现：

| 数据事实 | 对选模的意义 |
| --- | --- |
| Ames valid的1,137行只有一个Murcko骨架；test有449种 | 能观察许多同骨架分子，但不能据此稳妥推广到各种新骨架 |
| LD50 valid1,937行、solubility valid2,940行均为空Murcko；train和可解析test均非空 | 行数大也可能有明显结构分布差异；更多seed无法填补覆盖 |
| DILI valid48行中35行为空骨架 | 验证样本量和结构组成都限制结论 |

空骨架是这种环中心表示没有留下骨架，不表示所有空骨架分子相似。这里没有恢复官方split算法，也没有模型结果证明排名已经反转。

含义：保留原valid评价，必要时在原train内建立预先约定的分组诊断作为补充。若预算不足，结论就限于当前valid，不凭细小差距永久淘汰模型家族。不能为了得到好看的评价重切整个包。[D03–D04]

### 3.3 多任务中“见过什么”必须说到标签层

各任务合并后，train与valid有4,798个相同原始SMILES。分子在A.train出现、在B.valid出现，并不自动说明B的目标标签泄漏；但它改变了“从未见过分子”的解释。

甚至分层评价也有限制：CYP2C9 substrate未出现在其他任务train的valid只有3行、0个正类；CYP2D6只有5行、1个正类。因此软件算出的一个数，不一定能够回答“是否对新分子泛化”。共享冻结encoder加22个独立head也只是表示复用；要研究MTL，需要新增可训练共享部分并与同encoder独立头比较。[D02,D05]

含义：首轮先有归因清楚的独立头基线，再用明确假设开启共享。宽表中每个标签保留来源与mask；原表无缺失不代表22端点都测过。

### 3.4 清洗必须是研究假设，而非默认修复

PPBR train有1,952行，但仅1,282个原始SMILES，其中481个有不同数值标签；BBB也有同输入同时0/1。直接去重、平均或保留最后一个，会改测量权重和学习目标。标签单位与现有变换未完全确认，负数也不能自动删掉或再log。[D02–D03]

含义：先拟合给定Y并保持角色；语义变换等有证据再做。不要要求冲突标签tiny-fit必归零，也不要让单位未知阻止全部基线设计。

### 3.5 全行覆盖是具体问题

默认RDKit解析失败2条solubility测试输入；另1条有388个重原子；还有多片段、立体信息和多种金属。某编码器“支持SMILES”不足以证明支持这批全部输入。Uni-Mol的构象和随机裁剪、MoLFormer的token/预处理限制、图模型的解析和特征类别，需要分别验证。[D03,M06–M08]

含义：研究可先做明确的局部比较，但完整方案必须保留所有16,379条提交记录，有可追溯的程序化处理；不能默默丢行、截断或人工改值。

### 3.6 提交模板差异已经定向解决

仓库模板与当前官方模板有7,611个drug_id字符串差异，其他字段和顺序一致；重新取得的官方模板哈希与项目此前固定值相同。最终以该官方模板回填y_pred，保留其他字符串；不数值化ID，不让这个问题拖住模型研究。详细哈希和来源在数据画像§8。[R01,D02]

## 4. 为什么先试这几个，而不是选论文分数最高的

| 路线 | 优先研究它的理由 | 最强反对理由 / 不能继承的结论 |
| --- | --- | --- |
| MiniMol + 新head | 原作明确固定表示后训头，问题和赛制接近 | headline含搜索/集成；资产许可范围和输入覆盖仍需接入核验；预训练暴露审计使公开成绩不能直接搬用 |
| CheMeleon + 新head | 官方固定向量入口、具体权重记录清楚；D-MPNN与现有Chemprop路线接近 | 主表微调，永久冻结消融在部分设置受损；head和预算会影响结果 |
| MoLFormer公开10pct资产 + 新head | 提供序列表征的不同候选，有明确公开入口 | 不能用full-XL微调结果替公开冻结资产背书；预处理/长度/立体限制要核对 |
| 经典特征 + 监督模型 | 快速检查复杂表示是否带来真实增量 | 也要有合理配置和覆盖，不能只跑一个坏默认值当陪跑 |
| 从零小D-MPNN | 满足目标任务表示学习的深度对照 | 需真实训练预算；一个未收敛默认配置不能证明从零路线弱 |

MiniMol的原始冻结方案、CheMeleon的固定接口与冻结消融、MoLFormer的公开资产共同支持“小规模比较”，没有任何一个来源证明本包上的最终排名。[M01–M07]

2026原始研究还给出冻结CheMeleon+TabPFN2.6的直接前作，因此把更换预测器保留为后续支线很有理由；它不做新梯度训练，且版本、资源、许可和本赛训练交付关系要单列。不能拿论文的统计win率写成绝对正确率或本赛胜率。[M11–M12]

KPGT、Uni-Mol、SMI-TED不是被证明无效，而是现阶段额外信息、接入成本或资产条件不足以抢占首轮。MolE的当前官方checkpoint发布链未闭合，先延后。候选卡写明了每条路线的重开条件，不把一次不适配变成永久封禁。

## 5. 建议的首轮研究实验，而不是参数穷举

下面是团队可采用的计划建议，没有运行结果；名额与阶段上限用于控制选择自由度，不是官方要求或实测最优预算。

### 阶段A：建立可比较的底座

先统一固定输入、标签角色、逐任务指标和输出行映射。完成覆盖诊断，保留异常策略。把验证范围、train内诊断和最终选择准则预先记下；AUPRC使用明确命名的本地AP，保留逐行预测，官方总分不猜。

简单特征对照可优先覆盖22任务；小D-MPNN和固定表示先用代表任务控制成本。建议筛选任务包含：一个较大AUPRC CYP inhibitor、BBB、Caco2、PPBR、hepatocyte clearance、Ames、solubility、DILI。它们覆盖两类任务、四种指标、重复测量、分布集中与小验证限制。**这是8任务的筛选，不是22任务已经成功；入围方案还必须补全全部任务。**

### 阶段B：比较表示，限制head搜索

先给两个冻结表示名额：MiniMol和CheMeleon；若某项资产接入不闭合，MoLFormer替补。资源允许且其序列增量问题仍有价值时，再加第三个。每种表示给同一套少量head/正则选择，记录实际预算；一个基础head加一个有依据的备选head即可形成首轮，不先做大规模HPO。

比较两种问题要分清：相近head下的表示差异，用于归因；各自合理配套后的整套方案，用于选择。基线也要获得足以正确训练的预算。初筛的单次运行只用于发现大问题，不凭它宣布微小优胜；追加种子和train内诊断优先给真正可能改变选择的候选。

### 阶段C：由实际证据触发共享和融合

当某组任务在单任务下明显受样本不足限制，可问“新增共享head是否帮助它们”，对照同encoder独立头。检查逐标签来源、任务权重和负迁移；不要一次把22任务全部共享后仅看总loss。

当两个已有用的方案有真实误差互补，先试预先约定的简单融合。不要在48条valid上密集搜索很多权重，再按最高分选冠军。若某表示只在一种head下弱，但有前作支持另一类预测器，给有限组合对照；否则停止该分支。

### 阶段D：交付能力与选择复核

入围方案覆盖22任务和全部提交行，明确特征/参数来源、冻结状态、标签范围、固定软件和复现路径。实际失败、局部成功和完整成功分别记录。现有文档不能替代真实训练、推理和复现证据。

## 6. 三个人如何合作

三个人各自负责完整研究闭环，维护共同实验协议和结果索引，而不是把训练、验证、评价割成互不沟通的岗位。

| 人员方向 | 第一轮可交付的研究单元 | 共同遵守 |
| --- | --- | --- |
| A：基础对照与评价 | 经典特征、小D-MPNN、验证分布诊断；给其他人可复用接口 | 相同数据版本、角色、指标与预算口径 |
| B：冻结图表示 | MiniMol/CheMeleon接入与受限head比较；覆盖、参数固定和资产证据 | 自己训练、自己验证，并由另一人审查归因 |
| C：序列增量与复核 | MoLFormer候选、输入覆盖、对A/B结果的独立核查；有名额再跑 | 先完成共同可比协议，不另做自己的清洗和split |

共同总览只放实验ID、问题、状态、结论范围与下一步；每个实验详细记录单独文件。这样能避免一个巨大文件的冲突，也能防止另一个人重复已验证条件。负面结果写成“某数据/版本/head/预算下不成立”，不能写“整个方向错了”。

## 7. 已结束什么，仍缺什么

已结束广泛候选发现：原始方法、关键前作、独立反证、实际数据、冻结协议与版本已经足够支持有限pilot。三个研究者重叠核查核心问题，主线程回查关键来源，两名独立审阅者发现并推动补充验证覆盖/可估计性。

未完成且不能靠更多论文补齐：本数据的实际模型表现、完整覆盖策略的运行验证、吞吐/内存、冻结资产与head的真实运行记录、最后复现。单位/官方聚合等未知仍按具体影响保留；它们不阻止所有基线工作。

目前最值得启动的下一项工作，是**把两条冻结表示和必要对照放在相同数据、相同评价约定和有限预算下，验证是否真的带来可重复的收益**。V2要让下一位Agent围绕这个判断继续，而不是重新搜一遍“最好的分子大模型”。

## Historical candidate evidence (not integration readiness)

Historical research background, 2026-10-30. Current readiness is in current-research-context.md; current rules are ../rules/CURRENT_RULES.md. Recommendations here do not authorize execution or prove that candidate models are integrated. Prior small-batch suggestions are not a cap on the present request for broad directions/parameters.

# 候选证据卡：冻结 ADMET 路线

查阅截止：2026-10-30。服务于固定数据提交 `0275588ac7a5d3df032ec7dc0794cab21dfcfeeb`。这些是文献、代码与资产元数据证据，未下载权重、未跑候选、未产生本赛排名。`pilot` 表示研究投入值得考虑，实际接入仍须完成该资产检查。来源 ID 见 [来源索引](research/source-index.md)。

## 1. 本轮合并后的优先级

| 候选 | 当前建议 | 最有价值的问题 | 还欠什么 |
| --- | --- | --- | --- |
| Morgan/基础 RDKit 描述符 + 合理监督模型 | 保留对照 | 简单结构特征是否已足够 | 固定特征定义、仅 train 拟合处理、覆盖与本地效果 |
| 随机初始化的小型 Chemprop D-MPNN | 保留深度对照 | 学习目标任务表示是否胜过固定表示 | 实际训练接口、预算、覆盖与效果 |
| MiniMol + 新训练 head | 首轮 `pilot` | 生物/量子多任务预训练表示能否迁移 | 权重授权范围、加载完整性、异常行、受限 head 比较 |
| CheMeleon + 新训练 head | 首轮 `pilot` | 描述符预训练表示是否有效；head 是否关键 | 本地覆盖、冻结状态、同预算比较 |
| MoLFormer-XL-both-10pct + 新 head | 第三名额或替补 `pilot` | 序列表征能否提供不同增量 | 精确公开资产的 token/立体处理与效果 |
| Uni-Mol / Uni-Mol2 | `defer`，条件满足后几何 pilot | 几何是否在已选 2D/序列之上增加有效信息 | 固定资产、构象/裁剪/回退、覆盖与成本 |
| CheMeleon + TabPFN 2.6 | `defer`，组合对照支线 | 更换预测器能否救回有用表示 | 2.6 资产与许可、上下文/资源协议、训练交付关系 |
| KPGT | `defer` | 知识增强图表示是否值得更复杂接入 | 辅助特征与预拟合参数、依赖、完整覆盖 |
| SMI-TED | `defer` | 另一个序列预训练目标是否补充首选 | 序列路线先有价值、明确变体与资源预算 |
| MolE | `defer` | 获得真实 checkpoint 后才进入比较 | 当前官方发布链尚未闭合 |

没有候选达到 `preferred`。首轮名额是全队总额，不是各专项报告的候选简单相加。这里把 MiniMol/CheMeleon 排前，是方法相关性和接入证据的工作判断；若 MiniMol 资产接入未闭合，可先做 CheMeleon 与 MoLFormer，不需让全队等待。规则资格、候选价值与运行完成度分别判断。

## 2. MiniMol

**支持。** 原始方法直接用固定分子表示训练下游 MLP，与本赛冻结条件接近。官方入口输出 512 维特征。论文与评测脚本的成绩包含 head 搜索、5 模型集成和重复，不能当成单个默认头的效果。[M01–M02]

**资产。** 官方代码提交 `41642328affbb35e4950b7b7a9020aa95919b503`；目标路径 `minimol/ckpts/minimol_v1/state_dict.pth`，还需匹配配置与依赖。代码 MIT；README 特别说明 included code，未独立补齐权重授权范围。本轮未下载权重，不把仓库存在写成完整可运行。

**真实实现限制。** `load_state_dict(..., strict=False)` 需检查 missing/unexpected keys；默认入口/依赖可能隐藏失败输出，必须检查行数与映射。作者 benchmark runner 会调用 TDC loader，且读取 `test.Y` 推断任务类型；本赛不能直接执行该评测流程。预训练排除 >100 重原子分子，不等于推理接口有100原子的硬上限；配置中的同名限制是注释。[M02]

**反证范围。** 2026 TDC 审计对其预训练结构暴露提出质疑。它没有证明本赛目标测试标签进入训练，也不能把文中其他模型的安装失败归到 MiniMol。结构/相关 assay 暴露会削弱公开分数的直接迁移力度，不能单凭这一条判定当前冻结使用违规。审计作者也展示自己的模型，来源立场需要保留。[B01]

**判别实验。** 与经典特征、CheMeleon 在同一固定划分下比较，控制 head 搜索名额；若额外接入成本明显超预算，先让替补进入。若某个 head 失败，只给一个有理由的配套对照；持续无增益且无互补时暂缓。

## 3. CheMeleon

**支持与反证同时存在。** 它在 Chemprop D-MPNN 上用可计算描述符预训练。arXiv v2 主表主要是微调，kNN probe 也先微调再提取，不能作为原权重全程冻结证据。作者补充材料 S5/Fig S6 则确有永久冻结消融：在其 FNN 和验证设置下，回归较弱，分类的收敛表现也不同。后续独立团队研究固定 CheMeleon + 表格基础预测器，说明 head 能改变结论。以上均不是本赛成绩。[M03,M05,M11]

**资产与入口。** 代码提交 `b5e5bd88a7070c3f278e7e65e85b792617bf125c`。具体权重 [Zenodo 15460715](https://zenodo.org/records/15460715)，文件 `chemeleon_mp.pt`，34,859,448 字节，发布方 MD5 `6a80b54fdb7de37ef0374d302f01e8ce`，API 明确 MIT；[本次发布方响应](research/evidence/chemeleon-zenodo-metadata.json)可离线核对。未下载计算 SHA256。官方 fingerprint 入口用固定消息传递与聚合提取表示，缺少本地权重时会下载，需要正式接入时显式固定资产。[M04]

**版本限制。** arXiv v2 为2026-02-09；2026期刊版已经存在，出版社全文受阻，本轮不能声称和所读 arXiv/Research Square 附件逐字一致。旧 v1 headline 不混用；Research Square supplement 只标自己的版本，不冒充期刊附件。[M03,M05]

**输入。** 入口的默认 RDKit 解析会受本批两个失败串影响。Chemprop v2.2.1 的原子编码对1–36和 I 有独立类别，其余进 unknown；并非含金属一定报错，也不保证信息充分。不能为了支持新元素随意改变冻结 checkpoint 的输入维度。[M06]

**判别实验。** 固定表示 + 有限容量的新 MLP，与 MiniMol/经典特征对照；回归冻结证据较弱是需要检验的前提，不是排除所有 head 的依据。TabPFN 组合单列为另一完整方案。

## 4. MoLFormer-XL-both-10pct

原论文明确区分冻结表示和骨干微调；主要下游表默认 full-XL 微调。公开 `both-10pct` 只使用两个预训练库各10%，不能继承 full-XL 成绩。公开卡支持固定向量，但说明预训练去立体信息、排除长于202 tokens的输入；“超过约200 atoms未测试”是另一条条件。[M07]

精确 HF revision：`361063d0ad524ef77cf39b08469f6be770dc550f`；`model.safetensors` 元数据187,248,784字节；卡标 Apache-2.0。需一并固定 tokenizer、配置与远程自定义代码。本轮只有[发布方元数据摘录](research/evidence/alternative-model-metadata.json)，没有权重运行验证。

它的研究价值是以可复用公开序列表征提供不同候选。接入前实际计算 token/词表覆盖，不能把681个字符或388个原子当成 token 计数。若要改变标准化，记录其对立体、片段和原始行的影响。首轮作为第三名额或替补；没有序列路线增量之前，不同时扩多个近似语言模型。

## 5. Uni-Mol 与 Uni-Mol2

官方表示接口能从 SMILES 或给定坐标提取固定表示。SMILES 路径意味着额外构象生成；本仓库没有提供现成3D。当前前处理源码有构象回退、v1默认256原子随机裁剪、v2默认128原子裁剪。权重不变和 `eval()` 不会自动固定这些随机过程。本批388重原子输入使这个问题实际存在。[M08]

已核元数据的是 `dptech/Uni-Mol2` revision `bf37d253c0f5ac61f468137eb00059978a104ff0` 的 `modelzoo/84M/checkpoint.pt`，336,632,021字节，卡 MIT；不能拿它冒充 v1 复现。未测构象成功率、超128原子数量、吞吐和效果。

在2D/序列先有合理方案后，用一个固定资产问“额外几何是否带来收益”。覆盖与重复性先清楚：构象、裁剪、回退、seed、输出层都进入缓存身份。若不能完整处理所有提交行，仍可做明确标记的局部研究，但不能称整套方案可交付。预训练大规模或量化任务成果不能单独证明冻结 ADMET 优胜。

## 6. TabPFN 及组合路线

2026 ADMET 基准使用 **v2**；冻结 CheMeleon + TFM 前作使用 **2.6**；当前官方默认已经是 **3.5**。不同版本、许可、上下文协议不可混用。论文中的 `fit` / in-context prediction 不等于新增梯度训练。[B03,M11–M12]

2.6 前作：固定分子表示及 TFM，不做任务特定权重训练；默认8 estimators，部分基线复用 CheMeleon 团队已发布预测；“win”包括与最优统计上不可区分，不是逐项绝对第一。研究有特征维数/样本规模资源限制，不能从摘要胜率推出本赛优选。[M11]

它有价值，但先作为对照或组合支线。要明确本赛设计/训练交付由什么模块满足，不能声称“调用固定模型已完成新深度模型训练”。2.6 的确切权重哈希和许可尚未完成；不以已核的 v2 条目替代。

已核 v2 元数据供识别，不代表复现2.6：

| 资产 | HF revision | 文件元数据 |
| --- | --- | --- |
| `Prior-Labs/TabPFN-v2-clf` | `275f19d2add9c2c0de38f9ebaded3856599fa2e7` | 默认分类权重29,009,539字节 |
| `Prior-Labs/TabPFN-v2-reg` | `02a44705ff7790b50cded404bc59adb94da456a1` | 默认回归权重44,390,977字节 |

代码和权重授权分开记录，v2 权重使用自己的 Prior Labs License。没有在本轮安装/下载或测试任何 TabPFN。

## 7. 后置候选

**KPGT。** 原文有固定骨干 feature extraction；不是因为不支持冻结而后置。代码 `47dc1646c70b2138a157de481d24a1ac35d174cd`，Apache-2.0；官方指向的 Figshare 权重记录 MIT、327.41 MB。实现同时依赖图、指纹与描述符，归一化含预拟合分布参数；变量 `ecfp` 实际调用 RDKFingerprint，不可按名字猜。冻结图模型允许并不自动完成所有辅助资产的边界审查。历史 DGL 环境意味着需要接入验证，不证明今天一定不能运行。[M09]

**SMI-TED。** `ibm-research/materials.smi-ted` revision `414c3ea0a8603ef49d1c5bb3db336e09877c01ce`，权重元数据1,159,784,188字节，卡 Apache-2.0；需固定 light/large 等确切变体。2026多模态原始研究提供任务依赖的线索，但与IBM有机构关联，且本轮未恢复所有 ADMET 冻结/head 配置。它不能当成完全独立的本赛复证，也不能据此永久否定模型。[M10,B04]

**MolE。** 官方仓库 `dd56d319103e973fde0dcaa3537cb36a7b7a9843` 的 checkpoint 下载仍为 TODO，仓库 CC BY-NC 4.0。先解决具体资产来源，再评价其可用性；不能把延后写成精度差或所有参赛都被许可禁止。[M13]

## 8. 实验前的共同问题

1. 输入异常是否保留行映射并有程序化、可验证策略？是否把局部覆盖成功冒充全量成功？
2. 外部权重始终固定吗？推理的 buffer、构象与裁剪是否也可重复？
3. 自己的 head 只用获准 train 学习吗？拟合变换、缓存和标签角色是否清楚？
4. 对照预算是否支持所声称的归因？一个head失败后，是否只追加有意义的最小对照？
5. 当前收益是否仅反映特定验证分布？Ames单骨架、LD50/solubility空骨架验证需要限定解释。

这些问题应在实验计划里得到答案，不要求研究阶段伪造实际运行结果。下一项最有价值的信息是本数据上受控实验，不是继续扩充候选名字。

## Independent score verification

```json
{
  "checked_at": "2026-10-31T04:14:21.284621+00:00",
  "method": "Controller independent ordered join against original vault truth and immutable run predictions; Decimal50 mean absolute error, not executor scorer execution.",
  "passed": true,
  "runs": [
    {
      "run_id": "hainan-frozen-training-20261031",
      "rows": 91,
      "independent_mae_decimal": "0.37862513598901103296703296703296703296703296703297",
      "reported_mae": 0.37862513598901104,
      "matches": true,
      "prediction_sha256": "e674439f83d55a17703e2a0d59bc3142874b4ad956d9f6fbb7a3377b40675993"
    },
    {
      "run_id": "hainan-skill-follow-20261031",
      "rows": 91,
      "independent_mae_decimal": "0.38918859397802178021978021978021978021978021978022",
      "reported_mae": 0.3891885939780218,
      "matches": true,
      "prediction_sha256": "aa33ca53bc0e1570aba6cf6d4ec1e82f41e126dc0fd57715cd52c32d2ee29bfb"
    }
  ],
  "fixed_mae_ast_matches_host": true,
  "wrapper_review": "strict scope and order/identities; full original valid+test structure then valid subset; finite values; synthetic cases present",
  "timing_seconds": 0.010924209,
  "wrapper_sha256": "6410d987eb602f6258fe5a0f22a1f569c80ebc49aa54ef9f8cc8bd65e699cdda",
  "tests_provenance_note": "Prior attempt failed a newline projection identity precheck after authorized truth read and before any metric call; need preserve attempt, and distinguish tests before first vs second truth access."
}
```

## Structured-publication repair

An earlier candidate applied a Markdown-link regex to JSON text and corrupted a scaffold array; the controller rejected it before publishing. All affected JSON derivatives were rebuilt from original parsed objects. Numeric values, array lengths and molecular/scaffold strings were checked against the declared source projection; no original, training, inference or score was changed. See evidence/json-semantic-verification.json.
