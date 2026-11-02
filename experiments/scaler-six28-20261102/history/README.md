# 完整渐进历史

本索引包含35条历史记录和前轮2156项来源处置。历史失败和未执行计划保持原状态，不能因新成功而覆盖。

[机器登记](registry.json)；[前轮逐来源固定版本引用](prior-source-index.json)。

## baseline-22

Mini CPU冻结CheMeleon，22个任务各1头；v1/v2失败和v3复用缓存；22任务本地评分已完成，非海南。

状态：`accepted_with_quality_limits`。

- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/DELIVERY.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-74987a34c418c461.md.txt)
- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/runs/chemeleon-host-v3-20261030/result/model/metrics.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-8e8fd665eb04a9ef.json)
- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/runs/chemeleon-host-v3-20261030/prediction-range-review.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-616fd441ee2c48b2.json)
- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/runs/chemeleon-host-v3-20261030/host-artifact-verification.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-55e93c1e00cc10cb.json)

## hainan-skill-pilot-20261030

3次启动均失败，无完成训练；环境写入边界有失败。

状态：`failed_before_learning`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-skill-pilot-20261030/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-0132238ba7887d1c.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-skill-pilot-20261030/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-6fb5e5300524b060.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-skill-pilot-20261030/acceptance/report.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-d0ba96ef1bbbbae2.md.txt)

## hainan-frozen-training-20261031

首个主控修复后海南Caco2冻结训练；14epoch/70更新。

状态：`accepted_with_scope_limits`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-frozen-training-20261031/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-7383e960a5037d93.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-frozen-training-20261031/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-a875c49c4ef3f7da.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-frozen-training-20261031/acceptance/report.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-2e8f80a254694f54.md.txt)

## hainan-skill-follow-20261031

原Thread续聊，256头/lr0.0005/seed43；19epoch/95更新；前置失败后继续执行不合格。

状态：`science_pass_skill_follow_partial`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-skill-follow-20261031/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-d76e1996855c0b80.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-skill-follow-20261031/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-864582993a195702.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-skill-follow-20261031/acceptance/report.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-baecc4380e5873f5.md.txt)

## hainan-index-cycle-20261031

分组train内573/64；26epoch/130更新；旧run状态落后于周期验收。

状态：`accepted_cycle_completed`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-index-cycle-20261031/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/dcf4b21ad83f105942f58f7758a558540a4453ce3a1d203b3e9bd93877794021.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-index-cycle-20261031/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-4237568961ecd76c.json)
- [workspace/adhoc_jobs/admet_training/cycles/progressive-index-e2e-20261031/acceptance/training-final/report.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-a5746884ce9e7b35.md.txt)

## hainan-mae-monitor-20261101

15epoch/75更新；科学worker0/监督125；已评分及Pro回包，研究指南未全部可执行。

状态：`science_accepted_supervisor_failed`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-mae-monitor-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-5eee7cf4e075c648.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-mae-monitor-20261101/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-b4b42aa65ca5b485.json)
- [workspace/adhoc_jobs/admet_training/cycles/monitor-mae-e2e-20261101/acceptance/training-final/RUN_ACCEPTED.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-cc299dd2030e31cb.json)

## prep-glm-deepseek-original

四会话同prompt；GLM输出预算8192耗尽未交付；DeepSeek交付但模型路越权本机训练，数据评分合同不严。

状态：`both_with_defects`。

- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/acceptance/report.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-4b6bd3e314134152.md.txt)
- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/acceptance/session-summary.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-0dddbd87493c1036.json)
- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/comparison-setup.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-a3a0fa41584b691f.json)

## prep-glm-expanded-budget

保留旧历史，500k/100k预算重跑；与冷启动或旧预算不可作普遍模型排名。

状态：`completed_not_fully_accepted`。

- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/glm-rerun-500k-100k-20261030/acceptance/report.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-86a0d99651bb1fb3.md.txt)
- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/glm-rerun-500k-100k-20261030/acceptance/session-summary.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-b4d4e69d5f0b4671.json)

## prep-deepseek-coldstart

两个全新上下文；真实接口/缓存/严格评分缺陷；无训练。

状态：`both_failed_overall`。

- [workspace/adhoc_jobs/admet_deepseek_skill_coldstart_20261030/acceptance/report.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-63b9fa1c59efe431.md.txt)
- [workspace/adhoc_jobs/admet_deepseek_skill_coldstart_20261030/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-b06f87750c8c4027.json)

## prep-qwen-two-assets

MiniMol、MoLFormer各一路；旧状态preparation_running已过时，采用监控终态观察；未验收。

状态：`idle_incomplete_not_training_ready`。

- [workspace/adhoc_jobs/admet_qwen_preparation_20261031/CONTINUE.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-9a31f783d8e81780.md.txt)
- [workspace/contexts/infrastructure/opencode_terra_monitor_20261031/status.json](../evidence/objects/52d81c11c0e7bc06465cd38c8554bab3661e70ffb9fa991e191e911f26556116.json)

## prep-contract-regression

Qwen旧交付真实缺陷转生产反例，离线通过不等于新版模型通过。

状态：`offline_verified_model_behaviour_unverified`。

- [workspace/adhoc_jobs/admet_preparation_skill_v12_20261031/receipt.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-6216509212cabc37.json)

## pro-first

首轮双向传输和研究；历史问题保持原件。

状态：`closed_see_independent_acceptance`。

- [workspace/adhoc_jobs/admet_training/exchange/trials/public-repo-20261031/TRIAL.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-5b5ff1af75e579e1.json)
- [workspace/adhoc_jobs/admet_training/exchange/trials/public-repo-20261031/CONTINUE.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-718ef1a87f3c7002.md.txt)

## pro-index

渐进索引完整周期及下载恢复；存在交接延迟。

状态：`closed_see_independent_acceptance`。

- [workspace/adhoc_jobs/admet_training/cycles/progressive-index-e2e-20261031/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-a0ebe4cf15fbaaef.json)
- [workspace/adhoc_jobs/admet_training/cycles/progressive-index-e2e-20261031/CONTINUE.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-f599cec248e5e668.md.txt)

## pro-mae

最后Pro研究包；运输通过，角色/历史/执行方案合同有缺陷。

状态：`closed_see_independent_acceptance`。

- [workspace/adhoc_jobs/admet_training/cycles/monitor-mae-e2e-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-7ef97806a68c6177.json)
- [workspace/adhoc_jobs/admet_training/cycles/monitor-mae-e2e-20261101/CONTINUE.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-dfd1452361813316.md.txt)
- [workspace/adhoc_jobs/admet_training/audits/end-to-end-20261101/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-762d73df2fec316b.md.txt)
- [workspace/adhoc_jobs/admet_training/audits/end-to-end-20261101/clarifications-20261101.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-561e70aaa098fb10.json)

## research-origin

原调研包与模型候选依据；研究建议不是已准备或授权训练。

状态：`evidence_retained`。

- [workspace/adhoc_jobs/admet_research_intake_20261030/README.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-999813e56be8ac3a.md.txt)
- [workspace/adhoc_jobs/admet_research_intake_20261030/receipt.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-ba59fcd687692080.json)

## cleaning-audit

清洗zip审计；未采用为正式训练版本。

状态：`evidence_retained`。

- [workspace/adhoc_jobs/admet_cleaned_archive_audit_20261030/README.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-c07a76420469b05c.md.txt)
- [workspace/adhoc_jobs/admet_cleaned_archive_audit_20261030/audit.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-4a2d97c8ae60d2aa.json)

## rules-data-origin

旧Harness、规则和数据原始审计；实现约束不能冒充赛事条款。

状态：`evidence_retained`。

- [workspace/adhoc_jobs/admet_harness_startup_review_20261029/review-receipt.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-d12e9a32fee211ed.json)
- [workspace/adhoc_jobs/admet_harness_startup_review_20261029/data-audit/数据完整性与计划调整.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-12c1323fe8daf088.md.txt)

## control-audit

用户意图、授权与控制面逐条复核。

状态：`evidence_retained`。

- [workspace/adhoc_jobs/admet_training/audits/control-plane-20261101/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-94df3978c2d13390.md.txt)

## pipeline-audit

原始工具/产物独立复核与证据措辞更正。

状态：`evidence_retained`。

- [workspace/adhoc_jobs/admet_training/audits/end-to-end-20261101/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-762d73df2fec316b.md.txt)
- [workspace/adhoc_jobs/admet_training/audits/end-to-end-20261101/findings.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-2c65167fbd7d0584.json)
- [workspace/adhoc_jobs/admet_training/audits/end-to-end-20261101/clarifications-20261101.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-561e70aaa098fb10.json)

## issue-decisions

历史问题采纳与否决，不能用新回包覆盖旧账。

状态：`evidence_retained`。

- [workspace/adhoc_jobs/admet_training/exchange/issues/INDEX.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-796ff4a096812eff.json)

## catalog-events

已验证/推翻事件链和旧快照。

状态：`evidence_retained`。

- [workspace/adhoc_jobs/admet_training/exchange/catalog/inputs/20261031-v1.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-e5a566208d4762eb.json)

## evaluation-use

五个已完成学习run的26个任务评分交付；旧失败访问和探索复算总次数未全部记录，不能冒充无valid适应。

状态：`formal_deliveries_reconciled_lifetime_reads_unknown`。

- [workspace/adhoc_jobs/admet_training/control/evaluation-use-ledger.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/evidence/objects/f37f1b0cec261606f46260aa1f2727e475d53a800a4bba77113a5d6c73a8ab59.json)
- [workspace/adhoc_jobs/admet_frozen_baseline_20261030/runs/chemeleon-host-v3-20261030/host-grading-receipt.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-b84a8b80aa1f4648.json)
- [workspace/adhoc_jobs/admet_training/exchange/trials/public-repo-20261031/retrieval/private_scoring/scoring-receipt.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-d7fcc19e4a7653dc.json)
- [workspace/adhoc_jobs/admet_training/cycles/progressive-index-e2e-20261031/retrieval/phase2/private_scoring/scoring-receipt.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-1f9a4db89c969b26.json)
- [workspace/adhoc_jobs/admet_training/cycles/monitor-mae-e2e-20261101/retrieval/private_scoring/scoring-receipt.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/S-a55bb7e3f20b3aba.json)

## contract-follow-e2e-20261101

旧六项窗口已于原截止关闭，完成0/6；首项旧尝试学习步数未知，旧009无部署/启动。不得再因资源通知复活旧请求。

状态：`closed_deadline_expired_science_incomplete`。

- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/CYCLE.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-cb8fd187d71c55e8cad3.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-c5cc9760eea4c9c0482c.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/operator/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-2295bd16747b1b92512c.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/recovery-01/main-fault-acceptance.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-85bdbcd0e46dd96e9c3d.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/recovery-01/TASK.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-f4337c573f702ee02b00.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/deadline-closure-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-9c86263a4a5f17dd9239.json)

## hainan-paired-mse-s44-20261101

本批执行窗口到期，新增完成0/6。首项曾启动但优化步未知；最新009无部署/启动，原件保留。

状态：`closed_deadline_prior_failed_attempt_learning_unverified`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mse-s44-20261101/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-b1d83b2f8c87c7f721c0.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mse-s44-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-817f9c39bfb74dd6f650.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mse-s44-20261101/admission/MAIN_ACCEPTANCE.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-bb578831686178e5fb11.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/deadline-closure-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-9c86263a4a5f17dd9239.json)

## hainan-paired-mae-s44-20261101

本批执行窗口到期，该项未启动；最新009等待资源终止，原件保留。

状态：`closed_deadline_not_started`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mae-s44-20261101/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-ebc5d884889385458284.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mae-s44-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-d8d6bca81bb49ef40cbb.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mae-s44-20261101/admission/MAIN_ACCEPTANCE.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-23b385a92fc6269257b1.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/deadline-closure-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-9c86263a4a5f17dd9239.json)

## hainan-paired-mse-s45-20261101

本批执行窗口到期，该项未启动；最新009等待资源终止，原件保留。

状态：`closed_deadline_not_started`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mse-s45-20261101/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-b52f3d7c4f7f9f98e696.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mse-s45-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-6a437101bc5ea3e665df.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mse-s45-20261101/admission/MAIN_ACCEPTANCE.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-ae1eb4ad7aa6924c26f6.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/deadline-closure-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-9c86263a4a5f17dd9239.json)

## hainan-paired-mae-s45-20261101

本批执行窗口到期，该项未启动；最新009等待资源终止，原件保留。

状态：`closed_deadline_not_started`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mae-s45-20261101/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-0876323196b4be8e888d.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mae-s45-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-5a74c91263f29690014b.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mae-s45-20261101/admission/MAIN_ACCEPTANCE.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-64e3260a567e2bab2cb4.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/deadline-closure-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-9c86263a4a5f17dd9239.json)

## hainan-paired-mse-s46-20261101

本批执行窗口到期，该项未启动；最新009等待资源终止，原件保留。

状态：`closed_deadline_not_started`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mse-s46-20261101/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-6e8a84c5e20653051a80.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mse-s46-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-de833d8edab41cb47c96.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mse-s46-20261101/admission/MAIN_ACCEPTANCE.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-0bd7a24e7c82a28d7d20.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/deadline-closure-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-9c86263a4a5f17dd9239.json)

## hainan-paired-mae-s46-20261101

本批执行窗口到期，该项未启动；最新009等待资源终止，原件保留。

状态：`closed_deadline_not_started`。

- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mae-s46-20261101/PLAN.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-452c89ae88274516ca32.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mae-s46-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-f4444620b96df3fec6d1.json)
- [workspace/adhoc_jobs/admet_training/runs/hainan-paired-mae-s46-20261101/admission/MAIN_ACCEPTANCE.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-78ccb1fa8beb42d9eba7.json)
- [workspace/adhoc_jobs/admet_training/cycles/contract-follow-e2e-20261101/training/deadline-closure-20261101/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-9c86263a4a5f17dd9239.json)

## leaderboard-score-mapping-20261101

主控内置Browser核对前十53.688644/本队46.418；22项归一化及均值推导逐项吻合，理论满分吻合。Valid可本地估算但非官方test预报；仅Caco2提升不足以冲前十。

状态：`official_UI_read_and_inferred_conversion_crosschecked_not_official_formula`。

- [workspace/adhoc_jobs/admet_training/audits/leaderboard-score-mapping-20261101/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-d68e83c8e325d2541cd1.md.txt)
- [workspace/adhoc_jobs/admet_training/audits/leaderboard-score-mapping-20261101/current-official-observation.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-c68dbae0295309d2f4f2.json)
- [workspace/adhoc_jobs/admet_training/audits/leaderboard-score-mapping-20261101/valid-score-estimate.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-32099e3fce4b5fa09189.json)

## training-breadth-strategy-20261101

广度Pro原版与补全已完整收回，主控独立复核接受有局限的研究设计；42proposal/84fit未执行，21任务runner待实现/验收，不构成新增训练授权。

状态：`research_repair_received_main_reviewed_candidate_design_not_training_admitted`。

- [workspace/adhoc_jobs/admet_training/audits/training-breadth-strategy-20261101/RESEARCH_BRIEF.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-cb3fdf80a1564318bc5f.md.txt)
- [workspace/adhoc_jobs/admet_training/audits/training-breadth-strategy-20261101/AUTHORIZATION.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-f4387a22f55f4abcd57b.json)
- [workspace/adhoc_jobs/admet_training/audits/training-breadth-strategy-20261101/SOURCE_ANCHORS.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/history/archive-20261101/originals/N-388093db0a5d304cfde6.json)
- [workspace/adhoc_jobs/admet_training/audits/training-breadth-strategy-20261101/gateway/repair-001/main-review-002/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-d5a45626b5031f31d644.md.txt)

## agent-led-execution-20261101

用户要求结果确定性优于过程确定性；主控重写五项项目Skill及入口/Prompt，删除351文件（227源码、1缓存及配套）；原件留证。未新增训练或恢复旧009；科学与权限边界保持。

状态：`current_workflow_code_deleted_skills_rewritten_runtime_behavior_not_tested`。

- [workspace/adhoc_jobs/admet_training/audits/agent-led-execution-20261101/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-6f5f3cf9d11f9c6bc4e7.md.txt)
- [workspace/adhoc_jobs/admet_training/audits/agent-led-execution-20261101/RESULT.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-fac6ebf211ef923bc9d7.json)
- [workspace/adhoc_jobs/admet_training/audits/agent-led-execution-20261101/DELETION_MANIFEST.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-e4b353d1e582f5b11282.json)
- [workspace/adhoc_jobs/admet_training/audits/agent-led-execution-20261101/DELETION_RECEIPT.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-d5ae5b96a5812f292c7a.json)

## agent-led-resume-20261102

六个Caco2完成学习/评分及主控独立验收，4228文件公开材料与Pro原版/补全收回，主控独立研究验收并实际派下一批六任务24fit。GPU0共享失败、Qwen准备失败与主控CPU代码修订保留，非所有环节无缺陷。32正式任务评分/11完成逻辑run口径未因新派发改变。

状态：`six_runs_scored_published_Pro_repair_returned_main_consumed_next24_dispatched`。

- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/TASK.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-1c7a62b215d94513b377.json)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/CONTINUE.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/2f1d36bbc3af1b726b21de11b04253546a33efd087ae704b8a4c45d1c7cf9100.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/status.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/16ccbf8a197c4882d7fe5586f0acffff7ad9688c7234135e5462cc5420764faa.json)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/dispatch.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/prior-history/evidence/H-b89511969187df7d5c83.json)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/controller/history-intake-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/evidence/objects/479354ef93493936635cfe4d25b9d6144e1c172c44efcdec60a0314519a6f6bc.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/controller/shared-impact-review-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/evidence/objects/1274d6f0d2bdd99d1fe000ce89ce1dcf9b78a3885cc3c81ec9a37455ebba6e48.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/controller/stable-two-intake-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/evidence/objects/70408dfc3db62e1e07559779566333430d1f67001683890baec424ed3fc5eb81.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/retrieval/stable-two-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/prior-history/evidence/objects/0d19da30cd64b67215c821f8ae7d1d9e0830a0154cb295ddaab2addb9b7aff7b.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/controller/gpu1-four-intake-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/evidence/objects/003c6c81b2bb1204c2abc4cce0090449f1a21a4ca27b54228f8487d483a33824.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/controller/remaining-four-intake-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/092d21ddaeb44f305a0628bef15fb6232ea8eb4b/experiments/agent-led-six-20261102/evidence/objects/8295116e4736c8028a119aaaf6e55b04dc1790f89524518ef9a28a02cd6a97b9.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/controller/pro-repair-intake-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/73ce2c690ea24c577692faeeb456897951fe5149f63db22e253d173cab08231b.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/controller/breadth-interface-repair-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/2b62f685382ee91f8fc2fb7bafec8cc1ec8129ce74a8b9d6b3c0ad60d5a32f6e.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/agent-led-resume-20261102/gateway/pro-six-001/repair-001/execution/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/964085c3017247c3c64e8de038ee9ff35b37805b8950aa3ade552d3887ed7c54.md.txt)

## breadth-six24-20261102

24模型/24分数独立验收、966材料发布、Pro完整155文件回收。主控独立来源/算术/配置366检查通过并亲审科学建议，采纳中档28项，实际派发mini根Qwen准备并交原Terra。Pro初始语法失败、网关读取限流/一次页面加载恢复和训练故障保留；初始准备skill错命中旧v1.1单列待验，未把运行中当完成。

状态：`24_scores_published_Pro_recovery_accepted_next28_preparation_dispatched`。

- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/TASK.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/28bbaa3ef0ed880dbe8e434aa1e4af73c8eac0e4148fa9217185d4e1265100cc.json)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/CONTINUE.md](../evidence/objects/75b74aab9ea924d0be5c3e6d0c51c1e9c55103ede83c153d091ff2550990f7b1.md)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/IMPLEMENTATION_NOTES.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/c2f9cc03241690a744794b9195826ad7b74611d3660054d09e55ecbb2fdfebbc.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/dispatch.json](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/b3192de1f5e0fe59fa445770df4a3c72859d83fbc7d624ecf73e941265f4f555.json)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/status.json](../evidence/objects/3c64470916151fbc0416310c1e3f5adc5ca47dd4edd9a2757b72c3a0b3347bad.json)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/controller/resource-fault-intake-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/087195f8aa356f76a139b5dda4173759d90a3a850cbac29f0c2eec3ddebd232d.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/controller/final-training-intake-001/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/a55ba2f68bb442da148059214a85dd549815b25f0f1e38c501067c1eb3b87518.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/operator/REPORT.md](https://raw.githubusercontent.com/ZYDTR/admet-benchmark-data/adcfdd6074157a80d1ed58e9028927c64139f4d6/experiments/breadth-six24-20261102/evidence/objects/c72b65d7927d2577e121793ef0aedf4ebdf4ecb411bcdcb318a842eb0584daf6.md.txt)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/controller/retrieval-score-intake-001/REPORT.md](../evidence/objects/0a46cd72d39f93c41ff531505327203ddbef7a615fd24ea1405a800080fa3c9c.md)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/controller/retrieval-score-intake-001/scores-independent.json](../evidence/objects/89f428cc90a1fb030f0ffe5e738203c0669c3c59d5706f96fe090645c81c7941.json)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/controller/retrieval-score-intake-001/feature-distribution-diagnostic.json](../evidence/objects/bde1e04fae2f77a4ebcb141db8963b2c16854ce5cb27fcecbfe3dfd4dfe8d1d0.json)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/controller/pro-recovery-intake-001/REPORT.md](../evidence/objects/303d73e81bc3524253724e041118b41bccaa39dd59101065836f14a33bccf384.md)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/controller/pro-recovery-intake-001/scientific-independent.json](../evidence/objects/ab0bf716993a432f435510cd5470a8280e385b8897a154b05a7769dd36d2be87.json)
- [workspace/adhoc_jobs/admet_training/cycles/breadth-six24-20261102/controller/pro-recovery-intake-001/gateway-native-terminal.json](../evidence/objects/75a3ad16bc8ce18117fa3023da79e95f1ae4ea9f613d92e3947264cca63c8eaa.json)

## scaler-six28-20261102

28/28固定Valid指标已由主控独立Decimal50/配对AUROC/阈值AP/秩相关复算通过，最大差8.882e-16；26配对与22统计组及六组22任务分制估算核对一致。6标签源6935原行仅主控复核读取，不输出逐行真值/残差，不执行模型或返回代码。累计正式任务评分84，主控独立验证额外计算另列，已完成63逻辑run不变。F010双种子均优于旧H0的任务为lipo、BBB、hep、LD50、Sol；CYP方向不一致。其他16固定原Mini22时，H0均值43.3612、F001 44.5839、F010 45.4314，原Mini22 43.6032；这是推导公式下本地Valid结果，AP定义对应仍未确认，不是hidden test预测，也不是ensemble分数。 原Qwen失败及主控修复保留，完整取回/公开候选正在整理。

状态：`28scores_independently_accepted_full_retrieval_candidate_in_progress`。

- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/CONTINUE.md](../evidence/objects/2c16446ce014f85219e525dd50e28a23d4fd26391737c47d293316d05f4acc58.md)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/status.json](../evidence/objects/b9c8ffb4c8d3bcc8fb0f0b852f5a162abaf6f725bd2a27d69387243705e403d7.json)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/preparation/dispatch.json](../evidence/objects/4c1be6cc650a0a2116c538e03b6f3146503d7ce72b26d335b5bdc5b5d0cd8505.json)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/preparation/packet/TASK.json](../evidence/objects/83fa74c7349f5c233c676da680a9e4a089cd9886b92e783a3c98f04133e3103d.json)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/preparation/packet/SCIENTIFIC_TASK.md](../evidence/objects/cc63041513ffed0fd6f97f03b88b79402e704f7ba2e57e431eddbb68bd9a3697.md)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/controller/training-intake-001/REPORT.md](../evidence/objects/2adf0ca156ad318ac3519814c6d6c8262538b94ba8d502e6a6ae901aa7faae48.md)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/retrieval/batch28-001/RETRIEVAL_TASK.json](../evidence/objects/0f0ca3a5f0002f8daa17e7a8a47a9c9f32860551fd6f88eff8967674dc2a7daa.json)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/retrieval/batch28-001/dispatch.json](../evidence/objects/5387b4a1bd52039b2368958f3186275b164dc5515083664aed5b0a801e880f29.json)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/controller/score-intake-001/DECISION.json](../evidence/objects/2624cd0ad26ef5146e1863b0072d3e7c24d48f8491372ef03706f38855822303.json)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/controller/score-intake-001/scores-independent.json](../evidence/objects/aa6387484b1337e886bd1ded9cdf467b91fb38ae2e63f3e6deb40007ecb84495.json)
- [workspace/adhoc_jobs/admet_training/cycles/scaler-six28-20261102/controller/score-intake-001/comparison-independent.json](../evidence/objects/af6b4f515a0b4d74a236c45dd167539972215deac93f5ba20fd3f6f68bd5ccd3.json)
