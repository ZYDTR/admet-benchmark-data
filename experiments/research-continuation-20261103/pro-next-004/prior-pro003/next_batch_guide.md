# 下一批科学准备与登记指南

请求：`admet-pro-next-research-20261103-003`。固定输入SHA256：`c61e67a6dc85e2aada50e0a46b6d9a9d7241b385f26f15629ab5ecce790d0eb8`。

**本件只给主控审核、未来授权后的工作规格，不授权当前训练、推理、模型加载、远端连接、派Agent或发布。** 准备工作/零fit门槛不塞入训练数组。所有新训练必须由主控按最新实际身份登记；执行方不能根据本文自行追加seed、补缺任务或扩grid。已派工作由原执行链完成，本文不重派。

## 1. 发出任何新学习前只做哪些增量核对

### W0：源绑定和科学身份归一（0新fit；config_only准备）

**目标／问题**：I003-VIEWS、I003-ASSETBIND、I003-SELECTION。避免重复已经完成/已派轨迹，并把科学规格翻译到实际支持的字段，而非设计另一套任意CLI。

**输入**：本轮current/CURRENT_STATUS、已有实际run的source/cache/partition/optimizer/目标配置验收；`next_experiments.json`与`controls.json`。科学资产版本见`scientific_assets.json`，旧源不变的验收复用，不拉整库模型/trace/逐行标签。

**唯一身份键**至少为：task＋原输入版本＋encoder权重/池化/cache＋split成员SHA＋scaler规则及拟合范围＋head结构/初始化＋optimizer/lr/wd/batch/schedule＋训练目标及reduction＋stop规则/预算＋modelseed。view另加selector/checkpointSHA/predictionSHA，不作为新fit。TabICLcontextfit另计，不混入梯度fit。

**必须保持**：原行/分区/标签、已验encoder及全部buffers、已验旧控制、旧失败记录、原冻结/身份接收范围。不得用迁移主机的新包装SHA覆盖旧科学身份；同一unused wrapper predictor变化不等于encoder改变。

**需输出**：逐proposal实际解析后的配置、源/特征版本绑定、确定的父对照、去重清单、未就绪原因。已存在等价fit直接映射原run，不重训；切片/score引用不变时不重评分。

**真正待绑定而不能猜的字段**：当前ranking objective完整序列化block（来自已接受`hrs8-half_life_obach-f001-pairwise-canonical-s44`，objectives源SHA`7c805d610c37c11c6e9f6f826d85516a4c8fe2765ac75ee6415615dcc00203a1`）；hep父partition/cache receipt的确切SHA；新VDss分区清单；当前MoL/TabICL实际weight receipt（只用于来源核对，不重派）。报告里的H0 floor=null表示“没有新增floor”，不能未经映射就传null CLI。

**独立验收含义**：序列化往返后科学字段相同；当前parent/modelseed/losspair有共同初始化与batch规则；输入ordered row身份可指向已验回执。不是重做全部冻结测试，也不是把本验证器PASS当模型质量。

**预算／fallback**：0fit、0编码、0评分；未公开receipt字段只请求原主控安全摘录。局部无法绑定则对应单元保持blocked，不补猜值、不总停其余独立问题。

## 2. W-R：首批28项排序迁移（config_only，实际源绑定后）

### 2.1 精确矩阵和保持项

任务：micro、hep、VDss；每任务canonical/scaffold，splitseed43；modelseeds44/45。micro/hep固定CheM2048 F010；VDss固定CheM2048 H0。每个split新训HalfMSE和ranking两配置；VDss再补FullMSE。其余micro/hep FullMSE控制已有，不重训。14条proposal×2seeds=28新fit；逐条已展开在JSON与本件附表。

现有MLP字段：`feature_dim=2048, hidden_dim=256, activation=relu, dropout=0.1, optimizer=AdamW, lr=0.0005`（VDss为`0.0001`），`weight_decay=0.0001, batch_size=128, max_epochs=50, patience=8`。`monitor_metric=Spearman, monitor_direction=maximize, min_delta=1e-7`；tie取最早best；无新scheduler/gradient clipping。AdamW betas/eps沿当前接受默认值，不擅改。

**feature scaler**：每split仅fit统计，float32 mean/std、ddof0；`d0=where(std<1e-8,1,std)`；H0用d0，F010用max(d0,.01)。target按fit-only float64均值与总体std标准化，沿已验target transform及常量保护；常量目标不能计算Spearman的单元预定skip。输出`muY+sigmaY*prediction`逆变换一次；不能拿标准化prediction直接算原尺度MAE（本批外部虽Spearman不敏感，输出协议仍保持）。

### 2.2 目标必须精确，不用“排序loss”泛称

HalfMSE：`0.5*mean((z_pred-z_y)^2)`。

Ranking：`0.5*mean((z_pred-z_y)^2) + 0.5*mean softplus(-sign(z_yi-z_yj)*(z_pred_i-z_pred_j))`，沿已验batch内unordered i<j且y_i≠y_j的规则，两项各mean；无有效pair则pair项0。不额外采样pair、不改温度、不切掉近标签pair、不加入teacher或shuffle-label。

这些是完整数学值；实际生产目标名称/字段必须复制已验rank block，不把旧提案枚举当接口事实。若当前adapter不能原样支持，新代码需求先报告主控，不让执行方用“近似等价loss”代替。

### 2.3 分区与控制

micro canonical539/77/154、scaffold532/79/159，父split SHA在JSON固定。hep canonical591/86/171、scaffold593/85/170，复用E-HEPSTRESS父原件，公开投影未暴露SHA的字段由已验receipt绑定，不能另造同名分区。VDss现成canonical/scaffold builder一次物化目标70/10/20，不能凭总N假造valid行数；完整组保留，splitseed43固定。

拟议新分区保守门槛：fit至少官方train50%，stop/stress各至少20，待用目标非恒定；父规则更严则从严。这是可运行性门槛，不是p值或置信保证。失败整对skip，不换hashseed或混回stop/stress。

主对比同losspair从相同初始张量、同batch序列开始；不同loss触发不同earlystop后长度可不同，只比较共同前缀和各自规则选点。历史FullMSE若平台不完全同构，仅作为次级系数/旧配方锚；新rank对HalfMSE仍保持当批匹配，不用历史环境差掩盖主对比。

### 2.4 准备fixture与输出

只需对新增适配做无学习数学fixture：例如y=[0,0,1]有两条不等目标pair；检查tie不入分母、排序反向loss较高、常数预测pair项为log2、batch无pair时为0；HalfMSE恒为相应MSE的一半；固定输入重载后目标与prediction尺度一致。fixture不是实际ADMET实验，不读取Valid Y，不累加到头fit数。

未来授权真实训练输出：配置/version、source/cache/split身份、fit-only变换、train/stop每epoch汇总、MSE/pair项与有效pair计数、step/best epoch、optimizer状态、best/last语义、stop锁定时间、stress完整无真值预测与一次固定stress评分回执、实际资源/失败记录。stress标签仍由获准宿主评分，不转给准备方；指南只投影task级汇总。

**成本与停止**：R最多28fit、0encoder、0wholeValid、0contextfit。两种子/两partition方向不稳定也不加seed。所有配对齐套或登记真实skip后评审；冻结/标签/身份实质故障立即回主控。

## 3. W-X：第二批16项loss×表示交叉（config_only）

micro/hep固定Mini512 H0、MLP256、lr5e-4，其他目标/monitor/50/8与W-R一致，复用完全相同native成员，model44/45。两task×两partition×HalfMSE/ranking×两seed=16。旧Mini FullMSE四分区×两seed复用；与R对应格形成差分之差。

这里“同seed”只在相同表示的losspair中保证同张量；CheM2048与Mini512不能同first-layer权重。X不是R成功才有资格：CheM无效果而Mini有，正是交互信息。X无一致收益则限定此固定目标，不扫lambda。R+X可共享准备/取回批次，预算仍按44唯一fit登记；先收R也不需要重新问Pro才能按本条件处理X。

## 4. W-N：嵌套fit支持判别8项（new_code，条件追加）

**依赖**：R/X及原M6已足以显示结构差异仍未解释，主控判断样本支持假说会改变决策。固定micro/hep各自scaffold父split，只改其fit支持。

**确定算法**：使用父fit内的原scaffold group key；排序键为`SHA256(UTF8("pro003-nested-fit75-v1|43|" + groupkey))`，hash相同按groupkey精确UTF8排序。目标`floor(.75*n_parentfit)`；选累计不超过目标的最长完整组前缀。没有“换个能达到75%的组合”搜索。首组超target或子集不达资格则整task对比skip。其余原train行保留身份，仅标`unused_for_this_study`，不删除源行、不改标签/原官方partition。

**配置**：两task×CheMF010/MiniH0×44/45=8；FullMSE、原MLP256/lr5e-4/50/8；原stop/stress不变，feature/target统计对子fit重估。fullfit控制原样复用。属于fit支持＋必要统计重估bundle，不称纯化学单因素。

**fixture**：synthetic group-size清单验证prefix/wholegroup/row preservation，同输入两次成员SHA相同，stop/stress untouched，无法达标返回skip而非换方案。所有选择只由原fit key/大小决定，无stop/stress metric参与。

**输出／fallback**：父/子fit成员hash、真实N和未用行身份、变换统计、同task两表示对照；不能生成学习曲线额外25/50/90%格。N无判别价值就关闭，不补新任务。

## 5. W-K：容量线索的结构迁移4项（config_only，等待M6）

仅micro已有scaffold43，CheMF010 MLP128／MiniH0 MLP512×44/45。保持原FullMSE、lr5e-4、dropout.1、50/8与Spearman↑；对照为各表示原native MLP256。新增4，非原M6 raw46/47的重复。

M6当前准备里MiniF010身份透传须先真实通过；新scaffold不继承raw H0=F010等价，本方案明确MiniH0，避免同时改变scaler。参数量262401/263169仅近似匹配。fixture验证实际in/out维度、头参数数目和optimizer只包含新头；不需重验encoder全库。

触发：M6有一致且影响下一决策的容量线索。M6混合或无效则skip K，不加宽到1024，也不改成Sol补数。未来记录实际steps和memory，避免“同参数量必同成本”假设。

## 6. W-T：固定k32成员损失聚合2项（new_code，等待M5）

**task** `cyp2d6_veith`；Mini512 H0、现有scaffold43 split（6427fit/920stop/1844stress）；44/45；TabM代码`28e47ae301c92ec37787dde1ce923a0793f405b4`，3blocks512、k32、dropout.1、random-signs、num_embeddings=None、无类别特征、d_out=1。AdamW lr5e-4/wd1e-4、batch128、50/8、AP最大化早停。对照为已接受的同配置native成员平均BCE两fit；不重复k32基准。

**只改lossaggregation**：对每样本先取`pbar=mean sigmoid(logits_k)`，训练二元NLL。稳定表达：`log_pbar=logsumexp(logsigmoid(logits_k))-log(k)`，`log_1mpbar=logsumexp(logsigmoid(-logits_k))-log(k)`；按原y做平均NLL。不允许mean(logits)后BCE，不改推理mean-prob，也不按Valid挑成员。

**fixture与预期**：k=1与BCEWithLogits一致；所有成员相同logit时与原成员平均loss相同；不同logit时核对Jensen不等式与有限数值；极端正/负logit无NaN；梯度只流入新TabM头、encoder冻结。仅科学算法fixture，非训练资格自动通过。

**触发与停止**：M5消费后仍需区分成员监督与容量时才2fit；官方TabM默认不是bug，预期结果可正可负。若原控制版本/训练结构不完全相同先阻断，不加新k32控制掩盖差异。结果只归于该监督变化，不自动迁移所有TabM任务。

## 7. W-G：几何面板8项（blocked_assets，等待已派准备）

**目标**：D-GEOMETRY / I003-GEOMETRY；只测试具体checkpoint的增量信息。任务Sol、micro；每任务Monroe720和UniMol2-84M CLS768×44/45。各自复用现有scaffold43成员；新头MLP256/ReLU/dropout.1，AdamW5e-4/wd1e-4/batch128/50/8；H0 fit-only scaler、标准化Y MSE；stop/external为Sol MAE↓、micro Spearman↑；输出原numeric Y。旧CheM/Mini同split same-seed两套控制共享。

**资产版本**：必须逐字段使用scientific_assets中的代码commit、checkpoint路径、bytes/SHA，不用“Monroe最新版”“UniMol2大模型”。Monroe只取encoder表征，不调用其TabPFN后端。UniMol2必须CLS768与return_repr=True，而非分类头logit或atom平均的替代。

**现有准备不重做/不加量**：原32无标签train panel、每encoder≤12forward尝试、24synthetic head总预算由原链执行；本研究不发起任何forward。仅当该准备回执及主控准入通过，未来全任务编码各task/encoder一份完整原train cache，四份共享八头。已在当前准备产生的可复用asset/encoding不要再计费或重复读取。

**明确不变项**：全部原行、原分子字符串与ordered索引；冻结encoder参数和buffers；固定seed42几何策略；全部分支合计20秒超时；无atom crop、无隐式清洗/去重、无额外样本；失败不会变成只评成功子集。

**实现风险验收**：Monroe strict loading按encoder键覆盖验证，BatchNorm eval+buffer不变，forward图mutation不跨样本污染，重复SMILES保留多行，虚节点原点规则显式记录；UniMol2验证max_atoms/seed/multiprocess真正透传、没有默认128随机裁剪，atoms+coord路径保留所需bond语义，禁止静默HF下载/全局env更改。任何修复改变checkpoint输入语义都生成新资产版本，不冒充原版。

**许可与覆盖**：代码MIT/BSD/Apache的公开文本不能替代checkpoint与依赖通知的实际绑定；不接受TabPFN gated license/token。32probe通过不证明5045或770完整train全部可编码；全row失败率和fallback类型按无标签聚合记录。若不能全覆盖则阻断该task/asset，不填零、不裁剪、不筛掉分子。几何缓存没有质量疗效含义。

**成本／fallback**：4共享编码cache＋8头，几何全task成本未知，既有32probe不足精确外推；R/X不受此阻断。两个encoder不是必须同时成功；单独已准入的格可以由主控授权，但不能替换成更大的checkpoint补位。报告只归完整recipe，不证明PCBA/3D几何单因果。

## 8. 既派任务的只读接收规则（0新增fit）

- AMESdual4：先固定两个stop selector，再各自stress；samecheckpoint/view去重。best/last、A/B映射明确。失败不能变成选择stress较高的selector继续。
- window12：固定200轨迹；因果重放50/8、200/8、200/full，保存真实last/optimizer/RNG；50前patience终止的两策略应重合，不能伪造额外fit。
- M5/M6：原18+8个seed展开fit不进入本新增数组；M5旧k32六控制共享；M2十二skip仍skip。
- MoL余4：CYP MLP/TabM×46/47已派，不另补分类probe；与原12成面板报告全部负/混合。
- TabICL16：contextfit单列，按实际fit-context/预处理范围、random_state、模型版本、输出尺度验收，不升级为梯度训练；没有结果就保持unknown。

## 9. 取回、评分与交接

每条真实完成run输出完整科学配置、source/cache/partition/row身份、实际学习steps/停止原因/best epoch、模型与scaler版本、参数/buffer不变回执、完整无真值stress预测、固定评分回执及失败/成本记录。只验证新增变化及真正冲突，旧验收同版本同用途直接复用。准备方不获逐行Valid Y/残差；汇总反馈可含task/run/metric/方向/来源，不能包含可逆小群差分。

训练输出通过不等于模型质量好，评分好不豁免冻结/文件边界失败。worker业务结果与supervisor/资源失败分开保留。固定scorer每unique prediction一次；nativeStress、wholeValid、fixedcohort、composite独立计数。所有seed/任务格包括负、tie、unsupported都报告。

**成本台账**分别记P准备、E编码、H学习、R取回、S评分、J交接、Q研究及重叠区间；使用budget_scenarios的公式，不把GPU秒当端到端。首个自然获准fit顺带校准，不额外建试跑任务。

**正常评审节点**是完整对照块回齐、明确skip或决定性前提被推翻；不每训一头问Pro。剩余问题超出本矩阵、新family/接口出现实质改变、或所有有信息分支耗尽时才需要新研究。所有继续/停止均由主控核验与登记。

## 附表：确定候选的逐task/config/split索引

表中每行model seeds均为44、45，split seed为43；完整目标、资产SHA、scaler和控制在同ID的JSON逐项展开。这里只缩短显示，不是用跨task占位符替代矩阵。

| Proposal | Stage | Task | 资产 | Split | scaler | loss | 新fit |
|---|---|---|---|---|---|---|---:|
| `P003-R-clearance_microsome_az-chemeleon-canonical-half` | R | clearance_microsome_az | chemeleon | clearance_microsome_az:canonical:s43:v1 | F010 | HalfMSELoss | 2 |
| `P003-R-clearance_microsome_az-chemeleon-canonical-rank` | R | clearance_microsome_az | chemeleon | clearance_microsome_az:canonical:s43:v1 | F010 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-R-clearance_microsome_az-chemeleon-scaffold-half` | R | clearance_microsome_az | chemeleon | clearance_microsome_az:scaffold:s43:v1 | F010 | HalfMSELoss | 2 |
| `P003-R-clearance_microsome_az-chemeleon-scaffold-rank` | R | clearance_microsome_az | chemeleon | clearance_microsome_az:scaffold:s43:v1 | F010 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-R-clearance_hepatocyte_az-chemeleon-canonical-half` | R | clearance_hepatocyte_az | chemeleon | clearance_hepatocyte_az:canonical:s43:v1 | F010 | HalfMSELoss | 2 |
| `P003-R-clearance_hepatocyte_az-chemeleon-canonical-rank` | R | clearance_hepatocyte_az | chemeleon | clearance_hepatocyte_az:canonical:s43:v1 | F010 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-R-clearance_hepatocyte_az-chemeleon-scaffold-half` | R | clearance_hepatocyte_az | chemeleon | clearance_hepatocyte_az:scaffold:s43:v1 | F010 | HalfMSELoss | 2 |
| `P003-R-clearance_hepatocyte_az-chemeleon-scaffold-rank` | R | clearance_hepatocyte_az | chemeleon | clearance_hepatocyte_az:scaffold:s43:v1 | F010 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-R-vdss_lombardo-chemeleon-canonical-half` | R | vdss_lombardo | chemeleon | vdss_lombardo:canonical:s43:v1 | H0 | HalfMSELoss | 2 |
| `P003-R-vdss_lombardo-chemeleon-canonical-rank` | R | vdss_lombardo | chemeleon | vdss_lombardo:canonical:s43:v1 | H0 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-R-vdss_lombardo-chemeleon-canonical-mse` | R | vdss_lombardo | chemeleon | vdss_lombardo:canonical:s43:v1 | H0 | MSELoss | 2 |
| `P003-R-vdss_lombardo-chemeleon-scaffold-half` | R | vdss_lombardo | chemeleon | vdss_lombardo:scaffold:s43:v1 | H0 | HalfMSELoss | 2 |
| `P003-R-vdss_lombardo-chemeleon-scaffold-rank` | R | vdss_lombardo | chemeleon | vdss_lombardo:scaffold:s43:v1 | H0 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-R-vdss_lombardo-chemeleon-scaffold-mse` | R | vdss_lombardo | chemeleon | vdss_lombardo:scaffold:s43:v1 | H0 | MSELoss | 2 |
| `P003-X-clearance_microsome_az-minimol-canonical-half` | X | clearance_microsome_az | minimol | clearance_microsome_az:canonical:s43:v1 | H0 | HalfMSELoss | 2 |
| `P003-X-clearance_microsome_az-minimol-canonical-rank` | X | clearance_microsome_az | minimol | clearance_microsome_az:canonical:s43:v1 | H0 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-X-clearance_microsome_az-minimol-scaffold-half` | X | clearance_microsome_az | minimol | clearance_microsome_az:scaffold:s43:v1 | H0 | HalfMSELoss | 2 |
| `P003-X-clearance_microsome_az-minimol-scaffold-rank` | X | clearance_microsome_az | minimol | clearance_microsome_az:scaffold:s43:v1 | H0 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-X-clearance_hepatocyte_az-minimol-canonical-half` | X | clearance_hepatocyte_az | minimol | clearance_hepatocyte_az:canonical:s43:v1 | H0 | HalfMSELoss | 2 |
| `P003-X-clearance_hepatocyte_az-minimol-canonical-rank` | X | clearance_hepatocyte_az | minimol | clearance_hepatocyte_az:canonical:s43:v1 | H0 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-X-clearance_hepatocyte_az-minimol-scaffold-half` | X | clearance_hepatocyte_az | minimol | clearance_hepatocyte_az:scaffold:s43:v1 | H0 | HalfMSELoss | 2 |
| `P003-X-clearance_hepatocyte_az-minimol-scaffold-rank` | X | clearance_hepatocyte_az | minimol | clearance_hepatocyte_az:scaffold:s43:v1 | H0 | accepted half-MSE plus half pairwise-softplus | 2 |
| `P003-N-clearance_microsome_az-chemeleon-scaffold-mse` | N | clearance_microsome_az | chemeleon | clearance_microsome_az:scaffold:s43:fit75_v1 | F010 | MSELoss | 2 |
| `P003-N-clearance_microsome_az-minimol-scaffold-mse` | N | clearance_microsome_az | minimol | clearance_microsome_az:scaffold:s43:fit75_v1 | H0 | MSELoss | 2 |
| `P003-N-clearance_hepatocyte_az-chemeleon-scaffold-mse` | N | clearance_hepatocyte_az | chemeleon | clearance_hepatocyte_az:scaffold:s43:fit75_v1 | F010 | MSELoss | 2 |
| `P003-N-clearance_hepatocyte_az-minimol-scaffold-mse` | N | clearance_hepatocyte_az | minimol | clearance_hepatocyte_az:scaffold:s43:fit75_v1 | H0 | MSELoss | 2 |
| `P003-G-solubility_aqsoldb-monroe720-scaffold-mse` | G | solubility_aqsoldb | monroe720 | solubility_aqsoldb:scaffold:s43:v1 | H0 | MSELoss | 2 |
| `P003-G-solubility_aqsoldb-unimol2_84m_cls-scaffold-mse` | G | solubility_aqsoldb | unimol2_84m_cls | solubility_aqsoldb:scaffold:s43:v1 | H0 | MSELoss | 2 |
| `P003-G-clearance_microsome_az-monroe720-scaffold-mse` | G | clearance_microsome_az | monroe720 | clearance_microsome_az:scaffold:s43:v1 | H0 | MSELoss | 2 |
| `P003-G-clearance_microsome_az-unimol2_84m_cls-scaffold-mse` | G | clearance_microsome_az | unimol2_84m_cls | clearance_microsome_az:scaffold:s43:v1 | H0 | MSELoss | 2 |
| `P003-K-clearance_microsome_az-chemeleon-scaffold-mse-w128` | K | clearance_microsome_az | chemeleon | clearance_microsome_az:scaffold:s43:v1 | F010 | MSELoss | 2 |
| `P003-K-clearance_microsome_az-minimol-scaffold-mse-w512` | K | clearance_microsome_az | minimol | clearance_microsome_az:scaffold:s43:v1 | H0 | MSELoss | 2 |
| `P003-T-cyp2d6_veith-minimol-scaffold-mean_bce` | T | cyp2d6_veith | minimol | cyp2d6_veith:scaffold:s43:v1 | H0 | negative_log_likelihood_of_mean_member_probability | 2 |
