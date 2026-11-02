# ADMET：86项新增实验后的独立科学评审与连续批次路线

**request_id**：`admet-pro-parallel-20261102-001`  
**round_id**：`breadth22-confirm86-20261102`  
**固定快照**：`672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2`  
**输入清单绑定**：`25ba8a81a13e070f9d8f7f6336e5f0b97f06ae5c6097257361205ca1f2e2a213`。此摘要由请求提供，本会话没有独立重算输入清单字节哈希。  
**权限**：proposal_only。没有训练、拟合预处理、加载模型、编码、推理、安装、赛事上传或读取逐行Valid真值/残差。  
**科学状态**：needs_evidence；这是对机制、泛化及若干资产缺口的实质保留，不代表已交付方案为空，也不代表已授权执行。另一条Astra研究线路未被读取或推测。

本报告的`[E-…]`、`[X-…]`均解析到末尾来源表及`evidence_registry.json`的精确URI、版本和实际阅读范围。`derived_checks.json`保存从已验任务汇总抄录的数据和新增算术，而非重新评分。完整训练矩阵在`next_experiments.json`，本报告中的表只用于解释；两者不能以摘要替代。

## 决策摘要

**最值得下一步验证的不是“把F010推满22任务”，而是“哪些任务需要何种尺度—头—优化组合”。** 完整22任务呈10个双seed改善、5个双seed退化、7个方向不一致；所有5个MAE任务双改善，但分类和排序任务没有统一响应。当前所有22任务都已接入H0/F010；旧的“其余16任务尚未准备”已经过期。[E-SCORES, E-AUDIT64, E-INTERFACE]

新增敏感性算术进一步表明，本地推断均分的净改善主要由LD50、PPBR、Solubility三项贡献：seed46约85.75%，seed47约100.98%。剔除三项后的其余19任务，seed47平均归一化差值为−0.03204；同时剔除BBB后的其余18任务仍为−0.03324。它不是官方分数或无偏总体估计，却足以否定“接近46说明多数任务普遍学得更好”的推论。[E-SCORES, E-CONTROLLER；本轮派生]

F010是正对角缩放，不是删除低方差特征。理论上第一层重参数化可保持同一函数；实际收益可来自数值条件、初始化、有限步优化、正则或早停，而不是已被识别的“去噪”。DILI原件显示F010内部stop AUROC明显更好、外部Valid却更差，直接反对把早停曲线当泛化证据。[E-SCALER, E-HEADS, E-DILI-F, E-DILI-H]

**推荐中档89个新增唯一fit、分批登记，而非一次无条件发出。** 首批25＝12个退化/不稳定任务各补F001两seed（24）＋BBB前瞻性完整H0 seed46（1）；随后8任务×H0/F010×两seed的无dropout MLP（32）及相应线性头（32）。已有控制共享，不重新训练88个基线槽位。小档25；大档上限197，包含优化、损失、结构压力测试和有准备门槛的新表示，绝非“197项已经就绪”。[E-DATAIO, E-INTERFACE；本轮设计]

<a id="Q1"></a>
## Q1．完整22任务真正支持什么

### 1.1 可比较单位、验收范围与不能扩大之处

本轮是86个新增逻辑训练/评分＋2个复用控制组成88个任务—配置—seed比较槽位，不是88次新训练。原Mini22的一次逻辑run含22个任务头；430个checkpoint文件也不是430个fit。累计149逻辑run、170正式任务评分是已验账本口径，不与本轮fit数混加。[E-CONTROLLER, E-HISTREG, E-AUDIT22, E-AUDIT64]

比较以任务、原始输入版本、冻结CheMeleon缓存、内部fit/stop划分、预处理拟合域、训练目标、早停、model seed和本地外部指标为单位。已有身份匹配且主控准入的控制可以跨批复用；仅“来自旧批”不使比较无效。真正的限制是BBB H0 seed46缺原始encoder-after、部分seed46跨主机、旧缓存生产环境与新消费环境不同以及Valid反复使用。[E-LIMITS, E-ROOT-REVIEW]

64项桥接已验配置/冻结通过；22项新六任务中21项before/after一致、BBB一项缺after。BBB旧分数可作为注明限制的研究观察，不能宣布原冻结证据补齐。下文保留全部22任务描述，同时对去BBB的共同21任务作已验敏感性引用。标签、行身份、冻结或重载实质失败会使对应比较无效；它不算某个科学假设被反证，更不是分数好即可豁免的运行问题。[E-AUDIT22, E-AUDIT64, E-LIMITS]

### 1.2 全22任务分数、历史锚点与适用行数

下表来自已验`all22-comparisons.json`的paired部分。Δ统一为“正数更好”：MAE是H0−F010，其余是F010−H0。表中保留6位小数便于阅读，附加JSON保存原汇总精度。Mini22与当前并非同seed/同训练历史控制，只作历史参照。Valid行数及正/负类数引用原Mini22同v6分区汇总，并以本轮已验行身份一致性为适用前提；**不以数据集总量代替Valid行数，也不拿Valid类比例设计训练权重**。[E-SCORES, E-MINI22, E-CONTROLLER]

| task | 指标 | Valid n（正/负） | H0 s46 | F010 s46 | Δ46 | H0 s47 | F010 s47 | Δ47 | 原Mini22 | 结论 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ames | AUROC↑ | 1137（479/658） | 0.789769 | 0.790788 | +0.001018 | 0.782002 | 0.781190 | -0.000812 | 0.796606 | 不一致 |
| bbb_martins | AUROC↑ | 203（149/54） | 0.893301 | 0.911322 | +0.018021 | 0.890194 | 0.889821 | -0.000373 | 0.893674 | 不一致 |
| bioavailability_ma | AUROC↑ | 64（43/21） | 0.657807 | 0.681063 | +0.023256 | 0.687708 | 0.724252 | +0.036545 | 0.744186 | 双改善 |
| caco2_wang | MAE↓ | 91 | 0.429648 | 0.354666 | +0.074982 | 0.391865 | 0.366242 | +0.025624 | 0.426065 | 双改善 |
| clearance_hepatocyte_az | Spearman↑ | 122 | 0.288348 | 0.323984 | +0.035636 | 0.344073 | 0.398675 | +0.054602 | 0.357606 | 双改善 |
| clearance_microsome_az | Spearman↑ | 111 | 0.469117 | 0.479867 | +0.010750 | 0.492182 | 0.456283 | -0.035899 | 0.487330 | 不一致 |
| cyp2c9_substrate_carbonmangels | AUPRC↑ | 67（12/55） | 0.286116 | 0.336767 | +0.050651 | 0.368682 | 0.306749 | -0.061933 | 0.420994 | 不一致 |
| cyp2c9_veith | AUPRC↑ | 1210（406/804） | 0.758908 | 0.764208 | +0.005299 | 0.758663 | 0.759683 | +0.001019 | 0.759450 | 双改善 |
| cyp2d6_substrate_carbonmangels | AUPRC↑ | 67（14/53） | 0.392929 | 0.411943 | +0.019014 | 0.398161 | 0.401468 | +0.003306 | 0.463777 | 双改善 |
| cyp2d6_veith | AUPRC↑ | 1313（250/1063） | 0.665930 | 0.671483 | +0.005553 | 0.654895 | 0.690405 | +0.035510 | 0.690734 | 双改善 |
| cyp3a4_substrate_carbonmangels | AUROC↑ | 67（36/31） | 0.745520 | 0.738351 | -0.007168 | 0.760753 | 0.755376 | -0.005376 | 0.729391 | 双退化 |
| cyp3a4_veith | AUPRC↑ | 1233（581/652） | 0.874750 | 0.871855 | -0.002895 | 0.878327 | 0.876280 | -0.002047 | 0.877173 | 双退化 |
| dili | AUROC↑ | 48（13/35） | 0.865934 | 0.846154 | -0.019780 | 0.868132 | 0.824176 | -0.043956 | 0.861538 | 双退化 |
| half_life_obach | Spearman↑ | 67 | 0.267340 | 0.210403 | -0.056936 | 0.290869 | 0.269156 | -0.021713 | 0.073700 | 双退化 |
| herg | AUROC↑ | 66（42/24） | 0.900794 | 0.903770 | +0.002976 | 0.903770 | 0.898810 | -0.004960 | 0.896825 | 不一致 |
| hia_hou | AUROC↑ | 58（48/10） | 0.958333 | 0.945833 | -0.012500 | 0.964583 | 0.950000 | -0.014583 | 0.966667 | 双退化 |
| ld50_zhu | MAE↓ | 1937 | 2.035667 | 0.663665 | +1.372002 | 1.872181 | 0.644886 | +1.227295 | 1.043589 | 双改善 |
| lipophilicity_astrazeneca | MAE↓ | 420 | 0.562459 | 0.533663 | +0.028797 | 0.558012 | 0.535947 | +0.022065 | 0.539647 | 双改善 |
| pgp_broccatelli | AUROC↑ | 122（61/61） | 0.913464 | 0.914270 | +0.000806 | 0.905671 | 0.902446 | -0.003225 | 0.905402 | 不一致 |
| ppbr_az | MAE↓ | 279 | 22.327195 | 11.595599 | +10.731596 | 25.923121 | 11.363475 | +14.559646 | 20.831835 | 双改善 |
| solubility_aqsoldb | MAE↓ | 2940 | 6.117044 | 1.473620 | +4.643425 | 6.278395 | 1.565136 | +4.713259 | 11.113364 | 双改善 |
| vdss_lombardo | Spearman↑ | 113 | 0.331540 | 0.269795 | -0.061746 | 0.335928 | 0.369820 | +0.033892 | -0.016927 | 不一致 |

44个配对中27个有利、17个不利；去掉缺after的BBB s46，变为26/43个有利。这个计数是描述，不是44个独立试验的二项检验：同任务同Valid行、不同任务间可能相关，且候选已被Valid选择。两seed的范围不能转成可靠置信区间或显著性声明。Valid总计11735任务行也不是11735个独立跨任务样本。[本轮派生；E-SCORES, E-MINI22]

**必须同时看相对控制和历史锚点。** Bioavailability的F010双胜当前H0，却仍低于Mini22；CYP2C9/2D6 substrate同样没有恢复历史Mini22水平。Half-life的F010双输H0，但两配置都远好于旧Mini22；VDSS也有类似历史改善但当前不稳定。CYP2C9 Veith和lipophilicity的当前增益较小，不能仅因正号就称重大突破。训练历史、seed、头和实现差异仍在，不能由历史值反推出因果。[E-MINI22, E-SCORES]

### 1.3 旧24、旧28与新86的结论变化

旧24提供六任务H0及其他头/优化探索，旧28新增F001/F010；它们不是这次完整22任务的替代。旧28中lipophilicity、BBB、hepatocyte、LD50、Solubility在44/45双seed F010胜H0，CYP2D6 Veith一升一降。新46/47保留lipophilicity、hepatocyte、LD50、Solubility的双改善；BBB变成不一致并叠加缺after限制；CYP2D6 Veith新两seed转为双改善，但不能删除旧44/45反例。旧“六项替换其余16项Mini22”的约45.43混合推算，不是这次全22实测，不能当独立重复。[E-OLD28, E-PROGRESS, E-CLAIMS]

原Mini22冻结基线有质量限制；当前缓存复用与新头改善应独立于旧运行失败、准备修复、监督进程退出状态保存。历史42个proposal/84计划fit不能当已经执行；Caco2后续六项是真实已完成的损失探索，不能说“损失从未试过”。本轮没有沿未准入旧真值文件下钻，故不为Caco2重新声称逐样本残差结论。[E-HISTREG, E-PROGRESS, E-ADOPTION, E-POLICY]

### 1.4 为什么约46不等于全面泛化提升

主控接受的本地推断归一化结果如下；归一化公式及官方AP等价均未最终确认。因此以下值只能作项目内敏感性分析，不是官网隐藏榜分或赛事得分预告。[E-CONTROLLER, E-SCORES]

| 口径 | H0 s46 | F010 s46 | H0 s47 | F010 s47 |
|---|---:|---:|---:|---:|
| 全22 | 42.747790 | 46.001601 | 43.225989 | 46.046595 |
| 去BBB共同21 | 42.447525 | 45.832507 | 42.952642 | 45.908061 |
| 再去LD50/Sol共同19 | 45.145892 | 46.394306 | 45.637768 | 46.509910 |

本轮没有重新评分。只把已发布归一化任务差值相加：LD50、PPBR、Sol在46分别贡献24.753751、14.015285、22.610991个任务归一化点；47分别23.960623、17.169059、21.532463。除以22后与全22净增益比较，得到85.75%和100.98%的贡献率。超过100%并不矛盾，表示其余任务合计抵消了一部分收益。去三项的19任务平均改善为+0.537043和−0.032043；去BBB后18任务为+0.539144和−0.033241。它与共同19仍改善的已验结论并不冲突，后者保留了PPBR。[本轮派生，`derived_checks.json`]

反证检查：这三个任务是看完结果后挑出的，分析本身有选择性，不能把剩余任务当新独立验证集；换归一化公式会改贡献比例。即便完全不用推断公式，原始指标仍有5个双退化和7个不一致，足以否定统一推广。因此下一步不依赖未确认总公式才能成立。

### 1.5 机制：数学上保留信息，训练上改变条件

实际缩放为：`d0_j = 1 if std_fit32_j < 1e−8 else std_fit32_j`；F010使用`d_fj=max(d0_j,0.01)`，常数维仍分母1。均值和标准差仅来自内部fit、ddof=0，特征统计float32。不是clip变换后的特征，也不是删除低方差维度。[E-SCALER, E-DATAIO]

在精确算术下，令`z_H=(x−μ)/d0`、`A=diag(d0/df)`，则`z_F=A z_H`。A是正且可逆的对角矩阵。对于首层权重W，令`W_F=W_H A⁻¹`、偏置不变，可得到相同的首层激活，从而相同网络函数。**所以仅改变floor不降低理论函数表达能力，也不自动删除噪声信息。** 这是代码定义上的代数推导，不是未经运行的实验结果。

实际训练依然可能不同：相同seed产生相同数值初始化，不代表两种输入尺度下相同初始函数；梯度、AdamW的有限步轨迹、权重衰减、非线性、float32误差和早停可能全部不同。不能把AdamW的decoupled decay简单等同精确L2目标，也不能因其自适应步长就宣称完全尺度不变。小标准差下的异常放大与目标幅度失控是有根据的数值假设，但“哪几维有问题、是否化学噪声、哪行预测错”尚未识别。[E-TRAINER, E-SCALER, E-HEADS]

五个MAE任务全部改善，与缓解幅度/优化脆弱性相容；Spearman和AUROC/AP关注排序，单纯对最终预测作正仿射变换并不改变排序。但这里缩放发生在输入，网络重新训练，排序也可变化。不能用指标不变性否认真实排序改善，更不能把指标家族与任务数据、loss分布的混杂当成因果分解。

| 竞争解释 | 当前直接支持 | 反证/混杂 | 最小可检验后续 |
|---|---|---|---|
| H1：近常数维放大造成优化病态 | 实现有floor，MAE大幅改善；旧异常分数 | F010不删除信息；分类仍退化；尚未逐维归因 | A补F001；C低lr；D-PRECISION/REPARAM条件储备 |
| H2：当前MLP容量/正则与尺度耦合 | 约52.48万头参数；dropout固定.1；小Valid任务不稳定 | 单看样本小不能证明过拟合；head仍可能必要 | B1无dropout MLP、B2线性，两个floor共同seed |
| H3：loss与外部指标不一致 | 回归均MSE，即使外部MAE/Spearman；分类无权重BCE | 改loss未必提升；历史Caco2已试过一些损失 | L的twice-Huber/温和权重；保留原loss控制 |
| H4：内部stop不代表分布外泛化 | DILI内部更高、Valid更低直接反例 | 也可能是stop噪声或选模偏差，不能唯一归为scaffold shift | S固定train-only结构压力，D-STOP储备 |
| H5：只是不稳定seed/Valid选模 | 7任务方向翻转，历史seed响应改变 | lipophilicity等跨历史方向保留；不是全是噪声 | 同seed对照完整报告，条件新seed，不挑最好seed |
| H6：新表示比调头更重要 | 部分任务所有当前头仍低于Mini22历史；单表示可能有瓶颈 | 历史值并非新表示证据；其他资产未ready | N/M固定面板，等预算、独立冻结资产fixture |

### 1.6 定向原件交叉核验，不重复整批评分

**DILI s46**：同内部划分哈希`2778b33524d12ee485cd763f7772a4672e77bcd7dd087e86acbec0899b57c346`。F010 best epoch15，内部AUROC0.9210526，23epoch停止、69steps；H0 best23，内部0.8195489，31epoch、93steps。外部Valid却是F0100.8461538 < H00.8659341。这是“内部停得更好≠外部更好”的实际反例，不是损失曲线代替质量分。[E-DILI-F, E-DILI-H, E-SCORES]

**PPBR s46**：H0 best11、内部MAE10.246688、19epoch/266steps；F010 best42、内部MAE9.197728、50epoch/700steps，外部MAE22.327195→11.595599。内部只改善约1.05、Valid约10.73，提示尺度与分布敏感，不能在无残差准入下断言离群样本数量。best42＋patience8刚好50，不能据结束于50就认定被max_epochs提前截断。[E-PPBR-H, E-PPBR-F]

**Half-life F010 s46**：best7、内部Spearman0.579678、15epoch结束，Valid0.210403。尚未读取配对H0的完整内部曲线，不能凭此给出同任务stop差值归因。[E-HALFLIFE-F]

CYP也不能统一解释。CYP3A4 substrate和Veith均双退化，2D6两端点新两seed均改善，2C9 substrate混合而Veith双改善。端点、数据、指标不同；即使阳性较少可能增大AP波动，CYP3A4 Veith相对均衡仍退化，2D6 Veith更不均衡却改善，已反对“全由类别不均衡决定方向”。在DILI Valid13正/35负、HIA48正/10负上，一次无并列正负样本排名对翻转的AUROC增量分别约1/455、1/480；存在tie时可有半步。此处只说明分辨率，不设统计或业务阈值。[E-MINI22, E-SCORES；本轮算术]

**Q1结论**：局部配对效果可信到既有主控准入范围；全任务统一获益被否定；优化/数值修复有证据相容但未识别单一机制。真正影响下一步的是任务异质性、头/尺度交互和内部验证的代表性，而不是再重算86分数。

<a id="Q2"></a>
## Q2．逐任务行动与参数选择

当前22任务缓存和H0/F010接口已实跑，无须再建“16任务零fit接入”关卡。新任务使用同版本缓存仍需本次dispatch绑定任务/分区/row_index，这是增量身份检查，不是重新全库编码或冻结审计。[E-INTERFACE, E-AUDIT64]

以下优先级是研究信息价值，不是未经确认的赛分权重。“保留F010”指保留候选和产物，不是自动正式提交，也不按Valid选最好seed；“保留H0”同理。

| task | 下一步类别 | 确定路线 | 理由与限制 |
|---|---|---|---|
| ames | P1／混合 | A补F001；大档N比较冻结表示 | 当前差值很小且两seed反号，先不更换默认。 |
| bbb_martins | P0／混合+证据限制 | R前瞻H046；A补F001 | 旧after缺失不可补写；同主机新对照服务未来比较。 |
| bioavailability_ma | P1／双改善 | 保留F010；大档N表示面板 | 仍低于Mini22，floor局部胜出不等于任务已解决。 |
| caco2_wang | P1／双改善 | 保留F010；B/C容量与优化；L Huber | 已做历史损失试验，只有当前fit/split/尺度不同才构成新比较。 |
| clearance_hepatocyte_az | P1／双改善 | 保留F010；大档N表示面板 | 历史44/45与当前46/47方向保留，幅度仍seed敏感。 |
| clearance_microsome_az | P0／混合 | A补F001；条件预测分歧 | 不能从同为clearance把hepatocyte结论直接移植。 |
| cyp2c9_substrate_carbonmangels | P0／混合 | A+B/C+L权重+S结构压力 | 大幅反号，Valid仅12正例，且低于历史基线。 |
| cyp2c9_veith | P1／双改善 | 保留F010；大档N表示面板 | 小改善，不用未经校准的“显著”阈值；与substrate分开。 |
| cyp2d6_substrate_carbonmangels | P1／双改善 | 保留F010；L温和权重 | 当前胜H0但低于Mini22，不单因正号停止研究。 |
| cyp2d6_veith | P1／双改善但历史混合 | 保留F010；L权重；盲分歧/seed平均 | 旧44/45反例仍保留，不追溯改写成一直稳定。 |
| cyp3a4_substrate_carbonmangels | P0／双退化 | 保留H0；A补F001 | 指标AUROC，与Veith AP不能直接混平均。 |
| cyp3a4_veith | P0／双退化 | 保留H0；A+B/C | 较大Valid和相对均衡仍退化，挑战“只是小样本”解释。 |
| dili | P0／双退化 | 保留H0；A+B/C+S | 内部stop反例最直接，适合容量和结构压力对照。 |
| half_life_obach | P0／双退化 | 保留H0；A+B/C | 两当前配置仍远优于旧Mini22；不要为回退到Mini22而删除新证据。 |
| herg | P0／混合 | A补F001；盲分歧/固定seed平均 | 66个Valid且差值小，先共享控制，避免大网格适配。 |
| hia_hou | P0／双退化 | 保留H0；A+B/C | Valid仅10负例；训练权重仍只能用fit类计数。 |
| ld50_zhu | P1／双改善 | 保留F010；L Huber | 极大幅度改善，优先尺度诊断而非假定普适表征突破。 |
| lipophilicity_astrazeneca | P1／双改善 | 保留F010；L Huber；N表示 | 跨历史方向较一致，可作为新表示稳定锚点。 |
| pgp_broccatelli | P0／混合 | A补F001；盲分歧/seed平均 | Valid类平衡仍混合，反对纯类比例解释。 |
| ppbr_az | P1／双改善、机制锚点 | 保留F010；B/C+L+S | 均分贡献大，内部/外部改善幅度不同，适合竞争假设。 |
| solubility_aqsoldb | P1／双改善 | 保留F010；L Huber；N表示 | 大幅改善但仍非hidden-test证明；跨主机历史限制保留。 |
| vdss_lombardo | P0／混合 | A+B/C | 相对旧Mini22明显进步但当前floor反号，优先头/优化解释。 |

### 2.1 为什么不是更大MLP或更多seed优先

现有2048→256→1头有524801个参数；线性带偏置头仅2049个。这个数量是结构直接计算，不是容量不足/过拟合证明。B面板保留退化任务、一个不稳定AP、一个不稳定Spearman，以及两个已改善MAE作正向锚点，避免仅在失败任务上筛选后误称一般规律。先做dropout0 MLP，再用同dropout0线性头，避免“线性胜出”同时混入去dropout的解释。架构改变仍会改变参数化和随机数消耗，因此只推断整体头结构因素，不把结果归因于某个具体隐藏单元。[E-HEADS；本轮设计]

新seed48/49当前validator不接纳；必须新代码准入，且旧/新候选要共同新seed。仅追加F010新seed而H0沿用46/47不能称配对确认。既有46/47用于新因素对比信息量足够，只有继续反号且当前分支不能解释时，再以最多4任务×2配置×2新seed＝16储备fit补充；不是无限加seed直到均值有利。

### 2.2 参数空间不是全笛卡尔积

`search_space.json`给18个方向，每个有来源、反证、历史、取值、组合约束、计数和停止门槛。现成grid只限源码真实枚举：hidden128/256/512、dropout0/.1/.3、lr1e−4/3e−4/5e−4/1e−3、weight_decay1e−5/1e−4/1e−3、seed44–47。max_epochs50/patience8固定；“0.2 dropout、seed48、80epoch/12patience、Huber、线性、任意floor”都不是现成字段。不能用width/wd或task-native metric替代真实接口。[E-DATAIO]

先A的三点尺度，再B头比较，再C固定当前dropout.1而仅lr变1e−4；不要把B1的dropout0同时带入C冒充lr单因素。只有关键对照失败才启用更宽容量/优化grid。D-STOP储备区分最大epoch预算和monitor选择，不在主197里偷加；D-PRECISION只改变统计dtype，不能修复缓存本身已丢失的精度；D-REPARAM等函数初始化需明确权重映射，不能口头称“同seed所以初始化相同”。

### 2.3 与外部指标匹配但不强求训练loss相同

现有回归是fit-only标准化Y上的MSE，内部stop在原Y尺度按MAE或Spearman，输出逆变换一次回原Y；分类为无权重BCEWithLogits，stop AUROC/AP，外部连续概率。L的twice-Huber在标准化残差r上定义`r² (|r|≤1), 2|r|−1 (|r|>1)`，保持小残差曲率与MSE一致，主要检验尾部梯度而不是意外全局缩小loss。早停指标与预测尺度保持原定义，不把换loss同时变更选模规则。[E-TRAINER；本轮设计]

分类权重由fit计数确定：正类权重`clip(sqrt(nneg/npos),.25,4)`、负类1，并以fit平均权重归一化loss；遇fit缺某类则该分支不可估并停止，不用Valid补权重。总体最优加权概率`q=w p/(1−p+w p)`是p的单调变换，所以理想排序本身不因加权改变；AP改进只能来自有限数据/优化/正则等效应，需以未加权控制检验，不能把权重当AP提升保证。类别阈值、F1调参均不进入本轮。

<a id="Q3"></a>
## Q3．冻结底座、经典特征、新模块与集成如何排序

### 3.1 当前资产状态与候选来源

下表区分“科学上有研究依据”和“此项目已可运行”。只有CheMeleon现有22任务接口/cache已准入。GLM、DeepSeek、Qwen是执行角色；Pro和Astra是研究角色，均不列为分子编码器。新表示的论文或官方benchmark即便更高，也可能使用fine-tune、其他分区/数据和更大模型，不能直接成为当前冻结约束下优越性的证据。[E-ASSETS, E-ORIGINAL-ASSETS]

| scientific_asset_id | 独立模型角色与研究依据 | 本地准备度/关键未知 | 本轮顺序与可证伪候选 |
|---|---|---|---|
| chemeleon | 冻结分子图表示，官方支持指纹提取；当前2048维checkpoint SHA已锁定 | 22任务ready；生产者/消费者环境差异已登记 | 主线A/B/C/L/S；不更换现有encoder参数/buffer |
| minimol | Graphcore MiniMol，官方512维SMILES表示接口，预训练模型与任务头分开 | 旧准备下载404/idle不是质量失败；local package/revision/checkpoint SHA未准入 | 大档N：6任务×2seed＝12；无参数更新提取512维，禁止默认为已装好 |
| molformer_10pct | IBM MoLFormer-XL-both-10pct，masked-LM冻结pooler表示768维 | 旧off-root运行边界失败保留；当前未接入；不是完整全数据XL模型 | 大档N12；拟议上游revision361063d0…，deterministic_eval=True；本地权重SHA仍待准入 |
| classical_features | Morgan等不训练分子特征，非执行LLM | 新生成/拼接接口未准备；经典模型正式参赛资格另核 | M12：CheMeleon2048＋Morgan2048；比纯经典head先保留明确合规主表示 |
| small_dmpnn_scratch | 从随机初始化学习的新分子预测模型，不是获准预训练encoder | 当前无实现、额外训练预算/模型资格需登记 | 储备16fit；不可称免费复用encoder，也不以旧Harness要求强制取代当前路线 |
| tabpfn26 | 表格上下文预测器，不是分子encoder；可消费冻结特征 | 官方2.6模型许可标研究/非商业/非生产限制；本地资格、上下文与资源未核 | 储备8个ICL配置，不等同8个SGD fit；暂不进主矩阵 |
| kpgt | 官方知识引导图Transformer，图+描述符/指纹知识预训练 | checkpoint、环境、特征出口、local SHA未接入 | 独立储备8fit；表示必须在冻结前提下取出，不能借其fine-tune流程更新底座 |
| unimol | 官方Uni-Mol分子3D表征，CLS/atomic输出可分离 | 构象生成、氢处理、原行全覆盖和缓存费用未验证 | 储备16fit：1/3构象pooling因素；不能删难分子或把构象当新增标签行 |
| smi_ted | IBM SMI-TED light encoder，可从SMILES提取表示 | 代码/权重/长度覆盖/环境未准入 | 储备8fit；只用encoder，不使用生成器产生新样本 |
| mole | 原资产别名需与明确论文/模型谱系绑定；本轮查Recursion MolE官方仓库 | 官方仓库预训练下载处仍TODO；不能确认它就是旧本地别名所指权重 | 储备8fit但blocked；不用scratch初始化假冒预训练MolE |

来源：[X-CHEMELEON, X-MINIMOL, X-MOLFORMER, X-MOLF-CONFIG, X-MOLF-REV, X-KPGT, X-UNIMOL, X-SMITED, X-MOLE, X-TABPFN, X-TABLICENSE]。各来源实际阅读范围见登记；没有下载/加载任何模型。对原资产调研报告的某些本地路径未解析到可读精确公开对象，仍为“未读/未解析”，不是报告不存在。

MoLFormer固定候选的官方配置是12层、768维、max positions202，模型卡说明预训练长度过滤与长分子未充分测试。这里保留原始Drug和原行，不复制其过滤规则；准备fixture须逐行确认完整输入覆盖，不默许tokenizer截断成另一分子。SMI-TED也要明确长度/解析策略。Uni-Mol的构象失败不得通过删除样本或补标签掩盖。冻结不仅requires_grad=False，还包含buffer状态、eval模式、optimizer排除及前后身份；未就绪时矩阵保持blocked_assets。[X-MOLFORMER, X-MOLF-CONFIG, X-SMITED, X-UNIMOL；E-RULE]

### 3.2 资源分配与替代策略

**推荐先用现有缓存检验机制，而非先换大底座。** 优点是无需重复编码、控制连续、能解释当前退化；反对意见是现有表征可能已成为瓶颈，只调头会过度适配Valid。因此大档把6个明确任务交给MiniMol/MoLFormer/Morgan互补面板，且不要求小档所有任务改善才准入。新表示效果按同任务/同split/同seed比较，但输入维度使首层参数数不同，属于representation bundle，不能把任何收益全归给encoder本身。

为什么N面板不是只挑最差任务：ames/bioavailability体现小收益或历史落后；hepatocyte和lipophilicity是较稳定正向锚点；CYP2C9 Veith是AP端点；Solubility是幅度脆弱回归。它们让新资产在分类/排序/MAE和稳定/不稳定背景下受检。主中档已覆盖12个退化/混合及两个机制锚点，综合大档新训练覆盖全部22任务，但不把“全覆盖”当每方向必须22任务的理由。

**集成不要求先有两种编码器。** 同CheMeleon两个seed的固定0.5平均可以研究，前提是两个输出各自合规、同row_index且已回到相同预测尺度。先12个未解决任务×H0/F010各一个seed平均＝24个新增评分输出、0训练fit；其余10任务追加20个评分输出另记。不能平均两个AUPRC数值代替重新评分，不能从预测分歧推出谁正确；任何新Valid评分仍计入选择暴露账。不同底座集成先固定等权，learned stacking仅officialtrain内部OOF、另需新代码和预算，禁止用Valid标签学权重。[E-ROOT-REVIEW, E-METHOD, E-PREDINDEX]

**Q3的剩余缺口**不是“没有方向”，而是部分原调研对象、精确local权重版本、长度/构象覆盖和许可尚未落实。它们阻断相应资产执行，不阻断当前CheMeleon研究；本题在review中标partial，避免把上游论文阅读写成当地资产验收。

<a id="Q4"></a>
## Q4．连续多批、确定矩阵、预算与停止条件

### 4.1 三档规模来自信息对照，而非照抄86

| 档位 | 确定新fit上限 | config_only / new_code / blocked_assets | 直接新增训练任务数 | 主要用途 |
|---|---:|---|---:|---|
| 小 | 25 | 25 / 0 / 0 | 12 | 所有5退化+7混合补F001，加BBB前瞻对照 |
| **中（推荐）** | **89** | **57 / 32 / 0** | **14** | 小档＋无dropout MLP/线性在两floor的受控比较 |
| 大 | 197 | 89 / 72 / 36 | 22 | 中档＋lr、loss、结构压力、新表示/经典特征融合 |

所有档位完整分析22任务；“新增训练14任务”不等于其余8任务被遗忘。新代码/资产分支只有独立fixture和主控授权后执行。跳过的fit不自动转给其他分支。99个proposal对象展开197个model-seed fit；同一个proposal同时属于多个档位只计一次。

### 4.2 首批和后续矩阵的精确定义

默认split为`train-rawdrug-group-s43-stop10__external-official-valid-v6`（本方案描述性ID，不冒充原文件UUID），其真实runner字段是`{method:"raw_smiles_group_shuffle", seed:43, stop_fraction:0.1}`；model seeds46/47。每个task/config已单独展开于JSON，运行ID为新拟定而非历史run名。

| 阶段 | task集合与配置 | 新fit | 现有/新增控制 |
|---|---|---:|---|
| R | bbb_martins；H0；seed46；RTX4090；完整before/after | 1 | 未来对照；不抹去历史H046缺after |
| A | ames、bbb、microsome、cyp2c9_substrate、cyp3a4_substrate、cyp3a4_veith、dili、half_life、herg、hia、pgp、vdss；F001；46/47 | 24 | 同task/seed H0与F010；BBB46以R作未来有效控制 |
| B1 | dili、hia、half_life、cyp3a4_veith、cyp2c9_substrate、vdss、ppbr、caco2；H0/F010；MLP256 dropout0；46/47 | 32 | 已有dropout.1同floor控制 |
| B2 | 同B1八任务/两floor/两seed；Linear(2048,1)含bias、dropout0 | 32 | B1同dropout0；保持loss/lr/stop一致 |
| C | 同B八任务/两floor/两seed；MLP256 dropout.1，lr1e−4 | 32 | 已有lr5e−4 dropout.1；不误用B1 |
| L-reg | caco2、ld50、lipophilicity、ppbr、solubility；F010；twice-Huber δ=1标准化Y；46/47 | 10 | 已有F010 MSE |
| L-cls | cyp2c9_substrate、cyp2d6_substrate、cyp2d6_veith；F010；fit-only温和权重BCE；46/47 | 6 | 已有F010无权重BCE |
| S | dili、cyp2c9_substrate、ppbr；outer结构split101/102；每split H0/F010；model46/47 | 24 | 包括12个新split H0，不能复用旧split43控制 |
| N | ames、bioavailability、hepatocyte、cyp2c9_veith、lipophilicity、solubility；分别MiniMol512/MoLFormer768；F010头；46/47 | 24 | 现有同task/seed CheMeleon F010，解释为表示bundle |
| M | 同N六任务；CheMeleon2048＋Morgan2048；F010用于CheMeleon块；46/47 | 12 | 现有CheMeleon F010；拼接整体效果 |

JSON使用完整task_id而非表内简称。每个对象有全部head字段、每seed真实config、loss/scale/stop/externalmetric、asset/checkpoint状态、preprocessing-refit、controlID、依赖和skip。准备/诊断不是训练proposal；条件选任务的储备只在search_space/conditional_followups，必须选定后由主控形成确定矩阵。

### 4.3 每种目标的尺度、早停和输出

BCE分类：原0/1标签、raw logits上mean BCEWithLogits；stop AUROC或本地AP最大化；输出sigmoid概率而非硬标签。加权BCE仅改loss系数，stop和外部指标不变。回归MSE/Huber都在每个inner-fit的Y标准化尺度训练；MAE任务stop原Y MAE最小化，四排序回归stop原Y Spearman最大化；输出逆标准化一次。新linear不把这些改成sklearn默认metric。内部best checkpoint重载，max50/patience8/min_delta1e−7不变。[E-TRAINER, E-FIXED-SCORER]

S结构压力：在官方train内以chirality-preserving canonical molecule/scaffold组构建outer20%（split seeds101/102），再在outer-train内取stop10%（seed43）。Murcko空scaffold的acyclic分子用canonical isomeric身份，解析失败保留原Drug分组并报告，不删行。组排序/洗牌/切分规则在JSON明示。每个inner-fit重新估计特征/目标统计；outer只评分，不参与earlystop或超参再选。若某split分类单类或组结构无法估计，则报告不可估并跳过，不能换seed直到结果有利。原始train/valid/test不移动、不清洗。它是预登记的结构压力测试，历史train曾参与训练，且候选已受Valid影响，不能宣称由此获得全新无污染最终测试集。[E-METHOD, X-TDC-SPLIT；本轮设计]

### 4.4 对照去重与共享编码

`controls.json`列88个已验比较槽位，其中87个可作完整冻结前提控制，BBB H046单列研究限制。它们不进入任何“新fit”总数。小/中/大实际引用47/55/71个唯一既有可用槽位，另有一个拟议BBB前瞻控制；B2共享B1结果，S的12个新H0已包含在24内，不在别处再加。跨阶段同task、资产/配置、split、seed完全相同才复用；不同dropout/新split/新目标不能假称等价。[本轮矩阵集合检查]

小/中档CheMeleon新增编码次数0。大档每个新冻结表示覆盖6任务×train/valid/test＝18个逻辑缓存分区；MiniMol18、MoLFormer18、Morgan18特征分区。它们是共享编码工作单位，不是测得的GPU call数；实际批量、可复用分子计算、walltime未测。任何计算级复用必须还原全部原行/分区，不能变成去重训练数据。多个seed/头/内部split共享同冻结原始表示，但每个inner-fit单独拟合统计。

### 4.5 周转成本与可判断预算

当前实测：六任务22项GPU作业进程寿命H100 41.7177秒＋RTX 367.2318秒＝408.9496秒；64项634.3196秒；合计1043.2692秒。这包含加载/推理等，不是纯GPU kernel。64项contract到science complete约6454.65秒；共享取回窗口1171.26秒只计一次，不能在两个包重复相加。主控/执行角色active和阶段窗口可能重叠，64角色`as_of`的7280.57秒还包含之前的3680.845秒，不能假称final walltime。[E-COST22, E-COST64, E-RETRIEVE22, E-RETRIEVE64]

430个原checkpoint约2.731GB逻辑字节、约2.489GB压缩，不应每次重复回传全部历史；新增回传以这次稳定科学产物为界，保留必要原件索引。评分计算本身约十分之一秒量级，不意味着准备、身份绑定、运输和交接可忽略。旧固定“每批1.9小时”或按训练fit数线性推全链路都没有当前证据。[E-RETRIEVE22, E-RETRIEVE64, E-ROOT-REVIEW]

使用公式：`T=P既有配置+P新接口+排队Q+新表示编码E+头作业J+取回/评分/交接H+新研究R−实际重叠`。以下是**建议资源分配区间，不是历史测量或完成承诺**：

| 档位 | warm准备h | 新接口工程h | 头作业span粗代理h | 取回/评分/交接h | 非重叠规划和（还缺未知项） |
|---|---|---|---|---|---|
| 小25 | .25–.75 | 0 | .069–.129 | .25–.75 | .569–1.629h＋Q＋R |
| 中89 | .25–.75 | 1–3 | .245–.460 | .5–1.25 | 1.995–5.460h＋Q＋R |
| 大197 | .5–1 | 3–8 | .542–1.017 | .75–2 | 4.792–12.017h＋Q＋R＋E_MiniMol＋E_MoLFormer＋C_Morgan |

J仅用当前两批9.91–18.59秒/fit进程span作粗代理，线性/新loss/新表示实际成本未经测量，不能写成已知GPU小时。新增编码/构象资源无依据则保留符号；在首个真实有信息量的已授权科学任务计时，不为每个已知小头多造pilot。准备可与A并行，实际应减去重叠；工程预算耗尽而接口未过fixture则该支停止，不自动扩预算。预登记分支运行期间不需每个头再问Pro；新研究耗时R只在科学review触发点发生，不能照搬旧Pro UI作为固定常数。

### 4.6 有边界的继续、失败和停止

A改善：保留候选及共同对照，完成选定B/压力测试，不直接推广22。A无改善或分母与已验配置完全相同：不扫密集floor；B/C区分头与优化解释。继续反号：如实标不稳定，先盲分歧/固定等权seed输出；新seed储备最多16fit，需新代码/额外登记，**不在197内**。所有B/C无可复现改善：停止当前scaler/MLP局部grid，考虑已准入的新表示，而不是继续无界调参。

任何冻结/标签/row identity失败只停依赖任务，保存worker和supervisor各自状态；不能用退出码一致性掩盖SLO/边界失败。新资产覆盖不完整，不删除难分子；资产分支停止，其他已ready方案继续。正常在预定阶段收齐后深评审；决定性反证、重要科学接口变更或方案穷尽才触发新研究，不以固定分钟或每个头触发。

<a id="Q5"></a>
## Q5．历史结论、反例及追加事件

`claim_events.json`给9条可归并追加事件：保留前一event ID、原命题、支持/反证、适用范围、当前状态及方向影响；不知道精确发生时刻写null，不能用归档时间代替。`issues.json`是本轮14个问题的增量投影，不声称替换主控全历史账本。[E-CLAIMS, E-PROGRESS]

| 历史状态 | 本轮处理 | 新事件/方向 |
|---|---|---|
| E-F010-UNIVERSAL已否定统一推广 | 保留10/5/7，追加贡献集中与任务家族模式 | PRO86-E-HETEROGENEITY / CONCENTRATION |
| E-MECHANISM仍未识别泛化因果 | 追加可逆缩放推导及DILI stop反例，不假称已证明某维噪声 | PRO86-E-INVERTIBLE / STOP-COUNTEREXAMPLE |
| E-86-BBB旧稳定结论缩小、缺after | 新前瞻对照不是旧产物追溯修复 | PRO86-E-BBB-REPAIR |
| E-86-CYP新两seed获益而旧有反例 | 按isoform/端点拆开，不合并为“CYP改善” | PRO86-E-CYP |
| E-GLM桥接64项完成 | 当前22接口已ready；停止过期16任务接入要求 | PRO86-E-READINESS |
| E-DINO只是方法启发、相关接口未实现 | 线性/分组/loss/分歧变为具体有界候选，不自动继承视觉收益 | PRO86-E-DINO |
| 旧Pro过度限制cross-batch/ensemble | 采纳有原件支持的纠正：控制可复用、同表示集成可研究 | PRO86-E-ROOT-CORRECTIONS |

旧009关闭，不重新挂到本批新run；旧准备失败/不完整测试、跨目录/监督边界问题保留，不因当前分数好改成通过。GLM/DeepSeek/Qwen的具体执行责任只按原件归属，不能把主控本地Python/schema/tar故障全推给执行模型。研究建议未实施、代码准备失败、训练失败、稳定产物准入、科学效果失败是不同状态；原件支持哪一种只写哪一种。[E-HISTREG, E-ROOT-REVIEW, E-OPS]

新的方向不是无依据重来：A借现成F001补本轮缺失对照；B线性来自共同纲领且实际未实现，故先新接口；L不是否认历史Caco2已有损失，而是在当前同fit/split/scaler下规定一种受控鲁棒目标；S针对已读rawDrug分组不足以代表规范身份/结构分组，但不能据此判定官方分区泄漏；N/M针对真实资产瓶颈，而不是执行LLM选型。所有下一研究触发点绑定可改变选择的结果，而非篇幅或任务数。

<a id="Q6"></a>
## Q6．真正缺什么、现有材料如何最小补齐

### 6.1 本轮实读、继承和未读严格分开

本会话按入口、共同规则/纲领、当前结果、完整历史导航、真实资产/接口、问题分支的次序阅读。来源登记有69项，其中索引和大JSON只标实际范围，不宣称已读其指向的全部原件。对86评分、既有冻结、输入身份、运输回执继承主控验收；本轮只做新差值/类别/贡献率/矩阵/成本算术，并定向阅读DILI/PPBR/half-life训练原件。未运行归档Python，未读取模型/pickle、逐行Y或残差。没有实际可调用的subagent委派工具，故实际subagent数为0；交叉核验来自不同原件与两种算术路径，不能冒充独立研究者票数。

输入manifest摘要仅按请求绑定，未独立获得并哈希其原始字节；这不是完整模型归档阻塞，也不能写“manifest独立验证通过”。代码化来源视图的文件名hash与其内部原source hash可能不同，来源登记明确两者关系；未提取到对象sha的包装文件保留null，不拿checkpoint或别的对象hash填充。对公开URI的Web读取成功不等于container DNS下载成功；失败只按实际路径/工具范围报告。

### 6.2 缺口分类与最小动作

| 缺口 | 真实类别、已经做什么 | 最小补齐与影响 |
|---|---|---|
| BBB原H046 after | 未记录；已读limits及22验收明确缺失 | 无法补写历史；R新完整run仅供未来质量对照 |
| 完整逐维scaler/梯度/曲线 | 部分原件已发布但本会话未逐份读；已定向读5训练对象、scaler源码 | 主控沿run index只读被选task的无标签统计，区分是否floor实际改变；不重算86分数 |
| 盲预测分歧/极端范围 | 存在明确blind-predictions索引；本轮只读索引/schema未加载CSV | 可在授权零fit阶段以task/split/row_index对齐，报告分位/相关/排序分歧；无Y不判谁错 |
| 训练类权重 | 当前fit类计数未在本报告计算，不从Valid推算 | 未来fit-only计数按确定公式生成并固化；缺类停分支 |
| 官方AP/总分公式 | 本地固定评分器已读；官方精确定义未确认 | 取官方正文/实现明确tie/AP/PR积分/聚合再映射；不阻断本地同口径差值 |
| 全生命周期Valid使用次数 | 现有正式task-score计数已登记，完整历史访问次数未完整记录 | 不从新聊天重置选择偏差；以后append exposure账，过去未知保留 |
| 缓存生产/消费环境等价forward | 身份/字节复用已验；新环境逐行前向等价未测 | 本轮不编码；不为重复审计强制重算缓存；若新接口需不同forward，则另行批准并针对该接口验收 |
| 其他底座精确本地版本/权重/许可/覆盖 | 当前readiness明确未ready；官方资料已查；部分旧研究报告公共对象未解析 | 精确resolve到registry对象、锁定local SHA、全行coverage fixture；只阻断对应N/M/储备 |
| 新loss/linear/structure接口 | 从未在本轮生产接口实现，不是文件读不到 | 按guide新代码，合成输入无参数更新fixture通过后主控登记训练 |
| 泛化机制与未来seed结果 | 现有汇总本来不能回答，需新实验 | A/B/C/S及有界seed储备；不伪造因果确定性/置信度 |
| 真实kernel busy、排队、新表示编码、新接口工时 | 部分从未测量；有jobspan/roleas_of/共享wall原件 | 用已授权真实新任务记录阶段时戳，未知项符号保留；不将span当kernel |
| 输入manifest原字节独立校验 | 本轮未获得独立原字节；精确source-index查找未定位目标，container网络DNS失败 | 仅运输绑定保留用户给定摘要，不猜URI不报告404；不重审1256对象 |

完整记录见`evidence_gaps.json`。本会话没有把“未尝试”写成“不可达”，也没有因读了索引就把每份原件设为read_full。新编码、训练等不属于本轮补齐权限；每项缺口只阻断依赖它的结论/方案。

### 6.3 无真值诊断的可检验含义

允许的诊断是：feature每维fit std/分母比率分布、非有限值、row identity；预测分位/极端幅度、跨seed/配置Spearman、分类概率或rank分歧。它们识别数值路径和候选互补，不是质量指标。不能给“最大误差分子”、残差切片、逐行答案或窄分组差分。搜索方向中建议最小组数30仅为待主控批准的隐私工程门槛，不是赛事规则，更不保证任何分组一定安全；必要时只交任务级无标签摘要。[E-RULE, E-METHOD, E-PREDINDEX]

所有主观优先级均有反证路径：floor没有稳定改善就停止加密floor；linear不胜不能推断encoder无用；新表示不胜不能推断模型论文无效；结构split反转只缩小适用域，不重新选择最有利split；freeze/row失败是无效产物而非质量反例。主控接收可归并的方向/issue/event和明确矩阵，而不是由研究者直接修改本地账本。

## 结论验收位置

Q1：本报告§Q1及派生检查；Q2：逐任务表、机制竞争表与search_space；Q3：资产表、原始官方来源与blocked矩阵；Q4：预算、逐proposal矩阵、guide、branches；Q5：历史表和claim_events；Q6：阅读登记、缺口分类和端到端成本。`review.json`逐题绑定这些位置，保留支持与反对证据。文件结构检查通过只能说明输送一致性，不能替代科学判断；当前仍不声称未参与调参数据上的提升已经被证明。

## 来源定位表

以下为本报告实际使用的精确来源入口；详细版本、原source哈希/视图哈希区分、阅读行段、工具证据在`evidence_registry.json`。`read_full_text`只指该对象全文，不意味着其链接的所有原件已读。动态上游页面用于研究出处，不自动构成本项目固定资产版本。

| ID | 精确来源 | 本轮实读范围 |
|---|---|---|
| E-START | [E-START](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/START_HERE.md) | full |
| E-METHOD | [E-METHOD](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/methodology/EXPERIMENT_DESIGN.md) | full |
| E-RULE | [E-RULE](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/common/rules.md) | full |
| E-SUMMARY | [E-SUMMARY](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/common/results-summary.md) | full |
| E-HISTORY | [E-HISTORY](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/common/history.md) | full |
| E-LIMITS | [E-LIMITS](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/common/limits.json) | full |
| E-DECISION | [E-DECISION](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/research/decision-contract.json) | full |
| E-RETURN | [E-RETURN](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/research/return-contract.json) | full |
| E-BRIEF | [E-BRIEF](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/research/RESEARCH_BRIEF.md) | full |
| E-ASSETS | [E-ASSETS](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/assets/readiness.json) | full |
| E-INTERFACE | [E-INTERFACE](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/assets/current-interface.json) | full |
| E-RESULTS | [E-RESULTS](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/current/results.md) | full |
| E-SCORES | [E-SCORES](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/current/all22-comparisons.json) | paired_comparisons L2303-L3052 full; aggregate and selected score/per_task sections; NOT all 88 run objects |
| E-PREDINDEX | [E-PREDINDEX](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/current/blind-predictions.json) | index entry/schema, first 54 lines; no prediction CSV contents read |
| E-RUNINDEX | [E-RUNINDEX](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/runs/index.json) | task/run navigation including selected DILI/PPBR/half-life objects; not every run original |
| E-PROGRESS | [E-PROGRESS](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/history/progressive-index.json) | full |
| E-CLAIMS | [E-CLAIMS](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/history/claim-events.json) | full |
| E-ADOPTION | [E-ADOPTION](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/history/proposal-adoption.json) | proposal adoption and current-matrix sections; not full historical objects |
| E-PREVPRO | [E-PREVPRO](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/research/previous-Pro-index.json) | full |
| E-DINO | [E-DINO](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/research/DINO_REUSE_ADDENDUM.json) | full |
| E-OPS | [E-OPS](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/operations/cost-and-failures.json) | full |
| E-GAPS | [E-GAPS](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/gaps.json) | full |
| E-RULEMAP | [E-RULEMAP](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/common/rule-originals.json) | full |
| E-SOURCEINDEX | [E-SOURCEINDEX](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/source-manifest.json) | targeted registered source/view entries only; find reading-contract/feature-distribution names did not resolve exact entry; not a full 22718-line read |
| E-Q1 | [E-Q1](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/questions/Q1.md) | full |
| E-Q2 | [E-Q2](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/questions/Q2.md) | full |
| E-Q3 | [E-Q3](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/questions/Q3.md) | full |
| E-Q4 | [E-Q4](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/questions/Q4.md) | full |
| E-Q5 | [E-Q5](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/questions/Q5.md) | full |
| E-Q6 | [E-Q6](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/questions/Q6.md) | full |
| E-CONTROLLER | [E-CONTROLLER](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/0479d220edcb14d608d302e85e387c0b0a48f50ef69e83d2ea43786c575ec3f3.json) | L0-L89 result acceptance, exact normalized aggregates, counts |
| E-AUDIT64 | [E-AUDIT64](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/426d5850ddba29a4a60fa9b9160ebd8cb73ea894d4a72283e4fb33213db33002.json) | full |
| E-AUDIT22 | [E-AUDIT22](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/446e738d16fbbfb20043d23b2912aa90c36fdbc29fdc79cc757a8688e46eeeca.json) | full |
| E-ROOT-REVIEW | [E-ROOT-REVIEW](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/efd428ad5395a506a7b019ef51d8ec3cfce037ac9917af14b24c752927b075d9.md) | full |
| E-HISTREG | [E-HISTREG](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/263d3b905953bc18c17956babb180ecb71f3d8e3a22ff528b40bc362b60caa6c.json) | records/navigation covering major experiments/failures; L0-L331,L368-L535; gap L332-L367 and end not claimed read |
| E-COST22 | [E-COST22](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/93df7d1bacfcd0e5e8e15977152a7bccbb6e188268d2adcc3d7893fe23b72ae8.json) | full |
| E-COST64 | [E-COST64](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/dbd898d865603496ddfb0dde45acc7ada8a0b3d05f35da1624d51d49c3c6c4c1.json) | full |
| E-RETRIEVE22 | [E-RETRIEVE22](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/7efcb63f22cb4feec72df0af21bc518a2ed36c4cef58e630c4be582a81c845d8.json) | full |
| E-RETRIEVE64 | [E-RETRIEVE64](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/cc85de8a688015c5e51473e2efbdac46f0597f77665236b909a22a6063b30bdb.json) | full |
| E-DATAIO | [E-DATAIO](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/9a7a4410a215f0eaf040252cef6b3d3aa8c0eef57a799508d88757bfe5d0a9db.py) | full |
| E-BRIDGE | [E-BRIDGE](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/7a4afd41ebdd08ad42533a7570a9a3daf8bf792391d88be9388645fb8f472f59.py) | header/source trust/environment requirements L0-L62; acceptance from separate E-AUDIT64 |
| E-POLICY | [E-POLICY](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/eaa891c243aa95bc77d5e7958d59ba9adcfd1ad7d3aa075d7ea2131dcb2971ea.json) | policy L0-L88; narrower current evaluation scope takes precedence |
| E-DILI-F | [E-DILI-F](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/b7b53d508497cfac90ef4772c20f07d4cccb32565ed1f9a862f6bcce39c0e721.json) | training config/history/best reload L0-L423; row/cache summary L541-L625; acceptance L665-L706; no per-row labels |
| E-DILI-H | [E-DILI-H](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/ad55f831e0d25e18022fef143b0bbbcd8c116809d722eb86f69d0949d5354abd.json) | best/last/internal-stop/optimizer aggregate L455-L587 |
| E-PPBR-H | [E-PPBR-H](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/7d42d99e46e60a565fee83634e3768e9932f095aee949db9ef0b92bae4cd9aa6.json) | best/last/internal-stop L296-L322 |
| E-PPBR-F | [E-PPBR-F](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/8a6af03ed4067356b3b76e36a7cb3f2b5b7062c9b6f3464eb8cc489f9304d200.json) | best/last/internal-stop/training L728-L855 |
| E-HALFLIFE-F | [E-HALFLIFE-F](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2/experiments/breadth22-confirm86-20261102/parallel-research/evidence/8e060ffd5829c1d32caad13bcd1ea711a6028264e47c5466286900207689e1de.json) | best/last/internal-stop L226-L265 |
| E-TRAINER | [E-TRAINER](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f172e864efbfcb33837bbdd28768b0b4f7ca03a7/experiments/scaler-six28-20261102/evidence/objects/aa3fbc1a9b29a043f4bac3631cfb3244e4efbcab71636087ad679134edd9d4e5.py) | L0-L239 validator, optimizer, learning/early-stop/reload source; not executed |
| E-SCALER | [E-SCALER](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f172e864efbfcb33837bbdd28768b0b4f7ca03a7/experiments/scaler-six28-20261102/evidence/objects/98497dc52267fcb3b868cba2349232c7f2b3f171416a5f33ef7e991cf04fb929.py) | raw cache contract; L175-L423 scaling/statistics/target logic; not executed |
| E-HEADS | [E-HEADS](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/650862671076f7b40b5ca776b2a03f3116cb0df5dcb79d62d1a8f5adabfbef64.py.txt) | L0-L83 MLP/loss/AdamW/postprocess source |
| E-FIXED-SCORER | [E-FIXED-SCORER](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/host-scoring/fixed_metrics.py.txt) | L0-L65 local MAE/AUROC/tie-group AP/Spearman source; not executed |
| E-OLD28 | [E-OLD28](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/f172e864efbfcb33837bbdd28768b0b4f7ca03a7/experiments/scaler-six28-20261102/current/comparisons.json) | metadata/old normalized mapping and paired section L703-L1041; selected groups; not every object |
| E-MINI22 | [E-MINI22](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-764562710384d47e.json) | all 22 task score/count summaries L0-L351; not binary predictions |
| E-ORIGINAL-RULE | [E-ORIGINAL-RULE](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-a95c8473d1769a29.json) | public rules snapshot L0-L98; user-confirmed freeze sourced separately |
| E-ORIGINAL-MAP | [E-ORIGINAL-MAP](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-e275f0ef9a4955741956.md.txt) | full |
| E-ORIGINAL-ASSETS | [E-ORIGINAL-ASSETS](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-3d003c99381806758257.json) | full |
| X-DINO | [X-DINO](https://github.com/grapeot/dinov3-classifier-skill/blob/45f5bb6336470ebd534b2e81f1684366b63fd8b2/skills/skill.md) | frozen probes/grouping/representation sections L170-L371; project adaptation fully read E-METHOD |
| X-CHEMELEON | [X-CHEMELEON](https://github.com/JacksonBurns/chemeleon) | README sections/model provenance; no checkpoint download |
| X-MINIMOL | [X-MINIMOL](https://github.com/graphcore-research/minimol) | README interface 512-d, package/model role, evaluation limitations L188-L234 |
| X-MOLFORMER | [X-MOLFORMER](https://huggingface.co/ibm-research/MoLFormer-XL-both-10pct) | model card L94-L155: 10pct, feature extractor/pooler, training coverage; not finetuning execution |
| X-MOLF-CONFIG | [X-MOLF-CONFIG](https://huggingface.co/ibm-research/MoLFormer-XL-both-10pct/blob/main/config.json) | complete displayed JSON L118-L150 |
| X-MOLF-REV | [X-MOLF-REV](https://huggingface.co/ibm-research/MoLFormer-XL-both-10pct/commit/361063d0ad524ef77cf39b08469f6be770dc550f) | commit identity/tokenizer changes L84-L113; not entire diff |
| X-KPGT | [X-KPGT](https://github.com/lihan97/KPGT) | README LiGhT and descriptor/fingerprint dependencies L182-L245 |
| X-UNIMOL | [X-UNIMOL](https://unimol.readthedocs.io/en/latest/quickstart.html) | UniMolRepr and CLS/atomic output API L41-L58; no MolTrain call |
| X-SMITED | [X-SMITED](https://huggingface.co/ibm-research/materials.smi-ted) | model family and light feature-extraction interface L113-L132,L149-L259 |
| X-MOLE | [X-MOLE](https://github.com/recursionpharma/mole_public) | README L185-L280, checkpoint section says TODO; proposed explicit lineage, registry alias not proven |
| X-TABPFN | [X-TABPFN](https://huggingface.co/Prior-Labs/tabpfn_2_6/blob/main/README.md) | 2.6 model card/license scope, not a molecular encoder |
| X-TABLICENSE | [X-TABLICENSE](https://huggingface.co/Prior-Labs/tabpfn_2_6/blob/main/LICENSE) | primary license search result only; not a full legal interpretation |
| X-TDC-SPLIT | [X-TDC-SPLIT](https://tdcommons.ai/functions/data_split/) | generic split docs; not evidence of this competition official split or leakage |
