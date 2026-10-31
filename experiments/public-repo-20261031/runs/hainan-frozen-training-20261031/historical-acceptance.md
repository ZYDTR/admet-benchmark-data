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
