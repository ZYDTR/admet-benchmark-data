# 本批：既有六配置的新版本接续

**waiting_current_batch**。本页保存稳定任务与科学参考，不固定当前operator，不将派发或历史成功写作新完成。后续真实原件由主控核验后接入。

[主控实际任务与科学/资源边界](../../evidence/H-1c7a62b215d94513b377.json)

[当前接续意图与角色分工](../../evidence/H-c5a8d3a04166ac23d297.md.txt)

| 新run | 对应旧run | seed | 早停监控 | 当前交付状态 |
|---|---|---:|---|---|
|hainan-agentled-mse-s44-20261102|hainan-paired-mse-s44-20261101|44|internal_validation_standardized_mse|waiting_current_batch|
|hainan-agentled-mse-s45-20261102|hainan-paired-mse-s45-20261101|45|internal_validation_standardized_mse|waiting_current_batch|
|hainan-agentled-mse-s46-20261102|hainan-paired-mse-s46-20261101|46|internal_validation_standardized_mse|waiting_current_batch|
|hainan-agentled-mae-s44-20261102|hainan-paired-mae-s44-20261101|44|internal_validation_raw_mae|waiting_current_batch|
|hainan-agentled-mae-s45-20261102|hainan-paired-mae-s45-20261101|45|internal_validation_raw_mae|waiting_current_batch|
|hainan-agentled-mae-s46-20261102|hainan-paired-mae-s46-20261101|46|internal_validation_raw_mae|waiting_current_batch|

## 科学原件

- [configs/hainan-agentled-mae-s44-20261102.json](../../evidence/H-f683fc5886e4afbd76ef.json)
- [configs/hainan-agentled-mae-s45-20261102.json](../../evidence/H-439910f13ebc5ebf5df7.json)
- [configs/hainan-agentled-mae-s46-20261102.json](../../evidence/H-102f5d25fa7dd47f5deb.json)
- [configs/hainan-agentled-mse-s44-20261102.json](../../evidence/H-ac0ec151db9534d88017.json)
- [configs/hainan-agentled-mse-s45-20261102.json](../../evidence/H-4863689c4d801b1e8e4f.json)
- [configs/hainan-agentled-mse-s46-20261102.json](../../evidence/H-f7ac2778349c09d5e20f.json)
- [encoder.py](../../evidence/H-bab41f97fb5d2cfbc717.py.txt)
- [train_remote_v4.py](../../evidence/H-ddb484b8036bfe945679.py.txt)
- [training_science.py](../../evidence/H-3aa7fbd27c3e2a92579b.py.txt)

主控新任务沿用六个Caco2配置，CheMeleon冻结、MLP256、dropout0.1、AdamW/lr0.0005/wd0.0001、batch128，seeds44/45/46、raw-SMILES分组split43、standardized MSE学习，配对监控standardized MSE或raw MAE。新预算沿历史保守剩余5296.074905887725 GPU作业秒，资源等待/本地诊断分记；旧009和旧截止没有恢复。

未来合并时保留每run的真实来源、源码/输入/环境、训练/优化步、内部划分/预处理、head与恢复状态、原行预测、冻结及写入/资源退出证据。正文和来源表追加新版本，保留本历史快照；评分或发布需主控按实际结果另行接续。没有新CONTEXT_CONTRACT或旧脚本门槛。

[完整历史](../../history/README.md) · [当前规则](../../context/README.md) · [候选84fit的另行准备边界](../../research/breadth/README.md)
