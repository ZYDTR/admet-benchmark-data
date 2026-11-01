# 22任务策略研究：完整任务及固定历史快照

这是同一策略咨询的精确引用运输，研究范围未缩减。请完整读取 full-prompt.txt 并依其渐进索引、55项阅读合同完成分析；reading-contract.json为相同固定URI的机器可读副本。

科学材料固定在 https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/31a9bb2729ff1464bf6d4be1e23fcba0bf391725/experiments/training-breadth-strategy-20261101/START_HERE.md 。截至原科学快照2026-11-01T11:28:28Z，另含004启动前资源拒绝的明确补充；后续现场进展不在本快照。历史文件中的候选/尚未发布是原件形成时状态，实际已发布身份由固定commit与完整Prompt绑定，不将旧状态伪装为最新。

输入manifest_sha256：2b37cecef4b6f45481ba1991766a2b15eaaffb672a695d193ae03b878c5e04e8。request_id：admet-breadth-strategy-pro-20261101-001。完整Prompt SHA256：2a96147430e375f5f794215ef8062fb9e67d75a92b8353af06482554206214c6。

已有知识：5次完成学习/26头（22任务基线+4次Caco2），其余21项未后续优化；当前新增六项在本快照中均未开始学习。请比较三种预算分配策略，给出22任务优先级、精确批次与停止条件。所有外部编码器参数和buffer保持冻结，仅train.Y学习，valid保留选模。完整要求与六文件返回规范以full-prompt.txt为准。
