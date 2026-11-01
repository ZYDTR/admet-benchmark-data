from pathlib import Path
import datetime,hashlib,json,shutil,xml.etree.ElementTree as E
R=Path(__file__).resolve().parents[1];F=R/'raw/final-fetch';A=F/'artifacts'
load=lambda p:json.loads(Path(p).read_text())
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def link(p,label):return f'[{label}]({R/p})'
def cn(t):return datetime.datetime.fromisoformat(t).astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
plan=load(R/'PLAN.json');e=load(A/'training-evidence.json');check=load(R/'operator/evidence-check.json');supp=load(R/'operator/supplemental-checks.json');post=load(R/'acceptance/postcheck.json');audit=load(R/'acceptance/audit-final-fetch.json');rs=load(R/'operator/resource-summary.json');read=load(R/'operator/read-receipt.json');manifest=load(F/'fetch-manifest.json')
assert check['checks_passed'] and supp['passed'] and supp['plan_unchanged']
assert len(manifest)==65 and len(audit['traces'])==3 and not audit['manifest_mismatches']
assert all(not t['outside_mutation_evidence'] and not t['unresolved_count'] and not t['pending_at_eof'] for t in audit['traces'])
assert all(p['status'] in ['gone','pid_reused','exited_zombie'] for p in post['own_processes'])
protected=[]
for x in read['sources']:
 if x['path'].endswith('/CONTINUE.md'):continue
 protected.append({'path':x['path'],'before_sha256':x['sha256'],'after_sha256':sha(x['path']),'unchanged':sha(x['path'])==x['sha256']})
assert all(x['unchanged'] for x in protected)
for p in A.iterdir():
 target=R/'artifacts'/p.name
 if target.exists():assert sha(target)==sha(p)
 else:
  with target.open('xb') as f:f.write(p.read_bytes())
artifacts=[{'path':'artifacts/'+p.name,'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((R/'artifacts').iterdir()) if p.is_file()]
save(R/'artifacts.json',{'run_id':plan['run_id'],'files':artifacts,'primary_checkpoint':'artifacts/caco2_wang-head.pt','predictions':'artifacts/predictions.csv'})
health=E.fromstring(post['gpu_health']).find('gpu');assert health.findtext('gpu_recovery_action')=='None'
now=datetime.datetime.now(datetime.timezone.utc).isoformat();before=load(R/'raw/environment-before02.stdout')
jobs=[]
for phase in ['cuda01','cuda02','train01']:
 d=load(F/'raw'/f'{phase}-dispatch.json');exit=load(F/'raw'/f'{phase}-exit.json');launch=load(F/'raw'/f'{phase}-launch.json')
 jobs.append({'job_id':phase,'supervisor_pid':d['pid'],'strace_pid':launch['pid'],'pgid':launch['pgid'],'at':d['at'],'start_stat':d['start_stat'],'exit':exit,'worker_pids':rs[phase]['own_gpu_pid_matches'],'traces':'raw/final-fetch/raw/'+phase+'.strace'})
base=load(A/'encoder-before.json');kinds={k:sum(v['kind']==k for v in base['tensors'].values()) for k in ['parameter','buffer']}
receipt={'schema_version':1,'run_id':plan['run_id'],'observed_at':now,'review_scope':'execution-thread self-validation; parent independent acceptance pending','request':{'task':'Caco2/CheMeleon frozen backbone + 256 head','head_config':plan['head_config'],'same_existing_chat':True,'cold_start':False},'authorization':{'role':'explicitly_authorized_host_operator_leaf','remote_write_root':plan['remote_directory'],'local_write_root':str(R),'own_concurrent_jobs':1,'no_delegation':True},'target':{'host':'private-compute','uid':1012,'gid':1012,'route':'Registered Windows stream, pinned SSH keys','gpu_index':3,'gpu_uuid':load(F/'source/config.json')['gpu_uuid'],'post_recovery_action':health.findtext('gpu_recovery_action')},'training_completed':True,'prediction_completed':True,'freeze_verified':True,'write_scope_verified':True,'own_resources_released':True,'scoring_performed':False,'upload_performed':False,'independent_parent_acceptance':None,'configuration_verified':supp,'training':{'epochs_run':e['epochs_run'],'best_epoch_1_based':e['best_epoch_1_based'],'optimizer_steps':e['optimizer_steps'],'nonzero_gradient_steps':e['nonzero_gradient_steps'],'fit_rows':e['fit_rows'],'internal_validation_rows':e['internal_validation_rows'],'head_parameters':524801,'head_parameter_shapes':e['head_parameter_shapes'],'head_initial_sha256':e['head_initial_sha256'],'head_final_sha256':e['head_final_sha256'],'head_tensor_max_abs_changes':check['head_tensor_max_abs_changes'],'model_elapsed_seconds':e['elapsed_seconds']},'freeze':{'state_tensors':len(base['tensors']),'tensor_kinds':kinds,'state_sha256':base['sha256'],'before_equals_after':base==load(A/'encoder-after.json'),'pretrained_file_sha256':plan['pretrained_backbone_sha256'],'optimizer_encoder_intersection':e['optimizer_separation']['optimizer_encoder_intersection'],'forward_batches':len(e['encoder_forward_events']),'all_forward_events_cuda_eval_no_grad':True},'prediction':{'rows':check['prediction_rows'],'valid_rows':91,'test_rows':182,'original_identity_order_and_finite_values_verified':True,'reload_checks':e['reload_checks'],'output_scale':'original numeric Y scale; scaler fit only on internal training 573 rows'},'resource_budget':{'plan':plan['resource_budget'],'actual':rs,'torch_peak_allocated_mib':e['cuda_peak_allocated_bytes']/1024**2,'torch_peak_reserved_mib':e['cuda_peak_reserved_bytes']/1024**2,'allocator_cap_configured_bytes':4096*1024**2,'gpu_cap_limitation':'PyTorch allocator only; not a hard cap on CUDA context or other libraries','cpu_affinity':[0,1],'torch_threads':2,'dataloader_workers':0,'ram_enforcement':'sampled process-tree RSS guard, not a kernel memory quota','training_wall_watchdog_seconds':900,'result_budget_guard_bytes':1024**3,'dependency_download_bytes':0},'environment':{'readonly_path':plan['existing_environment_readonly'],'packages':len(before['packages']),'python_sha256':before['python_sha256'],'before_after_metadata_equal':supp['environment_metadata_unchanged'],'no_installs':True},'jobs':jobs,'retired_attempt':{'phase':'cuda01','reason':'Foreign GPU process appeared after idle prelaunch; own phase yielded before training; foreign process never signalled','later_waiting':'Read-only observations until GPU3 was healthy and idle again','source_and_logs_preserved':True},'trace_audit':{'files_fetched':len(manifest),'all_fetched_sha256_verified':True,'trace_files':len(audit['traces']),'outside_mutation_evidence':[],'unresolved_count':0,'denied_external_attempts_retained':True,'source_upload_manifest':'raw/upload-manifest.json','audit':'acceptance/audit-final-fetch.json'},'outside_scope_changes':{'successful_task_file_mutation_evidence':[],'special_device_io':'recorded separately','system_kernel_or_ssh_effects':'not_verified; not a whole-server audit'},'process_release':post['own_processes'],'resource_observations':['raw/resources01.stdout','raw/resources02.stdout','raw/queue03.stdout','raw/queue04.stdout','raw/queue05.stdout','raw/final-fetch/raw/cuda02-prelaunch.json','raw/final-fetch/raw/train01-prelaunch.json','acceptance/postcheck.json'],'artifacts_manifest':'artifacts.json','protected_sources_unchanged':protected,'checker_adapter':'operator/checker-adapter.json','limitations':['Same existing execution chat, not a cold-start agent test.','The first CUDA preflight yielded to a foreign process. Completed training used a freshly verified healthy idle GPU; intentional shared training and parallel own jobs were not tested.','Execution self-check does not replace parent independent code/trajectory/source review.','No private valid labels or official scoring/submission.','Landlock/strace do not provide full read, ioctl, hardware partition, or whole-system isolation.']}
save(R/'operator/receipt.json',receipt)
result={'reviewer':'execution_thread_self_validation','independent_parent_acceptance':'pending','checks_passed':True,'training_completed':True,'prediction_completed':True,'freeze_verified':True,'write_scope_verified':True,'own_resources_released':True,'scoring_performed':False,'upload_performed':False,'optimizer_steps':e['optimizer_steps'],'prediction_rows':273,'configuration':e['head_config'],'evidence_check':'operator/evidence-check.json','supplemental_checks':'operator/supplemental-checks.json','checker_adapter':'operator/checker-adapter.json','limitations':receipt['limitations']}
save(R/'acceptance/result.json',result)
status=load(R/'status.json');status.update({'phase':'execution_complete_pending_parent_acceptance','run_id':plan['run_id'],'observed_at':now,**{k:result[k] for k in ['training_completed','prediction_completed','freeze_verified','write_scope_verified','own_resources_released','scoring_performed','upload_performed']},'epochs_run':e['epochs_run'],'optimizer_steps':e['optimizer_steps'],'prediction_rows':273,'independent_parent_acceptance':'pending','report':'acceptance/report.md','checkpoint':'artifacts/caco2_wang-head.pt'});save(R/'status.json',status)
rows=[]
for j in jobs:rows.append(f"| {j['job_id']} | {cn(j['at']).split()[1]} | {j['exit']['exit_code']} | {j['exit']['elapsed_seconds']:.2f}s | {j['exit']['reason'] or '完成'} |")
report=f'''本轮 Caco2 训练完成，执行会话自检通过，主控独立验收待进行。实际配置为 **CheMeleon 冻结底座 + 256 单元预测头，lr=0.0005，seed=43**；其余参数与原 PLAN 一致。共训练 **{e['epochs_run']} epoch、{e['optimizer_steps']} 个优化步**，最佳内部早停 epoch 为 {e['best_epoch_1_based']}。产出 91 行 valid 和 182 行 test 的完整预测。未做私有 valid 评分或赛事上传。

主要产物：{link('artifacts/caco2_wang-head.pt','新头 checkpoint')}、{link('artifacts/predictions.csv','273 行预测')}、{link('artifacts/training-evidence.json','完整训练证据')}。复现代码、预处理统计、573/64 原始 train 行划分、特征和解析掩码随本 run 留存。

65 个取回文件逐项 SHA256 核对通过。CheMeleon 内存状态的 {len(base['tensors'])} 个张量（{kinds['parameter']} 个参数、{kinds['buffer']} 个 buffer）前后摘要相等，完整状态摘要为 `{base['sha256']}`；原始 checkpoint 摘要不变。运行断言覆盖 eval、requires_grad=False、无梯度 CUDA 编码和优化器排除底座。四个新头张量均发生有限非零变化，梯度非零步数与 {e['optimizer_steps']} 优化步一致。除模型自报外，还直接比较 checkpoint ZIP 的原始张量存储，确认 256 单元形状、524801 个参数和四项真实变化，宿主不反序列化 pickle 或执行返回模型。

仅使用官方 train 的 637 行，按 seed=43 划为 573 行拟合、64 行内部早停；标准化统计只在 573 行拟合。valid/test 输入不含 Y。预测逐行核对 task/split/row_index/Drug_ID/Drug，全部行序、空或重复 ID 语义及 SMILES 保留，273 个预测均有限。模型重新加载后的最大绝对预测差为 {max(v['max_abs_prediction_difference'] for v in e['reload_checks'].values()):.10g}，预测已还原原 Y 数值尺度。

执行绑定 GPU 3 / `{receipt['target']['gpu_uuid']}`，实际训练 PID 为 1527655，运行中 nvidia-smi 将该 PID 映射到同一 UUID。GPU 4/7 的恢复状态为 Reset，已排除。以下时间均为 2026-10-31 北京时间：

| 阶段 | 开始 | 退出码 | 阶段耗时 | 结果 |
| --- | --- | --- | --- | --- |
{chr(10).join(rows)}

首次预检期间其他 GPU 作业在预检的空闲快照之后出现，监控主动终止了本次自有预检；未控制该外部 PID。随后该卡被约 30–40GiB、100% 利用率的活动作业占用，本会话只读等待至健康空闲。旧尝试的源码、启动快照、日志、轨迹、退出状态均保留；第二次 CUDA 矩阵和完整依赖导入预检通过后才启动正式训练。CUDA 预检不是训练步，也没有将合成计算冒充学习。

本轮只读复用既有私有 venv，无安装或依赖下载。解释器和 78 项包元数据与已验收环境一致，本轮前后摘要也一致。一次环境元数据读取发生 SSH 认证失败，后续同一固定路由读取成功；没有修改凭据、网络或 SSH 设置。bootstrap 的实际输入和代码清单可核对 {link('raw/upload-manifest-initial.json','初始上传')} 与 {link('raw/upload-retry02-manifest.json','第二预检新增源码')}。

三份 strace 共覆盖退让预检、成功预检和正式训练，审读未发现成功的目录外项目文件改动，未解析写入为 0；设备节点单列，驱动被拒绝的设备链接尝试保留。任务写入根为 `{plan['remote_directory']}`，Landlock 从完整库导入前启用，joblib 不需要的多进程探测在导入前禁用。私有环境只读使用。它们不是读隔离、GPU 分区、IOCTL 隔离或全机审计，SSH/内核及无关进程的影响仍为未验证项。

正式训练整卡采样峰值 {rs['train01']['whole_gpu_sample_peak_mib']}MiB，自有 PID 采样峰值 {rs['train01']['own_process_sample_peak_mib']}MiB；torch 分配器峰值 {e['cuda_peak_allocated_bytes']/1024**2:.2f}MiB、保留峰值 {e['cuda_peak_reserved_bytes']/1024**2:.0f}MiB。4GiB 限制覆盖 torch 分配器，不是全设备硬限额。CPU 亲和 `[0,1]`，库线程 2，数据加载 worker 0；正式阶段进程树 RSS 采样峰值 {rs['train01']['exit']['peak_observed_tree_rss_bytes']/1024**3:.3f}GiB，8GiB 采样监护不是内核内存配额；900 秒自有作业监护及 1GiB 结果预算未触发。模型本体约 {e['elapsed_seconds']:.2f} 秒，含导入、预启动与轨迹的正式阶段约 {rs['train01']['exit']['elapsed_seconds']:.2f} 秒。

最终核对 9 个登记 PID/启动时间身份均已退出，GPU 3 回到 0MiB 且 Recovery Action=None。PLAN、两项 Skill 及项目规则摘要保持不变，{link('acceptance/postcheck.json','原始释放/身份复核')}和 {link('acceptance/audit-final-fetch.json','逐轨迹审查')}可复查。

{link('operator/evidence-check.json','只读证据检查')}使用原 Skill 检查器的本 run 适配版：PLAN 把选卡交给操作者，GPU 字段据实际 config 读取；成功预检阶段为 cuda02，同时要求三份轨迹全部审查。冻结、张量变化、行身份、退出和释放条件未降低，原 Skill、PLAN 及主控 criteria 均未改。适配差异和原版摘要在 {link('operator/checker-adapter.json','检查器说明')}；独立形状/学习率/seed/环境复核在 {link('operator/supplemental-checks.json','补充检查')}。本报告由执行会话给出，不能替代主控对原始代码和轨迹的独立结论。

本轮是同一已有聊天中的新固定配置训练，不是冷启动测试；保留了历史上下文。没有参数搜索、额外任务或委派。刻意共享、并行训练、其他任务/模型、环境新安装及真实 valid 评分均不据此宣称通过。全局项目工作记录和 Skill 索引归主控维护，本会话只写本 run。
'''
(R/'operator/report.md').write_text(report);(R/'acceptance/report.md').write_text(report)
p=R/'CONTINUE.md';p.write_text(p.read_text()+f'\n\n执行会话更新（{cn(now)} 北京时间）：训练及执行自检完成，19 epoch/95步，256头/lr0.0005/seed43，273行预测，11项底座状态不变、4个新头张量改变，9个登记进程退出。首次预检因外部GPU占用主动退让，等待健康空闲后完成；原件保留。无私有valid评分或上传。入口：acceptance/report.md、operator/receipt.json、status.json。主控独立验收待进行。\n')
files=[R/'PLAN.json',R/'status.json',R/'CONTINUE.md',R/'artifacts.json',R/'acceptance/report.md',R/'acceptance/result.json',R/'operator/receipt.json',R/'operator/evidence-check.json',R/'operator/supplemental-checks.json',R/'operator/checker-adapter.json']
files+=list((R/'artifacts').iterdir())
save(R/'delivery-manifest.json',{'observed_at':now,'fetched_manifest':'raw/final-fetch/fetch-manifest.json','fetched_files_sha256_verified':65,'files':[{'path':str(p.relative_to(R)),'sha256':sha(p),'size':p.stat().st_size} for p in files if p.is_file()]})
print(json.dumps({'training_completed':True,'review':'operator_self_check_pass_parent_pending','epochs':e['epochs_run'],'steps':e['optimizer_steps'],'predictions':273,'report':str(R/'acceptance/report.md'),'checkpoint':str(R/'artifacts/caco2_wang-head.pt')},ensure_ascii=False,indent=2))
