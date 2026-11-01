# 广度研究：完整补全与主控复核

主控接受补全版为有明确限制的策略与准备设计。它尚非21任务已实现runner，也未授权执行84次训练。原版缺陷、补全和主控限制均分别保留。

## 主控裁决与原版

- [原版研究主控拒绝/限制](../../evidence/H-04ce3a510ed1cbcc6c71.md.txt)
- [补全版主控全文复核](../../evidence/H-d5a45626b5031f31d644.md.txt)
- [研究复核收口决定](../../evidence/H-0a9e0e02482a244361cf.json)
- [主控独立算术与设计核对](../../evidence/H-1ec797a5e2e412dc5a57.json)

## 完整正式文件与附加材料

- [SOURCE_ACCESS.md](../../evidence/H-edbdf69a004e69595c8f.md.txt)
- [analysis.md](../../evidence/H-e933132547424eb19522.md.txt)
- [asset-bindings.json](../../evidence/H-98d2405330ccc8c3ad54.json)
- [build_delivery.py](../../evidence/H-63d3a8da5f6a4552c7a3.py.txt)
- [change-log.md](../../evidence/H-21faa8885d1feed28215.md.txt)
- [claim-events.json](../../evidence/H-2c9926d1443ceb2f8517.json)
- [conditional-followups.json](../../evidence/H-d4188fbcbf9e09b9f396.json)
- [delivery-manifest.json](../../evidence/H-064ad6a14e164f3af67e.json)
- [evidence/additional-reading-coverage.json](../../evidence/H-ca8e43d9480644fb605e.json)
- [evidence/coverage_tools.py](../../evidence/H-89673013cacee0f38deb.py.txt)
- [evidence/numeric-inputs.json](../../evidence/H-8929a0007d78d143ad8f.json)
- [evidence/numeric-recomputation.json](../../evidence/H-c5917e0f8f81c90a05d4.json)
- [evidence/previous-version-hashes.json](../../evidence/H-68455c5483e24a7e1a90.json)
- [evidence/read-receipts.json](../../evidence/H-b96e15987cf51ba699ca.json)
- [evidence/reading-contract-transcription.json](../../evidence/H-9da908d51b9497ee5b49.json)
- [evidence/reading-coverage.json](../../evidence/H-61b3c2a8f2383c2af6bc.json)
- [evidence/recompute.py](../../evidence/H-aa877844c71cc5810d46.py.txt)
- [evidence/source-index.json](../../evidence/H-1fcd251e5c052960186b.json)
- [evidence/tool-use.json](../../evidence/H-4fa1a64b2fb03707a109.json)
- [evidence/update_coverage_pass2.py](../../evidence/H-309b06d43e2f803f292b.py.txt)
- [evidence/update_coverage_pass3.py](../../evidence/H-fff30b4c97b0d14ac55a.py.txt)
- [evidence/update_manifest_coverage.py](../../evidence/H-92236e6f7ae154af5f02.py.txt)
- [evidence/update_manifest_final.py](../../evidence/H-8017d09d95c54a732a2d.py.txt)
- [evidence/update_manifest_pass2.py](../../evidence/H-5910da340e7556d053fe.py.txt)
- [evidence/update_manifest_pass3.py](../../evidence/H-aad9b37ea46eb98cdd0e.py.txt)
- [evidence/validate_delivery.py](../../evidence/H-d095a5625ea822184355.py.txt)
- [evidence/validation-report.json](../../evidence/H-0a2d9a51085d993d8117.json)
- [experiment-matrix.csv](../../evidence/H-84cc35afe8118a37e10b.csv)
- [experiment-matrix.json](../../evidence/H-2cdcdf014e443ab866c8.json)
- [issues.json](../../evidence/H-d71d5a2bab6eba0012e1.json)
- [new-code-interface.json](../../evidence/H-01194c2bce2c6a558d7e.json)
- [next_batch_guide.md](../../evidence/H-92e17ce0b2819094521c.md.txt)
- [next_experiments.json](../../evidence/H-288e5a656edf5d0484fc.json)
- [package_delivery.py](../../evidence/H-a6c5df790f6467b2dab7.py.txt)
- [preparation-gates.json](../../evidence/H-777716115682e825e910.json)
- [previous/analysis.md](../../evidence/H-f56fd769a33eee92a9df.md.txt)
- [previous/audit.zip](../../evidence/H-bbc54dd4f553ed7f3444.archive-reference.json)
- [previous/delivery-manifest.json](../../evidence/H-cbcbcb9729612e83b881.json)
- [previous/issues.json](../../evidence/H-4d6652b71cfd765d64ad.json)
- [previous/next_batch_guide.md](../../evidence/H-76cdca6ef1d1a58c15ae.md.txt)
- [previous/next_experiments.json](../../evidence/H-806a2fc2771a7251210d.json)
- [previous/review.json](../../evidence/H-98d8bc2235b15741f9ce.json)
- [previous/search_space.json](../../evidence/H-aa2962eb031dac9a7bac.json)
- [review.json](../../evidence/H-73d729eaeaac152e118f.json)
- [search_space.json](../../evidence/H-5f6c490e3e19082be7e6.json)
- [task-ledger.json](../../evidence/H-765f9fc186f74294eab6.json)
- [work_init.py](../../evidence/H-47a39345061fc36d5e10.py.txt)

42个proposal为21个非Caco2任务各H0/H1，每个seeds44/45，split43。S1为40fit，S1B为44fit且等待门槛释放；每配对只改变dropout0.1/0.3。小/中/大预算40/≤108/≤132含条件分支，不是全部立即执行。

阅读回执55/55属于模型声明，主控已独立核对关键原文和算术，但完整Chat工具轨迹没有独立重建；补全未使用真实subagents也保留原披露。两个种子不构成显著性结论，冻结/fit-only等true字段仍是设计而非实际行为。

原版MAE统一maximize、零fit准备门槛混入训练、自依赖和悬空D-METRIC已在补全中修正；旧错误没有覆盖删除。原时点公式为推断；valid估算43.60321693与官网显示分项均值46.41840768分开，Caco2完美上限46.33201276与48.81151482也分开。
