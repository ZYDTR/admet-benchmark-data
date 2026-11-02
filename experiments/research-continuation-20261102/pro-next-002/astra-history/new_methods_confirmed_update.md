# 新方法已经实测，下一步按任务采用

用户提供材料带来的直接新动作是接入TabM，并和原已在接入队列的MiniMol形成四任务32评价槽。首轮已全部真实学习和评分；随后26项同设备、新种子复验也已完成评分。所有预训练权重冻结，旧模型/分数复用，无重复拟合。以下是目前能据实际证据采用的结论。

| 任务 | 保留方案 | 同设备四种子结果 | 判断 |
|---|---|---|---|
| Solubility溶解度 | MiniMol512 H0 + MLP | MAE约1.066–1.088，对照CheM约1.409–1.525；4/4改善 | 预设判据满足 |
| 肝微粒体清除率 | MiniMol512 H0 + MLP | Spearman增量+0.049–+0.127；4/4改善 | 预设判据满足；Mini换TabM首轮反而两次下降 |
| CYP2D6 Veith | MiniMol512 H0 + TabM | 对CheMTabM AP增量+0.048–+0.075；4/4改善 | 预设判据满足 |
| CYP2D6同Mini换头 | TabM相对MLP | AP增量+0.0007–+0.0124；4/4改善 | 方向一致，但额外增益较小 |
| PPBR | MiniMol512 H0 + MLP | 3/4改善，seed46反例约+0.0387 MAE | 未满足四seed全改善标准，仍是有希望的限定候选 |
| AMES（另6项已完成复验） | Morgan2048 identity + MLP | AUROC四seed均高于同设备CheM H0 | 预设判据满足；内部stop排序反转限制保留 |

Caco2的CheM+TabM两个seed优于本轮MLP，但部分已有Huber配置更好，且三项Caco TabM达到原50epoch上限；它不是已证明的全历史最佳。DILI未呈稳定收益，当前不扩这个新组合。

本次确认选择的是完整配方，而非单独底座或集成机制。相同GPU/环境仍保留表示缩放、输入维度与头容量差异。SameValid反复选型和四个随机seed不等于独立数据集泛化；未做新的分组真值诊断，不把无标签预测分歧叫作已修复错误。TabICLv2、Monroe等材料中的其他路线仍是待准备候选，没有冒充已运行。

现在可以把溶解度MiniMLP、清除率MiniMLP、CYP2D6 MiniTabM及AMES Morgan纳入后续任务级候选比较，保留各自四seed完整结果。当前这26项复验的科学问题已收口，不自动追加新seed、融合或提交官网。两批模型/trace归档已全部完成，首轮Production52和TabM22完整原件也已收齐；最新归档采用记录见mini-task-confirm14-20261102/controller/confirm14-archive-complete-intake.json。

完整精确结果与证据：

- Mini12：packet://current/comparisons/01-four-seed-comparisons.json
- Confirm14：packet://current/comparisons/02-four-seed-comparisons.json
- AMES：packet://current/comparisons/00-ames-four-seed-comparisons.json
- 首轮32槽：packet://current/comparisons/03-factorial32-comparisons.json
