# TabICL 固定面板结果

All16 frozencontexts and16Valid scores complete; primary Mini-vsCheM7positive/1negative across8pairs, not independent pooledtest. TabICL is not a uniform readout replacement: Caco andCYP remain below existingTabM mean; DILI andMiniMicro justify only already-dispatched structuralstress followup.

| Task | Mini−CheM primary signed improvements | TabICL 相对旧头的判断 |
|---|---|---|
| caco2_wang | +0.0122796674, +0.0026266567 | MiniMol2of2betterwithinTabICL;newTabICLnotbetterthanexistingTabMmeanoneitherrepresentation;finishremainingregistered12slotswithoutadaptation |
| dili | +0.0285714286, -0.0065934066 | Mini_vsCheM_mixed;all4descriptiveTabICLrecipe_meanimprovements_support_followup_candidate_notwinnerclaim |
| clearance_microsome_az | +0.1532800230, +0.1150443331 | Micro111Valid:MiniTabICL two pairedMini-CheM contrasts positive (+.1532800230,+.1150443331); MiniTabICLmean .6356920776 exceeds oldMiniMLP/TabM means descriptively. CheMTabICLaboveoldMLPbutbelowoldTabM. GroupednativeTrainstresscandidate afteroriginal16,notuniversalreplacement/noadaptiveValidqueries. |
| cyp2d6_veith | +0.0389896973, +0.0518690921 | MiniMol beats CheM in both frozen TabICL contexts; MiniTabICL meanAP .7297453283 is lower than existingMiniMLP .7556804820 andMiniTabM .7653019636. No additionalCYPTabICL contexts orValid queries; retain existingMiniTabM candidate and finish separately registeredDILI/micro nativeStress16. |

正值统一表示Mini更好：Caco使用CheM MAE−Mini MAE，其余使用Mini metric−CheM metric。不能跨任务平均这些数值。

所有个体值、16个次级比较及来源见 [panel-results.json](panel-results.json)。次级比较是context44/45与旧gradient46/47的非配对均值，不是预测集成。复用同一验证集，不构成独立复现。

后续只执行已派DILI/micro固定结构stress16，0新官方Valid/test查询。原拟合状态、失败及日志由原Sol独立归档；首MiniCaco44内部forward数仍UNKNOWN。
