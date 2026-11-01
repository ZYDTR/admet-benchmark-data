# 现行规则与科学资产

本快照采用取回Skill1.1.0、证据Skill2.0.0。执行Agent自主选择现场方法；主控判断科学结果和接续。已退役流程只解释历史，archive目录中的旧接口、旧指令和程序不作为当前任务入口。

- [现行宿主入口](../evidence/H-9311b774191598549305.md.txt)
- [硬约束与标签边界](../evidence/H-3db7c2d1e67d40641a20.json)
- [赛事、用户确认、本地控制与试验限制来源](../evidence/H-e275f0ef9a4955741956.md.txt)
- [现行结果与协作约定](../evidence/H-61625294df99bdcaab62.md.txt)
- [取回Skill1.1.0](../evidence/H-81e0ba83f1440ade6a91.md.txt)
- [证据Skill2.0.0](../evidence/H-11db5a77c3d88cd7f86b.md.txt)
- [训练Skill3.0.0](../evidence/H-80262f77a72482c410c0.md.txt)
- [10项科学资产准备度原件](../history/archive-20261101/originals/S-d764c93e890f1a40.json)
- [角色与执行LLM原件](../history/archive-20261101/originals/S-178280ff32153587.json)
- [累积评价使用账](../history/archive-20261101/originals/S-56508b28d30b3f74.json)
- [现行研究Prompt正文](../evidence/H-e1f7dc517557467fa5d4.md.txt)

外部预训练参数和buffer保持冻结，新模块可训练；仅train.Y学习，预处理只fit相应内部训练部分。valid用于宿主评分/分析，准备与训练只接收允许的汇总诊断；最终train+valid另议。新Chat不清除累计valid选择偏差。

[既有Mini22精确评分与四Caco2原结果](../history/archive-20261101/history/evaluations/README.md)保留，正式26任务评分与未知终身标签访问次数分开。此阶段没有新读取真值或重算指标。
