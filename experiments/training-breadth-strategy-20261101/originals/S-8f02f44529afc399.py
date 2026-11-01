"""Write final honest failure delivery. Reads only this run and its registered rule identities."""
from pathlib import Path
import datetime,hashlib,json,shutil
RUN=Path(__file__).resolve().parents[1];FETCH=RUN/'raw/final-fetch';Z=datetime.timezone(datetime.timedelta(hours=8))
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def localtime(t):return datetime.datetime.fromisoformat(t).astimezone(Z).strftime('%Y-%m-%d %H:%M:%S')
def link(rel,label=None):return f'[{label or rel}]({RUN/rel})'
plan=load(RUN/'PLAN.json');inventory=load(RUN/'raw/inventory-final.stdout');gpu=load(RUN/'raw/gpu-final.stdout');release=load(RUN/'raw/release-final.stdout');audits=load(RUN/'operator/final-write-audit.json');manifest=load(FETCH/'fetch-manifest.json')
assert release['all_recorded_processes_terminated'] and release['recorded_pids_on_any_gpu']==[]
assert not inventory['tree_identity_violations'] and 'GPU Recovery Action                   : Reset' in gpu['selected_gpu_details']['stdout']
assert not (FETCH/'raw/train-runtime.json').exists() and not (FETCH/'raw/train-complete.json').exists()
assert {p.name for p in (FETCH/'artifacts').iterdir()}=={'no_thread_name.so','avoid_thread_name.so'}
for rel,meta in manifest.items():
    p=FETCH/rel;assert p.is_file() and p.stat().st_size==meta['size'] and sha(p)==meta['sha256']
for p in (FETCH/'artifacts').iterdir():
    target=RUN/'artifacts'/p.name
    with target.open('xb') as f:f.write(p.read_bytes())
(RUN/'artifacts/README.md').write_text('本次未完成模型训练。此目录仅保存两份任务局部线程命名兼容性辅助库，不含训练后的模型、新头 checkpoint、特征或预测。辅助库源代码及编译命令见 source/ 和 raw/final-fetch/raw/compile*-exit.json。\n')
source_receipt=load(RUN/'operator/read-receipt.json');protected=[]
for x in source_receipt['sources']:
    if x['path'].endswith(('/PLAN.json','/policy.json','/hainan-compute-access/SKILL.md','/admet_training/AGENTS.md')):
        protected.append({'path':x['path'],'initial_sha256':x['sha256'],'current_sha256':sha(x['path']),'unchanged':sha(x['path'])==x['sha256']})
assert all(x['unchanged'] for x in protected)
asset=next(x for x in inventory['files'] if x['path']=='assets/chemeleon_mp.pt');assert asset['sha256']==plan['pretrained_backbone_sha256']
for x in plan['inputs']:
    rel='input/'+{'train':'train','validation':'valid','test':'test'}[x['role']]+'.csv'
    observed=next(v for v in inventory['files'] if v['path']==rel);assert observed['sha256']==x['sha256']
jobs=[]
phase_reasons={'setup':'Official CDN pip bootstrap timeout','setup02':'Own cancellation to correct dependency file-size cap','setup03':'Operator launch bug: old setup worker selected; immediate assertion failure','setup04':'Own cancellation: sequential mirror route too slow for remaining preparation budget','setup05':'Private environment installed; import generated one out-of-root joblib semaphore','train':'CUDA error 304 at set_device; no encoder/head load','train02':'CUDA error 304 persists; pthread-only naming hook did not cover direct file writes','train03':'CUDA device properties obtained; memory allocator/context setup reports devices busy/unavailable'}
for job in inventory['jobs']:
    phase=job['phase'];exit=job.get('exit',{});launch=load(FETCH/'raw'/f'{phase}-launch.json')
    jobs.append({'job_id':phase,'supervisor_pid':job['supervisor']['pid'],'strace_pid':launch['pid'],'pgid':launch['pgid'],'started_at':launch['started_at'],'completed_at':exit.get('completed_at'),'exit_code':exit.get('exit_code'),'elapsed_seconds':exit.get('elapsed_seconds'),'peak_observed_tree_rss_bytes':exit.get('peak_observed_tree_rss_bytes'),'reason':phase_reasons[phase],'selected_gpu_uuid':plan['remote_directory'] and '<REGISTERED_GPU>' if phase.startswith('train') else None,'all_recorded_processes_terminated':True})
violation=next(x for x in audits if Path(x['trace']).name=='setup05.strace')['successful_outside_file_effects']
assert len(violation)==7
other_effects=[{'trace':Path(x['trace']).name,'effects':x['successful_outside_file_effects']} for x in audits if Path(x['trace']).name!='setup05.strace' and x['successful_outside_file_effects']]
assert not other_effects
peak_gpu_mib=0;own_gpu_samples=[]
for phase in ['train','train02','train03']:
    p=FETCH/'raw'/f'{phase}-observations.jsonl'
    for line in p.open():
        obs=json.loads(line);ids={v['pid'] for v in obs['processes']}
        for row in obs.get('gpu',{}).get('stdout','').splitlines():
            cols=[x.strip() for x in row.split(',')]
            if len(cols)>=4 and cols[1]=='<REGISTERED_GPU>':peak_gpu_mib=max(peak_gpu_mib,int(cols[2]))
        for row in obs.get('apps',{}).get('stdout','').splitlines():
            cols=[x.strip() for x in row.split(',')]
            if len(cols)>=3 and int(cols[1]) in ids:own_gpu_samples.append({'phase':phase,'at':obs['at'],'row':row})
wheel=load(RUN/'source/wheels-linux.lock.json');first=jobs[0]['started_at'];last_start=jobs[-1]['started_at'];last_end=jobs[-1]['completed_at']
setup_wall=(datetime.datetime.fromisoformat(load(FETCH/'raw/setup-complete.json')['completed_at'])-datetime.datetime.fromisoformat(first)).total_seconds()
last_launch_delta=(datetime.datetime.fromisoformat(last_start)-datetime.datetime.fromisoformat(first)).total_seconds()
checks={'registered_route_and_identity':'pass','plan_and_input_identity':'pass','dependency_install_and_import':'pass','gpu_idle_metadata':'observed_but_not_sufficient_for_compute_availability','selected_gpu_health':'fail_final_snapshot_recovery_action_reset','actual_gpu_encoder_execution':'fail_not_reached','actual_head_training':'fail_not_reached','optimizer_steps':0,'runtime_freeze_parameters_and_buffers':'not_verified_model_not_loaded','optimizer_excludes_encoder':'not_verified_optimizer_not_created','head_nonzero_parameter_update':'fail_no_head_created','model_reload_prediction':'not_verified_no_model','prediction_coverage':'fail_no_predictions','strict_write_scope':'fail_joblib_dev_shm_semaphore','post_correction_traced_persistent_file_effects':'pass_for_observed_calls','whole_system_zero_changes':'not_verified','own_process_and_gpu_release':'pass','official_upload':'not_performed','private_validation_labels':'excluded_from_inputs_and_execution','policy_plan_skill_unchanged':'pass','nested_delegation':'not_performed'}
receipt={'schema_version':1,'observed_at':now,'run_id':plan['run_id'],'request':'One real Caco2/CheMeleon frozen encoder plus new head GPU training via updated Hainan Skill','authorization':{'role':'explicitly_authorized_host_operator_leaf','local_write_root':str(RUN),'target_write_root':plan['remote_directory'],'parent_creation_allowed':'project-owner/admet only as necessary','max_concurrent_gpu_jobs':1,'no_official_upload':True,'no_nested_delegation':True},'target':{'hostname':'private-compute','uid':1012,'gid':1012,'address':'<COMPUTE_ADDRESS>:22','route':'Registered Mac -> Windows fixed TCP stream -> private-compute; pinned keys strictly checked','gpu_index':4,'gpu_uuid':'<REGISTERED_GPU>','driver_version':'570.211.01','final_compute_mode':'Default','final_mig_mode':'Disabled','final_gpu_recovery_action':'Reset','gpu_health_observed_at':gpu['at']},'workspace':{'canonical_root':plan['remote_directory'],'tree_identity_violations':inventory['tree_identity_violations'],'symlinks':inventory['links'],'bytes_by_top_directory':inventory['bytes_by_top_directory']},'checks':checks,'outcome':{'status':'failed','training_completed':False,'objective_achieved':False,'completed_model_trainings':0,'cuda_startup_attempts':3,'optimizer_steps':0,'encoder_forward_batches':0,'prediction_rows':0,'trained_checkpoint':None,'stopping_reason':'Repeated CUDA startup/context failure; no further attempts after original 45-minute preparation window; final GPU health reports Reset. Known outside-root setup side effect independently fails scope.'},'changes':{'pretrace_directories_created':[str(Path(plan['remote_directory']).parent),plan['remote_directory'],plan['remote_directory']+'/raw'],'task_tree_manifest':str(RUN/'raw/inventory-final.stdout'),'downloaded_evidence_manifest':str(FETCH/'fetch-manifest.json'),'fetched_files':len(manifest),'all_fetched_sha256_verified':True,'trained_artifacts':[],'helper_binaries':[{'path':str(p.relative_to(RUN)),'sha256':sha(p),'size_bytes':p.stat().st_size} for p in (RUN/'artifacts').glob('*.so')],'protected_source_identities':protected},'resource_budget':{'plan':plan['resource_budget'],'enforced_or_observed':{'cpu_affinity':[0,1],'cpu_thread_library_configuration':2,'dataloader_workers_configured':0,'cuda_visible_devices':'<REGISTERED_GPU>','training_watchdog_seconds':900,'gpu_allocator_cap':'attempted but function failed before enforcement; not_verified','ram_guard':'sampled descendant RSS; own process group termination configured above 8GiB','peak_observed_tree_rss_bytes':max(j['peak_observed_tree_rss_bytes'] for j in jobs),'max_observed_selected_card_memory_mib':peak_gpu_mib,'own_gpu_process_samples':own_gpu_samples,'cuda_allocator_peak':'not_verified_no_successful_model_context','environment_install_wall_seconds_from_first_setup':setup_wall,'last_attempt_start_seconds_from_first_setup':last_launch_delta,'last_attempt_exit_seconds_from_first_setup':(datetime.datetime.fromisoformat(last_end)-datetime.datetime.fromisoformat(first)).total_seconds(),'complete_wheel_bytes':wheel['total_bytes'],'temporary_partial_files_bytes':inventory['bytes_by_top_directory']['tmp'],'network_download_byte_quota':'not_verified; completed wheel total bounded before download, metadata and failed attempts not packet-metered','result_raw_plus_artifact_bytes':inventory['bytes_by_top_directory']['raw']+inventory['bytes_by_top_directory']['artifacts'],'installed_venv_bytes':inventory['bytes_by_top_directory']['venv']}},'resource_observations':{'initial':str(RUN/'raw/inventory.stdout'),'per_job':str(FETCH/'raw'),'final':str(RUN/'raw/inventory-final.stdout'),'gpu_health':str(RUN/'raw/gpu-final.stdout'),'release':str(RUN/'raw/release-final.stdout')},'jobs':jobs,'actual_concurrency':{'max_completed_or_attempted_cuda_jobs_running_together':1,'completed_trainings':0},'outside_scope_changes':{'status':'fail','observed_joblib_semaphore':{'at':'2026-10-30T15:02:44Z approximately; exact ordering in setup05.strace','pid':2187947,'bytes':32,'object_count':1,'paths':['/dev/shm/sem.kK3d5M','/dev/shm/sem.joblib-2187947-jg6d0uzx'],'successful_effects':violation,'dependency_unlinked_both_names':True,'manual_outside_cleanup_performed':False},'other_successful_traced_outside_file_effects':other_effects,'denied_driver_device_link_and_thread_metadata_attempts':'Retained in per-attempt strace; unsuccessful attempts are not reported as completed modifications.','ssh_server_kernel_unrelated_system_effects':'not_verified; not instrumented and not claimed zero'},'release':{'recorded_identities':release['recorded_identities'],'all_recorded_processes_terminated':release['all_recorded_processes_terminated'],'recorded_pids_on_any_gpu':release['recorded_pids_on_any_gpu'],'verified_at':release['at']},'limitations':['No real encoder forward pass or optimizer update occurred. On-disk checkpoint identity is not in-memory freeze verification.','Landlock and optional thread naming hooks were operator-added run-local experiments, not Skill requirements. CUDA failures under this path do not establish that all Hainan GPUs or the Skill connection are unusable.','Initial GPU selection missed hardware recovery state. Reset was only queried at final read-only audit; it is not proven to have been present at initial selection or caused by this task.','Filesystem traces cover selected task descendants/syscalls, not a complete system audit.','No device reset, global environment repair, colleague process termination, official upload, HPO, private valid labels, policy/Skill/PLAN modification, or nested agent/thread/CLI model operation was performed.'],'independent_acceptance':'Pending parent inspection; operator outcome is FAIL, not a pass claim.'}
save(RUN/'operator/receipt.json',receipt)
save(RUN/'operator/status.json',{'schema_version':1,'run_id':plan['run_id'],'observed_at':now,'stage':'failed_closed','status':'failed','training_completed':False,'objective_achieved':False,'completed_model_trainings':0,'cuda_startup_attempts':3,'optimizer_steps':0,'strict_write_scope':'failed_setup05_semaphore','selected_gpu_final_health':'GPU Recovery Action: Reset','all_recorded_processes_terminated':True,'recorded_process_identities':release['recorded_identities'],'evidence_files_verified':len(manifest),'independent_acceptance':'pending_parent','report':str(RUN/'operator/report.md'),'receipt':str(RUN/'operator/receipt.json')})
save(RUN/'operator/artifact-validation.json',{'status':'not_run','reason':'No model, feature cache, head checkpoint, or prediction file was produced; training stopped before encoder load.','optimizer_steps':0,'prediction_rows':0,'helper_binaries_only':True})
rows=[]
for j in jobs:
    rows.append(f"| {j['job_id']} | {localtime(j['started_at']).split()[1]} | {j['exit_code']} | {j['elapsed_seconds']:.1f}s | {j['reason']} |")
report=f'''本次单作业试验未完成真实训练，操作者结论为 **FAIL**。三次执行尝试均在 CUDA 启动或上下文准备阶段退出，编码器尚未加载，优化器步数为 0，未产出新头 checkpoint、特征或 273 行预测。另有一次已经证实的目录边界违规：准备阶段 joblib 在 `/dev/shm` 创建了一个 32 字节临时信号量，依赖随后自行删除。成功导入和连接不能替代训练与边界验收。

最终只读设备快照在 {localtime(gpu['at'])}（北京时间）显示 GPU 4 的 `GPU Recovery Action: Reset`，显存和利用率仍为 0，Compute Mode 为 Default，MIG Disabled。初选只核对了多时点空闲/进程指标，漏查恢复状态，这是操作者选卡检查不足。该状态与 CUDA 上下文失败相符，但未做恢复或对照，不能证明首查时已存在，也不能把其因果归于本任务。没有执行 GPU reset。

机器身份 `private-compute / private-compute / UID:GID 1012:1012` 与固定 Windows 通道及双层主机密钥一致。三份固定 CSV（637/91/182 行）和 CheMeleon 权重在本机计划检查、上传接收及最终文件清单中摘要一致。77 个固定 wheel 共 {wheel['total_bytes']:,} 字节，逐个与官方 PyPI 摘要核对后离线安装；`pip check` 和库导入通过。环境、缓存、代码和输入保留在 `{plan['remote_directory']}`。

以下开始时间均为 2026-10-30 北京时间。CUDA 三次尝试合计也未进入模型训练，不是三次超参试验。

| 尝试 | 开始 | 退出码 | 子阶段耗时 | 实际结果 |
| --- | --- | --- | --- | --- |
{chr(10).join(rows)}

准备过程还包含可避免的实现错误：450MiB 单文件限额小于 PyTorch wheel；一次启动器引用了旧 worker。均保留原代码、退出状态和独立编号。其后采用固定锁定清单、较快镜像和 4 路网络 I/O，CPU 亲和保持两核。完整安装从首次 setup 起约 {setup_wall/60:.1f} 分钟；末次执行开始于首次 setup 后 {last_launch_delta/60:.1f} 分钟。45 分钟准备窗口结束后只做取证与释放核验，没有新增计算。

写入审计覆盖 20 份 strace，解析结果见 {link('operator/final-write-audit.json','最终写入审计')}。setup05 中的一个 POSIX 信号量使用临时名及链接名，记录了 7 次成功文件效果（含 32 字节写入、映射、链接和 unlink），两名最终均由依赖自身 unlink。它虽未留下文件，仍违反 Skill 明示的 `/dev/shm` 边界。未为修复而操作任何目录外文件。其他已追踪阶段未观察到成功的目录外普通文件改动，设备节点单独统计；驱动对 `/dev/char` 链接的改动请求被拒绝，保留原始失败记录。

修正后的 `JOBLIB_MULTIPROCESSING=0` 完整导入复验未出现目录外写入。Landlock ABI 4 和两版局部线程命名辅助库是本操作者额外选择的任务内实现，**不是 Skill 规定的前置条件**。首次辅助库未覆盖驱动直接文件接口；下一版将本进程可选线程名写入重定向至 `/dev/null`，末次失败点从 `cuda.set_device` 推进至 `set_per_process_memory_fraction` 的设备忙/不可用。没有放宽 Landlock 文件规则或修系统设备。这些实验不能证明普通宿主执行也必然失败，亦不能把未成功的 CUDA 路径说成模型接入通过。Landlock 4 不提供完整读隔离或所有元数据/设备 ioctl 限制；strace 也不是全系统零变更证明。[Linux 官方接口说明](https://docs.kernel.org/userspace-api/landlock.html) 与本次 {link('raw/guard-support.stdout','目标 UAPI/joblib 实读源码')} 支持这里的实现判断；[joblib 官方源码](https://raw.githubusercontent.com/joblib/joblib/main/joblib/_multiprocessing_helpers.py)说明该导入探测的环境开关。

| 资源项 | PLAN 目标 | 实际及限制 |
| --- | --- | --- |
| 并发/GPU | 1 作业、1 GPU | 最大并发 1；三次启动尝试均串行，0 个训练完成 |
| CPU | 2 线程 | 两核亲和 `[0,1]` 实际设置；库线程配置 2，驱动线程数可多于 2 |
| GPU 显存 | 4096MiB | 分配器限额设置时失败，未证明限额生效；所选卡采样峰值 {peak_gpu_mib}MiB，不能当模型训练峰值 |
| RAM | 8GiB | 进程树采样峰值 {max(j['peak_observed_tree_rss_bytes'] for j in jobs)/1024**3:.3f}GiB；采样监测，不是内核内存配额 |
| 时长 | 准备 45min、训练 900s | 末次启动在准备窗口内；各 CUDA 尝试约 18–21s 退出；900s 自有进程组监护未触发 |
| 依赖下载 | 8GiB | 完整 wheel 约 {wheel['total_bytes']/1024**3:.3f}GiB；保留临时残片约 {inventory['bytes_by_top_directory']['tmp']/1024**2:.1f}MiB；网络总流量未逐包计量 |
| 结果 | 1GiB | 远端 raw+artifacts 约 {(inventory['bytes_by_top_directory']['raw']+inventory['bytes_by_top_directory']['artifacts'])/1024**2:.1f}MiB；venv 另为 {inventory['bytes_by_top_directory']['venv']/1024**3:.2f}GiB，属于环境而非模型结果 |

冻结验收中的 `eval/requires_grad/no_grad`、优化器参数身份隔离、内存参数与 buffer 前后摘要、新头非零更新、重新加载预测和行覆盖，全部 **未完成运行验证**。固定权重文件 SHA256 不变仅证明文件身份，不能替代上述检查。{link('source/train_remote_v3.py','训练代码')} 中准备了这些检查，但代码存在不构成执行证据。{link('operator/artifact-validation.json','产物状态')} 明确记为未运行；`artifacts/` 只有辅助 `.so`，没有训练模型。

最终任务树未发现指向外部的链接、硬链接普通文件或特殊文件。{release['recorded_identities']} 个已记录 PID/启动时间身份均确认结束，没有记录中的 PID 出现在任何 GPU 计算进程中。没有中止他人进程、修改系统或赛事上传。系统/SSH 自身审计及未观测的目录外影响记为 `not_verified`，未全盘扫描同事目录。PLAN、policy、项目 AGENTS 与海南 Skill 摘要仍与首次读取相同。

交付入口为 {link('operator/receipt.json','结构化回执')}、{link('operator/status.json','终态')}、{link('raw/final-fetch/fetch-manifest.json','143 文件下载清单')} 和 {link('raw/release-final.stdout','释放核验')}。全部取回文件逐字节 SHA256 核对通过；{link('raw/commands.jsonl','实际操作时间线')}、{link('raw/final-fetch/raw/train03-launch.json','末次实际命令')}、{link('raw/final-fetch/raw/train03.log','末次完整错误')} 与 {link('raw/gpu-final.stdout','硬件原始快照')}可直接复核。模型、依赖和原始输入清单均在回执指向的源文件中。

需要主控追加处理的是：先核实可用 GPU 的健康/恢复状态及此执行路径的 CUDA 兼容性，再决定是否另开预算重试同一固定配置。此 leaf 不修改 Skill/政策/验收标准，不替主控宣布通过，也未启动并行训练。
'''
(RUN/'operator/report.md').write_text(report)
# Seal the primary local delivery without recursive self-reference.
files=[RUN/'operator'/n for n in ['report.md','receipt.json','status.json','read-receipt.json','final-write-audit.json','fetch-receipt.json','artifact-validation.json']]
save(RUN/'operator/delivery-manifest.json',{'observed_at':now,'files':[{'path':str(p),'sha256':sha(p),'size_bytes':p.stat().st_size} for p in files],'fetched_evidence_files':len(manifest),'fetched_evidence_sha256_all_verified':True})
print(json.dumps({'status':'failed_closed','training_completed':False,'optimizer_steps':0,'report':str(RUN/'operator/report.md'),'receipt':str(RUN/'operator/receipt.json'),'status_file':str(RUN/'operator/status.json'),'evidence_files_verified':len(manifest),'all_recorded_processes_terminated':True,'gpu_recovery_action':'Reset'},ensure_ascii=False,indent=2))
