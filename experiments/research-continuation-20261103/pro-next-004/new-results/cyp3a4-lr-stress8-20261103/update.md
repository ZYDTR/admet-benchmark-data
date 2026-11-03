# CYP3A4：较小学习率的结构分组验证

采用较窄的当前候选：CheM2048 H0 +MLP256/dropout0.1/AdamWwd1e-4/lr1e-4/batch128/max50pat8。两结构分组各两种子低LR均优于5e-4，配对init/fit统计/共同样本顺序核实；与既有Window12低LR支持一致。停止本问题追加LR/种子/长窗口；不推其他任务、F010或所有未测LR。原train回溯、stress成员有交集、重复选择史保留。

| 分组 | 种子 | lr5e-4 AP | lr1e-4 AP | 提升 |
|---|---:|---:|---:|---:|
|canonical|44|0.854368|0.858145|+0.003777|
|canonical|45|0.849205|0.852319|+0.003113|
|scaffold|44|0.836069|0.859648|+0.023579|
|scaffold|45|0.849360|0.856880|+0.007520|

8个新头、7152次更新、8个nativeStress AP；0新增Valid评分。canonical fit/stop/stress6039/863/1726，scaffold6038/863/1727。每组四个best先锁定后才预测与评分；全部原physical-last、optimizer和使用的RNG先保存再恢复best。两个原CPU学习作业共192.3655451652594秒，累计快照不求和；全流程与归档独立记录。

AP采用既验定义，官方AUPRC等价性尚未确认。原始完整档案由原执行者继续取回。
