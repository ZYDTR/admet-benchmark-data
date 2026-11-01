# 本批六配置：2完成、1partial、3未开始

**主控已接受两项科学产物、只读取回与固定评分用于分析。共享影响未通过，整个训练Skill及六项闭环尚未验收通过。**

| 配置 | 状态 | official_valid MAE | 保存进度 |
|---|---|---:|---|
| MSE选轮 seed44 | 完成并评分、主控已复核 | 0.41727108770329663 | 20轮/100步，best第12轮 |
| MSE选轮 seed45 | 完成并评分、主控已复核 | 0.4477993207692307 | 39轮/195步，best第31轮 |
| MSE选轮 seed46 | partial，仍未完成 | 未评分 | 持久30步/6轮checkpoint，未执行接续 |
| MAE选轮 seed44 | 未开始 | 未评分 | 无完成产物 |
| MAE选轮 seed45 | 未开始 | 未评分 | 无完成产物 |
| MAE选轮 seed46 | 未开始 | 未评分 | 无完成产物 |

六项沿用冻结CheMeleon SHA c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651、2048→256→1新MLP、dropout0.1、AdamW lr0.0005/wd0.0001、batch128、最多50轮/patience8、模型seeds44/45/46、raw-SMILES分组split43。损失为standardized MSE，配对改变早停监控standardized MSE或raw MAE。两项各637train、91valid、182test，内部573fit/64stop。seed45复用已核验冻结表示，不能写成第二次完整CUDA编码；新头仍有实际CUDA更新。

MAE两项都未优于此前四海南run中最佳0.37862513598901104。旧配置/seed/split不同，两个分数不能作因果归因；三个MAE选轮未完成，也无法判定MSE与MAE选轮孰优。两个模型具有不同随机种子，不构成显著性结论。

## 先看裁定和完整诊断

- [主控独立验收全文](../evidence/documents/M-caca9559de3b2d3ed93e.md) · [精确采纳范围](../evidence/objects/40f87ace4af8ff65ab46f673394169f05aeb7987676e37de0809ca41325d6a99.json)。
- [固定分数与完整聚合诊断](../evidence/objects/7e0d8a9ff81657e4de4dd6effe3b5ab5f10302ecc1fdfd71c56b004e929708a3.json) · [历史同口径比较及限制](../evidence/objects/3e6dd39ede6e5da9d269475ebafb5d3b05bf0a966c2b3c2a88e0be52bd618620.json)。
- [真实张量/优化器/RNG/CPU预测重建复核](../evidence/objects/65481b9ae3bb7b997bafb9fd38f72d74c5123dd80a274587a1ca9a61a9cb5da2.json)。
- [执行方封存终态及未知项](../evidence/objects/ddbc07e548ce650bcf8e8985cd911ca9ab461eb4d11b50d8cf0a1884e915529d.json) · [主控封存581件与57分11秒原生任务验收](../evidence/documents/M-7008407d3f87b122aa4a.md)。
- [全部两项原件、来源和逐run入口](evidence.md) · [失败与资源资格](failures-and-resources.md)。

成功两项不重训。计算初始额度5296.074905887725作业秒，六次尝试消耗193.1029941495508，剩余5102.971911738175；这是包含导入/CPU的完整程序秒，纯kernel时间未知。剩余4项等待安全资源或主控后续版本化决策。长时段GPU1离散低负载记录已交原执行方重新判断，未证明训练已继续，也不等于无条件共享许可。
