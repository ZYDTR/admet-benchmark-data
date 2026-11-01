# 规则、指标、评价使用与完整时间

本次使用任务冻结的取回Skill1.1.0、证据Skill2.0.0。赛事公开原文、用户确认的外部预训练冻结条件、本地train-only/盲验证控制、历史实现限制分别保留。当前由Agent自主选择执行方法，退役索引/渲染/准入/交接/运行程序只作历史证据。

- [本批科学范围和原预算](../prior-history/prior-history/evidence/H-1c7a62b215d94513b377.json) · [主控最新六项已完成状态](../evidence/objects/e5f20759604431d0282a575974c08b766ae57048c87d6302af3d41367517e894.json)。
- [累计评价使用账](../evidence/objects/f37f1b0cec261606f46260aa1f2727e475d53a800a4bba77113a5d6c73a8ab59.json)。
- [22任务本地指标/方向及Q0–Q7](../evidence/objects/45acd7d65dcc88bee472b4b27bd1fdeb9e74f0a5285f42c00ed0b82358595778.json)。
- [执行方完整分段时间原件](../evidence/objects/cc0876217adf47ef7ac1c6e03c30162e1ff0d33cbf8330a9a1bfe37f3547f521.json) · [主控原生终态时长及最终收件](../evidence/objects/50bced4286b1e7aec1f93e3df921b5a684063f810482f02d320d8796dc702d58.json)。

**本轮evaluation_scope=aggregate_only。** 可用已登记任务级汇总、固定聚合诊断、train资料和盲预测；不新增valid真值、逐行残差、极小分组差分或未准入标签访问。旧公开链接可达不代表本轮获准读取。valid反复比较已进入累计使用账，不能视为独立最终泛化；新Chat不清零。官方总分、AUPRC与本地AP等价性等未确认项保留。

已完成11个逻辑run：Mini一组22任务、10个海南Caco2单任务，合计32次正式任务评分；不是32组run，也不是32种独立任务。当前六项固定评分6次，两个阶段各读一次真值；主控独立Decimal50复算另计，不增加正式新任务评分。终身访问次数仍有未知，null不等于0。

本批保守GPU作业程序总520.7900679865852秒，包含导入/CPU/失败，纯kernel活跃时间未知。两个训练原生turn总4895.984秒，不能用某命令耗时或GPU程序秒替代完整角色时间；两类时间包含关系不能直接相加。余4775.28483790114秒不授权新实验。取回评分两阶段全角色、历史整理及发布/Pro尚未测部分都有各自原件，见[证据页](../current/evidence.md)。
