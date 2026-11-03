# 薄覆盖端点的机制与判别实验

Request: admet-pro-thin-endpoints-20261103-006

Fixed cutoff: 2026-11-03T14:42:51.342353+00:00

Read [this request decision contract](decision-contract.json), [full research prompt](PRO_PROMPT.md), [shared scientific entry](../common/START_HERE.md), [current status](../common/current/CURRENT_STATUS.json), [complete experiment design](../common/normative/EXPERIMENT_DESIGN.md) and [research Skill3.5.1](../common/normative/RESEARCH_SKILL.md). All shared data is the same immutable set, stored once. [This request manifest](input-manifest.json) binds its request-specific files and the shared manifest/files at this exact commit.

This request investigates thin endpoint coverage for BBB, hERG, Pgp and the two distinct CYP2C9 endpoints, using evidence and mechanistic discrimination rather than assuming low scores.

## Questions

- Q1: For bbb_martins, herg, pgp_broccatelli, cyp2c9_veith and cyp2c9_substrate_carbonmangels, reconstruct exactly what was actually tested, learned and ruled out. Distinguish CYP inhibition and substrate endpoints; thin research coverage is not proof of poor scores. Pro005 only retained/monitored these without a new task-level mechanism.
- Q2: From primary assay/data and pharmacological literature, what scientifically plausible missing information or feature/readout limitation could explain existing mixed results? Separate input support, charge/ionization or lipophilicity proxies, assay heterogeneity, class imbalance/metric behavior and representation/readout bottlenecks; do not assume any one true or invent per-row assay covariates.
- Q3: Derive genuinely discriminating, finite train-internal studies using existing CheM/MiniMol/Morgan representations first where informative, plus source-justified prospective new-module alternatives. Reuse actual partitions/controls when available; missing partition is a preparation dependency. No retesting weighted BCE/Morgan/floor recipes under new names. Explain prediction patterns that would falsify each explanation.
- Q4: Prioritize at least one immediately specifiable high-information study when evidence supports one, with full concrete matrix and independent conditional alternatives. Do not force an arbitrary count or invent evidence to fill a matrix. If no candidate is justified, identify exact missing evidence and why each plausible experiment would not discriminate; give concrete reopening trigger/owner.
- Q5: Design full groups including consensus error and low-disagreement coverage, matched repair/harm transitions, proper AUROC/AP handling and group uncertainty. New score analyses require designated scope/owner. Distinguish repeated Valid selection from independent evidence, never declare AP=official AUPRC without source.

Conduct this investigation independently. Neither another research response nor active training is a prerequisite. Preserve full alternatives/counterevidence, verify new claims with primary sources, deduplicate against completed/active science, and report actual reading coverage. Source access or this publication grants no new training, scoring, data/label, model, deployment or persistent Codex role authority. Complete outputs are analysis.md, issues.json, next_batch_guide.md, next_experiments.json, review.json and search_space.json with useful original supplements. The original assigned gateway handles conversation transport; the publisher does not send research prompts.
