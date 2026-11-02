# 22任务科学接续

已验批次完成；研究仍在继续。可定案的是指定配方的保留/否决，不能把“任务名已有分数”当作终极模型定案。

|任务|目前判断与下一问题|
|---|---|
|ames|Morgan2048identity+MLP四seedValid正向，但stop四seed反向；下一48中的双分组检验。|
|bbb_martins|floor混合；旧H0s46缺after冻结证明不可补造。当前无新架构/表示证据，Pro判断扩面与可信基线。|
|bioavailability_ma|Mini/Morgan当前MLP均双seed负向，停止扩同配方；早停/有限样本与旧Mini22较优仍待解释。|
|caco2_wang|F010稳健优于H0；Huber/drop0四seed各3/4，TabM双改善但部分触顶50且未胜历史Huber；需要优化进度/容量判别，非追加盲seed。|
|clearance_hepatocyte_az|F010跨既有四seed方向支持；Mini在此任务尚未尝试，与microsome不同，下一表示扩面候选。|
|clearance_microsome_az|MiniH0 MLP同设备4/4正向；换TabM旧两seed退步。48中检验分组稳健性。|
|cyp2c9_substrate_carbonmangels|posBCE双负、Morgan双负、Mini混合；canonical/scaffold方向反转且Valid阳性少，不能继续只扫seed。|
|cyp2c9_veith|F010旧双seed小增益；未尝试新表示/TabM，不把少量增益等同任务定案。|
|cyp2d6_substrate_carbonmangels|F010fit-posBCE四seed正向；保留加权损失候选，分组泛化和具体阳性盲区未验证。|
|cyp2d6_veith|MiniTabM对CheMTabM四seed正向，同Mini换头增益较小但4/4；48中检验分组。|
|cyp3a4_substrate_carbonmangels|F010原双seed退步；其他已试floor/simpleheads见完整ledger；保留H0比较锚，非全任务已最优。|
|cyp3a4_veith|H0/F010内lr1e-4各四seed正向；低LR与有限训练窗口作用尚未拆开。|
|dili|F001相对H0四seed正向，groupstress已有局部支持/反例；Mini/TabM无稳定收益，48作为负向迁移对照。|
|half_life_obach|F001相对H0四seed正向但绝对值含0.053；F010lowLR新44/45双反转。排序loss4有具体设计但尚无接口/学习，不能标完成。|
|herg|floor混合、小Valid；当前不盲增相同seed，可由Pro评估表示/化学群或置信证据。|
|hia_hou|affine相对普通MLP两floor各4/4，F010对drop0也4/4；H0对drop0一平局，小Valid限制。|
|ld50_zhu|F010抑制极端预测且Huber对MSE4/4正向；已固定敏感群无分组误差证据，盲区尚未被总分关闭。|
|lipophilicity_astrazeneca|F010已有支持；Huber仅3/4且不同seed反转，固定敏感群具体改善未知。|
|pgp_broccatelli|floor混合且盲预测高度相近；停止密扫同因子，Pro评估未试表示的边际信息。|
|ppbr_az|Mini同设备3/4，seed46反例保留；48检验分组。CheMF010对H0大收益已经支持。|
|solubility_aqsoldb|MiniH0MLP对CheMF010同设备4/4大增益；48检验结构分组。|
|vdss_lombardo|H0lowLR四seed3/4，F010混合；Spearman与MSE目标/早停仍可能不匹配，新表示未试。|

当前实际新请求为48项分组压力训练，完整既定矩阵见该cycle。常规Pro新请求同时准备发布；独立三路只派发调研不在取回范围。
