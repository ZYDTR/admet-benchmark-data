# 六项科学训练与固定评分全部完成

主控已独立验收两阶段取回、六份完整91行MAE及真实模型/恢复/盲预测证据。当前没有剩余学习或pending评分；整批公开/Pro往返仍待后续完成。

| 监控 | seed | official_valid MAE，越小越好 | epoch / best | 总步 / 从断点沿用 |
|---|---:|---:|---|---|
|MAE|44|0.4068564265494504|17 / 9|85 / 0|
|MSE|44|0.41727108770329663|20 / 12|100 / 0|
|MAE|45|0.43222243850549447|14 / 6|70 / 0|
|MSE|45|0.4477993207692307|39 / 31|195 / 0|
|MAE|46|0.4296442182637361|23 / 15|115 / 0|
|MSE|46|0.4290186062747252|37 / 29|185 / 30|

六配置均为冻结CheMeleon、2048→256→1新头、dropout0.1、AdamW lr0.0005/wd0.0001、batch128、最多50epoch/patience8、raw-SMILES grouped split43、573fit/64stop。学习loss均为standardized MSE；配对仅更改内部选轮monitor为standardized MSE或raw MAE。配置逐seed只有run_id/monitor不同，但运行GPU、控制实现、缓存和seed46恢复历史有差异。

MAE选轮减MSE选轮的保存模型valid MAE：seed44=-0.010414661153846205，seed45=-0.015576882263736214，seed46=+0.0006256119890108991。MSE组三seed均值0.43136300491575086，MAE组0.4229076944395603。MAE选轮两胜一负，平均差约-0.00845531；3seed和复用valid只支持描述性比较。本批最好0.4068564265494504，未超过历史最好0.37862513598901104；历史配置混杂，无法据此作因果归因或声明显著性。

## 主控裁定与固定诊断

- [完整六项主控验收](../evidence/documents/F-97d460ac6baee86fe885.md)
- [主控六项比较](../evidence/objects/662844bce191ed4b5397477125476c40d53d04037c2fa6c9b43861cc1240d40e.json)
- [逐seed配置差异、分数差和限制](../evidence/objects/61f8795f1040539fb3e67a50d4a9a67a3e397bec6df2ab3ab67911e5498357b9.json)
- [新四项固定聚合诊断](../evidence/objects/f37f584c8ced3b83a796fac05b9becee14d653a6e0a9bbac35e5597b794fb2e8.json)
- [先两项固定聚合诊断](../prior-history/evidence/objects/7e0d8a9ff81657e4de4dd6effe3b5ab5f10302ecc1fdfd71c56b004e929708a3.json)
- [新四项Decimal50独立复算](../evidence/objects/36ba63c873dff3153aad0806c97cb8fe1ebf074f1894de3341bbb14d3cd04a96.json)

先两项未重评；新四项各评分一次。科学与行身份、冻结、真实序列化head/optimizer/RNG与CPU盲预测重建均有主控原件，见[证据页](evidence.md)。本轮研究可用不豁免GPU0失败；[共享/恢复与失败](failures-and-resources.md)另列。
