# 当前六任务24项

全部24个模型及151760行train/valid/test预测已由主控独立验收。固定宿主评分现已完成24/24，主控独立评分验收另行记录。H0/H1为dropout0.1/0.3，model seeds44/45，split seed43；全部配置在评分前冻结。

先读[完整分数与比较](validation-report.md)、[24项原始汇总分数](scores.json)、[配对和历史对照](paired-and-history.json)，再沿[逐模型完整索引](runs.json)下钻。[预测分布诊断](prediction-distributions.json)只用已保存预测，不含valid真值或残差。

lipo两seed偏向H1，CYP2D6与solubility两seed偏向H0；BBB/hepatocyte/LD50方向不一致。LD50和solubility有极端预测与大幅波动，保存原尺度和全行结果，不做事后修剪。与Mini22的跨配置变化是历史对照。两seed及复用valid仅支持描述性研究。

[评分使用登记](evaluation-use-ledger.json)：新增24次正式任务评分，累计56次；新增24个完成模型run，累计35个完成逻辑run，Mini22一组仍按1逻辑run/22任务头计。失败BBB父尝试的学习步数未知，未补0。没有新增训练、官网上传或新的Pro发送。

运行失败与科学可用分开，详见[质量与限制](quality-and-limits.md)。
