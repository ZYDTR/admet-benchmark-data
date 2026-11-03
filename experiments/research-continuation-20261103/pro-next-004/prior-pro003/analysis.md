# ADMET 第三轮独立研究：把局部收益转化为可判别的迁移实验

**请求** `admet-pro-next-research-20261103-003`  
**固定输入** commit `f9bce86edb177a6b74f0af7a2e630a1350de914b`；manifest SHA256 `c61e67a6dc85e2aada50e0a46b6d9a9d7241b385f26f15629ab5ecce790d0eb8`。  
**证据截止** 2026-11-02T21:11:09.516273+00:00。此后现场状态未知。  
**结论状态** `needs_evidence`：Q1/Q2/Q3/Q5/Q6在证据解释与可执行设计层作答；Q4对部分“实际运行版本—公开候选版本”来源绑定保留`partial`。不是所有因果问题已经解决，也不是执行授权。  
**边界** 只读研究；本轮没有训练、模型加载、编码、推理、context fitting、安装、远端操作、Agent派发、赛事提交或新增质量评分。既有评分/冻结/运输验收按原回执复用。源中的旧pending和旧准备失败是历史，不覆盖本轮CURRENT_STATUS。

文内`[E-*]`、`[H-*]`、`[X-*]`分别指本轮材料、历史分支、官方一手来源，均在`evidence_registry.json`中解析到精确URL、版本和实际读取范围。读过索引不等于读过每一原件。新数值只做已验汇总的差值、计数、参数量和预算算术，见`aggregate_inputs_and_new_checks.json`及`validation_report.json`。

## 0. 决策摘要

本轮最重要的变化不是“又多了一批正例”，而是三个命题的适用范围被明显区分。

**第一，半衰期排序项获得了比上轮更强的局部支持。** 排序配方相对同系数0.5MSE控制，在四个已用Valid种子及canonical/scaffold两划分各两种子均正向。因此，“只是把MSE乘0.5”不再是足够解释。但这仍不能单独证明它精确优化了Spearman、排除梯度/正则/早停机制，或证明所有排序任务受益。最有信息量的下一步是另外三个Spearman任务的受控迁移，不再追加半衰期seed。[E-HALFMSE, E-HLSTRESS]

**第二，MiniMol不是一个跨任务、跨划分的统一改进。** Sol和CYP2D6 Veith、以及PPBR当前结构配方保留支持；microsome与hepatocyte各只有一项结构配对改善。AMES的Morgan与DILI的MiniTabM在当前四项结构配对全部负。这些反例不抹去rawValid结果，却推翻“rawValid优势已证明结构稳健性”的扩大解释。[E-STRESS48, E-HEPSTRESS, H-AMES, H-MINISOL, H-CONFIRM14]

**第三，无信息量的拟合应当停止，缺失的判别才值得新增。** MiniMol在PPBR/Sol/micro当前raw-fit上的H0与F010实际分母相同；M2的12项skip有科学依据，不是队列缺口。已派dual4、window12、MoL余4、TabICL16和准备中的M5/M6都不重新登记。推荐中档44项新梯度fit：先28项CheM排序迁移与必要VDss基准，再16项Mini交互。条件储备最多22项，总上限66；不是必须用满。[E-M2, E-STATUS]

### Q1–Q6直接答案索引

| 问题 | 本轮答案 | 限制／待补 | 主位置 |
|---|---|---|---|
| Q1 | 按全部22任务保留、限定、否决当前配方或等待既派结果；不把表示＋缩放＋头部的效果叫表示单因素因果 | 没有全局最优模型或未触及终评保证 | §2，task22_actions.json，claim_events.json |
| Q2 | 不新增半衰期；三Spearman任务固定0.5系数与两种native分区；clearance增加两表示的loss交叉 | 实际rank目标序列化block须绑定已验父配置；VDss分区需零fit物化 | §3，R28/X16矩阵 |
| Q3 | 分别检验样本支持、选择器、化学邻域、平台与表示/容量；低分歧不是无误差 | 个体共同错误尚未定位；8抑制不推断类别数 | §4，cohort_register.json |
| Q4 | 限定MoL已测负配方，等待CYP/TabICL；几何仅做有准入门槛的Sol/micro面板 | 当前mf16与TabICL权重链的部分公开leaf为reference-only；无几何疗效 | §5，scientific_assets.json，evidence_gaps.json |
| Q5 | dual/window是共享轨迹的选择策略；M5/M6尚不能完全隔离成员监督与容量，只有T/K条件对照补缺 | 不重复原轨迹；尚无结果不声称哪一解释胜出 | §6，exclusions_and_reuse.json |
| Q6 | 小28／中44／大66，完整33个task/config/split条目；新增全是native stress，不新增wholeValid/contextfit | 条件不满足即skip，不替换为盲seed/grid；成本按全流程校准 | §7–8，next_experiments.json，guide |

## 1. 共同上下文：事实、验收与历史分开

### 1.1 计数和时间截面

本轮686个实际梯度头、665逻辑run；588项wholeValid加88项nativeStress为676个单项数值。另有88项fixedcohort数值、8项抑制、95项composite，不能作为新增拟合相加。10项历史未评分仍未知。实际头与逻辑run的21之差沿用多任务逻辑归组的定义，不视为重复训练错误。相对上轮586头增100；native20增68为88，whole556增32为588。这是对登记数字的新算术检查，不是重算676指标。[E-STATUS, E-CONTRACT]

| 截止时状态 | 物理单位 | 本轮如何处理 |
|---|---:|---|
| MoL已完成12 | 12梯度头，Caco/micro/DILI各4 | 已验结果用于拒绝/限定，不重跑 |
| MoL余CYP4 | 4梯度头已派未回 | 等待实际46/47的MLP256/TabMk32四格，不改seed |
| TabICL16 | 16冻结上下文fit，0梯度训练；实际结果0 | 四task×两表示×random_state44/45；准备成功不是疗效 |
| AMESdual4 | 4固定50-epoch轨迹，至多8选择器view | 不计为8 fit；原3280/468/468/468划分保持 |
| window12 | 12固定200-epoch轨迹，至多36因果policy view | 不额外新训50-epoch基准 |
| M5/M6 | 26个seed展开的未来fit定义，仍准备中 | 排除出新增矩阵；不能称已训练 |
| Monroe/UniMol2 | 无真实任务疗效；限定准备正在进行 | 不新增准备probe或冒称full-cache已准备 |
| M2 | 12拟合数学等价而skip | 不补高floor或新seed维持活动 |

本表所有pending以E-STATUS为准。原ledger局部`as_of`早于当前状态，其中“MiniMol setup404”“TabICL尚无权重”“某分支pending”等仅为旧事件，不能当现在障碍。相反，当前状态也不回写旧报告中的真实失败。[E-STATUS, E-ASSETS, E-HISTORY]

### 1.2 研究单元与数据边界

一个可比科学单元包含task、原输入身份、冻结表示与池化、cache版本、fit/stop/stress成员、每个fit的预处理统计、目标、监控、epoch预算、初始化seed、输出尺度和评分定义。只相同任务名、seed和metric不足以成为单因素对照。

本报告的新增矩阵全部仅学习官方train.Y；统计fit、模型选择stop、最后stress严格分开。原行、原标签、官方分区不改。canonical分组是防止同一规范化身份跨内部组，**不是去重删行**；scaffold只改变内部组划分，不重写官方Valid。nativeTrain来自此前已经被使用的官方train，不能事后宣称全新独立holdout。后续任何对已看stress的选择也须登记，不能以新请求清零Valid/stress选择历史。[E-DESIGN, E-SKILL, H-STRESS48PLAN, E-ISSUELOG]

local AP为已登记threshold tied-group average precision；官方AUPRC与总公式尚未闭合。所有MAE以给定numeric Y原尺度报告，未知物理单位不擅自解释。约46等本地推算不是官方隐藏榜分；本轮没有制造新的总榜数。[E-COHORT-REPORT, E-ISSUELOG U01/U04]

### 1.3 哪些验收继承，哪些本轮实际核对

**继承**：现有run的完整学习、冻结encoder参数和buffers、CPU reload、输入/预测task/split/row身份、固定评分器和运输的已验结论。沿原回执注明范围；没有加载模型、读取trace或重扫全库哈希。

**亲读**：当前核心入口/设计/Skill3.4.1、状态/合同、研究相关ledger选段、所有本轮主要新结果、原Pro002的analysis/guide/proposals相关选段、旧分支原更新与失败/反证链、当前资产可行性和官方代码/README/license/paper。`evidence_registry.json`逐对象记录可见工具引用、行数/选段和登记版本，不把远端登记hash冒充独立计算。原Pro002六件本地副本有字节hash核对；其中review/issues/search_space仅核身份并作为导航，未声明全文科学分析。原来源内容和本轮结论仍分开。

**本轮新核对**：四组half-life差值与方向、micro/hep的1/4计数、M2等价的数学后果、MLP参数量、33条矩阵的seed展开/控制共享/排除、固定群共同错误下界公式、分档成本。结果不以程序PASS代替科学成立。

**没有做**：逐行Valid Y/残差访问、已验单项或cohort评分重算、全部历史原件通读、未经授权的子Agent、外部模型执行。受限scope只阻断依赖该材料的结论，不能升级为原评分无效或全研究空等。

### 1.4 历史可枚举性与负结果不消失

原HISTORY_BRANCH_INDEX及当前history-index保留历史完整导航；当前报告按相关分支而非无差别遍历。已消费的主线包括Mini22/旧24/28/confirm86、优化72、head/loss140、confirm54、Morgan、Mini/TabM32、AMES6、MiniSol/PPBR12、confirm14、group20、ranking与新stress；组合分数分支只复用历史汇总，不重读95条全部成员或重新筛ensemble。[H-BRANCH, E-HISTORY, H-FRONTIER, H-OPT72, H-HEAD140, H-CONFIRM54, H-MORGAN, H-TABM32, H-ENSEMBLE59]

必须保留的限制包括：早期pilot和写边界失败；worker与supervisor退出码不一致；GLM的8192行截断与其他执行失败属于不同事件；BBB旧H0-s46缺after冻结快照不能补写；原wrapper总SHA差异已定位到未用于特征的随机predictor，不能再次指控encoder解冻；原009关闭不复活；M2准备超预算与文本行数错误不因后续科学等价而抹去；MoL单UUID拒绝并非当前逐run实际设备违规；LD50取回包装错误的修复不能计为重训；half-life步数348改288是记录修正而非质量值重算。[E-HISTORY, E-CLAIMS, E-ISSUELOG, E-M2, E-MF-CACO, E-MF-DILI, E-LD50, E-HLSTRESS-U]

## 2. Q1：全22任务行动前沿

### 2.1 不同证据强度对应不同采纳范围

“保留”意味着保留当前配方作为后续对照/候选，不是选定唯一模型；“否决”仅否决已测试配方的扩面理由，不是否定整个表示家族；“等待”指具体已经派发或准备的研究单元，而不是以队列空满定义科学完成。每个task下文都有未解问题和收口条件。

| Task | 外部指标 | 当前行动类别 | 下一判别／科学收口 |
|---|---|---|---|
| `ames` | AUROC ↑ | retain_rawValid_candidate_await_existing_selector | 消费已派dual4的同轨迹双selector；本轮0新AMES拟合。 |
| `bbb_martins` | AUROC ↑ | hold_trustworthy_controls_not_new_grid | 先核任何拟采用控制是否有独立准入；待某新表示在前置panel有证据才另定BBB问题，不自动复制seed。 |
| `bioavailability_ma` | AUROC ↑ | reject_tested_Mini_Morgan_MLP_expansion | 仅在TabICL完整预设panel给出方法性支持后考虑该低样本endpoint；目前0新fit。 |
| `caco2_wang` | MAE ↓ | retain_F010_await_window_M5_TabICL | 先收window12中的4轨迹、M5Caco及TabICL既派slots；不再建50对照。 |
| `clearance_hepatocyte_az` | Spearman ↑ | raw_candidate_not_structure_robust_rank_cross | R/X固定结构partition两loss×两representation；N仅需要时固定stop/stress减fit。 |
| `clearance_microsome_az` | Spearman ↑ | raw_candidate_not_structure_robust_rank_cross | R/X；等M6再决定K；N与geometry G为有界储备，不并行盲铺。 |
| `cyp2c9_substrate_carbonmangels` | AUPRC ↑ | keep_H0_and_F010_contextual_not_class_weight_universal | 保留两floor锚；若原ProM7温和权重问题再获登记，权重只fit统计并保持对照，本轮不重复转录未执行M7。 |
| `cyp2c9_veith` | AUPRC ↑ | retain_local_floor_evidence_defer_new_family | 先消费2D6 MoL/TabICL实际完整结果，再在新的任务化假设下选是否迁移，不本轮补seed。 |
| `cyp2d6_substrate_carbonmangels` | AUPRC ↑ | retain_fit_posBCE_task_specific | 保持fit-only权重/未加权控制；优先既有M7温和权重预案而非再次同seed原配方。 |
| `cyp2d6_veith` | AUPRC ↑ | retain_MiniTabM_structure_supported_await_dispatched | 等既派CYP4、TabICL、M5；若成员监督仍关键，T唯一新native scaffold 2fit，不重复M5raw。 |
| `cyp3a4_substrate_carbonmangels` | AUROC ↑ | retain_H0_anchor_reject_uniform_F010 | 暂不新增原floor或seed；只有先验明确新机制支持时另登记。 |
| `cyp3a4_veith` | AUPRC ↑ | retain_lowLR_await_window | 已派8条200epoch与三virtualpolicies；本轮0重复fit。 |
| `dili` | AUROC ↑ | reject_MiniTabM_rollout_keep_F001_F010_scoped | 当前negative-control价值已实现；等已派TabICL，不加新架构凑活跃。 |
| `half_life_obach` | Spearman ↑ | adopt_rank_recipe_locally_transfer_question_only | 不再追加half-life seed/权重或Valid评分；R迁移其他三个Spearmanendpoint。 |
| `herg` | AUROC ↑ | hold_mixed_floor_defer_evidence_led_family | geometry或TabICL前置panel支持且安全门槛通过后，才考虑新endpoint，不跳过其风险与许可。 |
| `hia_hou` | AUROC ↑ | retain_affine_task_specific_no_universal_simplicity | 保留affine现有控制；不统一推线性头，也不对HIA续盲seed。 |
| `ld50_zhu` | MAE ↓ | retain_raw_and_high_group_Huber_not_structure_general | 0追加Huber delta/seed；可在原合格固定群做无新truth的共同误差下界诊断。 |
| `lipophilicity_astrazeneca` | MAE ↓ | retain_F010_stop_Huber_expansion | 停止相同Huber扩面；复用既有群与预测作安全汇总，非再训。 |
| `pgp_broccatelli` | AUROC ↑ | stop_redundant_floor_scan_hold_baseline | 优先有来源差异且先在panel具效用的新表示；不堆同head seeds。 |
| `ppbr_az` | MAE ↓ | retain_Mini_structural_support_with_raw_counterexample | M2H0=F010已数学跳过；不调更高floor救解释；以现有候选进入后续清晰评审。 |
| `solubility_aqsoldb` | MAE ↓ | retain_Mini_recipe_strongest_cross_checks | 既有M6为容量反证；几何G作为阳性参考与micro反例配对，不先推广22。 |
| `vdss_lombardo` | Spearman ↑ | prioritize_bounded_rank_transfer | R建立native FullMSE/HalfMSE/rank三组×2scheme×44/45，共12新fit；lr固定1e-4不再扫描。 |

### 2.2 逐任务事实、反证、未知与停止条件

#### 01. ames

**事实与保留理由。** Morgan2048 identity+MLP sameGPU四seed Valid均优；高/低固定群新44/45均改善。

**反证与否决范围。** stop四seed排序反向；native canonical/scaffold 44/45四配对均负，不能推广Morgan结构稳健性。

**未解。** fit支持/stop选择/分子分布/特征与尺度捆绑；高群仍有低AUROC，不等于修复。

**下一动作与收口。** 消费已派dual4的同轨迹双selector；本轮0新AMES拟合。 若selector变更改变外部次序则限定选择器敏感；若都Morgan负则在该固定fit环境拒绝其结构优势，不再加seed。

来源：[H-AMES, E-STRESS48-U, E-COHORT-SUMMARY, E-STATUS]。

#### 02. bbb_martins

**事实与保留理由。** 已有CheM floor比较及混合方向；全22输入缓存现成。

**反证与否决范围。** 旧H0 seed46缺after冻结证据不可倒推补造；相近分数不免除冻结前提。

**未解。** 未有可信的新架构/结构stress/新表示增益；旧缺证run只可标范围受限。

**下一动作与收口。** 先核任何拟采用控制是否有独立准入；待某新表示在前置panel有证据才另定BBB问题，不自动复制seed。 当前floor密扫收口；新的完整冻结控制是前瞻比较而非修复历史。

来源：[H-FRONTIER, E-ISSUELOG, E-ASSETS]。

#### 03. bioavailability_ma

**事实与保留理由。** CheM旧Mini22/后续头比较仍为基准；小任务效应须按原split。

**反证与否决范围。** Mini与Morgan现有MLP两seed均负，不扩同配方。

**未解。** 旧Mini22优于部分新头的原因；小stop支持、容量与选择波动未分离。

**下一动作与收口。** 仅在TabICL完整预设panel给出方法性支持后考虑该低样本endpoint；目前0新fit。 负结果限定两个完整配方，不宣称全部指纹/小数据方法无效。

来源：[H-FRONTIER, H-MORGAN, H-HEAD140, E-STATUS]。

#### 04. caco2_wang

**事实与保留理由。** F010相对H0有局部支持；Huber/drop0四seed各3/4；CheMTabM现有双seed优于对应MLP。

**反证与否决范围。** MoL固定8主对比全负；Mini/Morgan未稳定替代；TabM未超所有历史Huber且触50上限。

**未解。** 容量/成员/窗口相互作用；高低分歧群各10被排除，误差未知；10历史未评不能当失败。

**下一动作与收口。** 先收window12中的4轨迹、M5Caco及TabICL既派slots；不再建50对照。 负MoL配方收口；窗口/成员问题由既派设计回答后决定是否独立loss×window，不能自加。

来源：[H-CONFIRM54, H-TABM32, E-MF-CACO, E-COHORT-REPORT, E-STATUS]。

#### 05. clearance_hepatocyte_az

**事实与保留理由。** MiniH0 MLP同CPU四seed rawValid正向，增量0.01164–0.11536；F010旧支持不抹去。

**反证与否决范围。** 新canonical1/2正、scaffold0/2；stop差值也非统一方向。

**未解。** train-size、chemistry、selector、loss与representation交互；不是只由GPU切CPU导致。

**下一动作与收口。** R/X固定结构partition两loss×两representation；N仅需要时固定stop/stress减fit。 禁止继续同配方加rawValid seeds；结构普适命题已不支持，保留局部候选。

来源：[E-HEPRAW, E-HEPSTRESS, E-HEPSTRESS-U, E-STATUS]。

#### 06. clearance_microsome_az

**事实与保留理由。** MiniMLP匹配四seed rawValid正向；对CheM约+0.049至+0.127。

**反证与否决范围。** Mini换TabM首轮双负；Mini结构stress仅1/4正；MoL8主比较负。

**未解。** 目标错配/维度容量/训练支持/平台跨数据比较；相同scheme内paired差可解释，跨scheme绝对分数不因果。

**下一动作与收口。** R/X；等M6再决定K；N与geometry G为有界储备，不并行盲铺。 原raw候选保留但结构优越收口为否；配方迁移不按更多seed救火。

来源：[H-CONFIRM14, H-TABM32, E-STRESS48, E-MF-MICRO, E-M2]。

#### 07. cyp2c9_substrate_carbonmangels

**事实与保留理由。** 有原floor与分组同成员对照；F010 canonical AP增而scaffold降。

**反证与否决范围。** fit-posBCE双负、Morgan双负、Mini混合；不能从2D6substrate搬权重结论。

**未解。** 原Valid阳性支持有限；分组阳性结构、AP分母与目标可能混杂。

**下一动作与收口。** 保留两floor锚；若原ProM7温和权重问题再获登记，权重只fit统计并保持对照，本轮不重复转录未执行M7。 当前posBCE/Morgan同配方扩面收口；AP口径仍未官方确认。

来源：[H-FRONTIER, H-HEAD140, H-GROUP20, E-P002-PROPOSALS]。

#### 08. cyp2c9_veith

**事实与保留理由。** F010旧两seed小改善。

**反证与否决范围。** 不足以主张task已最优；其他CYP方向不一。

**未解。** 未真实测试新表示/TabM/结构压力；需避免由2D6生物学名称推断迁移。

**下一动作与收口。** 先消费2D6 MoL/TabICL实际完整结果，再在新的任务化假设下选是否迁移，不本轮补seed。 现有小改善只作基线，停止同因子密扫。

来源：[H-FRONTIER, E-STATUS]。

#### 09. cyp2d6_substrate_carbonmangels

**事实与保留理由。** F010+fit-posBCE相对未加权四seed正向。

**反证与否决范围。** 2C9substrate同法双负，否定普适类别加权；结构泛化尚未证实。

**未解。** AP与损失权重影响、具体阳性盲区；小群不可逆推出个体。

**下一动作与收口。** 保持fit-only权重/未加权控制；优先既有M7温和权重预案而非再次同seed原配方。 四seed局部采用判据收口，不由此宣称所有结构群改善。

来源：[H-CONFIRM54, H-HEAD140, E-P002-PROPOSALS, E-ISSUELOG]。

#### 10. cyp2d6_veith

**事实与保留理由。** MiniTabM对CheMTabM四seedraw、双scheme×两seed stress均正；高分歧群新44/45改善。

**反证与否决范围。** 同Mini换TabM额外raw收益小至0.000693；低分歧132人群8项抑制，不能称无错；未检验独立外部集合。

**未解。** 成员机制vs容量；MoL/TabICL在途；低分歧真实风险未知。

**下一动作与收口。** 等既派CYP4、TabICL、M5；若成员监督仍关键，T唯一新native scaffold 2fit，不重复M5raw。 保留完整recipe，停常规确认seed；成员机制问题以M5/T收口，不把部分primary胜利当全比较胜利。

来源：[H-CONFIRM14, E-STRESS48, E-COHORT-SUMMARY, E-STATUS, X-TABM-README]。

#### 11. cyp3a4_substrate_carbonmangels

**事实与保留理由。** 原H0提供比较锚；已试floor与简单头见ledger。

**反证与否决范围。** 原F010两seed退步；与CYP3A4Veith并非同指标/任务。

**未解。** 新表示与结构stress未验；不可从共享酶名外推。

**下一动作与收口。** 暂不新增原floor或seed；只有先验明确新机制支持时另登记。 已试F010统一替代命题否，任务本身不是研究完成。

来源：[H-FRONTIER, E-RUNS]。

#### 12. cyp3a4_veith

**事实与保留理由。** 在H0/F010内lr1e-4各四seed正向。

**反证与否决范围。** 先前floor次序随LR变；低LR可能只是50epoch路径/停止策略互动。

**未解。** 优化快慢vs正则vs训练窗口；stop与Valid往往反向。

**下一动作与收口。** 已派8条200epoch与三virtualpolicies；本轮0重复fit。 若等窗口仍支持低LR可更窄采用；若被200/8逆转就修订有限窗口命题，不额外扫LR。

来源：[H-OPT72, H-CONFIRM54, E-STATUS, E-MECH]。

#### 13. dili

**事实与保留理由。** F001对H0四seedraw增益；旧canonical/scaffold F010比H0正向，F001只局部；固定等权组合已验。

**反证与否决范围。** 新MiniTabM stress0/4；MoL主对比3胜5负无一致替代，旧Mini/TabM不稳定。

**未解。** 48行rawValid反复选择；两个floor结构排序变化；生物标签/测量异质性未证实为原因。

**下一动作与收口。** 当前negative-control价值已实现；等已派TabICL，不加新架构凑活跃。 停止现有MiniTabM/MoL扩面，不把失败升级为所有深表示无效。

来源：[H-FOURSEED, H-GROUP20, E-STRESS48, E-MF-DILI, H-ENSEMBLE59]。

#### 14. half_life_obach

**事实与保留理由。** rank胜同CPU fullMSE四seed；再胜HalfMSE四seed；canonical/scaffold两seed四格再支持。

**反证与否决范围。** 绝对Spearman仍有限；旧F001seed44低、低LR新种子反转、四seedensemble不一定好；原生train非新外部。

**未解。** pairwise surrogate、梯度正则/target geometry/stop交互未分离；不等于直接优化Spearman。

**下一动作与收口。** 不再追加half-life seed/权重或Valid评分；R迁移其他三个Spearmanendpoint。 本任务rank-vs-coefficient问题达到局部收口，广义机制与任务迁移另题。

来源：[E-RANK8, E-HALFMSE, E-HLSTRESS, H-FOURSEED, H-ENSEMBLE59]。

#### 15. herg

**事实与保留理由。** 已有floor/头基线。

**反证与否决范围。** 小Valid、floor方向混合；没有本轮几何疗效。

**未解。** 表示覆盖/分子群风险未验证。

**下一动作与收口。** geometry或TabICL前置panel支持且安全门槛通过后，才考虑新endpoint，不跳过其风险与许可。 当前配方小幅波动不追seed；不能以未测当否决。

来源：[H-FRONTIER, E-STATUS, E-UNIMOL2]。

#### 16. hia_hou

**事实与保留理由。** affine相对普通MLP两floor各4/4；F010对drop0也4/4。

**反证与否决范围。** H0对drop0有平局；其余任务简单头大多负；小Valid不等于充分化学覆盖。

**未解。** 收益究竟是容量/正则/选择未识别。

**下一动作与收口。** 保留affine现有控制；不统一推线性头，也不对HIA续盲seed。 特定已有比较局部收口；新增仅在明确分布/容量问题时。

来源：[H-CONFIRM54, H-HEAD140]。

#### 17. ld50_zhu

**事实与保留理由。** F010数值极端缓解；Huberraw四seed正，高群四seed改善。

**反证与否决范围。** low群45负；canonical两seed混合(+.0120645,-.0013684)；scaffold4槽预设fit不足跳过不是负。

**未解。** 原Y物理单位、共同盲点、结构支持仍未决；不可为更好分数重抽scaffold。

**下一动作与收口。** 0追加Huber delta/seed；可在原合格固定群做无新truth的共同误差下界诊断。 raw局部候选保留；稳健结构命题未成立；不可把skip补成成功或失败。

来源：[H-CONFIRM54, E-LD50, E-COHORT-SUMMARY, E-ISSUELOG]。

#### 18. lipophilicity_astrazeneca

**事实与保留理由。** F010已有重复局部改善；Huberraw3/4。

**反证与否决范围。** 高固定群45负、低群44/47负；不存在一致切片改善。

**未解。** 误差化学机制与共识区风险仍未验，分歧不等于残差。

**下一动作与收口。** 停止相同Huber扩面；复用既有群与预测作安全汇总，非再训。 Huber普适改进命题在本scope否；F010不自动推出所有群修复。

来源：[H-CONFIRM54, E-COHORT-SUMMARY, E-ISSUELOG]。

#### 19. pgp_broccatelli

**事实与保留理由。** 现有floor/头比较与盲预测相近。

**反证与否决范围。** 混合方向、差异小不能证明等价，更不能证明任务完成。

**未解。** 新的独立信息源能否改变排序未验证。

**下一动作与收口。** 优先有来源差异且先在panel具效用的新表示；不堆同head seeds。 同因子小网格收口，未测方向保持unknown。

来源：[H-FRONTIER, E-RUNS]。

#### 20. ppbr_az

**事实与保留理由。** Miniraw3/4；native双scheme×两seed4/4增益；高分歧群4/4改善。

**反证与否决范围。** raw匹配seed46反例+0.038734 MAE；低群46/47负，不能删除。

**未解。** 高低群差异机制；本地尺度与业务意义未定。

**下一动作与收口。** M2H0=F010已数学跳过；不调更高floor救解释；以现有候选进入后续清晰评审。 结构支持强化而非抹去raw反例；不再为4/4口号补seed。

来源：[H-MINISOL, E-STRESS48, E-COHORT-SUMMARY, E-M2]。

#### 21. solubility_aqsoldb

**事实与保留理由。** Miniraw匹配4/4、native4/4、高/低群新44/45均改善；实际H0=F010。

**反证与否决范围。** 原Morgan负、旧floor跨scheme方向不一；组MAE仍非零；表征/尺度/容量捆绑。

**未解。** 是否因维度/头容量、预训练信息或chemistry未识别。

**下一动作与收口。** 既有M6为容量反证；几何G作为阳性参考与micro反例配对，不先推广22。 现有Mini recipe局部采用收口；整体收益不关闭具体盲区。

来源：[H-MINISOL, E-STRESS48, E-COHORT-SUMMARY, E-M2, E-STATUS]。

#### 22. vdss_lombardo

**事实与保留理由。** H0lowLR四seed3/4；固定平均有过局部收益。

**反证与否决范围。** F010混合、一个低LR新seed负；无native当前目标对照，不从raw复制。

**未解。** MSE/Spearman错配、stop高噪声、新表示未试。

**下一动作与收口。** R建立native FullMSE/HalfMSE/rank三组×2scheme×44/45，共12新fit；lr固定1e-4不再扫描。 schema/分组不可行就跳过；若rank不跨scheme成立，收口为非普适迁移，不再加seed。

来源：[H-FRONTIER, H-CONFIRM54, H-ENSEMBLE59, E-RUNS, E-HLSTRESS]。

### 2.3 当前证据实际推翻了哪些命题

需要推翻的是扩大后的命题，而非删除原来的数字。“MiniMol在micro四个rawValid seed均改善”仍是事实；“因此MiniMol在micro的结构外推更好”被新四配对中的三负收窄。“Morgan是AMES可保留raw候选”仍成立；“其选择器反转不影响稳健性”没有支持。PPBR则相反：raw3/4与低群46/47退化仍在，但native4/4给结构配方新的支持，不能把它永久归类为失败任务。[H-CONFIRM14, H-AMES, H-MINISOL, E-STRESS48, E-COHORT-SUMMARY]

跨表示比较默认是recipe：编码预训练、分子输入变换、池化、输出维度、fit标准化、第一层参数量和优化几何都可不同。即便头名同为MLP256，CheM2048和Mini512并非同参数量。只有在同表示、同partition、同初始张量、同batch序列、同停止规则下替换训练目标，才能把主差异归于目标这一因素；也仍包括该因素经优化轨迹和停止选择产生的总效应，而非直接化学因果。

`claim_events.json`保留原事件ID与旧命题，追加九个范围变化事件，发生时刻未知写null，不拿归档时间充当实验发生时间。旧Pro002建议M2 now skip、ranking4 now complete、stress48 now complete都明确更新；原文不改写。

## 3. Q2：排序项值得迁移，但还不是“Spearman已经被解决”

### 3.1 证据链与新增算术

四个rawValid种子中，排序配方相对同系数HalfMSE的Spearman增量如下。数字来自已验汇总；本轮仅复核算术，未再算Spearman。

| 模型seed | rank − HalfMSE |
|---:|---:|
| 44 | +0.1196004683 |
| 45 | +0.1530678445 |
| 46 | +0.1558817384 |
| 47 | +0.0358821362 |

描述均值+0.1161080468，范围+0.0358821362至+0.1558817384，不是置信区间。HalfMSE与FullMSE在44/45相同，46/47只有约−0.0003193/+0.0008382变化；不能用“乘0.5改善MSE优化”解释rank的全部差额。[E-HALFMSE]

| native分区／seed | HalfMSE控制 | ranking配方 | 增量 |
|---|---:|---:|---:|
| canonical／44 | 0.0452744319 | 0.3106227504 | +0.2653483186 |
| canonical／45 | 0.1911346668 | 0.2241782113 | +0.0330435445 |
| scaffold／44 | 0.1987232865 | 0.2571642891 | +0.0584410025 |
| scaffold／45 | 0.1567505287 | 0.2214669249 | +0.0647163962 |

描述均值+0.1053873155。canonical fit/stop/stress为326/46/93，scaffold为269/103/93；同一方案的训练支持和stop规模并不相同。当前8头的公共轨迹检查与288真实steps由主控验收复用；不重新执行objectives.py或模型。[E-HLSTRESS, E-HLSTRESS-U]

### 3.2 哪些竞争解释还在

设fit-only标准化标签为z，头输出为f。当前已接受的目标语义是：

`L_half = 0.5 mean((f-z)^2)`

`L_rank = L_half + 0.5 mean_{i<j,z_i≠z_j} softplus(-sign(z_i-z_j)(f_i-f_j))`

配对在当前batch内，等标签pair不计；空有效pair的排序项为0。必须复制实际已验目标block和pair reduction，不把旧设计中的名字当生产CLI枚举。全局epoch或batch归一化改动会改变系数含义。[E-HALFMSE, E-HLSTRESS, H-RANKSPEC]

**排序对齐解释得到支持，但不是唯一解释。** Spearman是平均秩的相关；pairwise软排序是次序surrogate，接近减少discordance，但不等同直接最小化Spearman的秩平方误差。有 ties、极端排序错误或不同pair权重时二者可不同。称“目标更贴近外部排序需求”合理，称“已证精确指标优化”不合理。

**梯度与有效正则解释仍在。** rank添加第二个梯度源，改变输出差的尺度和饱和区、优化方向及AdamW相对正则。HalfMSE控制排除了一个简单系数解释，不是梯度范数匹配的控制。改善可能来自优化条件，而非某类化学关系被学会。

**标签幅度和噪声解释仍在。** MSE强调数值距离，pair项只用大小关系，可能减轻幅度极值的支配；也可能放大接近标签间的不可靠次序。未获准的逐行残差不能拿来验证该叙事。可记录fit内label ties、有效pair数量和两项loss/梯度范数的聚合诊断，不改标签、不加伪标签、不用stress选pair阈值。

**早停是中介而非已经控制掉的变量。** 同监控规则下不同目标会改变最佳epoch；当前主对比估计“换目标＋其优化与早停后果”的总作用。只有相同轨迹的预定checkpoint对照才能进一步拆分停止选择，但本轮不另外增加半衰期view/评分，以免把已用Valid扩成自适应诊断库。

**有限任务、固定partition和重复选择仍限制外推。** 四模型seed不是四个独立化学群样本；两分区也不是随机重复抽样的总体估计。没有p值、确定最佳权重或普适增益承诺。下一步必须换endpoint、保留反例，而不是把半衰期再加seed当普适性证明。

### 3.3 具体首批：R28

本轮选择其余全部三个Spearman端点——`clearance_microsome_az`、`clearance_hepatocyte_az`、`vdss_lombardo`。使用现成CheM原2048缓存、当前MLP256、model seeds44/45；splitseed43与modelseed分开。

| Task | 表示／scaler | loss候选 | 分区 | seeds | 新fit |
|---|---|---|---|---|---:|
| microsome | CheM2048 F010 | HalfMSE、0.5MSE+0.5pairwise | canonical、scaffold父分区 | 44,45 | 8 |
| hepatocyte | CheM2048 F010 | 同上 | canonical、scaffold父分区 | 44,45 | 8 |
| VDss | CheM2048 H0 | FullMSE、HalfMSE、0.5MSE+0.5pairwise | 同builder的新canonical、scaffold43 | 44,45 | 12 |
| 合计 | | | | | **28** |

micro/hep已有FullMSE同task/representation/partition/seed父控制复用，不重算；VDss当前raw控制不是新native划分控制，因此确实要4项FullMSE。VDss学习率固定1e-4，其余5e-4，以历史受支持配方为锚；所有loss对照内部同lr，不把task间绝对效应当同一优化条件。[H-OPT72, H-CONFIRM54, E-STRESS48, E-HEPSTRESS]

头固定一层ReLU256/dropout0.1、AdamW weight_decay1e-4、batch128、50epochs、patience8、min_delta1e-7、最早best；不另调lambda、lr、dropout、batch。feature/target统计每个fit重新估计；只在native stop按Spearman↑选checkpoint，stress一次报告；输出反变换回原numeric Y。新增wholeValid评分为0。

VDss的新分区未物化不是空task占位符：方法、seed、原train、组规则和候选都已确定；主控仅需无学习地生成一次成员清单与SHA并检验资格。若大scaffold造成fit不足或指标不定义，则整个对应对照对跳过，不换seed、不拆组、不用随机划分补位。

### 3.4 为什么canonical/scaffold和loss×representation各有独立信息

canonical检验规范化身份聚集下的稳健性，主要避免同一身份跨内部区；scaffold检验更粗的结构核心分组。二者不是“严/松程度”单一标尺：构成、fit数量、stop难度和ties同时变动。应比较**每个分区内**rank−HalfMSE，再观察方向是否跨分区保持，不能用scaffold分数低就宣称泄漏已证明。

X16固定两个clearance端点，加入Mini512 H0的HalfMSE/rank×两分区×两seed。这样同分区/seed上计算：

`interaction = (rank−HalfMSE)_Mini − (rank−HalfMSE)_CheM`。

这是比“Mini排名更高”更具体的loss×recipe交互。即便CheM的R为空效应，X仍可判断排序目标是否只适配Mini；因此不以“R必须先成功”机械阻断X。反过来，X全无支持时应收口本轮固定目标，不加0.1/0.25/1.0系数网格。交互仍包含表示维度/尺度和第一层容量的差别，不能称纯编码器因果。[E-STRESS48, E-HEPSTRESS, E-M2]

**反证预登记**：若仅某seed或仅某分区改善，保留局部线索而不统一采用；若rank与HalfMSE在有效pair/梯度诊断中实际等价，停止该重复单元；若目标作用因native分区而反转，不用rawValid最佳值覆盖。全部预定配对报告，不只报赢家。

## 4. Q3：rawValid不转移，可能是什么，不能先断言是什么

### 4.1 两个clearance的具体反例

| Task／分区 | seed44 Mini−CheM Spearman | seed45 Mini−CheM | 支持数 |
|---|---:|---:|---:|
| micro canonical | −0.0710224456 | −0.0288967030 | 0/2 |
| micro scaffold | −0.0177820989 | +0.0227888343 | 1/2 |
| hep canonical | +0.0750644317 | −0.0068136362 | 1/2 |
| hep scaffold | −0.0467532244 | −0.0437615561 | 0/2 |

micro四项描述均值−0.0237281033；hep为−0.0055659963。这些均值只压缩四个受关联的局部比较，不是总体效应。hep raw四seed均正、平均约+0.0584543，而且raw确认已在同CPU条件下匹配。故“全部只是GPU换CPU”不能解释hep结果；micro有跨平台历史差异，不能顺便当已完全控制。[E-STRESS48, E-HEPRAW, E-HEPSTRESS]

micro raw fit693/stop77、Valid111；canonical539/77/154；scaffold532/79/159。hep官方train848，raw stop86、fit762为减法推得；canonical591/86/171；scaffold593/85/170。raw到native不仅测试分布变，fit支持减少，stop与预处理也可能改变。两个native方案的fit数量接近，但不是同一成员，所以仍不能把所有剩余差异归为scaffold化学。[E-STRESS48, E-HEPSTRESS, E-HEPRAW]

选择器反转并非AMES独有：micro canonical44的Mini内部stop约0.71245高于CheM约0.67917，但外部stress却更低；hep scaffold45也有Mini stop优势而stress负差。它们支持“stop不完全代表目标分布”的可检验假说，不证明早停是唯一原因。[E-STRESS48, E-HEPSTRESS]

### 4.2 竞争解释矩阵

| 假说 | 当前支持 | 当前反证／未控制 | 最小有信息判别 |
|---|---|---|---|
| fit数量或化学覆盖下降，使Mini优势消失 | 两clearance raw→native fit减少；大表示/小头的学习曲线可不同 | Sol/CYP在减少fit后仍支持；hep两native fit量接近但表现不同 | N8固定scaffold stop/stress，按固定组前缀只缩fit；同时比较两表示 |
| stop选择在分布变化下偏好错误epoch | AMES、micro、hep均有stop/外部排序反转 | 不同表示可能本身在所有epoch都弱；当前未看全轨迹反事实 | 先消费AMES已派dual4；clearance不立即复制dual任务，必要时未来专门登记 |
| Mini预训练或2D邻域偏向rawValid化学 | 表示效应明显task/split异质 | 未读逐行结构-误差关联；canonical/scaffold还改支持量；不能指认某官能团 | 固定结构父分区的R/X和现有群/相似性无标签诊断；几何仅经门槛G8 |
| 平台、随机初始化与实现改变造成差异 | 历史部分raw/结构跨主机；不同尺寸seed不产生同张量 | hep raw确认同CPU仍4正，native仍3负；不能归因平台单独 | 新对照同进程/缓存/初始化/数据顺序；继承旧源版本，不重演全库audit |
| label尺度／损失与Spearman不匹配 | half-life rank受控增益；clearance也是Spearman | 当前MSE尚不说明无法学排序；rank也可能失败或只Mini有效 | R28/X16同系数目标对照 |
| Mini512与CheM2048引起头容量/正则差 | 相同MLP256参数量差近四倍 | 不等于参数少必更好；Sol/CYP正、micro负；M6未回 | 先原M6；只有有线索再K4结构迁移 |
| 表现只是重复Valid选择赢家 | 候选确实经过多轮选择；已用Valid不是终评 | native预定配对提供独立于该run stop的证据，不能全部抹去 | 全格报告及固定native压力，保留选择史，不发明p值 |

没有一个假说能单独解释全部任务；不存在“某种划分使MiniMol必败”的证据。Sol MiniMLP与CYP MiniTabM在两分区四配对皆正，PPBR同样结构4/4正。CYP还同时换了表示、缩放和深头配方；它并非单独验证了Mini编码器。Sol正例是后续几何面板的正向配方对照，micro负迁移是压力对照，不扩成全22新family扫表。[E-STRESS48, H-TABM32]

### 4.3 N8如何区分“fit支持”而不重做划分

仅在R/X与已派M6消费后仍有决策价值时，取micro/hep已有scaffold split，在其fit集合中按既有组key的固定哈希顺序选取不超过原fit的75%行的**完整组前缀**。种子固定43，model44/45；stop/stress成员一字不动。两表示用同一子集，分别重拟合scaler/target统计，固定原FullMSE与MLP256。每task×两表示×两seed，共8新fit；fullfit旧控制复用。

这是“样本支持＋必要预处理重估”的policy bundle，不是单纯标签数量或化学机制单因素。完整前缀可能比75%略少，实际N随组大小登记。首组导致无合格子集就skip，不挑另一个前缀/seed。干预只回答同固定stress下局部样本支持敏感性，不是完整学习曲线；没有理由增加25%、50%、90%网格。

### 4.4 固定群88：哪些是真实误差证据，哪些仍未知

96登记单元来自48个既有模型在12个冻结Valid群上的评分；88数值、8抑制；44可评配对、4支持不足配对；0新fit、0wholeValid重算。44/45在组定义后训练，但46/47参与选组；新seed不是新分子测试集。分类的总N≥20、每类≥5是当前发布门槛，不是普适统计可信阈值。[E-COHORT-REPORT]

| Task | 固定群N | high四seed增益方向44/45/46/47 | low四seed方向 | 结论边界 |
|---|---:|---|---|---|
| AMES | 114／114 | + + + + | + + + + | 群内配方收益存在；结构stress仍0/4，不能抵销 |
| PPBR | 28／28 | + + + + | + + − − | 新seed与选组seed不同；低共识群非统一修复 |
| Sol | 294／294 | + + + + | + + + + | 两群改善不等于残余错误清零 |
| CYP2D6 Veith | 132／132 | + + + + | 抑制×4对 | 8个指标单元无数值，不报小类数，不当0 |
| LD50 | 194／194 | + + + + | + − + + | low45反例保留；native canonical也混合 |
| lipophilicity | 42／42 | + − + + | − + + − | 增益不稳定，不能因整体3/4正而说群已修复 |

Caco的高/低群各N10、micro各N12未进入评分；不扩群到“刚好能评分”，不通过总体与小群差分恢复个体。所有完整既有群入口在`cohort_register.json`保留：包括原公开指针、current SOURCE_MAP的cohort-index/bindings身份、12个RS48原成员ref/SHA及新增half/hep/LD50父分区入口。部分成员leaf明确只公开身份，不伪造可下载URL，也不在报告复制行号、SMILES或标签。[E-COHORT-REPORT, E-ISSUELOG, E-SOURCEMAP]

已有低群的真实数值足以否定“共识就没有风险”：PPBR seed44低群两模型MAE约5.697745与5.274544；Sol低群约0.841010与0.677738。AMES high44 AUROC仅约0.572881与0.655470，说明正增量不意味着该群已高质量。跨分类群绝对AUROC/AP还受类别构成和样本分布影响，不能以高低群差值指认某类化学机制。[E-COHORT-COMP]

但“两模型在同群都有非零MAE”**不等价于它们错在同一分子**。这一逻辑差别很重要。只需安全聚合、无需新增真值访问，就有一个可用的新判别：在完全相同的固定群、预测版本和原输出尺度上计算无标签分歧

`D = mean |p_A − p_B|`。

令`a=|y−p_A|, b=|y−p_B|`，由`|a−b|≤|p_A−p_B|`及`min(a,b)=(a+b−|a−b|)/2`，得到

`mean min(|y−p_A|, |y−p_B|) ≥ max(0, (MAE_A + MAE_B − D)/2)`。

若右侧为正，即使每行有“oracle”选择两模型中更准者，群平均仍至少残留该误差，可证明一定程度的共同盲区，而不识别任何个体答案。这是数学推导，不是已算出的实测下界：本轮没有可直接绑定到相同群/同预测的D汇总，所以不填数。若主控已有准入的无真值预测，计算D只用预测；两MAE继续引用既验值，不重评分。此式不能用AUROC/AP替代MAE，不用于N10/12的禁止群，不给极小阈值群或成员错误比例的新查询。[E-COHORT-COMP, E-COHORT-REPORT；本轮推导CHK-COMMON-ERROR-BOUND]

具体官能团、立体异构、元素、环系、大小/电荷或低相似度群的误差目前没有同口径安全证据。可疑结构特征可以从已准入无标签输入描述，但不能写成“某群已被修复”。若需要新的化学slice，应先由主控给固定定义、足够支持与披露授权，再取汇总；本轮不自行扩分组或读取逐行真值。

## 5. Q4：模型家族的下一决策必须受实际结果和资产版本约束

### 5.1 MoLFormer：固定配方负例已足以停止这三任务扩面

已完成12头为Caco、micro、DILI各MLP256/TabMk32×46/47。Caco与micro各8个预登记跨表示主比较全部负；DILI为3胜5负。MoL内部TabM相对MLP在micro两seed改善，在DILI也改善，但这不等于超越CheM或Mini：它只是给定MoL表示下的readout收益。必须同时保留主比较和辅助比较。[E-MF-CACO, E-MF-MICRO, E-MF-DILI]

| Task | MoL MLP46／47 | MoL TabM46／47 | 固定主比较判断 |
|---|---|---|---|
| Caco，MAE↓，Valid91 | 0.4550803332／0.4121863991 | 0.4190882376／0.4197524989 | 8/8负；内部换头一正一负 |
| micro，Spearman↑，Valid111 | 0.3923772173／0.4254760407 | 0.4322754114／0.4561373539 | 8/8负；内部换头两正不改变主结论 |
| DILI，AUROC↑，Valid48 | 0.8241758242／0.8373626374 | 0.8307692308／0.8439560440 | 3/8正，没有一致替换证据 |

结论是**停止这些已测MoL配方的直接扩面**，不是宣告SMILES预训练家族无效。50epoch有限窗口、输入缩放、768维与不同第一层、跨run设备等可能影响结果；但这些限制也不自动赋予“再训200一定能救”的理由。已有window12的科学对象不是MoL，不能把其结果无条件迁移为MoL延长授权。只有窗口结果提出新的明确反证、或CYP余4显示有价值的任务特例，才另行登记新问题。[E-MF-CACO, E-STATUS]

CYP余4只消费既派输出。若两头均无跨表示支持，则这一固定16头面板可按当前目标收口；若仅某头/seed正，保留局部例外，不扩全22。若出现较大预测分歧但质量负，不能据此创建Valid调权ensemble；分歧是潜在互补的必要线索，不是收益证明。组合权重若以后研究，应只由train内部预定方案选择，实际复合分数与物理fits分账。

### 5.2 精确资产与来源绑定：已知什么，尚缺什么

| 科学资产 | 精确候选／本项目标识 | 已有能力 | 尚不能宣称 |
|---|---|---|---|
| CheMeleon | 原2048，权重SHA `c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651` | 全22 raw缓存与现有native切片，真实头结果 | 新池化或新source版本已验；代码commit未在此投影暴露，不凭空补 |
| MiniMol | v1 gnn15 max512；代码`41642328affbb35e4950b7b7a9020aa95919b503`；权重SHA `a3061e1cdbbd5e544168fbf8c1e01836c8c19ac030891d495a2ae9f29cfe97a7` | 已编码/已学习多任务，包含hep；旧404过期 | H0=F010可跨任何新fit继承；新任务任意池化已就绪 |
| MoLFormer | 公开候选 `ibm-research/MoLFormer-XL-both-10pct` rev `361063d0ad524ef77cf39b08469f6be770dc550f`，权重SHA `0795977fe7192c4acdaf052f0e8464af57bc4bb59211271c5e61aaba2637b9c6` | 当前实际ibm MoL768/meanpool已完成12，CYP4待回 | 仅凭同家族名就将旧候选hash绑定为当前mf16实际hash；当前source-adoption leaf未公开 |
| TabICLv2 | 当前代码`d83091b845a8c5f7c087bd54964f755a9e560f45` v2.2.0；jingang公开分类／回归v2-20260212 checkpoints | 96资产ready报告、16contextfit已派，0真结果 | 论文成绩是本项目成绩；准备成功是推理成功；旧候选weight指针无需与实际receipt再绑定 |
| Monroe | 代码`de075eabe98e4adbbedbc86ca9e877f4bfd9b629`；weights.pt SHA `df996e8e98b12a3cda5fe5acbef3e1e9a4ea31946d3736461cd07e53a5bf205a`；720维 | source/配置/风险已读，限定无标签准备中 | 全任务覆盖、几何疗效、TabPFN许可已接受 |
| UniMol2 | 代码`90f52c41299a1a582da0f9765e9f87aa21faa16a`，tools0.1.3.post1；HF `dptech/Uni-Mol2` rev `bf37d253c0f5ac61f468137eb00059978a104ff0`；84M checkpoint SHA `5b9241630f1cf0b173fb06d1e76096e5daf5f91c3e51b066ba69524dafe60e35` | CLS768固定候选，限定准备中 | 1.1B模型结果等同84M；默认API无裁剪；32probe证明完整输入覆盖 |

精确文件大小、版本、风险、原URL在`scientific_assets.json`和证据登记中。MoL公开模型卡标Apache-2.0且明确10pct；不能写full-XL训练数据规模。TabICL代码BSD-3-Clause已读，具体权重/可选组件通知与当前准备receipt分别登记。新分子读出器不得自动引入TabPFN gated terms、账号token或商业许可接受。上述public code licence核对不是法律许可意见，也不等于所有checkpoint/用途已由用户准入。[X-MF-CARD, X-TABICL-LICENSE, E-STATUS, E-ASSETS, E-MONROE, E-MONROE-ADD, E-UNIMOL2]

**真实缺口而非假404**：当前mf16来源`ref-323e465705337344`经SOURCE_MAP定位为`source-adoption.json`的reference-only；TabICL当前准备receipt也未在本轮核心状态中逐个暴露96资产哈希绑定。此前公开候选有明确版本，可以列出，但不能把“候选版本”冒充“本次执行恰用版本”。最小补件是原已验receipt的安全版本/权重hash/接口配置摘录，不是重做冻结/运输审计，更不要求模型文件或私有路径。它影响新复制/版本因果解释，不取消已验12项质量数值的条件性比较。[E-SOURCEMAP, E-MF-CACO, E-STATUS]

### 5.3 TabICL待结果时可以判定什么

TabICL是冻结的表格in-context预测器，不是分子编码器。`.fit`构建训练上下文及预处理；random_state影响上下文/特征变换/集成顺序，不是随机初始化预训练权重。即便0梯度，也有监督学习过程与统计拟合边界：上下文Y只来自train-fit，stop/Valid/test不可作为context答案；预处理也不能把query集合当额外训练数据拟合。[X-TABICL-REGRESSOR, X-TABICL-CLASSIFIER, X-TABICL-PAPER]

16项面板有两种表示与四个任务，足以判断该固定上下文方案在这些任务是否优于登记头；不是一次科学筛选后无限尝试context顺序。当前官方代码默认参数不能代替准备方实际配置；是否`n_estimators=8`、分类温度/average_logits、回归逆变换、长表内存策略，都应读实际准备receipt。若回归库本身已返回原Y尺度，不能再按头部管线反变换一次；分类须输出连续正类分数，不可硬阈值代替AUROC/AP。

若16项无支持，停止该版本/配置的扩面，不当作许可问题或重开探针；若只有小样本或某表示获益，保留限定recipe，与现有native结构问题的下一步另行登记；若context污染、buffer更新或输出尺度错误，则是实现/准入故障，不能作为方法负效应。此时先修正受影响分支的科学身份，不把失败打包成全通过。

### 5.4 Monroe与UniMol2为何可能互补，也为何难以做“几何因果”结论

两者是一手论文、官方代码和本项目固定checkpoint风险调查支撑的候选，不是随意列家族名。它们与现有2D图、Morgan和SMILES表示确有输入几何信息、预训练目标与架构差异，可能补充构象相关信号；但“3D更物理”本身不证明ADMET优势，单构象可能不代表溶液/蛋白结合态，构象生成/质子化/立体化学/失败回退都可能主导结果。[X-MONROE-PAPER, X-MONROE-README, X-UNIMOL-PAPER, X-UNIMOL-README]

**Monroe尤其不能称纯几何实验。** 官方README显示PM6量化性质大规模数据之外还使用PCBA生物测定多任务预训练。这个来源差异可能提高相关生物信息，也使以后收益不能单独归于几何。没有重叠审计证据时，不能声称泄漏，也不能保证无重叠；若目标用途对预训练来源有更强限制，由主控按原规则审查，而非本轮擅自删数据或改checkpoint。[X-MONROE-README]

Monroe的720维encoder可接新MLP，无需采用其附带TabPFN路径。但实际风险包括SMILES字典键合并重复行、`strict=False`掩盖encoder漏键、BatchNorm buffers在train模式变化、图对象forward后被原位修改、RRWP/dense pair计算的N²成本，以及虚节点放在原点而`zero_vn_edge_rbf=false`时的坐标参考框架依赖。不能悄悄居中/旋转/关虚节点距离来“修复”同一资产：那是新预处理/版本。允许在既有准备预算内做不学习的可复现性/坐标fixture，发现问题先记录，不将fixture输出当任务疗效。[E-MONROE-ADD, X-MONROE-GRIT]

**UniMol2采用84M CLS768，而非最大模型。** `return_repr=True`应绕过任务分类头。现有API存在外层kwargs未真正传递seed/max_atoms/multiprocess的风险；默认随机截128个heavy atoms与当前原行全覆盖要求冲突；直接传atoms+coords可能丢bond信息；invalid SMILES在`is_train=False`可能抛错；隐藏HF_ENDPOINT/网络下载、默认8workers、pair512的N²内存与私有环境依赖都需明确。不能因“API参数写了max_atoms”就验收，也不能默默删失败分子或只评成功子集。[E-UNIMOL2, X-UNIMOL-API]

两个几何checkpoint当前都只有准备方案，未有真实全任务编码或质量结果。既派32个无标签train panel、每encoder≤12forward尝试、合计24synthetic head checks、seed42、所有几何分支合计20秒超时等预算沿用，不新加一套probe。没有完整task row cache时，G8保持blocked_assets。

**G8具体面板**：Sol（已支持Mini配方的正对照）与micro（结构转移失败压力），各Monroe720、UniMol2 CLS768×44/45，使用已验scaffold43父分区、H0 fit-only标准化、MLP256/50/8/MSE，外部分别MAE↓与Spearman↑，控制为旧CheM/Mini同分区same-seed。四个task×encoder原train编码cache各共享两头；不编码Valid/test。不同dim第一层参数量仍不同，所以只估计完整recipe。只有出现受支持互补后，才值得另研究dim/capacity匹配或融合；本轮不额外添加几何＋TabM＋集成的笛卡尔积。

### 5.5 其他已调研家族的处理

KPGT、Uni-Mol一代、SMI-TED、MolE保留历史source/资产与适用性问题，不用UniMol2的准备进展替代一代checkpoint验收。TabPFN2.6作为独立预测器保留许可/版本/赛制边界，Monroe源代码引用它不授权本项目使用。其他经典描述符与从零小D-MPNN没有本轮新一手证据或准备优势足以优先于R/X；Morgan和简单affine头则早已真实做过，不再列成“尚未尝试的新方法”。GLM、DeepSeek、Qwen、Astra和Pro是执行/研究角色，不是科学底座。[E-ASSETS, H-HEAD140, H-MORGAN, H-NEWMETHODS]

因此本轮新增family面板只有已有明确checkpoint的一对几何候选，而且有条件阻断；没有凭借负MoL结果随意补十个模型名维持广度。

## 6. Q5：已派设计的可识别性审查

### 6.1 AMES dual-selector4：能回答选择器敏感性，不能完全回答化学机制

四条轨迹固定fit3280；stopA、stopB、stress各468，CheM2048 H0／Morgan2048 identity×44/45。每条50epoch不因某selector停止，A/B分别选checkpoint，先锁定两选择器，再对同一个stress分别评价。这样可以问“同一梯度轨迹只改选择集合，模型排序是否改变”，并计算每个表示的selector效应及其差异；不是8个新训练。[E-STATUS, E-MECH]

必须保持fit预处理只用3280行，不能两selector分别把stop并入fit；不允许先看stress再决定A或B。两view同checkpoint或同预测SHA时去重。若两选择器都Morgan负，能排除“这个固定fit轨迹仅换选择器即可恢复”这一解释，不证明所有训练支持/化学划分都无效；若排序反转，则证明选择器敏感而不是自动挑stress更好的selector部署。A/B本身若不具独立结构性质，也不能冒称一次重复实验。

### 6.2 window12：50epoch与patience是不同问题

Caco CheMF010的MLP/TabM×46/47为4条；CYP3A4Veith的H0/F010×lr5e-4/1e-4×44/45为8条。每条保存完整200epoch实际trajectory，离线因果重放50/8、200/8、200/full三种策略。三种策略不产生36个梯度fit。[E-STATUS]

50/8与200/8只在50之后可能不同；若patience8在50前已触发，两者应同checkpoint，不可硬称延长收益。200/full忽略patience但仍只在已出现stop记录中选择；它考察继续优化机会与更长选择窗口的整体效应，而非纯额外梯度步。长时间查看同一stop也能增加选模偏差。若长窗口改善必须同时报告早期/晚期选点和实际steps，不因单一最高Valid值宣布收敛已解决。

关键实现风险是“从best而非last继续”：完整轨迹的epoch51须接epoch50真实末态、optimizer/RNG，不能先reload最优再延伸。只有初始张量、batch顺序、库与优化器状态相同时，前50轨迹才可称旧50运行的因果prefix；不满足时当前12轨迹内部策略比较仍成立，但不能把旧run差归于epochs一因素。现有12已承载控制，不能另添50-epoch重复fit。

### 6.3 M5：k、共享、参数量与监督方式仍有多个因素

M5三task：CacoCheMF010、microMiniH0、CYPMiniH0，各plain3×512／TabMk1／TabMk8×46/47，共18未来fit，旧k32六fit共享。它能描述固定特征下宽深MLP、单/少/多成员的质量与成本；不能把plain与k1当完全同构单因素，因为TabM还有成员尺度、共享参数化与初始化结构。[E-STATUS, X-TABM-README, X-TABM-CODE]

官方TabM建议对每个成员分别计算训练loss再平均，推理分类平均概率。不能把`loss(mean prediction)`当成“修复实现”；那是另一个科学目标。对于回归，

`mean_k (f_k-y)^2 = (mean_k f_k-y)^2 + mean_k(f_k-mean_k f_k)^2`。

所以成员MSE比均值MSE多一个预测离散惩罚；它不是简单“鼓励成员输出多样性”。分类由于log-loss凸性也有Jensen gap，但输出/梯度/参数共享共同作用，不能从该代数式独断质量方向。[X-TABM-README；本轮代数检查]

**真正缺失的条件对照T2**：仅当M5后成员监督问题仍影响CYP决策，固定已有native scaffold MiniH0 k32结构、初始化、输出mean-prob、batch与stop/AP，只把训练从`mean_k BCEWithLogits(z_k,y)`换为`−log(mean_k p_k)`相应二元概率混合NLL。44/45共2fit，旧同split k32两个控制共享。稳定实现用logsumexp(logsigmoid(±z))−log(k)，不是先平均logit。它需要new_code。若M5已足以拒绝/采纳当前k32，或该问题无决策价值，就不跑T2。

### 6.4 M6：近参数匹配是有效判别，但不是表示因果的终点

M6在Sol/micro raw上做CheMF010 MLP128与MiniF010 MLP512×46/47，共8，原MLP256控制共享。单隐层标量MLP参数量为`D*h+2h+1`：CheM2048×256=524801，Mini512×256=131585；CheM×128=262401，Mini×512=263169，两新配置相差768参数（约0.293%），称近参数匹配，不能称完全匹配。宽度、函数空间、优化路径仍不同。[E-STATUS, E-P002-GUIDE；CHK-CAPACITY]

当前Mini三个raw-fit中H0/F010分母完全相同，等价仅对这些fit成员成立；其`fit_std`下限分别为PPBR0.2198244、Sol0.0672848、micro0.1076810，均高于0.01，改动维数为0。原M2数学skip不代表MiniF010 reader任意路径已正确：准备方正在补cache/scaler身份透传，synthetic检查不等于真实cache通过。新split须独立fit统计，不继承等价。[E-M2]

**条件K4**只在M6出现一致、可解释的容量线索且仍影响micro结构结论时使用：micro已验scaffold43上CheMF010 MLP128、MiniH0 MLP512×44/45，与旧native256控制比较。它不是M6 raw46/47重复。固定MiniH0避免在新split无证据地把F010等价假设带入。M6无一致线索或问题已经收口，就跳过K4，而不是把宽度再扫到1024/2048。

### 6.5 既派工作的有效等待条件

等待的是特定识别问题，不是等待所有队列清空。R/X不依赖MoL或TabICL返回，可以先登记；K依赖M6科学结果和接口，T依赖M5；G依赖已派几何准备完成和完整task cache准入。AMES不新增fit，window不新增view任务，TabICL不加准备probe，M2不补无效slot。若已派出现冻结/数据/标签故障，暂停受影响比较，不要求其他独立问题总停。

## 7. Q6：足够支持多批、但有明确边界的实验路线

### 7.1 三档预算不是三张重复表

`next_experiments.json`根为33个具体proposal的数组，每条恰好一个task、一个完整配置、一个split、model seeds44/45。小档是R子集，中档是R∪X，大档是所有条件集合的上限；不把三档相加，不把direction cap相加。已有控制、已派physical fit、context fit、预测view分账。[E-STATUS；本轮矩阵展开]

| Stage | 所解决问题 | 新条目 | 新梯度fit | 准备类别 | 进入条件 |
|---|---|---:|---:|---|---|
| R | 三Spearman task迁移及VDss缺失FullMSE锚 | 14 | 28 | config_only，源绑定后 | 主控注册；不依赖其他在途结果 |
| X | 两clearance loss×representation交叉 | 8 | 16 | config_only，源绑定后 | 与R一并预定或完整R后分批；不只挑R赢家 |
| N | 固定scaffold内fit支持量效应 | 4 | 8 | new_code | R/X和已有M6后仍有判别价值 |
| G | 已具体化两几何checkpoint的互补性 | 4 | 8 | blocked_assets | 既派准备与全task缓存、许可/冻结/覆盖均就绪 |
| K | M6容量线索向结构micro迁移 | 2 | 4 | config_only，依M6 | 原M6提供一致且决策相关线索 |
| T | 固定CYP k32的成员监督聚合 | 1 | 2 | new_code | 原M5后该机制仍需判别 |
| 上限 | | **33** | **66** | 48配置型＋10新代码＋8资产阻断 | 任何无信息分支可skip |

小档R28覆盖所有三个其他Spearman任务，而不是只做清除率。推荐中档44，使两clearance的loss×表示问题可在同一个研究计划中完成。大档66不优先全部启动：N/K/T是反事实分支，G等待新资产，满足条件才由主控登记。各分支都可以关闭而不补齐总数。

整个最大矩阵最多新增66个nativeStress指标、0wholeValid、0contextfit。8个G头只共享4个新原train编码cache（两任务×两encoder）；R/X/N/K/T复用旧raw cache无需编码。所用旧控制共11组两seed=22个唯一既有physical fit，任何方向引用都只计一次；小档和中档的具体reuse集合见budget文件。当前已经派发的20梯度轨迹、16contextfits及26准备fit都不计入本新增预算。

### 7.2 一次只改变什么

R/X内部以HalfMSE对ranking是目标单因素；FullMSE是系数控制，原control可复用但跨环境标为次级锚。K是固定表示下hidden_dim单因素。T是固定架构下成员损失聚合单因素。N同时缩fit并重估依赖fit的统计，明列为policy bundle；G换表示/几何/维度/首层，明列recipe bundle。跨表示same数值seed不等于同初始化张量；同维度目标pair须共享初始张量与dataloader前缀。

**全部候选共有的数值定义**：回归fit-only float64 mean/std对给定Y标准化，训练目标表中明确MSE/系数/pairwise；早停分别Spearman↑或MAE↓；外部在nativeStress同定义比较；输出只做一次inverse回给定原Y尺度。T是原0/1标签概率混合NLL，stop与外部均local AP↑，输出mean(sigmoid(member_logits))。不得用`task-native metric`模糊替代。

**源版本不是“latest”**：具体权重SHA/代码版本在每条asset_version展开；cache必须指向accepted父run相同源与ordered row identity。对未公开的父cache/partition hash，本报告写明确的原run/原receipt定位和待绑定条件，不虚构hash；主控可从已有验收原件复制最小字段，不重做全库验收。VDss新manifest和G全task cache未生成，登记为未来准备输出。

### 7.3 继续、停止、跳过与回研究条件

1. **R正且稳定**：保留task局部目标，继续预定X识别交互；不自动打wholeValid、不调lambda。R全无改善也不是立即扩大网格：X仍有预定的“表示特异性”价值，可按中档继续；预算只小档时科学结论停在CheM迁移受限。
2. **跨seed或分区相反**：保留四格，不以平均投票淘汰反例。不追加模型seed去凑稳定；先看预定fit统计、pair计数、stopepoch是否可解释，决定N/K是否仍能区分竞争解释。
3. **X无支持**：收口固定0.5/0.5目标在这两个表示/两个native分区的迁移，不否定未来全部排序学习；本方案没有系数网格fallback。
4. **N无fit支持依赖**：在该一档干预与固定stress范围内削弱“数量单独解释”，不是证明无数据量效应；停止学习曲线扩张。
5. **M5/M6没有一致线索**：T/K不运行，不换一个任务补位。若结果与本前提矛盾，带具体run、源版本、对照和差值回研究，而非让执行方自行扩展。
6. **G某资产不满足完整覆盖或冻结**：阻断该task/encoder单元，不删失败行、不把失败分子填零输出、不改变两task面板；另一个独立资产可继续其已获准部分。
7. **源、标签、参数/buffer或行身份失败**：科学比较暂停，失败单独登记；不以更好分数豁免，也不把基础设施失败当方法负结果。
8. **何时需要下一次Pro**：预定信息问题已回答、出现重要反证、新family/目标超出此矩阵、或现有有信息分支耗尽。不是每个头、固定分钟或空队列触发。

数值方向只作为描述与分支分类，不伪造统计阈值。当前没有统一业务最小有意义差；主控若需部署门槛，应先登记任务语义或已有稳定性基准，而不是事后选择让赢家通过的Δ。两seed只允许有限一致性判断，不把4/4当95%置信度。

## 8. 完整周转成本、准备与取回不能省略

### 8.1 已测成本与不可相加的口径

当前stress48记录CPU job1843.198455秒、17823steps；hep8约34.018494秒（某更完整检查/包装口径35.517231秒）；LD50实际4头约50.02869527秒、1628steps。它们不是相同task/头/数据量，更不是纯GPU kernel。不能把每个角色活跃时间、job寿命和包含包装的总时长相加。现有控制直接复用省的是重新训练及整份取回验收，不意味着其历史成本本轮又发生一次。[E-STRESS48-U, E-HEPSTRESS-U, E-LD50]

用两个异质已测anchor作粗量级敏感性：hep8的4.2523秒/fit，stress48的38.4000秒/fit，分别乘28得到约119/1075秒；乘44约187/1690秒。它们**不是预测区间、置信区间或成本上限**：pairwise B²成本、平台、实际epoch和VDss分组均可使新任务超出。大档非几何58fit同理约247/2227秒，另8几何头和四cache编码/构象成本未知。不能因此报“只需若干GPU分钟”的全流程预算。

### 8.2 可判断的预算函数

完整墙钟应按依赖图关键路径计：

`T = critical_path(P准备/源绑定, E共享编码, H实际头训练, R取回, S固定评分, J交接/队列, Q必要研究)`。

保守串行预算可写`P+E+H+R+S+J+Q`，但实测复盘对重叠区间取union；训练角色、CPU/GPU占用和人工活跃另列。Q只在科学节点发生，本轮不能承诺未来异步交付。

缓存路线可用**明确假设**做主控预算情景：P暂按0.5–2小时，R+S+J暂按0.5–1.5小时，得到1–3.5小时非学习开销再加实测校准H；这些数值不是包内实测、不是时间承诺，也不用于证明哪种模型便宜。new_code N/T需要额外准备未知项；几何E尚无全task测量，G不得硬填GPU小时。下一获准真实fit自然记录首批成本即可，不新增“专门试跑头”。[budget_scenarios.json]

中档推荐的理由是：R和X可共享源绑定、两个clearance既有cache与split、成批取回/评分；增加16个小头能回答不同科学问题，通常比另开一轮研究再补交叉更有价值。但如果准备源绑定、队列或审查成本显著上升，主控可只批R28并保留X明确矩阵，不由执行方自行追加。

几何完整原train缓存按task/encoder各一次，复用44/45；不同几何生成/输入键/原子氢/虚节点规则未经证明相同，不能假设Monroe与UniMol2共用同一个构象cache。以20秒timeout乘分子数可给最坏几何路由上界的组成项，但加上重试、图内存、encoder forward仍未知；本报告不以32probe外推精确全任务时间。

## 9. 补证据的分类、影响和最小闭环

完整分类见`evidence_gaps.json`，这里列影响实际决定的事项。

- **已发布但未逐原件读取**：一些与已读报告重复的MoL分数/对比/更新文件、大ensemble全表、SOURCE文档的未读部分；本报告不假称亲读，不因此否定已验相同汇总。若后续复用精确ensemble identity，再定向读相应成员，而非补一次全库审计。
- **公开投影只给reference身份**：当前mf16 source-adoption、TabICL当前全部资产绑定、部分cohort-member leaf、hep父partition/cache exact hash。SOURCE_MAP明确packet_path和inherited URL为null，不是“下载404”或原件不存在。最小补件是原主控已有验收的安全配置/版本摘要；不索要逐行Y/残差、模型载荷或机器路径。
- **实际工具失败**：container对raw.githubusercontent.com发生DNS解析失败，web对同URI成功，因此不是仓库不可达。部分HF模型metadata/文件指针经web实际返回InternalError；只影响本轮新独立确认那一路元信息，不覆盖包中固定许可/版本记录。失败URL与尝试结果保留在registry。
- **从未完整记录**：生命周期所有探索/Valid访问次数和当前各角色端到端活跃/队列成本没有完整记录。不能从已验正式score总数反推全部访问，不用新会话重置历史。
- **现有准入材料可计算但本轮未算**：匹配固定群的无标签D、fit维度scaler变化量、有效pair数量/梯度汇总。可由原主控在准入范围内零训练或随真实fit自然记录；未算不能说已通过或已证明机制。
- **必须未来实验**：排序对其余三任务的迁移、固定fit支持因果、M5/M6结果、TabICL真实query性能、几何完整任务收益、共识的个体错误定位。前几项有确定矩阵或既派身份；最后个体定位超出当前权限，不列入执行任务。

局部缺口只阻断依赖结论。例如MoL source-binding缺口限制“精确checkpoint复制/来源因果”，不使当前已验score消失；geometry未就绪只阻断G，不阻断R/X；CYP低群抑制只保留该群未知，不使其whole/native高群证据失效。`needs_evidence`不是降标准凑通过，而是准确表达边界。

## 10. 封口前的定向交叉核验结论

关键新主张逐一检查支持与反例：

| 主张 | 支持来源 | 定向交叉核验 | 反例／余留不确定 |
|---|---|---|---|
| half-life不仅是MSE减半效应 | HalfMSE4与native8结果 | 从已验两个标量独立减法；四种子与四native方向；确认288steps修订 | pairwise不是Spearman精确目标；梯度/stop机制仍在 |
| Mini clearance的raw优势不稳健迁移 | raw4seed、stress48、hep8 | 同seed/task/split符号；hep同CPU排除平台单独充分解释 | 样本支持/化学/selection仍混杂，不指认单因 |
| M2等价应skip | 三任务真实fit std统计 | d0最小值全部>.01→max(d0,.01)=d0 | 仅这些fit统计；readeridentity仍需独立正确 |
| 低共识非无风险 | fixed88实际低群MAE | 不把非零群MAE推出同一行错；给纯数学保守下界 | D尚无同源汇总；分类不可套MAE式 |
| 中档44/最大66无重复 | 完整33proposal与当前exclusions | 两种独立展开法：按seed完整identity与按stage闭式求和；控制集合唯一 | 不是全库hash扫；派发前主控仍以最新实际identity查一次增量 |
| M6近容量匹配不等价模型 | 2048/512×宽度及状态 | 参数量公式独立复算 | 宽度和优化仍不同，不能称纯backbone因果 |
| 几何准备不等疗效 | 两feasibility、官方源码/论文 | 版本/role/许可风险与本地ready状态分开 | PCBA来源、虚节点、裁剪、全行覆盖、私有依赖未闭环 |

没有因多个模型口头赞同而增加证据等级；本轮按用户边界没有派Agent。验证器只操作本交付JSON与汇总算术，不能训练或计算任何质量指标。研究收口以每个问题已有可采取/可否决/明确依赖的下一决策为准，不以报告长度、工具次数或队列状态为准。
