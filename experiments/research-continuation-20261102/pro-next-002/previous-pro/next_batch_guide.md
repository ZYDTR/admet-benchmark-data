# 后续批次准备与派发指南（科学接口版）

request_id：`admet-pro-parallel-20261102-001`；固定快照`672730a7c9f76d7b4f1cbc5bac80cf9fbda573b2`；输入清单摘要`25ba8a81a13e070f9d8f7f6336e5f0b97f06ae5c6097257361205ca1f2e2a213`。

**本文是建议，不授权执行。** 研究者没有运行下述训练、单元fixture或模型；主控选择预算并登记后，准备方实现新接口，训练方只执行确定矩阵。准备不能取得逐行Valid真值/残差、上传赛事、操作未授权主机或擅自安装/训练。需要模型forward的验收也必须在后续允许的阶段另行登记；本轮只是给预期行为。运行细节可由执行方解决，科学参数、任务、split和控制不允许自行改动。

## 0．交接文件与控制权

`next_experiments.json`是99个task/config/split对象，展开最大197个seed-fit；`budget_scenarios.json`选小25、中89（推荐）、大197的互相嵌套子集。`controls.json`是88个已有比较槽位，不是88个新训练；BBB H046缺after的槽位不可作为完整冻结控制。`conditional_followups.json`把结果依赖分支单列；`search_space.json`中的储备不自动加入主预算。`issues.json`、`claim_events.json`由主控/Astra按真实执行增量归并，研究者不直接维护本地账。

准备清单、诊断和合规门槛不出现在训练数组。每个拟议run必须记录父proposal_id与request_id；相同科学配置跨方向引用同一fit，不能复制run换名重算预算。

## 1．所有工作项共用的已验接口与不变量

### 1.1 科学资产和输入

当前唯一ready分子底座是`scientific_asset_id=chemeleon`，冻结checkpoint SHA256：
`c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651`。

沿`evidence_registry.json`中的E-INTERFACE、E-DATAIO、E-BRIDGE、E-RUNINDEX绑定本任务已验2048维缓存；原输入版本、train/valid/test分区和ordered row_index保持一致。Drug_ID不是唯一键，不因重复SMILES、空字段或Drug_ID重复删行。已有22任务桥接/缓存验收复用，不重新审1256对象，不重新编码CheMeleon全库。

每个新run输出：完整有效config及其哈希、输入/缓存/分区身份引用、fit/stop row_index与哈希、序列化scaler与target_transform、头checkpoint、每epoch训练loss和内部stop指标、best_epoch/结束原因、best重载证据、连续预测及输出身份、参数与buffer before/after、optimizer参数集合、worker业务状态与supervisor运行状态。后两者独立保存。

### 1.2 生产字段，不用别名

现有config必需根字段：`run_id, task, kind, pretrained_sha256, head, split, monitor_metric, monitor_direction`。

默认head：
```json
{
  "feature_dim": 2048,
  "hidden_dim": 256,
  "activation": "relu",
  "dropout": 0.1,
  "optimizer": "AdamW",
  "lr": 0.0005,
  "weight_decay": 0.0001,
  "batch_size": 128,
  "max_epochs": 50,
  "patience": 8,
  "seed": 46
}
```

另一个确定model seed为47。当前真实枚举：hidden_dim128/256/512、dropout0/.1/.3、lr.0001/.0003/.0005/.001、weight_decay.00001/.0001/.001、seed44/45/46/47；batch128、max_epochs50、patience8固定。AdamW betas(.9,.999)、eps1e−8、amsgrad=False，无gradient clipping。监控min_delta1e−7来自已验训练路径，不能换成自定义阈值。[E-DATAIO, E-TRAINER]

默认split字段：
```json
{"method":"raw_smiles_group_shuffle","seed":43,"stop_fraction":0.1}
```

这是按原始Drug字符串分组，不是canonical identity/scaffold。不同model seed不改变split seed。方案描述ID`train-rawdrug-group-s43-stop10__external-official-valid-v6`用于归并，不能替换运行时真实split manifest/hash。

H0完全省略`feature_scaler`字段，走已验legacy路径。F001/F010分别是下列`denominator_floor`的0.001/0.01：
```json
{
  "method":"fit_std_denominator_floor_v1",
  "denominator_floor":0.01,
  "legacy_epsilon":1e-8,
  "legacy_low_std_replacement":1.0,
  "fit_statistic_dtype":"float32",
  "ddof":0,
  "transform_dtype":"float32",
  "fit_scope":"internal_fit_only"
}
```

先`d0=where(std_fit<1e−8,1,std_fit)`，再取max(d0,floor)；常数维分母1，不是floor。相同inner-fit/policy可复用已序列化统计；不同inner-fit必须重拟合，禁止让stop、outer、Valid或test参与统计。不能把“全train无标签标准化”默认为等价。

### 1.3 目标、指标与预测尺度

分类：原二元标签、BCEWithLogits mean，连续sigmoid正类概率；AUROC/AP最大化，不使用硬阈值或F1。AP为本地固定评分器定义，官方等价未确认。

回归：inner-fit的Y均值/标准差float64，训练目标为标准化Y上的mean MSE；预测逆变换一次回原Y。外部MAE的任务内部stop也用原Y MAE最小化；外部Spearman的任务内部stop用原Y Spearman最大化。各proposal已明确具体指标，不用“task-native metric”让执行者猜。当前9回归任务都不能擅自把log/单位变换加入Y。

内部stop选最优checkpoint并重载；外部Valid不是训练端earlystop信号。用户允许Valid评分/调参，不因此设定“只能看一次”的虚构硬规则；但每次外部评分均登记选择暴露。最终train+valid合训未授权。

### 1.4 独立fixture的预期意义

这些是后续准备验收规格，不是本轮已经运行的检查：

- **缩放数学fixture**：直接给已知std向量`[0,5e−9,5e−5,.005,.1]`。预期H0分母`[1,1,5e−5,.005,.1]`；F001=`[1,1,.001,.005,.1]`；F010=`[1,1,.01,.01,.1]`。验证branch与floor，不用于模型质量。不能用stop/Valid重新估计这些统计。
- **目标尺度fixture**：保存mean=10、std=2，标准化输出1应只逆变换一次得到12；classification logit0对应概率.5。不允许将已是原Y的输出再次inverse。
- **输入身份fixture**：给重复Drug_ID/重复Drug/非连续row_index的合成清单，按task/split/row_index定位；预测必须保留每个原行，不能按Drug_ID join产生多对多或自动去重。
- **冻结fixture**：检查所有预训练参数/buffer身份不变，optimizer只含新模块；requires_grad=False不单独构成全部证据。新头checkpoint重载预测一致，不等于未经检查的整个系统冻结。
- **早停fixture**：预置指标序列与方向，验证1e−7改善门槛、patience8、best重载；不得把最后epoch当best。固定评分器不因新loss改变外部口径。
- **边界fixture**：缺字段、非法seed48、非法dropout.2应由当前validator拒绝；新接口只有显式版本提升后才接纳。监督失败和worker返回不可互相覆盖。

验收通过仅代表接口行为符合约定，不代表模型泛化改善。任何失败只阻断依赖工作项。

## 2．WP-R：BBB前瞻控制（config_only，1fit）

关联I-BBB-AFTER、D-BBB、`P-A-BBB46-REPAIR`。目标是为未来BBB比较建立完整证据，而不是补写旧H0 s46的after。

输入：同v6 BBB缓存、当前H0配置、seed46、已验split43。计划主机RTX4090，与当前F010 s46匹配；原H0缺after产物只作为历史research-only槽位保留。输出和fixture采用§1，尤其参数/buffer before/after及重载。

保持head256/dropout.1/lr.0005/wd.0001/50/8；无scaler扩展，即H0。仅此1次重复fit有明确新增信息。若匹配主机不可用，不能在预算内悄悄添加另一套对照；主控另行登记cross-host策略。新控制失败时，A中BBB46相关比较停下，其他任务继续。旧缺after不会因这次成功变成历史通过。

## 3．WP-A：退化/不稳定12任务的F001（config_only，24fit）

关联I-TASK-HETEROGENEITY、I-SCALE-MECHANISM、D-FLOOR。任务固定：
`ames, bbb_martins, clearance_microsome_az, cyp2c9_substrate_carbonmangels, cyp3a4_substrate_carbonmangels, cyp3a4_veith, dili, half_life_obach, herg, hia_hou, pgp_broccatelli, vdss_lombardo`。

每task只新增F001、model46/47、原split43。变化仅`denominator_floor=.001`，其余§1不变。已有H0/F010共同seed控制从controls引用一次；BBB46用WP-R新对照。24个新fit，不重跑48个已有H0/F010槽位。

科学问题：中间尺度是否能缓解F010退化，又不回到H0放大；若F001两seed也不胜，不加密floor网格。预处理fixture和行身份先验收；scaler变换若与既有配置数学等价则登记跳过，不为了凑数训练。

输出：每task每seed三点H0/F001/F010原始指标和方向、训练/stop轨迹、无标签标准差/分母比率汇总。没有Valid残差，不给“错误分子”名单。一个seed有利另一seed不利标不稳定，不能将平均升幅当成功。12任务是因为本轮5退化+7混合全部覆盖，不是从86或旧28机械分摊。

## 4．WP-B：尺度×容量/正则分解（中档新增64fit）

任务固定八个：`dili, hia_hou, half_life_obach, cyp3a4_veith, cyp2c9_substrate_carbonmangels, vdss_lombardo, ppbr_az, caco2_wang`。

### WP-B1（config_only，32fit）

8task×H0/F010×seed46/47，MLP256，仅dropout从.1变0。与已有同floor、同seed控制比较，保留lr.0005/wd.0001/50/8和原目标/stop。输出包括完整config、checkpoint、轨迹与Valid汇总。原代码支持dropout0，无需再实施一个新的通用MLP框架。

### WP-B2（new_code，32fit）

同八任务、两floor、两seed，将B1的MLP替换为单个`Linear(2048,1,bias=True)`，不含ReLU或dropout。拟议新字段`head.architecture="linear_only"`、`head.bias=true`，删除hidden_dim/activation；这些字段**当前不支持**，必须在独立版本实现并做明确互斥校验。

保持B1的dropout0、loss、优化器、split、fit-only transforms、stop、seed。线性头参数2049；现有MLP256参数524801。参数量差与初始化/随机数消耗是架构改变的一部分，不能声称只删除某个噪声层。

独立fixture：线性分支拒绝hidden_dim/activation混入；预置二维输入/权重应按纯仿射式输出，无ReLU截断；序列化只包含新线性参数和固定transform绑定，重载一致。classification仍rawlogit训练/概率输出；回归仍标准化MSE/原Y输出。模型实例或forward fixture必须在后续授权准备环节，不在本研究会话执行。

B1是B2的真实控制，不用已有dropout.1 MLP冒充“只变架构”。若linear接口未完成，中档只运行已准入57个config_only fit，32个保持待准备；预算不自动转向别的模型。若linear在两floor均胜且方向稳定，支持简化头；若仅H0/F010之一胜，支持交互而非普遍简单模型更好。若均不胜，保留MLP，不以此推断冻结表示无用。

## 5．WP-C：学习率单因素（大档32fit，config_only）

同B八任务×H0/F010×46/47，**恢复默认dropout.1**，仅lr从.0005变.0001；control是已有默认.1/5e−4，不能用B1 dropout0。

目的：如果H0在较小lr下追回F010，而F010变化很小，支持优化条件/有效步长解释；如果所有lr仍保持方向，也不等于机制已经确定，只说明这个lr对照未解释。真实validator支持1e−4。输出除质量分数外给best/last epoch与停止原因，不把多训epoch数单独当质量证据。warm缓存0新增编码。

## 6．WP-L：目标函数对照（大档16fit，new_code）

### L-reg：5个MAE任务×2seed＝10fit

`caco2_wang, ld50_zhu, lipophilicity_astrazeneca, ppbr_az, solubility_aqsoldb`，F010，seed46/47，其他默认。新loss为twice-Huber δ=1、标准化残差r：
`L(r)=r²`当|r|≤1；否则`L(r)=2|r|−1`，再取batch mean。

相比MSE只改尾部梯度，不改小残差曲率。fixture在r=0,.5,1,2预期loss0,.25,1,3；r=±1函数值/导数连续，正负对称。target标准化统计inner-fit only；早停原Y MAE最小化，预测原Y。不能改成原Y Huber δ=1或PyTorch默认半倍Huber而不登记。

### L-cls：3个AP任务×2seed＝6fit

`cyp2c9_substrate_carbonmangels, cyp2d6_substrate_carbonmangels, cyp2d6_veith`，F010，46/47。`w_pos=clip(sqrt(nneg_fit/npos_fit),.25,4)`、w_neg=1；loss为带class weight的BCEWithLogits，并除以该fit的平均样本权重。确切公式和fit counts写入checkpoint/manifest，不让worker凭Valid比例猜权重。

fixture：n_pos=n_neg时权重1完全退化回无权重损失；n_pos=25,n_neg=100时w_pos=2、平均样本权重1.2。fit单类停止该分支，不以stop/Valid样本补权重。stop本地AP最大化，概率不阈值化；输出是加权模型的sigmoid分数，不能自动宣称已校准概率，也不以AP增加证明校准改善。

新loss只增加明确enum/参数，原BCE/MSE路径保持回归fixture兼容。任何历史Caco2 MAE/MSE试验保持记录；本分支仅对本次同split/F010/scaler/目标新定义做增量比较，不能抹去旧探索。

## 7．WP-S：官方train内部结构压力（大档24fit，new_code）

任务`dili, cyp2c9_substrate_carbonmangels, ppbr_az`；每task两outer split seeds101/102；每outer split H0/F010；model46/47。合计3×2×2×2=24，含12个新的H0控制。旧rawgroup43控制不可拿来代替新split控制。

输入仍是全部官方train原行与原标签；官方分区不移动。创建split manifest时按canonical isomeric molecule/Bemis–Murcko scaffold分组，含chirality；acyclic空scaffold以canonical isomeric身份作组；parse failure保留rawDrug字符串组并报告。sorted unique group keys后使用明确split seed洗牌，按整组累积到目标outer20%，然后在剩余outer-train内按同组规则取stop10%（seed43）。不能把同组拆开追求精确行数；实际fit/stop/outer计数必须报告。

这只改变**train内部验证设计**，不擅自清洗训练数据。外部指标是train-outer的同任务MAE/AUROC/AP/Spearman，outer不能用于earlystop/scaler/权重/候选再选；官方Valid本分支不是主比较指标。每个inner-fit独立拟合X/Y统计。全量冻结原表示缓存可以共享，不新增CheMeleon编码。

fixture：同identity的不同SMILES编码和同scaffold组不得跨fit/stop/outer；重复行仍全部保留；任意split三部分并集等于官方train、交集为空；没有Valid/test行；split seed变化不能误当model seed变化。分类任一必要评价集单类则不可估、跳过，不重新采样到有利结构。解析工具版本必须锁定，若按此定义无法实现全行覆盖则主控评估备用规则，不能由worker自行改变。

结果判读：同一个模型跨split值变化只表示敏感性，不是候选排名比较；本矩阵两配置每split都有，才可讨论H0/F010的结构压力下排序。结构压力也不是事后重造“完全独立隐藏测试”，因为历史train曾被使用、候选已经参考Valid。

## 8．WP-N/M：新表示及经典特征组合（大档36fit，blocked_assets）

共同任务面板：`ames, bioavailability_ma, clearance_hepatocyte_az, cyp2c9_veith, lipophilicity_astrazeneca, solubility_aqsoldb`。每候选6×2seed=12fit。保持原rawgroup43 stop10%、hidden256/ReLU/dropout.1、AdamW.0005/wd.0001、batch128/50/8、原目标/stop；对照是已有CheMeleon F010同task/seed。

这不是已就绪的调配置；表示出口维数/预处理与头第一层参数数一起改变，design_type=bundle。原控制只计一次。不得因floor .01在CheMeleon有效就声称其对新表示最优；它是固定预算初筛policy，若新表示失败先检查尺度分布而非直接否定模型。

### MiniMol（scientific_asset_id=minimol）

官方512维per-molecule表示。拟议float32、batch128、eval/no_grad、所有pretrained参数/buffer冻结，使用官方表示API，不使用fine-tune helper。**本地版本/revision/权重SHA目前未知**，JSON保留null和blocked，不用名字伪装已固定。

准入：准确package/code/tokenizer/weights/buffers版本；所有原Drug完整处理；每行512维finite；cache(task,split,row_index,sourceSHA)；冻结前后；只学新头。原下载404准备失败保留，但不是质量反例。失败则停止该资产，不退化为随机初始化MiniMol。

### MoLFormer（scientific_asset_id=molformer_10pct）

候选上游：`ibm-research/MoLFormer-XL-both-10pct`，已查revision`361063d0ad524ef77cf39b08469f6be770dc550f`。拟议pooler_output768、deterministic_eval=True、eval/no_grad、float32/编码batch64（头训练batch128）；本地checkpointSHA未验所以blocked。

长度上限/完整SMILES覆盖必须先确认。不开默认silent truncation、不复制预训练过滤规则删长分子、不给无法编码行补标签。若任何task原行覆盖不成立，停该task/资产，主控决定是否另研究科学表示策略。旧off-root违规不能靠换输出名当通过；新实施需自己的合规边界。

### CheMeleon＋Morgan（scientific_asset_id=classical_features，组件含chemeleon）

新模块配置固定：Morgan radius2、fpSize2048、includeChirality=True、countSimulation=False，bit向量除sqrt(2048)，与CheMeleon F0102048维拼接成4096维。Morgan块不再fit标准化，CheMeleon块使用既有fit-only F010；不能将整个4096块统一scaler后还称这个方案。

原行不去重，不添加外部样本；RDKit/feature schema版本锁定。当前缺生成/拼接生产接口，所以blocked_assets而非config_only。纯经典模型的正式赛事资格另核，不把研究对照等同获准提交；本方案保持冻结CheMeleon主体和新头，仍由主控核规则。

### 三个候选共同成本与fallback

各候选6task×train/valid/test=18逻辑cache分区，跨seed/头共享；不是18次物理GPU调用。MiniMol、MoLFormer编码和Morgan计算成本未测，不能把89档每头耗时当编码耗时。先在第一个真实已授权任务记录实际span/内存/准备，资源超过已登记上限则停本分支。不能为省一次研究把6任务扩到22或把10pct换完整更大checkpoint。

KPGT/Uni-Mol/SMI-TED/MolE、scratch D-MPNN/TabPFN属于search_space储备，主197没有包含；它们各有明确面板/参数和预算公式，但需另行准入，不与这36fit混计。

## 9．WP-DIAG/ENSEMBLE：零fit，不等于零选模代价

关联D-DISAGREE、D-ENSEMBLE。先沿E-PREDINDEX的精确URI只取批准的blank-Y预测，不用private-scoring或旧公开Y文件。以task/split/row_index对齐，检查无重复遗漏与尺度；不可按行顺序想当然匹配不同文件。

只输出任务级预测分位、非有限数、跨seed/rank相关、概率分歧和预先定义分子结构切片的无标签描述。分歧不说明哪模型正确，极端预测也不是已知大残差。小分组可能构成答案侧漏，任何任务/组级质量诊断都须主控私有评分授权与安全阈值；建议30只是工程提议而非规则/统计保证。

固定等权seed平均：对12个未解决任务，每个H0/F010各平均46/47，产生24个新评分输出、0fit；已有BBB缺after组合不可作完整冻结集成，需先WP-R。回归必须先各自inverse到原Y再平均；分类平均连续概率，不平均AP/AUROC指标。额外10任务20个输出是另记的可选扩展。每次新增Valid输出评估都进入exposure账，不能用“0fit”掩盖额外适配。学习ensemble权重/stacking要用train内部OOF，需新预算/接口，不能Valid拟合。

## 10．预算、交接与研究节点

推荐依次R/A→B1/B2；新linear工程可与A并行准备，正常收齐注册阶段后评审，不强制等12任务全改善。大档仅在主控另批准后增加C/L/S/N/M；工作项可按独立依赖排程，不按GPU秒忽略准备/取回。小25、中89、大197是最大确定候选数，跳过保留原因，不给worker调剂成别的任务。

已验历史span：22项408.95秒、64项634.32秒；64contract→科学完成6454.65秒；共享取回1171.26秒只计一次。规划采用`准备+新接口+排队+编码+头作业+取回评分交接+新研究−实测重叠`；budget_scenarios把小/中/大非重叠资源分配和未知项分别列出，不是完成时限或核小时承诺。新增checkpoint按增量传输，不重传430个旧checkpoint。

**改善**：报告各seed方向/幅度与历史范围，不编统计阈值；保留控制，按既定后续检验机制。

**无改善**：停止密集floor，使用B/C辨别容量/优化；若也失败，停止局部grid，再看已ready新表示。

**不一致**：如实标记，盲分歧和固定平均优先；至多4任务×2配置×2新seed48/49=16额外储备，需要扩validator且另登记，不在197里。

**实质故障**：冻结/标签/row identity/reload失败立即回主控，只停依赖产物；保存业务与监督失败，不继续同一违规方法。候选无效不能当科学反证。

**值得下一次Pro研究**：预登记阶段收齐并改变候选排序；出现否定当前主要机制的结果；新表示需要改变科学输入/池化/覆盖；结构split不可估；既定方向耗尽或预算上限到达。不是每个头、固定时间或返回JSON成功就触发。

主控接收每task/config/split/seed实际状态、已验聚合指标、fit/stop计数和尺度、唯一fit账、阶段时戳及失败记录。未执行为未执行，不从计划推断完成。以上指南可以投影给准备/训练方，但不得夹带逐行Valid真值/残差或可逆答案分组。
