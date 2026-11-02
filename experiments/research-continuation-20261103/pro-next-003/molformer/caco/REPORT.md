# MoLFormer Caco四头固定评分交付

4份新完整Valid预测已按固定评分器各计算一次，8个已验旧标量原样复用，组成12槽。无旧/组/ensemble/stop/stress重算。

决策：descriptive_registered_recipe_comparisons_only。

MoLvsCheM/Mini的8个固定head同seed比较全部退化，四组各两seed均为no_support_for_this_recipe。MoL内部TabM对MLP一胜一负，仍未解决。MoL768、CheM2048、Mini512的底座、缩放、维度和首层容量不同，比较完整pipeline。MoL MLP197121参数、TabM1089568参数。producer/MLP实际GPU3、TabM实际GPU2；逐run实际UUID和Astra intake已绑定，没有单UUID要求。TabM两seed触及50epoch，无追加epoch授权。原SCI01单UUID报告拒绝及hidden_dim构造失败保留，没有重训已完成模型。全部12槽共用91行Valid/raw43，不是独立holdout，不做事后赢家ensemble或官方总分。

| Run | 来源 | 指标 | N | Value |
|---|---|---|---:|---:|
| mf16-caco2_wang-mlp-s46 | 本次新增 | MAE | 91 | 0.4550803332159369 |
| mf16-caco2_wang-mlp-s47 | 本次新增 | MAE | 91 | 0.4121863990983842 |
| mf16-caco2_wang-tabm-s46 | 本次新增 | MAE | 91 | 0.4190882376353298 |
| mf16-caco2_wang-tabm-s47 | 本次新增 | MAE | 91 | 0.4197524988773911 |
| tm32-chemeleon-tabm-caco2_wang-s46 | 旧值复用 | MAE | 91 | 0.3456691745369795 |
| tm32-chemeleon-tabm-caco2_wang-s47 | 旧值复用 | MAE | 91 | 0.3453513071087541 |
| hl140-base-caco2_wang-f010-s46 | 旧值复用 | MAE | 91 | 0.3545367803771313 |
| hl140-base-caco2_wang-f010-s47 | 旧值复用 | MAE | 91 | 0.3662417954042883 |
| astra001-minimol-caco2_wang-s46 | 旧值复用 | MAE | 91 | 0.3769815916969229 |
| astra001-minimol-caco2_wang-s47 | 旧值复用 | MAE | 91 | 0.4056833441036455 |
| tm32-minimol-tabm-caco2_wang-s46 | 旧值复用 | MAE | 91 | 0.3584183169671808 |
| tm32-minimol-tabm-caco2_wang-s47 | 旧值复用 | MAE | 91 | 0.3590589838353953 |

signed improvement正值表示treatment更优。Spearman采用treatment−control，MAE采用control−treatment。

| Comparison | 主/辅 | Treatment | Control | Signed improvement | Outcome |
|---|---|---:|---:|---:|---|
| mf16-caco2_wang-mlp-s46_vs_hl140-base-caco2_wang-f010-s46 | 主 | 0.4550803332159369 | 0.3545367803771313 | -0.1005435528388056 | loss |
| mf16-caco2_wang-mlp-s46_vs_astra001-minimol-caco2_wang-s46 | 主 | 0.4550803332159369 | 0.3769815916969229 | -0.07809874151901403 | loss |
| mf16-caco2_wang-mlp-s47_vs_hl140-base-caco2_wang-f010-s47 | 主 | 0.4121863990983842 | 0.3662417954042883 | -0.04594460369409592 | loss |
| mf16-caco2_wang-mlp-s47_vs_astra001-minimol-caco2_wang-s47 | 主 | 0.4121863990983842 | 0.4056833441036455 | -0.006503054994738633 | loss |
| mf16-caco2_wang-tabm-s46_vs_tm32-chemeleon-tabm-caco2_wang-s46 | 主 | 0.4190882376353298 | 0.3456691745369795 | -0.07341906309835028 | loss |
| mf16-caco2_wang-tabm-s46_vs_tm32-minimol-tabm-caco2_wang-s46 | 主 | 0.4190882376353298 | 0.3584183169671808 | -0.06066992066814891 | loss |
| mf16-caco2_wang-tabm-s47_vs_tm32-chemeleon-tabm-caco2_wang-s47 | 主 | 0.4197524988773911 | 0.3453513071087541 | -0.07440119176863702 | loss |
| mf16-caco2_wang-tabm-s47_vs_tm32-minimol-tabm-caco2_wang-s47 | 主 | 0.4197524988773911 | 0.3590589838353953 | -0.06069351504199588 | loss |
| s46-MoLTabM_vs_MoLMLP | 辅 | 0.4190882376353298 | 0.4550803332159369 | +0.03599209558060718 | win |
| s47-MoLTabM_vs_MoLMLP | 辅 | 0.4197524988773911 | 0.4121863990983842 | -0.007566099779006963 | loss |

四份新预测的来源SHA、task/split/原行号/ID/Drug及完整行数在真值前核对并冻结，8旧标量逐字段对应原固定来源、truth/blind/metric身份。9列原CSV仅移除空Y/internal_partition、将parsed改名parse_ok并固定CRLF；原数值字符串、分子字符串和行序保持。固定入口读取一份登记真值，6bound CSV均在首指标前通过，公式16项旧数学验收复用，不重复测试。无逐行Y/残差导出。

原接收方已验传输和Astra已消费的实际学习/冻结/原CPU reload/写入/设备/匹配证据直接引用，不重读模型、cache、trace或整树。原Sol独立归档，不把源历史pending改写或冒称当前完整归档验收。此执行者0主机连接/网络数据/模型加载或forward/训练/编码/发布/新角色。

材料：[4新分](scores.json)、[12槽](../../SOURCES.md#ref-d292e35d910a0e80)、[全部对比](comparisons.json)、[评分回执](../../SOURCES.md#ref-1c8ef6da46e58a70)、[来源](../../SOURCES.md#ref-323e465705337344)、[冻结](../../SOURCES.md#ref-fa92e5ca85362535)、[投影链](../../SOURCES.md#ref-e56292ce9d3f4e3d)、[coverage](../../SOURCES.md#ref-cc7012590729f359)、[verification](../../SOURCES.md#ref-6b5505503c427b70)、[timing](../../SOURCES.md#ref-472681503b5fe024)。稳定结果已先回Astra，见[交接](../../SOURCES.md#ref-0ebf91f5a5b1fa23)。
