Historical research background, 2026-10-30. Current readiness is in current-research-context.md; current rules are ../rules/CURRENT_RULES.md. Recommendations here do not authorize execution or prove that candidate models are integrated. Prior small-batch suggestions are not a cap on the present request for broad directions/parameters.

# 来源索引与使用范围

查阅日期：2026-10-30。此处只收录进入最终决策的来源集群。原始论文、作者代码、模型卡和同团队后续材料不是独立性能复证；关键数值与具体版本相连。网页无法完整读取的状态明确保留。

## 赛事、数据与方法来源

| ID | 来源 | 支持什么／限制 |
| --- | --- | --- |
| R01 | [赛事159](http://www.aiinnovation.com.cn/web/#/trackDetail?id=159)；公开接口 `POST http://www.aiinnovation.com.cn/api/app/getTrack`，请求 `lang=zh,id=159` | 当前公开规则、截止、提交模板链接；接口更新时间2026-10-26。本轮读取成功，网页抓取失败不当作规则不存在 |
| R02 | 用户在本对话明确转述赛方确认 | 外部预训练权重可用但必须冻结；状态 `user_confirmed`，没有伪造公开FAQ链接 |
| D01 | [数据固定提交](https://github.com/ZYDTR/admet-benchmark-data/tree/0275588ac7a5d3df032ec7dc0794cab21dfcfeeb) | 用户指定数据，67CSV逐文件哈希/Git blob核验；没有README/语义说明；未另行证明官网链接到此仓库 |
| D02 | `evidence/dataset-audit.json` 与 `scripts/audit_dataset.py` | 字节、表结构、原始串身份、Y数值、模板比较；此脚本不作化学身份判断 |
| D03 | `evidence/chemistry-audit.json` 与 `scripts/audit_chemistry.py` | RDKit2025.09.6默认解析、canonical、Murcko诊断；不清洗或恢复官方split算法 |
| D04 | `evidence/scaffold-distribution-review.json` 与同名脚本 | 独立写的聚合复算，版本/身份定义与D03相同；不是第二种独立化学方法 |
| D05 | `evidence/mtl-exposure-review.json` 与同名脚本 | 仅train输入与valid标签，按原串检查跨任务暴露和分类子群规模；不等于泄漏判决 |
| G01 | [Best Practice Skill Writing，固定提交](https://github.com/grapeot/context-infrastructure/blob/c747317c90af9d1071a1157fa95e3766edcb6441/rules/skills/bestpractice_skill_writing.md) | 目标、验收、资源、输出；稳定判断与按需材料；不照搬作者个人规范 |
| G02 | [Deep Research Survey，同提交](https://github.com/grapeot/context-infrastructure/blob/c747317c90af9d1071a1157fa95e3766edcb6441/rules/skills/workflow_deep_research_survey.md) | 主张、前作定位、重叠研究、原始核验、独立审阅；按科学问题选择证据权威性 |

## 分子模型与资产

### M01：MiniMol 原始研究

[arXiv 2404.14986v1](https://arxiv.org/html/2404.14986v1)，2024-04-23，方法、§4.2与附录。冻结表示与下游头的直接方法证据；head搜索、集成和重复使其不是默认单模型预算。作者报告，未本地复现。

### M02：MiniMol 固定实现

[README](https://github.com/graphcore-research/minimol/blob/41642328affbb35e4950b7b7a9020aa95919b503/README.md)、[model.py](https://github.com/graphcore-research/minimol/blob/41642328affbb35e4950b7b7a9020aa95919b503/minimol/model.py)、[配置](https://github.com/graphcore-research/minimol/blob/41642328affbb35e4950b7b7a9020aa95919b503/minimol/ckpts/minimol_v1/config.yaml)、[评测runner](https://github.com/graphcore-research/minimol/blob/41642328affbb35e4950b7b7a9020aa95919b503/tdc_leaderboard_submission.py)。支持入口、加载、自动外部数据与test.Y访问的静态判断；没有运行证据。

### M03：CheMeleon 论文版本

[arXiv 2506.15792v2](https://arxiv.org/html/2506.15792v2)，2026-02-09；[期刊版 DOI](https://doi.org/10.1021/acs.jcim.6c01546)、[PubMed元数据](https://pubmed.ncbi.nlm.nih.gov/42734497/)，2026-08-07 online。当前期刊版存在，但全文访问403；本轮方法核查依赖明确标出的 arXiv版本，不声称最终版逐字一致。

### M04：CheMeleon 代码与具体权重

[固定fingerprint代码](https://github.com/JacksonBurns/chemeleon/blob/b5e5bd88a7070c3f278e7e65e85b792617bf125c/chemeleon_fingerprint.py)、[具体Zenodo记录](https://zenodo.org/records/15460715)、[发布方API](https://zenodo.org/api/records/15460715)。固定表示实现、自动下载路径、权重文件元数据和MIT字段；发布方MD5不是本轮下载校验。[本次API响应](evidence/chemeleon-zenodo-metadata.json)保留在交付内。

### M05：CheMeleon 冻结消融

[Research Square补充材料](https://assets-eu.researchsquare.com/files/rs-8834086/v1/c5362286af93146edbbdf1ed.pdf)，S5 / Fig S6，PDF页9–11。主线程核对永久冻结、延迟解冻与整体微调的区别及结果范围；这是该附件版本，未证实与期刊最终附件字节一致。

### M06：Chemprop 特征定义

[v2.2.1 原子特征](https://github.com/chemprop/chemprop/blob/v2.2.1/chemprop/featurizers/atom.py)、[默认特征选择](https://github.com/chemprop/chemprop/blob/v2.2.1/chemprop/featurizers/molgraph/mixins.py)。用于判断原子类别/unknown机制，不支持性能结论。

### M07：MoLFormer

[原论文v3](https://arxiv.org/html/2106.09553v3)，2022-12-14，Frozen/Finetuned与主要结果协议；[公开both-10pct模型卡](https://huggingface.co/ibm-research/MoLFormer-XL-both-10pct)及[资产API](https://huggingface.co/api/models/ibm-research/MoLFormer-XL-both-10pct?blobs=true)。区分full-XL与公开资产、预训练输入处理、许可与局限。

### M08：Uni-Mol

[官方使用文档](https://unimol.readthedocs.io/en/latest/quickstart.html)、[前处理源码](https://unimol.readthedocs.io/en/latest/_modules/unimol_tools/data/conformer.html)、[Uni-Mol2资产](https://huggingface.co/dptech/Uni-Mol2)。用于表示入口、构象回退、裁剪与资产识别；`latest`文档会变化，实际集成必须固定软件提交。

### M09：KPGT

[原论文](https://www.nature.com/articles/s41467-023-43214-1)、[固定README](https://github.com/lihan97/KPGT/blob/47dc1646c70b2138a157de481d24a1ac35d174cd/README.md)、[特征入口](https://github.com/lihan97/KPGT/blob/47dc1646c70b2138a157de481d24a1ac35d174cd/scripts/extract_features.py)、[预处理](https://github.com/lihan97/KPGT/blob/47dc1646c70b2138a157de481d24a1ac35d174cd/scripts/preprocess_downstream_dataset.py)、[权重记录](https://figshare.com/s/d488f30c23946cf6898f)。冻结实验确实存在；辅助特征、预拟合参数和依赖增加接入问题。Figshare网页检索可读，直接抓页403；未下载权重。

### M10：SMI-TED

[作者模型卡](https://huggingface.co/ibm-research/materials.smi-ted)、[资产API](https://huggingface.co/api/models/ibm-research/materials.smi-ted?blobs=true)。模型变体、特征接口、预训练输入与Apache-2.0标记；性能需另外看具体实验。

### M11：冻结分子表示 + TFM

[2604.16123v2](https://arxiv.org/html/2604.16123v2)，2026-04-20，Methods4.1–4.5、S1；[代码存档](https://zenodo.org/records/19605631)、[原仓库](https://git.rwth-aachen.de/avt-svt/public/tabpfn-molprop)。作者与CheMeleon不同；用TabPFN2.6，固定两个模型，统计win定义和基线复用已核。原仓库有访问墙；存档含datasets，未下载整包；具体2.6权重尚未固定。

### M12：TabPFN 版本与许可

[官方库](https://github.com/PriorLabs/TabPFN)、[v2-clf](https://huggingface.co/Prior-Labs/TabPFN-v2-clf)、[v2-reg](https://huggingface.co/Prior-Labs/TabPFN-v2-reg)。2026-10-30当前默认3.5；v2、2.6、3.5不能共用一条许可/性能声明。研究仅核对元数据与文档。

### M13：MolE 发布链

[原论文](https://www.nature.com/articles/s41467-024-53751-y)、[固定README](https://github.com/recursionpharma/mole_public/blob/dd56d319103e973fde0dcaa3537cb36a7b7a9843/README.md)、[LICENSE](https://github.com/recursionpharma/mole_public/blob/dd56d319103e973fde0dcaa3537cb36a7b7a9843/LICENSE)。下载章节TODO支持暂缓接入，不证明模型效果或所有用途的许可裁决。

## 反证、基准与评价

| ID | 一手来源 | 实际用于什么／不能外推什么 |
| --- | --- | --- |
| B01 | [2026 TDC end-user审计](https://pmc.ncbi.nlm.nih.gov/articles/PMC13417885/)，[DOI](https://doi.org/10.1021/acs.jcim.6c00819) | 分离结构暴露、相关标签、目标标签与环境问题；其作者有自己的方法，不自动是无立场裁决 |
| B02 | [2025 ADMET特征原始比较](https://link.springer.com/article/10.1186/s13321-025-01041-0) | 支持认真保留简单特征；数据清洗和MPNN预算限制阻止普遍排名结论 |
| B03 | [2026 ADMET可靠性基准](https://link.springer.com/article/10.1186/s13321-026-01217-2) | TabPFNv2和不同场景的候选线索；重清洗/重切分、部分骨干更新、指标不同，不是本赛冻结对照 |
| B04 | [2026多模态分子研究](https://www.nature.com/articles/s41467-026-74487-x) | 涵盖22TDC ADMET和多种融合；IBM机构关联；ADMET与DTI协议分开，全部冻结配置未恢复，不移植其知识图谱输入 |
| B05 | [Deng2023原始系统评估](https://doi.org/10.1038/s41467-023-41948-6)；[开放全文XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10575948/fullTextXML) | 冻结MolBERT/GROVER与简单方法的历史证据；预测头容量不同，不能当所有新模型的定论 |
| E01 | [TDC ADMET overview](https://tdcommons.ai/benchmark/admet_group/overview/)、[ADME背景](https://tdcommons.ai/single_pred_tasks/adme/) | 任务背景、历史规模和评价；与本包映射未经完整证明，不补写未知单位/split |
| E02 | [TDC evaluator源码](https://tdc.readthedocs.io/en/main/_modules/tdc/evaluator.html)、[sklearn AP定义](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html) | TDC pr-auc映射AP；AP不是梯形积分。未证明赛方算法相同 |
| E03 | [Cawley & Talbot2010](https://www.jmlr.org/papers/v11/cawley10a.html) | 有限验证集上的选择过拟合；本赛未测出具体偏差量，不能伪造置信区间 |
| E04 | [2025多任务负迁移研究](https://www.nature.com/articles/s42004-025-01592-1) | 逐任务保存/负迁移的重要性；训练共享GNN的结果不直接代表冻结表示后的共享head |

没有用二手榜单、博客或模型名气决定最终优先级。也没有找到完全满足“本包同划分、全编码器冻结、同预算head、全部候选”的独立实测；这正是停止文献排名、进入受约束本地比较的理由。
