# MoLFormer microsome4固定评分交付

4份111行wholeValid预测的固定Spearman评分完成；8个原factorial32 micro标量原样复用，组成12槽。8个MoLvsCheM/Mini固定head同seed主对比全部退化，四组两seed均no_support_for_this_recipe。MoL内部TabMvsMLP两seed均正，为辅对比分列。无后续epoch、种子、池化或ensemble自动授权。

| Run | 来源 | Spearman |
|---|---|---:|
| mf16-clearance_microsome_az-mlp-s46 | 本次新增 | 0.3923772173034321 |
| mf16-clearance_microsome_az-mlp-s47 | 本次新增 | 0.4254760407119383 |
| mf16-clearance_microsome_az-tabm-s46 | 本次新增 | 0.4322754114121354 |
| mf16-clearance_microsome_az-tabm-s47 | 本次新增 | 0.4561373538694306 |
| tm32-chemeleon-mlp-clearance_microsome_az-s46 | 旧值复用 | 0.4798665825199555 |
| tm32-chemeleon-mlp-clearance_microsome_az-s47 | 旧值复用 | 0.4562833390568778 |
| tm32-chemeleon-tabm-clearance_microsome_az-s46 | 旧值复用 | 0.5171237718739303 |
| tm32-chemeleon-tabm-clearance_microsome_az-s47 | 旧值复用 | 0.5178536978111669 |
| tm32-minimol-mlp-clearance_microsome_az-s46 | 旧值复用 | 0.5843645040264084 |
| tm32-minimol-mlp-clearance_microsome_az-s47 | 旧值复用 | 0.5829621583918003 |
| tm32-minimol-tabm-clearance_microsome_az-s46 | 旧值复用 | 0.5680716366060248 |
| tm32-minimol-tabm-clearance_microsome_az-s47 | 旧值复用 | 0.550416237780407 |

signed improvement为treatment−control，正值有利MoL/TabM；主辅对比全部保留。

| Comparison | 主/辅 | Treatment | Control | Delta | Outcome |
|---|---|---:|---:|---:|---|
| mf16-clearance_microsome_az-mlp-s46_vs_tm32-chemeleon-mlp-clearance_microsome_az-s46 | 主 | 0.3923772173034321 | 0.4798665825199555 | -0.08748936521652345 | loss |
| mf16-clearance_microsome_az-mlp-s46_vs_tm32-minimol-mlp-clearance_microsome_az-s46 | 主 | 0.3923772173034321 | 0.5843645040264084 | -0.1919872867229763 | loss |
| mf16-clearance_microsome_az-mlp-s47_vs_tm32-chemeleon-mlp-clearance_microsome_az-s47 | 主 | 0.4254760407119383 | 0.4562833390568778 | -0.0308072983449395 | loss |
| mf16-clearance_microsome_az-mlp-s47_vs_tm32-minimol-mlp-clearance_microsome_az-s47 | 主 | 0.4254760407119383 | 0.5829621583918003 | -0.157486117679862 | loss |
| mf16-clearance_microsome_az-tabm-s46_vs_tm32-chemeleon-tabm-clearance_microsome_az-s46 | 主 | 0.4322754114121354 | 0.5171237718739303 | -0.08484836046179495 | loss |
| mf16-clearance_microsome_az-tabm-s46_vs_tm32-minimol-tabm-clearance_microsome_az-s46 | 主 | 0.4322754114121354 | 0.5680716366060248 | -0.1357962251938894 | loss |
| mf16-clearance_microsome_az-tabm-s47_vs_tm32-chemeleon-tabm-clearance_microsome_az-s47 | 主 | 0.4561373538694306 | 0.5178536978111669 | -0.06171634394173625 | loss |
| mf16-clearance_microsome_az-tabm-s47_vs_tm32-minimol-tabm-clearance_microsome_az-s47 | 主 | 0.4561373538694306 | 0.550416237780407 | -0.09427888391097644 | loss |
| s46-MoLTabM_vs_MoLMLP | 辅 | 0.4322754114121354 | 0.3923772173034321 | +0.03989819410870332 | win |
| s47-MoLTabM_vs_MoLMLP | 辅 | 0.4561373538694306 | 0.4254760407119383 | +0.03066131315749226 | win |

全部12槽共用111行重复观察的Valid及raw43划分，两head seed不是独立化学holdout。MoL768、CheM2048、Mini512的表示、维度、缩放、容量和设备不同，只比较登记pipeline，不独立归因底座。MoL MLP197121、TabM1089568参数。当前4head各自实际GPU UUID已与Astra intake绑定；不据此假定整个MoL16只有一个GPU，producer身份继续保留在原源。没有追加epoch/任务池化/种子/ensemble搜索，也没有官方总分。

来源ceb37f36…与映射6509e244…绑定本机原SOURCE字节、原接收science-clearance_microsome_az-receipt02和Astra micro4 intake。四份444行原预测逐一核对task/split/原行号/Drug_ID/Drug及完整行数；空/重复ID按原行保留。9列原CSV只删除空Y/internal_partition并将parsed改名parse_ok、固定CRLF，原预测数值字符串、分子字符串与行序保持不变。旧8标量逐字段匹配固定factorial32源0f133d85…和相同truth/blind/metric/n身份。全部先冻结，再由私有固定入口读取一份111行原truth；6bound CSV首指标前全部通过，Spearman每份恰好一次。

原producer进程参数/buffer冻结、4真fit/600步、真实checkpoint、CPU reload、narrow file/write/mmap及传输验收由原Sol/Astra形成并已消费。本次直接复用，不重读模型/cache/trace或整树，不重演这些已验事实。固定公式与16项数学证明复用，无测试重跑；评分入口一次通过，无失败，无逐行Y或残差输出。原始失败与源证据仍由不可变源/原intake导航保留，不补造训练记录。

归档由原Sol独立进行。本批源清单340对象、270轻对象接收证明复用、70非轻对象按冻结截点记录；不修改源pending，也不以历史pending断言当前归档状态，不在此声称全归档验收。此执行者0旧指标/组/ensemble/stop/stress，0主机连接/网络数据/模型load-forward/训练/编码/发布/新角色。

精确文件：[4新分](scores.json)、[12槽](../../SOURCES.md#ref-907abce5aeffd2c9)、[10对比及组决策](comparisons.json)、[固定评分回执](../../SOURCES.md#ref-7a2d19940024d245)、[投影链](../../SOURCES.md#ref-5c3d971ac4e3b7ad)、[冻结](../../SOURCES.md#ref-473813473ff49467)、[来源采用](../../SOURCES.md#ref-a9d0069c36b93f77)、[coverage](../../SOURCES.md#ref-d94db09b30111b95)、[verification](../../SOURCES.md#ref-15b3c75e6ad1ecf1)、[timing](../../SOURCES.md#ref-f9e39fd6c90a9dba)。稳定结果已先直接回Astra，见[交接](../../SOURCES.md#ref-e743bf17f319a917)。
