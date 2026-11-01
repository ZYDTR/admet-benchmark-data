# 规则、评价与数据边界

本次使用取回Skill1.1.0、证据Skill2.0.0。来源区分赛事原文、用户确认的冻结条件、本地训练/评分控制和某次实现限制。科学定义及权限由主控确定，执行方法由Agent在范围内判断；旧固定索引、渲染、准入和交接脚本仅作历史证据。

- [既有完整规则和10项资产来源](../prior-history/context/README.md)。
- [本批实际任务：六配置、授权及计算预算](../prior-history/evidence/H-1c7a62b215d94513b377.json)。
- [本次收集时的主控状态](../evidence/objects/f590a044fc795c509551d1c5b7f1424f89d3e88bd9b17aede32a5ba5716f16d6.json)。
- [更新后的累计评价使用账](../evidence/objects/ead3a3385ffb6375f73f26f26f1231a7a714f5894467da001b3dab912ecddaa6.json)。
- [主控独立Decimal50复算与使用记录](../evidence/objects/5a5175aebce601435593f2b9d311cf5aed644bc3c2240cb1ef53ca030a218ef6.json)。

外部预训练CheMeleon参数/buffer保持冻结，只有新头学习。仅train.Y用于训练，内部573/64分组划分做早停，预处理只fit内部训练部分；valid/test为盲输入。发布候选中的新CSV仅为官方train数据/其训练集预测、盲valid/test和模型预测，未新增逐行valid真值或残差。固定MAE按给定Y数值尺度，越小越好；不推断官方总分。

现已完成7个逻辑run、28个头/任务正式评分（1个Mini22及6个海南单任务），不是28个run。旧六项0/6仍封闭。本次取回方真值文件读1次、固定评分2次；主控独立真值读1次、Decimal复算2次，新增正式任务评分0。终身次数仍未知，null不补0；新Chat也不会清除valid复用的选模偏差。
