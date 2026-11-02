# 结构分组20项：相同成员上的缩放比较

D20与Morgan E16共36项学习完成，7086优化步、173.637 GPU作业秒；D的20个原生压力测试指标已消费，E16已交原评分方。MiniMol另16项仍由原Sol继续，不能把36项称作MiniMol完成。

本次D在训练标签池内先冻结fit/stop/stress完整分子组，stop选最佳轮次，stress在之后只评分一次。同任务、同分组方案的H0/F010/F001共享完全一致的成员；下表都是同一组成员上的比较。完整组身份沿用原AR001-03 cohort_id与原输入版本，不另选最有利子群。

|任务|分组|人数|指标|H0|F010|F001|
|---|---|---:|---|---:|---:|---:|
|dili|canonical|66|AUROC|0.837406|0.854323|0.859023|
|dili|scaffold|66|AUROC|0.792593|0.863492|0.802116|
|cyp2c9_substrate_carbonmangels|canonical|93|AUPRC|0.310092|0.413788|未测试|
|cyp2c9_substrate_carbonmangels|scaffold|94|AUPRC|0.424992|0.370097|未测试|
|half_life_obach|canonical|93|Spearman|0.066833|0.059072|0.079005|
|half_life_obach|scaffold|93|Spearman|0.120091|0.134022|0.137492|
|solubility_aqsoldb|canonical|1009|MAE|0.676777|0.671423|未测试|
|solubility_aqsoldb|scaffold|1009|MAE|0.795611|0.804491|未测试|

DILI的F010在canonical与scaffold组都优于H0，AUROC分别增加0.01692与0.07090；F001也均高于H0，但scaffold上F001明显低于F010，不能把正式Valid上F001的好结果推广成所有化学群都最好。

CYP2C9 substrate的F010在canonical组AP增加0.10370，在scaffold组却下降0.05489。half-life与solubility的F010方向同样随分组方式改变。half-life的F001在两组均优于H0/F010，但绝对Spearman仍只有0.07900与0.13749，且只有一个训练种子；这是有限支持，不是解决泛化问题。

F010对H0共8组中5改善、3退步；F001对H0的4组均改善，对F010为3改善、1退步。这个计数只描述已测试组，不能当跨指标总分、显著性或普适胜率。

AR001-03现已从只有划分风险假设推进到8个固定完整成员群的实际同组比较，但问题未关闭。所有成员来自历史使用过的官方train，属于回顾性结构压力测试；仅seed47、每种方法一个划分，跨canonical/scaffold比较还同时改变fit/stop/stress成员。仍不能断言已消除泄漏、发现真实误差机制，或获得独立未来化学泛化。

兼容故障保留：第一job完成8项后，在第9项学习前被诊断mean的Python加法版本差异拦下。原8不重放，独立18与10接续。正式补充仅把审计mean改为显式逐项累加，原划分/标签/scaler/模型数学不改，严格JSON比较继续；原执行者报告8记录精确复现及3个负例均拒绝。

完整来源与逐组配对见 [group20-stress-results.json](../SOURCES.md#ref-6c2002bc62ed162b)；固定成员索引见 [原cohort-index](../SOURCES.md#ref-16f2da438242992a)。本研究没有重算20个指标或读取Valid真值。
