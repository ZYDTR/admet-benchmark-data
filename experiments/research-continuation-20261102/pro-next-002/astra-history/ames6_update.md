# AMES四种子复验已满足预设判据

在同GPU2、原H140环境、相同2048维头容量和fit/stop划分下，Morgan identity+MLP对CheM H0的整体Valid AUROC四次均提高：44/45新种子约+0.009918/+0.030804，46/47同设备控制约+0.010248/+0.016241。6个新分数与2个既有Morgan分数构成8槽；旧值未重算。支持把该完整方案保留为AMES任务候选，不需要为本判据追加拟合。

原生train.stop却在四seed均显示CheM更高（CheM约0.894–0.902，Morgan约0.870–0.873）。同一模型优劣在内部stop和官方Valid上反转，是值得保留的划分适配信号；这里没有额外重算指标，也不能把差异归因于明确的分布机制或已修复样本错误。

AR001-13原固定高/低分歧群各114/1137原行保持不变，新增44/45的盲预测分歧已对应记录。没有逐行标签、残差或分组错误率，整体提升不能关闭具体错误机制问题。表示和缩放捆绑、SameValid反复选型限制保留；四seed不是独立数据集泛化证据。

完整逐seed数值与原生stop：packet://current/comparisons/00-ames-four-seed-comparisons.json
成员跟踪：evidence-ref:ref-9f5530846948b69b
模型30项与1原trace由原Sol独立归档。
