# ADMET 独立科学研究：从已验证配方到可判别机制与范围收口

**request_id：admet-pro-next-research-20261102-002**  
**固定输入commit：f65d8149a897ea1db64c6f7cb16e52e06987229a**  
**输入manifest SHA256：1fce919c9e7c6ee47ff7572446723966c83056c197a65283d0ee4790a38bae91**  
**快照截止：2026-11-02T15:55:34.713393+00:00**  
**科学状态：needs_evidence；本轮仅研究，无训练、模型加载、编码/推理、安装、Agent派发或额外发布。**

本文中的 `[E-…]`、`[X-…]` 均解析到 `evidence_registry.json` 的真实来源、精确URI、登记版本、可见原文行数和实际阅读范围。数值引用已验聚合，不重新计算既有质量指标。新代数与去重见 `derived_checks.json`。六主体文件是研究正文，不以ZIP包装替代科学证据。

## 0. 直接结论与本轮边界

第一，当前最可靠的资产已经不止CheMeleon。MiniMol、Morgan及TabM都有真实学习、评分与正反例；“MiniMol仍被旧setup.py 404阻断”“其他16任务未接入”是旧状态，不能再作为本轮事实。另一方面，TabICLv2只有固定代码/许可与本轮进一步查到的具体checkpoint元数据，Monroe只有源码/config/LFS pointer，MoLFormer10pct还没有本项目可接受的payload/冻结/全行覆盖路径。研究过、可下载、生产接口支持、真实训练、科学改善是五种不同状态。[E-ASSETS、E-NEW、E-FACTORIAL]

第二，多个四seed确认已足以停止重复确认同一配方：AMES Morgan、Sol MiniMLP、microsome MiniMLP、CYP2D6 Veith MiniTabM均应保留其**指定任务、指定数据/划分、指定头和预算**的收益。PPBR只有3/4；DILI的负迁移、micro换TabM的负结果、Bio的Mini/Morgan双负、半衰期低lr反转仍有效。不能为了追求“全部正向”再加seed，也不能把没有新队列当作研究完成。[E-UAMES、E-UMMSOL、E-U14、E-U54、E-FACTORIAL]

第三，最有价值的下一步是**互补判别**，不是再派一次48。已派48是12完整配方×canonical/scaffold×modelseed44/45，主要判别整个配方在新的train内分组压力下是否保持排序。它不单独分离表示、floor、头参数量、成员机制或stop选择。本文首层22个新梯度fit依次针对：半衰期rank目标与尺度、MiniMol内floor、AMES同轨迹双stop选择、Caco训练窗口。中档60个新梯度fit再加容量/成员、近似参数量匹配、加权BCE尺度及低lr×窗口。大档是70个梯度fit加4个冻结上下文fit，共74个新监督fit身份，含14个资产受阻身份，绝不是74项可立即训练。[E-48、E-RANK4；next_experiments.json]

第四，建议采用**中档作为分批上限**，按模块结果提前收口，不是一次授权60项。当前小档22项均需新增科学接口/受控日志准备；中档另外4项CheM128为已证明字段的config_only，其余新机制适配明确new_code。大档新增资产分支可并行做零学习准入工作，但不抢先训练。原ranking4被继承一次，不另起同科学身份副本；PPBR128已完成而未重复建议。[E-EXECUTION、E-RUNS、E-OLDGUIDE]

第五，盲区仍然是**可疑群而不是已知错误群**。保留所有固定高/低分歧入口；Sol的1009行train.stress不是2940行Valid。旧group20已经有20个原生stress分数，不能照抄嵌套旧字段继续称“待评分”。Valid固定群真实误差/改善尚未有本轮准入的安全汇总。小分组抑制不得变成通过多个差分问题恢复个体答案。[E-ISSUES、E-GROUP20、E-SOURCEMAP]

### 0.1 证据时钟与复用

本轮快照为586实际任务头、565逻辑run、556整体Valid分数、20 native train.stress数值和95复合分数；10历史未评分仍未知。头数、逻辑run数、评分次数、复合分数不能相互代换。48已派无结果，只按派发身份排除；不推测截止之后成功或失败。[E-START、E-MANIFEST、E-CONTRACT]

已验冻结、输入行序、评分和运输回执作为适用前提继承，不重新整批验收。BBB旧H0 seed46缺after的限制不会被新胜例追溯修复；本研究BBB新表示分支使用真实F001控制，不使用该缺证run。监督器退出码/worker业务失败/科学产物准入分别记账；未测不写通过。GLM、DeepSeek、Qwen、Sol、Terra、Astra是角色，不是科学底座。[E-ISSUES、E-RUNS、E-RULEMAP]

学习仅official train.Y。内部fit拟合所有统计，stop选择，压力分区在选择锁定后评分；外部预训练参数和buffers全部冻结。已见过的Valid不能因新会话、新split或新modelseed重新成为独立终评。官方允许Valid调参，不等于取消本地取回/私有真值边界；这里建议控制查看频率是研究设计，不提升为用户硬规则。约46的本地推断指标不是官方隐藏榜，官方AP/总公式与部分原Y单位仍有缺口。[E-RULES、E-RULEMAP、E-ISSUES]

## Q1. 全22任务：保留、否决、未解决与科学收口

下表的“停止”只终止被证据否决的任务×配方/机制分支，不主张该任务已全域最优。四seed确认是稳定性证据，不是四个独立数据集或统计显著性检验。表中Valid n及类别数沿用本轮可读的已验历史汇总，仅用于理解评价粒度；不以数据集总量替代Valid行数。[E-PROOLD、E-FRONTIER；task22_actions.json]

|任务与外部指标|Valid范围|保留/停止|关键未知与下一判别|有限范围收口标准|证据|
|---|---:|---|---|---|---|
|`ames`；AUROC ↑|1137；正479/负658|保留Morgan2048 identity+MLP四seed局部Valid优势；**停止/否决**：不接受内部stop最优等同Valid最优；不追加同split盲seed|四seed stop/Valid均反转，分布差与epoch选择偏差仍未分离；**下一步**：先消费已派48的canonical/scaffold，再M3同轨迹双stop选择检验|48和M3均完成后能限定适用划分与selector即收口本问题；非全域最优|E-AMES, E-UAMES, E-48|
|`bbb_martins`；AUROC ↑|203；正149/负54|保留有完整证据的F001参考；原H0-s46不得作为冻结完整控制；**停止/否决**：floor混合，不扫更密floor；不能补造旧after|新表示收益未知，旧after缺口只影响该run；**下一步**：M10用F001有效控制比较冻结MoLFormer/Monroe；资产未齐不开始|获得有效表示对照或资产依赖明确关闭即收口本分支；旧缺口独立保留|E-RUNS, E-FRONTIER, E-ASSETS|
|`bioavailability_ma`；AUROC ↑|64；正43/负21|暂留现有CheM候选及旧Mini22历史参考；**停止/否决**：MiniMol/Morgan当前MLP均双负；width128双负，不重复相同配方|小Valid与旧Mini22差距口径/早停原因尚不清；**下一步**：仅做现有fit/stop配置历史对齐和宽组无标签结构覆盖诊断；若缺表示而非优化才进储备D14|负配方停止；没有新可判别证据不添训练，不声称任务已最优|E-MORGAN, E-NEW, E-RUNS, E-FRONTIER|
|`caco2_wang`；MAE ↓|91|F010；Huber/drop0各3/4；TabM两seed相对其匹配MLP改善；**停止/否决**：不称TabM击败历史Huber；不可将触顶50等同已收敛|容量、成员与训练预算混杂；固定高低分歧群误差未知；**下一步**：M4 200epoch同轨迹策略比较；M5 plain深MLP/k1/k8；安全群汇总|预算/架构主效应与交互能定位后停止同因子搜索；未测群不标修复|E-FACTORIAL, E-U54, E-ISSUES|
|`clearance_hepatocyte_az`；Spearman ↑|122|CheM F010四seed方向支持；**停止/否决**：不把microsome的MiniMol结果直接外推|MiniMol在此任务未试；rank与MSE机制未知；**下一步**：M11一次MiniMol512 H0×46/47，缓存身份另准备；不盲全家族迁移|首组匹配表示负向则停该配方；同向再按预定条件检验分组，非追加seed凑一致|E-FRONTIER, E-U4, E-ASSETS|
|`clearance_microsome_az`；Spearman ↑|111|MiniMol H0 MLP同设备4/4；**停止/否决**：MiniMol TabM旧两seed退步，否定TabM普适升级|表示、floor与头参数量未拆开；低分歧不等于正确；**下一步**：消费48；M2 MiniF010；M5容量/成员；M6近似参数配平|配方分组适用范围+负头机制有界定位后收口；不要求消除全部不确定性|E-MMCYP, E-U14, E-FACTORIAL, E-48|
|`cyp2c9_substrate_carbonmangels`；AUPRC ↑|67；正12/负55|H0比较锚；保留canonical/scaffold反转证据；**停止/否决**：posBCE双负、Morgan双负；Mini混合，不靠再加seed改判|AP小阳性样本、加权loss尺度与结构迁移未分离；**下一步**：M7归一化原posBCE；已有group20反例不重复；安全宽组审查|归一化仍双负则停该加权配方；仅train-stress支持不足以推Valid可靠性|E-GROUP20, E-MORGAN, E-U140, E-U54|
|`cyp2c9_veith`；AUPRC ↑|1210；正406/负804|F010旧双seed小增益局部保留；**停止/否决**：不把微小平均增益当任务定案|新表示/TabM尚未真试，是否能迁移CYP2D6机制未知；**下一步**：待M5解释CYP2D6头增益后，D14有界MiniMLP/TabM配对扩面，不现在无条件开整组|若机制不迁移停止该配方；无新证据时保持当前而非扩大网格|E-FRONTIER, E-FACTORIAL|
|`cyp2d6_substrate_carbonmangels`；AUPRC ↑|67；正14/负53|F010+fit-posBCE四seed正向；**停止/否决**：不宣称概率校准变好或AP理论必升|类别权重与梯度尺度、分组泛化未识别；**下一步**：M7保留原w仅归一化平均loss；确认与负对照CYP2C9相反效应|规范化与原加权同向则保留规则，之后一次分组检验；不扫无限w|E-U140, E-U54, E-OLDGUIDE|
|`cyp2d6_veith`；AUPRC ↑|1313；正250/负1063|MiniTabM对CheMTabM4/4且同Mini对MLP4/4但增量较小；**停止/否决**：不把表示增益全部归因TabM|表示与头正则/成员仍混杂；共识盲区未知；**下一步**：消费48；M5 plain/k1/k8；M9固定TabICLv2分类checkpoint研究控制|如k1/plain足以解释不再加大k；表示稳定但头边际无实益则选较简单候选|E-MMCYP, E-U14, E-FACTORIAL, E-48|
|`cyp3a4_substrate_carbonmangels`；AUROC ↑|67；正36/负31|H0锚；已试floor/simpleheads历史继续有效；**停止/否决**：F010原双seed退步，不统一推广F010|少样本排序稳定性与新表示未试；**下一步**：无优先新fit；按D14单表示条件扩面，不沿CYP3A4 Veith低lr自动移植|已负floor配方收口；新的独立假设/资产才重新打开|E-FRONTIER, E-RUNS|
|`cyp3a4_veith`；AUPRC ↑|1233；正581/负652|lr1e-4在H0/F010各4/4；**停止/否决**：不把所有收益归因50epoch截断：存在非触顶正例|步幅、正则路径与候选epoch窗口交互未拆开；**下一步**：M8两floor×两lr×44/45固定200轨迹；同时虚拟50/8及200选择|低lr作用在等窗口保持则限域保留；若仅增加窗口有效则改变训练策略而非继续扫lr|E-CONF54, E-U54, E-U72|
|`dili`；AUROC ↑|48；正13/负35|F001对H0四seed局部支持；**停止/否决**：Mini/TabM无稳定改善；低lr可能很早停止；负结果不被Sol胜例覆盖|small stop/Valid排序与group交互；敏感群误差未知；**下一步**：消费48负迁移对照；M9固定TabICLv2小预算不同归纳偏置；不密扫TabM|新方法仍负则停该家族此任务；F001收口只限当前配方，不称化学盲区修复|E-U4, E-GROUP20, E-OPT72, E-FACTORIAL, E-48|
|`half_life_obach`；Spearman ↑|67|F001对H0四seed方向支持，绝对值含0.053需保留；**停止/否决**：F010低lr在新44/45反转；四成员平均不胜双成员|MSE/rank目标错配、种子敏感与有限stop；ranking4尚未执行；**下一步**：M1承接原ranking4并补0.5MSE尺度控制四项，复用fullMSE|ranking不能胜尺度控制则否决本pairwise配方；有益再单个分组测试，不无限lambda/seed|E-RANK4, E-U4, E-U54, E-ENS59|
|`herg`；AUROC ↑|66；正42/负24|现有H0/F010作为局部锚；**停止/否决**：floor混合，停止同因子密扫|新表示覆盖与小Valid可靠性未知；**下一步**：M10冻结Monroe/MoLFormer各46/47，对照已验H0；化学群仅可疑|两种表征均负则暂停新底座此任务，不能把小Valid置信当成功|E-FRONTIER, E-RUNS, E-ASSETS|
|`hia_hou`；AUROC ↑|58；正48/负10|affine对普通MLP两floor各4/4，F010对drop0也4/4；**停止/否决**：不自动加宽/加深；H0对drop0一平局保留|小Valid仅10阴性；线性方向可能已足够，不代表全线性已优化；**下一步**：保留简单头；D13只在收敛诊断显示AdamW affine未到达时考虑凸解研究对照|现有有限问题可收口为保留affine；无新增判别需求不训练|E-U140, E-U54|
|`ld50_zhu`；MAE ↓|1937|F010和Huber对MSE四seed正向；**停止/否决**：整体改善不等于194个高分歧分子的错误被修复|Huber鲁棒性与0.5局部MSE尺度混杂；共识风险；**下一步**：先请求合规固定高/低组汇总；D12条件0.5MSE/MAE差异分解，复用既有Huber|若群证据充分可关闭特定盲区；缺群误差则只收口整体配方结论|E-U54, E-ISSUES, E-OLDGUIDE|
|`lipophilicity_astrazeneca`；MAE ↓|420|保留F010，Huber作为3/4有条件候选；**停止/否决**：seed45反例不删；不宣称Huber统一改善|敏感42行与低分歧群误差均未知；**下一步**：先固定群安全汇总；D12有界损失尺度分解，不添盲seed|Huber若未对同群稳定改善则不称修复，保留MSE候选|E-U54, E-ISSUES|
|`pgp_broccatelli`；AUROC ↑|122；正61/负61|现有CheM锚；近似同排序本身是信息；**停止/否决**：floor预测rank相关约0.995，不再密扫floor|高共识是否共同漏掉特定化学空间未知；**下一步**：优先无标签覆盖/固定宽群，不把低分歧当安全；新表示按D14明确触发才开|现有scale方向可收口；共识风险只能待合规误差汇总，不编造改善|E-PROOLD, E-FRONTIER, E-ISSUES|
|`ppbr_az`；MAE ↓|279|CheM F010相对H0大幅改善；Mini3/4暂保留；**停止/否决**：Mini seed46同设备反例；width128已完成不得重复|Mini与CheM的feature单位、参数量、目标位置估计混杂；**下一步**：消费48；M2 MiniF010；M9TabICL回归固定median输出|Mini若group反转则限域保留或退回CheM；严禁以追加seed补齐4/4|E-MMSOL, E-UMMSOL, E-RUNS, E-48|
|`solubility_aqsoldb`；MAE ↓|2940|MiniH0MLP同设备四seed显著量级改善；**停止/否决**：不跨旧/新CheM seed47控制混算；不把1009 train.stress当2940Valid|表示信息、维度/容量、缩放贡献未分离；固定群无误差结论；**下一步**：消费48；M2 MiniF010；M6近似参数配平；保留原4/4|结构stress和参数/尺度排除完成后给限域默认，不称全22通用底座|E-MMSOL, E-UMMSOL, E-GROUP20, E-48|
|`vdss_lombardo`；Spearman ↑|113|H0低lr3/4有条件保留；既有均值ensemble参考；**停止/否决**：F010混合，不统一套半衰期ranking|MSE/rank、优化和种子适配不清；**下一步**：仅当M1能胜尺度控制，D12一次VDss迁移；否则不复制失败ranking配方|该配方迁移负向即停，不以任务未最优为由无限扫参|E-U54, E-ENS59, E-FRONTIER|

### Q1支持与反对证据的层次

不能把“全部任务有分数”当作研究完成，也不能反过来要求22任务每项不断加新fit。HIA已经有相当明确的简单头证据，当前可收口为保留affine；Bio/Morgan/Mini的失败配方可停止；Pgp密扫floor信息量低，应转向共识盲区验证，而不是维持队列；CYP2C9 Veith/BBB/hERG仍缺独立表示覆盖，可以给有界新方法而非自动全22替换。这样的行动类别差异才体现了全任务覆盖。[E-FRONTIER、E-U54、E-MORGAN]

已否决的是“当前具体学习配方”，不是整个方法族。例如affine38个配对只7优31差，但HIA特异受益；有限50epoch的AdamW affine不等于所有正则线性求解器已经充分求解。Mini在Bio负向，也不能否决其在Sol/microsome已有明确收益。反之，Sol收益再大也不覆盖PPBR seed46或DILI反例。[E-U140、E-U54、E-UMMSOL]

**本问题直接答案**：22任务分别给出了可保留的局部结论、停止的配方及可重开的具体条件；没有证据要求统一模型或统一损失，也没有证据支持全域最优。适用条件是上述真实版本、行身份、split和已验评分有效。剩余未知主要是未来机制/压力验证，而不是重复评分所能解决。

## Q2. 独立解释最新正反结果，以及48能与不能回答什么

### 2.1 AMES：stop/Valid排序反转不是应忽略的“验证噪声”

AMES四共同seed44–47的Morgan相对CheM Valid AUROC增量约为+0.009918、+0.030804、+0.010248、+0.016241；四个内部stop却都由CheM胜出。两者同为2048维输入和256宽MLP（524801头参数），同设备同数据/划分比较排除了“只是维度较小/头参数较少”这类解释；但Morgan identity与CheM H0预处理不同，不能把差异归为纯表征信息。[E-AMES、E-UAMES]

竞争解释至少有三种：第一，raw字符串group-stop与官方Valid化学分布不同，表示排序确实随分布变化；第二，stop有限且反复挑epoch，使模型选择偏差/噪声不同，较高stop不意味着较高Valid；第三，Morgan位输入与稀疏冻结特征的缩放、优化轨迹和隐式正则不同。四seed重复方向削弱“仅某个seed偶然”的解释，但四seed共享同一stop/Valid，不能当作四次独立反证，也不能凭其断定官方划分泄漏。

已派48用两类分组train.stress检验配方迁移，能说明某些结构划分下排序是否稳定，却不能在相同学习轨迹上隔离选择器。本轮M3新增两个表示×44/45，共4条固定50epoch轨迹。新的canonical四路分配为fit70%、stopA10%、stopB10%、final stress10%；同一权重轨迹分别由A/B独立选择epoch，最终stress在两个选择都锁定后读取。这样比较selector时保持训练数据和权重候选不变；8个最终checkpoint输出仍仅4个fit。两表示比较仍是bundle，且新fit行集与历史raw不同，不能把M3与历史差值冒称纯selector效应。[E-48；P-M3-*]

判别：若A/B选择导致stress排序变化而表示跨分区相对稳定，选择偏差有支持；若同轨迹选择稳定但canonical/scaffold之间变号，分布交互更可疑；二者可共存。若所有新的分组验证支持Morgan，则保留这个局部默认，同时明确反转并未证明单一化学机制。此时停止再加raw种子有科学依据。

### 2.2 MiniMol：清楚的收益与不能省略的混杂

Sol同设备四seed控制中的CheM MAE约1.409417、1.524624、1.473621、1.449465，对应Mini约1.066396、1.088217、1.071334、1.068881。最后一个CheM控制是本次匹配对象，不能拿旧86批的不同控制值1.565136代替。Microsome的MiniMLP四seed Spearman增量约+0.062817、+0.049209、+0.104498、+0.126679；但同Mini换成TabM在旧46/47反而下降。CYP2D6 Veith的MiniTabM相对CheMTabM四seedAP增量约+0.047525、+0.061019、+0.054014、+0.074885，而同Mini TabM对MLP的增量只有约+0.000693、+0.006175、+0.006857、+0.012386。相对收益主要出现在整个表示配方的改变上，不能都归功于TabM。[E-MMSOL、E-MMCYP、E-U14]

这些比较同时改变了表示来源（2048→512）、feature分布与floor（CheM F010→Mini H0），以及头参数量（524801→131585）；保持隐藏宽度256不等于保持参数容量。Mini的收益可以来自更有用的信息、更温和的尺度、更适宜的容量/正则，或多者组合。仅增加seed不能拆解这些解释。

M2在同一个Mini缓存和同一头上只改变floor，三任务PPBR/Sol/microsome×46/47，共6fit。0.01是Mini单位下的干预，不宣称与CheM单位相同。零fit统计先记录触发floor的维度数、非零比例、分母分布与stop/Valid无标签极值；若两个变换完全相同则跳过等价训练，不临时加大floor。

M6在Sol/microsome进一步比较CheM128F010与Mini512F010。头参数分别262401和263169，差768（约0.293%），远比同hidden256的4倍差距小；Mini256F010共享M2，不重复计数。此近似配平不等于等函数类/等信息/等正则，只让“只是头参数更少”成为可反证解释。PPBR128是已完成实验：两seed MAE 11.526014553522387和11.345502393032495，不能再提为新验证。[E-RUNS、E-OLDGUIDE；derived_checks.json]

### 2.3 PPBR seed46不是可被三次胜利抹去的例外

Mini−CheM四seed MAE差依次约−0.414011、−0.324749、+0.038734、−0.509500。正号seed46意味着Mini更差；它发生于匹配设备/控制，因此不能简单用旧跨主机差异解释。当前注册的四seed全正准则未满足，结论是有条件候选而非普遍替换。对是否保留，该反例的重要性取决于业务允许的风险和实际误差群，不能凭3/4转成统计概率。[E-MMSOL、E-UMMSOL]

48测试整配方结构压力；M2测试Mini内floor；M9的冻结TabICL回归提供另一种条件估计/非参数上下文偏置。后者PPBR预注册使用其`median`输出，但官方实现是各变换视图median预测的平均，不是整个混合分布的数学中位数，不能借“median更匹配MAE”声称已有收益。所有方法仍要比较原Y尺度MAE。[X-TABICL-REG]

### 2.4 DILI：负迁移本身是可用的对照，不是要被“修好”的日志

DILI保留F001对H0四seed的局部收益；canonical/scaffold的floor排序又不同。其Valid仅48行（13正/35负），成员排序和early-stop选择都可能十分敏感。Mini/TabM没有稳定收益，因此48把它作为负向迁移对照是合理的，但结果无论正负都不解释全部头机制。[E-U4、E-GROUP20、E-FACTORIAL]

实际反例：H0 drop0 seed46 Valid约0.857143低于base约0.865934，两者内部stop约0.819549却相同；低lr H0 seed46 Valid约0.749451，最佳epoch3、结束11。这样的run不可能仅把max_epochs从50改200就受益，因为patience8早已触发。此前已有stop更优而Valid更差的其他配对，支持审查选择/分布风险，不能用train loss或更长训练作为替代质量指标。[E-OPT72]

因此本轮不为DILI密扫TabM结构。它保留48负对照及M9冻结TabICLv2的小型新归纳偏置分支。若仍负，停止该家族在DILI的当前配方；不去挑选较好seed，不主张“DILI不适合所有新底座”。

### 2.5 对已派48的完整覆盖与排除

48含六任务：AMES、PPBR、Sol、microsome、CYP2D6 Veith、DILI。前四类按CheM/Morgan或CheM/Mini MLP成对，后两类CheM/Mini TabM成对；12配方×两group×44/45。分组hash seed43，目标fit70/stop10/stress20；原行不删，标签只在fit学习；stop挑epoch，stress最后一次；三份类别/非恒定及样本量门槛不达则整组跳过，不重抽直到出好结果。[E-48、E-OLDGUIDE]

能回答：固定配方在两种指定train内结构压力下是否保持方向、跨seed是否反转、负迁移是否稳定。不能回答：外部完全未见数据的泛化、表示单因子因果、成员机制、目标错配、固定Valid群真实错误、全22统一配方。历史上这些train行已经被其他模型学过，因此是回顾性压力测试，不是彻底未触碰终评。`dispatched48_exclusions.json`展开48身份，全部本轮新增fit记0。任何新返回由主控增量并入，不能改变本报告快照后反写“当时已知”。

## Q3. 高价值未试方法：具体资产，不以模型家族名代替版本

### 3.1 已做与未做的边界

真实已做：CheM22任务、MiniMol指定任务、Morgan2048 identity、MLP/affine/128宽、dropout/学习率、Huber、fit-posBCE、TabM k32、固定均值ensemble及group20。未做：半衰期ranking4真实学习、TabM k1/k8/deep-plain机制拆解、固定200epoch轨迹、多stop同轨迹选择、归一化原posBCE、TabICLv2/Monroe/MoLFormer本项目实测。仅有原proposal而无learning记录的方向不算完成；反之旧Pro建议若已由Astra真实执行，不能继续叫“从未测试”。[E-EXECUTION、E-RUNS、E-RANK4、E-ASSETS]

### 3.2 TabICLv2：优先于未闭环的新编码器，但仍不是ready

本轮检索一手论文与官方代码，固定代码commit `0dbff3ec8fc68c123c87af77b0ea8b25cd2d23f3`（v2.2.0），不是只写TabICL家族。HF仓库`jingang/TabICL` revision `4dcd344ece2c00be9e831fdd35bed57b5ad83e19`有两个不同checkpoint：

|用途|文件|登记权重SHA256|
|---|---|---|
|分类|tabicl-classifier-v2-20260212.ckpt|bdc7dbd5e4ff21f8f0456fcf90c6b7cdf72dbea960f2d05b19bec19f9b3d4ed0|
|回归|tabicl-regressor-v2-20260212.ckpt|0db9cb538f114e79026bf08f45f41ad8dd7ad2de2aaca9a5ca8cd3bd9748ae7a|

论文/源码支持其为预训练表格上下文预测器；v1/v1.1不能默认为具有同一回归能力。代码主许可BSD-3-Clause，forecast衍生部分保留其Apache通知；许可已读不是本项目全部使用条件已批准。checkpoint元数据已读，没有下载二进制、运行或本地freeze验收。[X-TABICL-README、X-TABICL-LICENSE、X-TABICL-PAPER、X-TABICL-CKPT-C/R]

实际`.fit`路径装载固定模型，拟合输入编码/变换与带标签context；回归还用context Y的StandardScaler，预测再inverse。这里可以不更新预训练参数，但**fit仍会使用标签形成状态**，必须只传train-fit，不能把Valid/stop塞入上下文，也不能调用finetune API。缓存可以作为运行中间态存在，但原预训练state参数与buffers不得改变；query的次序、分块和数量不能悄悄改变fit统计。`kv_cache=False`作为首个明确配置，禁止自动下载未登记版本。[X-TABICL-REG、X-TABICL-CLS]

M9使用现成Mini512原特征，PPBR/microsome固定回归checkpoint，CYP2D6 Veith/DILI固定分类checkpoint；random_state44仅管理8个变换视图，不是新训练了8个基础模型。配置固定`norm_methods=[none,power]`、outlier_threshold4；regressor caller不再提前标准化Y；分类采用官方logit平均/temperature0.9路径，不能偷换成TabM的概率均值。没有early-stop训练过程，stop指标只是诊断，不据其遍历更多checkpoint。这四项是**4个冻结context fit，0个梯度头fit**。[next_experiments.json M9]

反证与适用性：tabular benchmark优势不保证ADMET特征分布适配；高维连续embedding、样本/特征规模和标签分布都可能出界，不能凭paper分数宣布胜出。M9对已成功的CYP/micro、反例PPBR和负迁移DILI做小型互补面板，信息量高于无条件22任务全面接入。

### 3.3 Monroe：不能把PT、FT和TabPFNv3混为当前允许的算法

官方研究`arXiv:2608.18982v1`与`blazejba/Monroe`给出720维编码器、具体GRIT配置和checkpoint。已读LFS pointer对应权重OID `df996e8e98b12a3cda5fe5acbef3e1e9a4ea31946d3736461cd07e53a5bf205a`、300057823 bytes；这只是指针，不是权重payload。main源码/config/loader可读，但本轮未可靠解析完整不可变code commit，所以该字段保留null，M10必须blocked_assets。不能把任意后续main配同一个旧权重当完整版本。[X-MONROE-CONFIG、X-MONROE-POINTER、X-MONROE-LOADER]

其论文区分native predictor、预训练encoder、微调encoder及TabPFNv3条件。有些比较改善依赖FT encoder，本项目明确禁止外部encoder更新，不能移植这种收益。TabPFNv3是另一个需要独立许可/准入/权重的预测器，不是旧资产表的TabPFN2.6，更不是TabICLv2。本文只建议冻结Monroe720+本项目MLP，不自动引入TabPFNv3。[X-MONROE-PAPER、X-MONROE-README]

工程风险直接关系科学有效性：loader里的非严格加载可能掩盖encoder键缺失，旧`torch.load`安全选项不能未经审查执行；允许舍弃的预训练head键必须列清单，其余encoder键严格一致。默认inference示例会读Polaris数据，不得运行；分子输入转换、构象/2D fallback、stereo信息与失败覆盖须显式绑定，不能丢行。MIT与NOTICE原文已读，但checkpoint具体使用/再分发条件与固定代码仍由主控准入，不能仅凭仓库许可证推所有依赖。[X-MONROE-LICENSE、X-MONROE-NOTICE、X-MONROE-INFERENCE]

### 3.4 MoLFormer：选择公开10pct checkpoint，而非借用full-XL宣传

本轮具体候选是`ibm-research/MoLFormer-XL-both-10pct`，revision `361063d0ad524ef77cf39b08469f6be770dc550f`，`model.safetensors`的SHA256为`0795977fe7192c4acdaf052f0e8464af57bc4bb59211271c5e61aaba2637b9c6`。它不是full1.1b训练版本；论文方法和这一资产的精确训练范围必须分开。[X-MF-PAPER、X-MF-CARD、X-MF-WEIGHT]

已读config：hidden768、12层/12heads、max_position_embeddings202、num_random_features32，**deterministic_eval默认false**。因此单写`.eval()`和`requires_grad=False`不足以证明buffers冻结；必须对固定code中随机feature路径和前后state做独立fixture。本研究将deterministic_eval=True列为具体准备配置，但未测试其是否消除全部buffer变化。原code有版本兼容提示，config记旧transformers版本、模型卡有新API示例，不允许执行方按“最新版”随意换tokenizer/remote code。[X-MF-CONFIG、X-MF-CODE、X-MF-CARD]

官方模型卡预处理使用canonical non-isomeric SMILES；这可能丢弃原输入立体信息，应记录原行与原SMILES映射，而不是改原始数据。长分子覆盖、特殊字符/token长度与pooling定义须在批准的零学习fixture中核对；不能不记录地截断、删行、用全零替换后仍称完整公平比较。模型卡Apache2并不自动解决本地依赖版本/代码执行安全。旧MoLFormer目录外写入失败作为运行历史保留，重做合法准备不追溯清除失败。[E-ASSETS、X-MF-CARD]

### 3.5 其余已调研底座及排序

KPGT、Uni-Mol、SMI-TED、MolE、scratch小D-MPNN、TabPFN2.6仍按其最新有据准备状态保留，不能冒称已具本轮数据覆盖/冻结接口。经典特征“家族”中Morgan已经实做，并不代表所有descriptor/solver都已准备。本文没有重新逐份读完这些未被选中分支的全部历史论文，因此不对其作新的性能判断，也不把未读记成不可达。[E-ASSETS、E-BRANCH]

优先顺序不是“参数更大更好”：先利用已验缓存完成M1–M8；并行仅准备TabICLv2固定上下文接口，其可用现成512特征而无需新编码；Monroe/MoLFormer按严格版本与覆盖准入各提供一个新表征机会；MiniMol hepatocyte是已批准encoder的真正新任务，准备成本应小于全新底座，但任务cache不能假定现成。具体收益必须靠未来实测，资产检索不是效果证据。

**Q3状态partial**：主要checkpoint与代码/许可出处已明确；Monroe不可变源码、三种新方法的payload/runtime/全行覆盖和本地准入没有被本轮完成。这个局部缺口只阻断M9–M11相应分支，不阻断已有表示上的机制研究。

## Q4. 用可执行对照区分目标、容量、成员和优化窗口

### 4.1 训练loss、早停与外部指标不能混写

当前MAE/Spearman任务默认fit-only标准化Y上的MSE；分类默认logit BCE。选择epoch按原生MAE↓、AUROC/AP/Spearman↑；Valid固定评分在选择结束后进行。早期历史把Caco“训练与早停都用MSE”写成当前实现是已纠正的问题，不能重现。Huber、posBCE、affine、128宽已经真实实现；ranking4才是尚未执行的新接口。[E-EVENTS、E-OLDGUIDE、E-RANK4]

Spearman不受严格单调变换影响，而MSE偏好条件均值与幅度拟合。因此MSE优化不会保证排序提升；但换pairwise损失也不直接等价于最大化Spearman，尤其存在重复Y、小batch及stop选择时。半衰期M1继承原四seedF001计划，loss为：

`0.5 mean((zhat-zY)^2) + 0.5 mean_{i<j,Yi!=Yj} softplus(-sign(zYi-zYj)*(zhati-zhatj))`。

两个项独立mean，temperature=1，batch128内所有非tie无序对，不另抽pair；无可用pair时rank项为0。输出仍逆标准化一次回原Y；stop和外部都是Spearman最大化。预列`0.5*MSE`四项作为有界尺度控制：若rank组合仅胜原fullMSE而不胜halfMSE，不能说学到了额外排序信息。旧fullMSE四控制只复用，原planned ranking4只学一次。纯系数控制在AdamW下也受§4.2所述尺度不变性约束，不能当作预期获益配方；能证明等价则复用原控制并减少fit。[E-RANK4；M1]

对于Huber，其小误差项是0.5e²，与原MSE的e²存在二倍梯度系数差；因此“Huber更好”不等于“对离群值更鲁棒”已被识别。LD50明确4/4，lipo/Caco各3/4，可保留配方同时在条件储备D12以halfMSE/L1做有限拆解，不马上给所有MAE任务无限loss grid。[E-OLDGUIDE、E-U54]

### 4.2 加权BCE不保证排序更好

实际权重是`w=min(5,max(1,sqrt(Nneg_fit/Npos_fit)))`，不是直接负正比；它只从fit原行计算。对无约束、无限数据的理想二分类条件概率p，加权BCE最优q满足：

`q = w*p/(1-p+w*p)`，故`logit(q)=logit(p)+log(w)`。

固定正w严格保序。因此其AP/AUROC收益不能仅凭“更重视阳性”从公式保证；实际变化来自有限容量、训练正则、优化或样本分布。M7保留w及采样，唯一除以fit平均权重`Z=(Nneg+w*Npos)/N`，对正向CYP2D6 substrate与负向CYP2C9 substrate配对各两seed，4fit。若w=1，两目标等价，跳过，不临时换更大权重。这里有重要反证：对固定正倍数c，在相同batch、初始化及状态、无clipping时，AdamW满足m_c=c*m、v_c=c²*v，自适应步为m/(sqrt(v)+eps/c)。若eps=0，连同相同decoupled weight decay的整个轨迹严格不变；weight decay本身不造成所谓相对正则变化。当前eps=1e-8及有限精度/AMP仅留下数值路径差异。因此M7是低优先级有界负控制，不预设正收益；若主控能证明注册实现的轨迹等价则直接复用、跳过，不为凑4项训练。[E-OLDGUIDE、E-U140、E-U54；以上为本轮代数推导，不是新实测]

### 4.3 TabM的容量与成员机制

实际TabM为3个512宽块、k32、random-signs fast-factor初始化、dropout0.1，不是32个独立数据集上的完整MLP。训练loss对行和成员都mean；分类预测为每成员sigmoid后平均，不能替换成sigmoid(mean logit)。同样k1仍有乘法fast factors和成员化输出，不等于plain深MLP。[E-FACTORIAL、X-TABM-CODE]

按已读实际架构推导，输入维度D时参数为`512D+524288+k(D+4609)`。MiniD512、k32=950304，与实际记录吻合；CheMD2048、k32=1785888。对应去掉fast factors的plain3×512是`512D+526337`，分别788481与1574913。M5并排新plain、k1、k8，复用旧MLP256与k32；Caco正例、CYP正例、micro负例三任务共18新fit。保持同表示、floor和50/8预算，让“深头容量足以解释收益”与“成员机制有额外收益”可区分；仍承认k改变参数量和优化噪声，不把它写成完美等参数实验。[derived_checks.json]

### 4.4 50epoch是上限，不是收敛判据

Caco某些run最佳或终止到50是right-censoring信号，可能需要更长轨迹，但不能直接断言未收敛。DILI的低lr run最佳3/结束11说明单增max_epochs无用；CYP3A4某低lr正例最佳22/结束30、原对照最佳18/结束26，说明低lr收益并不都由触顶解释。[E-FACTORIAL、E-OPT72、E-CONF54]

M4和M8每个seed实际只训练一条固定200epoch轨迹；只用stop指标虚拟回放三种预声明选择策略：(50,patience8)、(200,patience8)、(200,patience200)。它们是同一学习轨迹的不同检查点输出，不应计三倍fit。日志/评估不得推进训练RNG，前50更新规则需与既有实现对齐；若prefix不匹配，只能将新轨迹当新实现bundle，不能伪造同轨迹控制。Valid不每epoch打分，只有预先锁定策略的结果由主控按授权评分。三策略扩大了候选epoch预算，必须作为选择政策变化报告，不能混称单纯训练时间。

Caco只对CheM F010的MLP256与TabM32做4fit；CYP3A4 Veith是H0/F010×lr5e-4/1e-4×44/45的8fit。若200/8与50/8完全相同，原因可能是早停已经触发；若200fullwindow也不改善，本分支停止，不再自动提400/800epoch。

### 4.5 floor是缩放，不是删除特征

在非零分母且无后续截断的条件下，改变正对角分母是可逆坐标变换，第一层权重可吸收其逆变换。因此不能把F010获益简单称作“去掉不可靠维度”。真正变化的是初始激活、梯度、权重衰减在原坐标的等效惩罚、有限训练路径与数值范围；若数据已量化/裁剪/溢出，可逆假设才需重新检查。原constant rule将std<1e-8分母置1，也须与普通floor分开看。[E-OLDGUIDE；本轮代数解释]

M2/M6专门保留这些竞争解释。后续若仍分不开维度信息和参数容量，D15才允许fit-only PCA与固定随机投影在两任务、两seed上最多8fit；不能把PCA rank受nfit限制时仍写成512等维，也不能将PCA改成额外样本的拟合。此储备不包含在确定74内。

## Q5. 具体分子群、误差未知与共识风险

### 5.1 现有完整群入口是什么

`cohort_register.json`保留六个Huber Valid群、八个已评分train.stress群的具体cohort_id、成员ref、SHA及分母，并另保留AMES、MiniSol/PPBR、microsome/CYP和48的完整索引入口。入口不是举几个分子示例，更不是本轮读取了全部成员。公开SOURCE_MAP对多个ref给`packet_path:null`和`inherited_fixed_url:null`，所以它们是**已登记但没有本包可读blob链接**，不是实际404，不是从未记录。未尝试他人本地路径，也未猜hash目录。[E-ISSUES、E-SOURCEMAP]

已固定的Huber高/低分歧群为Caco各10/91、LD50各194/1937、lipo各42/420；完整URI导航与成员SHA见附表。AMES高低群各114/1137；microsome各12/111、CYP2D6 Veith各132/1313沿已登记followup入口。MiniSol/PPBR本次未读到可核群数，保留null，不从十分位名称或总量猜数。群成员指针存在不等于具体化学盲点已经识别，更不能凭分子结构反推真实标签。

### 5.2 什么已经可用，什么仍然未知

八个train.stress群已真实评分：DILI F010在canonical/scaffold都有正向，CYP2C9 substrate在canonical与scaffold方向反转；half/Sol的floor排序也有群依赖。Sol每种stress1009/5045，其他任务各自有真实群规模，不能拿它们当官方Valid分母。旧issue的嵌套“awaiting”需要按最新`current_resolution`和group20 update解释，不能覆盖真实已评分事实。[E-GROUP20、E-ISSUES]

Valid高低分歧群目前主要提供**模型敏感性**：例如旧低分歧组在新增seed下也会出现预测分歧变大。这说明共识随训练随机性不一定保持，不说明谁错。整体MAE/AP提高无法推出同一群误差减少，更无法推出解决了特定化学机制。低分歧模型可能共享相同表示缺口、偏置或未覆盖结构，尤其同底座/同训练数据集成。[E-ISSUES、E-ENS59]

### 5.3 获准的验证请求必须是聚合而非逐行答案

建议主控在私有区将固定群与旧/新已验预测关联，只输出用户授权且支持度足够的组级汇总：群ID、成员版本、定义时间、n/必要类别support、对应模型/seed、指标定义、成对差异及实际不确定性方法。回归在原Y尺度报告MAE和必要的宽范围分布；分类需同时有两类，AP受阳性比例影响必须注明，不能用accuracy/阈值替换AUROC/AP。组小或组合可逆时抑制发布；Caco10行组不因“已经公开成员”就自动允许精确误差。不能密集询问交集、补集、相邻排名小组从差值恢复个体。

允许的新无标签诊断包括：固定群内原子/环/电荷等分子描述分布、距train-fit的预先固定相似度分层、模型/seed分歧稳定性、长输入或解析mask比例、feature范数与floor触发情况。阈值仅用train-fit定义并冻结；不根据Valid误差反复寻找最差小群。无真值诊断可支持“候选风险”，不能支持“此结构预测错了”。需要真实修复判断时，必须同一预固定完整群、同一原输出尺度、同一合法评价范围比较前后，保留未改善的反例。

**Q5状态partial**：所有当前可定位完整群入口与已有stress事实已保存，验证路径明确；部分成员blob未在公开映射中可读，且Valid群真实误差缺少准入汇总。因此不能给确定的分子错误机制或声称群已修复。这个缺口不阻止M1–M8的整体机制判别。

## Q6. 多批精确矩阵、预算与范围收口

### 6.1 确定矩阵而不是待执行者猜范围

`next_experiments.json`逐条为一个task、一个完整配置、一个split，可包含共同model seeds；共37条proposal。默认raw-string group split43、stop10%、MLP256/drop0.1、AdamW5e-4/wd1e-4/betas0.9,0.999/eps1e-8、batch128、50/8/min_delta1e-7。所有例外逐项写明。每条包含资产版本、预处理、loss及尺度、early-stop metric/direction、外部指标及原输出尺度、对照和准备方式。新适配器的科学字段明确标new_code，不冒称已有CLI支持。

|模块|任务/配置|共同seed与split|新增唯一fit|作用/准备度|
|---|---|---|---:|---|
|M1|half：原rank混合+0.5MSE，fullMSE复用|44/45/46/47；raw43|8|8；new_code|
|M2|PPBR、Sol、micro：MiniF010；MiniH0复用|46/47；raw43|6|6；new_code|
|M3|AMES：CheMH0/Morganidentity，各双stop同轨迹|44/45；新四路canonical43|4|4；new_code|
|M4|Caco：CheMF010 MLP256/TabM32，200轨迹|46/47；raw43|4|4；new_code|
|M5|CacoCheM、microMini、CYPD6Mini：plain深头/k1/k8|46/47；raw43|18|18；new_code|
|M6|Sol/micro：CheM128F010/Mini512F010|46/47；raw43|8|8；其中4 config_only、4 new_code|
|M7|CYPD6substr F010、C9substr H0：原posBCE/Z|46/47；raw43|4|4；new_code，w=1等价跳过|
|M8|CYP3A4Veith：两floor×两lr×200轨迹|44/45；raw43|8|8；new_code|
|M9|PPBR/micro回归、CYPD6/DILI分类：固定TabICLv2|random_state44；raw43|4|4context；blocked_assets|
|M10|BBB/herg：Monroe及MoLFormer10pct+MLP256|46/47；raw43|8|8；blocked_assets|
|M11|hepatocyte：Mini512H0MLP256新任务|46/47；raw43|2|2；blocked task cache|

### 6.2 建议小/中/大预算，按信息与依赖而非固定实验数

|预算|新增梯度fit|冻结context fit|总新身份|已有唯一控制seed身份（0新fit）|共享新编码对象|建议|
|---|---:|---:|---:|---:|---:|---|
|small|22|0|22|14|0|可选|
|medium|60|0|60|36|0|推荐作为分批上限|
|large|70|4|74|45|5|可选|

小档M1–M4是22：不等待48的全部机制结论，也不与其身份重复。中档M1–M8是60：在首层接口准备后把具有正反任务的机制面板接续完成，有界而非无限grid。大档加入10个新梯度头与4个冻结context fit，共74；新增5个task/encoder cache对象（Monroe2、MoLFormer2、Mini-hepatocyte1），各对象train和Valid两分区，只编码一次共享seed，不暗加test编码权限。TabICL8个视图不计8个梯度fit。controller可按模块依赖跳过，预算减少，不用别的任务填满名额。

本轮已存在的控制只按科学身份计一次；已经完成的PPBR128等不再训练。原planned ranking4纳入8项M1一次，采用时继承原run IDs，不因本报告proposal名再产生副本。48已派仅作并行证据来源，不再计48个新fit。`controls.json`对部分旧alias使用原比较文件内task/representation/floor/head/seed唯一选择器，而不猜历史run文件名；采用时必须解析到原物理产物。各版本的对照不是随意换一个同seed分数。[E-RUNS、E-EXECUTION、E-RANK4、E-48]

### 6.3 端到端成本，避免把机器秒当全部成本

真实历史量级：Mini12的12新fit GPU程序约78.383257秒；confirm14约182.237658秒/14新头；早前8fit约38.326秒；optimization72约753.420710秒。它们含不同样本数、epoch、加载/评分流程，不是固定50epoch单头耗时；不能机械按平均秒数保证200epoch成本。[E-UMMSOL、E-U14、E-U4、E-U72]

较旧28批记录还显示训练角色1733秒、准备到取回启动6815秒、取回到候选1905秒、transfer492秒、Pro UI4169秒。它们有时间重叠，也不是本轮UI/思考用时，不相加成“总GPU耗时”。以这些事实说明新代码准备、取回、评分、主控消费与研究等待可能比小头训练更重要，不代表每次都会同样耗时。[E-ASTRAOLD]

本报告只给可检验计算式：

`Tcritical = DAG critical path(preparation, shared encoding, gradient/context fits, retrieval, fixed scoring, review/decision)`。

小/中/大分别有4/12/12条200epoch轨迹，按200/50倍数作**名义**head-epoch计数为34/96/106个50epoch等价量；这不是实测flops或跨模型统一秒数。附表以每等价量5–60秒做宽敏感性范围，得到梯度程序170–2040秒、480–5760秒、530–6360秒；这些仅是明确假设下的代数，**不含**准备、new-encoder、TabICL、取回评分/研究/等待，也不是置信区间。新TabM宽头/大task实际可超出该范围，应记录真实step与时间更新，而不是掩盖不确定性。

端到端可选预算应由主控登记：例如准备模块共享一次fixture和运行包，随后连续派发M1/M2、M3/M4、M5/M7、M6/M8几个有信息批次；已有微型头不要为计时再造重复试训。资产分支单独批准文件/显存/过程生命周期上限，某新encoder超过限制就停止对应分支，不让整个研究等它。资源额度是执行授权，不由本研究中的时间敏感性代替。

### 6.4 条件接续与停止

所有条件见`conditional_followups.json`。核心规则如下：

若48结构反转，保留任务/配方适用范围，优先M2/M5/M6相应反证，而不是重新抽split或加seed凑一致。M2变换等价就跳过；M1 rank不胜scale则否决该pairwise解释并停止lambda/temperature扫描；M5 plain/k1已解释k32优势就停止增加成员；M4/M8长窗口无改善则不自动400/800。

只有新证据支持转移，才进入条件储备：VDss rank/scale最多4fit；CYP2C9 Veith或Pgp新表示/头每task最多4fit；PCA/随机投影机制最多8fit。它们不是确定74里的隐藏占位符，不授予执行方自行选task/seed；采用前主控展开真实矩阵并与最新台账再去重。现有固定均值ensemble已展示比最佳成员更差很常见，未来组合最多先注册两组零新训练均值，不用Valid拟合权重，不凭较好seed剔除成员。[D12–D17、E-ENS59]

触发下一次研究的理由应是重要反证、一个新资产/科学分支获得可用证据、当前预注册判别已完成，或明确方案耗尽且问题仍重要；不是固定分钟、单个头完成或空队列。冻结/标签/身份/重大版本错误立即回主控。正常情况在一个完整可比较模块返回后消费，无需每头都重新等Chat。

### 6.5 如何知道本轮研究范围可以收口

局部配方收益已经有足够稳定证据时，停止原样确认，转入部署资格/范围限定而非继续重复Valid。机制问题至少要把会改变下一动作的竞争解释区分到可决策程度，不要求找到唯一宇宙级因果原因。负配方在注册面板内被反证就停止；有正式的资产/许可阻碍则记录依赖与再开条件，不把它伪装成性能失败。盲区只有同一群真实错误与前后比较的证据才可关闭；如果无准入汇总，明确其尚未解决，但不阻断独立任务。

全22任务各自满足表内范围收口条件，连同未知/失败/版本/再开触发一起归档，才是本研究问题的科学收口。没有训练队列并不构成这个证明，持续有队列也不构成持续有信息。

## 7. 关键新主张的定向交叉核验

|新判断|直接支持|独立的另一种检查/反例|仍存不确定性|
|---|---|---|---|
|AMES应从确认转为selector/分布判别|四seed比较原文E-AMES|相同2048/头参数，stop排序相反；48字段显示它不是双selector实验|不把共同分布的四seed当独立外部验证|
|Mini表示收益有容量/尺度混杂|E-MMSOL/E-MMCYP真实config|解析头参数公式；PPBR46同设备负例；micro换TabM负例|参数近似匹配不等表征信息完全隔离|
|TabM k1不能作plain对照|实际3×512/k32记录|官方源码枚举与factor结构；参数代数在D512k32对上950304|未实例化k1/k8或测训练效率|
|单增maxepochs不能解决所有case|Caco触顶记录|DILI epoch3/11及CYP3A4正例22/30都未触顶|长窗口增加选择预算，需报告虚拟策略|
|权重公式不等负正比|已采纳指南原文E-OLDGUIDE|目标最优logit平移推导；C9负/CYPD6正|实际fit权重仍由执行端原行统计绑定，不从Valid比例估计|
|半衰期更多seed ensemble非必好|E-ENS59已验均值|0.332458569−0.377460914=−0.045002345纯算术|跨host/成员选择历史混杂，不推所有ensemble无效|
|PPBR128不能当新首批|E-RUNS两条真实run|proposal-execution映射与原guide任务列表相符|只排除相同科学身份，不禁止不同新假设|
|新模型元数据不等ready|官方代码/modelcard/LFS元数据|项目asset ledger未有payload/runtime；Monroe code pin未闭合|只能blocked，不能声称质量未知=质量差|

这里“交叉核验”指原件、实现、已验汇总和新代数的定向对照，不是声称进行了独立subagent研究。本轮用户禁止派Agent，未派任何Agent；更没有用角色扮演的多个同意票作为证据。

## 8. 实读、继承、未读与失败尝试

`evidence_registry.json`逐对象记录URI、版本、字节登记值、可见行数和阅读范围。巨大experiments/claim/issues/source索引只按本问题相关分支下钻；不把索引摘要当全部原文件已经读过，也不声称重新审核586个训练或556个评分。source_version的输入/历史SHA是登记绑定，不是本轮下载原字节独立重算。当前环境容器网络访问失败，但web原文可读；因此用web原文分析，没有执行下载来的模型或代码。

局部取回问题具体分类在`evidence_gaps.json`。例如TabICL一开始路径猜成`sklearn`出现404，经官方路径查正为`_sklearn`后已读源码，这不是“原件不可达”。MoLFormer rawconfig失败后固定revision的blob已经读到；Monroe代码commit解析没有得到可用固定版本，main原文仍已读，二者不混淆。固定群ref没有公开blob链接是记录与公开映射差异，不能说从未有记录。

未来机制证据需要实验；未返回48需要主控消费真实结果；现有群无标签描述可由已准入原件计算，但本轮未收到完整blob；Valid群误差须主控私有安全聚合；未选中底座的完整旧原文是尚未读取而非不可达。这些分类分别关联Q1–Q6和受阻模块，不以局部缺口要求全库重审。

## 9. Q1–Q6完成位置与科学状态

Q1 answered：§Q1全22行动与条件，task22_actions.json可归并；结论只针对配方范围。Q2 answered：§Q2独立竞争解释与48局限、M2/M3/M5/M6互补方案；机制未识别明确保留。Q3 partial：§Q3官方版本/许可/冻结接口研究与具体blocked矩阵已完成，Monroe code pin和新资产本地准入未闭环。Q4 answered：§Q4四类混杂及M1/M4–M8可落地新接口，未冒充真实训练。Q5 partial：§Q5完整群入口、证据等级和安全验证路径，缺部分公开成员blob及真实群误差，不能称错误已定位。Q6 answered：§Q6 37proposal、三档预算、去重和条件收口；proposal_only不是执行授权。整体科学status必须为needs_evidence，文件完整性和会话交付完成另行登记。
