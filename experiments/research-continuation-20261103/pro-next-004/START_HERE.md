# Pro004：完整历史与最新科学证据

科学截止 **2026-11-03T01:14:50.075644+00:00**。先读 [CURRENT_STATUS](current/CURRENT_STATUS.json)。另有唯一获准的 [晚到T2进度证据](current/LATE_OBSERVED_T2_STARTUP.json)：attempt03两fit已通过tensor初始化及scaler等同门禁并开始更新，01:18:49观测seed44为23epoch/1173steps、seed45为31epoch/1581steps。它纠正原快照中attempt03仍待路径修复的旧已知状态；**最终AP和科学消费仍0**。原69份文件、科学cutoff、配置与预算不改。T2/Hep8不能写成科学完成或重复提案。

已完成 **784实际梯度头、763逻辑梯度run**。单项数值 **652wholeValid + 164nativeTrainStress = 816**；固定cohort另有 **88数值、8抑制项**，含cohort共 **904**。**95composites**另列；历史 **10unknown**保留。**32冻结contexts**与梯度头分开；32个D和32个代数下界L不计质量评分。以上不代表独立数据集数或赛事总分。

## 核心入口与完整历史

1. [Q1–Q7与交付合同](decision-contract.json)、[实验纲领](methodology/EXPERIMENT_DESIGN.md)、[研究Skill3.4.1](methodology/RESEARCH_SKILL.md)、[证据复用](methodology/evidence-reuse.md)、[阅读合同](READING_CONTRACT.json)。
2. [完整历史分支索引](HISTORY_BRANCH_INDEX.json)、[本次历史索引](ledger/history-index.json)、[784头与32context账本](ledger/experiments.json)、[全22任务frontier](ledger/task22-frontier.json)、[问题](ledger/issues.json)、[提案执行](ledger/proposal-execution.json)、[主张事件](ledger/claim-events.json)、[资产准入](ledger/assets.json)、[组合](ledger/ensembles.json)。
3. [Pro003固定完整入口](https://github.com/ZYDTR/admet-benchmark-data/blob/f9bce86edb177a6b74f0af7a2e630a1350de914b/experiments/research-continuation-20261103/pro-next-003/START_HERE.md)、[其固定账本](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f9bce86edb177a6b74f0af7a2e630a1350de914b/experiments/research-continuation-20261103/pro-next-003/ledger/experiments.json)、[其manifest](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f9bce86edb177a6b74f0af7a2e630a1350de914b/experiments/research-continuation-20261103/pro-next-003/input-manifest.json)，以及[Pro002及更早完整分支](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f65d8149a897ea1db64c6f7cb16e52e06987229a/experiments/research-continuation-20261102/pro-next-002/HISTORY_BRANCH_INDEX.json)。沿固定commit可枚举Mini22、早期失败、未就绪底座和全部相关旧分支。旧公开对象不重传；本包prior-pro003/列出上轮22份完整返回原件的公开派生，脚本只读、不执行。

## 新证据与反例

- Rank44的rank−HalfMSE主对比18正2负，两个负向均在hepatocyte。micro8/8、Hep6/8、VDss4/4正；VDss FullMSE与HalfMSE四对相同。这些配对不是20个独立数据集。
- TabICL原16与nativeStress16：Mini micro在两个原生划分的context均值均改善相对旧MiniMLP；DILI表示排序随方案反转。CYP MiniTabICL均值低于旧MiniMLP/TabM。保留完整矩阵、split与随机态差异，不作纯head/backbone因果结论。
- Capacity26、Window12、CYP3A4lr8、AMESdual4、最终MoLFormer16均已真实消费。M5/M6混合/负向结果及window策略相同状态别名完整保留；物理拟合、策略视图和评分数分开。
- common-error-bound32的32D/32L全部有效且L正；仅为固定配对和群上的代数下界，不能定位错误分子、识别机制或约束任意预测混合。
- Geometry旧Monroe/UniMol2缓存缺原producer冻结证明，未准入。UniMol2v4只是未来协议静态验收；Monroe额外调用及原证据纠错保留。几何方法科学效果仍未测，不是科学效果失败。
- **T2两梯度头和Hep8八冻结context已派发，当前最终质量结果均0**。晚到文件只证明T2实际更新进度，不提供质量结果。已有完成证据可先研究，无需等待活动实验或bulk归档。
- Window12、TabICL原16、Tabstress16在科学截止点的bulk归档仍pending，科学已就绪。firstMiniCaco44 internal-forward count与真实global total仍UNKNOWN；不得填0/反推。Tabstress16的24public/48direct internal调用单列。

## 阅读边界

原件身份、公开派生SHA和范围见[SOURCE_MANIFEST](SOURCE_MANIFEST.json)；所有新对象见[input-manifest](input-manifest.json)。[SOURCE_MAP](SOURCE_MAP.json)和[SOURCES](SOURCES.md)逐项解析来源。packet://path按本包固定commit解析；evidence-ref:ref-ID是来源身份，reference-only底层原件未公开，不能声称已读。

仅更改基础设施路径和操作身份字符串，JSON数字字面量、数组、布尔值、空值和全部科学结果与负例保真。只含获准汇总，不含逐行真值、残差、特征或模型。外部参数及buffer冻结、train.Y学习、原行/分区、重复Valid使用边界继续适用。研究只读；新公开方法/资产主张核对一手来源，不授权训练、评分、模型加载或派发。

## 全部70份批准科学文件

### ledger

- [ledger/experiments.json](ledger/experiments.json)
- [ledger/ensembles.json](ledger/ensembles.json)
- [ledger/history-index.json](ledger/history-index.json)
- [ledger/issues.json](ledger/issues.json)
- [ledger/claim-events.json](ledger/claim-events.json)
- [ledger/decision-frontier.json](ledger/decision-frontier.json)
- [ledger/task22-frontier.json](ledger/task22-frontier.json)
- [ledger/assets.json](ledger/assets.json)
- [ledger/proposal-execution.json](ledger/proposal-execution.json)

### new-results

- [new-results/molformer16-20261103/micro-update.md](new-results/molformer16-20261103/micro-update.md)
- [new-results/molformer16-20261103/cyp-update.md](new-results/molformer16-20261103/cyp-update.md)
- [new-results/molformer16-20261103/caco-update.md](new-results/molformer16-20261103/caco-update.md)
- [new-results/molformer16-20261103/caco-results.json](new-results/molformer16-20261103/caco-results.json)
- [new-results/molformer16-20261103/dili-update.md](new-results/molformer16-20261103/dili-update.md)
- [new-results/capacity26-20261103/cyp6-update.md](new-results/capacity26-20261103/cyp6-update.md)
- [new-results/capacity26-20261103/sol4-update.md](new-results/capacity26-20261103/sol4-update.md)
- [new-results/capacity26-20261103/micro10-update.md](new-results/capacity26-20261103/micro10-update.md)
- [new-results/capacity26-20261103/caco6-update.md](new-results/capacity26-20261103/caco6-update.md)
- [new-results/window12-20261103/cyp-update.md](new-results/window12-20261103/cyp-update.md)
- [new-results/window12-20261103/caco-update.md](new-results/window12-20261103/caco-update.md)
- [new-results/tabicl16-20261103/panel-results.json](new-results/tabicl16-20261103/panel-results.json)
- [new-results/tabicl16-20261103/panel-update.md](new-results/tabicl16-20261103/panel-update.md)
- [new-results/ames-dual-selector4-20261103/results.json](new-results/ames-dual-selector4-20261103/results.json)
- [new-results/ames-dual-selector4-20261103/update.md](new-results/ames-dual-selector4-20261103/update.md)
- [new-results/cyp3a4-lr-stress8-20261103/combined-results.json](new-results/cyp3a4-lr-stress8-20261103/combined-results.json)
- [new-results/cyp3a4-lr-stress8-20261103/update.md](new-results/cyp3a4-lr-stress8-20261103/update.md)
- [new-results/common-error-bound32-20261103/scientific-summary.json](new-results/common-error-bound32-20261103/scientific-summary.json)
- [new-results/rank-transfer44-20261103/clearance_hepatocyte_az-results.json](new-results/rank-transfer44-20261103/clearance_hepatocyte_az-results.json)
- [new-results/rank-transfer44-20261103/clearance_microsome_az-results.json](new-results/rank-transfer44-20261103/clearance_microsome_az-results.json)
- [new-results/rank-transfer44-20261103/vdss_lombardo-results.json](new-results/rank-transfer44-20261103/vdss_lombardo-results.json)
- [new-results/rank-transfer44-20261103/combined-results.json](new-results/rank-transfer44-20261103/combined-results.json)
- [new-results/rank-transfer44-20261103/combined-update.md](new-results/rank-transfer44-20261103/combined-update.md)
- [new-results/tabicl-stress16-20261103/dili-results.json](new-results/tabicl-stress16-20261103/dili-results.json)
- [new-results/tabicl-stress16-20261103/clearance_microsome_az-results.json](new-results/tabicl-stress16-20261103/clearance_microsome_az-results.json)
- [new-results/tabicl-stress16-20261103/combined-results.json](new-results/tabicl-stress16-20261103/combined-results.json)
- [new-results/tabicl-stress16-20261103/combined-update.md](new-results/tabicl-stress16-20261103/combined-update.md)

### prior-pro003

- [prior-pro003/aggregate_inputs_and_new_checks.json](prior-pro003/aggregate_inputs_and_new_checks.json)
- [prior-pro003/analysis.md](prior-pro003/analysis.md)
- [prior-pro003/budget_scenarios.json](prior-pro003/budget_scenarios.json)
- [prior-pro003/claim_events.json](prior-pro003/claim_events.json)
- [prior-pro003/cohort_register.json](prior-pro003/cohort_register.json)
- [prior-pro003/conditional_followups.json](prior-pro003/conditional_followups.json)
- [prior-pro003/controls.json](prior-pro003/controls.json)
- [prior-pro003/delivery-manifest.json](prior-pro003/delivery-manifest.json)
- [prior-pro003/evidence_gaps.json](prior-pro003/evidence_gaps.json)
- [prior-pro003/evidence_registry.json](prior-pro003/evidence_registry.json)
- [prior-pro003/exclusions_and_reuse.json](prior-pro003/exclusions_and_reuse.json)
- [prior-pro003/history_navigation.json](prior-pro003/history_navigation.json)
- [prior-pro003/issues.json](prior-pro003/issues.json)
- [prior-pro003/next_batch_guide.md](prior-pro003/next_batch_guide.md)
- [prior-pro003/next_experiments.json](prior-pro003/next_experiments.json)
- [prior-pro003/review.json](prior-pro003/review.json)
- [prior-pro003/scientific_assets.json](prior-pro003/scientific_assets.json)
- [prior-pro003/search_space.json](prior-pro003/search_space.json)
- [prior-pro003/split_register.json](prior-pro003/split_register.json)
- [prior-pro003/task22_actions.json](prior-pro003/task22_actions.json)
- [prior-pro003/validate_delivery.py](prior-pro003/validate_delivery.py)
- [prior-pro003/validation_report.json](prior-pro003/validation_report.json)

### readiness

- [readiness/geometry-consumption.json](readiness/geometry-consumption.json)
- [readiness/monroe-original-evidence-corrections.json](readiness/monroe-original-evidence-corrections.json)
- [readiness/unimol2-v4-static-review.json](readiness/unimol2-v4-static-review.json)
- [readiness/TabM-memberloss-preparation-consumption.json](readiness/TabM-memberloss-preparation-consumption.json)

### methodology

- [methodology/scoring-and-publishing.md](methodology/scoring-and-publishing.md)
- [methodology/native-chat-transport.md](methodology/native-chat-transport.md)
- [methodology/RESEARCH_SKILL.md](methodology/RESEARCH_SKILL.md)
- [methodology/evidence-reuse.md](methodology/evidence-reuse.md)
- [methodology/retrieval-SKILL.md](methodology/retrieval-SKILL.md)
- [methodology/EXPERIMENT_DESIGN.md](methodology/EXPERIMENT_DESIGN.md)

### current

- [current/CURRENT_STATUS.json](current/CURRENT_STATUS.json)
- [current/LATE_OBSERVED_T2_STARTUP.json](current/LATE_OBSERVED_T2_STARTUP.json)

按Q1–Q7独立深入研究，可推翻已有判断；完整返回analysis.md、review.json、issues.json、next_batch_guide.md、next_experiments.json、search_space.json，可附有价值原件。报告实际读取覆盖、事实/推断/反证/未知及能改变决定的下一实验。原网关独立收发，发布方不向Pro发消息。
