# 六任务、48个头的分组压力测试结果

48个登记头全部完成，24个预先登记的成对比较均有结果。Astra已核对六任务的本机原样来源索引、轻包及所有索引文件，核对了原进程实际学习、同组划分、fit-only统计、beststop选择后stress仅一次和全行预测重载证据。没有新增private Valid评分，没有重新编码。模型大包和全批CPU写轨迹审计另行收尾；这不是整个研究结束。

表中正值表示候选优于CheMeleon：MAE是CheM−候选，AUROC/Spearman/AP是候选−CheM。前四任务用MLP256；CYP2D6/DILI两边均用TabM。MiniMol使用H0，CheM在AMES为H0、其他为原F010，Morgan为identity，因此比较的是已冻结的整套表示/预处理配方。

| 任务与候选 | 指标 | canonical44 | canonical45 | scaffold44 | scaffold45 | 改善配对 |
|---|---|---:|---:|---:|---:|---:|
| AMES（Morgan） | AUROC | -0.022999 | -0.016925 | -0.054387 | -0.057044 | 0/4 |
| PPBR（MiniMol） | MAE | +0.475969 | +0.468672 | +0.402558 | +0.051680 | 4/4 |
| 溶解度（MiniMol） | MAE | +0.031803 | +0.023715 | +0.078114 | +0.033481 | 4/4 |
| 微粒体清除率（MiniMol） | Spearman | -0.071022 | -0.028897 | -0.017782 | +0.022789 | 1/4 |
| CYP2D6（MiniMol+TabM） | AUPRC | +0.038497 | +0.040500 | +0.051035 | +0.051984 | 4/4 |
| DILI（MiniMol+TabM） | AUROC | -0.070489 | -0.067669 | -0.017989 | -0.009524 | 0/4 |

PPBR、溶解度、CYP2D6三项的MiniMol在两种分组和两个模型seed下均改善。溶解度、CYP2D6同时延续既有Valid四seed的方向，证据更强；PPBR强化了条件候选，但历史Valid seed46的反例仍保留。

AMES的Morgan此前四seed Valid及固定Valid群优势没有转移到当前分组stress，当前stop也四组落后，因此不再将其描述为稳定替代。微粒体清除率的MiniMol只赢一组，应收窄为划分依赖候选。DILI中MiniMol+TabM四组均低于CheM+TabM，这条配方当前不优先；不据此否定尚未测试的读出或其他任务。

这些是CPU上同批匹配配方的比较。与先前GPU结果之间同时存在分区成员、fit数量、stop集合及平台变化，不能将跨批反转单独归因为分子骨架、容量或数值误差。每种scheme两个seed共享stress分子，不是两个独立数据集；所有stress分子来自历史已用官方train，不能称全新独立holdout。AUPRC沿用固定average_precision实现，与官方具体口径的等价性仍未新增证明。

原worker报告1843.198455 CPU作业墙钟秒（约30.72分钟）、17823次优化步，GPU作业0，峰值RSS约1.60GB。各任务的learning_and_export_wall_seconds是该任务首个开始至最后完成的跨度，CYP先跑首对、后跑余项，中间穿插其他任务，因此这些跨度重叠，不能相加冒充总计算时间。最终批次审计与全量归档另行核对。

下一步继续已派LD50的4个合格canonical头（scaffold因fit比例不足预先跳过，不能补抽），以及半衰期排序损失8头。后者包括4个同CPU MSE对照，避免平台混杂；全部beststop与blind预测冻结后再单独派一次固定Valid评分。TabICL/MoLFormer仍须完成真实入口修复和主机资源验证后试跑。当前结果已经更新下一步，不用相同配方盲加seed追正例。

完整数值与每个run的来源：[verified-light-science.json](results.json)。
