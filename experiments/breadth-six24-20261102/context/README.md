# 本批规则和评价边界

用户确认允许外部预训练但必须冻结；训练只更新新头，train.Y学习、内部stop早停，valid/test给训练方保持盲输入。本指定宿主取回角色使用登记完整valid固定评分；公开新增范围仅任务级汇总和技术诊断。没有逐行valid真值、残差、可查表答案或极小分组差分输出。

赛事公开原文、用户确认、本地控制和实际实现分开。参考[上一批固定规则入口](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/context/README.md)及[source-index](../evidence/source-index.json)中的本次冻结项目入口/policy/角色规范。连接规范只保留私有原件身份，不进入公开材料。

MAE越低越好；AUROC、AP、Spearman越高越好。AP采用分数并列分组Average Precision，AUROC为Mann–Whitney平均秩，Spearman为平均秩Pearson。官方AUPRC等价性及官方综合公式未确认，不造官方总分。训练loss、内部stop和外部valid三者独立记。

全部24项已先验登记，当前只取回与评分。研究可提出新方向，实际新增训练、seed46、60档、最终train+valid合训和官网上传均由后续具体决定控制。


本次具体[取回合同](RETRIEVAL_TASK.json)、[24项评分合同](SCORING_TASK.json)，以及冻结宿主[严格全批入口](../host-scoring/strict_batch_scorer.py.txt)、[固定数学函数](../host-scoring/fixed_metrics.py.txt)、[16项合成反例](../host-scoring/test_synthetic.py.txt)、[既有合成结果](../host-scoring/synthetic-results.json)与[固定来源](../host-scoring/metric-origin.json)原文可直接审读；代码以文本展示，不执行返回模型。
