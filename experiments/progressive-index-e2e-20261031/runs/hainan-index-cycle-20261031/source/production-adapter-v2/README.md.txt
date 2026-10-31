# 运行包装恢复候选 v2

当前仅本地候选，尚未部署或获得新的生产绑定。v1、原正式dispatch、已准入科学文件、PLAN、Skill及失败原件全部保留。

v1在GPU5完成完整依赖导入和CUDA matmul，worker返回0并生成有效凭据；监督器随后读取/proc缺失的VmRSS，返回125并跳过训练。确切错误来自resource_checks.own_process_observation。终态进程是可重现的触发方式，但原采样未记录抛错PID，不能断言当时具体状态。47个返回文件及24.95MB原件已校验；见本run acceptance/execution-01/。

本候选保留v1保护、科学准入、完成凭据及退出传播，增加：

1. source/runtime-recovery-v2/resource_checks.py区分确认终态与未知内存。缺VmRSS且State为Z/X时，记录终态并将已释放地址空间的RSS计0；非终态经过有界10ms再读stat确认退出。仍存活/未知、负值或不能解析的RSS继续硬失败。FileNotFound仍按退出期间样本消失处理。
2. 只从新的runtime-recovery-v2加载库；common_guarded和linux_boundary原字节复制。科学源码和manifest 1f944daecd5a629a488dfba180ee2611091a2482d2e2f489005c2836c0260dd5不变。
3. 阶段证据、追踪与pipeline-exit进入raw/attempt-v2/；独占锁为state/production-adapter-v2-start.lock。不覆盖v1任何状态、dispatch或锁。
4. 训练前要求所有科学输出尚不存在；旧pipeline记录须明确training_started=false且旧训练child_identity=null。再以state/learning-started.lock独占登记本run首次学习启动。已学习、未知或已登记均阻断，不自动重投。

checks/recovery.patch是与v1的差异；checks/final-validation.json给出22项本地检查（18组真实假pipeline）、8项/proc夹具和已准入源码早期接口探针。旧解析器在Z且无VmRSS夹具重现KeyError，新版本通过；alive/unknown缺内存仍失败。没有参数更新，Linux真实竞态分支仍须新的正式绑定后验收。

默认adapter-profile.json仍execution_enabled=false。主控审查后用当前PLAN SHA和新的runtime manifest创建正式恢复dispatch及执行profile，保留科学acceptance/manifest，登记新message_id并刷新GPU证据。接口与v1相同，指向本目录pipeline.py。执行前确认v1进程退出且学习未启动，不能把v1外层125改写为成功。

测试.pt/.npz只是独立夹具的未加载字节；真实科学探针使用inert numpy，在_load_late前中止。模型、数据、标签、冻结条件及一轮一次学习额度不变。本候选未部署、未训练、未评分/发布或创建后台任务。
