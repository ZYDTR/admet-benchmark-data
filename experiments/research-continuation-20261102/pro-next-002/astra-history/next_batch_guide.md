# 后续实验执行指南

这是科学设计，不是所有112项的执行授权。实际采用A见 evidence-ref:ref-97824a84d18abc8b，实际任务绝对路径由delivery.json给出。其余方案待登记具体批次。现任唯一实验调度者是Astra，用户身份授权见同研究目录DISPATCH_AUTHORITY_AMENDMENT.json。

## 不变的共同配置

每项精确字段见next_experiments.json的exact_runner_config（现有可运行）或science_config（尚需接口）。CheMeleon2048冻结原特征，权重SHA c376624d3407204e780a0ed13a9ac097cc9bb1c13ef89cdbc633c1715c183651；复用相同控制run的真实缓存，不能换生产实现重新编码后仍叫同表示。MLP默认2048→256/ReLU/dropout0.1→1，AdamW lr0.0005/wd0.0001、betas(0.9,0.999)、eps1e-8、batch128，max50、patience8、min_delta1e-7、相同值保留更早best；模型seed46/47，除D外raw字符串分组shuffle split43，stop目标10%。数据行/顺序/标签不改，训练统计仅fit。

分类未加权BCEWithLogitsLoss(mean)，预测sigmoid概率；回归MSE(mean)作用于fit-only标准化Y，预测只inverse一次回给定原Y。选epoch按合同：MAE最小、AUROC/AP/Spearman最大；AP沿现有tie-aware实现，保持AUPRC命名与实际算法差异。早停和Valid固定评分相互独立，不用Valid选epoch。fit-onlyScaler的原dtype、epsilon/常数替换规则照原配置。

## A：F001，24项，已采用并派发

任务：Ames、BBB、clearance_microsome、CYP2C9 substrate、CYP3A4 substrate、CYP3A4 Veith、DILI、half-life、hERG、HIA、Pgp、VDss；各seed46/47。唯一变化F010分母floor0.01→0.001，H0/F010不重训。BBB H0-s46仅研究参考，缺after不能入正式对照。现有cache.py已接受0.001，两个原source_group及各自缓存接口精确绑定实际TASK。新fit24、0新编码、900累计GPU作业秒、有界恢复，不依赖OpenCode。

## B：头容量与简单对照，24项

DILI、half-life、CYP2C9 substrate、VDss用H0特征，bioavailability、PPBR用F010。各seed46/47，分别128宽度MLP和单层affine2048→1带bias。前者仅改hidden_dim；后者删除隐藏非线性/dropout，是一个完整架构比较。分别262401/2049参数，原256头524801。仍同AdamW/MSE或BCE及task-stop预算；不能因为线性头未收敛便推论所有线性方法无效。已有256对照复用。

## C：匹配目标，16项上限

Caco2、LD50、lipo、PPBR、Sol各F010×两seed，训练目标改为标准化Y空间Huber(delta1)，|e|<1时0.5e²，否则|e|−0.5，mean reduction。它与原MSE在小误差区还存在梯度比例差，结论是“此loss策略效果”，不是仅因鲁棒性；必要时后续0.5MSE尺度控制，先不加新fit。保持原Y反变换与MAE早停。[Huber文档](https://docs.pytorch.org/docs/2.15/generated/torch.nn.HuberLoss.html)支持函数定义。

CYP2C9 substrate使用H0；CYP2D6 substrate/Veith使用F010；各两seed。BCE pos_weight=min(5,max(1,sqrt(nneg_fit/npos_fit)))，只由fit原行计数，记录实际值，若等于1跳过重复。不得按Valid阳性数选择权重。不调阈值、不改变AP监控。加权改变优化目标与可能的概率校准，不能保证AP/AUROC提高；[BCE定义](https://docs.pytorch.org/docs/2.15/generated/torch.nn.BCEWithLogitsLoss.html)仅支持权重意义。

## D：训练内分组压力，16项上限

DILI、CYP2C9 substrate、half-life、Sol × 两种group × H0/F010 × modelseed47。RDKit2024.09.6；canonical为sanitize后canonical isomeric SMILES、不去盐/互变异构；scaffold为非空Murcko/includeChirality=False，空scaffold回退ACYCLIC::canonical，解析失败RAW::原字符串。原行都保留，不按标签合并。

按SHA256(UTF8("astra001|43|"+groupkey))排序，hash并列按key；先整组累积至round(0.2N)为stress，再整组至round(0.1N)为stop，其余fit。记录实际比例/组数及独立行身份。fit须≥50%N、stop/stress各≥20行，分类三份都有两类、回归各非恒定；不满足就整对跳过、报原计数，不重抽至得到好分数。新fit统计只在新fit，stop选epoch、stress仅一次最终任务指标。此批不请求官方Valid评分，可保留盲预测。

历史上这些train行已被学习，所以这是回顾性分组压力对照，不能称全新未见终评；D内部成对新H0/F010才是有效控制。canonical/scaffold的分数不能不加条件互相排名，因为难度/样本不同。

## E/F：八任务表示对照，各16项

固定panel：Ames、bioavailability、Caco2、CYP2C9 substrate、DILI、half-life、PPBR、Sol，各seed46/47。控制锚点逐项在矩阵，不由新结果挑。

E使用RDKit2024.09.6 Morgan radius2、2048binary bits、chirality=True、bondTypes=True、countSimulation=False、ringMembership=True；无特征标准化。解析失败全零2048+记录mask，不丢行。MLP256不改。每任务三官方分区的特征共享两seed，共24特征对象，非预训练编码。

F固定MiniMol代码41642328affbb35e4950b7b7a9020aa95919b503、minimol_v1/gnn:15/global_max_pool512。fit-only传统标准化，常数/近常数分母替换1；不把CheMeleon0.01绝对单位搬过来。512→256头，其余同预算。真实checkpoint SHA、许可、载入、精确特征含义、全行覆盖及冻结接口要准备后绑定；缺少任一就保持blocked_assets，不下载外部训练数据或用未来参考分补齐。24分区编码共享两seed，GPU前向次数与成本要实际记录。

## 比较、停止与接续

每个批次保留正反结果及全部尝试。同一科学身份只学习一次，失败恢复纳入预算；收尾失败先收现有产物，不重训完成项。只有完整有限预测、正确行身份/尺度与冻结学习证据成立才交指定取回角色固定评分，缓存/旧评分已接受则引用，不重做全量核验。

逐任务两个seed方向一致才进入下一种划分/表示的确认；方向混合保留旧锚点，不按较好seed上报。优先判断收益是否超过本任务既有seed波动，但两seed的sd不是置信区间。D的结果为分组压力证据，不以此挑一个最好划分作为终评。进入下一分支时登记唯一任务和预算，Pro晚到意见不可变更正在运行A。

新接口准备才调用既有GLM5.3父会话及3直接子方，Terra只观察运行，不审质量。调度者完成必要科学接口判断；训练角色执行资源/冻结/数据身份核验，不能被迫重新审准备产物。优先稳定评分输入与科学轻量原件交付，模型大包归档独立完成。报告各角色实际时间和未知项。
