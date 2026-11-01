from pathlib import Path
import json,re,hashlib,datetime,collections
w=Path.cwd();r=w/'adhoc_jobs/admet_training';a=r/'audits/control-plane-20261101';before=a/'before';now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def loc(rel,needle):
 p=before/'adhoc_jobs/admet_training'/rel
 if not p.exists():p=before/rel
 lines=p.read_text().splitlines();found=[i+1 for i,s in enumerate(lines) if needle in s]
 assert found,(rel,needle)
 return {'file':str(p),'line':found[0],'quote':lines[found[0]-1]}
def F(i,title,status,impact,action,*refs):return {'id':f'F{i:02}','title':title,'status':status,'impact':impact,'action':action,'evidence':[loc(*x) for x in refs]}
items=[
 F(1,'历史试验、当前规范和实现限制混在同一入口','文档已修正','旧的单作业/不评分/原生限定被后续Thread当成长期规则。','当前架构重写为职责和路由，249行原稿在原目录按历史留存；PRD/RFC/test/source-map明确范围。',('design/chat_gateway_20261031/README.md','当前通道约定'),('docs/prd.md','本轮不做')),
 F(2,'当前入口指向旧周期，接续全文堆叠互斥状态','已修正当前路由和状态','新Thread可能认为仍等准备、未派训练，或继续v3只回主控。','项目索引指向11/1；cycle和观察CONTINUE只保留现行路由；终态转主控，观察的该run不再资源唤醒；旧全文保存。',('skills/INDEX.md','当前闭环'),('cycles/monitor-mae-e2e-20261101/CONTINUE.md','当前等待准备终态'),('resources/hainan/CONTINUE.md','仅回主控')),
 F(3,'机器合同也包含过时权限，不只是README','已修正','future_analysis_sessions写仅原生发送，chat_transport却允许Browser首发；历史已评分字段貌似所有当前run都已评分。','contracts rev15与当前混合通道一致，历史目标/状态显式定界；新目标从当批登记取，不从首轮ID回退。',('design/chat_gateway_20261031/contracts.json','gateway sends only via native'),('design/chat_gateway_20261031/contracts.json','completed_for_current_hainan_runs')),
 F(4,'共享授权与运行代码能力不一致','规则已澄清；实现缺口未关闭','当前v4允许非零已用显存，但仍要求无其他活跃进程，运行中见外部PID会退出自有作业；不能称共享已支持。','保留用户共享意愿和Michael/他人保护约束；下一实现需按需求、负载影响和自有退出条件支持共享，不是继续加0/4MiB门槛。本次未部署新分支。',('skills/admet-frozen-training/SKILL.md','选卡依据是任务预计需求'),('src/plan_checks.py',"'max_concurrent_jobs': 1")),
 F(5,'观察分类仍把任何非零显存归为occupied','实现差异已披露；未改运行采样器','occupied不是不可用，但旧名称和仅分类变化的事件容易漏掉可用余量变化。','当前通知合同已要求看原始数值和实际等待状态，不能拿分类当资格；应改为占用事实与任务适配判断分列，并验证余量变化通知。',('resources/hainan/implementation/normalize.py','elif processes or (memory_used'),('resources/hainan/implementation/normalize.py','if old["classification"]')),
 F(6,'计划检查器硬编码五个run、单任务、单GPU和单底座','范围已明示；通用实现未完成','扩一个任务/组合就要改代码，和未来批量试验目标不符；并非用户禁止并行。','明确它只是历史试跑检查器；后续用批准任务清单驱动数据/资产/并发范围。当前一次学习不因审查扩大。',('src/plan_checks.py','admitted_runs ='),('src/plan_checks.py',"'max_concurrent_jobs': 1"),('src/plan_checks.py','expected_rows =')),
 F(7,'监督异常阻断对已完成科学产物的处理','Skill已修正；运行代码未修复','本轮worker0/75步/273预测，但监控VmRSS异常使外层125且未验证完成凭据。失败现场stat/status未完整保存，不能认定根因已证实。','主控独立核对96件摘要与完成身份；保留125和学习锁，分开审查科学结果、监督故障、完整性。后续修复监测取证及终态对账，不用未知=0或自动重训。',('skills/admet-frozen-training/references/runtime-recovery.md','资源监控区分已确认终态与未知')),
 F(8,'把新头每项/每步非零当普遍成功要求','通用Skill已修正；历史检查器保持原范围','有限的零梯度或未变参数不必然意味着未训练；旧参考脚本还要求四项都变、每步非零。','通用条件改为有效优化步、有限梯度、整体非零和实际参数变化；旧参考验收不冒充任意架构标准。',('skills/admet-frozen-training/SKILL.md','新头须有有限非零梯度'),('skills/admet-frozen-training/scripts/check_evidence.py',"require(all(x>0")),
 F(9,'准备包生成器把Skill版本写死为v1.2','代码已修复，13项检查通过','实际正文v1.2.1也会交付v1.2元信息，妨碍判断是否收到新版；hash仍绑定原字节，不能夸大为一定读错正文。','版本从实际frontmatter读取，目标核验同时检查版本与冻结原文一致；缺失/错版本拒绝，旧任务包不改。',('skills/ml-preparation-only/scripts/preparation_packet.py','version = "v1.2"')),
 F(10,'准备阶段一概禁止安装和权重下载','待用户Q1','准备会话只能交未验证代码，主控反复补环境；此额外收窄不等于用户的“不训练”。','建议准许mini任务私有目录内准备获准依赖/资产及无更新接口检查。尚未改变权限；海南操作与训练仍不交准备方。',('skills/ml-preparation-only/SKILL.md','环境安装、权重下载和服务器执行由主控负责')),
 F(11,'精确分数隔离与train-only被写得像长期硬条件','待用户Q2/Q3；来源已澄清','官方valid可调参与本地角色隔离不同；只给模糊指南可能削弱下一步判断。换新Chat也不消除valid选择偏差。','建议准备/训练可看任务及分组汇总诊断，仍不给逐行答案；选模阶段保留valid，最终合训另决。未改当前数据/反馈权限。',('AGENTS.md','准备/训练会话只接收技术指南'),('policy.json','"training_labels"')),
 F(12,'首次学习锁容易被推广成永久禁止故障恢复','待用户Q4；单轮与通用已分开','一次试跑的防重复学习要求，如果永久套用会阻断自主恢复。','这次完成的作业不重跑；今后是否在原配置/总预算内有界恢复由用户核对。未知启动始终先对账，不能盲目重投。',('skills/admet-frozen-training/SKILL.md','恢复须先证明旧作业已退出且学习未启动')),
 F(13,'禁止读取其他会话产物没有合法复用例外','已修正','与使用主控明确交付的已验收旧资产/runner冲突。','允许只读本次明确列入输入的旧资产；仍禁止自行翻其他会话目录。',('skills/ml-preparation-only/SKILL.md','不读其他会话产物')),
 F(14,'训练执行方被要求更新主控专属索引/工作记录','已修正','训练Skill尾段与AGENTS写入边界矛盾；结束训练也可能误停独立资源观察。','执行方只写run回执；Skill、项目索引、工作记录由主控维护；资源观察直到用户停止。',('skills/admet-frozen-training/SKILL.md','更新项目工作记录和 Skill 索引'),('AGENTS.md','每个可用阶段更新')),
 F(15,'取回本机只写单目录与评分发布职责冲突','已修正','私有评分输出和Git发布副本可能有独立登记路径，无法同时满足字面禁令。','允许当次清单明列的取回/评分/发布工作副本，不扩大到其他目录或任何远端写入。',('skills/hainan-training-retrieval/SKILL.md','本机只写本次独占取回目录')),
 F(16,'30/60分钟发Chat、两批无收益停止等自定阈值','已从当前规范移除','会促成只训少量头就调用昂贵研究，或把助手建议当用户硬限制。','正常按约定比较批次评审；异常提前处理。4–8、20–40和三路均非永久上限或自动执行授权。旧建议保留在历史稿。',('design/chat_gateway_20261031/README.md','最多等到 60 分钟'),('design/chat_gateway_20261031/README.md','连续两批无可靠收益')),
 F(17,'渐进阅读与“必读全部实验原件”互相抵触','已修正模板rev8/Skill','历史越多，按字面执行越可能无限读或虚假报全读；无推翻历史却强求一条链也不合理。','各层索引必读、相关原件按问题下钻、全部可达；没有适用推翻链明确不适用。完整研究深度和六文件内容不缩减。',('design/chat_gateway_20261031/CHAT_PROMPT.md','取回的全部实验原件'),('skills/admet-evidence-review/SKILL.md','read_checks')),
 F(18,'总入口一律禁止推送，和已授权公开发布冲突','已修正','取回方可能在用户已选定ZYDTR方案上重复索要许可或停住。','按角色区分：登记科学包可发布；其他数据不扩大；官网仍仅用户手动提交。',('AGENTS.md','不自动上传赛事或推送仓库')),
 F(19,'通用海南Skill仍强制跳回旧SAP规范','已修正路由','旧规范还含禁Chat真值、镜像/网关等旧约束，和项目选择性继承冲突。','改到ADMET唯一入口；旧SAP只作来源映射中的选择性历史参考。',('rules/skills/hainan-compute-access/SKILL.md','ADMET 作业还须遵守其')),
 F(20,'全局mini运维Skill留了具体准备Skill版本','已移回项目索引语义','v1.2准备实测状态与通用运维能力无关，且已过期。','全局仅保留项目入口、根目录及监控协议；项目版本/行为验收看项目索引。',('rules/skills/<PREPARATION_HOST_ALIAS>-orbstack-ops/SKILL.md','v1.2修订')),
 F(21,'任何通用Skill文字修改都会令历史PLAN失效','实现局限保留；历史证据未动','本次只修海南路由，原实跑PLAN再对当前Skill校验就会hash不符。最初一项测试也确实失败。','新任务绑定当前版；历史验收必须读取当时冻结版。只修内存测试夹具，旧PLAN保持；后续检查器应区分历史复核与新准入，不能篡改旧hash凑通过。',('src/plan_checks.py',"if plan['hainan_skill_sha256']")),
 F(22,'部分“固定工具”仍是首轮特例','能力缺口已明示；未虚报实现','通用取回/评分/发布尚未抽取，旧check_evidence限定参考布局/0MiB，不能仅换run直接循环。','优先复用已验证内核、用清单和配置驱动；结构、科学、在线行为分别验收。此审查没有上线通用批量执行器。',('design/chat_gateway_20261031/contracts.json','Generic retrieval/scoring/publish'),('skills/admet-frozen-training/scripts/check_evidence.py',"g.findtext('fb_memory_usage/used')=='0 MiB'")),
 F(23,'接续检查器不识别主控亲自处理','文档已修正；工具仍缺processing状态','只有派别的Thread/外部等待/问用户/收口四类，主控亲自验收反而无法表达，容易为过门槛伪造派发。','真实当前turn和工作证据可证明主控在处理；没有自报就算完成。后续工具补processing与完成区分，不能无限留review_pending。',('scripts/check_handoff.py','unsupported disposition'),('skills/admet-evidence-review/references/handoff-completion.md','仅写received')),
 F(24,'提交CURRENT仍标专用Terra，实际已换Sol','已修正','目录入口与专用Thread身份冲突。','以submissions/thread.json身份为准，保留手动触发、不自动提交；未操作独立提交Thread。',('submissions/CURRENT.json','dedicated Terra')),
]
(a/'findings.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n')
# Sentence/line inventory is bookkeeping of the primary agent's full reading, not an automated semantic oracle.
paths=sorted((before/'adhoc_jobs/admet_training/skills').glob('*/SKILL.md'))+sorted((before/'adhoc_jobs/admet_training/skills').glob('*/references/*.md'))
rows=[]
for p in paths:
 rel=p.relative_to(before/'adhoc_jobs/admet_training').as_posix();text=p.read_text();heading='';in_code=False
 for n,line in enumerate(text.splitlines(),1):
  if not line.strip():continue
  if line.startswith('#'):heading=line.lstrip('# ').strip()
  if line.startswith('```'):in_code=not in_code
  # Keep original line text and expand Chinese sentence boundaries only outside code.
  sentences=[line] if in_code or line.startswith(('#','---','```','|')) else [x for x in re.split(r'(?<=[。！？；])',line) if x.strip()]
  for s in sentences:
   associated=[f['id'] for f in items if any(e['file']==str(p) and e['line']==n for e in f['evidence'])]
   if associated:
    verdict=' / '.join(next(f['status'] for f in items if f['id']==i) for i in associated)
    basis=' / '.join(next(f['action'] for f in items if f['id']==i) for i in associated)
   elif line.startswith(('#','---','```','name:','description:')):
    verdict='结构/导航';basis='非独立授权条款；链接另核验。'
   elif any(x in heading for x in ['教训','实测','案例','已经发生','已发生','已验证参考','原会话 Follow','真实']):
    verdict='保留为历史证据';basis='已读其含义和当前适用范围；本次不重新验证历史每个数值，不因此授予当前权限。'
   else:
    verdict='保留，按本角色与当次任务适用';basis='对照当前用户目标未发现新增冲突；具体文件格式、固定工具与检查方式属于实现选择，不冒充赛事或用户逐字条款。'
   rows.append({'file':rel,'original_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'line':n,'text':s,'section':heading,'verdict':verdict,'basis_or_action':basis,'finding_ids':associated})
(a/'clause-ledger.json').write_text(json.dumps({'method':'主控已通读全部15个项目Skill/参考文件并人工确定findings；此表只把原文按行/中文句界展开并定位发现项，不把关键词命中或程序生成当语义验收证据。未直接命中发现项的条款仍受同文件/根入口的范围纠正和待核对项约束。','rows':rows},ensure_ascii=False,indent=2)+'\n')
md=['# 项目Skill原文逐条审读记录','','原文快照与SHA保留。主控已通读六项Skill及九份引用；本表按原行/中文句界展开供逐条核对。问题与处置见同目录REPORT和findings.json；程序仅生成覆盖清单，不代替主控判断。历史事实未在本次逐项重跑。','']
for p in paths:
 rel=p.relative_to(before/'adhoc_jobs/admet_training').as_posix();md+=['## '+rel,'']
 for row in [x for x in rows if x['file']==rel]:
  md += [f"- L{row['line']}：{row['text']}",f"  - 判定：{row['verdict']}"+(f"；关联 {'、'.join(row['finding_ids'])}" if row['finding_ids'] else '')]
 md+=['']
(a/'CLAUSE_REVIEW.md').write_text('\n'.join(md)+'\n')
count=sum(len(p.read_text().splitlines()) for p in paths)
report=f'''# ADMET控制面复核

审查时间：{now}。主控亲自审读，未派新Agent/Thread，未连接海南、训练、评分、公开发布或发送新Pro请求。

问题主因在主控维护方式：用户硬约束、局部试跑条件、实现局限、历史状态被不断追加到同一入口，缺少明确退役和作用范围。不是准备模型单方面“不听话”。

## 覆盖与边界

已通读六项项目Skill及全部九份引用，共{count}行原文；逐行/句记录见[完整审读记录](CLAUSE_REVIEW.md)和[机器清单](clause-ledger.json)。另交叉审读项目入口/policy/来源映射、PRD/RFC/test/工作历史、架构/Prompt/字段合同、资源/提交/资料索引入口，以及通用海南与mini Skill。初始65文件快照在scope-manifest.json；后补涉及文件也保留before原件。

关键代码审读包括plan_checks、准备包生成器、Prompt渲染器、历史验收器、索引器、接续检查器、资源分类和本轮监督/资源执行路径。没有声称审计全工作区、每个历史run源码或重验全部历史数字。动态资源快照只是审查时样本，不作为当前选卡结果；本次没有完整复现共享/并行或全链行为。

来源分层：官方条款使用现有原文快照，冻结外部权重来自用户报告的赛方确认；他人服务/文件、资源共享、角色/模型、mini根入口、Pro深研究、取回公开、手动提交和偶发恢复来自本聊天明确要求。train-only、精确分数隔离、时间额度、特定文件/工具格式等是本地选择或当次计划，不能写成官方逐项禁令。本次是内部一致性审计，没有重新查询官网最新公告。

## 全部发现与处置

| ID | 问题 | 当前处置 |
|---|---|---|
'''
for f in items:report+=f"| {f['id']} | {f['title']} | {f['status']} |\n"
report+='\n每项的原文位置、影响和修改依据见[findings.json](findings.json)；原版、修改摘要在before/与changes.json。明确冲突已修；有待用户决定或代码尚未实现的条目没有伪装为关闭。\n\n'
report+='''## 不需要再次请用户批准的已明确事项

- 外部底座参数/buffer冻结；只更新获准的新模块。保护他人服务与文件，海南项目写入仅Michael；共享余量与并发按需求和不影响他人的证据决定，没有零显存或固定三路规则。
- 准备在mini Context Infrastructure根项目，输入输出可分任务子目录；准备不训练。资源观察和训练为独立Sol/xhigh；OpenCode观察Terra只收主控实际派发后的登记任务。
- 主控负责实验决策与Prompt；普通资源信号观察→等待中的训练方。Chat指南先回主控，再由主控下发OpenCode。取回与Chat网关分离；评分由指定取回方在本机完成。
- 新批新Pro、历史+本批渐进索引、充分深入研究和交叉核验；长不是缺陷。已有授权的科学包按清单发ZYDTR；官网提交仍是专用Thread手动触发。
- 偶发连接异常有界恢复；未知发送/启动先对账，不重投。当前已学习作业不因监控错误自动重训。

## 请用户核对的四项

这些是偏好或后续授权范围，不是工具安全拒绝，也不是要求用户重批已授权训练。已通过本聊天问题卡发送；答复前保留当前运行权限。

| 编号 | 当前额外限制/疑点 | 建议 |
|---|---|---|
| Q1 | 准备方一律不能安装依赖或下载底座 | 允许mini任务私有目录内安装获准依赖、下载获准资产及无参数更新接口检查；不训练、不碰海南及共享环境。 |
| Q2 | 准备和训练方一律不能看精确评分 | 允许任务/分组汇总分数和技术诊断；仍不给逐行valid答案、残差或查表指示。 |
| Q3 | 只用train.Y是否应成为永远的规则 | 选模阶段保留valid供评分和分析；最终是否train+valid合训另行决定，并核实适用赛事规则，不能再把该valid成绩当未见泛化证据。 |
| Q4 | 学习一旦开始，故障后是否必须停止等用户 | 今后在已批准总预算、原配置下允许主控有界恢复；原状态未知先对账，确实退出后才判断恢复/重训。当前已完成这次不重跑。 |

## 本轮实际验证及仍需解决的实现

准备包版本修复13项、Prompt渲染7项、计划检查11项通过，共31项。计划检查初次有一项因通用Skill文字hash变化失败，原输出保留；修的是内存中的当前版本测试夹具，实际旧PLAN不改。这同时证明历史复核不应机械对可变全局文件做hash比较。[测试原件](tests.json)。21个活动入口/Skill/引用/Prompt的本地Markdown链接核验无缺失；不代表外网可读或所有代码正确。

当前共享分支、批量通用计划/执行、监控采样异常与已完成凭据的接续、接续检查器的processing状态仍需要代码工作。通用Skill不禁止这些能力，但现有局部实现不能直接宣称支持。控制文档改正不等于上线修复；本次未部署新的远端运行代码。

v4训练回报已由主控消费：96件取回文件摘要和完成凭据身份通过，编码器11项记录相等，273行预测为有限数值；原件同时支持科学worker0及监督125。源码显示监督先采样，再检查子进程退出；异常路径不消费已有完成凭据。现场缺失VmRSS的精确内核状态未保存，根因仍未知。完整科学/写入轨迹验收尚未完成，不给总体PASS；不清学习锁、不重跑。[主控局部核验](training-callback-check.json)。该run已从资源等待移至终态记录，独立观察继续。

## 生效与接续

唯一活动入口仍是项目AGENTS，没有新增第二套长期Skill。架构历史移出当前正文，已完成/未完成与当前角色路由分开。修改只用于后续明确版本绑定的任务；旧任务包、Prompt v7、原始运行源码/PLAN/失败和官方快照不回写。新Prompt为rev8，证据Skill v0.4.2，准备Skill v1.2.2，取回Skill v0.4.1。

主控接下来消费用户对Q1–Q4的选择，统一相应文本、生成器与模板；继续独立验收当前完整训练产物，并修复已定位的监督/通用能力缺口。后续仍按原登记周期取回评分发布及Pro分析，不能把本次审查或宽泛研究建议当新HPO许可。尚无一次完整无中断全链通过的结论。
'''
(a/'REPORT.md').write_text(report)
(a/'review-coverage.json').write_text(json.dumps({'recorded_at':now,'skill_and_reference_files_fully_read':len(paths),'original_lines':count,'line_sentence_items':len(rows),'findings':len(items),'scope':'All current project Skill prose and all referenced Markdown; core control docs cross-read; selected enforcement code inspected. Historical run claims not all re-executed.','files':[{'path':str(p.relative_to(before)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'lines':len(p.read_text().splitlines()),'review':'full_text_read_by_primary'} for p in paths]},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'skill_files':len(paths),'original_lines':count,'clause_items':len(rows),'findings':len(items)},ensure_ascii=False))
