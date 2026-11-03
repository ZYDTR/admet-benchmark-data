# Pro005 独立科学评审：端点收益、排序失败与真正有判别力的下一步

**请求**：`admet-pro-next-research-20261103-005`  
**固定输入**：commit `c3859f400e81ddb3ef18681d3329094287c8d0d0`；manifest `457fd2f1109482fdb600b708f9d29cad52ac5f5f7f81518637ca80ba28c39b8d`。  
**科学截止**：2026-11-03T12:25:18.713994+00:00。  
**科学状态**：`needs_evidence`；这不影响明确提出有界设计，也不表示既有分数不可信。全部新方案仅建议；没有训练、推理、标签获取、评分、派发、安装或赛事操作。

引用格式为 `[E-…:定位]` 或 `[X-…:定位]`，完整固定URI、登记版本、实读范围和失败尝试在 `source_registry.json`、`review.json`。数值转录与新增聚合算术分别在 `evidence_tables.json`、`quantitative_checks.json`。文中的“保留/关闭”均限定任务、表示、读出、划分及历史选择范围，不宣称全局最优。

## 0. 决策摘要与问题导航

| 问题 | 直接结论 | 答案位置 | 剩余边界 |
|---|---|---|---|
| Q1 | local的端点/平均绝对误差收益是真实的条件内结果，扩展到旧未覆盖542行；它没有建立排序替换或共同错误修复。集中、目标错配、局部支持和测定条件均仍是竞争解释。 | §§2–4 | scaffold未完成；集中诊断不是完整848同状态因果试验；逐行测定映射未闭合 |
| Q2 | 先做一个固定状态T=2干预，另预先锁定局部读出的HalfMSE/加全配对排序对照；有足够信息价值时采用同一预登记2×2目标×全局距离尺度设计。不要扫T、q或种子。 | §§5–6 | 新接口需实现/fixture；所有新outer回验仍是历史适配后的研究数据，禁止用它调参或按折挑模型 |
| Q3 | 保留22任务各自正负边界；独立的新信息方向优先考察冻结SMI-TED具体瓶颈表示在AMES/PPBR的8头面板，而不是在Hep上继续同信息调头。KPGT有机制依据，但权重绑定不足；GEO002继承而不重派。 | §§7–8 | SMI固定源文件/全行producer准入未完成；KPGT checkpoint访问403；没有任何新底座疗效证据 |
| Q4 | 上轮8条H提案对应16个已完成头，固定gap路线关闭；2条SOLCTX和4条G保留原ID，不重复计数。新确定矩阵24条，20/40/48个新梯度fit三档，0个新contextfit。 | §§9–11 | 预算不是授权；既有状态/缓存的安全身份绑定与新代码准入仍是局部门槛 |

本轮最重要的判断不是“local有效/无效”二选一，而是把四个问题分开：**某段Y的数值误差是否下降；端点总体排序是否改善；已经锁定的共同错误群是否修复；出现这些变化的原因是否被隔离。** 前者得到支持，不自动推出后三者。[E-HOOF-AGG; E-HOOF-LEGACY; E-CONCENTRATION]

## 1. 当前事实、继承验收与阅读边界

### 1.1 状态不可从旧报告回填

当前为864个实际梯度头、843个逻辑run、52个冻结context；656个wholeValid、230个native stress、30个train OOF fold分数，共916个单项数值。88个固定Valid cohort和105个composite另列。头、逻辑run、context、视图、单项分数不能互相代换；这些计数也不证明历史未评分项获得了结果。`task22-frontier`尾部仍保留804/783等旧时点数值，须由CURRENT覆盖，而非改写旧事件。[E-CURRENT; E-TASK22:current_global_counts; E-START]

锁定full22组合的本地推断口径为46.366840429270006→47.49160908243727，11个替换任务改善，11个保留参考任务相同。这是实际锁定组合的重复Valid比较，不是新隐藏榜分、独立泛化证据或22个纯表示因果实验；本轮不重排候选、不新增Valid消费。[E-FULL22; E-EVENTS:E-FULL22-EXISTING-GAINS-20261103]

canonical HOOF的30项已完成；相同预冻结设计的scaffold30尚未得到稳定结果。GEO002是已派的可信fresh producer准备范围，不是准备通过即模型有效。旧geometry缓存缺少原producer冻结证明仍不准入，不能用后来哈希补出过去的冻结事实。[E-HOOF-CONSUME; E-GEO-DESIGN; E-GEO-PRIOR]

### 1.2 实际读取和没有做的事情

本会话实际读取了当前入口、状态、问题合同、完整共同实验纲领、阅读合同、当前历史导航；下钻了HOOF设计、静态统计源码、canonical全部关键指标/完整群及补集统计、旧群回验、集中与测定发现、ME40最终消费、Pair16四个核心单元及其正反分组结果、B24全部已登记数值、22任务条目、GEO002及原Pro004六文件。对成员大数组保留完整原入口和selector，没有声称逐个成员手工重验。对大ledger/SOURCE_MAP采用相关条目定向读取，不把索引打开称为读完每个历史原件。

Pro004六文件使用本对话中真实存在的原件逐字节哈希，均与本轮公开manifest条目一致，再解析相关JSON、完整方案和长文段落。旧Pro003 split/asset/cohort研究登记仅作为已有验收元数据继承。没有执行这些研究原件里的脚本。

评分、冻结、原行身份、生产/取回成功等已有验收只引用原回执；本轮没有重新计算任何行级质量指标。唯一新数值工作是既有汇总数的加权恒等式、差值/分区计数及新矩阵去重。当前包不含原始Y、逐行预测/残差或权重数组；没有补取。没有真实subagent调用，也没有把角色扮演当独立核验。

公开源能被Web读取，不等于容器网络可直接下载。容器请求曾发生DNS解析失败，下载工具亦报错；Web原文可达，因此未将其写成“源材料不存在”。KPGT官方权重链接实际403，以及SMI固定revision源文件的读取失败，单独记录，不外推到整个仓库不可用。[source_registry.json; review.json:read_checks/network_attempts]

## 2. Q1：canonical完整结果支持什么，否定什么

### 2.1 三方法比较必须按原统计定义

所有方法只使用同一fold的inner-fit；MLP/local用inner-stop选epoch，TabICL不使用该stop扩充上下文；不做outer-train refit。MiniMol原512维缓存不变，每fold重拟合H0与目标尺度。外层5折按固定canonical身份分组，保留全部原行；分组不等于去重。原方案先锁定每方案20个梯度状态及10个上下文状态，再看outer指标。[E-HOOF-DESIGN:fixed_group_keys,outer_partition,inner_partition,locking]

| 已验指标 | MLP | local | TabICL |
|---|---:|---:|---:|
| 五折、各折先平均44/45预测后的Spearman均值（主比较） | 0.516919773 | 0.523078040 | 0.540058315 |
| pooled848 Spearman（仅描述） | 0.525086191 | 0.524848552 | 0.543522595 |
| pooled848原Y尺度MAE | 32.161292954 | 29.520818379 | 33.299290995 |

local−TabICL的五个主排序差依次为 **+0.062677、+0.004792、−0.030681、−0.077029、−0.044660**，均值−0.016980275；原条件95%区间为[−0.052831384, +0.018885585]。这既不支持排序优越，也不能当作等效、不劣或“只是噪声”。两个模型seed的结果不是两套独立数据，5折有大量训练重叠；条件bootstrap只反映固定预测、固定分组和当前数据的重采样，不覆盖选择史与重训不确定性。pooled848排序还混合不同fold模型的输出标尺，不能替代逐fold主比较。[E-HOOF-AGG:metrics/comparisons; E-HOOF-STATS]

### 2.2 改善不只是旧stress挑出的覆盖假象，但不是独立新样本验证

旧两套stress的并集306行中，local/TabICL MAE为26.784102/30.839128。旧未覆盖542行中为31.065902/34.688239，差−3.622338，条件区间[−5.455499,−1.647343]。因此“收益只在旧已观察306行存在”的解释被缩小；但这542行来自同一官方train，可能参加过旧fit/stop，新五折也在长期研究之后设计，不能称新独立数据集。[E-HOOF-AGG:comparisons; E-HOOF-DESIGN:why_now]

| 固定Y段 | n | local MAE | TabICL MAE | local−TabICL |
|---|---:|---:|---:|---:|
| Y≤3 | 130 | 15.766716 | 25.897188 | −10.130472 |
| Y≥150 | 97 | 66.826915 | 81.139203 | −14.312289 |
| 3<Y<150 | 621 | 26.572899 | 27.376267 | −0.803368 |

中段差的条件区间[−2.554566,+0.894897]跨零。将上表既有MAE乘各段n后相加，端点227行（全体26.7689%）贡献了总MAE净收益的 **84.4298%**。这是新做的聚合代数分解，不是新的行评分、机制贡献率或“端点解释了84%的因果效应”。Decimal和独立float路径一致，三段及所有错误群/补集加权回到原全体MAE。[E-HOOF-AGG; quantitative_checks.json]

### 2.3 完整改进、伤害及共同错误群：不只展示成功切片

下表均是当前equal-seed local与TabICL的完整群；它们由已看结果定义，不构成预先可用的路由规则。

| 当前群 | n | local MAE | TabICL MAE | 补集n | 补集local / TabICL MAE |
|---|---:|---:|---:|---:|---:|
| local误差较小 | 534 | 15.032932 | 31.722682 | 314 | 54.159454 / 35.980531 |
| local误差较大 | 314 | 54.159454 | 35.980531 | 534 | 15.032932 / 31.722682 |
| 相等 | 0 | 不定义 | 不定义 | 848 | 29.520818 / 33.299291 |
| 改善至少5 | 434 | 14.648928 | 34.564878 | 414 | 45.111157 / 31.972565 |
| 伤害至少5 | 250 | 61.633188 | 39.464215 | 598 | 16.095915 / 30.721981 |
| 两者误差均大于50 | 123 | 92.879453 | 79.228744 | 725 | 18.771698 / 25.507122 |
| 两者误差>50且预测差≤10 | 39 | 79.925835 | 79.149439 | 809 | 27.090910 / 31.088962 |
| Tab-only误差>50 | 75 | 23.303119 | 62.471846 | 773 | 30.124088 / 30.468836 |
| local-only误差>50 | 52 | 69.014041 | 33.515538 | 796 | 26.940859 / 33.285164 |
| 两者均不超过50 | 598 | 13.834477 | 20.174694 | 250 | 67.042547 / 64.693328 |

123+75+52+598=848是互斥分区；39是123的子集，不能重复加。其它改善/伤害群与这套分区相交，不能叠加成“总病例数”。75个Tab-only是当前横截面中的差异群，不能自动叙述为“75个旧病例经同一干预治愈”；52个local-only是当前新增风险相对于Tab的定义，也不是独立的未来失败率。阈值5/50/10继承原描述，不是业务容忍界或置信门。[E-HOOF-AGG:complete_error_cohorts; cohort_register.json]

旧canonical共识大误差31行在新canonical OOF上的local−Tab MAE为 **+5.284823**，条件区间[−3.667575,+14.259854]；旧scaffold定义的32行用同一新canonical OOF回验为 **+9.470508**，[−0.621427,+20.694981]。它们没有稳定修复证据。后者不是尚未完成的scaffold OOF结果。旧canonical改善98行中仍有69改善、13转为伤害；旧伤害47中34仍伤害。历史旧群保持完整入口，不能因一次新全体均值下降而消失。[E-HOOF-LEGACY:fixed_CB_results,legacy_local_transitions]

### 2.4 竞争解释证据表

| 解释 | 直接支持 | 反证/替代解释 | 现在能说什么 | 下一判别 |
|---|---|---|---|---|
| 点值目标/输出标尺有利端点MAE，但未优化排序 | 端点贡献大；中段弱；local主rho低于Tab；point-MSE与Spearman不是同一目标 | local并非直接优化MAE；Tab和MLP目标/选择体系不同；仅称“校准改善”缺少独立校准诊断 | 存在指标/估计目标张力，尚非唯一原因 | O：同局部读出HalfMSE vs HalfMSE+全batch排序，其他相同 |
| 学到的几何过于集中，复制少量近邻标签 | 旧stress初始化→选中状态有效bank数大幅下降；部分查询>99%权重落于很少候选 | 集中同时见于改善和伤害；某seed有效bank明显更大；不同状态/查询位置有数值影响 | 集中是可干预现象，不是已验证坏样本门 | Z：锁定状态T2；S：目标×全局距离尺度完整对照 |
| fit-bank局部标签支持不足/不合适 | 旧化学邻居标签分散；PPBR低尾fit邻居标签中心较高；AMES高相似反标签邻居存在 | 并非所有错误缺近邻或重复输入；更换读出也可能放大而非解决支持问题 | 支持与几何联合限制合理，但不能诊断个体错误原因 | 不额外采样；先检验读出，再按旧群测试独立表示 |
| 隐藏测定条件或相同输入多标签 | Hep重复输入冲突、端点测定范围与截断语义有出处 | 逐行人/鼠/qualifier映射未确认；唯一身份576行仍有164个material harm和30个local-only大误差 | 不能用测定噪声包办全部失败，也不能清洗标签 | 仅安全来源映射；没有已批准条件字段则不训练条件模型 |
| 只在历史观察覆盖中收益 | 旧306是研究触发源，选择史真实存在 | 新542也有MAE收益 | “纯旧切片假象”被反证；独立泛化仍未建立 | 等待原预冻结scaffold结果；新干预不以canonical为调参集 |

## 3. 集中、测定语义与信息边界的进一步解释

### 3.1 集中不能直接变成拒绝门或混合权重

旧8个初始化/选中状态视图共1364个查询状态中，canonical44有效bank中位数177.66→2.13，canonical45为180.03→2.00，scaffold44为211.61→1.78，scaffold45为187.66→10.12；>99%权重相关计数分别15/171、30/171、22/170、0/170。收益和伤害都出现这种集中。原输入相同slot回验与父预测差为0；压缩查询batch是另一个数值诊断，不能用其结果直接替换原同位置比较。[E-CONCENTRATION]

这些数字是旧native stress状态，不是完整canonical848每个新fold模型的集中分布。完整848的状态条件诊断尚未记录在当前公开聚合。后续可由获准宿主在固定状态上报告无标签的熵/有效bank分布，再按现有完整群发布安全聚合，但研究端不得索取逐行邻居标签、残差或用于还原个体的窄交叉群。

对本项目线性局部头，

\[
w_j(x;W,T)=\operatorname{softmax}_j\{-\|W(x-x_j)\|_2/T\},\qquad \hat y=\sum_jw_jy_j.
\]

固定候选bank与状态时，T=2严格等价于把W乘0.5后T=1（偏置在差中抵消；浮点实现另验）。它不改变邻居距离排序，但改变标签加权；所以是一个固定的有效带宽干预，不是“独立温度机制”与“独立W尺度机制”两个实验。逐查询单位范数归一化会同时改变方向几何、点范数信息和有效带宽，不能当作只删除一个尺度因素。已准入的范围裁剪旧MLP对照在ME001中已做，不再冒充新实验。[E-HOOF-DESIGN:recipes.local; E-EVENTS:ME001-E-RANGE-CONTROL-01; mathematical reasoning]

### 3.2 端点单侧损失很可能是数学空操作

公开测定线索支持人肝细胞clearance的单位和<3/>150端点语义，但它没有确认本地848每行的原assay、物种和qualifier。TDC总量1020不能替代本地848或native stress行数。若仍保留提供的3/150数值，而local凸组合输出已在[3,150]内，那么低端一侧误差`max(pred-3,0)`与普通绝对误差相同，高端`max(150-pred,0)`也相同；对应平方形式在域内同样无变化。该同义替换不增加信息，不应占新fit。旧观测中local与Tab都在界内；MLP少量越界单独保留，不外推到所有未来模型。[E-ASSAY]

相同规范输入对应不同给定Y的136个情形及条件MAE下界6.431474只约束特定“相同输入必须同输出”的函数类和当前观测标签。它不等于普适Bayes噪声下界，不证明错标，更不授权去重或均值化标签。唯一身份群仍有明显新伤害，直接反对“全部失败都由重复身份或删失解释”。只有已有允许输入中的可靠条件字段，才可能为相同结构提供真正不同的观测信息；目前只能提出来源核对，不借此获取新训练标签。[E-ASSAY; E-HOOF-AGG:additional_descriptive_identity_cohorts]

### 3.3 凸组合共错下界的适用范围保持不变

旧D/L证据对同一对标量预测满足
`(|y-a|+|y-b|-|a-b|)/2 = dist(y,[min(a,b),max(a,b)])`。
其均值L约束同一对、同一行集合内的任意逐行凸混合；不约束第三模型、非线性校准、外推或不同模型对。它不定位错误行，也不提供无上界条件下的错误比例下界。当前39个低分歧且双大误差是新的明确聚合共同错误证据，但由当前结果定义，不能反过来当无标签可信区域。[E-EVENTS:E-COMMON-INTERVAL-BOUND-20261103; E-HOOF-AGG]

## 4. mechanism40：负结果不被canonical正结果覆盖

ME40完成40头（Pair16+local24），41次梯度尝试，其中1次未完成，26个未完成步骤为记录推断而非当时精确计数。新增40native分数、24初始化诊断视图、0Valid、0编码、0GPU使用；H3关闭。失败不改成通过，初始化视图也不增加fit数。[E-ME40]

### 4.1 大间隔配对不是当前可推荐的默认

| 表示/划分 | gap−uniform主Spearman | 44 / 45方向值 | 条件95%区间 | 原尺度MAE差 |
|---|---:|---:|---:|---:|
| CheM/scaffold | −0.048960 | −0.038867 / −0.037245 | [−0.093253,−0.011805] | +1.690137 |
| Mini/canonical | +0.001690 | −0.013706 / +0.029929 | [−0.035601,+0.041133] | −0.319144 |
| CheM/canonical | −0.023318 | −0.011865 / −0.016433 | [−0.048099,−0.003234] | +0.158217 |
| Mini/scaffold | −0.023975 | +0.011409 / −0.078355 | [−0.061641,+0.016609] | +0.913839 |

四格一近零、三负；主指标用等seed预测计算，不能偷换成两seed分数差的均值。Mini/canonical高尾有改善，但不等于整体排序获益；CheM/scaffold的均匀匹配稀疏臂相对旧全配对rank也有正向结果，所以“只有挑大间隔才能改善高尾”被反证。相同batch匹配的是配对数，不是各行暴露、总梯度范数或端点比重；固定median-gap在fit上把高端暴露提高约1.92–1.94倍、低端约0.82–0.83倍。不得将q50解释为测定噪声估计或继续扫q找正值。[E-PAIR16:cells; E-EVENTS:ME001-E-PAIR-EXPOSURE-01]

### 4.2 local24的实际完整数值不等于24次“一概失败”

`evidence_tables.json.local_readout_B24`逐项保存全部24个task/rep/scheme/seed已登记原分数。AMES的local CheM约0.813–0.846、Morgan约0.811–0.860；Hep Mini约0.505–0.560优于同local读出的CheM约0.388–0.468；micro Mini约0.381–0.550，而CheM约0.161–0.508。由此既不能宣称所有表示都一样，也不能只从表示内比较宣布local打败既有最佳MLP/TabICL。

主控原消费是固定linear128 local recipe未支持生产替换，保留范围内高尾结果，不是否定ModernNCA全部结构、PLR或所有局部方法。官方源码还包含不同特征映射/块/采样实现，本项目实际配方只覆盖其中一小部分。canonical随后说明在匹配覆盖上local仍有端点MAE价值，但主排序/旧共错问题未消失；两批证据应该并存。[E-EXPERIMENTS:mn24 records; E-ME40:not_claimed; X-MODERN]

B24完整原逐run生产配置和部分全群决策仅以`ref-55bbbb2118b7d029`等reference-only身份公开，SOURCE_MAP未给物理payload。已读24分数与最终消费足以保留有限结论；它们不足以宣称已经独立比较每个B24群对所有历史控制。这个局部缺口不阻断HOOF内新的明确定义对照。[E-SOURCE-MAP; E-ME40:decisions]

## 5. Q2：有判别力的下一步不是再挑一个最优参数

### 5.1 优先顺序与不适配OOF的边界

建议先准备**Z固定状态带宽干预**，同时锁定**O目标对照**；对“训练时全局尺度”也要回答时，在查看任何新Z/O外层结果前选定完整**O+S四格**。执行上可先返回无标签/inner诊断，但新outer聚合统一消费，不根据已看过的新外层成绩决定补哪一格、改温度或换监控。

这是把既有矛盾变为受控研究，**不是把同一批已适配OOF恢复成盲测试集**。原canonical848被用来提出假说，新的对比仍属回顾性、条件内研究；若需要新的独立泛化主张，现有数据和本轮权限本来不能提供它。尚未完成的原scaffold30只评价原预冻结三方法，不将新O/S插入它的运行任务，也不事后以scaffold最佳值选择新配置。[E-HOOF-DESIGN; E-CURRENT; E-METHOD]

### 5.2 Z：仅改变固定已学状态的有效带宽，零新fit

对象是10个既有`hoof60-hep-minimol-local-canonical-f{0..4}-s{44,45}`选中状态。T从1改为2；W、bias、fit-only H0、目标变换、完整fit标签bank、查询原槽位、顺序、dtype、距离实现和软件版本全部保持原样。不能拿last/init替代selected checkpoint，不能为“方便批量”压缩查询而改变数值路径；此前已观察原槽位可精确复现、compact查询可能出现数值差异。[E-HOOF-DESIGN; E-CONCENTRATION]

该工作产生**10个新预测视图、0梯度fit、0contextfit、0新编码**。原T1视图直接复用。另一个`W×0.5,T1`只是数学等价fixture，不作为第二个候选重复评分。T2是预先固定的单次扰动，不是经验最优值，也不据其结果扫{1.5,2,4,…}。

必须同时观察有效bank/权重熵等无标签摘要和原完整群的质量投影。可能结果及其意义：

- 集中下降且旧共错与主排序改善：支持**这个状态下带宽改变有实用作用**；不证明所有集中均有害、也不允许学习拒绝门。
- 集中下降、端点MAE优势减弱、排序/共错仍不改善：反对“只需平滑即可修复”，说明端点收益可能依赖标签局部复制；保留目标/支持解释。
- 集中显著变化但错误不变：缩小全局带宽的解释力；不因为CI跨零宣布严格等效。
- T2与T1在准入输入上函数等价或原状态缺失：前者零信息skip，后者记录局部阻断，不用替代状态伪造对比。

### 5.3 O：局部读出自己的HalfMSE控制，而不是借旧MLP控制

每fold/seeds44、45创建两个同期头，除loss外相同：

\[
L_H=\tfrac12\operatorname{mean}_i(p_i-z_i)^2,\qquad
L_R=L_H+\tfrac12\frac1{|\mathcal P|}\sum_{(i,j)\in\mathcal P}\operatorname{softplus}[-\operatorname{sign}(z_i-z_j)(p_i-p_j)],
\]

其中\(\mathcal P=\{i<j:z_i\ne z_j\}\)是当前query batch的**全部不等标签对**；tau=1固定；空集合时排序项恰为0。label差只取符号，不以间隔、尾部或可见外层误差加权。系数来自既有HalfMSE/rank的受控比较思路，但它在这个local读出上尚未验证，不能继承旧MLP疗效。[E-TASK22; E-PAIR16]

| 因子 | 两臂共同固定值 |
|---|---|
| 输入/表示 | 原848行官方train；冻结MiniMol512原cache，权重SHA `a3061e1c…fe97a7`，完整值见scientific_assets |
| split | HOOF原canonical5fold及各自inner-fit/stop；split seed20261103；外层各170/170/170/169/169，不重抽 |
| 头 | Linear512→128，bias=True；无PLR、blocks、dropout、top-k；无query单位范数化 |
| 读出 | 无平方L2距离，softmax(-d/T)，T=1；回归为fit bank标签凸组合 |
| 训练候选 | 从fit-minus-batch无放回抽floor(0.5×剩余数)，batch追加一次；只屏蔽原行自身；共享每batch候选抽样索引 |
| 预测bank | 该fold全部且仅inner-fit；不加入stop/outer |
| 统计 | X的H0 float32/ddof0、std<1e-8置1；Y float64 fit-only均值/标准差；每fold重拟合 |
| 优化 | AdamW lr0.01、weight_decay0.0002、betas(0.9,0.999)、eps1e-8；batch128；max50；无scheduler或梯度裁剪 |
| 选模 | **inner-stop Spearman最大化**，patience8、min_delta1e-7、earliest best；新两臂同规则 |
| seed | 44/45仅模型/批序/候选抽样seed；各fold共享initial W和独立RNG流，不改变split |
| 原输出 | zY凸组合后逆变换一次，原Y单位；不裁剪、不另校准 |
| 外比较 | 主：每fold先平均两seed预测后Spearman、再等fold平均；次：原Y MAE及完整固定群/补群 |

**20个新梯度fit**（5fold×2目标×2seed）。此处使用新同期Half控制，因为原HOOF DESIGN没有明确暴露历史选epoch的monitor字段；新明确的Spearman不能冒称历史同构。原10local FullMSE、10MLP及10TabICL仍为有用的次级参照，但不是每项新因素的完美因果控制。[E-HOOF-DESIGN:recipes; split_register.json; control_register.json]

选择Spearman而不是MAE，是为了对齐本任务已登记主指标；这并不要求端点MAE无条件牺牲。新rank若提升rho却加重共同大误差，结论是**目标权衡**，不是已修复任务。若新Half优于旧Full但Rank不优于新Half，不能归功于排序项，更不能从旧新实现差异中推断监控是唯一原因。

### 5.4 S：移除全局距离尺度自由度，保留方向几何

对每个inner-fit H0特征求固定总体协方差\(\Sigma_f\)，定义

\[
S(W)^2=2\operatorname{tr}(W\Sigma_fW^\top),\qquad
 d_{S}(x,x_j)=\frac{S(W_0)}{S(W)}\|W(x-x_j)\|_2.
\]

\(\Sigma_f\)用分母n，故\(S^2\)等于包括自身零项在内的全部n²有序fit-pair平方距离均值；实际不用枚举n²。S0在公共初始化W0下固定。bias抵消。S在float64精确统计路径计算并**保留对W的梯度**；没有stop/outer标签/特征参与统计。S或S0非有限/非正必须记数值失败，不能偷偷夹到调出来的epsilon。新读出仍为T1。[proposed mathematical interface]

固定W时正比例缩放W不会改变这个有效读出；初始化时free和S距离完全相同。这比逐点L2单位范数化更接近只去除全局尺度，因为它没有把每个分子的向量范数分别抹掉。但它仍然会改变优化参数化及weight decay的功能效果；方向/各向异性可以继续产生集中，因此不能将S的效果等同于“排除了全部集中”。

四格一次性设计是：

|  | HalfMSE | HalfMSE+HalfPair |
|---|---|---|
| free全局尺度 | O-H（10fit） | O-R（10fit） |
| 固定fit距离RMS | S-H（10fit） | S-R（10fit） |

S仅新增20fit，O控制复用一次，总40。O-R−O-H和S-R−S-H比较目标在两种尺度约束下的作用；S-H−O-H和S-R−O-R比较尺度作用；差中差用于描述交互，不当作多独立数据集检验。`contrast_register.json`已按fold展开20个比较视图，视图不增加fit。

解释预先锁定：若rank在两种尺度下都改善，单纯全局距离膨胀不足以解释全部收益；若只在free下改善，则全局尺度与优化路径是竞争解释，但不能断言仅一个原因；若尺度约束修复端点/共错却损害主排序，报告权衡，不择优报单指标；若四格均无修复，当前两个机制不足，停止该四格，不通过调lambda、维度或epoch继续同一问题。

### 5.5 “真正不同的信息”要分三种

第一种是**同一向量上的新读出**（O/S）：它改变可利用关系，不增加冻结输入信息。第二种是**相同SMILES由不同外部预训练先验编码**（SMI、KPGT、几何）：它可能保留不同可学习结构，但仍非新增测定条件。第三种是**样本原本存在而当前模型未见的可靠条件变量**（物种、实验体系、qualifier等）：它可能改变同结构多标签的可辨识性，然而本包没有逐行可用映射；不能为凑新方向补取答案、查标签或改训练样本。

本轮确定的新信息面板属于第二种，不夸称能解决未观察的第三种。其选择AMES/PPBR，而不是继续把所有探索压在Hep，依据是两任务已有具体共同盲区、表示/目标的多次反证，且原生结构划分和对照齐全。SMI源码/全行覆盖未准入会阻断其8头，但不阻断Z/O/S。[E-TASK22; E-ASSAY; X-SMI-CARD; X-SMI-CODE]

## 6. 有界矩阵、预算和可接续分支

### 6.1 三档不是授权，也不是为凑数的预算配额

| 档位 | 包含 | 新梯度fit | 新context | 新预测视图 | 共享新编码 | 已有控制唯一复用 |
|---|---|---:|---:|---:|---|---:|
| 小档，建议首个学习批次 | O目标对照；另Z固定视图 | 20 | 0 | 10 | 0 | 30：20梯度+10context |
| 中档，预登记机制判别上限 | O+S四格；另Z | 40 | 0 | 10 | 0 | 同30，不重复 |
| 大档，独立新资产准入后 | O+S+N8；另Z | 48 | 0 | 10 | SMI两任务各一次，6636原train行 | 46：36梯度+10context |

24个proposal逐条对应一个task、一个配置、一个split，均明确44/45；其中20条O/S为`new_code`，4条N为`blocked_assets`。已有原代码可复用不等于新目标已生产支持，故没有把拟议field冒充当前CLI。小档20并非数字偏好：需要两目标×完整五折覆盖×两个现存配对seed。N8来自两任务×两既有结构划分×两seed，不是补满48的余额。[next_experiments.json; budget_scenarios.json]

该表**不再计入**待回原HOOF scaffold30、机制40、已经派发GEO002准备、旧G8、旧SOLCTX4。原G8中Uni4是用户合同所说的G4，另Monroe4也保留原ID但未准入；两者都不是本轮新增学习。新T2的10视图也不重算成10上下文fit。

### 6.2 实际成本的正确口径

ME40记录CPUworker575.703875秒、40成功头、0GPU；还有不同保守完成界和41attempt，不能将这些重叠时长求和，也不能把混合任务均值当新HOOF局部头的精确速度。20/40local头的朴素角色时间参照约288/576秒，仅作为算式展示；SMI两次全原train编码和8头均未实测，不套同一均值。准备代码、fixture、取回、固定聚合、解释和主控交接可能远大于训练时间。[E-ME40]

完整周转估计应采用
`准备与身份绑定 + 实际调度关键路径(共享编码、训练、视图) + 取回 + 授权汇总消费 + 主控交接/研究判读`，仅在实际并行成立时取max而非相加。优先取已经完成HOOF和ME40的阶段时间，不对每个熟悉的小头新增试跑；新资产正常producer首次获准执行时记录覆盖、峰值和耗时。未有数据的GPU小时、准备人时、网络等待均留null，不作保证。预算的科学选择依据是不同假说可被区分，而不是只节省算力。[budget_scenarios.json]

### 6.3 下一批之后，不需要每训一个头再问一次研究

- **原scaffold同样端点MAE正、排序不正**：原局部配方的失配跨两种结构压力重复，支持继续按已预注册目标/尺度问题解释；两方案仍非独立数据集。不要给原scaffold插入新头。
- **原scaffold端点优势消失或伤害**：缩小local适用范围；完整旧群/补群消费优先。canonical机制仍可作限定研究，但不得宣称跨结构稳健。不自动扩大S或新seed。
- **Z平滑修复而O/S无修复**：支持固定推理带宽方向的限定效用，不证明目标结构无关；不从已看外层选择一个最佳T部署。
- **O两目标都有改善但Rank没有额外收益**：目标添加不被支持；旧新monitor/实现变化保留，不能把Half改善叫排名学习成功。
- **O/S rank收益且旧共错仍在**：主排序与问题修复分别记账；可保留局部质量候选，不关闭共错issue。后续若要外推，须新的主控科学登记，不自动在其余Spearman任务加同样头。
- **O/S均无效或新大误差群扩大**：关闭这些固定配方，转向已准备的独立表示/来源条件问题；不能靠盲seed或微调温度维持分支活跃。
- **N在一任务/一方案有效，另一不成立**：只采纳范围内bundle证据，保留全部8结果；不宣布SMI优于所有图表示、不在22任务全铺。若收益能改变任务决定且有新表示/头交互问题，下一研究再登记匹配容量/不同读出，不先做无限交叉。
- **新资产不准入**：停止该producer，保留失败原因；不会把接口失败当疗效负，也不要求Hep所有分析等待它。

正常深评审在约定完整对照收齐后进行；冻结、标签/输入身份、原状态不可复现等实质故障立即交主控。研究收口指某个有限问题已获支持、反对、无法区分或暂缓及重开条件；不是队列空或研究方向总数达标。

## 7. Q3：完整22任务行动边界

以下每行同时保留当前任务事实、反例与下一动作；详细未决和独立收口条件在`task22_actions.json`。它覆盖所有22个task而不意味着每任务应新增训练。方向未列新proposal表示其现有信息不足以正当化重复学习，不是丢失任务。[E-TASK22; E-FRONTIER; E-EXPERIMENTS; E-EVENTS]

| task / 已登记指标 | 当前可保留事实 | 反证与未知 | 下一动作 / 收口 |
|---|---|---|---|
| ames / AUROC↑ | Morgan旧rawValid四seed支持未稳定转移至native结构压力；dual-selector同轨迹视图已完成；mechanism40的local读出未支持生产替换。 | 旧共享高置信错误群canonical38/scaffold19仍重要，低分歧不是可靠性证据；不同表示在固定local下仍有差别，不能宣称所有表示等效。 选择器、读出、表征支持与分子条件仍可混杂；没有证据给每个错误指定化学原因。 | SMI固定轻量checkpoint面板，canonical/scaffold各2seed；复用同任务同split CheM/Morgan控制。资产不齐先准备，不重复dual4/local24。 固定面板若既未改善主AUROC也未修复旧群且无互补信息，关闭这一checkpoint/输入wrapper配方，不靠加seed挽救。 |
| bbb_martins / AUROC↑ | floor收益与seed稳定性混合；历史H0 seed46的after冻结证据缺口只影响该run。 | 两seed/重复Valid不证明统一F010；不能把一个缺after问题嫁接到其余已验产物。 没有新的BBB特定机制证据；当前资料不支持再开容量或floor网格。 | 维持当前登记候选；仅在新的任务级反证或已批准独立表示显出相关机制时重开。 有限既有对比保留局部结论；不宣称全球最优、也不为填队列重复。 |
| bioavailability_ma / AUROC↑ | 既有Mini/Morgan MLP各两seed未支持替换，简单读出家族已有真实比较。 | 负结果是具体表示/头/划分配方，不是否定所有冻表示；小任务的选择误差仍大。 正式标签来源异质性与新表示增益未知；没有值得再扩seed的明确差异假设。 | 保留候选和完整负表；对新家族先在有明确盲区的AMES/PPBR面板辨别，不统一扩全22。 只有出现输入/机制相符且独立于既有Valid最佳值的新证据，才登记任务级新配置。 |
| caco2_wang / MAE↓ | 既有floor/TabM/目标配方有局部支持；MoL固定对比负，TabICL不优于当前TabM；M5和window已完成。 | k成员数不等于独立网络数，改变k的效果非单调；不能以有限50epoch为所有负结果开脱。 容量、成员共享、不同预训练/输入接口仍影响配方，但当前没有新Caco特定判别。 | 不重跑M5/window/MoL；等待有相关结构假设的独立新证据，不借Hep结果改本任务。 关闭已测容量/窗口配方，保留问题而不是继续固定网格。 |
| clearance_hepatocyte_az / Spearman↑ | canonical848 local MAE29.520818 vs Tab33.299291，旧未覆盖542也改善；主五折rho .523078 vs .540058，差区间跨零；旧共享大误差群未稳定修复。 | Rank转移6/8有正但2负；Pair16一近零三负；75个Tab-only大误差与52个local-only共存。 loss/监控、全局尺度、各向异性、标签条件和支持覆盖仍竞争；scaffold OOF尚未知。 | Z固定T2视图10；O完整五折HalfMSE/rank20；预先锁定的S尺度约束20作为独立因子；不以新outer分数自适应选择S。 按同一完整群、补群、primary rho、secondary MAE分别收口；无改善关闭对应固定干预，不调T/q/lambda/seed。 |
| clearance_microsome_az / Spearman↑ | 受控rank迁移8/8支持；MiniTabICL在两native方案相对MiniMLP有支持；MiniMLP原raw优势未稳定转移结构压力。 | MoL固定配方未支持替换；local24的Mini vs CheM差异不等于超过当前最佳；8配对不是独立数据集。 表示×读出×split交互与条件支持未完全分离，不能拿微粒体替代Hep原因。 | 保留当前配方；GEO002 fresh producer后只继承既有micro几何头，不重记G4；新Hep机制如成功，另行注册迁移而不是自动推广。 不重跑rank44/TabICL32/local24；几何若不准入只记接口/来源失败，不记科学负。 |
| cyp2c9_substrate_carbonmangels / AUPRC↑ | 已有weighted BCE与Morgan固定小矩阵不支持替换；Mini表现混合。 | 不能把CYP2D6成功传播成同一家族所有CYP成功；AP与类别结构不同。 官方AP/AUPRC等价仍需既有来源闭环；无本轮新任务级解释。 | 保留当前登记配置，关闭已测loss/表示配方；新的联合家族实验须有task特定对照。 不新增统一CYP网格；反例保持可枚举。 |
| cyp2c9_veith / AUPRC↑ | 已有F010两个seed的小幅支持，没有新native确认。 | 小幅两seed改善不证明新表示/损失一定可迁移。 重复Valid选择史与AP定义未解决。 | 不新增种子；只在明确readout/representation机制由相邻任务产生且有匹配证据时重开。 保持有限适用范围，不称本任务已科学最优。 |
| cyp2d6_substrate_carbonmangels / AUPRC↑ | 已有weighted BCE与F010组合的四seed rawValid支持。 | native结构外推未被本轮结果确认；加权与floor是组合效应。 是否为类权重、尺度还是选择效应仍未知。 | 不因2D6 Veith的T2结果加新成员或loss网格；未来只做任务特定固定内部压力对照。 将native未知保留，不能以raw正例抹平；无新决定价值时暂停。 |
| cyp2d6_veith / AUPRC↑ | MiniTabM在raw/native有支持，T2真实完成；mean-probability监督比较的AP改善约.006338/.001247。 | Jensen只约束损失数值、不推出AP提升；MiniTabICL弱于旧MiniMLP/TabM；固定MoL补项没有替换依据。 成员误差相关性和概率排序如何作用仍未因果分离，但现有T2不再pending。 | 沿用实际T2局部结论；不加T2 seeds/k/lossweights，不把新请求重新登记旧fit。 关闭已测T2提案为已回答的有限对比；保留未做因果解释而不空转。 |
| cyp3a4_substrate_carbonmangels / AUROC↑ | F010两个seed相对H0退化。 | 不能用五个MAE任务或2C9Veith的floor收益推翻本任务负例。 尚无新的任务特定判别机制。 | 保持H0登记候选，不继续floor剂量扫参。 只有独立新机制证据才重新打开，负记录不删。 |
| cyp3a4_veith / AUPRC↑ | H0低学习率1e-4的native配对有支持；CYP3A4lr8和window真实完成。 | 更长窗口不是一致修复；不能把早停窗口当所有负例理由。 概率校准与AP关系仍不能由loss数值判断。 | 复用已验低lr配方；无新增窗口/lr网格，维持具体外部AP报告。 停止既有优化扫描，需新科学因子才重开。 |
| dili / AUROC↑ | MiniTabM在native四配对未支持；TabICL Mini−CheM排序随canonical/scaffold反转；MoL主比较3胜5负。 | 内stop优于对照而外部Valid更差已有反例；不能统一认定Mini或MoL更强。 小样本结构支持、selection、完整recipe混杂尚在。 | 保持现有候选；本轮不将新家族任意加到DILI；待独立信息源有对应假说后登记。 不以混合胜负平均为有效，不重跑容量/TabICL矩阵。 |
| half_life_obach / Spearman↑ | rank相对同.5MSE控制在四Valid种子及两native结构划分×两seed均支持。 | 这些共享端点/标签，不是八个独立数据集；不证明rank适用于所有readout。 样本对暴露、目标优化和监控原因仍可能并存；现有假设已经有足够局部对照。 | 保留recipe，不重复半衰期seed或lambda；新local目标只在Hep验证。 有限recipe效益支持，不扩为因果通则。 |
| herg / AUROC↑ | 已有floor结果方向不一致，无本轮新增任务分数。 | 不能凭全22汇总升高就认定修复hERG。 稳健性和化学盲区尚未有新的可辨证据。 | 保留任务级不确定性与当前配置；不凑一个新seed。 有独立分组反证才重开，不称已完成泛化验证。 |
| hia_hou / AUROC↑ | 简单affine读出的四seed局部支持已有真实学习。 | 小任务的AUROC饱和和valid选型限制仍在，复杂头不自动更好。 结构压力外推未由本轮解决。 | 保留简单头；不因为已有新局部方法而强制替换。 同任务更复杂对照须有新的失败机制，不循环容量网格。 |
| ld50_zhu / MAE↓ | Huber等raw四seed配方支持；canonical结构压力方向不稳定。 | scaffold因fit仅约36.37%按登记门槛跳过，不是模型质量负例；旧H0数值异常放大raw收益。 目标尺度修复与一般化仍未完全分离。 | 保持raw/structure分账；不重做跳过条件或通过补seed假装解决。 若新划分改变支持须明确新问题，不事后重排到最好分。 |
| lipophilicity_astrazeneca / MAE↓ | F010旧配对收益支持；Huber分组结果不一致。 | MAE改善不是所有低/高标签群修复；Hep的端点规律不能直接推广。 已有具体群仍有剩余风险；无新的lipo-specific待测机制。 | 保持当前候选，闭合已有Huber分支而非再扫delta。 仅新的独立表征/分组反证触发重开。 |
| pgp_broccatelli / AUROC↑ | floor混合、部分候选盲预测近同，潜在信息增益低。 | 预测同或验收通过不是质量相同证明，也不能凭无标签分布宣称改善。 新的生化条件或不同表征是否提供增量未知。 | 不在现有近同候选上加seed/缩放网格；等待差异明确且有任务假说的方向。 数学同义先零fit排除，统计未显著不作等效。 |
| ppbr_az / MAE↓ | Mini当前native四配对支持，raw3/4且seed46有同平台反例；M2Mini F010=H0；Huber16低尾未修复。 | 平均改善与低尾共同错误共存，不能把平台作为唯一原因或把缩放等价槽算实验。 表征偏置、读出与具体分子条件仍待区分；低尾成员按旧登记固定。 | SMI面板作为不同预训练信息编码的完整配方，canonical/scaffold各2seed；复用CheM/Mini并重查旧尾群及补群。 若只搬迁错误/旧尾未改善且总体无收益，关闭这一个新表示配方，不改旧群成员。 |
| solubility_aqsoldb / MAE↓ | MiniMLPraw/native支持；M6近参数量对照制约简单容量解释；Mini F010=H0等价skip。 | 参数数量相近不证明相同归纳偏置；不能自动认为上下文读出或几何更优。 SOLCTX4成本/收益与GEO新表示尚无结果，前者并未由Hep提升自动授权。 | 保留P004-SOLCTX两proposal共4context条件，不新计；几何仅继承P003-G固定头；不把准备当疗效。 实际trigger不满足则跳过，不把HOOF不同TabICL配置偷换成旧SOLCTX控制。 |
| vdss_lombardo / Spearman↑ | rank−HalfMSE四配对正；FullMSE与HalfMSE四项外部得分一致。 | 相同外部分数不证明权重、梯度轨迹或预测逐点相同；不能以此否认系数控制的必要性。 本任务rank机制与Hep局部目标可能不同。 | 保留现有rank配方，不扩seeds/lambda；本轮新增目标只在已发生矛盾的Hep。 有限recipe支持；遇新结构/群反证再开，不设全局最优终点。 |

## 8. 新方法：按可改变的判断排序，而不是按家族名凑广度

### 8.1 冻结SMI-TED具体瓶颈：值得准备，但尚未准入

拟定资产不是泛称“SMI-TED”，而是`ibm-research/materials.smi-ted`的`smi-ted-Light_40.pt`，LFS指针大小1,155,124,350字节、SHA256 `baf252dbc081a00c68d2fd6ed8b08a0db0fa15244cfea442d49f0619a3a65375`。固定modelcard revision为`414c3ea0a8603ef49d1c5bb3db336e09877c01ce`，模型卡标Apache-2.0；但在这个精确revision读取权重指针和源码的Web路径未成功，当前main原文和LFS指针不被追认成完整immutable producer。必须在准备阶段核实固定源码、词表、config、checkpoint及许可关系。[X-SMI-CARD; X-SMI-WEIGHT; X-SMI-CODE]

实读官方源码暴露了重要的不兼容点：默认`normalize_smiles(...,isomeric=False)`会去掉立体信息；tokenizer默认截断至202；encoder token输出经padding/flatten后进入**冻结decoder.autoencoder.encoder瓶颈**得到768，而非随意均值池化。`detach()`不等于全参数/buffer冻结证明；`strict=False`可能隐藏关键key缺失；默认批切分也不应当作可靠的峰值约束。[X-SMI-CODE:normalize_smiles,encode,extract_embeddings]

新的`FrozenSMILightStereo005-v1`是明确待准备的wrapper：保留原SMILES及原行，模型输入规范化只做已登记canonical **isomeric**编码、不做盐/互变异构清洗；无静默截断、未知token、失败丢行或零向量。超过202或不支持输入不能默默取子集，必须将该任务置blocked、报告完整覆盖缺口。预训练Transformer、autoencoder瓶颈和全部buffers均eval冻结，不训练任务原生net、不生成分子、不加入重构标签；只在未来批准的任务头学习train-fit.Y。这样会偏离作者默认输入规范化的训练分布，所以新结果只评价这个保持本项目输入身份的完整配方，不归因于单一“语言模型效应”。

N面板固定为AMES与PPBR，原canonical/scaffold，seed44/45，H0各fit重拟合；768→256→1、ReLU、dropout0.1；AdamW lr0.0005/wd0.0001、batch128/max50/pat8/min_delta1e-7。AMES用BCE-with-logits，stop AUROC↑，sigmoid连续概率；PPBR用fit-zY MSE，stop原尺度MAE↓，逆变换一次。两个任务只编码一次全部官方train（4684、1952行），特征在两个split和两个seed共享；不编码Valid/test。8个新梯度头，16个历史同期split/seed控制只复用一次。[next_experiments.json:N; split_register.json; E-OLD-SPLITS]

控制是AMES的CheM/Morgan、PPBR的CheM/Mini对应旧native头，保持它们真实预处理不重写成H0。新头输入维度及参数量随表示变化，故这是一项**bundle**，不是纯表示因果干预。必须检查整体主指标、原盲区、互补群、输入覆盖；即便任务平均上升也不能宣称同一错误已修复。论文/模型卡的公开benchmark仅是方法依据，不是本项目冻结encoder的收益预报。[X-SMI-PAPER; X-SMI-CARD; E-TASK22]

### 8.2 KPGT：有明确接口意义，但不能冒造可运行checkpoint

KPGT官方v1.0.0代码提供不同于SMI的图/知识联合表示。`generate_fps`拼接FP虚拟节点、MD虚拟节点和图均值各768，得到2304维。其预处理FP是RDKFingerprint512、path1…7，不是Morgan；MD是NormalizedRDKit2D200。辅助信息已经进入图消息路径，不能把输出的graph片段切出来就宣称“没有指纹/描述符的纯图先验”。预处理还会筛`valid_ids`，图forward有节点移除的原地操作，示例特征脚本不提供本项目的完整冻结及eval证明。[X-KPGT-MODEL; X-KPGT-PREPROCESS; X-KPGT-EXTRACT]

官方repo/code为Apache-2.0，v1.0.0版本可定位；官方base权重Figshare链接实际返回403，未获得可绑定的checkpointSHA与权重使用条款闭环。故KPGT仅保留**独立、有机制根据的储备方向**，不填一个假的“base”资产到可执行矩阵。未来仅在精确权重、全行图输入、eval/param+buffer冻结与已有实验身份去重均通过后，才值得注册一个能区分图先验和已有SMI/Mini信息的有限面板。当前阻断是访问/来源，不是科学质量负例。[X-KPGT-REPO; X-KPGT-WEIGHT; X-KPGT-PAPER]

### 8.3 已调研资产与当前实际准备度

| 资产/角色 | 当前证据与接口 | 当前动作 |
|---|---|---|
| CheMeleon2048 | 已验冻结缓存/任务头，多任务控制；真实权重SHA在scientific_assets | 复用控制，不因Hep失败统一换底座 |
| MiniMol512 | 当前HOOF原cache、结构stress多任务证据；任务/读出交互明显 | O/S复用；其余任务按22表保留范围 |
| Morgan2048 | RDKit2024.09.6 radius2/chiral二进制；确定特征非预训练encoder | 保留AMES正负native和local结果，不用SMI同化其identity预处理 |
| TabICLv2.2.0 | 分类/回归精确checkpoint在表；context、norm、cache配置需逐配方绑定 | HOOF与原SOLCTX不能互换；本轮0新context |
| MoLFormer-XL-both-10pct | 具体768表示配方已有16头负/混合，实际receipt版本链不足处保留 | 不把同一MoL再换名字试；不推广为全sequence家族无效 |
| UniMol2-84M CLS768 | exactweight/code已登记；GEO002 freshproducer准备已派 | 继承Uni G4，不重复派发，不把静态v4当真实生产 |
| Monroe720 | exactweight/code已登记；旧cache原producer冻结缺失，且预训练并非几何唯一信息 | 保留原Monroe G4阻断；不能借后补hash追认旧缓存 |
| SMI-TED Light40 stereo768 | 本轮深入原模型卡/代码/LFS，固定源关系和全行producer未闭合 | N8明确`blocked_assets`；独立准备有信息价值 |
| KPGT | 官方代码/2304接口已查；权重链接403 | 只保留具体准备缺口，不冒填新fit |
| Uni-Mol v1 / MolE | 历史调研未完成具体资产链；Uni v1≠已选UniMol2 | 不冒称当前准备好，不以家族名列训练 |
| TabPFN2.6及Monroe可选TabPFN组件 | 许可/使用门槛没有被本轮新证据解除 | 不绕过gated terms，不把TabICL许可搬给TabPFN |
| scratch小D-MPNN / 其它经典特征 | 分别是新从零图模块或手工特征，并非外部冻结底座；已有简单头/Morgan试验需去重 | 没有新的可区分假说时不重开通用基线网格 |

`scientific_assets.json`中明确区分historical_status与current_readiness；某历史16context pending字段不代表当前仍pending。GLM、DeepSeek、Qwen、Astra、Pro等始终是执行/研究角色，不是分子编码器。[E-OLD-ASSETS; E-CURRENT; E-TASK22]

几何新增信息也有边界：由相同SMILES生成的构象不是实测条件；原子裁剪、失真立体/键、失败丢行会改变任务样本。GEO002已登记的whole-row coverage、seed/timeout与全producer冻结必须保持；结果只有准备成功时仍为零疗效证据。当前原G8评估仍是同两个任务同scaffold的有限配方，不替换全22。

## 9. Q4：上轮14条提案逐项更新，保留原ID

`prior004_disposition.json`逐项绑定原Pro004六文件中的proposal，不以同名新提案重复物理学习。原Pro004根矩阵14条的科学身份已完整读取与本轮状态对照。[E-P004-MATRIX; E-P004-INTAKE; E-ME40]

| 原proposal | 当前事实 | 本轮决定 / 新增fit |
|---|---|---|
| P004-H-chemeleon-canonical-gap | Pair16已完成 | 固定gap不支持默认；关闭这一对比路线，0 |
| P004-H-chemeleon-canonical-uniform_matched | Pair16已完成 | 保留完整均匀控制，不把gap负等同rank全负，0 |
| P004-H-chemeleon-scaffold-gap | Pair16已完成 | 主rho相对uniform明显负，0 |
| P004-H-chemeleon-scaffold-uniform_matched | Pair16已完成 | 相对旧全pair rank有有限正支持，0 |
| P004-H-minimol-canonical-gap | Pair16已完成 | 主近零、seed翻转，端点局部好不扩大结论，0 |
| P004-H-minimol-canonical-uniform_matched | Pair16已完成 | 保留匹配pair数的控制，0 |
| P004-H-minimol-scaffold-gap | Pair16已完成 | 主差负且seed不稳，0 |
| P004-H-minimol-scaffold-uniform_matched | Pair16已完成 | 高尾收益也见uniform，反对gap独有机制，0 |
| P004-SOLCTX-chemeleon-scaffold | 原2个context身份未执行/条件保留 | 不新计、不偷换HOOF配置；实际触发再由主控审，0 |
| P004-SOLCTX-minimol-scaffold | 原2个context身份未执行/条件保留 | 同上，0 |
| P003-G-solubility_aqsoldb-monroe720-scaffold-mse | 原2头，producer不准入 | 保留阻断，0 |
| P003-G-solubility_aqsoldb-unimol2_84m_cls-scaffold-mse | 原2头，freshproducer准备已派 | 仅继承GEO002准入条件，0 |
| P003-G-clearance_microsome_az-monroe720-scaffold-mse | 原2头，producer不准入 | 保留阻断，0 |
| P003-G-clearance_microsome_az-unimol2_84m_cls-scaffold-mse | 原2头，freshproducer准备已派 | 仅继承GEO002准入条件，0 |

保留历史失败：ME001准备时provider quota中断属于真实未准入准备；后续修复准入不删除该事件。ME40有一项未完成梯度尝试，26个partial steps为记录推断；不能改写为所有attempt都成功。旧LD50 scaffold门槛skip、Mini分母等价skip、未评分历史项、源链接缺口也各保持其类型，不混为模型性能负例。新本地文档生成的语法/键错误另记在review，不冒作训练失败。[E-EVENTS:ME001-E-PREP-INTERRUPTION-01; E-ME40]

## 10. 关键新主张的定向复核与局部缺口

| 新判断 | 直接支持 | 定向交叉检查 | 反证或不能推出的内容 |
|---|---|---|---|
| 端点贡献约84.43%净MAE收益 | 原三段n和MAE | Decimal与float两路径加权，并回到全848MAE | 非行级评分、非因果贡献率；中段CI跨零不是无效证明 |
| 共同错误未修复 | 当前123/39及旧31/32回验 | 检查完整群/补集n和已验MAE恒等式；检查旧scaffold群是canonical预测回验 | 不能定位行错误成因，不拿当前群建部署gate |
| gap默认路线不支持 | 四核心单元完整主差、seed差及高低尾 | 与ME40最终消费、事件链及uniform正例对照 | 不否定所有pairwise损失或所有local架构 |
| O/S不重复旧学习 | 原HOOF是fullMSE+旧selected state；新Half/rank同期控制与尺度约束 | 按完整config/split/seed双路径去重；历史14提案逐项映射 | 新monitor必须明确，不宣称旧新同实现因果 |
| S去掉全局正尺度、非单位归一化 | 全fit协方差数学定义 | 零更新fixture给初始化相同、正尺度不变、batch拼法无关验收式 | 仍有优化/正则和各向异性解释，不能等同不集中 |
| SMI是候选而非ready资产 | 官方模型卡/权重pointer/代码 | 对照normalize/截断/实际瓶颈，固定revision读取尝试保留失败 | 代码/词表/权重完全绑定未闭合；论文分数不是本项目疗效 |

原HOOF消费还明确披露CPU context continuation。没有做CPU/GPU等价实验，不把原跨实现/平台因素默认为零；新O/S所有臂固定相同CPU实现以减少这项新混杂，原TabICL作为有用完整配方参照但不作纯readout因果控制。[E-EVENTS:HOOF001-E-CANONICAL-OOF01]

证据缺口分为：**已发表但定向未读完**（例如历史索引下未影响本问题的原件，不冒称全库审计）、**当前公开仅reference-only**（B24部分原配置/全群消费无法通过登记payload下钻）、**实际访问受阻**（KPGT官方权重403、SMI固定文件路径不可达）、**未记录在本投影**（HOOF旧monitor/fit-stop逐fold计数、安全cache哈希）、**未来实验本来才可回答**（T2与新objective/RMS、SMI收益）、**实际进行中**（原scaffold/GEO002）。每项及受影响proposal都在`evidence_gaps.json`。局部缺口不要求重验已可信冻结、整库评分或运输。

## 11. 最终逐问题判定与科学收口

**Q1：answered（证据解释层）。** MAE改善扩展覆盖但不建立排序或旧盲区修复；目标/标尺、集中、支持、测定条件、历史覆盖各有支持与反证，未虚构唯一原因。旧未覆盖542与已看542的区别保留；条件CI不被升级为独立泛化。答案见§§2–4，后续Z/O/S与安全来源核对。

**Q2：answered（设计层）。** Z固定状态、O同期目标、S预锁尺度四格和N独立表示明确区分；T/尺度同义、逐点单位范数多因素、界内单侧loss空操作均排除。全task/config/split/seed/预处理/头/优化/监控/预测尺度与完整群在机器文件中；未实现接口写new_code，SMI写blocked_assets。具体因果结果必须未来授权实验，方案完整不意味着科学效果已成立。

**Q3：partial。** 全22任务动作和已调研底座真实状态已覆盖；SMI/KPGT一手资料、接口风险及冻结方案已查。SMI固定源码与checkpoint关系/full-row producer、KPGT权重可得性/许可、现有实验身份的最终执行端核对仍未闭合，不写ready。GEO002已派，不重复；缺口只阻断依赖新资产的8头，不阻断Hep机制设计。

**Q4：answered（方案和历史处置层）。** 上轮14提案逐一保留/关闭/条件继承；新24proposal为20/40/48有限上限，已有控制、context、view、共享编码分开；所有重复方向有科学跳过原因，不以成本或队列状态冒充结论。预算未知项和相应停止规则可供多个批次连续派发，授权仍由主控另行登记。

因此整体`scientific_status=needs_evidence`。`file_integrity_status`和聊天终态独立：文件封包成功不把Q3改成answered，也不证明全部机制已解决。下一研究触发于预注册对比完整消费、关键反证、新资产准入改变可选问题或原scaffold结果实质改变解释；不按单头、分钟或空队列触发。
