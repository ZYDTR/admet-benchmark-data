# 薄覆盖端点的机制与判别实验

**Request:** `admet-pro-thin-endpoints-20261103-006`  
**输入截点:** `2026-11-03T14:42:51.342353+00:00`  
**请求 manifest identity:** `7d2c9fabaa18f80aba0ae7cf28e19f860bfefa55b990efd924ae35d2cc18442b`  
**共同 manifest SHA256:** `7137ed63416654ad2a56808ed4b5378940a47abbee17625211b43cebbf5bd3ed`  
**固定 commit:** `b9b8e9659ddb2138ffe37b5f23a5a4f739ba22cb`  
**阶段:** 探索性科学设计；没有训练、推理、模型加载、checkpoint下载、标签获取或评分权限。

## 0. 决策摘要

- “薄覆盖”指 Pro005 对五端点没有新增 task-level 机制实验，不代表端点分数低、数据质量差或预测能力差。已知结果混合：BBB floor收益/seed稳定性混合；hERG floor方向不一致；Pgp floor混合且部分盲预测近同；CYP2C9 inhibition 的 F010 两seed小幅支持但没有native确认；CYP2C9 substrate 的 weighted BCE 与 Morgan 固定小矩阵未支持替换，Mini表现混合。
- CYP2C9 inhibition (Veith) 与 CYP2C9 substrate (Carbon–Mangels) 是不同readout、不同数据来源、约一个数量级的数据规模差异。前者是重组酶生化抑制筛查；后者是跨六篇文献汇总的底物/非底物注释。抑制不等价于被代谢。
- 机制上有来源支撑的可检验缺口：BBB的电离/极性/被动渗透与外排耦合；hERG的多药效团、多模式结合及碱性/疏水相互作用；Pgp inhibition的膜分配、药效团与protocol异质性；CYP inhibition的重组酶/探针/发光readout与阈值；CYP substrate的productive binding、代谢位点与跨文献异质性。以上均为竞争解释，不是逐行已知协变量。
- 高信息优先候选：Pgp固定表示×理化描述符增量比较（Morgan/CheM/MiniMol × 无/有预先固定RDKit描述符）。Broccatelli原始研究明确使用MIF、药效团和膜分配性质，故可用既有表示先检验简单2D proxy是否补足。它不是当前可执行任务：五任务准确train-internal partition及原行绑定未在当前共享split register中出现，必须由数据/partition owner提供已验收train-only split manifest。不能自行编造split或借用其他任务split。
- hERG/BBB/CYP2C9 inhibition作为第二层有限矩阵；CYP2C9 substrate不先做跨任务loss迁移，应先取得独立split/label lineage并检验三种现有表示。SMI/KPGT/几何模块只作后续有条件alternative；不能修改在途SMI8/HEPOS40/SOLCTX4/GEO32。
- 新score cohort由指定score owner在原train内部、按完整任务行集合一次性产出。本研究未取得逐行预测/标签/残差，未计算任何群的实际人数或收益。重复Valid不是独立证据；AP不默认等于官方AUPRC。

## 1. 阅读覆盖、边界与证据身份

实读：本请求START_HERE、decision-contract、PRO_PROMPT、input-manifest；共同CURRENT_STATUS、完整EXPERIMENT_DESIGN、RESEARCH_SKILL、evidence-reuse、scoring-and-publishing、SOURCES；Pro005 analysis、task22_actions、next_experiments（定向检索）、scientific_assets、diagnostic_requests、fit_identity_register、split_register；TDC ADME/Tox与benchmark overview；Martins BBB原始论文摘要；Broccatelli Pgp原始论文及数据方法；Veith CYP原始论文与PubChem AID1851 protocol；Carbon–Mangels数据说明、Ahlström CYP2C9 substrate实验；hERG Wang数据论文及hERG多源异质性研究。

未能做到：没有可调用的真实研究subagent，因此没有虚构并行；机制、测定、方法来源交叉核对。容器网络DNS失败，无法取得上游原件字节或重打包完整原件。ZIP含六正式文件、来源注册表、固定链接/读取状态和request身份，**不声称包含全部上游原件字节**。未读到五任务逐行数据、原行预测、残差、真实标签文件或未公开run logs；不补造逐行测定条件或真实群计数。

共同状态截至该请求截点：884 gradient heads、863 logical runs、62 frozen contexts、946 individual scores（656 Valid、230 native stress、60 train OOF fold；88 fixed Valid cohorts和105 composites另列）。HOOF001全部60项完成/消费；HEPOS001 40矩阵准备因规则注入失败而没有模型操作；SMI005 6636行静态输入覆盖已建立，原N8未执行；GEO002 producer仍在途。Pro005 12:25 cutoff早于这些变化，不得沿用旧waiting作为当前状态。

## 2. 五端点：真实任务语义与已测范围

### 2.1 bbb_martins — AUROC

TDC/MoleculeNet来源的BBB二分类任务。Martins et al. 2012从文献整理约1,970个分子，原文指出文献集偏向BBB positives；常用阈值为 logBB ≥ −1（Kp≥0.1）。TDC group约1,975个样本；另一表示研究使用约1,945行、约1,490 positives，版本/标准化差异不可拼接。BBB readout综合被动跨膜、离子化、极性、尺寸、外排/代谢，不等于单独测P-gp substrate。

Pro005 task22 action=`retain_monitor`：floor收益与seed稳定性混合；H0 seed46 after冻结证据缺口只影响该run；两seed/重复Valid不足以支持统一F010；无新BBB特定机制证据；不支持再开容量或floor网格；没有新proposal/新BBB任务分数。排除的是把seed46单一缺口嫁接所有已验产物，以及把两seed/重复Valid说成普遍稳定。未排除输入支持不足、pKa/中性分数与极性proxy不足、外排信号不足、标签来源/阈值异质性及表示读出问题。

### 2.2 herg — AUROC

TDC hERG为648-compound二分类任务，引用Wang et al. 2016多药效团+ML研究。不能与hERGCentral（多浓度大库）、DeepHIT/ChEMBL大汇编或其它IC50 cutoff数据集混为同一数据集。hERG blocker是Kv11.1通道阻断，不是临床QT风险的完整预测。

Pro005 action=`retain_monitor_mixed_floor`：既有floor方向不一致，本轮无新增任务分数；不能凭full22汇总升高认定hERG修复；无独立分组反证，保留任务级不确定性、不凑新seed；无新proposal。排除“全22平均提升即hERG修复”和“再加一个seed就解决”。未排除多模式/多药效团结合、碱性中心+疏水芳香骨架、细胞/协议差异、表示对空间药效团压缩等。

### 2.3 pgp_broccatelli — AUROC

任务是P-glycoprotein/ABCB1 inhibition，不是substrate prediction、净外排率或BBB penetration。Broccatelli原研究从文献汇编超过1,200结构；探针底物转运抑制标签使用IC50≤15 μM或一定百分比抑制为inhibitor、IC50≥100 μM或低百分比为non-inhibitor，中间灰区常被排除。数据跨多个文献与protocol；原研究使用膜分配相关理化性质、药效团和GRID molecular interaction fields。

Pro005 action=`hold_low_information_direction`：floor混合；部分候选盲预测近同，预期增量可能低；预测近同或验收通过不等于质量相同；无标签分布不能证明改善；不在现有近同候选上加seed/scale网格；无新proposal。排除重复跑近同候选seed/scale作为新信息。未排除Morgan/CheM/MiniMol缺少空间药效团/膜分配信号、输入覆盖不足、protocol异质性、灰区阈值影响。

### 2.4 cyp2c9_veith — AUPRC（项目登记方向）

这是CYP2C9 inhibition。Veith et al. 2009用重组CYP同工酶和bioluminescent CYP-Glo探针体系测大型化学库；PubChem AID1851给多浓度曲线。发光readout反映luciferin产物生成；抑制剂和某些底物都可能降低发光，因此是assay-defined inhibition/competition signal，不是直接底物代谢标签。TDC约12,092 compounds；公开二次分析的curated子集/正例计数与TDC版本不完全一致，不能拼接。Veith观察不同library和isozyme差异明显。

Pro005 action=`retain_local_floor_evidence`：F010两个seed小幅支持、无新native确认；小幅两seed改善不证明新表示/损失可迁移；重复Valid选择史和AP定义未解决；不新增种子，只有相邻任务出现明确readout/representation机制且有匹配证据时才重开；无新proposal。不能把F010两seed小幅支持扩张为已证明迁移。未排除probe/substrate/isozyme选择性、发光readout、阈值化、化学空间与表示交互。

### 2.5 cyp2c9_substrate_carbonmangels — AUPRC（项目登记方向）

这是CYP2C9 substrate/non-substrate。TDC说明合并六篇出版物的底物与非底物信息，约666个药物；一份公开表示研究统计141 positives。productive binding、代谢位点暴露、取向、周转和实验体系影响底物身份。强抑制剂可能不是底物；底物也可能在竞争探针体系表现为抑制。

Pro005 action=`retain_close_weighting_and_fingerprint_recipe`：weighted BCE与Morgan固定小矩阵不支持替换；Mini表现混合；不能把CYP2D6结果推广到所有CYP；AP/AUPRC官方等价仍需来源闭环；无新任务级解释；关闭已测loss/representation配方，不新增统一CYP网格。排除“2D6成功即可迁移到2C9 substrate”及换名重跑weighted BCE/Morgan。未排除跨六篇文献标签差异、代谢位点/三维productive pose缺失、类别稀少与AUPRC方差、输入支持不足。


## 3. 竞争解释与反证

|解释|有来源支撑的缺口|不能声称|反证模式|
|---|---|---|---|
|输入支持/化学空间|scaffold外推、稀有骨架、训练近邻不足；各端点药效团域不同|薄覆盖不等于低分；模型分歧不是真错证据|三表示在低近邻支持群均无一致退化、repair/harm与支持度无关联，则纯支持不足解释减弱|
|电离/电荷/脂溶性proxy|BBB依赖中性分数/极性/尺寸/外排；Pgp抑制与膜分配相关；hERG多模式结合与碱性/疏水药效团相关；CYP受电荷/疏水与口袋影响|没有逐行pKa/logD/assay pH；Morgan片段不等于显式pKa|同表示+固定RDKit描述符若不改善OOF主指标及低支持/共错群，简单2D proxy解释减弱；只涨总体AUROC不修群则不支持修复机制|
|assay heterogeneity|Pgp跨文献protocol与灰区阈值；hERG不同细胞/实验与cutoff；Veith为探针/发光体系；substrate合并六文献|不能填造species、cell line、pH、probe、IC50 qualifier或publication id|来源映射完整后，同source内与跨source表现相同且冲突不富集，则异质性解释减弱|
|类别不平衡/指标|BBB文献集偏positive；CYP2C9 substrate约141/666 positive；CYP2C9 inhibition公开快照约三成positive；AUPRC受prevalence影响|AP不自动等于官方AUPRC；AUROC仍有有限样本不确定性|固定OOF中PR基线解释不了组间差，AUROC、校准/召回也一致，则纯metric解释减弱|
|representation/readout|Broccatelli用3D MIF/药效团/膜分配；hERG Wang用多药效团；CYP substrate需productive pose/site；BBB需电离/极性|论文分数不代表项目收益；不同头/划分/输入不可作表示因果|同头同fold下Morgan/CheM/MiniMol差异不稳定且不集中于机制群，则当前表示瓶颈解释减弱|

### 3.1 语义边界
- BBB Martins是brain/blood penetration，不是Pgp substrate。Pgp Broccatelli是Pgp inhibition，不是substrate/efflux readout。两者生理相关但不能互作逐行机制变量。
- CYP2C9 inhibition与substrate不同。AID1851探针发光信号可能受竞争性底物影响；降低发光不必然表示该分子自身被代谢。
- hERG不同IC50 cutoff、百分比抑制、细胞系与protocol会改变标签；其他公开hERG集合不构成本项目648行逐行来源映射。
- Pgp原始研究排除弱抑制灰区；TDC汇总数与原论文数不可混作本地训练集真实类计数。
- 公开文献理化特征只是候选；不把pKa、logD、charge、pH或assay source填入任一项目样本。

## 4. 优先候选 PGP-REP-PHYS：表示×理化描述符增量

**问题：** 现有表示是否已编码足够膜分配/理化信息？少量透明2D描述符能否在同任务内提供增量，而非重命名loss/floor？

**对象：** `pgp_broccatelli` 原始train行、标签、行身份；AUROC主指标。复用准入的CheM 2048 raw、MiniMol 512 raw、Morgan ECFP4 2048缓存（RDKit 2024.09.6，radius=2、chirality=true、binary）；不新生成Morgan、不加载模型或checkpoint。

**新增固定描述符：** MW、RDKit Crippen cLogP、TPSA、HBD、HBA、rotatable-bond count、aromatic ring count、formal charge。固定版本化RDKit实现；不引入外部pKa预测器、不估计assay pH、不加外部信息。仅在inner-fit拟合均值/标准差，std<1e-8置1。Morgan bits不做逐bit z-score，只对8个连续/离散描述符做fit-only z-score。

**矩阵：** CheM only / CheM+8 descriptors / MiniMol only / MiniMol+8 / Morgan only / Morgan+8，共6格。统一L2 logistic regression readout，C=1.0、fit intercept、class_weight=None、固定solver和软件版本；连续概率输出。若solver确定性，不虚报seed；以已接受fold为主要重复单位。

**split依赖：** 当前shared split register仅有Hep HOOF与AMES/PPBR stress，没有Pgp entry。先查原task ledger和训练端已接受partition；若存在，逐字复用；否则由partition owner登记train-only grouped/scaffold OOF、原行映射、split seed与哈希，只在官方train内部构造。不得重切官方外部划分或使用Valid/test标签。没有partition receipt不执行。

**成本：** 6格×K个已接受fold；若K=5则30拟合（仅算式，不代表已确认fold数）。无新编码器/权重；描述符在原train行计算。资源时长未知。

**预注册解释：**
- 某表示base显著更好且低支持/共错群也改善：支持表示支持差异。
- descriptors对Morgan/CheM/MiniMol一致增量，且相关低支持/错误群改善：支持简单理化proxy未充分编码。
- 仅一表示+descriptor有效：表示×描述符交互，不是普遍physchem效应。
- 仅总体AUROC涨而共错/低支持群不修复：不支持它解决薄覆盖机制。
- 无稳定增量：停止2D proxy分支，不扩大描述符扫参；下一步才考虑3D MIF/药效团或有来源映射的assay subgroup。
- formal charge不是pKa；若只依赖它不能声称识别了pH-dependent ionization。

### 4.2 次优先：hERG与BBB
**hERG：**先Morgan/CheM/MiniMol原始缓存、同一线性/逻辑读出、相同train-only folds做3表示对照；不先加药效团或扫floor。若表示对照能稳定定位错误群，再在同split加固定8描述符视图。648行不得借用其他hERG集合阈值/标签。只有来源清楚且仍有大共错群，才考虑固定多药效团/3D MIF模块并独立准入。
**BBB：**先三表示同头，再加相同8描述符。关注logBB阈值边界、低近邻支持和低分歧群；不把Pgp inhibitor预测当BBB机制标签。若描述符只提升AUROC但未修复低支持/共错群，不能宣称电离/渗透机制解决。要测主动外排须有可信Pgp substrate/efflux readout或assay字段。

### 4.3 CYP2C9 inhibition与substrate分开处理
**Inhibition：**原train folds上Morgan/CheM/MiniMol固定同头比较。AID1851源信息支持probe-dependent readout异质性；取得原始来源映射后，才可做train内部source/protocol完整组分层。未映射前不按假设covariate分组。若三表示排序一致且来源组间无差异，停止assay-heterogeneity分支。不得重复F010两seed或加权BCE/floor recipe。
**Substrate：**小数据、positive稀少，单独用原train folds；先三表示固定同头。关注productive binding/site-of-metabolism，但不直接迁移CYP2D6 recipe或重跑weighted BCE/Morgan。只有六篇来源映射可追溯且现有表示盲区明确，才考虑有来源的site-of-metabolism/3D docking frozen feature；需独立资产/许可/producer准入，不用外部预测标签或改原标签。

## 5. 分组评分协议（未来由指定owner执行）

每个任务、每个已接受train-only OOF fold、每个模型/表示输出完整行覆盖；保留row_index、Drug_ID、SMILES版本和split id。不按Drug_ID去重，不丢重复/冲突行。连续分数为输入。

**完整群及补集：**
1. `all_train_oof`：全部外层OOF行。
2. `model_consensus_correct`：所有模型固定0.5概率阈值同判且正确。
3. `model_consensus_error`：所有模型同判且错误；一致错误是关键盲区，不等同低分歧正确。
4. `low_disagreement`：预先指定模型概率两两差异均值的最低五分位；分位数仅由train预测分布定义。
5. `high_disagreement`：最高五分位；中间60%单列，覆盖不丢失。
6. `low_support`：inner-fit中最近Morgan Tanimoto邻居相似度的train-fit分布预登记分位数；每fold只用该fold fit bank。
7. `repair_transition`：control错/candidate对。
8. `harm_transition`：control对/candidate错。
9. `persistent_shared_error`：两者均错。
10. `new_candidate_only_error`：control对/candidate错，保留作为跨候选风险迁移群。
每组附互补组、n、正负数、coverage、fold分布；成员表留在私有score zone，研究者只接收不暴露小群标签的安全聚合。

**指标：** AUROC按完整群计算；单一类别群AUROC记undefined，不填0。AP与官方AUPRC分别命名；只有官方scorer源码/contract明确映射时才能叫official AUPRC。报告prevalence、AUROC、AP/official AUPRC（若有）、PR曲线摘要、Brier/log-loss次级校准指标；阈值指标另列，不在群内重新选阈值。

**不确定性：** 以scaffold或预登记规范化分子组为cluster bootstrap单位；重复结构保留行但同cluster一起抽样。按fold先算，再报fold等权均值、fold间分布、cluster bootstrap区间。5折训练集重叠，不能当独立数据集。小群CI宽要如实报告；不显著不等于等效。repair/harm必须同一行、同一fold、同一control；全群与补集数可加回总行数。

**owner与权限：** score owner负责原train OOF score和群统计；partition owner提供split manifest；研究方只提供群定义和解释，不读取私有逐行残差。proposal必须指定owner、scope、输入hash、fold/行覆盖、输出字段与隐私最小群限制。Valid只由指定host按现有政策评分，不能用于fit/选择矩阵；复用旧Valid分数需注明使用次数和选型历史，不称独立泛化。

## 6. 条件备选与停止规则

- **BBB电离/被动渗透：**若2D增量为正但formal charge proxy不足，只有存在可核验pKa/logD/实验pH来源才重开；没有这些字段时不提议外部pKa模型。
- **hERG多药效团：**Wang 2016支持该方向，但需固定可复现的药效团/空间表示资产。若简单表示对照及理化增量已解释改善群，无需3D模块；若仍有大而低分歧共错群且覆盖充足，再独立登记固定pharmacophore/MIF模块。
- **Pgp 3D MIF：**Broccatelli论文直接支持。只有现有表示+理化增量后仍有完整低支持/共识错误群，且可证明MIF输入版本、坐标、质子化/构象规则、许可证与producer冻结身份时才进入准备。
- **CYP substrate site-of-metabolism：**Ahlström等对14个celecoxib类分子用docking/site-of-metabolism预测，并以recombinant CYP2C9孵育LC-MS/MS验证productive pose/site信息；这不是Carbon–Mangels逐行标签来源。须先有六篇来源mapping与可复现资产。
- **KPGT/SMI/几何：**不是本次五端点的独立任务提案；在途SMI8、HEPOS40、SOLCTX4、GEO32完全冻结，006不增预算、不重派、不修改。未来只有形成独立证据后才登记task-specific迁移。

**停止：**三表示无稳定差异、descriptor增量无增益且完整共识错误/低支持群无一致机制，则关闭有限矩阵，不继续seed/floor/loss/descriptor扫参。partition/row identity缺失记为准备阻断，不是科学负结果。数据源映射缺失则停止assay subgroup解释，不猜测每行条件。

## 7. 关键外部来源

- TDC ADME任务定义（Pgp、BBB、CYP inhibition/substrate）：https://tdcommons.ai/single_pred_tasks/adme/
- TDC Toxicity任务定义（hERG 648及Wang 2016引用）：https://tdcommons.ai/single_pred_tasks/tox/
- TDC ADMET group任务规模、scaffold split、指标选择：https://tdcommons.ai/benchmark/admet_group/overview/
- Martins et al. 2012 BBB原始研究，PMID 22612593, DOI 10.1021/ci300124c：https://pubmed.ncbi.nlm.nih.gov/22612593/
- Broccatelli et al. 2011 Pgp inhibition原始研究，PMID 21341745, DOI 10.1021/jm101421d：https://pubmed.ncbi.nlm.nih.gov/21341745/
- Broccatelli完整数据方法（探针底物、灰区、IC50/百分比阈值、MIF/膜分配）：https://pmc.ncbi.nlm.nih.gov/articles/PMC3069647/
- Veith et al. 2009 CYP isozyme selectivity原始研究，PMID 19855396, DOI 10.1038/nbt.1581：https://pubmed.ncbi.nlm.nih.gov/19855396/
- PubChem AID1851 CYP panel assay/protocol：https://pubchem.ncbi.nlm.nih.gov/bioassay/1851/
- Carbon–Mangels CYP2C9 substrate数据说明（六文献合并）：https://pytdc.arcell.ai/datasets/adme/CYP2C9_Substrate_CarbonMangels
- Carbon–Mangels & Hutter 2011, DOI 10.1002/minf.201100069；TDC任务页列明该数据与Cheng et al. 2012来源。
- Ahlström et al. 2007 CYP2C9 substrates/inhibitors/metabolites，DOI 10.1021/jm070745g：https://pubmed.ncbi.nlm.nih.gov/17915853/
- Wang et al. 2016 hERG pharmacophore ensemble study，PMID 27379394, DOI 10.1021/acs.molpharmaceut.6b00471：https://pubmed.ncbi.nlm.nih.gov/27379394/
- hERG多源数据异质性与IC50阈值变化实例：https://pmc.ncbi.nlm.nih.gov/articles/PMC3324100/ ; https://academic.oup.com/bioinformatics/article/36/10/3049/5727757

## 8. 结论边界

本研究提供的是可改变后续决定的候选研究设计，而不是任务成绩声明。唯一优先建议是先补齐Pgp train-only partition/row-identity依赖，再执行6格固定表示×描述符对照；如split无法验收，立即停在准备层。其他端点分开保留机制假设，不以一个通用loss/seed/floor网格覆盖。当前没有训练、评分、标签获取或部署授权。
