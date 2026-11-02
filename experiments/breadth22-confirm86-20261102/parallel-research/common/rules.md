# 规则、数据及指标边界

先读[已验固定原文与来源映射](rule-originals.json)。用户向赛方确认：外部预训练权重允许且必须冻结，参数和buffer应保持不变；新头可训练。公开赛事原文、用户确认、本地控制和某次实现限制分开，旧SAP/固定Docker/随机初始化等不能冒充赛事规则。

本地选模阶段只用官方train.Y学习，内部train-fit拟合变换，train-stop作早停；原行/Drug/Drug_ID及重复或空ID均保留，不改标签或删行。valid保留本机指定角色固定评分和获准汇总分析。当前研究aggregate-only：不新增私有逐行valid真值、残差、教师伪标签或测试拟合；公开历史中的标签不自动进入本次准入。最终train+valid合训或官网提交需后续独立决定。

MAE越小越好，AUROC/AP/Spearman越大越好；AP为并列阈值组平均精度，官方AUPRC等价性仍未确认。官方模板和比赛原始尺度沿原合同，不把阈值F1优化当AUROC/AP路线。本轮研究和准入汇总/无标签输出上的无更新诊断计算，不拟合、不新编码/模型推理、不安装、不发训练/蒸馏/部署或改标签指令。DINO补件属于被研究对象，不能反向授予执行权限。

历史固定对象沿已有发布验收引用，不要求重查全库；新增科学主张需有原件/反证/限制。

本批现行本地规则：[当前policy来源视图](../evidence/eaa891c243aa95bc77d5e7958d59ba9adcfd1ad7d3aa075d7ea2131dcb2971ea.json)。既有原文的旧状态不覆盖本批已准入配置与当前研究范围。


当前方法按[共同实验研究纲领](../methodology/EXPERIMENT_DESIGN.md)；Pro与Astra同版独立研究，沿本轮decision-contract，旧Prompt17仅为历史。
