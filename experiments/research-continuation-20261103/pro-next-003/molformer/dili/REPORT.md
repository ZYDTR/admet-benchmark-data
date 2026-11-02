# MoLFormer DILI4固定评分交付

4份48行wholeValid预测的固定AUROC评分完成；8个已验factorial32 DILI标量原样复用，组成12槽。8个主对比为3胜5负：MLPvsCheM、MLPvsMini、TabMvsMini各一胜一负，均unresolved；TabMvsCheM两负，为no_support_for_this_recipe。MoL内部TabMvsMLP两个seed均正，仅为辅比较。

| Run | 来源 | AUROC |
|---|---|---:|
| mf16-dili-mlp-s46 | 本次新增 | 0.8241758241758241 |
| mf16-dili-mlp-s47 | 本次新增 | 0.8373626373626374 |
| mf16-dili-tabm-s46 | 本次新增 | 0.8307692307692308 |
| mf16-dili-tabm-s47 | 本次新增 | 0.843956043956044 |
| tm32-chemeleon-tabm-dili-s46 | 旧值复用 | 0.843956043956044 |
| tm32-chemeleon-tabm-dili-s47 | 旧值复用 | 0.8505494505494505 |
| hl140-base-dili-f010-s46 | 旧值复用 | 0.8461538461538461 |
| hl140-base-dili-f010-s47 | 旧值复用 | 0.8241758241758241 |
| astra001-minimol-dili-s46 | 旧值复用 | 0.8417582417582418 |
| astra001-minimol-dili-s47 | 旧值复用 | 0.8197802197802198 |
| tm32-minimol-tabm-dili-s46 | 旧值复用 | 0.8417582417582418 |
| tm32-minimol-tabm-dili-s47 | 旧值复用 | 0.8219780219780219 |

signed improvement为treatment−control，正值更优，主辅对比全部保留。

| Comparison | 主/辅 | Treatment | Control | Delta | Outcome |
|---|---|---:|---:|---:|---|
| mf16-dili-mlp-s46_vs_hl140-base-dili-f010-s46 | 主 | 0.8241758241758241 | 0.8461538461538461 | -0.02197802197802201 | loss |
| mf16-dili-mlp-s46_vs_astra001-minimol-dili-s46 | 主 | 0.8241758241758241 | 0.8417582417582418 | -0.01758241758241763 | loss |
| mf16-dili-mlp-s47_vs_hl140-base-dili-f010-s47 | 主 | 0.8373626373626374 | 0.8241758241758241 | +0.01318681318681325 | win |
| mf16-dili-mlp-s47_vs_astra001-minimol-dili-s47 | 主 | 0.8373626373626374 | 0.8197802197802198 | +0.01758241758241763 | win |
| mf16-dili-tabm-s46_vs_tm32-chemeleon-tabm-dili-s46 | 主 | 0.8307692307692308 | 0.843956043956044 | -0.01318681318681314 | loss |
| mf16-dili-tabm-s46_vs_tm32-minimol-tabm-dili-s46 | 主 | 0.8307692307692308 | 0.8417582417582418 | -0.01098901098901095 | loss |
| mf16-dili-tabm-s47_vs_tm32-chemeleon-tabm-dili-s47 | 主 | 0.843956043956044 | 0.8505494505494505 | -0.00659340659340657 | loss |
| mf16-dili-tabm-s47_vs_tm32-minimol-tabm-dili-s47 | 主 | 0.843956043956044 | 0.8219780219780219 | +0.02197802197802201 | win |
| s46-MoLTabM_vs_MoLMLP | 辅 | 0.8307692307692308 | 0.8241758241758241 | +0.006593406593406681 | win |
| s47-MoLTabM_vs_MoLMLP | 辅 | 0.843956043956044 | 0.8373626373626374 | +0.00659340659340657 | win |

全部12槽共用48行复用Valid/raw43划分，两seed不是独立holdout。MoL768、CheM2048、Mini512的底座、维度、缩放、容量和设备不同，比较登记pipeline，不独立归因底座。MoL MLP197121、TabM1089568参数；head与producer实际GPU身份分开绑定，不据此推断整个MoL16使用一个设备。不自动追加epoch/seed/池化/ensemble/子群查询，无官方总分。

源e3007619…与映射cf8e79d7…绑定本机原SOURCE字节、science-dili-receipt03及Astra DILI intake。四份192行原预测逐一核对task/split/原行号/Drug_ID/Drug与完整行数，空/重复ID按原行保留；所有概率为有限[0,1]。9列仅删除空Y/internal_partition、将parsed改名parse_ok并固定CRLF，数值字符串、分子字符串与原行顺序不变。旧8标量与固定factorial32源0f133d85…及truth/blind/metric/n身份逐字段一致。全部新预测及旧标量先锁定，再由固定入口读取一份48行原truth并验证二元标签；6bound CSV首指标前全部通过，各预测只调用一次AUROC。

原4真实head/276steps、producer原进程参数/buffer冻结、真实checkpoint、CPU reload、narrow file/write/mmap与传输验收直接复用Astra/原Sol已消费的证据，不重读模型/cache/trace或整树。按原intake编码口径，DILI新增60次实际forward，全局累计314，不能将分区累计296/302/314相加；此宿主执行者编码0。公式与16旧数学证明未变，无重跑，无逐行Y/残差输出。

覆盖计数修正：执行包装沿用了micro的静态prediction_rows=444，实际所有源/行验证/投影/固定读取都是4×48=192，指标始终正确。当前回执已仅把覆盖计数修正为192；原回执保存于raw/scoring-receipt-before-coverage-correction.json，manifests/coverage-counter-correction.json保留依据。执行脚本和INPUT_FREEZE原样保留。首次修正保存因raw目录未建而在写前停止，创建授权本地目录后完成；0额外真值或指标。真实固定评分入口只运行一次成功。

原Sol独立归档，源294对象含244轻对象接收证明与50非轻对象的冻结截点记录；不修改源pending，不以历史pending断言当前归档状态，也不在此冒称完整归档验收。此执行者0旧/组/ensemble/stop/stress指标，0主机连接/数据网络/模型load-forward/训练/编码/发布/新角色。

精确材料：[4新分](scores.json)、[12槽](../../SOURCES.md#ref-e1520700229e6ca3)、[10对比及组决策](comparisons.json)、[固定评分回执](../../SOURCES.md#ref-6e4d7a0bc0339219)、[投影链](../../SOURCES.md#ref-1ccfa3a074b6a168)、[冻结](../../SOURCES.md#ref-5b18971184d8e8da)、[来源采用](../../SOURCES.md#ref-46b8d05b128a6f9d)、[覆盖修正](../../SOURCES.md#ref-429a4353740330c1)、[coverage](../../SOURCES.md#ref-b9dc5ca0bef5cc08)、[verification](../../SOURCES.md#ref-7a0a9e1f37916af7)、[timing](../../SOURCES.md#ref-4d52ace2c75b042f)。稳定结果已先回Astra，见[交接](../../SOURCES.md#ref-ef72563b6a5a39bc)。
