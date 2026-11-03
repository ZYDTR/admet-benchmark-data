# 下一批科学接口与条件派发指南

request_id：`admet-pro-next-research-20261103-004`  
input manifest：`d5c998c3c95c40a7ed0555da01cb566a46457f65f9eb279530cd4c797d703fae`  
性质：**proposal_only；本文件不授权准备方训练、编码/推理、接训练主机、取逐行Valid Y/残差或扩大任何现有作业。** 所有实际ML动作及私有评分由主控另行登记。工具、部署、并发与运输细节可由执行角色在额度内选择；科学配置、数据与比较单位不能自行改。

<a id="0"></a>

## 0. 先复用，而不是重演验收

实际已完成：R/X44、capacity26、window12、AMESdual4、CYP3A4lr8、MoL16、TabICL32。T2两个梯度头、Hep8八个冻结上下文已经派发，当前0质量结果。它们都不进入新学习表。M2十二个数学等价槽是skip，不能重开；95复合分数已经存在，不能把“试集成”写成未做过的泛泛新方向。[E-STATUS]

复用现成CheM2048和Mini512身份匹配cache、原nativeTrain成员及既有固定评分定义。旧可信参数/buffer、行身份与完整评分验收不用全量重做。新的产物仍要绑定自己的输入/配置/初始状态/输出行身份、目标尺度和接收回执。运行失败、资源违规、监督故障与worker业务结果各自保存；没有用分数覆盖故障的例外。

<a id="1"></a>

## 1. P004-H：肝细胞配对信息判别（new_code）

**目的与问题**：`I004-RANK`。既有rank6/8，两个负例在CheM/scaffold44和Mini/canonical45。检验rank配对中较大标签间隔是否有用，还是仅减少pair数量/改变梯度随机性。不要改变原标签、MSE系数、lambda、表示、head或训练窗口。

### 1.1 完整首批和条件后续

| stage | task | 表示 / scaler | 既有split | 新配置 | model seeds | 新gradient fits |
|---|---|---|---|---|---|---:|
| H1 | clearance_hepatocyte_az | CheM2048 / F010 | scaffold，593/85/170 | gap；uniform_matched | 44,45，每配置两seed | 4 |
| H1 | clearance_hepatocyte_az | Mini512 / H0 | canonical，591/86/171 | gap；uniform_matched | 44,45，每配置两seed | 4 |
| H2（条件） | clearance_hepatocyte_az | CheM2048 / F010 | canonical，591/86/171 | gap；uniform_matched | 44,45，每配置两seed | 4 |
| H2（条件） | clearance_hepatocyte_az | Mini512 / H0 | scaffold，593/85/170 | gap；uniform_matched | 44,45，每配置两seed | 4 |

每一行的两个配置在`next_experiments.json`已经展开成两条proposal，不让准备方自行选mask/任务。H1共四proposal八fit，H2另四proposal八fit。父dense-rank与HalfMSE按同rep/split/seed复用；H1旧控制8fit，完整H1+H2旧控制16fit，计一次，不重训。

**资产**：CheM weights SHA `c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651`；Mini code `41642328affbb35e4950b7b7a9020aa95919b503`、weights SHA `a3061e1cdbbd5e544168fbf8c1e01836c8c19ac030891d495a2ae9f29cfe97a7`。不生成新encoder输出，不改变pooling。

**split绑定**：复用确切原行顺序，不按一个seed重生成成员。Hep canonical记录`ref-0d0360fdbd73b25c`，SHA `e00c41ebfa889075448beb6cdd05c13111cdab729f3c21bee8df9aef52c04741`；scaffold记录`ref-fcdec596afdf97c0`，SHA `7a934f1a274048fe5dfd4bf16ba967d5dde2e1c99bed704ad82c5ce1546aafb3`。partition记录hash与成员manifest hash是不同对象，不互换。旧s43是谱系，不是本轮再次抽样。

### 1.2 生产接口保持项

使用已验MLP：D→256→1，ReLU，dropout0.1；AdamW lr0.0005、weight_decay0.0001、betas(0.9,0.999)、eps1e-8；batch128、max_epochs50、patience8、min_delta1e-7、最早并列best，无scheduler或gradient clipping。early stop为nativeTrain.stop的Spearman最大化，外部仅nativeTrain.stress Spearman最大化。

X统计在本split fit上用float32 population mean/std；`d0=where(std<1e-8,1,std)`，H0=d0、F010=max(d0,.01)。目标均值/总体std继承fit-only float64规则，传入loss的target tensor dtype沿用父配置，不自行加log/rounding。所有目标必须非恒定或按父guard拒绝。输出回原numeric Y尺度，仅逆变换一次；不推断未确认物理单位。

两新臂共享实际初始head tensor、训练RNG和新记录的epoch/permutation；允许读取已批准的原初始化状态元数据/只读tensor绑定，不能为了匹配初始状态试seed或重跑旧头。旧run没有记录的batch trace必须仍写unknown。

### 1.3 唯一新接口：PairMaskRank004-v1

这不是现有CLI枚举。准备方需要新增可审读objective block，产出真实新code hash；本文件没有预先伪造该hash。

q：从父目标变换后实际训练target tensor值（通常float32）取fit全体，升为float64做正pair间隔统计；所有i<j的正绝对间隔中位数，偶数项取中间两项算术平均。只fit标签，不接触stop/stress/Valid Y。记录q与tie总量。

当前batch列出不等实际训练target值的无序pair。gap臂选间隔≥q的pair，数量m；uniform臂从同batch全部不等pair里选恰好m个。排序键：

`SHA256(UTF8("P004PAIR-v1|{task}|{split_id}|{model_seed}|{epoch_1based}|{batch_index_0based}|{min_row_index}|{max_row_index}"))`

按digest字节序再按row-index pair排序，取前m；不消耗torch/numpy/loader RNG。m=0则pair项与其梯度为零。batch里即使部分pair不参与rank，所有行仍参与MSE；没有删除或改写任何原始行/标签。

`L = .5*mean((prediction−zY)^2) + .5*mean softplus(−sign(z_i−z_j)*(prediction_i−prediction_j))`

第二项只对所选pair求mean。两臂lambda与pair数量相同，不声称梯度范数相同。q只取0.5分位一次，不允许根据stress改q、coef或排序边界。

### 1.4 独立fixture与预期意义

准备阶段只允许主控批准的纯函数/合成无真实标签fixture，不代表授权模型载入或优化更新。

- objective输入fixture z=[−2,−1,1,2]时，六个正gap排序为1,1,2,3,3,4，q=2.5，gap选择三pair。uniform也必须恰三pair，重复调用key一致；改变模型RNG状态不能改变固定key结果。该fixture直接测试loss输入，不声称这四值本身有单位方差。
- predictions全0时两臂pair loss均ln2，MSE=2.5，总loss=1.25+0.5ln2。两套独立标量实现和实现中的向量路径应一致；这不是ADMET指标。
- 相同target批内pair空时仅保留HalfMSE；父dtype使极近原标签合并时保留原target semantics并记合并总量，不修改标签解决。
- 外部预测逆变换一次后shape与原stress成员/row_index一致，重载变换不fit新统计。fixture验证的是函数/尺度/隔离，不是泛化质量。
- 若所有实际已知batch成员下两臂选择数学等价，可以零fit证明后skip，不为补数量强行训练。

**产出**：新source/code manifest、逐proposal配置、mask定义/fit统计、独立fixture、原cache/split/init引用、训练epoch/stop选择、selected/final head、实际step/permutation/组件loss聚合日志、原尺度stress预测与行身份、固定评分入口回执。不要导出逐行ValidY或残差。

**预算/fallback**：H1八新梯度fit；H2八有条件新增。0新encoderpass。任何身份、label边界或冻结问题停受影响项；代码fixture失败只修实现，不以训练试错。头CPU作业基数约23.3秒只是R44类比，mask/准备/交接未知，见budget；实际限额由主控先登记。

<a id="2"></a>

## 2. P004-SOLCTX：Sol读出交互（new_code，非梯度）

**触发**：先消费已派Hep8。若结果和现有Micro/Sol证据使“是否采用冻结上下文读出”成为实际决策，才解锁；否则跳过。不重复Hep8，不把这个分支当等队列的填充。

**矩阵**：task=`solubility_aqsoldb`；已有scaffold fit3531/stop505/stress1009；CheM2048F010与Mini512H0各context RNG44/45，共4context fits、0gradient。旧同split两表示MLP44/45四个控制复用。

**固定读出**：TabICL2.2.0 code `d83091b845a8c5f7c087bd54964f755a9e560f45`；HF revision `4dcd344ece2c00be9e831fdd35bed57b5ad83e19`；regressor文件`tabicl-regressor-v2-20260212.ckpt`，SHA `0db9cb538f114e79026bf08f45f41ad8dd7ad2de2aaca9a5ca8cd3bd9748ae7a`。不是classifier、TabICL家族任意checkpoint或TabPFN。

真正API为`TabICLRegressor(...).fit(Xfit,yfit)`再`predict(Xstress,output_type="mean")`。本矩阵显式kwargs：n_estimators8，norm_methods[none,power]，feat_shuffle_method=latin，outlier_threshold4.0，batch_size1（ensemble推理batch，不是训练mini-batch），kv_cache="repr"，allow_auto_download=False，device=cuda，use_amp=False，use_fa3=False，offload_mode=cpu，disk_offload_dir=None，n_jobs2，verbose=False，inference_config=None，random_state分别44/45，model_path必须解析到已批准SHA的本地资产。不存在或版本不合即停止，不安装下载替代。

源码在固定commit的constructor/fit/predict已经核对：`.fit`构建数值转换、fit-only Y scaler和特征ensemble，可内部做forward缓存；不是梯度学习。`predict(mean)`已逆变换回原Y，禁止外部再inverse。使用repr cache只改变缓存路径，不把其生成称新分子编码。cache/参数/buffer的允许变化要分开：上下文与KV状态可以按准入接口形成，预训练参数及注册buffers不得改变。n_jobs不能被当成所有BLAS/native线程的全面上限，实际资源需记录。[X-TABICL-REGRESSOR]

**数据**：只fit3531原行标签；stop505完全保留且不查询；stress1009不参与拟合。所有四context及其身份先封口，再按授权一次得到每context stress MAE。不增加Valid/test查询。模型RNG不是MLP初始化种子，即使都是44/45也只能作完整读出配方对照。

**接口fixture**：无真实labels的mock estimator验证调用只见fit；校验kwargs和输出scale contract；在授权实际context作业内记录parameters/buffers不变、context IDs与query隔离、所有原行、实际内部forward数和公开predict数。此研究不会执行这些调用。对现有已接受checkpoint冻结验收可复用，但新context的边界仍要留证。不得以“auto-download=False”误以为已经验证本地model_path或许可。

**成本与失败**：3531行大context不能用532行Micro经验等比例保证；CPU offload与全部预处理峰值RAM也记录。fullcontext超预算则停止，不偷偷降n_estimators、启AMP、抽样或PCA后保持同配置名字。当前first MiniCaco44旧internal-forward数未知仍保留；新fourcontexts要实测，不推计成已完成calls。

<a id="3"></a>

## 3. G8继承几何判别（blocked_assets）

保留`P003-G-{solubility_aqsoldb|clearance_microsome_az}-{monroe720|unimol2_84m_cls}-scaffold-mse`四个原ID，每项44/45，共8新梯度fit。没有再登记第二套G8。相关准备成功、probe、source静态接受都不等于这8头已执行。

### 3.1 输入、pooling与新producer门槛

源权重/代码/pooling及确切bytes/SHA见scientific_assets.json和analysis §Q6。Monroe720保留发表virtual node设置；Uni84M返回CLS768，绕过classifier。原geometry seed42、20秒完整过程超时含fallback的已定规格继续绑定；准备方不得自行换种子、cropping、氢处理、构象数、coordinate convention或fallback。它们必须在将来producer配置中逐项显式列出并由主控接受；这些值尚未完整绑定时保持blocked，不拿default猜。

Uni v4必须固定40文件manifest `66cb65a94d9dab2e7fabbf8aeace7efaaad86ebe8460c421f2023d9d08d019a8`；这只复用静态接受，不重复全40文件审计或冒称实际运行。Monroe未来producer协议尚未准入，需要单独版本化；旧5/9缓存均不得重用，不允许用后来重新加载的hash给旧缓存补签。

**fresh producer必须证明**：原producer调用前与最后调用后完整参数及all buffers不变；eval/no梯度；原行（含重复SMILES）一一输出；完整任务覆盖，无删除/补标签/无声crop；失败/timeout/fallback逐原行状态保留；独立SMILES→图→坐标→pooling接口和重载一致；strict=False不能掩盖encoder missing/unexpected keys。不得引入TabPFN受控条款或外部样本学习。

**失效fixture的含义**：重复输入不能dict合并；同图重复forward不得受图就地mutation污染；Monroe BN buffers、virtual-node坐标依赖要明确；Uni kwargs应真正传到maxatoms/seed/multiprocess，无bond的atoms+coords不充作完整分子图。只有主控将来批准的producer范围才可实际模型调用，准备角色不能自己增加探针次数。

### 3.2 训练配方与比较

每task/encoder生成一次完整officialTrain cache，两个headseed共享。Sol完整5045行、micro770行，四pass。不会编码官方Valid/test。只把对应旧scaffold成员切给fit/stop/stress。

MLP单隐层256、ReLU、drop0.1；AdamW5e-4/wd1e-4，betas/eps同既有；batch128、50/8、min_delta1e-7、最早best；H0 X、fit-only标准化Y MSE；Sol stop/native MAE最小化，micro stop/native Spearman最大化；原numericY一次逆变换。旧CheM/Mini同split同head控制直接复用。该比较改变表示、维度、第一层参数量和预训练内容，是bundle，不叫geometry-only因果。

新编码是最贵且未测的共享准备，不能拿头训练秒数预算全流程。任何producer/coverage/许可失败只阻断相应asset；不因为另一方法ready就替换候选，不给失败挑更好子集。两任务均无可改变决策收益则收口这个固定geometry面板，不加seed或池化搜索。

<a id="4"></a>

## 4. T2与Hep8：唯一允许的下一动作是消费既定结果

T2 request `admet-tabm-memberloss2-training-20261103-001`；两头`tml2-cyp2d6_veith-minimol-tabm-scaffold-meanprob-s44/45`，主比原AP0.7688841197331191/0.773429274836159。不得发第三个seed、改k或额外meanprob权重。低loss不是AP；两正/两负/混合/失败按原规则记录。

Hep8 request `admet-tabicl-hepatocyte8-inference-20261103-001`；CheM/Mini×canonical/scaffold×contextRNG44/45。0新头。必须分开四个同context-RNG表示主比、旧FullMSE均值和旧rank均值；相同数值seed不使这三个问题变同初始化因果比较。若Mini被救回，优先读出解释、不自动N8；若反转，保留scheme条件；若失败，只能记录运行问题。

<a id="5"></a>

## 5. GQ12：固定群新证据，不放训练数组

由主控另行批准私有固定评分。完整请求在cohort_evidence_requests.json。Sol M6四已存预测×两个旧群=8cells；CYP TabICL四已存预测×旧high132=4cells。before已发布群score复用；每个request含issue/cohort/source/run或唯一原记录selector，不发起新预测。

结果只回聚合metric/n或suppressed、run/cohort/预测/成员hash。不得拿rowwise Y/残差、成员行号、罕见化学小交集、未过门槛类别数、leave-one-out或差分。CYP low保持抑制；Caco10和clearance12不扩群。需要解释化学性质时，可给同一完整大群的无标签粗描述分布，不能把描述profile说成错误原因已经确证。

<a id="6"></a>

## 6. 交付、独立验收与成本

每个实际新fit/context输出科学配置/来源版本、输入与成员绑定、RNG角色、fit-only变换、loss/earlystop/outputscale、运行与失败、所选状态/预测行身份、唯一外部metric回执和实际费用。context的内部forward、公开predict、冻结上下文fit、gradient step、编码pass、prediction view、metric cells分列。

**不需要**：重复全部历史freeze/score/运输，遍历全库1256/更多对象，补造旧未记日志，或拿新实验代替旧真实性证明。**必须**：针对新的差分实现做fixture、针对新producer建立第一次真实性证据、针对实际矛盾核原文与对象。

小/中/大上限分别8梯度；16梯度+4context；24梯度+4context，既有T2/Hep8不混入，旧控制只计一次。GQ最多12额外群metric单列。时间记录准备、学习/上下文、共享编码、评分、取回、交接和研究，重叠不相加；只有测过的阶段报实测。主控在执行前登记资源额度和共同host/precision，不由本文件自动授予。无信息价值可跳过，禁止凑满预算。

下一次研究评审发生在完整预登记对照块收齐、实质前提被推翻、真正新科学分支出现或本计划可行动分支耗尽时；不是每个头跑完或队列暂空。原任务“继续研究”不等于必须不断训练。
