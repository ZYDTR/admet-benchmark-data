# 上下文、规则与资产

GLM、DeepSeek、Qwen 是准备执行模型。科学资产分子编码器、预测器、经典特征和从零模型分别列在 [科学资产准备度](scientific-assets.json)；MiniMol 和 MoLFormer 均未完成生产接口验收，不能当作可训练底座。

[执行模型边界](execution-models.json) · [冻结底座身份](chemeleon-weight-reference.json) · [真实接口与返回合同](runtime-and-return.md)

## 规则来源

- [宿主规则](../originals/S-6315de690f4dd839.md.txt)
- [本次冻结 policy](../originals/S-0dace3cc6ba62f7e.json)
- [赛事原文、用户确认与本地控制的来源区分](../originals/S-0d9ddc76ab776c6b.md.txt)
- [本版交接合同](../originals/S-640a1a533aaa4ea8.md.txt)

外部预训练权重必须冻结来自用户向赛方确认后的条件；旧 Harness 的随机初始化、本机 Docker 或执行器限制不等于赛事要求。官方 valid 可调参，与本项目训练只读 train.Y、valid 由指定宿主评分是不同层面的决定。新 Chat 不清除 valid 适应偏差。

## 资产与数据原件

- CheMeleon：`trained_22_tasks_and_caco2_refinements`。
- MiniMol：`preparation_incomplete_not_training_ready`。原准备idle_incomplete，上游setup.py 404；资产加载/生产接口未验收
- MoLFormer公开10pct资产：`preparation_incomplete_not_training_ready`。原准备idle_incomplete，目录外写入拒绝；资产/接口未验收；不得冒充full-XL
- 经典分子特征：`researched_not_prepared`。尚无本项目已验收运行包
- 从零小D-MPNN：`researched_not_prepared`。需独立科学配置、预算和准入；不是预训练微调
- TabPFN 2.6：`researched_not_prepared`。许可/版本/资源/赛制适用性待核验；不是分子encoder
- KPGT：`researched_deferred`。额外信息与接入成本未闭合
- Uni-Mol：`researched_deferred`。构象/裁剪及完整输入覆盖未核验
- SMI-TED：`researched_deferred`。资产条件与接入尚未闭合
- MolE：`researched_deferred`。官方checkpoint发布链未闭合
- [完整原研究报告](../originals/S-3c82354467f75764.md.txt)
- [Mini22 训练/盲输入身份清单](../originals/S-53e7d9ed8024a163.json)
- [候选资产来源审计](../originals/S-04ae8258d836773b.md.txt)
- [底座来源元数据](../originals/S-51b7dd3fb543bede.json)

本阶段没有读取标签数据集。既有 Caco2 valid 只能按旧批准对象引用：SHA256 `63328bf307b850a4a0986165d0800bae5aa737c41bd63f1026d16114d8560bb4`，91 行；本候选没有新增标签文件。旧训练预测与汇总指标保留科学数值。
