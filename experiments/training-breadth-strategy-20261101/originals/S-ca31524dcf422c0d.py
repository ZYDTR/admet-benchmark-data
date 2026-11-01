from pathlib import Path
import json,hashlib,datetime
w=Path.cwd();r=w/'adhoc_jobs/admet_training';a=r/'audits/control-plane-20261101';c=r/'cycles/monitor-mae-e2e-20261101';now=datetime.datetime.now(datetime.timezone.utc).isoformat();changes=json.loads((a/'changes.json').read_text())
def save(p,new):
 old=p.read_bytes();new=new.encode() if isinstance(new,str) else new
 dst=a/'before'/p.relative_to(w);dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():dst.write_bytes(old)
 elif dst.read_bytes()!=old:
  other=a/'concurrent-before'/p.relative_to(w);other.parent.mkdir(parents=True,exist_ok=True);other.write_bytes(old)
 p.write_bytes(new);changes.append({'path':str(p.relative_to(w)),'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':hashlib.sha256(new).hexdigest()})
def js(p,d):save(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=c/'CONTINUE.md';history=p.with_name('history-through-v4-20261101.md');assert not history.exists();history.write_bytes(p.read_bytes())
save(p,'''# 当前周期：控制面复核与训练终态独立验收

项目入口是 ../../AGENTS.md。当前真实状态读 status.json，旧准备/部署/等待过程在[历史记录](history-through-v4-20261101.md)，其中v1/v2/v3限制不能覆盖v4或用户新要求。

用户最新要求主控逐条复核整个控制面与Skill；本次审查在 ../../audits/control-plane-20261101/REPORT.md。先完成该审查及用户需要确认的偏好，不把这次审查变成新训练或新的分析请求。

本轮Qwen准备已结束，主控修复科学元数据，Terra观察队列空且已暂停。海南原Sol/xhigh的v4实际学习已完成：原始凭据支持75次更新、273行盲预测；外层监控VmRSS异常退出125。原执行状态failed和首次学习锁必须保留；不得重跑或清锁。主控已核验96个取回文件摘要、完成凭据身份、编码器11项前后记录和预测有限性；这还不是完整科学/写入边界验收。证据见 ../../audits/control-plane-20261101/training-callback-check.json。

当前负责人为主控private-role-298cc5edc25e。接续动作是完整审读本run源码、训练/写入轨迹与产物，分别判定科学结果可用性和监督失败；之后在原授权内安排指定取回Thread固定评分/批准发布，再由既有网关完成本批新Pro请求与六文件回收。不能把monitor失败自动当科学失败，也不能仅凭worker完成跳过主控验收。

本周期原授权仍是一个新训练及其后续取回/评分/发布/Pro往返；没有追加HPO或自动赛事上传。v4部署/科学源码、PLAN及当时冻结Skill都不回写。新的通用Skill修订用于后续任务，派发时必须显式绑定新版本；冻结旧计划的历史复核用当时快照，不为通过当前全文件hash检查修改旧证据。

网关已准备一个空白Pro草稿，正式消息尚未发送，不再建Chat或发占位。主控模板现在revision8、证据Skill v0.4.2；旧v7交接包保留，下一正式任务需重新绑定当前适用版本，不能自动追随可变文件。未来按比较批次深评审，不按每个头/固定30或60分钟强制发Chat。

独立海南观察仍沿用automation-5，每10分钟只读更新，直到用户停止。此次训练已终态，移出活动等待登记，不再发资源唤醒；无主控新定时。正常资源变化直接通知登记中仍等待的训练方，主控只接实质故障和结果。其他手动提交Thread独立，不因本次审查派新任务。
''')
d=json.loads((c/'status.json').read_text());keep=['new_preparation_dispatched','analysis_sent','chat_request_id','single_trigger_full_cycle_verified','preparation_session_id','preparation_request_id','preparation_model','gateway_draft','gateway_creation_probe','gateway_creation_disposition','monitor_thread_id','monitor_state','execution_thread_id','execution_turn_id','current_dispatch','resource_handoff','resource_handoff_model_execution_verified']
new={k:d[k] for k in keep if k in d};new.update(state='controller_control_audit_and_training_terminal_review',updated_at=now,new_training_started=True,scientific_worker_completed=True,supervisor_exit_code=125,full_independent_training_acceptance=None,learning_starts_remaining=0,monitor_active=False,next_owner='private-role-298cc5edc25e',next_action='Complete control audit and separate full training artifact/trace acceptance; no repeated learning. Then continue registered retrieval/score/publication/Pro cycle.',control_audit='../../audits/control-plane-20261101/REPORT.md',independent_terminal_partial_check='../../audits/control-plane-20261101/training-callback-check.json',historical_state_snapshot='../../audits/control-plane-20261101/before/adhoc_jobs/admet_training/cycles/monitor-mae-e2e-20261101/status.json')
js(c/'status.json',new)
p=r/'resources/hainan/registry.json';d=json.loads(p.read_text());moving=[x for x in d['active_runs'] if x['request_id']=='admet-monitor-mae-e2e-20261101:main:resume-residual:v4'];assert len(moving)==1
entry=moving[0];entry.update(state='execution_terminal_supervisor_failed_science_completed_main_review',terminal_recorded_at=now,resource_wake_enabled=False,independent_acceptance='pending',terminal_evidence=str(r/'runs/hainan-mae-monitor-20261101/operator/execution-04/result.json'))
d['active_runs']=[x for x in d['active_runs'] if x is not entry];d['completed_runs'].append(entry);d['updated_at']=now;js(p,d)
p=r/'resources/hainan/CONTINUE.md';save(p,'''# 海南资源观察接续

以本目录 registry.json 的真实任务登记为准，latest.json/status.json是采样事实。用户要求的独立观察使用原automation-5每10分钟执行一轮，直到用户停止；无变化只落盘，不另建定时。

入口为项目AGENTS与资源观察Skill；海南操作先读通用连接Skill及connection参考。只查机器/GPU/必要进程元数据，不读取同事项目、不训练、不安装、不更改远端服务和文件。运行 implementation/observe.py 前遵守已有命令身份核验；旧原件及解析版本保留。

登记中的原训练任务仅在真实状态waiting_for_resources、请求身份一致且出现有意义候选/余量变化时，直接通知该原训练Thread，由它现场复核并继续原授权。响应不明先核回执；部署/学习/收集中、终态或状态未知不重复唤醒。普通资源变化不经主控中转；实质故障或登记截止问题回主控一次。没有等待任务也照常记录资源，但不产生训练派发。

候选按需求和余量判断，不设零显存/任意小已用上限。现有normalize分类仍是旧保守口径，occupied包含非零显存，不能把这个词当禁止共享；资源变化比较需结合实际数值和原始进程证据。共享还需满足通用Skill的负载/影响条件，观察本身不授予资格。

monitor-mae v4已真实终态，原worker完成但外层监控125；主控在做独立验收，已移入completed_runs并关闭资源唤醒。不要再沿用v3仅回主控、4MiB草稿或旧活动状态。v4冻结协议及实际消费证据仍留在implementation/handoff-v4-consumption.json及对应cycle；旧接续全文已保存到本次控制审查before快照，只有历史用途。

每次保留唯一观测ID、真实时间、原件/hash、成功/partial/失败和前后变化。15分钟以上或未知记录须补查，启动前直接核验始终归训练方。连接偶发异常按通用Skill有界退避；已用尽本轮重试时下个既有周期再接续。无权改变训练预算或其他Thread任务。
''')
(a/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n');print({'changed_files_total':len(changes),'resource_waiting_or_active':len(d.get('active_runs',[]))+len(d.get('waiting_runs',[]))})
