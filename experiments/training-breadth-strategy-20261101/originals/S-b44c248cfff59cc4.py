from pathlib import Path
import hashlib,json,datetime
w=Path.cwd();r=w/'adhoc_jobs/admet_training';a=r/'audits/control-plane-20261101'
changes=[]
def save(p,new):
 old=p.read_bytes();new=new.encode() if isinstance(new,str) else new
 if old==new:return
 dest=a/'before'/p.relative_to(w);dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():dest.write_bytes(old)
 else:assert dest.read_bytes()==old, f'concurrent change: {p}'
 p.write_bytes(new);changes.append({'path':str(p.relative_to(w)),'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':hashlib.sha256(new).hexdigest()})
def replace(p,pairs):
 s=p.read_text()
 for old,new in pairs:
  assert old in s,(p,old);s=s.replace(old,new)
 save(p,s)
replace(r/'AGENTS.md',[
 ('## 固定规则','## 规则来源与适用范围\n\n用户本聊天的明确要求决定当前任务；公开赛事原文、用户向赛方确认的条件、主控选择的本地控制、某次试验限制和代码能力必须分开。`policy.json` 的 train-only/盲验证等是当前本地选择，`pilot_*` 只描述首试；都不能冒充赛事逐项禁令。单项试跑不是长期单任务上限；批量范围按用户已授权任务登记，已批准范围内不逐卡、逐次重新询问。\n\n当前周期从 [monitor-mae-e2e-20261101](cycles/monitor-mae-e2e-20261101/CONTINUE.md) 进入；状态读其 `status.json`。角色 Skill 定义职责，冻结的当次任务定义具体输入/预算，历史报告只证明过去事实。新规则不回写旧证据；发现冻结任务与用户新要求冲突时，主控明确版本化接续，不能让执行方自行猜优先级。\n\n## 固定规则'),
 ('不自动上传赛事或推送仓库。','训练/准备角色不自动上传赛事或推送仓库；用户已授权的分析材料由取回方按登记清单发布到 ZYDTR 仓库，官网提交只走用户手动触发的专用角色。'),
 ('该检查只核对计划与允许输入；不能代替代码、GPU、路径、运行及冻结状态审计。','该检查目前是 Caco2/CheMeleon、单GPU、已登记试跑的专用检查器，硬编码范围见 `src/plan_checks.py`；不支持新任务/并行不是用户禁止。新模型/批次应先扩展并核验任务合同，不能伪造旧run通过。该检查不能代替代码、GPU、路径、运行及冻结状态审计。')])
replace(r/'skills/INDEX.md',[
 ('v1.2.1；v1.2冷启动真实读取已验','v1.2.2；v1.2冷启动真实读取已验'),
 ('新增兼容反例的新版行为待测','新增兼容反例的新版行为待测；准备包版本改为从实际Skill读取并核对'),
 ('v0.4.1；主控Prompt模板/受检填值','v0.4.2；主控Prompt模板/受检填值'),
 ('当前闭环：[progressive-index-e2e-20261031](../cycles/progressive-index-e2e-20261031/CONTINUE.md)。','当前闭环：[monitor-mae-e2e-20261101](../cycles/monitor-mae-e2e-20261101/CONTINUE.md)。旧 progressive-index 周期为历史记录。'),
 ('新远端部署/训练待测，共享分支未测','v4执行方已报告科学学习完成、外层监控125，主控独立验收未完成；共享分支未实现验收')])
replace(r/'skills/ml-preparation-only/SKILL.md',[
 ('Workflow。v1.2.1，','Workflow。v1.2.2，'),
 ('不修改原始输入，不读其他会话产物。','不修改原始输入，不自行寻找其他会话产物；主控作为本次输入明确交付的已验收旧资产可以只读复用。'),
 ('并给出两者的实际路径和 Skill 摘要','并给出两者的实际路径和 Skill 摘要；版本号须从本次原文读取，不能在生成器里写死')])
replace(r/'skills/admet-frozen-training/SKILL.md',[
 ('更新：2026-11-01（部署恢复与资源接续补充）','更新：2026-11-01（控制面复核；旧冻结任务不变）'),
 ('内部 train 划分早停。','在官方 train 内划分拟合与内部验证部分，后者用于早停。'),
 ('新头须有有限非零梯度和实际参数变化。','新头须有有效优化步和实际参数变化；梯度应有限，整体存在非零梯度，不要求每个参数、每一步都非零。'),
 ('恢复须先证明旧作业已退出且学习未启动，保留旧失败，新版本独立证据及全run首次学习锁。没有这项证据就查询原作业，不因“只是重试”再启动学习。','对本次只准一次学习的试跑，重新启动须先证明旧作业已退出且学习未启动；保留失败、新版本证据及全run首次学习锁。这个限制不能自动推广成永久禁止断点恢复。将来是否可恢复已有学习，由明确的批次恢复预算决定；未知状态始终先对账。\n\n外层监督失败、科学worker完成、产物完整性和科学可用性分别判定。外层异常保留真实退出码；已经生成的完成凭据和产物仍由主控独立审查，不因一个监控字段读取失败就自动丢弃或重训。监测未知不能填零；应保存当次PID身份、原始状态与缺字段证据，有界复核，并按实际完成/边界证据决定后续。当前2026-11-01 v4出现worker返回0、监控125的实证；根因和完整验收尚未确认，不能写成竞态已证实。'),
 ('只有本次授权范围全部完成才标完成；既有观察自动化按用户要求停止，保留记录。更新项目工作记录和 Skill 索引，交给用户一个明确入口。','只有本次授权范围全部完成才标完成。训练执行方写本run结果并交主控；项目工作记录、Skill与索引由主控维护，执行方不修改。资源观察是用户要求的独立常驻职责，单次训练结束不停止它；其他任务专用监控按各自已登记停止条件收口。')])
replace(r/'skills/hainan-training-retrieval/SKILL.md',[
 ('Workflow。v0.4，2026-10-31。','Workflow。v0.4.1，2026-11-01。'),
 ('本机只写本次独占取回目录，保留原件、失败尝试和日志。','本机只写当次明确登记的取回目录、私有评分输出与发布工作副本；这些不同用途的路径须在任务清单中列清，不能把“只写取回目录”误用于阻断已授权评分/发布。保留原件、失败尝试和日志。')])
replace(r/'skills/admet-evidence-review/SKILL.md',[
 ('Workflow，v0.4.1，','Workflow，v0.4.2，'),
 ('一条历史结论推翻链、本批实际配置或数值计算','一条与本批有关的历史结论推翻链（若历史没有则明确不适用）、本批实际配置或数值计算'),
 ('各层使用同一封口commit，','各层使用本批登记的封口commit，'),
 ('该合同不授权新定时或扩大科学任务，','主控亲自审读也是有效接续，不必为了回执形式再派一个Thread；新的用户指令可以调整处理顺序，但须保留负责人和下一动作。该合同不授权新定时或扩大科学任务，')])
replace(r/'skills/admet-evidence-review/references/handoff-completion.md',[
 ('仅写received、review_pending或口头“下一步会做”不算接续。','主控亲自审读、修复或做科学判断属于实际接续，应保留正在处理的请求、当前turn、工作记录和下一动作，不必再派一个Thread。仅写received、review_pending或口头“下一步会做”不算接续。'),
 ('脚本不发送消息、不建定时、不调用模型，也不能强制Application拦住结束按钮。','脚本当前只识别派发/外部等待/用户问题/收口四种结果，尚不识别主控正在亲自审读；遇此情况不能为了过检查伪造派发或外部依赖，应依据实际工作记录标 processing 并保留该工具局限。脚本不发送消息、不建定时、不调用模型，也不能强制Application拦住结束按钮。')])
replace(w/'rules/skills/hainan-compute-access/SKILL.md',[
 ('ADMET 作业还须遵守其 [远端作业规范](../../../adhoc_jobs/admet_sap_setup_20261029/remote-execution/SKILL.md)。','ADMET 作业从其[项目唯一入口](../../../adhoc_jobs/admet_training/AGENTS.md)读取当次规范；旧 SAP 远端规范只按项目来源映射选择性参考，不能重新引入已排除的限制。')])
replace(w/'rules/skills/<PREPARATION_HOST_ALIAS>-orbstack-ops/SKILL.md',[
 ('v1.2修订的准备效果尚待真实新任务验证；无需为更新Skill自行追加或续写会话。','具体项目的Skill版本和实测范围在其项目索引维护；无需为更新运维Skill自行追加或续写会话。')])
# The historical narrative remains byte-for-byte at the same directory depth, so its relative links still resolve.
p=r/'design/chat_gateway_20261031/README.md';history=p.with_name('history-through-20261101.md')
assert not history.exists();history.write_bytes(p.read_bytes())
save(p,'''# ADMET 控制面与交接

从[项目唯一入口](../../AGENTS.md)进入。本文只说明当前职责和有效路由；[历次设计、试验与复盘](history-through-20261101.md)是有日期的历史证据，不能覆盖当前规则。当前执行状态读[本周期](../../cycles/monitor-mae-e2e-20261101/CONTINUE.md)，不从历史段落猜测。

## 规则与职责

公开赛事条款、用户确认的冻结条件、主控本地选择、单轮授权和实现能力分别记录在项目入口、policy及[来源映射](../../docs/source-map.md)。一次只训一个Caco2头是当前闭环试跑范围；资源足够且不影响他人时可并行、可共享，不是永久单卡或零显存规则。实际共享和批量运行能力尚需实现及验收，不能只凭Skill文字声称已具备。

| Thread/角色 | 做什么 | 何时接续 |
|---|---|---|
| 脑-兴智杯（主控） | 制定实验与Prompt，独立验收，维护问题和采纳记录；下发准备及训练 | 消费结果、实质故障或需要科学/权限变更；不转发每次资源变化 |
| mini OpenCode准备会话 | 在Context Infrastructure根项目做已分配准备，不训练 | 仅主控派发；输入输出隔离在项目子目录 |
| 👁️OpenCode的准备（Terra） | 观察主控登记的会话、检查终态与产物，回报主控 | 有登记任务才启用既有观察；空队列暂停 |
| 👁️海南算力观察（Sol/xhigh） | 每10分钟只读采样、更新资源记录 | 相关变化直接通知仍在等待的原训练Thread；实质故障回主控；直到用户停止 |
| ✋丢到海南训练（Sol/xhigh） | 读资源记录、启动前复核、执行已批准任务、记录产物及退出 | 原任务内资源等待自行接续；完成或实质故障回主控 |
| 海南训练产物取回与测速 | 取回、固定valid评分、打包与获准发布 | 消费已登记run和来源通知；不重新训练、不发Chat分析 |
| 🔄Chat收发与分析交接 | 按固定模板收发、检查目标Pro与材料、收回完整问题及指南 | 可按当批登记协议通知取回方；不能自行派OpenCode、训练或扩范围 |
| 每批新Pro Chat | 渐进阅读规则、历史、本批证据，深入研究与反证，返回详细实验方案 | 按比较批次评审；篇幅和方向数量不作质量缺陷 |
| 📤赛事提交与查分 · Sol | 用户手动触发后提交候选、查官网分数 | 独立于训练循环，不自动订阅训练结果 |

角色身份由当批任务与 `resources/hainan/registry.json`、OpenCode Terra登记及 `submissions/thread.json` 核对。主控登记任务就已包含相应授权，不是要求用户逐环节再批准。相同请求只由一个登记责任方接续，响应不明先对账。

主路径：主控 → OpenCode准备／Terra观察 → 主控验收 → 海南训练 → 主控科学与边界验收 → 取回评分与批准发布 → 网关／新Pro → 网关取回 → 主控审查并记录下一批。

网关可以在当批明确登记的范围内观察训练终态、通知取回方处理同一run；这是已指定工作的传递，不是自由派任务。当前周期选择主控先验收再派取回，不能把这一试跑的串行安排当成所有未来周期的唯一架构。稳定产物的只读取回可与主控审查并行；是否进入评分/发布/比较以当批准入和完整性证据为准。新的实验决策和OpenCode派发始终回主控。

## Chat 输入、输出与通道

主控拥有[研究模板](CHAT_PROMPT.md)和批次研究目标；网关仅按[字段合同](PROMPT_CONTRACT.md)填入登记事实和链接。当前模板要求充分研究、实际subagent/cross check、明确参数/对照/seed/成本和条件分支。六文件是运输合同，不限制研究长度或候选数量；未知科学量标未知，不为凑字段编造。

每批新Pro读取固定版本仓库根 → context → history → 本批/delta → 相关原件。全部相关资料可达，不要求无差别逐字遍历全部历史。valid真值对研究有价值，具体接收范围由已核验来源及当批evaluation_scope决定；训练当前只用train.Y。分析可见不等于新增公开权限；精确分数对准备/训练的隔离是本地选择，正在本次控制审查中向用户核对。

用户已允许Browser创建并选择Pro；已有真实会话ID时优先原生发消息。首发前无真实ID时可在Browser发一次已封口正式任务，核对接收与真实ID后原生续接。Browser可下载真实附件；不发占位，不重发未知请求，不绕过工具明确拒绝。完整文件、聊天终态和科学可信度分别验收；文件已齐就先取回，不强等长正文结束。

## 节奏、恢复与材料

正常按已登记比较组收齐触发一次深入评审；重大故障或决定性反证可提前处理。没有每个头、30/60分钟或连续两批的固定Chat/停训门槛。研究方案可广泛展开，实际执行只消费用户已批准的有限范围；扩大范围再明确预算。

观察日志不是资源预留。选卡按自身峰值、他人需求、余量及运行影响；不设零显存门槛，不停止他人任务。偶发连接异常有界恢复；状态未知查询原作业，不重复学习。学习已完成但监督异常时保留两种状态，主控检查原件后裁决，不能自动丢弃或重训。

原件、输入摘要、问题/反证/采纳和失败持续保留；按身份复用已验环境、底座与特征，新增配置不应每次重写整套运行器。公开包仅发登记科学材料，保留源映射；私有连接信息和非公开数据不随全目录上传。时间记录以本批在各Thread的完整跨度和关键路径为主，命令耗时用于解释，未知不伪装成模型思考时间。

实际规范只在[项目Skill索引](../../skills/INDEX.md)维护；`contracts.json`提供机器字段和实现局限。未实现的自动回调、共享、并行及全链能力如实标明。一次训练或若干分段通过，不等于一次触发全闭环已通过。
''')
save(r/'docs/prd.md','''# 项目目标与范围

通过一个项目入口，让准备、资源观察、训练、取回评分发布、Pro研究与主控验收协同提升ADMET预测质量。外部底座参数和buffer冻结；任务及数据边界、保护他人服务/文件不变。用户希望成批比较、完整历史与反证、少做重复准备和人工催办。

当前范围与状态由项目AGENTS路由到当次周期；不得把首轮Caco2单作业、不评分试验当长期范围。并行按资源及已批准批次决定，旧试验记录保留。一次触发全链是否完成需真实因果交接证据，不能把分段成功相加。
''')
save(r/'docs/rfc.md','''# 控制面设计

项目AGENTS是唯一入口；policy保存当前数据/冻结等本地条件，source-map区分来源。角色规范只维护在项目skills；单轮输入、预算和状态在cycle/run，原件与历史只读。用户新要求优先，旧试验与实现限制不能升级成赛事规则。

运行优先复用已验环境、资产及runner，配置差异由受检任务描述；固定检查负责身份、冻结、完整性和边界，Agent处理科学判断与未知异常。计划不是授权本身，hash通过不是实际行为已通过。

当前check_plan仍硬编码五个Caco2/CheMeleon单GPU试验及其输入规模，check_evidence仍是历史参考布局；这两项不是通用批量执行器。扩任务/模型时应实现受检的任务合同，不能删除安全检查或改旧证据凑通过。共享显卡的通用授权已存在，当前运行实现只有无其他活跃工作负载分支；待补共享的需求/影响与自有退出机制。

当前职责及消息路由见design/chat_gateway_20261031/README.md；重复历史不作为第二套规则。主控负责科学准入和独立验收，不逐次中转普通资源更新。学习结果、监督状态、材料状态分开，不因单一监测异常自动重复训练。
''')
save(r/'docs/test.md','''# 验证边界

检查身份、冻结、数据角色、真实设备、行覆盖、重载一致、写入边界和自有资源释放；验收依据是源码及原始证据，不能仅凭执行方PASS。每个run的实际通过/失败/未知见其acceptance。旧试验、旧Skill和失败原件保持不变。

计划检查与离线反例只证明对应实现的合同；不能证明海南训练、共享/并行、新Chat读取或全链已经通过。无系统调用级或同等写入证据时，不声称目录外副作用已排除；不为取证扫描他人项目。

首试hainan-skill-pilot失败；随后frozen-training与follow等有真实训练证据，严格Follow和未测分支分别保留。当前monitor-mae v4执行方报告worker完成而监督125，尚需主控独立验收，不能将文档修订当运行修复。本次控制面复核见audits/control-plane-20261101/REPORT.md；没有新训练或线上部署。
''')
replace(r/'docs/source-map.md',[
 ('| no training / check-adapter | 当前授权包含一次真实模型训练，不能机械继承过去不训练任务；离线 scaffold 测试仍不训练。 |','| no training / check-adapter | 准备不训练、执行方按当次授权训练；首试一次不构成长期次数上限。离线scaffold检查不训练。 |'),
 ('| 原外部评分/量化反馈网关 | 不声称已部署，本轮不评分。未来由主控固定评分器读取预测数据，不执行返回脚本。 |','| 原外部评分/量化反馈网关 | 旧Harness网关不继承。当前由指定取回方在本机用固定评分器评分；评分环境不执行返回脚本。 |'),
 ('| 上传/发布 | 本轮无赛事上传、无仓库推送。 |','| 上传/发布 | 训练循环不自动上传赛事；用户已授权取回方发布登记分析包到ZYDTR，专用提交Thread仅在用户手动触发时上传赛事。 |'),
 ('2026-10-31 职责补充：','以下是历史变更证据，不是并行生效的旧指令。\n\n2026-10-31 职责补充：')])
p=r/'submissions/CURRENT.json';d=json.loads(p.read_text());d['activation']='Only human-triggered dedicated thread identified by submissions/thread.json; updating this pointer does not authorize or trigger upload.';save(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(a/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'changed_files':len(changes),'historical_architecture':str(history)},ensure_ascii=False))
