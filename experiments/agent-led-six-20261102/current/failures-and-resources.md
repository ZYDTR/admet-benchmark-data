# 失败、恢复与条件性资源接受

GPU0旧共享失败保持原裁定：对方SM下降伴随本任务负载，连续3次阈值、固定暂停及N/A填0不能证明无影响。科学完整的稳定模型/预测已由主控明确准入用于分析，不能因此消除运行风险。

MSE seed46从6epoch/30步持久head/optimizer/RNG/best/history恢复到37epoch/185步，新增155步；前6轮历史保留。原停止后可能多做但未落盘的更新仍未知。GPU1 attempt02因过敏CPU任一tick条件在CUDA/恢复前退出-15，随后只读校准表明1tick属当时观测的低活动背景，再校准为每间隔>3tick退出；原条件、失败及修订差异均保留，未重复完成两项。

187份GPU1历史文件中186条数值完整、186个唯一时间戳，首条unknown，不能写187份全部0。GPU1新鲜健康/身份、余量及本次小头串行低占用的监控支持该条件分支，缺数全unknown；没有对方业务延迟/吞吐直接证明，不能推广为任意共享或绝对零影响。末次37个登记自有生命周期已退出/terminal/reused，原驻留他人进程未发信号；这不是全机进程清场证明。

- [执行方全轮报告与原失败/校准细节](../evidence/documents/F-ca969709b4cb743c534e.md)。
- [GPU1条件、退出控制和已知限制](../evidence/objects/89d720ea810fa7d36aee72f510eae3e55a535769b2357fd3e2ec266f83a8b3b5.json) · [原始资源样本与unknown计数](../evidence/objects/2719fd6bbf915d92e4e861b0a69e57a2db302a9bd8744d6fc87c03b64ab55a23.json)。
- [11次尝试，6完成/5失败或中途，预算全部计入](../evidence/objects/592581a0b98aa8663796a19031cf517ddf2b5238f8b0c8b3bc37ef36384b3241.json)。
- [主控GPU1科学和条件性共享复核](../evidence/documents/F-3eae03c3b5751b0ccefb.md) · [最终原始postcheck独立复核](../evidence/documents/F-97d460ac6baee86fe885.md)。
- [完整旧GPU0争议及时间点](../prior-history/current/failures-and-resources.md) · [六项逐run现存原件](evidence.md)。

十六条窄文件/write/mmap轨迹的已保存审查没有报告成功越界修改，拒绝和device IO分列；主控未独立重放全部syscall，也未做全服务器/ioctl零副作用证明。首次本机取回导入路径、RNG层级诊断错误、超时SSH reader未知退出等失败都保留，不能用随后成功覆盖。
