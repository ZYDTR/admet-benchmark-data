# ADMET Pro 第四轮独立研究：从更多胜例转向可区分的解释

**request_id**：`admet-pro-next-research-20261103-004`  
**输入固定commit**：`730373b4718d24618592b677a71a69508054f07a`  
**输入manifest SHA256**：`d5c998c3c95c40a7ed0555da01cb566a46457f65f9eb279530cd4c797d703fae`  
**科学截止**：2026-11-03T01:14:50.075644+00:00；仅补入包内01:20:10的T2运行观察，不推断任何新质量结果。  
**角色与权限**：只读研究、方案交付；没有训练、模型加载、编码/推理、逐行Valid真值/残差访问、任务指标计算、Agent派发或外部发布。  
**科学状态**：`needs_evidence`。Q1–Q5及Q7在解释/方案层回答，Q6的fresh producer和全行准入仍是`partial`。这不是把尚待实验检验的机制伪装为确定，也不是等待全部旧档案才继续。

文中`[E-…]`、`[X-…]`、`[P003-…]`指向`evidence_registry.json`的精确原件、版本和实际阅读范围。数值表来自已验汇总原文；没有执行归档脚本、重算原评分或从逐行数据导出指标。新计算限于方案计数、参数量算式、文件完整性与数学推导。

## 执行摘要与问题定位

最重要的科学更新不是“排序18胜2负”这个总数，而是三个层次必须分开：**给定任务的配方有效性**已有显著增加的实证；**表示×读出×划分交互**已有直接反例；**表示单独或某种生物化学机制的因果解释**仍未被这些配方比较识别。它们不能相互替代。[E-RANK-HEP/E-RANK-MICRO/E-RANK-VDSS/E-TAB-STRESS]

本轮建议优先完成一个此前没有的Hep判别：固定0.5MSE+0.5pair项、头、种子和划分，比“大标签间隔配对”与“每批相同数量的均匀配对”。这不同于再扫seed、lambda或训练窗口，也不同于已完成R/X44。先做两个有负例的表示/划分细胞，共8新梯度fit；只有需要完成交互判别才补另两个细胞8fit。Hep8仅消费已派结果，不重复。Sol四冻结上下文为有条件读出迁移；既有G8保留原proposal ID，fresh geometry producer过关前不启动。[E-STATUS/E-RANK-HEP]

| 问题 | 直接结论 | 本文位置 | 未闭合的决定性部分 |
|---|---|---|---|
| Q1 | 全22任务分别保持、收口、条件等待或判别；没有统一最佳配方 | §Q1、task22_actions.json | 10历史未评分、特定BBB after、外部最终泛化 |
| Q2 | rank迁移局部支持增强；Hep负例值得做配对信息而非更多种子 | §Q2、H1/H2矩阵 | pair-gap改善若出现仍非真实标签噪声证明 |
| Q3 | TabICL体现读出/表示/划分交互；N8不自动触发 | §Q3、条件Hep8/S | Hep8零结果，样本支持与化学组成未隔离 |
| Q4 | M5/M6、窗口和LR已经约束旧解释；T2不能由Jensen预言AP | §Q4 | T2零质量结果、成员机制具体贡献 |
| Q5 | 正L证实限定预测对的区间外共同误差；不能定位分子或约束任意混合 | §Q5、cohort_evidence_requests.json | 新配方在原固定群的合规前后汇总 |
| Q6 | MoL当前配方收口；几何未被疗效否决，旧cache因producer缺证拒绝 | §Q6、scientific_assets.json | 原producer缺证不能补签；fresh full-row生产未发生 |
| Q7 | 14条确定proposal，分8梯度／16梯度+4上下文／24梯度+4上下文上限 | §Q7、next_experiments.json | 授权、实现fixture和被明确标出的资产门槛 |

## 证据和计数的基线

当前784实际梯度头、763逻辑run；652wholeValid与164nativeStress共816单项指标。32冻结上下文、88固定群指标、8被抑制群项、95复合分数，以及32个D/32个L诊断分别记账。不能将context当梯度、views当fit、D/L当新的模型质量测量或将10项历史未评分视为零分。旧的pending/next字段保留为历史，但本轮CURRENT的完成状态覆盖它们。[E-STATUS/E-READING]

Rank44、window12、capacity26、CYP3A4lr8、AMESdual4、MoL16和TabICL32均已实际完成。科学消费可以先于完整归档：window、Tab原16和Tabstress16的bulk pending不否定已经接受的数值。T2两头的早期两次失败都在新头构建/更新前退出，约6秒各一次；晚观察记录训练更新已发生，却仍为0质量结果。Hep8也是0结果。不能把“已开始更新”或者“准备通过”写成模型改善。[E-STATUS/E-LATE]

冻结、标签边界、输入行序与固定评分的既有可靠验收作为继承事实；本轮没有重新打开全部tensor/预测数组，也没有重演全库冻结或运输。核心输入/输出的task/split/row_index对齐在已验评分入口继承；新方案仍要求其新预测保持相同原行成员与顺序。登记的模型、配方、partition和输出尺度是科学比较单位，不是仅看run名字或seed整数。[E-DESIGN/E-REUSE/E-POLICY]

完整历史可从当前`ledger/history-index.json`、`HISTORY_BRANCH_INDEX.json`、完整experiment/issue/claim/proposal账，以及固定旧002/003分支枚举。本轮定向读了所有22端点行动条目、相关新数值矩阵、旧问题链和此前003原件的相关字段；没有声称逐行读完24494行实验账、28144行SOURCE_MAP或每个二进制。旧准备错误、原pilot无学习失败、资源/写边界失败、被否定的冻结摘要、Mini尺度问题、等价skip和未评分项不因新胜例消失。详细实际范围与未读项见review和evidence_gaps。[E-HISTORY/E-EVENTS/E-ISSUES/P003-HISTORY_NAVIGATION]

<a id="q1"></a>

# Q1：全22端点行动前沿

## 三个必须分开的判断

**配方有效性**：例如在固定nativeTrain成员、指定表示与0.5/0.5目标下，microsome八个rank-minus-HalfMSE为正，足以保留这一已测配方。它不需要重新评分才成立。

**表示/读出交互**：MiniMicro在MLP结构压力下不稳定，但在同两套结构方案中，换冻结上下文读出后相对旧MiniMLP均值均改善；CheM未同样改善。这直接反对“Mini信息一律不足”与“TabICL一律更好”两个简化解释。

**机制**：更大的label-gap、共享成员、上下文预处理或者3D几何可以是有依据的解释，但这些单独因素尚未由已有多因素配方完全隔离。Mini维度512与CheM2048、特征缩放、第一层参数量、预训练内容、stop选择和主机精度都可能参与。应把可识别的实验因子写清，而不是把某个更高分数命名为机制。[E-RANK-ALL/E-TAB-STRESS/E-CAP-MICRO/E-CAP-SOL]

## 22任务逐项清单

下表的“收口”针对给定方向，不等于该任务已经科学完成。每项完整事实/反证/未知/下一判别/引用在`task22_actions.json`。

| task / 本地指标 | 已支持与保留 | 反证或未知 | 当前行动与收口条件 |
|---|---|---|---|
| ames / AUROC↑ | Morgan rawValid四seed及固定群有收益。 | 结构stress既有负例；双选择器同4轨迹8views，Morgan相对CheM四次均负，selectorB不恢复表示排序。 | 消费dual4完成结论；不重复selector、窗口或seed。仅当独立描述性分布诊断改变行动时另注册。 关闭“只换stop选择器便能修复Morgan结构迁移”的当前解释，保留raw范围。 |
| bbb_martins / AUROC↑ | 旧floor有局部改善与混合方向；当前无新增决定性结果。 | 既有H0 seed46缺after冻结证据，不能以其他run结果填补。 | 只索引原有before/after元数据；未找到保留受影响run不可用于依赖该前提的比较，不为补档重训。 无新证据不重复floor/seed；缺口只阻断该run，不阻断全库。 |
| bioavailability_ma / AUROC↑ | 保留旧已验基线及已做简单头对照。 | Mini/Morgan MLP各两seed负；heads140已包括简单头，不能宣称尚未尝试。 | 不扩同配方seed；如未来新读出先在有明确交互任务过关再谈迁移。 当前被测Mini/Morgan MLP方向收口，不否定整个家族。 |
| caco2_wang / MAE↓ | F010及已有TabM、Huber/drop0有局部收益；四新TabICL结果已知。 | MoL主比全负，TabICL未超过旧CheMTabM；M5不随k单调；200窗口未改善；固定群n10不准评分。 | 复用已完成窗口/容量，不新增Cacofit；保留whole指标，不扩大n10小群。 当前窗口/k的加量理由不足；不是任务最优已证明。 |
| clearance_hepatocyte_az / Spearman↑ | Mini rawValid四seed优势；Rank6/8；两个小负例分别位于CheMscaffold44与Minicanonical45。 | Mini结构stress仅1/4改善；不能把6/8写成跨表示一致或八独立数据集。 | P004-H配对选择vs等数量均匀配对；Hep8只消费已派，不重复。 有信息对照失败/反向则停止该pair-gap假说；不扫q/lambda/seed。 |
| clearance_microsome_az / Spearman↑ | Rank8/8；MiniTabICL两native方案均优于旧MiniMLP均值，MiniMLP rawValid优势仍是事实。 | Mini结构MLP原优势不稳；CheMTabICL两方案未改善；M5 k32不胜k8；近参数预算M6两seed异向。 | 不重复R/X与N8；可作为已有G8几何判别任务，只有freshproducer门槛过才计新fit。 当前rank迁移和读出交互有局部支持；无额外seed/grid。 |
| cyp2c9_substrate_carbonmangels / AUPRC↑ | 现有对照/指标可复用。 | posBCE两seed负，Morgan两seed负，Mini混合；不能与另一substrate任务合并结论。 | 不重跑已负权重；待跨任务机制有可迁移依据再单列预登记。 当前权重/表示配方否决范围保留；任务尚非科学完结。 |
| cyp2c9_veith / AUPRC↑ | F010两个seed小幅正。 | 不足以推到所有CYP或新数据；无本轮特异新交互证据。 | 无需维持活跃而新开搜索。 保留候选，不增加同方向seed。 |
| cyp2d6_substrate_carbonmangels / AUPRC↑ | weightedBCE+F010四个Valid种子支持。 | 不能将此收益转嫁到Veith或其他CYP；结构迁移仍未知。 | 若未来允许新的结构方案，单独登记比较；本轮不空造结构成员与对照。 该配方raw范围保留，非机制或全局最优。 |
| cyp2d6_veith / AUPRC↑ | MiniTabM raw/native稳定局部收益，M5 k1<k8<k32为该任务支持。 | MiniTabICL弱于旧MiniMLP/TabM；MoL主比8负；Jensen不保证AP。 | 只等T2两头既定AP；GQ-CYP固定high群四个已存TabICL预测的合规汇总可补局部比较。 T2若负/零则保留mean-member，不加seed/k/lossweight；若正仅保留当前scaffold范围。 |
| cyp3a4_substrate_carbonmangels / AUROC↑ | 保留H0。 | F010两seed退化，不能同CYP3A4Veith低lr收益混在一起。 | 不追加统一floor。 本配方方向否决，不否决该任务未来新假说。 |
| cyp3a4_veith / AUPRC↑ | H0 lr1e-4四native配对均胜5e-4。 | window8的200/8与50/8相同；full200三负五同；F010主比多负。 | 不新开lr/epoch/floor格点。 本配方优化解释已足够收口；未来改变表示才另立问题。 |
| dili / AUROC↑ | MiniTabICL相对旧MiniTabM两native均值均改善。 | Mini−CheM TabICL canonical两正、scaffold两负；旧MiniTabM结构4负；MoL主比3胜5负。 | Hep8对clearance机制有信息但不等于DILI答案；本轮不再DILI无动机新fit。 维持按方案条件化结论，未有decision-changing新对照前暂停此配方搜索。 |
| half_life_obach / Spearman↑ | 四Valid种子与两native结构划分×两seed对同系数HalfMSE支持。 | 重复Valid/原train结构压力并非独立外部；rank收益非完整因果机制。 | 不新增半衰期seed/系数；用Hep判别而非重复正例。 当前半衰期配方收口，等待真正新反证。 |
| herg / AUROC↑ | 旧对照保留。 | floor小幅混合方向，没有本轮跨任务证据可替代本任务。 | 不机械将rank/context/geometry全任务推广。 无新假说可暂收当前搜索，不宣称最佳已知。 |
| hia_hou / AUROC↑ | affine在既有两floor四对照有支持；F010 affine相对drop0亦支持。 | H0某drop0对比持平；复杂头并非必然更好。 | 不以“尚未做线性基线”重复heads140。 简单头局部配方可留，停止无理由扩容。 |
| ld50_zhu / MAE↓ | Huber raw及high群四seed改善。 | canonical结构一正一负；scaffold因fit36.37%低于既定50%门槛skip，不能记为负结果；low群混合且L>0。 | 维持原群，不重抽“好划分”或扩小群。 Huber泛化只在已测范围成立；结构原因未知。 |
| lipophilicity_astrazeneca / MAE↓ | F010与其他既有候选保留原成绩。 | Huber两固定群均有正负，不支持普适修复。 | 不追加Huber同配方seed。 当前Huber方向收口，原风险保留。 |
| pgp_broccatelli / AUROC↑ | 已有H0/F010及同分/近同预测记录。 | 方向混合，近同预测不构成新表示信息。 | 不借模型共识认定正确；不为idle创建新fit。 当前floor搜索可暂停。 |
| ppbr_az / MAE↓ | Mini结构4正、raw三正一负。 | seed46原尺度负例保留；low固定群46/47负；MiniH0/F010数学同分母，M2无需训练。 | 不重启等价floor；保留D/L下界限制，不擅自组合/校准。 M212skip是等价结论，不是四次新成功；Mini非普适。 |
| solubility_aqsoldb / MAE↓ | Mini raw/native支持；M6近参数预算Mini512胜CheM128两seed。 | 低分歧群L明显为正，不能把整体MAE下降写成盲区修复；M2等价。 | 先GQ-SOL8个固定群汇总；条件SolTabICL4上下文；仅freshproducer可解锁继承G8面板中Sol4。 参数量单因子解释被削弱，非表示因果证明；不做新宽度/floor网格。 |
| vdss_lombardo / Spearman↑ | Rank四native主比均正；FullMSE和HalfMSE四个指标相等。 | 指标相同不证明预测或训练轨迹相同；两个划分来自同一官方train。 | 不再扩大seed或lambda；借Hep困难例做目标选择判别。 当前rank迁移已足够保留配方，等待外部反证。 |

不能为了覆盖22任务就在22任务上新增同一loss或新模型。HIA的简单头收益、CYP2C9 substrate的负权重、CYP3A4 substrate的负floor、CYP3A4 Veith的低lr收益、LD50不可行scaffold的skip，是不同的科学状态。尤其LD50 fit比例门槛失败既不是模型负例，也不允许重抽到一个“好看”的划分。对新矩阵之外的任务，报告明确触发条件比重复训练更有信息。[E-TASKS/E-FRONTIER]

<a id="q2"></a>

# Q2：排序迁移的签名证据与剩余判别

## 完整主比，不将20个配对当20个数据集

下面数值直接引用R/X原表；Δ为原件已发布的rank−HalfMSE。`canonical`与`scaffold`来自相同官方train，模型seed又共享同一成员集。没有独立样本假设、p值或“18/20成功率可外推”的结论。[E-RANK-HEP/E-RANK-MICRO/E-RANK-VDSS]

| task | 表示/方案/seed | Rank | HalfMSE | 原件Δ |
|---|---|---:|---:|---:|
| clearance_hepatocyte_az | chemeleon / canonical / 44 | 0.564837303989 | 0.469135769906 | +0.095701534083 |
| clearance_hepatocyte_az | chemeleon / canonical / 45 | 0.538150154138 | 0.529749668769 | +0.008400485368 |
| clearance_hepatocyte_az | chemeleon / scaffold / 44 | 0.550793862509 | 0.570375218203 | -0.019581355695 |
| clearance_hepatocyte_az | chemeleon / scaffold / 45 | 0.552095360873 | 0.538727095863 | +0.013368265010 |
| clearance_hepatocyte_az | minimol / canonical / 44 | 0.565860156486 | 0.543794791708 | +0.022065364778 |
| clearance_hepatocyte_az | minimol / canonical / 45 | 0.492502623021 | 0.522842198842 | -0.030339575821 |
| clearance_hepatocyte_az | minimol / scaffold / 44 | 0.544561403861 | 0.523411006277 | +0.021150397585 |
| clearance_hepatocyte_az | minimol / scaffold / 45 | 0.511576008255 | 0.493400307001 | +0.018175701253 |
| clearance_microsome_az | chemeleon / canonical / 44 | 0.617700484263 | 0.616732304276 | +0.000968179988 |
| clearance_microsome_az | chemeleon / canonical / 45 | 0.632357011004 | 0.610726614421 | +0.021630396583 |
| clearance_microsome_az | chemeleon / scaffold / 44 | 0.372050391983 | 0.358079458857 | +0.013970933126 |
| clearance_microsome_az | chemeleon / scaffold / 45 | 0.335059239545 | 0.316030072144 | +0.019029167401 |
| clearance_microsome_az | minimol / canonical / 44 | 0.566867730546 | 0.543813151115 | +0.023054579431 |
| clearance_microsome_az | minimol / canonical / 45 | 0.586351939750 | 0.582335479768 | +0.004016459983 |
| clearance_microsome_az | minimol / scaffold / 44 | 0.385126689366 | 0.341843352235 | +0.043283337132 |
| clearance_microsome_az | minimol / scaffold / 45 | 0.389647596931 | 0.338640292227 | +0.051007304704 |
| vdss_lombardo | chemeleon / canonical / 44 | 0.718491654754 | 0.633672195518 | +0.084819459237 |
| vdss_lombardo | chemeleon / canonical / 45 | 0.705258772410 | 0.608432655613 | +0.096826116797 |
| vdss_lombardo | chemeleon / scaffold / 44 | 0.573994767954 | 0.443044378928 | +0.130950389026 |
| vdss_lombardo | chemeleon / scaffold / 45 | 0.578923949022 | 0.417649968314 | +0.161273980709 |

Hep两个负例是CheM/scaffold/44的−0.0195813556946和Mini/canonical/45的−0.0303395758210。它们分处不同表示、划分和seed，不能据此否决某一种表示的排序项。micro最小正差只有约0.00096818，因此“八正”也不等于八项都有实际业务重要性。VDss四个增量较大，但仍限于一个端点及其相关划分。[E-RANK-HEP/E-RANK-MICRO/E-RANK-VDSS]

当前已解决的是一个重要竞争解释：原rank配方同时把MSE系数降为0.5，若只与FullMSE比，改善可能仅来自尺度或优化变化。新HalfMSE保持同0.5系数，rank再增加pair信息，因而比原FullMSE对照更可解释。VDss FullMSE与HalfMSE四个**评分数值**一致，且rank四正，进一步削弱该任务的“仅MSE系数改变”解释。不能把同metric升级为逐行预测一致、checkpoint一致或梯度轨迹一致。Adam的自适应分母可能部分抵消整体梯度缩放，但eps、权重衰减、浮点误差和stop选择仍可打破严格不变性；这里是机制推理，不是已测证据。[E-RANK-VDSS]

已有排序目标在标准化Y尺度上，用不等标签的批内无序pair的softplus；MSE仍承担基数尺度拟合。Spearman本身对严格单调变换不敏感，MSE不具备这个性质，因此排序目标对测量幅度与异常点的重视方式确实不同。不过“相近标签更噪”需要测量重复性/误差信息，包中没有这种证据；不能由rank增益直接倒推实验标签噪声。实际单位和可能既有变换未完全确认，所有方案使用已提供numeric Y，不自行取对数或清洗。[E-ISSUES/U01的原文；E-RANK-HEP]

## 最有信息的下一实验：配对信息选择，控制数量

设父配置实际训练target tensor为z。只用当前fit行计算所有正的`|z_i−z_j|`，取其**中位数q**，并序列化。q=50%是本次处理因子的固定定义，不是经验最优值或噪声阈值；没有第二个分位数候选。

每个原批次先列出标签不等的无序pair。gap臂保留`|z_i−z_j|≥q`的全部pair，记数量m。uniform臂从同一批全部不等标签pair中，按独立的SHA256确定性顺序取恰好m个，不抽有放回、不改变原标签、不消耗模型/loader RNG。两臂都训练`0.5 MSE(all batch rows)+0.5 mean softplus(selected pairs)`。m=0时pair项为零。相同数量控制了简单的pair-loss样本数；相同系数控制了显式loss权重，但并不保证真实梯度范数相同——那正是需要保留的竞争解释。

**首批H1**只含CheM/scaffold与Mini/canonical，每细胞gap/uniform×seed44/45，共8fit；不是仅补跑两个负seed，而是在两个原有细胞中保留完整两seed对照。**条件H2**是CheM/canonical与Mini/scaffold，另8fit。它补齐表示×划分交互，但只有H1结果能改变下一决策时才做。所有已完成的dense-rank/HalfMSE控制直接复用，不重训。H1选择了旧负例所在细胞，因此是回顾性机制判别，不是独立验证。[E-RANK-HEP；next_experiments.json中的P004-H-*]

结果解释预先锁定：gap相对等数量uniform有稳定方向，支持标签间隔选择在该细胞中的作用；gap和uniform一起胜dense而彼此没有可行动差别，更支持稀疏化/随机梯度或正则竞争解释；二者都不改善或产生无法改变决策的混合结果则收口。不追加q、lambda、seed或窗长。完整新臂共享相同初始tensor与**新记录的**batch顺序；旧run未记过的permutation不能事后宣称已观察到。

canonical与scaffold、loss与表示交叉各自有信息：前者检验分组支持变化，后者检验同一排序处理在表示/缩放背景下的交互。但它们不是独立数据，也不隔离唯一“化学机制”。本轮保持既有成员集，不新划分、移行或让stress参与stop选择。

<a id="q3"></a>

# Q3：TabICL交互、Hep8与N8

## native16的完整表示主比

| task | 方案 / context RNG | MiniTabICL | CheMTabICL | 原件Mini−CheM |
|---|---|---:|---:|---:|
| DILI | canonical / 44 | 0.862781954887 | 0.798872180451 | +0.063909774436 |
| DILI | canonical / 45 | 0.859022556391 | 0.809210526316 | +0.049812030075 |
| DILI | scaffold / 44 | 0.857142857143 | 0.887830687831 | −0.030687830688 |
| DILI | scaffold / 45 | 0.876190476190 | 0.903703703704 | −0.027513227513 |
| Micro | canonical / 44 | 0.628074549352 | 0.600369071175 | +0.027705478177 |
| Micro | canonical / 45 | 0.617332047169 | 0.625804448152 | −0.008472400984 |
| Micro | scaffold / 44 | 0.420740093678 | 0.309832609437 | +0.110907484241 |
| Micro | scaffold / 45 | 0.410144779435 | 0.295713081298 | +0.114431698137 |

DILI是AUROC、Micro是Spearman，均最大化。表中不是MLP对比，也没有把模型seed和上下文RNG等同。[E-TAB-STRESS]

## 与旧读出的均值比较：两个不同问题

| task / 表示 / 方案 | TabICL均值 | 旧梯度头均值 | 原件差 | 旧头 |
|---|---:|---:|---:|---|
| DILI / CheM / canonical | 0.804041353383 | 0.847744360902 | −0.043703007519 | TabM |
| DILI / Mini / canonical | 0.860902255639 | 0.778665413534 | +0.082236842105 | TabM |
| DILI / CheM / scaffold | 0.895767195767 | 0.865608465608 | +0.030158730159 | TabM |
| DILI / Mini / scaffold | 0.866666666667 | 0.851851851852 | +0.014814814815 | TabM |
| Micro / CheM / canonical | 0.613086759664 | 0.613413892151 | −0.000327132487 | MLP |
| Micro / Mini / canonical | 0.622703298260 | 0.563454317826 | +0.059248980435 | MLP |
| Micro / CheM / scaffold | 0.302772845368 | 0.337239383547 | −0.034466538179 | MLP |
| Micro / Mini / scaffold | 0.415442436556 | 0.339742751260 | +0.075699685297 | MLP |

因此，“Mini在结构stress失败”必须附上原读出：MiniMicro使用冻结上下文可在两方案相对旧MiniMLP改善。这不抹去旧MLP负例，也不证明整个增益来自一个encoder因素。DILI在scaffold里MiniTabICL仍能胜旧MiniTabM均值，同时输CheMTabICL；“相对旧头改善”与“跨表示最好”是两件不同的事。[E-TAB-STRESS]

原wholeValid16也不能只挑Micro胜例。Caco四个MAE分别为CheM 0.377126322/0.367958018、Mini 0.364846655/0.365331361；旧CheMTabM为约0.345669175/0.345351307，TabICL并未统治。DILI原Valid仅48行，Mini两RNG是0.890109890/0.857142857，不能只报道前者。Micro原Mini上下文0.647019622/0.624364533优于旧MiniMLP均值的迹象，与native读出交互一致但仍非相同初始化。CYP MiniTabICL均值0.729745328弱于旧MiniMLP约0.755680482及MiniTabM约0.765301964；换成“大冻结读出”不是必然提升。[E-TAB-RAW；全部16原值见accepted_aggregate_evidence.json]

## 竞争解释及不能省略的混杂

1. **样本规模**：raw训练与native fit缩小同时发生，确实可能影响MLP；但同一nativefit上换读出能改变结果，而且Micro两nativefit为539/532、Hep为591/593，规模接近并不保证相近结果。它不能证明规模无关，也不支持“主要就是样本少”的单因果结论。
2. **组成与化学支持**：canonical和scaffold分组改变相似性与具体成员，也改变stop/stress标签分布。分区名称本身不说明哪个任务泄漏、哪个结构域缺失，更不能从分数反推某分子群标签。
3. **目标与选模**：MLP有50/8和stop选择；TabICL不是从同一随机头训练到同样epoch，而是冻结模型构建上下文、使用特征变换与推理集成。旧head mean与context mean是完整读出配方对照。
4. **缩放与维度**：CheM2048 F010、Mini512 H0仍带不同输入维数和特征几何；TabICL内部none/power与异常值处理可再改变有效坐标。不能把它们叫“仅换表示”或“仅换头”。
5. **平台与数值**：CPU梯度头和GPU上下文、dtype、AMP、cache、query批处理等均须有记录。实际可信分数不因跨主机就失效，但不能自动认定所有差异是统计模型本身造成。[E-STATUS/E-TAB-STRESS/X-TABICL-REGRESSOR]

## Hep8只消费，不补做

Hep8已固定2表示×2native方案×contextRNG44/45；fit/stop/stress分别591/86/171与593/85/170；只用fit上下文，不查询stop或官方Valid/test。四组旧FullMSE均值是CheMcanonical0.4994427193、Minicanonical0.5335681171、CheMscaffold0.5536630469、Miniscaffold0.5084056566；四组rank均值另列，不拿rank均值冒充MLP基准。[E-STATUS]

若MiniTabICL在两native都救回相对旧MiniMLP，读出限制解释增强，不能自动启动N8；若只有CheM改善或都没有改善，通用TabICL救回假说不成立；若跨scheme反转，保留条件化配方；运行失败则只有运行结论。任何分支均不追加Hepcontext、seed或内部ensemble设置。

**N8的自动触发应取消。** 一个subset与fullfit的对比至多给该抽样方式下的有限差分；它同时改变样本量与组成，不是一条学习曲线，也不隔离化学覆盖。真正决定标签/上下文预算时才有理由预登记同一fit池的三个嵌套规模、固定stress和独立组成对照。这是储备研究，不是本轮隐含训练数组，也不能为了有事做把它转为无界格点。[E-STATUS/P003-NEXT_EXPERIMENTS]

Sol四上下文分支是具体但条件性的另一问题：MiniSol的优势是否在冻结读出切换后仍保留，或者是读出交互。它复用3531/505/1009的既有scaffold分区和既有两个表示缓存，精确锁定TabICLv2 regressor。新Sol adapter与显式kwargs要准备，不冒称当前所有旧context运行过完全相同的配置；不查stop、不做外部第二次逆变换、不给fullcontext失败悄悄缩成子集的权限。

<a id="q4"></a>

# Q4：容量、成员机制、窗口与T2

## M5/M6不能被概括为“大模型好”

M5的plain三层MLP、TabM k1、k8与旧k32已真实比较；M6给出CheM128/Mini512近参数预算对照。各新值及原run选择器均保存在`accepted_aggregate_evidence.json`，不是把旧计划当结果。[E-RUNS/E-CAP-CACO/E-CAP-MICRO/E-CAP-SOL/E-CAP-CYP]

| task / 配置 | seed46 | seed47 | 指标方向 |
|---|---:|---:|---|
| Caco plain3 | 0.363163136566 | 0.339460699129 | MAE↓ |
| Caco k1 | 0.355286614971 | 0.352767611881 | MAE↓ |
| Caco k8 | 0.352074604592 | 0.331549877217 | MAE↓ |
| Micro plain3 | 0.469075767170 | 0.576534372250 | Spearman↑ |
| Micro k1 | 0.489363328937 | 0.547673479757 | Spearman↑ |
| Micro k8 | 0.585912835169 | 0.554574612848 | Spearman↑ |
| Micro CheM128 | 0.548568096491 | 0.496526589063 | Spearman↑ |
| Micro Mini512 | 0.569425320405 | 0.489310243298 | Spearman↑ |
| Sol CheM128 | 1.360991313155 | 1.636409720626 | MAE↓ |
| Sol Mini512 | 1.087303112579 | 1.087426714811 | MAE↓ |
| CYP plain3 | 0.750382052074 | 0.755657704562 | AP↑ |
| CYP k1 | 0.738610272169 | 0.744776040551 | AP↑ |
| CYP k8 | 0.758861608576 | 0.761028474190 | AP↑ |
| CYP旧k32（只复用） | 0.765440245834 | 0.765163681433 | AP↑ |

CYP中k1弱于plain，而k8胜k1、旧k32再胜k8；这支持当前任务的成员因素，不支持“只要换TabM就好”。micro旧k32相对k8两个seed均负，M6 Mini512−CheM128一正一负；Caco也有方向混合。Sol两个近预算对照则都保留Mini优势。这些完整反例共同排除了统一的单调容量解释。[E-CAP-CYP/E-CAP-MICRO/E-CAP-CACO/E-CAP-SOL]

对于单隐层D→H→1且含bias的MLP，参数量为`H(D+2)+1`。CheM2048/H128为262401，Mini512/H512为263169；这是根据登记架构的**新算术检查**，不是模型加载所得。近预算仍不等于相同函数类：隐藏宽度、输入几何和特征信息不同。Sol结果削弱“Mini只是头参数更多”的解释，却不单独证明Mini表示的生化因果优势。

TabM的成员共享主体权重，成员相关的缩放/初始化因子与计算轴提供多个预测；k32不是32个独立训练网络，也不是32个独立数据集。k改变可增加成员特定因子和计算/预测多样性，但共享大矩阵容量、优化耦合、dropout与初始化都需区别。k1与plain仍不一定是同一初始化和乘性结构，所以不能拿k1−plain当纯容量差。[X-TABM-README/X-TABM-PAPER]

## T2：固定初始状态的目标对照已经在途

已派T2只改训练目标，保持Mini512/H0、TabMk32三块512、drop0.1、同初始tensor、同shuffle policy、AdamW5e-4/wd1e-4/batch128、50/8和平均sigmoid输出。原scaffold9191是总行数，不是seed；fit6427/stop920/stress1844。两旧AP为0.7688841197331191和0.773429274836159，直接复用，不做旧forward或评分。[E-STATUS]

令成员给正确类别概率为q_k。凸性只给出

`−log(mean_k q_k) ≤ mean_k[−log q_k]`。

这是**同一成员概率集合**上的数值loss关系；训练后两目标产生的概率集合并不相同，AP又依赖样本间排序。mean-prob目标可允许强成员补偿弱成员，既可能提升集成排序，也可能弱化每个成员的约束；mean-member目标则要求各成员都解释标签。不能用Jensen直接推出AP提高，不能把T2结果解释成独立成员个数最优。

T2结果的约定已足够：两seed均正保留该固定scaffold目标候选；均负则否决；混合或同分保持范围；运行失败只有运行结论。新T2 seed、k和loss权重都不在本轮矩阵。旧permutation观察可能未记录，本轮不追溯伪造“见过旧batch trace”。[E-STATUS/E-T2-PREP/E-LATE]

## Window12及CYP3A4lr8的实质信息

Caco四条物理轨迹各有50/8、200/8、full200三个view；CYP八条也是如此。36个view不等于36次学习。两任务的200/8都与50/8相同，full200没有新增改善：Caco三差一同；CYP三差五同。Caco某full200所选epoch46仍在50以内，说明patience提前结束和epoch上限是不同机制，不能只用“50轮太短”解释所有现象。[E-WINDOW-CACO/E-WINDOW-CYP/E-RUNS]

CYP3A4 Veith H0低lr1e-4相对5e-4的四native AP原件增量分别为canonical44 +0.003777370593、canonical45 +0.003113419016、scaffold44 +0.023578665627、scaffold45 +0.007519869928。两个stress集有重叠，四个数不构成四独立证据集。它们足以为当前配方选择低lr提供支持，不足以推论所有端点或新表示都应使用该lr。[E-LR]

因此，本轮不再增加宽度/k/epoch/patience/lr矩阵。已有M5/M6和窗口结果是对先前假说的真正实验回答；不能继续把它们写成“需要准备”。可能尚有优化现象不代表每个未试数值都值得试。只有新目标或新表示引入了会改变决策的动力学假说，才另立有限对照。

<a id="q5"></a>

# Q5：固定群、共同错误和安全的下一份证据

## 已建立与尚未建立的盲区判断

原固定群以46/47的无标签预测分歧发现；后续44/45以及这次新的群汇总仍是回顾性研究，不变成未经选择的独立Valid。完整cohort ID、成员引用/hash和适用范围在`cohort_register.json`保留，但不复制成员行号/SMILES/答案。固定群96个潜在score cells中88可报、8被抑制；Caco n10及clearance n12的其他候选小群没有error score。抑制不是0错误。[H-COHORT/H-COHORT-SUM/P003-COHORT_REGISTER]

已有变化不是全好：PPBR高群四seed改善，低群46/47反而退化；Sol高群大幅改善，低群改善较小；LD50低群混合；lipophilicity高低群均有正负；CYP高群改善而低群8项受类别门槛抑制。因此，whole metric提高不等于所有固定群改善，更不等于原模型共识区已修复。[H-COHORT]

D/L提供了不同信息。对同一原Y尺度、相同行/权重的两组回归预测a、b，已有汇总定义

`L = (MAE(a,y)+MAE(b,y)−mean|a−b|)/2`。

源摘要已记录32个正L；本轮不重新计算。例子：Sol低群seed46的D约0.162348、L约0.611828；seed47的D约0.155632、L约0.608463。LD50低群seed46的D约0.023962、L约0.612918；高度一致显然不保证接近真值。PPBR低群44的L约3.954843。这些数值属于特定原配方对与固定组，不是“所有模型共同错误”的诊断。[E-DL]

## 一个可复查的新推论：区间距离，而非任意集成不可能

逐行定义`l_i=(|a_i−y_i|+|b_i−y_i|−|a_i−b_i|)/2`。若y在a,b之间，两条到y的距离之和恰等于端点距离，因此l_i=0；若y在区间外，较近端点距y的距离被计算两次，减半后即为到区间的距离。于是

`l_i = dist(y_i,[min(a_i,b_i),max(a_i,b_i)])`。

对任何`w_i∈[0,1]`，`w_i a_i+(1−w_i)b_i`都位于这个区间，所以其逐点绝对误差至少为l_i，取相同权重平均后至少为L。**L因此约束这同一对标量预测的任何逐点凸组合**，包括固定全局权重；它也下界于两端点的标签感知oracle选择误差。

这是一个严格但窄的结论。它**不**约束任意混合：外推权重、非线性校准、第三个模型、不同输出尺度/成员集都可超出该区间。逻辑例子y=0、a=1、b=2时L=1，但外推`2a−b=0`可无误差；而y=0、a=−1、b=1时L=0，两个端点oracle仍有误差1。例子不是任务样本，也不是新任务metric计算。

正aggregate L意味着某些正权重行的真值在这对预测区间外，因而存在两预测共同的同方向误差；但不能指出是哪一行、错误比例、哪个化学子群、所有行均错、或错误来自何种机制。没有逐行误差上界，甚至无法用aggregate L给错误行比例一个非平凡下界。这个数学推论的独立核验是上述区间分情况证明和凸组合包含性，而不是“多个Agent都同意”。[E-DL为公式输入，区间证明为本轮新推导]

## 具体可批准的群级前后证据：0新学习，最多12新群指标

**GQ-SOL**：复用已经完成的M6 CheM128/Mini512、seed46/47四个预测，在原Sol high294和low294两个群上取8个MAE；before复用原同群CheM256/Mini256指标，不重算。它回答“近参数预算下的Mini收益是否仍在原低分歧群出现”，而不回答某分子已经修复。读出宽度改变依旧是配方对比，不强行称纯表示因果。

**GQ-CYP**：复用已完成TabICL的CheM/Mini、contextRNG44/45四个预测，在原CYP high132群取4个本地AP。before用既有该群CheM/Mini TabM指标（不假称该群已有MLP分数）；不同RNG与模型seed的mean描述不能伪装同初始化对照。CYP低群继续抑制，不请求类别计数、重划组、leave-one-out或差分来绕过。[E-CAP-SOL/E-RUNS/E-TAB-RAW/H-COHORT]

具体issue/cohort/oldrun/新增证据请求的联接在`cohort_evidence_requests.json`。GQ是未来主控私有固定评分器的另行授权请求，不在训练数组内；本Chat没有执行任何评分。输出只允许任务、群、模型ID、metric、可披露n、聚合值、source/hash和suppressed状态。连续群n≥20、分类另每类≥5沿用既有安全门槛，这不是统计置信阈值。

这些群目前是**模型分歧定义的群**，不能重命名为已知某化学机制盲区。为了让解释更具体，可在同一固定大群上另给不带标签的描述性概况：既有RDKit/Morgan接口计算的分子量、重原子数/环数/电荷的粗分布，以及到原train-fit的相似度分位数。仅报告整个既有群的安全聚合，禁止以小化学交集再带出标签/残差或行身份。没有这些摘要时，极性、大小、带电或骨架家族等原因只能列未知，不能凭分数猜测。此描述请求不新增模型推理/学习；本轮也未计算这些描述。

<a id="q6"></a>

# Q6：新的冻结表示，先区分候选、接口、producer和疗效

## MoLFormer：关闭当前固定配方扩张，不否定所有序列表示

16头在四任务的32个主比中只有3正29负；Caco、micro和CYP主比均负，DILI为3胜5负。CYP内部MoL TabM胜MoL MLP并不能抵消它相对CheM/Mini的主比负。两种结论必须并列，不能用“换头有用”覆盖底座配方落后。[E-MOL-CYP/E-MOL-CACO/E-MOL-DILI/E-TASKS]

对应的是`ibm-research/MoLFormer-XL-both-10pct`，revision `361063d0ad524ef77cf39b08469f6be770dc550f`，登记权重SHA `0795977fe7192c4acdaf052f0e8464af57bc4bb59211271c5e61aaba2637b9c6`，768维当前pooling；不是任意“大MoLFormer”。官方卡为Apache-2.0且有SMILES预处理/长度背景；本项目过长输入的零填处理保留原行，却也是实际配方的一部分。不能在未做新完整输入策略时把负结果扩大到所有长分子、所有序列预训练或任意checkpoint；当前也没有足够信息价值去再跑同panel seed或池化格点。[X-MOL-CARD/P003-SCIENTIFIC_ASSETS]

## 两个几何checkpoint的具体性和互补假说

| 科学对象 | 固定资产 | 输出/用途 | 当前状态 |
|---|---|---|---|
| Monroe | code `de075eabe98e4adbbedbc86ca9e877f4bfd9b629`；checkpoint/weights.pt SHA `df996e8e98b12a3cda5fe5acbef3e1e9a4ea31946d3736461cd07e53a5bf205a`，300057823 bytes | 原发表encoder pooling 720维，保留原virtual-node设置；不使用TabPFN | 旧5cache不准入；未来producer协议尚未接受 |
| UniMol2-84M | code `90f52c41299a1a582da0f9765e9f87aa21faa16a`；HF `dptech/Uni-Mol2` rev `bf37d253c0f5ac61f468137eb00059978a104ff0`；84M/checkpoint.pt SHA `5b9241630f1cf0b173fb06d1e76096e5daf5f91c3e51b066ba69524dafe60e35`，336632021 bytes | `return_repr=True`的CLS768，绕过任务classifier，不是论文最大1.1B | 旧9cache不准入；v4仅静态协议通过 |

Monroe的PM6、PCBA与去噪预训练可提供与当前2D表示不同的归纳偏置，但这并不是“纯几何因子”。原论文/仓库的任务收益不证明本项目疗效，也不能把其cleaning、额外样本或默认TabPFN流程移植过来。Monroe代码MIT不等于自动接受TabPFN受控条款；本方案明确排除TabPFN加载或拟合。[X-MONROE-PAPER/X-MONROE-README/X-MONROE-LICENSE]

Uni-Mol2的几何预训练和CLS路径是另一个互补候选；固定84M checkpoint与最大模型家族不同。官方MIT源码与固定模型卡已核，具体生产仍需逐模型来源和依赖notice准入。高层`UniMolRepr`的kwargs传播、默认128 heavy-atom crop、`atoms+coords`丢bond信息、invalid输入、默认多进程、pair维度内存等都会影响真实接口。新producer必须走已接受v4的显式无crop/种子/数据路径，而不能只在调用处写一个未传播的参数。[X-UNI-PAPER/X-UNI-README/X-UNI-PREDICTOR/X-UNI-CARD/X-UNI-LICENSE]

## 原producer证据不能由后来的模型补签

原准备事实：Uni与Monroe各12次encoder attempt；head forward分别capacity7、Uni2、Monroe9，共18，虽未超过全局24，却超过Monroe自己的4次额度5次。learning/backward为0，不能当作训练疗效。实际越界写/随后移动、早期import/weight-pin失败、原PID被找回等修正应保存；找到tail不等于完整stdout/stderr，重建后来模型hash不等于原RunA/B before/after。它们是运行合规和证据问题，不是几何科学效果负例。[E-GEOM/E-MONROE-FAIL]

Uni v4静态检查验证了16个adapter/diff对象并继承24个upstream来源，40文件manifest为`66cb65a94d9dab2e7fabbf8aeace7efaaad86ebe8460c421f2023d9d08d019a8`；原producer缺证和old9不准入没有因此消失。Monroe未来协议尚未接受，更不能把准备完成升级为full-task encoding。未来必须重新批准一个freshproducer，不改写旧产物状态、不重置已耗预算。[E-UNI-V4/E-GEOM]

必须取得的门槛是：调用前后完整参数及**全部buffers**、model.eval/no梯度、完整原行和重复输入保留、固定geometry seed42及原有20s全流程超时/fallback定义、具体氢/坐标/构象/pooling配置、输入失败处理、没有默认crop、严格加载encoder key、缓存source/schema/row_index、重载输出一致。旧缓存不满足，不能用后来冻结证明搭桥。Monroe的BN、virtual-node原点距离、图就地修改、SMILES字典去重和RRWP16的平方成本各需fixture；Uni的CLS/无任务头接口和大分子内存同理。

## 有界G8仍保留原身份

原P003-G8只是条件建议，尚未学习；本轮沿用相同四个proposal ID：Sol/micro × Monroe/UniMol2 × seed44/45，共8新梯度fit。只用既有scaffold划分、MLP256、H0、标准化Y的MSE、50/8，Sol stop MAE最小化、micro stop Spearman最大化，原Y一次逆变换。两seed共享每任务/encoder完整train缓存；4个编码pass，不生成Valid/test几何缓存。[P003-NEXT_EXPERIMENTS；本轮next_experiments.json]

它能判别“固定几何预训练配方是否带来可改变表示选择的收益”，不能只归因3D：checkpoint来源、预训练监督、维度、尺度和第一层参数量均不同。若两个任务都无可行动收益，关闭这两个固定checkpoint配方，不立刻追geometry seed、pooling或更大模型。若某任务正，限定为其配方与划分范围，后续确认另需新问题。没有fullcoverage/freeze的资产不得进入头训练。

本轮没有为KPGT、SMI-TED、MolE或另一未版本化家族制造新矩阵。它们在历史资产清单中保留“已调研/未准备”的真实位置；已经有的简单头、TabM和95复合分数也不是未试方向。研究广度应该来自不同可反证的解释，而不是每轮再列几个模型家族名。

<a id="q7"></a>

# Q7：确定矩阵、预算和收口

## 分批上限由判别结构推导

| 档位 | 确定内容 | 新梯度fit | 新冻结上下文fit | 新完整编码pass | 复用旧控制fit（唯一） |
|---|---|---:|---:|---:|---:|
| 小档 | H1：CheM/scaffold与Mini/canonical，各gap/uniform×44/45 | 8 | 0 | 0 | 8 |
| 中档（建议上限） | H1+有条件H2补齐另两细胞；有条件Sol四上下文 | 16 | 4 | 0 | 20 |
| 大档 | 中档+原G8，freshproducer通过前blocked | 24 | 4 | 4 | 24 |

中档不是一次默认发满20个身份；先8个H1，随后分别判断H2和S的信息价值。大档28个fit身份中只有24是梯度头，4是context，8个几何梯度头受资产门槛阻断。旧控制24个仅共享一次，不算新训练。T2的2gradient和Hep8的8context已有派发预算，不在表中；GQ最多12个新固定群指标是0fit的独立评分请求，不能偷偷并入“0新增Valid分析”。本轮学习矩阵为0新增wholeValid评分；群请求仍是事后Valid分析，需单独批准。

14个proposal每条严格一个task、一个完整配置、一个split，seed数组[44,45]角色明确。已有G8保留旧ID；其他新ID与已完成dense-rank、HalfMSE、原Tab32、活跃Hep8及T2均不相同。所有预处理每split只fit本fit行；stop用于早停，不参与统计；stress只在锁定完整对照后一次评价。新代码门槛在guide/conditional_followups，不伪装训练项。

## 成本：不能拿数秒头训练代替完整周转

已验R44的44头互不重叠训练组时长之和为128.12134457891807秒（原件注明初始失败/支持开销尚未并成最终预算总数）；nativeTab16 GPU作业388.54210678162053秒，MicroTab8为185.081285秒。它们不是纯kernel、训练角色全部活跃时间或准备/交接总时长。[E-RANK-ALL/E-TAB-STRESS/E-TAB-MICRO]

小档8头的线性类比基数是`8×128.1213446/44≈23.3秒`，**不是预测完成时间**：新的pair哈希排序可能压过小头算子，q的全fit间隔也有一次准备成本。预算文件给3倍和10倍基数的敏感性情景，不称置信区间或上限。实施fixture、父配置/初始tensor绑定、导出、私有评分、取回和主控交接必须另记。首批内测量，不为每个小头再加“试跑”fit。

Sol fit3531远大于Micro532/539，且显式无AMP、CPU offload与KV cache设置不一定等于旧作业。上下文成本不能简单按4/8乘Micro时间；若资源限额不够应停，不静默子采样或改变精度后冒充同配置。具体CPU/RAM/VRAM/时间上限由主控在执行登记时决定，当前Hep8的1800秒GPU预算不是Sol的许可。

几何4pass需保留Sol5045行、Micro770行，在两个encoder上共11630行次；这是分区计数的派生算术，不是已发生编码。构象失败/fallback、原子数分布、RRWP或pair-square内存可能主导成本，因此不编GPU小时。全流程时间应按关键路径和重叠区间合并：准备＋学习/上下文/编码/导出/评分/运输的关键路径＋交接/研究；不能把重叠角色时间直接相加。旧6815秒准备至取回、4169秒Pro等观察仅保留为历史，不当本轮固定常数。[P003-BUDGET_SCENARIOS]

## 继续、停止、跳过及下一次研究节点

- H1没有可改变决策的gap-v-uniform区别则关闭，不补q/seed；有区别且需要区分表示/划分才解锁H2。所有符号保留，没有用新的“最优seed”代替差异。
- Hep8/T2按原登记分支消费。Hep读出救回不自动证明样本支持问题；T2较低loss不自动证明AP。两者失败时保留真实失败，不借改loss权重重启。
- Sol四context只有在Hep8后读出迁移会改变资源分配时才做；结束后不扫内部集成参数。全context资源失败是该固定接口失败，不擅改任务。
- freshgeometry任何关键producer/coverage/freeze门槛失败只阻断该asset；其他已准入研究继续。已排队几何准备不等于G8已执行，旧拒绝cache不能复用。
- 固定群补证保持原成员hash和抑制策略；不能因为低群无结果而改组。从L到行级化学诊断需要新的获准证据，不能推测填满。

正常在完整预登记对照块收齐后深评审。冻结/标签/行身份的实质故障，或者足以推翻关键前提的反证，可以提前回主控；不按每个头、固定分钟或队列是否空触发。科研的收口标准是“当前可检验问题在预算内已经区分到足以行动”，不是批次结束或某方法碰巧有一个最佳数值。

# 实际阅读、继承验收与缺口

## 已亲读的核心与新证据

核心入口、CURRENT、late amendment、decision-contract、实验纲领、Skill3.4.1、policy/reuse、history branch和reading contract已读。新结果中，R44三任务所有主/次比较、Tab原16和native16的全部主要数值、M5/M6原run数值和更新、窗口/低lr、AMES8views、D/L决策及有代表性的完整行、几何三份准入/纠错原文均实际阅读。D/L其余行继承原摘要“32正”的验收，不冒称逐行复算。

固定群comparison原文进一步补齐了AMES/PPBR/Sol/CYP的原cohort ID和GQ既有run绑定；旧P003-pointer保留为别名历史。当前完整实验账、source-map和proposal账用于定位/定向下钻；不将总行数当读完行数。旧003的22文本原件可从本轮prior-pro003和原ZIP枚举，已读取字节/解析并按问题审查相关字段；静态脚本只读、不运行。旧历史叶子中与本轮新增决定无关的对象不重审；具体范围在evidence_registry和review中逐项写明。

## 缺口逐类，而不是统一“材料不可达”

1. **真实未记录/不可补签**：旧几何原producer全部参数buffer before/after、部分完整流和RunA原vectors等没有完整原证据；后来重新加载不能恢复原时刻。只阻断旧cache准入。[E-MONROE-FAIL]
2. **已发布但本轮未逐项读完**：大实验账/issue/proposal/source索引的非相关条目，D/L全部32细行、部分历史bulk源对象。仍可导航；不称不存在，不作为新增因果结论依据。
3. **reference-only、未在当前公开投影重发**：例如Hep原intake的`ref-bd3ae1fd72145679`在SOURCE_MAP中无packet path或继承URL。当前R44Hep结果仍可读，缺口只影响原intake细节的进一步复核，不否定聚合质量。[E-SOURCEMAP]
4. **实际读取路线失败**：运行环境直接requests对rawgithub出现NameResolutionError，download失败，固定IP curl退出7；web读取同一类公开原件成功，故不是原件不可达。TabICL固定HF card的raw/blob两条精确URL返回InternalError；固定代码/LICENSE和已接受项目checkpoint回执仍可用，不声称权重不存在。
5. **准入数据将来可计算**：pair-gap fit统计、已有预测固定群汇总、无标签群描述可在授权角色中按方案产生；本轮没有计算这些任务数据。
6. **需未来实验**：H1/H2的配对选择效应、Sol上下文可迁移性、fresh geometry疗效。未来未知是科学限制，不因报告长短变成既成结果。
7. **在途**：T2与Hep8真实新结果未知；不需要等待它们才能完成其他问题分析，条件分支已经给出。

没有伪造subagent。本轮用户明确禁止派Agent，交叉核验由同一研究者对原数值矩阵、状态/claim链、官方接口代码，以及对新计数/数学推论的独立计算路径进行；“多份摘要同意”不被当作独立实验复制。完整来源、限定范围、反例和对决策的影响共同决定科学可信性，文件校验只证明运输完整性。
