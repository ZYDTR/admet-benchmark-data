# Fresh MAE-monitor run: local runtime preparation

This directory is prepared for `hainan-mae-monitor-20261101`. The checked-in
profile has `execution_enabled: false`; no connection, deployment, scientific
`main()`, inference, fitting, backward pass or optimizer step was performed.
The production path has not been exercised in this run.

The frozen run instructions and main's accepted four scientific files are the
authorities. `science-binding.json` maps the accepted local files to their future
deployment positions: runner/helper/config under `source/`, encoder at the run
root. Source bytes and the original flat four-file manifest remain unchanged.
The configured checkpoint/early-stop monitor is raw MAE. The training loss
remains MSE. The legacy best-MSE field retains its MSE prefix-minimum meaning.

## Prepared entry and admission

The finite outer entry is `job_waiter.py production --profile <absolute-profile>`.
It waits for the actual pipeline OS exit and writes `raw/job-wait-exit.json`.
There is no transport, resident service, timer or restart loop here. A later main
dispatch must separately authorize deployment and execution. The exact command
and layout are recorded in `operator/preflight-01/readiness.json` and
`deployment-layout.json`.

Before scientific import, admission requires all of the following:

- Exact run/root, PLAN, head/split settings, MAE monitor and budget identity.
- The unchanged original flat scientific manifest, passed main acceptance and
  their SHA256 bindings. The acceptance's `manifest` is compared to the original
  authority path as a string; the documents are read from copies inside the run.
- A normalized binding to a formal main message authorizing exactly one job,
  plus the exact frozen-instructions and reviewed runtime-source manifest hashes.
- All four deployed scientific files, all frozen instruction files, three fixed
  input CSV hashes/row counts and the frozen backbone checkpoint hash.
- Explicit GPU UUID/index and the target Linux `<COMPUTE_HOST>` / UID 1012 identity.

`source-manifest.json` separately pins the runtime files. A later execution
profile must set its path/hash and formal message; the default profile stays
closed. Templates in `operator/preflight-01/` contain no execution authorization.
An optional preload is separately bound with `runtime_artifacts_manifest` and
the matching dispatch hash. The copied C/shared-object bytes were not loaded or
compiled locally. They are not part of the four-file scientific authority.

## Runtime behavior prepared for later target verification

Protection precedes all scientific imports, including `training_science`'s
top-level NumPy import. The legacy `common_guarded` interface has the exact
`ROOT`, `GPU_UUID`, `environment()`, `now()`, `safe(path, existing)`, `sha(path)` and
`write_json(path, value)` signatures. The clean environment, Linux limits and
write guard are established before loading the runner/helper/encoder.

Preflight imports the actual stack, verifies a single visible CUDA device and a
CUDA matrix multiplication, then checks real Tensor/optimizer-payload/RNG storage
with `weights_only=True`. That probe has zero parameter updates and does not
instantiate a model or optimizer. A successful worker return alone does not
admit learning: the outer supervisor also requires the current attempt's
identity-bound receipt and storage proof.

Learning can follow only a passed outer preflight, fresh output paths and an
exclusive `state/learning-started.lock`. The run-start and finite-waiter locks
also use exclusive creation and are never reclaimed. There are no dependencies
on an old failed attempt's exit, PID, lock or recovery files. Unknown launch or
learning outcomes retain the lock and require reconciliation, not replay.

After a real scientific return of zero, the worker must load the actual best,
last and optimizer/RNG checkpoints with `weights_only=True`, validate selected
epochs/steps, both metric meanings, configuration/source identities, four actual
head and optimizer Tensor states and all RNG sources before issuing its receipt.
Main's independent scientific, row, trace and process acceptance remains required.

The copied resource monitor retains the confirmed Z/X terminal-state fix:
missing VmRSS is zero only for confirmed terminal tasks (including the bounded
stat reread); live/unknown missing RSS, negative RSS and parse errors fail.
Timeouts, cancellation, failed checks and missing/mismatched receipts propagate
nonzero exits through worker/supervisor/pipeline/outer waiter. Only own recorded
process identities/groups are signaled.

## Local evidence and limits

Run the fixed tests with `python3 -I -B tests/check_adapter.py`,
`tests/check_science_interfaces.py`, `tests/check_proc_race.py` and
`tests/check_job_waiter.py`. Evidence is unique per invocation under `checks/`.
Offline subprocesses use only the fixed `toy_science.py`; their `.pt`/`.npz`
fixtures are inert bytes and do not certify scientific storage.

The science-interface test executes selected exact AST definitions from the
accepted sources, not a rewritten monitor implementation. It uses real approved
CSV/source/checkpoint bytes for read-only admission checks. The extracted
production `save_head` definition is exercised for both monitors and best/last
with an explicitly metadata-only serializer. NumPy and Torch are absent in the
local interpreter; no installation was attempted. Actual module import, numeric
interfaces, Tensor serialization, model execution, CUDA, target write guard,
strace coverage, real resource enforcement/availability and training remain
unverified in this run. Budget targets are not aggregate OS quotas.

Reports preserve these limits. No private validation labels/scores or uploads
are used. `checks/` and local fixture state are excluded from deployment.
