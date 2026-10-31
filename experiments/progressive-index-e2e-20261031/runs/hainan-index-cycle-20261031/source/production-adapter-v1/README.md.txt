# 本地生产适配准备 v1

本目录接入主控已准入的 host-science-v1，科学 manifest SHA256 为 `1f944daecd5a629a488dfba180ee2611091a2482d2e2f489005c2836c0260dd5`。四项部署位置保持 `source/train_remote_v4.py`、`source/training_science.py`、`source/config.json`、根 `encoder.py`。原科学文件、PLAN、Skill、阶段一 runtime 均未改动。

入口 `readiness.json`；精确适配器清单 `source-manifest.json`；检查记录 `checks/final-validation.json`。这是本地准备交付，生产 profile 的 `execution_enabled=false`，GPU、正式消息和执行 binding 尚未登记。默认 production CLI 实测返回 78；没有海南操作、真实科学库导入、CUDA、数据加载或参数更新。

## 适配方式

`adapter_common.py` 以私有模块名加载阶段一 generic common_guarded，向科学代码注入独立的 `common_guarded` 模块。它提供 `ROOT`、`GPU_UUID`、无参数 `environment()`、`now()`、`safe(path, existing=False)`、`sha(path)` 和 `write_json(path, value)`。函数闭包保留明确 root，不改通用库的 root 参数签名。Linux 边界模块在装配时捕获通用 safe，避免被科学兼容接口覆盖。

`guarded_worker.py` 先确认准入与目标身份，建立全部环境/缓存/joblib 设置，再设置 Linux 进程限额、Landlock，最后导入科学 entry 及其 helper。helper 顶层会导入 numpy，所以保护必须早于加载 runner 模块。发现 torch/numpy/chemprop/rdkit/joblib/encoder 提前导入时立即退出。真实预检会加载完整依赖及 runner._load_late 并执行有界 CUDA matmul；训练另起受同样保护的进程。两者都不修改已准入源码。

`phase_supervisor.py` 和 `pipeline.py` 贯通预检到训练。每阶段真实 Popen returncode 与监督状态分别保留；只有前一步外层返回 0 且 adapter 凭据校验通过，才能进入训练。超时返回 124，检查/监测失败 125，完成凭据不明 126，已存在 run 锁返回 73，准入门关闭返回 78。子任务退出 7 会成为 pipeline 的 7，`SystemExit(main())` 将其传到最外层。每个运行的独占锁只登记一次，响应不明查询原锁/进程，不在本模块重放启动。

## 完成凭据

原 `raw/train-complete.json` 仅是科学输出之一，不能授权成功。worker 仅在 `main()` 明确返回整数 0 后，核对本次 runtime PID/run/GPU/config 身份、冻结/优化器/更新的结构声明、encoder 前后记录和优化器/RNG重载记录，要求 21 项产物全部新建且非空，再生成该阶段 `adapter-complete.json`。遇到预先存在的训练产物会拒绝执行，不覆盖旧结果。

新凭据绑定 run、阶段、随机 token、worker PID/PGID/可用时的 Linux start_ticks、科学 manifest、GPU、保护记录和完整产物 SHA。外层将它与 `worker-start.json`、Popen leader 的 PGID 和预期 token 对账，并再次校验完整产物集合及 SHA。生产使用 strace 时，worker PID 与 launcher PID 可以不同，必须同进程组且在运行中独立观察过 worker 的 start_ticks。离线无追踪时二者必须是同一 PID。

这些是进程完成和证据身份检查。模型张量、逐行预测、完整冻结、写入轨迹、全部后代和 GPU 释放仍须主控独立验收。本机回收检查只证明测试的 Popen leader 已退出；没有声称完整树、目标机释放或零资源影响。

## 当前检查

固定玩具模块只用标准库和字节文件，`.pt/.npz` 仅是从未反序列化的测试字节。预检/训练成功、各自退出7、各自超时、前置失败、监测失败、预检凭据缺失、只有旧成功文件、缺失新凭据、错 token/PID/manifest、产物摘要漂移、陈旧 train-complete 均有真实外层子进程记录。另有重复锁、提前导入阻断、规范化准入正反例和运行兼容库单独绑定检查。

`tests/check_science_interface.py` 对真实准入源码做只读接口检查：先准备环境，使用 inert numpy ModuleType 导入 helper 的定义，阻止真实科学依赖导入；调用实际 main 的早期路径，在 `_load_late` 处由哨兵终止。它不加载数据、构建模型、调用优化器或做参数更新；不将此检查当作真实依赖/CUDA证明。原始四个 deploy_path 还在未执行的本地部署夹具中通过同一 admission 校验。

```sh
python3 -I -B adhoc_jobs/admet_training/runs/hainan-index-cycle-20261031/source/production-adapter-v1/tests/check_adapter.py
```

接口探针需要一个尚不存在的本目录 `checks/` 后代路径作为参数。每次测试使用新目录，旧记录全部保留。主控精确复查入口见 `checks/final-validation.json`。

## 正式执行前的绑定合同

当前 `accepted-science-binding.json` 保存本机四项科学来源及主控 acceptance 的精确 SHA，`adapter-profile.json` 保存关闭的默认配置。后续仅在主控另发正式执行消息后，由执行方保存新的执行 profile，并登记精确清单，不覆盖本地准备证据。pipeline 和 worker 都支持 `--profile <run内绝对路径>`，默认仍是关闭的 profile。

执行 profile 须包含现有 run/root/python/预算/PLAN SHA、实际新选 GPU UUID/index、`execution_enabled=true`、`science_entry=source/train_remote_v4.py`、`accepted_manifest.sha256`、`main_scientific_acceptance.sha256`、`admission_binding`，以及 `formal_execution_message.message_id/origin_thread_id`。主控来源线程固定 `<PRIVATE_ROLE_REF_298cc5edc2>`。这里只接受主控正式下发后保存的消息身份；测试中带 SYNTHETIC 的记录仅作不执行的反例夹具。

`admission_binding` 指向 run 内规范 JSON：

```json
{
  "plan_sha256": "原 PLAN 的 SHA256",
  "acceptance": {"path": "source/admission/MAIN_ACCEPTANCE.json", "sha256": "主控原件 SHA256"},
  "manifest": {"path": "source/admission/scientific-manifest.json", "sha256": "1f944daecd5a629a488dfba180ee2611091a2482d2e2f489005c2836c0260dd5"},
  "formal_dispatch": {"path": "source/admission/formal-dispatch.json", "sha256": "正式执行记录 SHA256"}
}
```

acceptance 和 manifest 原字节复制，按主控现有 `accepted_source_manifest_sha256` 与 `deploy_path` 字段验收。formal-dispatch 内容须绑定 `action=execute_one_frozen_run`、run_id、同一科学 `accepted_source_manifest_sha256`、plan_sha256、整数 `max_training_jobs=1` 及同一 message_id/origin_thread_id。科学源码逐项核验目标 deploy_path 的实际 SHA，不能只依赖 passed。

可选线程命名兼容库通过 `compatibility_preload={path,sha256}` 和 `runtime_artifacts_manifest={path,sha256}` 单独登记，formal-dispatch 另绑定 `runtime_artifacts_manifest_sha256`。运行产物 manifest 的 files 使用 `{path,sha256}`，全部在本 run 内核验；其源码、编译过程和产物需主控审查。本轮没有生成、加载或盲复用旧二进制，也没有改科学 manifest 以容纳兼容库。

实际目标阶段仍按海南 Skill 固定路由，先完成连接/身份/路径/环境/输入/权重检查及有界只读恢复，再做当前 GPU 健康、占用和启动前复核。适配器内没有 SSH、上传或通用连接重试。上传/启动响应丢失按原作业身份对账。目标入口还核对 Linux/<COMPUTE_HOST>/UID1012，GPU 空闲观察和资源监测仅在正式准入后执行；共享/并行未提供许可或验收。真实 CUDA、Linux 限制/追踪兼容性、全依赖副作用、目标资源与最终科学结果均待正式执行后验证。
