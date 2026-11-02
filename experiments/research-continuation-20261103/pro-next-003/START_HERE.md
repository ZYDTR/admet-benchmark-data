# Pro003：完整历史与最新科学快照

本次截止时间为 **2026-11-02T21:11:09.516273+00:00**。先读 [CURRENT_STATUS](current/CURRENT_STATUS.json)：它覆盖旧报告中 pending 等时间状态；历史原文、负例和当时判断完整保留。不得从当前快照推断后来运行结果。

已完成 **686 个梯度头、665 个逻辑梯度 run**；整体 Valid 数值 **588**、原生 train.stress 数值 **88**。固定分组另有 **88 个数值、8 个受抑制项**；**95 个复合指标**另计。10 个历史未评分项仍未知。分组、视图、context fit 与物理梯度训练不能混计，不生成赛事总分。

## 研究入口

1. [Q1–Q6 与交付判据](decision-contract.json)、[实验纲领](methodology/EXPERIMENT_DESIGN.md)、[研究 Skill 3.4.1](methodology/RESEARCH_SKILL.md)、[验收边界](methodology/RESEARCH_ACCEPTANCE.md)、[证据复用](methodology/EVIDENCE_REUSE.md)、[阅读合同](READING_CONTRACT.json)。
2. [当前历史索引](ledger/history-index.json)、[686 头完整账本](ledger/experiments.json)、[问题与反证](ledger/issues.json)、[提案执行映射](ledger/proposal-execution.json)、[资产](ledger/assets.json)、[组合](ledger/ensembles.json)、[主张事件](ledger/claim-events.json)。
3. 前次 Pro002 的六份完整返回在下方逐一列出；其建议与本次新证据共同阅读，不能只采用摘要或丢弃反例。

## 本次新增证据与状态

- stress48 已完成：Mini PPBR/Sol/CYP 四 seed 均胜；Morgan AMES 0/4、Mini micro 1/4、Mini TabM DILI 0/4。原 rawValid 优势仍属真实但有限的证据。
- LD50 canonical Huber 两 seed 混合，四个 scaffold 槽按预设 fit<50% 跳过，未重抽。
- half-life ranking 对同 CPU fullMSE 四 seed、0.5MSE 四 seed 均胜；两个原生 train 结构划分、两个 seed 亦胜 0.5MSE。stress8 实际 288 steps；旧消息 348 的更正保留。原生分组不构成新的外部盲集。
- Mini hepatocyte rawValid 四 seed 均胜，scaffold 两 seed 均负、canonical 混合，不支持结构稳健性断言。
- MoLFormer Caco/micro 主比较各 8 负；DILI 3 胜 5 负，无一致替代收益；MoL 内 TabM 的 micro/DILI 增益不证明底座更好。
- M2 诊断表明 Mini PPBR/Sol/micro 在 constant-rule 后 floor 的 H0=F010，跳过 12 个等价拟合。固定分组只用预注册 cohort，88 数值、8 抑制，不新增训练。

尚在执行/准备的 CYP2D6 MoL 四项、TabICL16、AMES dual4、window12 和 M5/M6/几何资产，以 CURRENT_STATUS 和 decision-contract 为准：不得重复已派物理拟合或把多个策略视图当成拟合。它们在本截止时刻没有的结果不能补写为完成。

## 完整历史导航

- [上轮固定入口](https://github.com/ZYDTR/admet-benchmark-data/blob/f65d8149a897ea1db64c6f7cb16e52e06987229a/experiments/research-continuation-20261102/pro-next-002/START_HERE.md)、[完整历史分支索引](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f65d8149a897ea1db64c6f7cb16e52e06987229a/experiments/research-continuation-20261102/pro-next-002/HISTORY_BRANCH_INDEX.json)、[上轮完整账本](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f65d8149a897ea1db64c6f7cb16e52e06987229a/experiments/research-continuation-20261102/pro-next-002/ledger/experiments.json)、[上轮 manifest](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f65d8149a897ea1db64c6f7cb16e52e06987229a/experiments/research-continuation-20261102/pro-next-002/input-manifest.json) 和 [原件映射](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f65d8149a897ea1db64c6f7cb16e52e06987229a/experiments/research-continuation-20261102/pro-next-002/SOURCE_MANIFEST.json)。沿其链接可枚举更早 Mini22、失败、未就绪资产和各阶段正反证据；旧对象按固定 commit 复用。
- 本包完整科学投影及原件身份见 [SOURCE_MANIFEST](SOURCE_MANIFEST.json)；全部新对象及 SHA 见 [input-manifest](input-manifest.json)。[SOURCE_MAP](SOURCE_MAP.json) 与 [SOURCES](SOURCES.md) 逐项解析来源。
- `packet://path` 从本包固定 commit 解析；`evidence-ref:ref-ID` 为来源身份，reference-only 的底层原件未公开，不能声称已读。科学配置、所有数字、数组与负例保留；本机路径与操作身份转换不代表新资产。
- 仅提供经批准的汇总科学资料；外部权重与全部 buffer 冻结、train.Y 学习、fit/stop/stress 分离、保留原行、重复 Valid 选型历史与 Y 单位边界均继续适用。旧材料可见不扩大本次标签访问或执行权。

## 全部 50 份科学文件

### ledger

- [ledger/experiments.json](ledger/experiments.json)
- [ledger/ensembles.json](ledger/ensembles.json)
- [ledger/issues.json](ledger/issues.json)
- [ledger/claim-events.json](ledger/claim-events.json)
- [ledger/assets.json](ledger/assets.json)
- [ledger/proposal-execution.json](ledger/proposal-execution.json)
- [ledger/history-index.json](ledger/history-index.json)

### prior-pro002

- [prior-pro002/analysis.md](prior-pro002/analysis.md)
- [prior-pro002/review.json](prior-pro002/review.json)
- [prior-pro002/issues.json](prior-pro002/issues.json)
- [prior-pro002/next_batch_guide.md](prior-pro002/next_batch_guide.md)
- [prior-pro002/next_experiments.json](prior-pro002/next_experiments.json)
- [prior-pro002/search_space.json](prior-pro002/search_space.json)

### stress48

- [stress48/update.md](stress48/update.md)
- [stress48/results.json](stress48/results.json)

### LD50

- [LD50/update.md](LD50/update.md)
- [LD50/results.json](LD50/results.json)

### half-life

- [half-life/ranking8-update.md](half-life/ranking8-update.md)
- [half-life/halfMSE4-results.json](half-life/halfMSE4-results.json)
- [half-life/halfMSE4-update.md](half-life/halfMSE4-update.md)
- [half-life/stress8-results.json](half-life/stress8-results.json)
- [half-life/stress8-update.md](half-life/stress8-update.md)

### hepatocyte

- [hepatocyte/raw4seed-update.md](hepatocyte/raw4seed-update.md)
- [hepatocyte/stress8-results.json](hepatocyte/stress8-results.json)
- [hepatocyte/stress8-update.md](hepatocyte/stress8-update.md)

### cohort96

- [cohort96/REPORT.md](cohort96/REPORT.md)
- [cohort96/summary.json](cohort96/summary.json)
- [cohort96/comparisons.json](cohort96/comparisons.json)

### preparation

- [preparation/M2-scaling-adoption.json](preparation/M2-scaling-adoption.json)
- [preparation/mechanisms-adoption.json](preparation/mechanisms-adoption.json)

### new-assets

- [new-assets/monroe-feasibility.json](new-assets/monroe-feasibility.json)
- [new-assets/monroe-addendum.json](new-assets/monroe-addendum.json)
- [new-assets/unimol2-feasibility.json](new-assets/unimol2-feasibility.json)

### methodology

- [methodology/RESEARCH_SKILL.md](methodology/RESEARCH_SKILL.md)
- [methodology/EXPERIMENT_DESIGN.md](methodology/EXPERIMENT_DESIGN.md)
- [methodology/RESEARCH_ACCEPTANCE.md](methodology/RESEARCH_ACCEPTANCE.md)
- [methodology/EVIDENCE_REUSE.md](methodology/EVIDENCE_REUSE.md)

### molformer

- [molformer/caco/scores.json](molformer/caco/scores.json)
- [molformer/caco/comparisons.json](molformer/caco/comparisons.json)
- [molformer/caco/REPORT.md](molformer/caco/REPORT.md)
- [molformer/caco/astra-update.md](molformer/caco/astra-update.md)
- [molformer/micro/scores.json](molformer/micro/scores.json)
- [molformer/micro/comparisons.json](molformer/micro/comparisons.json)
- [molformer/micro/REPORT.md](molformer/micro/REPORT.md)
- [molformer/micro/astra-update.md](molformer/micro/astra-update.md)
- [molformer/dili/scores.json](molformer/dili/scores.json)
- [molformer/dili/comparisons.json](molformer/dili/comparisons.json)
- [molformer/dili/REPORT.md](molformer/dili/REPORT.md)
- [molformer/dili/astra-update.md](molformer/dili/astra-update.md)

### current

- [current/CURRENT_STATUS.json](current/CURRENT_STATUS.json)

研究按 Q1–Q6 深入完整相关分支和外部一手来源，给出有证据的采纳、否决或明确等待条件。完整返回 analysis.md、review.json、issues.json、next_batch_guide.md、next_experiments.json、search_space.json，并报告真实读取覆盖。研究不自动授权训练、评分或发布。原网关依据精确发布回执交付，本发布方不代发 Pro 消息。
