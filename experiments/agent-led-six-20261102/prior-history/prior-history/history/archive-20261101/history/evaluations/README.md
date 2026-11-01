# 正式评分与评价使用史

[评价使用账](../evaluation-use-ledger.json) · [Mini22 精确逐任务结果](mini22-scores.json) · [既有 Caco2 汇总评分原值](existing-caco2-scores.json)

正式交付包含 22+2+1+1=26 个任务评分，来自五个完成学习的 run。一个 22 任务 Mini 基线与四个 Caco2 run 不能写成五组 22 任务。历史所有探索及独立复算的终身真值访问次数未完整登记，null 不是 0。此阶段指标调用与新真值数据集读取均为 0。

| 任务 | 指标 | 既有数值 | 行数 |
|---|---|---:|---:|
|ames|AUROC|0.7966064051881135|1137|
|bbb_martins|AUROC|0.8936738752174994|203|
|bioavailability_ma|AUROC|0.7441860465116279|64|
|caco2_wang|MAE|0.4260650306813186|91|
|clearance_hepatocyte_az|Spearman|0.35760632366306705|122|
|clearance_microsome_az|Spearman|0.48732952225400383|111|
|cyp2c9_substrate_carbonmangels|AUPRC|0.42099418064714555|67|
|cyp2c9_veith|AUPRC|0.7594504271256293|1210|
|cyp2d6_substrate_carbonmangels|AUPRC|0.46377724431807144|67|
|cyp2d6_veith|AUPRC|0.6907342342611147|1313|
|cyp3a4_substrate_carbonmangels|AUROC|0.7293906810035843|67|
|cyp3a4_veith|AUPRC|0.877172798563802|1233|
|dili|AUROC|0.8615384615384616|48|
|half_life_obach|Spearman|0.0737000716718027|67|
|herg|AUROC|0.8968253968253969|66|
|hia_hou|AUROC|0.9666666666666667|58|
|ld50_zhu|MAE|1.0435887458260573|1937|
|lipophilicity_astrazeneca|MAE|0.53964650071|420|
|pgp_broccatelli|AUROC|0.9054017737167428|122|
|ppbr_az|MAE|20.83183522548387|279|
|solubility_aqsoldb|MAE|11.113363941834361|2940|
|vdss_lombardo|Spearman|-0.016927405626888218|113|

## 后续 Caco2 既有结果

| run | MAE |
|---|---:|
|hainan-frozen-training-20261031|0.37862513598901104|
|hainan-skill-follow-20261031|0.3891885939780218|
|hainan-index-cycle-20261031|0.42147216141758237|
|hainan-mae-monitor-20261101|0.40302117308791197|

这些是已有 valid 评价，不构成独立最终泛化结果。上轮 MSE/MAE 选轮差异伴随浮点特征缓存微差，不能仅凭两次结果宣称 monitor 的因果效果。新六 run 批次将单独登记实际缓存、配对种子、评分与后续决策用途。
