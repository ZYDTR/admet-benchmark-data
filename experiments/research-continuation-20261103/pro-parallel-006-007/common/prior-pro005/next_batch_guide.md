# Pro005 下一批科学接口与条件派发指南

request_id：`admet-pro-next-research-20261103-005`；固定输入manifest：`457fd2f1109482fdb600b708f9d29cad52ac5f5f7f81518637ca80ba28c39b8d`。本文件仅设计，不是准备、学习、访问主机或发布授权。Research Chat没有执行下列fixture或方案。主控按真实当前队列和授权登记；当前正在运行的scaffold/GEO002不改变。

## 1. 工作清单、接口成熟度与绑定

| 工作项 | 对应issue / direction | 性质 | 新工作计数 | 科学输入版本与输出 |
|---|---|---|---|---|
| W-Z 固定状态T2 | I005-CONCENTRATION / D005-TEMPERATURE | `new_code`预测视图适配；已学状态复用 | 10views，0fit/context/encoding | 原10canonical local selected states、同fit-bank/scaler/queryslot→无真值预测视图+批准群聚合 |
| W-O Half与Rank同期对照 | I005-OBJECTIVE / D005-OBJECTIVE | `new_code`，原局部头可复用但新目标/监控必须显式实现 | 20gradient | MiniMol原848×512cache，5fold各自fit/stop/outer→20新头状态/日志/私有预测与聚合 |
| W-S 固定全局距离RMS | I005-CONCENTRATION / D005-SCALE | `new_code`，只在新外层回验前预登记 | +20gradient，与O共享控制 | W-O相同cache/分区/初始化→20尺度受控头 |
| W-N SMI独立表征 | I005-NEW-ASSET / D005-SMI | `blocked_assets`；需新冻结producer及wrapper | 8gradient；2shared task encodes；0context | 指定Light40/768资产、AMES4684+PPBR1952原train→完整缓存及8头 |
| W-C 固定群/补群消费 | I005-COMMON-ERROR | `new_code`聚合投影，只有指定评分角色可做 | 复用上列预测；不增fit | cohort_register原成员与输入身份→允许汇总、不含行级真值/残差 |
| W-P 来源与去重 | I005-ASSAY-SUPPORT / I005-DEDUP | 零学习来源判断 | 0fit | 已批准元数据、原14proposal/当前ledger→有限缺口/继承记录 |

`next_experiments.json`是唯一新增确定训练数组。每条task、完整config、split、seeds独立；`diagnostic_requests.json`只放0fit诊断，不混入训练数组。`split_register.json`里的HOOF规范ID为本交付引用名，绑定真实原run及完整划分算法，不冒称当前runner已有同名CLI枚举。实际source/config codeSHA必须在准备准入时写入；null表示尚未产生，不以“new_code”代替科学参数。

## 2. W-Z：固定状态带宽视图

**目标与竞争解释。** 集中可能与端点MAE收益或共同错误同时相关。只把T从1改为2可以检验全局带宽扰动的方向，不学新几何，不把相关性当因果门，也不搜索最佳T。

**输入**：`hoof60-hep-minimol-local-canonical-f0…f4-s44/45`的已接受selected checkpoint、原H0和Yscaler、全部且仅inner-fit标签bank、原查询槽位/顺序、原CPU/dtype/kernel软件绑定。MiniMol权重`a3061e1cdbbd5e544168fbf8c1e01836c8c19ac030891d495a2ae9f29cfe97a7`不更新；复用原cache，不新编码。

**唯一改动**：`temperature=2.0`；`distance=unsquared Euclidean p2`；同W/b；其它全保持。T1预测复用，不重算既有质量指标。“W×0.5,T1”等价形式只作实现fixture，不另外记新模型、上下文或质量视图。

**验收fixture（未来准备方执行，Research不执行）**：
- FIX-LOCAL-STATE：原selected state、bank、scaler、ordered row IDs完整绑定；T1用原queryslot应在原允许数值准则内复现已验预测。不可复现时先定位，不能拿last/init或不同batch取代。
- FIX-T-EQUIV：合成固定向量验证`softmax(-||WΔ||/2)`与`softmax(-||.5WΔ||)`，double精度参考；误差准则来自浮点精度/原fixture而非质量差选择。验证不改变近邻距离次序，但可改变加权输出。
- FIX-BANK-BOUNDARY：stop/outer标签不进入bank，训练query的own-row自mask只按原row index；重复结构的其它fit原行不擅自删除。测试/Valid全不参与。
- FIX-FREEZE：该视图无optimizer、无参数更新；producer已验的Mini冻结回执复用，只核新适配边界，不做全库重复审计。

**输出**：每视图源state/hash、原输入和queryslot绑定、temperature、预测输出尺度；无标签熵/有效bank统计；指定宿主一次返回原群/补群聚合。预测文件按原规范留宿主，不向研究交付行Y/残差。

**预算与停止**：10视图，0新fit；没有原状态则只阻断对应视图，不替代猜测。T2负/零结果关闭这个固定干预，不触发T网格。量化集中下降不等于质量成功。

## 3. W-O：LocalObjectiveScale005-v1 基础接口

### 3.1 数据/划分/预处理

原官方train848行全部保留；原canonical isomeric group keys，不重算化学规范、不去重/清洗。外层group_oof5_sizebalanced_hash_v1、split_seed20261103：按(-group size,SHA256(`HOOF001|outer|20261103|canonical|`+key),key)排序，放到当前行数最少的fold，平局小fold index。每行恰一次outer，outer n为170/170/170/169/169。

inner排除当前outer，按SHA256(`HOOF001|inner|20261103|canonical|`+fold+`|`+key),key排序，以整群前缀直到>=Python round(0.125×outer_train行数)为stop，其余fit；成员按原row index升序。这里重述算法用于可核查，但生产直接绑定已验原HOOF分区，不另造新的更好分区。实际fit/stop n及分区SHA由既有安全receipt提供，本报告不编数值。

每fold独立：X float32 population mean/std(ddof0)，std<1e-8则分母1，其余原std；H0；Y float64 mean/std fit-only，非有限或无尺度则明确失败；不log、不裁剪、不改变原标签。编码cache可共享，fit的scaler和bank不能跨fold共享。原48/64其它任务缓存也不能冒充该848身份。

### 3.2 模型、训练目标与监控

配置对象由以下**新建议接口字段**构成，不声称当前runner已支持；可以实现成显式JSON适配器，不能擅自改值：

```text
interface = LocalObjectiveScale005-v1
input_dim = 512
projection = Linear(512,128,bias=True)
projection_blocks = 0
PLR = false
dropout = 0
distance = euclidean_unsquared
temperature = 1
scale_mode = free                  # O；S改为fit_global_rms
query_l2_normalize = false
topk = null
train_bank = sample floor(.5*(n_fit - batch_rows)) other fit rows w/o replacement + batch once
train_self_mask = exact original row identity
inference_bank = all_and_only_inner_fit
optimizer = AdamW(lr=.01,weight_decay=.0002,betas=(.9,.999),eps=1e-8)
batch_size = 128
max_epochs = 50
patience = 8
min_delta = 1e-7
best_tie_policy = earliest
scheduler = null
gradient_clipping = null
monitor = inner_stop_Spearman
monitor_direction = maximize
```

两目标：`HalfMSE=.5*mean((p-zY)^2)`；`HalfMSE_Pair=.5*MSE+.5*mean softplus(-sign(zYi-zYj)*(pi-pj))`。pair为当前batch全部i<j且实际目标dtype不相等；tau1；零有效pair时pairterm0。禁止再套median-gap、tail权重、q、lambda网格。

mini-batch query标签仅为train-fit.Y；候选bank标签也只来自同fit。自mask防止自己的答案进入权重读出，不能把同batch其他fit样本标签使用误称stop泄漏。预测zY逆变换一次为原尺度；softmax凸组合本来受fit标签范围约束，不加clip/calibration。

种子44/45分别绑定公共初始W/b、固定每epoch行序、独立候选抽样流，记录确切RNG状态；不要让新增pair诊断调用推进数据抽样RNG。所有新臂固定相同CPU float32头实现，协方差/目标统计可float64。早停统一Spearman↑，选择仅inner-stop；报告原尺度MAE是次指标，不用它再挑epoch。

### 3.3 独立fixture与含义

- FIX-PAIR-LOSS：手算3条不同排序和有tie的合成batch；验证交换i/j不改变总loss、排除tie、空pair返回0；单rank项的零/符号应与公式一致。验证缩放Y用同fit zY，不能在inverse后混单位。
- FIX-LOCAL-STATE：相同权重、bank、输入和抽样索引，两臂loss之外输出一致；不同目标只能在后续学习产生区别。源代码读取/fixture不是疗效证据。
- FIX-OOF-LOCK：每行外层恰一次，fit/stop/outer原canonical组互斥；所有预处理fit-only；视图无outer标签；拟合/选epoch/最终聚合分开，不能加入stop扩大bank。
- FIX-FREEZE：optimizer仅包含新Linear head；外部encoder与所有buffers不变；头梯度路径只到新W/b。无需重新编码或重审所有旧run。
- FIX-OUTPUT：同checkpoint+serialized统计重载后原尺度预测一致；sigmoid不适用回归；无原Y/残差输出到准备者反馈指南。

**学习矩阵**：5fold×2目标×seeds44/45=20。已有10local FullMSE不是HalfMSE对照，也不因分数看似接近就抵扣；它们及10MLP/10TabICL仅次级参照。新Half与Rank是同期主配对。新interface明确monitor；历史DESIGN没有暴露旧monitor，所以对旧对照不能称单因素因果。

## 4. W-S：预先锁定的尺度因素，不是见分数追加

在W-O所有值不变的条件下，新增`scale_mode=fit_global_rms`：

```text
Sigma = (X_fit - mean(X_fit))^T (X_fit - mean(X_fit)) / n_fit
S2(W) = 2 * trace(W Sigma W^T)
S0 = sqrt(S2(W_initial))           # fixed once per matched fold/seed
distance_eff = (S0/sqrt(S2(W))) * euclidean_unsquared(Wx,Wx_bank)
```

统计只用已经H0处理的fit特征；使用全部n²有序对的总体定义、包括自身零项，对应公式不需要计算n²矩阵。对S(W)保留autograd，不detach分母；S0和Sigma固定，不包含labels。bias在距离相消；S或S0无效时记数值失败，不换epsilon/temperature求好分数。无需修改MiniMol的任何参数/buffer。

**FIX-RMS**：合成向量的直接有序pair均值与trace式一致；初始化free/S距离相等；W乘任意正数时S有效距离不变；各向异性变形可改变距离，证明它不是“所有几何都无差别”。两臂相同W参数数量但有效自由度/优化正则改变，这一事实必须在结果解释保留。

S-H/S-R各5fold×2seed=20新fit；共享O20控制形成40唯一fit。预登记在Z/O任何新outer聚合消费前完成，不能按每折哪个更好补一格。小档选O就做完整O，不在看完O外层后宣称新增S是未受污染确认性实验；确需改变问题必须另记探索性研究及新选择史。

## 5. W-N：FrozenSMILightStereo005-v1，资产门槛后的独立面板

### 5.1 固定目标资产

- 官方repo/modelcard：`ibm-research/materials.smi-ted`，卡revision `414c3ea0a8603ef49d1c5bb3db336e09877c01ce`。
- checkpoint：`smi-ted-Light_40.pt`，1,155,124,350 bytes，SHA256 `baf252dbc081a00c68d2fd6ed8b08a0db0fa15244cfea442d49f0619a3a65375`。
- 实际forward读出：token202×768经flatten送入**冻结decoder.autoencoder.encoder**得768。不是对token均值，也不是原任务net。
- 固定source/词表/config与该checkpoint的关系尚未被本研究闭合；main原文只是实读证据，不允许生产runtime自动抓main。代码/适配器hash须在准入后填。
- 官方模型卡Apache-2.0不是所有依赖/权重使用的自动豁免；固定源与依赖notice、代码/模型许可证分别核验。不要借用TabICL或TabPFN许可。

### 5.2 输入和freeze验收

原行/SMILES完整保存，仅模型输入按canonical isomeric、保留盐/立体信息，不清洗、不去重。默认源码isomeric=False及truncation=True不能原样采用。对原SMILES、规范输入、token长度/覆盖提供无标签摘要；@/@@、键/电荷/环/分量token必须可追溯。fixture验证**输入信息未被预处理丢掉**，不是强求两个对映体输出必须不同（后者是科学表现，不是软件合规判据）。超过202或不受支持样本使该任务blocked，不删行/零填充/改变标签。

所有预训练参数和buffers（包括瓶颈、norm和可选模块）`eval`且冻结；encoder不进入optimizer；producer读取checkpoint并在完整调用前后固定state hash。缺key/额外key需逐项白名单解释，不能`strict=False`一概吞掉；`.detach()`不是冻结证明。正常生产的输入/输出/软件版本记录只覆盖本任务，不重复全库审计。无generation、伪标签、重构标签、teacher输出或外样本。

SMI只有这次全行producer真正通过后才是可用资产；若fixed source无法绑定或任一原行不覆盖则N整任务blocked，保留KPGT/几何独立状态，不随意换checkpoint救活矩阵。

### 5.3 具体矩阵与控制

AMES官方train4684行、PPBR1952行各一次冻结encoding，产[rows,768]的顺序绑定cache；不含Y列。复用原native canonical/scaffold分区，准确SHA在split_register；这两方案共享行，不是独立数据集。每task×scheme一个完整proposal，seed44/45，共8新头。

H0 fit-only float32统计；头768→256(ReLU,dropout.1)→1；AdamW .0005/.0001、betas.9/.999 eps1e-8、batch128、max50/pat8/min_delta1e-7、earliest；无scheduler/clip。AMES BCEwithlogits无posweight，stop AUROC↑，输出sigmoid正类概率；PPBR fit-zY MSE，stop original-Y MAE↓，输出逆变换一次。每split的fit/stop/stress与旧控制身份一致，不能重抽。

历史控制：AMES CheM/Morgan，PPBR CheM/Mini；各两scheme×两seed，共16个既有梯度fit只数一次。保留旧控制真实scaler、数据、head、monitor，不为“匹配”重写历史。该新表示改变输入维度/头参数数，是bundle，先评价完整recipe，不声称纯encoder因果。验证原完整群+补群；某旧群n<20/类别支持不足则按规则抑制新数值，而非小群反查个体。

## 6. W-C：安全聚合回验合同

所有定义和完整成员入口在cohort_register：当前10组及其补集、原31/32共识错误群、全848、旧306、新542、端点130/97、中段621；AMES/PPBR旧blindspot及同一stress补群另有身份。固定这些成员，不按新模型重新分组以制造修复。当前组基于结果选取，回验也须标retrospective。

获准评分方保留行级Y/预测/残差，只返回task、原输入/split身份、cohort_id、定义时点、n/允许组数、方法/seed或固定等seed平均、主指标及方向、原尺度MAE、配对差与现有条件区间方法、suppression标记和互补群结果。每fold先平均44/45预测再计算Spearman、五fold等权；pooledrho仅描述。**不要把两seed分数平均冒充平均预测评分。** 本Chat不评分、不获取行数据。

未来群数值发布沿用宿主抑制（至少n20，分类各类别至少5）及重叠/差分披露检查；“每组都n20”并不自动防止组合还原。旧已经批准的小群事实可以引用，但不能因此新增更细交叉。原n=0组指标null，未知fit/stop数null不伪造。不得加入任意浓度阈值门、邻居标签明细或分子逐行error表。全部实验选择先锁定，汇总服务只做完整指定对比，不能让准备方对标签反复查询。

## 7. 继承和不执行清单

原HOOF scaffold30进行中；不改变它的code/config/seed或再注册60。ME40 Pair16和B24已实际完成；固定gap路线关闭，不再扫分位/lambda。M5/M6/window12/lr8/T2/Hep8均是历史已完成，不再pending。GEO002 freshproducer已派；Uni G4使用原proposalID继承，Monroe G4保持blocked，不新派任一producer。原P004-SOLCTX4若trigger满足仍用原配置/ID，不用HOOF的norm=null/kv_cache=false替代原方案。详见prior004_disposition。

## 8. 预算、批次与收口

小20、中40、大48新梯度，0新context；Z10视图另列。O/S不新编码；N两任务共6636原train行共享两次编码。既有控制分别30/30/46，不计新学习。预算为上限，不是必须用完。

原CPUworker575.703875s/40成功混合头只能作数量级参照，20/40local头线性算式288/576s，不是HOOF模型或新SMI性能实测。SMI编码/内存/头时长、准备人时、取回/聚合/交接未知；用真实关键路径估算，不加重叠角色时间、不编GPU小时。新准备仅在明确已有缺口下实施；不为每个已知小头安排预试跑。

**收口按问题**：Z若改变集中却不修复，则固定平滑解释缩小；O/S区分目标/尺度及其交互但不保证唯一因果；N若平均增益没有旧盲区修复，则分别记录而非整体关闭issue。所有负/零/失配/skip保留。若冻结/身份/权限失败，停止受影响方案并交主控；科学结果不足也不无限扩seed。下一次研究在完整约定对照、关键反证、资产准入实质改变选择或原scaffold返回后按信息需要触发，不按单头或固定分钟调用。

### SMI producer数值路径补充（同一候选，不增加fit）

Producer基准固定CPU/float32/no AMP、batch32；不得由源码`is_cuda_available`自动迁移模块。202为包括special tokens的总长度。官方公开config已通过固定revision的重定向读到，但`train_decoder=1`和500epoch是上游示例训练设置，不用于本项目；在未来获准准备中checkpoint实际hparams须与声明架构一致，不一致则阻断而非静默改模型。随机特征/rotary等全部已注册buffers须绑定和保持，不能以eval或detach替代验证。若需要另一设备/批大小/dtype，是单独数值producer变更验收，不暗中替换当前候选。CPU编码成本未知，正常producer准入前不估造耗时。

**平台与自由尺度补充界定：** N8新头固定CPU float32/no AMP；旧控制的实际平台沿原验收回执保留，未经原回执证明，不声称CPU/GPU等效。O自由尺度臂不使用S0/S，也不添加S相关失败门；S0/S仅是S臂定义的一部分。所有新臂共同执行通常的有限值、身份和冻结边界检查。
