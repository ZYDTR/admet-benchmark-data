# Next batch guide — `admet-pro-thin-endpoints-20261103-006`

## Current decision
先准备、暂不执行 `P006-PGP-REP-PHYS`。科学理由：Broccatelli原始研究明确使用药效团/MIF及膜分配性质；项目已接受CheM、MiniMol、Morgan缓存，可在不更换预训练模型的前提下检验简单2D理化增量。此研究比重跑weighted BCE、Morgan、floor或增加seed提供更直接的机制判别。

## Mandatory preparation handoff
**Owner:** task partition/data owner.  
**Deliverable:** 原始Pgp train-only split manifest，含task/split id、原row_index全覆盖映射、fold/inner-fit/stop成员、seed、grouping/duplicate policy、partition hash、输入版本及label source lineage。先检查既有task ledger；如有已接受partition，复用，不重建。当前公开split_register没有Pgp记录，故该项是阻断依赖，不是科学负结果。

**Owner:** feature/cache owner.  
**Deliverable:** 对CheM 2048、MiniMol 512、Morgan ECFP4 2048原缓存做只读身份绑定；确认原行覆盖/顺序与Pgp train一致。Morgan固定RDKit 2024.09.6 radius2、chirality、binary；不重新生成缓存。新增8描述符代码版本固定、确定性测试和fit-only scaler fixture。

**Owner:** scoring owner.  
**Deliverable:** 原train OOF全行连续概率；按 `analysis.md §5` 产生完整群与补集、安全聚合、AUROC/AP及cluster uncertainty。禁止读取/输出逐行valid/test真值或残差。

## Fixed science config
- 6 cells: CheM base / CheM+8 physchem; MiniMol base / MiniMol+8; Morgan base / Morgan+8.
- 8 descriptors: MW, Crippen cLogP, TPSA, HBD, HBA, rotatable bonds, aromatic rings, formal charge.
- L2 logistic regression C=1, intercept, no class_weight; solver/version/tolerance pinned at prep. Continuous probabilities. Fit-only scaling for 8 added descriptors; Morgan bits unchanged.
- Fit only original train.Y; all external parameters/buffers frozen. No new rows, labels, pKa model, assay covariates, checkpoint downloads, Valid/test scoring.
- If accepted folds K, total fits = 6K. K is not assumed; do not create folds without partition-owner receipt.

## Conditional follow-on
hERG, BBB, CYP2C9 inhibition and CYP2C9 substrate remain separate. For each, first bind its own accepted train-only split and source semantics; compare the three existing representations with the same readout. Add the descriptor view only when the task-specific split and complete score owner are ready. CYP substrate requires six-source lineage; CYP inhibition requires Veith/AID1851 assay lineage. No shared “CYP2C9” config.

## Stop/continue rules
- No partition receipt -> stop at preparation.
- No stable descriptor increment and no repair of low-support/consensus-error groups -> close Pgp 2D-proxy branch; do not tune descriptor list or seed.
- Only one representation benefits -> record representation interaction, not generic physchem effect.
- Overall AUROC improves but consensus errors persist -> no mechanism resolution.
- Source lineage absent -> do not run assay subgroup explanation.
- Any prospective 3D module needs independent asset/license/producer admission; no alteration of active SMI8/HEPOS40/SOLCTX4/GEO32.
