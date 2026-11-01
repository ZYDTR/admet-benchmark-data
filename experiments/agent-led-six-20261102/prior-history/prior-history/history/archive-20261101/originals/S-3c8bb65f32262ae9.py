"""Apply the four explicit user choices; snapshot every edited current file first."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

W = Path('<LOCAL_WORKSPACE>')
R = W / 'adhoc_jobs/admet_training'
A = Path(__file__).resolve().parent
now = datetime.now(timezone.utc).isoformat()
pending = {}

def read(rel):
    return pending.get(rel, (R / rel).read_text())

def replace(rel, old, new):
    text = read(rel)
    assert text.count(old) == 1, (rel, old, text.count(old))
    pending[rel] = text.replace(old, new)

def append(rel, text):
    pending[rel] = read(rel).rstrip() + '\n\n' + text + '\n'

def update_json(rel, update):
    obj = json.loads(read(rel))
    update(obj)
    pending[rel] = json.dumps(obj, ensure_ascii=False, indent=2) + '\n'

decision_ref = 'audits/control-plane-20261101/user-decisions-20261101/decisions.json'
def policy(p):
    p['policy_revision'] = 2
    p['user_decision_record'] = decision_ref
    v = p['validation_policy']
    v['feedback_to_preparation_or_training'] = 'exact_task_and_group_aggregate_scores_and_technical_diagnostics_without_row_truth_residuals_or_lookup_answers'
    v['feedback_scope'] = {
        'allowed': ['task_level_exact_scores', 'group_level_exact_scores', 'technical_diagnostics'],
        'excluded': ['row_level_valid_truth', 'row_level_valid_residuals', 'lookup_answers', 'aggregates_that_reveal_individual_answers'],
        'provenance_required': ['run', 'task', 'split', 'metric_definition', 'group_definition_if_any', 'scoring_receipt'],
        'scoring_role_unchanged': True,
        'does_not_authorize_whole_analysis_packet_access': True,
    }
    v['selection_phase'] = 'learn_on_official_train_Y; retain_valid_for_scoring_and_analysis'
    v['final_train_valid_refit'] = 'separate_future_user_decision; not_currently_authorized'
    v['authorization_basis'] += ' User 2026-11-01 Q2 permits exact task/group aggregate feedback and technical diagnostics; Q3 retains valid during selection and defers final combined fitting.'
    p['preparation_permissions'] = {
        'scope': 'mini_task_private_directories_registered_in_TASK',
        'allowed': ['prepare_task_dependencies', 'download_approved_base_assets', 'lightweight_interface_checks_without_parameter_updates'],
        'task_records': ['approved_asset_sources_and_versions', 'private_write_directories', 'applicable_resource_budget'],
        'excluded': ['training', 'whole_batch_encoding', 'hainan_operations', 'shared_environment_changes', 'unapproved_model_assets'],
        'record_actual_dependencies_asset_hashes_commands_and_check_results': True,
        'no_repeated_permission_for_already_approved_scope': True,
    }
    p['training_recovery_policy'] = {
        'scope': 'future_batches_within_original_scientific_configuration_and_approved_total_budget',
        'decision_owner': 'controller',
        'recoverable_failure_requires_evidence': True,
        'unknown_launch_or_state': 'reconcile_original_job_before_any_start',
        'no_concurrent_duplicate_job': True,
        'checkpoint_restore': 'verify_checkpoint_input_code_config_optimizer_rng_and_progress_identity',
        'restart_if_restore_not_possible': 'controller_decision_after_original_job_exit_verified_and_remaining_budget_checked',
        'bounds': 'controller_records_attempt_limit_and_remaining_compute_or_time_budget_before_recovery; all_attempts_count',
        'completed_learning': 'collect_and_independently_accept_existing_artifacts; no_automatic_retraining',
        'current_completed_run_relaunch_authorized': False,
        'frozen_historical_plans_unchanged': True,
        'implementation_validation': 'generic_checkpoint_recovery_not_yet_runtime_verified',
    }
update_json('policy.json', policy)

replace('AGENTS.md', '本入口当前仅使用官方 train.Y 学习，内部划分做早停；', '本入口选模阶段仅使用官方 train.Y 学习，内部划分做早停；valid保留用于评分与分析，最终是否train+valid合训由用户另行决定；')
replace('AGENTS.md', '准备/训练会话只接收技术指南与盲输入，不接收私有验证标签、精确分数或逐行误差。', '准备/训练会话可接收任务级、分组级精确汇总评分和技术诊断，保留指标、分组与来源身份；不接收逐行valid真值、残差或查表答案，也不能通过极小分组或差分还原个体答案。实际评分仍由指定宿主角色完成。')
replace('AGENTS.md', '不回传精确官网分数给准备/训练方。', '结果先交用户和主控；主控可按统一反馈边界将任务级/分组级汇总评分与技术诊断纳入后续准备材料。')
replace('AGENTS.md', '准备方使用 `skills/ml-preparation-only/SKILL.md`，', '准备方可在mini任务私有目录准备任务依赖、下载已批准底座，并做不更新参数的轻量接口检查；环境、缓存和临时文件须在TASK登记的私有写入范围内，不修改共享环境、不训练、不操作海南。准备方使用 `skills/ml-preparation-only/SKILL.md`，')
replace('AGENTS.md', '每次 run 独占目录；失败留证，不覆盖旧尝试。', '每次 run 独占目录；失败留证，不覆盖旧尝试。未来批次遇到已查明的可恢复故障，主控可在原科学配置及已批准总预算内登记有界恢复；先核对原作业身份与状态，恢复不可行时须证明原作业已退出，再决定是否重训。全部尝试计入总预算；已完成学习的当前作业不因此重跑。')

prep = 'skills/ml-preparation-only/SKILL.md'
replace(prep, 'version: 1.2.2', 'version: 1.3.0')
replace(prep, 'Workflow。v1.2.2，', 'Workflow。v1.3.0，')
replace(prep, '核验真实行身份、生产消费接口、完整恢复状态和检查点身份，缺依赖明确未验证。', '可在mini任务私有目录准备依赖和已批准权重，核验真实行身份、生产消费接口、恢复状态和检查点身份；不更新参数。')
replace(prep, '- 只读取任务指定输入和必要公开技术资料；只写自己的输出目录，包括临时文件、缓存、日志、`__pycache__`。临时路径、shell 重定向、库缓存都须显式落在自己的输出目录；命令失败也不能改用目录外 `/tmp`。环境安装、权重下载和服务器执行由主控负责；缺依赖就记录原始错误和未验证项，继续完成能做的准备，不自行扩权。', '- 可在mini本任务私有目录安装任务所需依赖、下载已批准底座及其必要资产，并做不更新参数的轻量接口检查。TASK登记可用资产来源/版本、私有写入目录及适用预算；默认新建内容均在本任务output内，可用其中venv、assets、cache、tmp等子目录。缓存、编译、日志、`__pycache__`及安装临时文件同样落在登记范围；不改共享环境、不取得海南权限。已批准范围无须重复询问。依赖或下载失败保留原始错误，完成能做的部分并说明未验证项。')
replace(prep, '- 不寻找验证/测试真标签，', '- 可使用任务交付的任务级/分组级精确汇总评分和技术诊断，核对其run、任务、split、指标/分组定义与来源；不读取含逐行valid真值、残差或查表答案的分析原包，也不通过分组或差分还原个体答案。不寻找验证/测试真标签，')
replace(prep, '输出目录含代码、依赖/资产清单、', '输出目录含代码、依赖/资产清单（实际版本、下载来源与摘要、私有安装/缓存路径及命令退出记录）、')
replace('skills/ml-preparation-only/scripts/preparation_packet.py', '"实际训练由宿主执行；你不更新参数、不整批编码、不安装/下载、不访问服务器，也不派生Agent或会话。"', '"允许在mini任务私有目录准备任务依赖、下载已批准底座，并做不更新参数的轻量接口检查；写入范围及资产以TASK和Skill为准。"\n              "实际训练由宿主执行；不训练、不整批编码、不操作海南、不修改共享环境，也不派生Agent或会话。"')
replace('skills/ml-preparation-only/scripts/test_preparation_packet.py', '        self.assertIn("skill-use.json", prompt)', '        self.assertIn("skill-use.json", prompt)\n        self.assertIn("允许在mini任务私有目录准备任务依赖、下载已批准底座", prompt)\n        self.assertIn("不更新参数", prompt)\n        self.assertIn("不操作海南、不修改共享环境", prompt)\n        self.assertNotIn("不安装/下载", prompt)')

train = 'skills/admet-frozen-training/SKILL.md'
replace(train, '更新：2026-11-01（控制面复核；旧冻结任务不变）', '更新：2026-11-01（用户确认汇总反馈、选模保留valid及有界恢复；旧冻结任务不变）')
replace(train, '当前入口只以官方 train.Y 学习；', '选模阶段只以官方 train.Y 学习，valid保留评分/分析，最终train+valid合训由用户另行决定；')
replace(train, '本轮授权没有评分就只交付预测。', '本轮授权没有评分就只交付预测。可读取主控交付的任务级/分组级精确汇总评分和技术诊断以理解目标，注明来源和用途；不接收逐行valid真值、残差、查表答案或还原个体答案的分组。看汇总结果不授予自行评分权。')
replace(train, '将来是否可恢复已有学习，由明确的批次恢复预算决定；未知状态始终先对账。', '用户已允许未来批次对已查明的可恢复故障，在原科学配置、已批准总预算内由主控留证安排有界恢复；未知状态始终先对账。')
replace(train, '## 成功的证据', '## 批次故障的有界恢复\n\n主控记录故障依据、原作业run/PID/启动时间、存活状态、已完成进度、累计消耗、剩余总预算及本次恢复次数/时间上限。所有失败尝试计入同一预算，不以新attempt重置额度。能恢复时核对checkpoint与输入、代码、配置、head/优化器/RNG及累计步数身份，在原科学配置内续接；不能恢复时须核实原作业已退出，主控再判断余量是否足以从头重训。状态不明持续查询原作业，完成学习则取回验收，不因外层监控异常重复学习。超出原配置或总预算属于新方案，不能称为恢复。\n\n恢复的成功标准是：只有一个身份明确的活动作业、各尝试与进度可追溯、恢复状态匹配、冻结和数据边界仍通过、总消耗在限额内。恢复入口不具备这些证据时标记未验证，交主控完善实现；不能清除旧完成锁或修改失败原件来制造成功。当前已完成学习的monitor-mae作业不重训；通用断点恢复尚未真机验收。\n\n## 成功的证据')
append('skills/admet-frozen-training/references/runtime-recovery.md', '2026-11-01用户确认的现行规则：未来批次允许在原科学配置及已批准总预算内有界恢复，具体判断与验收见[训练Skill](../SKILL.md#批次故障的有界恢复)。上文“学习产物不存在/首次学习锁”属于当时只准首次学习的试验，不是通用断点恢复条件；旧记录不改，当前已完成学习的作业不因此重跑。')

evidence = 'skills/admet-evidence-review/SKILL.md'
replace(evidence, 'Workflow，v0.4.2，', 'Workflow，v0.4.3，')
replace(evidence, '开放分析后依旧只有官方train.Y进入训练；', '选模阶段只有官方train.Y进入训练，valid用于评分与分析，最终是否train+valid合训由用户另行决定；')
replace(evidence, '训练和准备方继续不接收真值/逐行残差/精确分数。', '训练和准备方可接收任务级/分组级精确汇总评分及技术诊断，附run/task/split、指标/分组定义和评分来源；仍不接收逐行valid真值、残差或查表答案，不用极小分组或差分还原个体答案。交付是获准的反馈投影，不能把可能带真值的整个分析包直接下发。')
retrieval = 'skills/hainan-training-retrieval/SKILL.md'
replace(retrieval, 'Workflow。v0.4.1，', 'Workflow。v0.4.2，')
replace(retrieval, '规则见[评分与发布]', '任务级/分组级精确汇总评分和技术诊断可由主控纳入准备/训练反馈，逐行valid真值与残差仍只在获准的评分/分析范围内。规则见[评分与发布]')
scoring = 'skills/hainan-training-retrieval/references/scoring-and-publishing.md'
replace(scoring, '适用 v0.4。', '适用 v0.4.2。')
replace(scoring, '海南训练和 mini 准备方继续只有盲输入。', '海南训练和mini准备方的valid/test样本保持盲输入，可另接收任务级/分组级精确汇总评分与技术诊断；选模阶段保留valid，最终合训由用户另行决定。')
replace(scoring, '公开评分可被任何人读取，不能宣称对准备方实现技术保密；准备/训练不读取分析评分包仍是角色规则。', '公开评分可被任何人读取，不能宣称对准备方实现技术保密。准备/训练可读取主控交付的精确汇总反馈；反馈须绑定run/task/split、指标/分组定义和评分回执，排除逐行valid真值、残差、查表答案以及可还原个体答案的分组或差分。若原分析包含受限逐行信息，另生成获准反馈文件及来源映射，不能整包转发。')

D = 'design/chat_gateway_20261031/'
replace(D+'CHAT_PROMPT.md', 'revision8', 'revision9')
replace(D+'CHAT_PROMPT.md', '当前学习仅使用官方 train.Y，内部划分做早停；', '选模阶段仅使用官方 train.Y，内部划分做早停；valid保留评分与分析，最终train+valid合训由用户另行决定；')
replace(D+'CHAT_PROMPT.md', '给OpenCode的指南不得包含私有标签、精确分数或逐行误差。', '给OpenCode及训练方的指南允许包含任务级/分组级精确汇总评分与技术诊断，附run/task/split、指标/分组定义和评分来源；不得包含逐行valid真值、残差、查表答案或用于还原个体答案的分组/差分。指南是获准反馈投影，不能直接转发带真值的整个分析包。')
replace(D+'CHAT_PROMPT.md', '只要求准备，不训练、不安装到海南、不访问私有验证标签。指南本身不含精确验证分数或逐行残差，关联问题通过ID和技术描述表达。', '只要求准备：允许mini在任务私有目录准备任务依赖、下载已批准底座并做无参数更新的轻量接口检查；明确资产来源/版本、写入目录和适用预算，不改共享环境、不训练、不操作海南、不访问逐行valid真值。指南可含带来源的任务级/分组级精确汇总评分与技术诊断，不含逐行残差或查表答案；关联问题通过ID追溯。')
replace(D+'README.md', '训练当前只用train.Y。分析可见不等于新增公开权限；精确分数对准备/训练的隔离是本地选择，正在本次控制审查中向用户核对。', '选模阶段只用train.Y，保留valid评分与分析，最终合训另由用户决定。分析可见不等于新增公开权限；用户已允许准备/训练读取任务级/分组级精确汇总评分与技术诊断，逐行valid真值、残差和查表答案仍不下发。')
replace(D+'README.md', '偶发连接异常有界恢复；状态未知查询原作业，不重复学习。', '偶发连接异常有界恢复；未来批次已查明的可恢复故障，可由主控在原科学配置和已批准总预算内留证恢复，确认原作业退出后才可决定重训。状态未知先查询原作业，避免重复学习。')
append(D+'README.md', '2026-11-01用户四项选择已写入policy及各角色Skill：准备方可用mini任务私有环境准备依赖/已批准权重；汇总反馈开放；选模保留valid；未来批次有界恢复。准备不训练、不操作海南。更新只用于后续版本化派发，当前已完成科学学习的run不重跑。决策与检查见[落实记录](../../audits/control-plane-20261101/user-decisions-20261101/REPORT.md)。')
replace(D+'GATEWAY_PROMPT.md', 'revision13', 'revision14')
replace(D+'GATEWAY_PROMPT.md', '当前证据Skill为v0.4.2', '当前证据Skill为v0.4.3')
update_json(D+'prompt_contract.json', lambda p: p.update(template_revision=9))
def contracts(p):
    p['revision'] = 16
    p['catalog_skill']['version'] = '0.4.3'
    p['prompt_contract']['template_revision'] = 9
    p['scoring']['exact_task_and_group_aggregate_feedback_to_preparation_or_training'] = True
    p['scoring']['row_truth_residuals_lookup_answers_to_preparation_or_training'] = False
    p['scoring']['feedback_scope_source'] = '../../policy.json#/validation_policy/feedback_scope'
    p['validation_analysis_proposal']['selection_phase_learning'] = 'official_train_Y_only; valid_scoring_and_analysis'
    p['validation_analysis_proposal']['final_train_valid_refit'] = 'separate_future_user_decision'
    p['current_user_decisions'] = '../../' + decision_ref
update_json(D+'contracts.json', contracts)
idx = 'skills/INDEX.md'
replace(idx, 'v1.2.2；v1.2冷启动', 'v1.3.0；允许mini任务私有依赖/已批准权重准备，新版权限行为待实测；v1.2冷启动')
replace(idx, '| v0.4.1；历史302文件', '| v0.4.2；允许任务/分组汇总反馈，原始真值隔离；历史302文件')
replace(idx, '| v0.4.2；主控Prompt', '| v0.4.3；汇总反馈/选模边界同步；主控Prompt')
append(idx, '2026-11-01用户确认四项偏好已纳入当前规则，见[落实记录](../audits/control-plane-20261101/user-decisions-20261101/REPORT.md)。训练Skill增加未来批次有界恢复的证据与预算标准；当前完成作业不重跑，通用恢复实现尚未真机验收。下一次派发绑定本索引对应新版及引用，旧任务快照保留。')
append('docs/source-map.md', '2026-11-01当前用户决策：准备允许mini任务私有依赖和已批准权重下载；准备/训练可见任务级、分组级精确汇总评分和技术诊断，逐行valid真值、残差和查表答案仍隔离；选模保留valid，最终合训另议；未来故障可在原配置及已批准总预算内由主控留证安排有界恢复。以上是用户明确的项目控制，不是新增赛事条款。原件及落实范围见[决策记录](../audits/control-plane-20261101/user-decisions-20261101/REPORT.md)。')

C = 'cycles/monitor-mae-e2e-20261101/'
replace(C+'CONTINUE.md', '先完成该审查及用户需要确认的偏好，', '审查已完成，用户四项偏好已确认并落实到当前规范，')
replace(C+'CONTINUE.md', 'revision8、证据Skill v0.4.2', 'revision9、证据Skill v0.4.3')
append(C+'CONTINUE.md', '四项选择落实见 ../../audits/control-plane-20261101/user-decisions-20261101/REPORT.md。当前policy已更新，旧PLAN仍绑定原快照；不得为通过新hash回写旧PLAN。后续准备/评分反馈/网关任务使用新版本；本轮科学学习完成，学习额度仍为0。')
def cycle(p):
    p['updated_at'] = now
    p['control_policy_questions'] = []
    p['control_policy_decisions'] = '../../' + decision_ref
    p['next_action'] = 'Primary completes full training artifact/trace acceptance under original frozen execution contract; next dispatch uses the newly confirmed policy and Skill versions. No repeated learning.'
update_json(C+'status.json', cycle)
def audit(p):
    p['state'] = 'audit_completed_user_policy_choices_applied'
    p['recorded_at'] = now
    p['pending_questions'] = []
    p['user_decisions'] = 'user-decisions-20261101/decisions.json'
    p['decision_application_report'] = 'user-decisions-20261101/REPORT.md'
update_json('audits/control-plane-20261101/status.json', audit)
append('docs/working.md', f'## 2026-11-01 四项用户决策落实\n\n记录时间UTC {now}。主控完整读取Best Practice后，将用户Q1–Q4写入policy、AGENTS、准备/训练/取回/研究Skill、准备包真实生成入口及Chat模板revision9。准备v1.3.0、取回v0.4.2、证据v0.4.3；原任务快照和当前已完成学习的PLAN/源码保持。详见audits/control-plane-20261101/user-decisions-20261101/REPORT.md；实现测试与模型真实行为分开记录。主控接续当前训练的完整独立验收，不因监督125重训。')

changes = []
for rel, new in pending.items():
    p = R / rel
    old = p.read_bytes()
    backup = A / 'before' / rel
    assert not backup.exists(), backup
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_bytes(old)
    p.write_text(new)
    changes.append({'path': rel, 'before_sha256': hashlib.sha256(old).hexdigest(), 'after_sha256': hashlib.sha256(p.read_bytes()).hexdigest()})

decisions = {
    'recorded_at_utc': now,
    'source': 'User answers to request_user_input_async call_528d2e7f860b44c3bb985939dd3a8b34',
    'answers': {'Q1': '允许在任务私有目录准备（推荐）', 'Q2': '允许看汇总评分和诊断（推荐）', 'Q3': '选模保留 valid，最终合训另行决定（推荐）', 'Q4': '允许有界恢复，主控留证判断（推荐）'},
    'policy_revision': 2,
    'frozen_historical_tasks_unchanged': True,
    'new_training_started': False,
    'new_threads_or_automations': False,
    'permission_to_retrain_current_completed_run': False,
    'model_behavior_tested': False,
}
for name, value in [('changes.json', changes), ('decisions.json', decisions)]:
    with (A / name).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
print(json.dumps({'files_changed': len(changes), 'recorded_at': now}))
