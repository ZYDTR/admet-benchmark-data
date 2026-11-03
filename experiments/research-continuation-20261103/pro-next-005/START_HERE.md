# Pro005：canonical848与机制反证后的独立研究

本包科学截止为 **2026-11-03T12:25:18.713994+00:00**。先读 [CURRENT_STATUS](current/CURRENT_STATUS.json)、[Q1至Q4决策合同](decision-contract.json) 和 [完整实验纲领](methodology/EXPERIMENT_DESIGN.md)，再沿问题读取完整证据。旧报告中的状态保留原时间含义，当前状态以本截止点为准。

当前记录：864个梯度头、843个逻辑run、52个冻结context；656个official Valid、230个native stress、30个train OOF fold分数，共916个单项分数。88个固定Valid cohort和105个composite单列。原full22候选保持；canonical848完整聚合已消费，scaffold30输出在本截止点尚未稳定，GEO002可信fresh producer准备已派。此包不追加训练、评分、标签获取或部署权限。

## 本次核心证据与限制

- [CANONICAL_AGGREGATES](hoof001/CANONICAL_AGGREGATES.json)、[完整发现](hoof001/CANONICAL_FINDINGS.md)、[旧群回验](hoof001/LEGACY_COHORT_AGGREGATES.json)：保留全848及旧未覆盖542行、完整改善/伤害/共同错误群和互补群。local端点MAE收益与整体排序、共同错误修复的结论分别判断；条件区间跨0不能解释为等效或不劣。
- [集中诊断](hoof001/CONCENTRATION_FINDINGS.md)、[测定语义](hoof001/ASSAY_FINDINGS.md)：集中同时出现在改善与伤害；测定级界限与逐行映射未确认分开，既有凸组合边界内的一侧损失不自动构成新干预。
- [ME40最终消费](mechanism40/FINAL_CONSUMPTION01.json)、[PAIR16反证](mechanism40/PAIR16_DECISION01.json)、[full22报告](full22/REPORT.md)、当前ledger及prior-pro004完整研究共同用于去重和修正判断，保留所有负向、零和未知。
- [GEO002已派设计](geo002/DESIGN.json) 与 [方向决定](geo002/DIRECTION_DECISION01.json) 是现有准备范围，科学效果在本截止点仍未知。不得重发同一准备或覆盖活动HOOF配置。
- 所有群成员、统计定义、不确定性与条件限制按固定输入保留；没有逐行真值、预测、残差或特征/权重数组，不能自称重新评分。统计源码仅供阅读，不能执行。

## 完整历史与来源
- [Pro004固定入口](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/730373b4718d24618592b677a71a69508054f07a/experiments/research-continuation-20261103/pro-next-004/START_HERE.md)、[其完整分支导航](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/730373b4718d24618592b677a71a69508054f07a/experiments/research-continuation-20261103/pro-next-004/HISTORY_BRANCH_INDEX.json)、[固定账本](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/730373b4718d24618592b677a71a69508054f07a/experiments/research-continuation-20261103/pro-next-004/ledger/experiments.json)、[manifest](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/730373b4718d24618592b677a71a69508054f07a/experiments/research-continuation-20261103/pro-next-004/input-manifest.json)。沿固定分支可枚举更早全部相关研究、Mini22、失败、未准入资产及正反证据，继承可信验收，不重传旧全库。
- [READING_CONTRACT](READING_CONTRACT.json)、[HISTORY_BRANCH_INDEX](HISTORY_BRANCH_INDEX.json)、[SOURCE_MANIFEST](SOURCE_MANIFEST.json)、[SOURCE_MAP](SOURCE_MAP.json)、[SOURCES](SOURCES.md)、[input-manifest](input-manifest.json)。
- 身份分三层：记录的科学原件、Astra批准的限定输入副本、本次基础设施脱敏公开件。批准副本中已排除的raw诊断行/示例不在本包。没有读取底层排除原件来重新生成或补标签。reference-only来源只是身份，不能当成实际公开原件。
- 本次完整覆盖28份批准文件，另含明确准入的决策合同和共同实验纲领。来源数字、科学键/类型/数组、完整群成员、正负未知结果与限制保真；操作资源名、路径和线程身份转换不产生新科学结果。

## 全部28份批准科学文件

### ledger

- [ledger/experiments.json](ledger/experiments.json)
- [ledger/decision-frontier.json](ledger/decision-frontier.json)
- [ledger/proposal-execution.json](ledger/proposal-execution.json)
- [ledger/issues.json](ledger/issues.json)
- [ledger/claim-events.json](ledger/claim-events.json)
- [ledger/task22-frontier.json](ledger/task22-frontier.json)

### mechanism40

- [mechanism40/FINAL_CONSUMPTION01.json](mechanism40/FINAL_CONSUMPTION01.json)
- [mechanism40/PAIR16_DECISION01.json](mechanism40/PAIR16_DECISION01.json)

### full22

- [full22/REPORT.md](full22/REPORT.md)

### hoof001

- [hoof001/DESIGN.json](hoof001/DESIGN.json)
- [hoof001/oof_statistics.py](hoof001/oof_statistics.py)
- [hoof001/CANONICAL_AGGREGATES.json](hoof001/CANONICAL_AGGREGATES.json)
- [hoof001/LEGACY_COHORT_AGGREGATES.json](hoof001/LEGACY_COHORT_AGGREGATES.json)
- [hoof001/CANONICAL_FINDINGS.md](hoof001/CANONICAL_FINDINGS.md)
- [hoof001/CONCENTRATION_FINDINGS.md](hoof001/CONCENTRATION_FINDINGS.md)
- [hoof001/ASSAY_FINDINGS.md](hoof001/ASSAY_FINDINGS.md)
- [hoof001/CANONICAL_CONSUMPTION01.json](hoof001/CANONICAL_CONSUMPTION01.json)

### geo002

- [geo002/DESIGN.json](geo002/DESIGN.json)
- [geo002/DIRECTION_DECISION01.json](geo002/DIRECTION_DECISION01.json)

### geometry-prior

- [geometry-prior/CONSUMPTION.json](geometry-prior/CONSUMPTION.json)

### prior-pro004

- [prior-pro004/SCIENTIFIC_INTAKE.json](prior-pro004/SCIENTIFIC_INTAKE.json)
- [prior-pro004/analysis.md](prior-pro004/analysis.md)
- [prior-pro004/next_batch_guide.md](prior-pro004/next_batch_guide.md)
- [prior-pro004/next_experiments.json](prior-pro004/next_experiments.json)
- [prior-pro004/issues.json](prior-pro004/issues.json)
- [prior-pro004/search_space.json](prior-pro004/search_space.json)
- [prior-pro004/review.json](prior-pro004/review.json)

### current

- [current/CURRENT_STATUS.json](current/CURRENT_STATUS.json)

研究Q1至Q4要求竞争解释、可区分的有限干预、22任务方向与原提案逐项去重；完整返回analysis.md、issues.json、next_batch_guide.md、next_experiments.json、review.json、search_space.json及有价值补件，记录实际读取覆盖。原网关独立收发，本发布方只交固定发布回执。
