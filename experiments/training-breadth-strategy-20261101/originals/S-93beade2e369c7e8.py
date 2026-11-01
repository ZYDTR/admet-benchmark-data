"""Assemble an evidence receipt draft only; never execute packet code or score labels."""
from pathlib import Path
from collections import defaultdict, Counter
from decimal import Decimal, localcontext
import csv
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'agent-reviews/review-json-draft.json'
COMMIT = 'eaec280cf142839597fe75ce748cd2b9a8a897d4'
MANIFEST_SHA = 'dbdec244caa8ddb106721877cf93625c1957b9184985c07b1cf751eed5d70505'
RUNS = {'A': 'hainan-frozen-training-20261031', 'B': 'hainan-skill-follow-20261031'}
manifest = json.loads((ROOT / 'manifest.json').read_text())
issue_ledger = json.loads((ROOT / 'deliverables/issues.json').read_text())
download = json.loads((ROOT / 'download-receipt.json').read_text())
download_by_path = {x['path']: x for x in download}
assert hashlib.sha256((ROOT / 'manifest.json').read_bytes()).hexdigest() == MANIFEST_SHA

route_files = {
 'R': 'root-checks/read-receipt.json',
 'D': 'agent-reviews/rules-data-read-receipt.json',
 'I': 'agent-reviews/implementation-read-receipt.json',
 'S': 'agent-reviews/statistics-read-receipt.json',
 'P': 'agent-reviews/failure-predictions-read-receipt.json',
 'E': 'agent-reviews/representations-read-receipt.json',
 'H': 'agent-reviews/head-search-read-receipt.json',
 'L': 'agent-reviews/repro-records-read-receipt.json',
 'K': 'agent-reviews/independent-skeptic-read-receipt.json'
}
reads = defaultdict(list)
for route, rel in route_files.items():
    j = json.loads((ROOT / rel).read_text())
    if isinstance(j, list):
        entries = j
    else:
        entries = next(j[k] for k in ['files','read_receipt','files_read'] if isinstance(j.get(k),list))
    for e in entries:
        path = e.get('path', e.get('artifact_path'))
        if path:
            reads[path].append((route, str(e.get('coverage', ''))))

critical_dists = {'chemprop-2.2.1','torch-2.6.0','rdkit-2024.9.6','numpy-1.26.4','joblib-1.6.0','pytorch_lightning-2.5.1','scikit_learn-1.6.1'}

def coverage_for(path):
    claims = reads.get(path, [])
    routes = ''.join(sorted({route for route, _ in claims}))
    if path.endswith('.pt') or path.endswith('/preprocessing.npz'):
        return 'U', ''
    if '/features-' in path and path.endswith('.npz'):
        return 'N', routes
    if '/site-packages/' in path:
        dist = Path(path).parent.name.removesuffix('.dist-info')
        if dist not in critical_dists:
            return 'H', ''
        if path.endswith('/METADATA'):
            return 'M', 'L'
        return ('P' if path.endswith('/RECORD') else 'T'), 'L'
    if not claims:
        return 'H', ''
    if path == 'ANALYSIS_BUNDLE.md':
        return 'S', routes
    if path.endswith(('.json', '.jsonl')):
        return 'P', routes
    if path.endswith('.csv'):
        if any(('all' in c.lower() or 'entire' in c.lower()) and ('row' in c.lower() or 'record' in c.lower() or 'content' in c.lower()) for _,c in claims):
            return 'A', routes
        return 'P', routes
    if any((('full' in c.lower() or 'complete' in c.lower() or 'entire' in c.lower()) and not any(x in c.lower() for x in ['not full','no claim full','not claim','selected','targeted','intro/','scoped_read','truncated'])) for _,c in claims):
        return 'T', routes
    return 'S', routes

# One compact, fully expandable per-file inventory; all hashes resolve through fixed manifest.
text_groups = defaultdict(dict)
binary_groups = defaultdict(dict)
env_index = {}
hash_failures = []
text_files = 0
binary_fetched = 0
coverage_counts = Counter()
for entry in manifest['payload_files']:
    rel = entry['path']
    f = ROOT / rel
    code, routes = coverage_for(rel)
    coverage_counts[code] += 1
    if f.suffix in ['.pt', '.npz']:
        present = f.exists()
        sha_ok = None
        if present:
            sha_ok = hashlib.sha256(f.read_bytes()).hexdigest() == entry['sha256'] and f.stat().st_size == entry['bytes']
            binary_fetched += 1
            if not sha_ok: hash_failures.append(rel)
        binary_groups[str(f.parent.relative_to(ROOT))][f.name] = [entry['bytes'],code,routes,present,sha_ok]
        continue
    b = f.read_bytes()
    if hashlib.sha256(b).hexdigest() != entry['sha256'] or len(b) != entry['bytes']:
        hash_failures.append(rel)
    text_files += 1
    lines = len(b.decode('utf-8-sig').splitlines())
    if '/site-packages/' in rel:
        dist = f.parent.name
        env_index.setdefault(dist,{})[f.name] = [lines,code,routes]
    else:
        text_groups[str(f.parent.relative_to(ROOT))][f.name] = [lines,code,routes]
assert text_files == 380 and binary_fetched == 6 and not hash_failures

read_checks = []
data = {}
for split in ['train','valid','test']:
    with (ROOT / 'data' / (split + '.csv')).open(encoding='utf-8-sig',newline='') as f:
        data[split] = list(csv.DictReader(f))
for alias,run_id in RUNS.items():
    base = ROOT / 'runs' / run_id
    with (base / 'artifacts/predictions.csv').open(encoding='utf-8-sig',newline='') as f:
        prediction = list(csv.DictReader(f))
    valid = [r for r in prediction if r['split'] == 'valid']
    with localcontext() as ctx:
        ctx.prec = 60
        mean = sum((Decimal(r['y_pred']) for r in valid),Decimal(0))/Decimal(len(valid))
    assert len(prediction)==273 and len(valid)==91
    seen = set()
    for row in prediction:
        key = (row['task'],row['split'],int(row['row_index']))
        assert key not in seen and key[0]=='caco2_wang'
        seen.add(key)
        original = data[key[1]][key[2]]
        assert row['Drug_ID']==original['Drug_ID'] and row['Drug']==original['Drug']
        assert math.isfinite(float(row['y_pred']))
    assert {key[2] for key in seen if key[1]=='valid'}==set(range(91))
    assert {key[2] for key in seen if key[1]=='test'}==set(range(182))
    evidence = json.loads((base/'artifacts/training-evidence.json').read_text())
    read_checks.append({'run_id':run_id,'all_prediction_rows':len(prediction),'valid_rows':len(valid),
        'mean_valid_prediction':str(mean),'optimizer_steps':evidence['optimizer_steps'],
        'best_epoch_1_based':evidence['best_epoch_1_based'],'epochs_run':evidence['epochs_run'],
        'input_prediction_alignment':{'task_split_row_index_unique':True,'valid_index_range':[0,90],
           'test_index_range':[0,181],'Drug_ID_and_Drug_match_all_rows':True,'finite_predictions':True},
        'evidence_refs':[alias+':artifacts/predictions.csv#all273 records; split=valid91',
                         alias+':artifacts/training-evidence.json#optimizer_steps,best_epoch_1_based,history',
                         'data/valid.csv#all91 records','data/test.csv#all182 records'],
        'method':'Python stdlib csv utf-8-sig; filter split==valid; sum Decimal(y_pred)/91 with precision60. Count steps/best directly from JSON, reconcile full epoch history/log. No model, truth reconstruction or scorer call.',
        'independent_prior_checks':['root-checks/read-checks.json','agent-reviews/independent-skeptic-read-receipt.json']})

reference_dictionary = {k:v for k,v in issue_ledger['reference_dictionary'].items() if k not in ['MINI','MOL','TFM']}

findings = [
 {'finding_id':'trust-current-two-runs','issue_ids':['AR001-11','AR001-16'],
  'judgment':'bounded_pass','statement':'当前公开证据支持真实新头学习、每run编码器8参数/3buffer前后不变、优化器只含新头、官方盲输入预测身份及最佳头重载一致。不是本轮重新执行训练或原始strace审计。',
  'direct_evidence':['FREEZE','CURVE','PRED','IMPL_A','IMPL_B'],
  'countercheck':'跨run wrapper总SHA不同已定位到未参与fingerprint的随机predictor；同一run全state前后相等。历史审计原件/外部checkpoint未公开，仍限制独立验证层级。'},
 {'finding_id':'published-quality-observation','issue_ids':['AR001-02','AR001-12'],
  'judgment':'descriptive_only','statement':'在同一91行已发布fixed MAE上A=0.37862513598901104，B=0.3891885939780218，B-A=0.01056345798901076；较低更好。B的RMSE略低，因此没有跨指标一致优势。',
  'direct_evidence':['SCORE'],
  'countercheck':'宽度/LR/seed/内部划分/拟合变换同时变；64行内部stop仅8行共用，无同配置重复。不能单因果归因、给虚假显著性或称已提高未调参数据泛化。'},
 {'finding_id':'row-and-label-boundary','issue_ids':['AR001-03'],
  'judgment':'verified_identity_with_split_limitation','statement':'保留train637、valid91、test182原行。两份prediction均273行，按task/split/row_index及Drug_ID/Drug全部对齐。每份内部fit573/stop64索引互斥完整，但各有一个raw分子组跨fit/stop。',
  'direct_evidence':['DATA','PRED','SCALE'],
  'countercheck':'内部重复分子不等于官方valid标签泄漏；Drug_ID不唯一不能作唯一键。不得去重、改标签或用真值重评分。'},
 {'finding_id':'feature-scale-priority','issue_ids':['AR001-04','AR001-08'],
  'judgment':'measured_risk_unproven_cause','statement':'已安全解析的特征和fit变换显示内部stop最大|z|约871.665/1637.415。跨run raw特征最大差约3.58e-7，近似相同但bytes身份不同。优先准备同一登记cache下的scale单因子对照。',
  'direct_evidence':['SCALE','FREEZE'],
  'countercheck':'大|z|未与逐行误差关联，也可能是有用稀疏信息；不能声称已证明性能瓶颈。归一化只fit内部train，禁止test拟合。'},
 {'finding_id':'monitor-head-and-config','issue_ids':['AR001-05','AR001-06'],
  'judgment':'implementation_gap_and_testable_hypotheses','statement':'实际优化器是AdamW；A宽度硬编码512、B有固定参数assert，不能直接当通用HPO入口。训练/选epoch都用标准化MSE，官方任务观察指标为原Y MAE。',
  'direct_evidence':['IMPL_A','IMPL_B','CURVE','SCORE'],
  'countercheck':'MSE并非已证错误，先分离monitor、loss、scale改动；修配置不等于质量提升。'},
 {'finding_id':'process-and-records','issue_ids':['F1','AR001-07','AR001-15'],
  'judgment':'open','statement':'F1只做离线门禁修订未真实Follow复测；监督器打印业务失败但未sys.exit(rc)，只看外层返回码存在漏检风险。缺逐batch、同模式fit误差、last/逐epoch头、optimizer moments与RNG状态。',
  'direct_evidence':['F1','EXIT','GAPS','CURVE'],
  'countercheck':'后续正式train成功且产物通过，不能把流程问题自动当当前科学结果无效；上层control原件excluded，未证明其一定只看退出码。'},
 {'finding_id':'error-slice-and-alternative-models','issue_ids':['AR001-09','AR001-10','AR001-13'],
  'judgment':'preparation_only','statement':'预测分布可算，化学错误切片/残差互补未验证；MiniMol/MoLFormer最新状态idle_incomplete，其他候选仅研究。当前只有同一冻结底座两个MLP，无匹配简单/从零/不同表示实测。',
  'direct_evidence':['PRED','SCORE','RESEARCH','ASSETS'],
  'countercheck':'外部paper排名和预测相关不等于本任务性能或残差互补。准备候选不代表取得训练、安装或资产准入授权。'},
 {'finding_id':'incomplete-history-and-provenance','issue_ids':['AR001-01','AR001-14','U01','U02','U03','U04','U05'],
  'judgment':'needs_evidence','statement':'完整历史ledger/既往评分史、官方完整API原文、原始strace、外部权重bytes和训练时完整依赖实现未在包中提供；不足以完成全历史去重、关闭旧问题或独立原始全流程审计。',
  'direct_evidence':['GAPS','RULE','RESEARCH','ASSETS'],
  'countercheck':'现行用户确认冻结许可和本地范围清楚，足以作有限两run分析与条件性准备；不把旧pending发布文字当当前未发布，也不索取私有标签。'}
]

missing = [
 {'evidence_id':'ME-HISTORY','issue_ids':['AR001-01','AR001-12'],
  'missing':'完整实验/失败/问题/否定假设ledger及既往评分使用史。',
  'decision_affected':'全历史去重、继承旧issue ID、噪声估计、确认真正未调参终评。',
  'requested_safe_evidence':'主控提供脱敏索引、状态、控制组/seed/split、排除理由、已有issue映射和评分调用史；不提供私有标签。'},
 {'evidence_id':'ME-RAW-PROVENANCE','issue_ids':['AR001-14'],
  'missing':'完整官方API历史原文、原始strace/若干主控原件、外部权重bytes、训练时完整依赖实现。',
  'decision_affected':'逐字规则、最终资格或独立重建原始完整验收；不自动推翻当前受限证据的两个run。',
  'requested_safe_evidence':'仅由已授权主控提供必要原文/安全衍生件与明确hash映射；本轮不追取服务器或运行原件。'},
 {'evidence_id':'ME-PROCESS','issue_ids':['F1','AR001-15'],
  'missing':'修订门禁真实Follow复测和上层业务返回码处理的公开可核证据。',
  'decision_affected':'是否可关闭F1及业务失败传播问题。',
  'requested_safe_evidence':'先准备状态协议与失败fixture；任何真实复测须另获执行授权。'},
 {'evidence_id':'ME-ASSET-READY','issue_ids':['AR001-10'],
  'missing':'不同冻结底座确切资产/许可/冻结buffer/输入覆盖/成本与完整准备验收。',
  'decision_affected':'候选能否进入执行批次，而非外部论文优劣。',
  'requested_safe_evidence':'补版本固定的asset card、adapter/cache契约及静态验收记录；不自动安装/推理。'},
 {'evidence_id':'ME-ERROR-AGGREGATES','issue_ids':['AR001-09'],
  'missing':'合法的预定义分组误差及配对误差聚合。',
  'decision_affected':'化学失败切片、误差集中、互补性与paired不确定性。',
  'requested_safe_evidence':'若另有授权，由主控在私有区产生允许发布的聚合；不请求原始valid/test标签或逐行残差给本分析/准备agent。'},
 {'evidence_id':'ME-MATCHED-REPEATS','issue_ids':['AR001-02','AR001-12','AR001-13'],
  'missing':'共同划分/共同seed下受控候选和重复结果。',
  'decision_affected':'因果归因、稳定性、最小效果阈值与未调参泛化。',
  'requested_safe_evidence':'本轮仅提案，主控另行批准后采集匹配实验；当前阈值TBD，不假造CI。'}
]

review = {
 'schema_version':'admet.research_review.v2',
 'request_id':'admet-public-repo-pro-20261031-001',
 'round_id':'public-repo-round001', 'packet_version':2,
 'manifest_sha256':MANIFEST_SHA,'fixed_commit':COMMIT,'status':'needs_evidence',
 'status_scope':'有限两run审查和准备方案可交付；全历史ledger/原始验收层级等缺口阻止声称完整全历史审查或确认未调参泛化提升。',
 'authorization':{'budget':'proposal_only','new_training':False,'hpo':False,'model_inference':False,'installation':False,'server_access':False,'rescoring':False,'competition_upload':False,'private_truth_access':False},
 'run_aliases':RUNS,
 'read_receipt':{
   'version_for_all_packet_rows':COMMIT,
   'path_rule':'text_groups/binary_groups: parent + / + filename (parent . means packet root). environment_table: environment_base + / + distribution + / + METADATA|WHEEL|RECORD. Every payload file is expanded exactly once. Hash/byte identity resolves via this fixed manifest.payload_files[path].',
   'row_schema_text':['physical_lines','coverage_code','reviewer_routes'],
   'row_schema_binary':['manifest_bytes','coverage_code','reviewer_routes','locally_present','actual_hash_match'],
   'coverage_codes':{
     'H':'仅下载并核hash/行数；本收据未声称语义阅读。',
     'T':'至少一路完整文本/源码静态阅读或完整跨run比较；未执行源码。',
     'P':'完整结构化记录解析，并检查相关字段/数组；不声称每项元数据均逐句语义研究。',
     'A':'全部CSV数据行解析，覆盖所声明身份/数值检查。',
     'S':'定向部分阅读；具体范围见scope_notes和路线原回执。',
     'M':'METADATA完整bytes核验；头部/Requires-Dist研究，长说明未逐句审。',
     'N':'6个特征NPZ后来实际取得并hash匹配，stdlib ZIP/NPY非对象数值安全解析；未导入模型/pickle/native。',
     'U':'仅manifest及可读结构/预处理衍生件；这6个binary未取回、未加载，不能声称原binary已读。'
   },
   'reviewer_routes':route_files,
   'summary':{'manifest_payload_files':392,'initial_text_files_downloaded_hash_verified':380,'later_feature_npz_downloaded_hash_verified':6,'remaining_binary_not_fetched_or_loaded':6,'read_coverage_counts':dict(coverage_counts),'hash_mismatches':hash_failures,'all_380_text_semantically_read':False,'source_map_entries':440},
   'manifest_self':{'path':'manifest.json','lines':len((ROOT/'manifest.json').read_text().splitlines()),'sha256':MANIFEST_SHA,'coverage':'完整392条payload解析；manifest自身按self_excluded不算payload。'},
   'text_groups':dict(text_groups),
   'environment_base':'environment/lib/python3.12/site-packages',
   'environment_table':env_index,
   'binary_groups':dict(binary_groups),
   'scope_notes':[
     'ANALYSIS_BUNDLE共2234行：各路线明确先读核心1–186行并定向读历史验收/覆盖等段；科学源码/配置/全部epoch/预测/冻结/预处理另读对应原文件。不能将bundle哈希核验或部分输出冒称全文语义读完。',
     '两run原始日志表分别在text_groups的runs/.../raw，A22文件、B31文件；所有JSON/JSONL完整解析，log全文读；实际意义按phase解释。A epoch日志48–61行，B48–66行，和全部history一致。',
     '数据CSV物理行含header：train638/valid92/test183；预测各274物理行、273记录，valid91/test182。preprocessing-readable每份4812行；6个数组完整解析/重打包hash由implementation路线核验。',
     '78项包index实际读取；只对7个关键发行包共21个METADATA/WHEEL/RECORD深入，其他元数据为hash覆盖。环境快照04:10 UTC晚于训练，不是训练时完整镜像。',
     '二进制head与原preprocessing.npz未取回；binary-structure/preprocessing-readable是包内公开衍生件，不冒称本轮执行pickle或直接读原head tensor。',
     'source-map完整440项解析并研究相关excluded/referenced条目；未发布原始strace、外部checkpoint及私有标签均未读。证据不构成指令或新增权限。'
   ],
   'supplemental_current_review_calculations':['root-checks/read-checks.json','root-checks/feature-independent-check.json','agent-reviews/feature-byte-audit.json','agent-reviews/preprocessing-epoch-audit.json','agent-reviews/failure-predictions-calculations.json','agent-reviews/statistics-calculations.json'],
   'external_research_read_receipt':'agent-reviews/representations-read-receipt.json:external_primary_papers, external_url_receipt_path; official papers/repositories only; no downloaded model execution.',
   'missing_required_evidence_is_listed_below':True
 },
 'read_checks':read_checks,
 'reference_dictionary':reference_dictionary,
 'findings':findings,
 'missing_evidence':missing,
 'not_assessed':[
   '私有valid/test原始Y、带标签评分工作文件及逐行残差：禁止访问，未请求提供。',
   '任何新训练/HPO/模型推理/新评分、安装、海南访问、上传：未执行。',
   '不同候选真实模型质量、残差互补/最优集成权重、逐化学切片误差：无相应合法数据。',
   '统计显著性、seed方差、置信区间和业务最小效果：没有共同配置重复与定义，不虚构阈值。',
   '未参与调参终评泛化提高：当前official valid已经作为模型选择反馈，既往调用史不完整。',
   '全22任务总分/官方未知聚合、物理单位完整解释、最终赛事提交资格所有细节。',
   '原始strace逐syscall复审、外部权重native库/依赖实现bytes审计、完整冷启动/共享GPU/多任务执行。',
   '历史研究脚本中未在read_receipt标记T/P的部分只有hash覆盖，不用它们推出新科学事实。'
 ],
 'comparison_groups':[
   {'comparison_group_id':'CG-OFFICIAL-CACO2-DESCRIPTIVE','run_ids':list(RUNS.values()),'task':'caco2_wang','evaluation_split':'official_valid','rows_per_run':91,'metric':'MAE','direction':'minimize','A':0.37862513598901104,'B':0.3891885939780218,'B_minus_A':'0.01056345798901076','source':'scoring/scores.json and independent-controller-check.json; no rescoring','same':['official input rows','encoder checkpoint','fixed metric'], 'confounded':['head width512/256','lr0.001/0.0005','seed42/43','internal split and fitted transform','initialization/shuffle RNG'], 'matched_stop_rows':8,'comparison_type':'descriptive_not_causal','uncertainty':'没有同配置seed重复、paired逐行误差或独立终评；minimum_effect和CI不定。'},
   {'comparison_group_id':'CG-MATCHED-CAUSAL','run_ids':[],'status':'not_available','reason':'没有同任务/划分/seed及其余配置相同的单因子候选对照；建议实验未获执行授权。'},
   {'comparison_group_id':'CG-FAILURE-EVIDENCE','run_ids':[RUNS['B']],'phase':'cuda01','include_in_model_quality_ranking':False,'reason':'外部进程出现后预检退让，无模型训练完成；cuda02与正式train01分开核对。'},
   {'comparison_group_id':'CG-OTHER-TASKS-OR-ENCODERS','run_ids':[],'status':'not_measured','reason':'当前包只含Caco2两次CheMeleon冻结MLP；不同底座和总分不做实测排名。'}
 ],
 'stop_reasons':[
   {'scope':'execution','reason':'proposal_only没有新增训练/HPO/推理/安装/服务器或上传授权；所有候选仍为建议。'},
   {'scope':'evidence_boundary','reason':'不补取或重建valid/test真值，不重评分；无残差不作已验证错误切片。'},
   {'scope':'historical_completion','reason':'全历史ledger/issue映射/评分史缺失，status保持needs_evidence；有限两run分析与准备仍继续。'},
   {'scope':'quality_claims','reason':'没有匹配重复或未调参终评证据，停止单因果、显著性和真正泛化提高的断言。'},
   {'scope':'run_admissibility','reason':'冻结/文件资源边界/输入身份失败的实验只能作故障证据；当前未观察到正式两run在这些项目失败，follow失败预检已排除。'}
 ]
}
# Compact JSON is intentional: all file rows are present, and UTF-8 gateway budget is bounded.
OUT.write_text(json.dumps(review, ensure_ascii=False, separators=(',',':'))+'\n')
print(json.dumps({'output':str(OUT),'utf8_bytes':OUT.stat().st_size,'payload_files':392,'text_files':text_files,'coverage_counts':dict(coverage_counts),'means':[r['mean_valid_prediction'] for r in read_checks]},ensure_ascii=False))
assert OUT.stat().st_size <= 35000, OUT.stat().st_size
