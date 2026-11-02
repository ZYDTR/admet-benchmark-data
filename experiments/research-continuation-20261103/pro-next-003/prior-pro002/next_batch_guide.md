# 下一批科学准备与连续实验指南

request_id: admet-pro-next-research-20261102-002  
固定输入：f65d8149a897ea1db64c6f7cb16e52e06987229a / manifest 1fce919c9e7c6ee47ff7572446723966c83056c197a65283d0ee4790a38bae91。

**这是交给主控归并的方案，不是训练、Agent派发、模型加载或新资产下载授权。** 已派48按原科学配置继续，不被本指南中途修改；先到的真实结果可由主控按截止增量核对。准备、训练和评分角色只收到各自已准入投影，不把private scoring真值发给准备/训练方。

## G0. 共用科学契约与零fit准备项

输入为各任务原始train行及只读盲Valid输入、已验冻结原特征缓存、源版本与完整原行身份。原始分区/行/标签不删不改；相同task/split/row_index只是必要键，必须与原输入版本和cache schema共同绑定。不要重新编码已有CheM/Mini/Morgan后假称同一控制表示。旧控制通过本报告controls.json的实际来源与唯一选择器解析；别把slot/alias当新的物理fit。

CheM权重SHA `c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651`，2048原特征；Mini权重SHA `a3061e1cdbbd5e544168fbf8c1e01836c8c19ac030891d495a2ae9f29cfe97a7`，code41642328affbb35e4950b7b7a9020aa95919b503，gnn:15/global_max_pool512；Morgan RDKit2024.09.6/radius2/2048bit/chirality/bondTypes/ringMembership启用，countSimulation关闭、identity。不是执行LLM底座。[E-ASSETS、E-OLDGUIDE]

默认production字段是`head.feature_dim/hidden_dim/activation/dropout/optimizer/lr/weight_decay/batch_size/max_epochs/patience/seed`与已登记split/monitor；AdamW betas(0.9,0.999)、eps1e-8、无scheduler。实验数组里的新科学字段仅是适配器实现规格，不暗称旧runner CLI已经接受。尤其禁止向TabM.make传`arch_type=plain`；plain深MLP是另写的新模块。Mini的floor、fixed-trajectory和TabICL都是新接口门槛。

每个split单独用fit行计算feature mean/std(float32、ddof0)，std<1e-8先将分母置1；H0用此分母，F001/F010再下限0.001/0.01。原样序列化并预测复用，不在stop/Valid/test重拟合。回归fit-only Y统计float64，constant sigma按原规则置1；标准化Y训练、预测inverse一次。分类连续sigmoid概率，不能硬阈值替代AUROC/AP。具体训练loss、stop和外部metric分离见每个proposal。[E-OLDGUIDE]

### G0-A：继承什么，不重复什么

继承同版本已验的冻结、行序、固定评分和运输回执；不重算556个整体Valid、不重验全库586原件。不继承不覆盖当前用途的证明：新encoder或新适配器要验它自己，BBB旧H0s46缺after保留，不能用新run补回旧事实。监督器/业务失败和科学评分分栏，不因分数好把违规或资源失败改成通过。[E-ISSUES]

### G0-B：所有新接口的独立验收fixture（不是训练数组中的假实验）

1. **身份**：输出行数/原task/split/row_index与输入映射完整一致；原顺序、重复原行、缺失/解析mask不私自清除。每个cache与输入URI/hash/encoder+pooling版本绑定；旧控制摘要直接引用，不重制旧审计。
2. **统计隔离**：合成非标签fixture包含常数列、near-constant列、普通列；只fit子集，修改stop/query行不能改变fit统计。分母先constant替换再floor；保存/重载后相同数值。每新split都重新fit统计，不继承另一个split的mean/std。
3. **目标与输出**：合成Y的mean/std逆变换单次可逆；二分类正类映射明确；TabM形状(B,k,1)，成员loss均值与推断概率均值手工计算相符。loss/early-stop/external指标字段不可用task-native泛称。
4. **冻结**：只对变更相关的encoder/预训练predictor核params和buffers；optimizer组只能含新模块；eval并不自动证明buffer不变。任何inference缓存与真正预训练state分开列出。
5. **重载**：最佳checkpoint与其对应transform共同保存；预测重载的有限性/行身份/尺度一致；nan/inf是失败，不能删行求分。没有损失曲线不能用一个最后checkpoint冒充原best。
6. **可重复轨迹**：M3/M4/M8的eval/logging不推进训练随机状态；batch顺序/optimizer每步一致；不把额外selector当额外fit。prefix不一致要如实变成新实现bundle，并停止声称纯epoch对照。

输入的fixture允许在未来主控批准的准备环境里执行无参数更新检查；本轮Chat没有执行这些fixture或模型前向。预期结果是明确的不变量通过/失败，不是预期质量分数。

## G1. 首层22fit：四个互补问题，不复制48

### M1：半衰期rank信息与MSE尺度，8fit，new_code

问题：half F001四seed方向正但绝对不稳；原ranking4尚未执行。输入为原CheM2048F001缓存、raw43 fit/stop、modelseed44/45/46/47；对照是原fullMSE F001四项，直接复用。新rank4采用原`astra003-ranking-half_life_obach-f001-s44/45/46/47`身份，不再平行创建同配方；另新增0.5MSE四项。

rank loss精确为0.5MSE+0.5mean softplus(-sign(ΔzY)Δzpred)，所有batch内i<j且Y不相等的pair，temperature1，零pair返回0；MSE和rank项各自mean。固定AdamW/batch/50epoch/pat8，stop Spearman↑，原Y输出、外部Spearman↑。不要换成sum reduction或按pair数同时扩大loss系数。

fixture：三个Y含tie时只计两个可用pair；相同预测rank项为log2；没有可用pair为0；交换两样本不改变loss；MSE-only尺度控制确为0.5倍。输出每epoch两个loss分量、eligible pair数（train内部汇总）、best/last epoch和既有合规预测包，不输出Valid残差。若rank不胜scale，停止该pairwise归因/无穷lambda网格。依赖原排名接口准备；不依赖48等待。

### M2：MiniMol内floor，6fit，new_code

任务PPBR/Sol/microsome，Mini512H0控制46/47复用，唯一变更floor0.01。不是把CheM的绝对floor解释成同生物单位。先无标签检查Mini的std分布、被floor改变维度数、常数处理与极值；若转换与H0完全相同跳过对应2fit，不另选floor凑数量。

输出MiniF010 scaler JSON/np无标签统计、同512→256头、MSE标准化Y、PPBR/Sol MAE↓、micro Spearman↑、原Y预测。保存cache/source/row映射；允许本模块晚于准备，但不因无新encoder而冒称零准备。后续M6的Mini256F010复用此结果，不再单列一次baseline。

### M3：AMES同轨迹双stop选择，4fit，new_code

输入同CheM2048H0和Morgan2048identity。新canonical四路split43使用`pro002_stop_swap_v1|43|groupkey`的SHA256排序，whole-group先累计到round(.1N)为finalstress，再各round(.1N)为stopA/stopB，其余fit。保留原行、解析失败RAW::原字符串，不去盐/互变异构；fit>=50%N，各stop/stress>=20且分类各含两类。任一门槛不达则该任务双表示双seed整组跳过，不能重抽。

modelseed44/45，每表示固定50epoch，不物理early terminate。stopA和B各自按AUROC↑、min_delta1e-7、同值取最早选择checkpoint；finalstress只在二者锁定后评估。原raw43四seed仅历史参照，不能算新四路的同split控制。CheM新四路轨迹是Morgan新四路的匹配control。

fixture：在固定保存轨迹上只交换selector输入，不改变weights/batches；一个trajectory两个checkpoint选择最多两次原生stress输出，算1fit。输出完整成员manifest先固定、两个选择器的epoch及聚合曲线；不发逐行标签。该新四路不是48的70/10/20，设计作用互补；历史train使用史仍保留。

### M4：Caco窗口，4fit，new_code

任务仅Caco，CheMF010，MLP256与TabM32各46/47；同batch/优化器/目标，固定200epoch。stop原MAE↓，三虚拟政策(50,8)/(200,8)/(200,200)，同min_delta/earliest规则。原50epoch已验结果作历史控制；只要prefix未证同构，不宣称后200轨迹“复现原控制”。

fixture：保存并回放stop标量序列，构造epoch20后无改善时50/8与200/8选相同checkpoint，200fullwindow仍只按stop选；计数必须4物理fit，不是12。输出steps/每epoch wall time/best/last/selector结果；外部评分候选预固定，不逐epoch看Valid。若都无改善，停止继续加epoch。

## G2. 中档接续：增加38fit，共60

### M5：三任务×三新头×两seed=18，new_code

Caco使用CheMF010；micro和CYP2D6 Veith使用MiniH0。三个新头分别plain3×512、TabM k1、TabM k8；既有MLP256和TabM32直接复用。

plain结构是三层Linear→ReLU→Dropout(.1)，最后Linear输出1；不能把“plain”当TabM.make已有枚举。TabM新k保持3blocks/512、arch_type=tabm、random-signs、无num embeddings/cats、d_out1，源码commit28e47ae301c92ec37787dde1ce923a0793f405b4；其余优化/50/8一致。Caco/micro MSE标准化Y，CYP BCE logits；stop按对应MAE↓/Spearman↑/AP↑。TabM分类输出是mean(sigmoid(member))，不换聚合定义。

fixture：D512/k32参数950304应与既有实际记录一致；k1≠plain参数数也不同；成员轴batch轴均mean。头参数与训练steps全部保存。若deep-plain或k1已经解释k32改善，停止扩大k，不从k32到64/128无限扫。

### M6：Sol/micro的近似参数配平，8fit，其中4 config_only

CheM2048 hidden128/F010、Mini512 hidden512/F010，各task46/47；CheM128字段已有真实生产支持，Mini512扩宽需新准备证明，不靠维度猜。配平参数262401 vs263169；原CheM256复用，Mini256F010复用M2。PPBR128已完成，不再提出。

fixture：参数计数按实际权重shape独立展开；scaler在每个asset单位独立fit，不能复制CheM统计给Mini；对应task缓存/行身份绑定。将结果解释为有限容量反证，不能称纯encoder信息因果。若M2变换等价而skip，MiniH0原控制可在统计等价证据下承担同身份F010控制，不补等价训练。

### M7：原posBCE归一化，4fit，new_code

CYP2D6 substrate F010、CYP2C9 substrate H0，各46/47。实际w沿原已采纳规则`min(5,max(1,sqrt(nneg_fit/npos_fit)))`；Z=(nneg+w*npos)/nfit；仅原BCE(mean)/Z，其余不变，不weighted sampler。先核对原配置/fit-count规则，若旧实际rule不符停止此因果对照，不能默默换控制。

fixture：w=1时Z=1与未加权一致；归一化不改变各样本相对权重，只有总体尺度；无正或负类违反原分类资格直接失败。输出fit类数/w/Z、loss曲线与AP↑，sigmoid连续分数不声称已校准。此模块的负对照是实际双负C9任务，不是只挑已有胜例。恒正loss缩放在eps=0的AdamW下严格抵消，decoupled decay不破坏该等价；eps=1e-8/AMP/舍入是剩余路径。它是低优先级负控制，不是预期收益方向；可证明注册轨迹等价时直接跳过等价fit，不填满预算。

### M8：CYP3A4 Veith低lr×窗口，8fit，new_code

H0/F010×lr5e-4/1e-4×44/45，固定200轨迹，与M4相同虚拟策略。loss BCE logits；stop/local AP↑；原50/8每格对照复用。低lr非触顶正例已有，不能仅据50cap做解释。

输出等优化步/等epoch与不同selector结果，区分学习率路径和候选窗口。若所有增益仅在更大选择预算出现，收口为策略bundle，而非“低lr改善泛化”。如长窗口无益停止；不为保持活跃自动添另一lr档。

## G3. 大档储备：14个受阻身份，不当现成生产资产

### M9：TabICLv2四个context fit，blocked_assets

具体code/checkpoint/hash见scientific_assets.json。PPBR、micro用回归文件；CYP2D6 Veith、DILI用分类文件。复用raw Mini512，禁止caller再标准化Y；固定8views、norm_methods none/power、outlier_threshold4、random_state44、kv_cache=False、allow_auto_download=False；绝不调用finetune。`.fit`仅官方train-fit context，stop/Valid/test不进context。PPBRprimary median为官方每view median的均值，micro mean；分类官方average_logits/temp.9输出正类概率。

fixture：权重和buffers哈希不变；X/Y scaler只fit；改变query batch/chunk/order不改变fit统计或原有context；classifier/regressor文件不混用；输出尺度一次inverse。没有early stopping训练，stop metric仅诊断，不用它挑多个checkpoint。每条proposal的`official_api_binding.constructor_kwargs`是可传给官方类的参数；type、hash、finetune、feature_dim与prediction_output是包装元数据，不能直接传constructor。回归用`predict(...,output_type="median"或"mean",alphas=None)`，分类用`predict_proba`及classes_中正类索引。固定inference batch_size8、use_fa3=False、offload_mode=cpu；若内存不够，先报资源阻点，不自行改科学参数或使用磁盘卸载。许可/权重payload/runtime/全行覆盖缺一则blocked；不从paper成绩预估本项目提升。预算4contextfit、0梯度更新、0新分子编码。

### M10：Monroe / MoLFormer10pct × BBB/hERG ×46/47，8梯度fit

Monroe固定weightOID与720维config，但immutable code commit仍null，先补此依赖；MIT/NOTICE与checkpoint用途、strict loading key白名单、构象/输入fallback覆盖需主控批准。不得运行默认Polaris样例或顺手下载TabPFNv3，不采用FT encoder。MoLFormer固定revision361063d0ad524ef77cf39b08469f6be770dc550f和safetensors SHA，768维；deterministic_eval=True、精确tokenizer/remote code/pooling；长分子或stereo转换覆盖报告不得省略。

BBB使用已验CheMF001 s46/47控制，不用旧H0s46；hERG用已验CheMH0。新encoder沿同floor/MLP256/AdamW/batch50/8；由于维度不同是表示配方bundle，不称纯encoder因果。若host/runtime变化，登记混杂，不自动重跑大批旧控制。

fixture：完整保留每task原行；无未登记裁剪/丢行；encoder params+buffers在完整获准forward范围不变；repeated/serialized预测有限且同尺度；asset hash/license/inputmap全部绑定。每task/encoder缓存共享两个seed，总4task-cache对象（train/Valid各分区），本计划不新增test拟合/编码权限。任何一底座门槛失败只停该分支，M1–M8继续。

### M11：MiniMol hepatocyte，2fit，blocked task cache

Mini512H0MLP256，46/47，MSE标准化Y/stop Spearman↑/原Y输出；对照CheMF010同split46/47。Mini编码器已在别的任务验收，但此task cache未记录；明确一次新task原行缓存准备（train/Valid）共享两seed。Microsome收益不是hepatocyte事实，不同时扫头和floor。负/混合就收口当前迁移，不添seed凑正。

## G4. 群验证与零fit工单

问题对应I-P002-09/10、方向D16。先保留cohort_register.json的完整成员入口和已有group20结果，不重画“最难10个”小组。主控私有评分只释放获准安全的固定群聚合，不发送逐行Y或残差；组小或可差分恢复答案则抑制，不能靠更多交叠查询绕开。

输出应有群ID/定义时间/成员版本、模型源run/seed、实际support和指标定义、同群前后差异、未改善群与抑制原因。共识底十分位与高分歧同时考虑；低分歧不是安全区。若只做无标签结构/相似度/feature统计，标题只能写“风险候选”，不能写“错误已定位”。对公开映射null的成员blob，本轮已记录阻点；未来需要时从主控映射获取允许的无标签对象，不尝试他人本机路径。

## G5. 成本、记录、fallback与下次研究

小/中/大名义新fit为22/60/74；大档=70gradient+4context。已派48和所有已有controls费用均0新增。新统计转换等价、类别资格不达或资产失败会减少实际数，不能用备用任务补满。共享编码小中0，大档5个task/encoder缓存对象；TabICL特征已缓存。预算明细和全部任务集合见budget_scenarios.json，未授权执行。

记录准备者活跃与墙钟、asset/cache准备、每fit steps/epoch/程序寿命、取回/评分/主控消费、Pro研究/等待；重叠不相加。当前未知接口的第一次实际准备/使用可以校准成本，但不要为每个已知小头再建重复试跑。旧255秒GPU、1733秒角色、6815秒准备到取回等不是当前新接口预言。

通常在一个完整可比较模块收齐后评审；冻结/标签/行身份、决定性反证、资产准入失败可提前返回主控。条件接续见conditional_followups.json，所有额外储备都必须另登记，不交执行者自动选任务。范围收口按task22_actions.json和analysis Q6，不按空队列、固定时间或模型名称投票。没有资源/许可的分支明确暂停，不要求其他独立问题等待。

## 逐proposal索引

下列索引仅供导航；完整精确参数、原目标尺度、控制ID、依赖和来源均在next_experiments.json，控制ID解析见controls.json。

|proposal|task|asset/配置要点|split|modelseeds|新fit|准备度|
|---|---|---|---|---|---:|---|
|P-M1-half_life_obach-01|half_life_obach|chemeleon / F001 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[44, 45, 46, 47]|4|new_code|
|P-M1-half_life_obach-02|half_life_obach|chemeleon / F001 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[44, 45, 46, 47]|4|new_code|
|P-M2-ppbr_az-01|ppbr_az|minimol / F010 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M2-solubility_aqsoldb-01|solubility_aqsoldb|minimol / F010 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M2-clearance_microsome_az-01|clearance_microsome_az|minimol / F010 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M3-ames-01|ames|chemeleon / H0 / mlp h=256|pro002_canonical_fourway_s43_fit70_stopA10_stopB10_stress10_v1|[44, 45]|2|new_code|
|P-M3-ames-02|ames|morgan_ecfp4 / identity / mlp h=256|pro002_canonical_fourway_s43_fit70_stopA10_stopB10_stress10_v1|[44, 45]|2|new_code|
|P-M4-caco2_wang-01|caco2_wang|chemeleon / F010 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M4-caco2_wang-02|caco2_wang|chemeleon / F010 / tabm k=32|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M5-caco2_wang-01|caco2_wang|chemeleon / F010 / plain_mlp3|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M5-caco2_wang-02|caco2_wang|chemeleon / F010 / tabm k=1|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M5-caco2_wang-03|caco2_wang|chemeleon / F010 / tabm k=8|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M5-clearance_microsome_az-01|clearance_microsome_az|minimol / H0 / plain_mlp3|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M5-clearance_microsome_az-02|clearance_microsome_az|minimol / H0 / tabm k=1|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M5-clearance_microsome_az-03|clearance_microsome_az|minimol / H0 / tabm k=8|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M5-cyp2d6_veith-01|cyp2d6_veith|minimol / H0 / plain_mlp3|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M5-cyp2d6_veith-02|cyp2d6_veith|minimol / H0 / tabm k=1|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M5-cyp2d6_veith-03|cyp2d6_veith|minimol / H0 / tabm k=8|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M6-solubility_aqsoldb-01|solubility_aqsoldb|chemeleon / F010 / mlp h=128|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|config_only|
|P-M6-solubility_aqsoldb-02|solubility_aqsoldb|minimol / F010 / mlp h=512|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M6-clearance_microsome_az-01|clearance_microsome_az|chemeleon / F010 / mlp h=128|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|config_only|
|P-M6-clearance_microsome_az-02|clearance_microsome_az|minimol / F010 / mlp h=512|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M7-cyp2d6_substrate_carbonmangels-01|cyp2d6_substrate_carbonmangels|chemeleon / F010 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M7-cyp2c9_substrate_carbonmangels-01|cyp2c9_substrate_carbonmangels|chemeleon / H0 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|new_code|
|P-M8-cyp3a4_veith-01|cyp3a4_veith|chemeleon / H0 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[44, 45]|2|new_code|
|P-M8-cyp3a4_veith-02|cyp3a4_veith|chemeleon / H0 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[44, 45]|2|new_code|
|P-M8-cyp3a4_veith-03|cyp3a4_veith|chemeleon / F010 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[44, 45]|2|new_code|
|P-M8-cyp3a4_veith-04|cyp3a4_veith|chemeleon / F010 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[44, 45]|2|new_code|
|P-M9-ppbr_az-01|ppbr_az|minimol / ICL internal / TabICLRegressor|raw_smiles_group_shuffle_s43_stop0.10_original|[44]|1|blocked_assets|
|P-M9-clearance_microsome_az-01|clearance_microsome_az|minimol / ICL internal / TabICLRegressor|raw_smiles_group_shuffle_s43_stop0.10_original|[44]|1|blocked_assets|
|P-M9-cyp2d6_veith-01|cyp2d6_veith|minimol / ICL internal / TabICLClassifier|raw_smiles_group_shuffle_s43_stop0.10_original|[44]|1|blocked_assets|
|P-M9-dili-01|dili|minimol / ICL internal / TabICLClassifier|raw_smiles_group_shuffle_s43_stop0.10_original|[44]|1|blocked_assets|
|P-M10-bbb_martins-01|bbb_martins|monroe / F001 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|blocked_assets|
|P-M10-bbb_martins-02|bbb_martins|molformer_10pct / F001 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|blocked_assets|
|P-M10-herg-01|herg|monroe / H0 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|blocked_assets|
|P-M10-herg-02|herg|molformer_10pct / H0 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|blocked_assets|
|P-M11-clearance_hepatocyte_az-01|clearance_hepatocyte_az|minimol / H0 / mlp h=256|raw_smiles_group_shuffle_s43_stop0.10_original|[46, 47]|2|blocked_assets|
