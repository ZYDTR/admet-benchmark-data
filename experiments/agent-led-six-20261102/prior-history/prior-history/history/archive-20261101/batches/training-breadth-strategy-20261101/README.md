# 本次增量：从 Caco2 扩展到 22 任务

**这是策略咨询输入，不是新增训练结果或执行授权。** 当前已完成学习为 Mini22 + 四次 Caco2，共五个 run / 26 个头。新六项 learning_starts=0；本地 core 修复尚未完成，不等待未完成结果。

[主控完整研究说明（含六项决策问题）](../../originals/N-cb3fdf80a1564318bc5f.md.txt)

## 新评分换算证据

- [REPORT.md](../../originals/N-d68e83c8e325d2541cd1.md.txt)
- [current-official-observation.json](../../originals/N-c68dbae0295309d2f4f2.json)
- [valid-score-estimate.json](../../originals/N-32099e3fce4b5fa09189.json)

官网榜单为 2026-11-01 10:39:26 UTC 观察快照。换算公式是对页面 22 组 raw/reference/score 的反推核验，不是官方源码证明。本地 valid 总分估算不是隐藏 test 榜单预测；AP/AUPRC 等价性尚未确认。保留原值，未新评分。

## 本轮全部已结束故障与裁定

- [首次外层故障原报告](../../originals/N-2295bd16747b1b92512c.md.txt)
- [主控首次故障验收](../../originals/N-85bdbcd0e46dd96e9c3d.json)
- [恢复合同/PID 参数缺陷原件](../../originals/N-a35a15212404755781bf.md.txt)
- [恢复修复主控验收](../../originals/N-f053758599714d868aed.json)
- [首次恢复执行/资源等待终态](../../originals/N-4bcb99d46f1ba07fc053.md.txt)
- [第二次恢复执行完整原报告](../../originals/N-73d7ddec8f0fe973ddab.md.txt)
- [原六项状态及原始 GPU5 描述](../../originals/N-78b7adb084bde65a27ee.json)
- [原子 rename 与监控临时文件路径证据](../../originals/N-1e3e8ffd4ad5bd81ecd6.json)
- [主控461件复核与 GPU6 纠正](../../originals/N-95eef1ee1c5f3873e212.json)
- [主控旧失败/新通过与硬错误反例](../../originals/N-86bb2c12f3e6bb36190e.json)
- [修订范围和未测项](../../originals/N-85a4bf5450aa433101c6.json)

第二次恢复仅进入第一项预检，监督退出125，六项均未学习；实际 GPU6，旧文字GPU5保留并更正。早期 VmRSS 的故障当刻值/OS退出未保存仍未知，不能把原子 rename 新根因扩展到旧故障。已通过10项局部资源扫描测试不等于完整runtime、目标CUDA或恢复身份通过。

## 未完成事项（不等待，也不伪造缺失）

[进行中本地 core 修复任务](../../originals/N-8da17ce405eb66ff8995.json)

[完整旧 Pro、主控裁决与推翻链](../../history/issues/README.md) · [所有旧实验](../../history/README.md) · [真实 runner 与返回 schema](../../context/runtime-and-return.md)


## 主控后续状态补充

本科学策略快照仍截至11:28 UTC；此补充只更新并行工程恢复状态。主控随后修正完整候选中的旧日志文件名碰撞，六组本机回归及保留6份旧日志的实际子进程批处理通过；原Sol已收到一次attempt02目标执行。尚无新的学习/valid结果，不能把本机fixture当作海南CUDA通过。原始失败与此前状态全部保留。

- [status.json](../../originals/U-d987dc8b5927e03500bf.json)
- [MAIN_ACCEPTANCE.json](../../originals/U-f0d901ca7a02baee0e2c.json)
- [regression-results.json](../../originals/U-01adbf76ff9dc5ecf930.json)
- [corrected-existing-log.stdout](../../originals/U-9c96aae6435beb41dd67.txt)


## 最新已终态资源拒绝（004）

2026-11-01T11:48:18.475707+00:00：三次选卡合格后，实际启动前GPU3已有其他任务，因此outer78拒绝，batch/六项学习均0；这不是新core异常或模型失败。主控已逐项核验783件原始记录，自有进程已退出，原372+9及新308件未变；剩余执行5348.207345秒、截止不变。当前只在本机准备可有界接续的运输入口，尚未授权新的目标启动。科学结果仍是5run/26头。

- [status.json · V-66db113416b956b3e3cd](../../originals/V-66db113416b956b3e3cd.json)
- [status.json · V-4bfcab2729123156ea9e](../../originals/V-4bfcab2729123156ea9e.json)
- [status.json · V-1a10b18d39bbaa5f3d0b](../../originals/V-1a10b18d39bbaa5f3d0b.json)
- [status.json · V-d6f1466962d13cca97d2](../../originals/V-d6f1466962d13cca97d2.json)
- [status.json · V-217eb931a27448501100](../../originals/V-217eb931a27448501100.json)
- [status.json · V-75d82b6f12b7ec207806](../../originals/V-75d82b6f12b7ec207806.json)
- [status.json · V-98bdd9f4beb4fab73c6a](../../originals/V-98bdd9f4beb4fab73c6a.json)
- [MAIN_RESOURCE_REFUSAL_REVIEW.json · V-b0949d6ee567cd9a0cec](../../originals/V-b0949d6ee567cd9a0cec.json)
- [REPORT.md · V-68436b23be68c0fbb68e](../../originals/V-68436b23be68c0fbb68e.md.txt)
- [TIMING.json · V-6d583dcc46ba146768bf](../../originals/V-6d583dcc46ba146768bf.json)
- [evidence-manifest.json · V-2051e8344e4b9867967c](../../originals/V-2051e8344e4b9867967c.json)
- [receiver-release.json · V-53db6467ab45b65e083c](../../originals/V-53db6467ab45b65e083c.json)
- [outer-outcome.json · V-0d9b28872dd0fd10737f](../../originals/V-0d9b28872dd0fd10737f.json)
- [watch-actual-exit.json · V-a93068f4a28aca56f9c3](../../originals/V-a93068f4a28aca56f9c3.json)
- [launcher-watch-exit.json · V-d1aabc933fb28ad8e041](../../originals/V-d1aabc933fb28ad8e041.json)
- [query-00.json · V-92bdea80a862cf00439c](../../originals/V-92bdea80a862cf00439c.json)
- [query-01.json · V-41bdbea37446e388aa8e](../../originals/V-41bdbea37446e388aa8e.json)
