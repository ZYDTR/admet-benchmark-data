# 本轮研究入口：标准化28项结果与全任务后续

请先读本目录 decision-contract.json，按Q1–Q3完整回答。研究目标是提升泛化质量，并让一次深入研究支撑多个后续实验批次。

按渐进索引阅读：

1. context-references.json 内赛事规则原文、来源映射、本地标签/冻结约束及返回合同；历史公开标签不在本次准入范围。
2. ../history/README.md 查看完整35记录及失败/未执行历史，../issues/validated-and-open.json 查看当前问题与反证；相关历史原件按问题下钻，历史全库入口见context-references。
3. ../current/README.md、scores.json、comparisons.json、evaluation-use.json，以及current-interface.json和../runs/index.json。28项已训练、已评分、已主控验收，不再重复计算。
4. ../assets/README.md与index.json区分分子底座/准备度和执行模型；../research/README.md可追踪上轮研究与原155文件，../preparation/README.md保留准备失败和修复。
5. timing-evidence.json用于规划端到端成本。大体积二进制与原始跟踪按问题查；完整来源映射在../evidence/source-index.json，索引不冒称本轮已亲读所有原件。

历史状态以对应截点解释。F010五任务双种子改善，但CYP方向不一；22任务推导Valid约45.38/45.48，其他16保持原Mini22，不是官网分数或集成结果。返回仍用六类完整文件与audit.zip；本轮预算proposal_only，不发起训练。一个新Pro内部按互补问题组织实际subagents，不固定数量，不重复全库核验。
