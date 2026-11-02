# 完整22任务：H0/F010 × seed46/47

64项新增固定Valid评分一次完成，合并已验six22和2项旧H0汇总，共88槽位；没有重算旧模型。

|配置|种子|22任务推算Valid|共同21任务（排除BBB）|共同19任务（排除跨主机三任务）|
|---|---:|---:|---:|---:|
|H0|46|42.747790477（冻结证据受限）|42.447525049|45.145891626|
|H0|47|43.225989415|42.952641741|45.637767655|
|F010|46|46.001601277|45.832506520|46.394305767|
|F010|47|46.046595332|45.908060744|46.509910439|

|任务|指标|H0双种子均值|F010双种子均值|改进量（正更好）|seed46/47|
|---|---|---:|---:|---:|---|
|ames|AUROC|0.785885615295|0.785988730321|0.000103115025604|better / worse|
|bbb_martins|AUROC|0.89174745215|0.900571712652|0.00882426050211|better / worse|
|bioavailability_ma|AUROC|0.672757475083|0.702657807309|0.0299003322259|better / better|
|caco2_wang|MAE|0.41075663314|0.360454018043|0.0503026150972|better / better|
|clearance_hepatocyte_az|Spearman|0.316210905423|0.361329940173|0.0451190347501|better / better|
|clearance_microsome_az|Spearman|0.48064959398|0.468074960788|-0.0125746331915|better / worse|
|cyp2c9_substrate_carbonmangels|AUPRC|0.327398869775|0.321758075427|-0.00564079434803|better / worse|
|cyp2c9_veith|AUPRC|0.758785776848|0.761945109733|0.00315933288462|better / better|
|cyp2d6_substrate_carbonmangels|AUPRC|0.395545274282|0.406705262759|0.0111599884768|better / better|
|cyp2d6_veith|AUPRC|0.660412612727|0.680944246135|0.0205316334086|better / better|
|cyp3a4_substrate_carbonmangels|AUROC|0.753136200717|0.746863799283|-0.00627240143369|worse / worse|
|cyp3a4_veith|AUPRC|0.876538451942|0.87406767462|-0.00247077732175|worse / worse|
|dili|AUROC|0.867032967033|0.835164835165|-0.0318681318681|worse / worse|
|half_life_obach|Spearman|0.279104346701|0.239779680784|-0.0393246659164|worse / worse|
|herg|AUROC|0.902281746032|0.90128968254|-0.000992063492063|better / worse|
|hia_hou|AUROC|0.961458333333|0.947916666667|-0.0135416666667|worse / worse|
|ld50_zhu|MAE|1.95392416572|0.65427556317|1.29964860255|better / better|
|lipophilicity_astrazeneca|MAE|0.560235728549|0.534805201953|0.0254305265964|better / better|
|pgp_broccatelli|AUROC|0.909567320613|0.908357968288|-0.00120935232464|better / worse|
|ppbr_az|MAE|24.12515785|11.4795370571|12.645620793|better / better|
|solubility_aqsoldb|MAE|6.19771988996|1.51937792639|4.67834196358|better / better|
|vdss_lombardo|Spearman|0.33373399165|0.319807353384|-0.0139266382658|worse / better|

44个配对：优27，劣17，平0。

双种子均改善：bioavailability_ma, caco2_wang, clearance_hepatocyte_az, cyp2c9_veith, cyp2d6_substrate_carbonmangels, cyp2d6_veith, ld50_zhu, lipophilicity_astrazeneca, ppbr_az, solubility_aqsoldb。
双种子均退化：cyp3a4_substrate_carbonmangels, cyp3a4_veith, dili, half_life_obach, hia_hou。

- Formula inferred from retained website22 tuples, not published official formula; local Valid only, no hidden-test/leaderboard forecast.
- AP is tied-group average precision; exact official AUPRC equivalence unknown.
- BBB H0seed46 missing original encoder-after remains research-only. Full22 H0s46 is explicitly evidence-limited; common21 excludes BBB from every group.
- Three seed46 pairs cross hosts; LD50/Sol reuse old-batch H0. Common19 additionally removes all three affected tasks, not a replacement official aggregate.
- Mini22 cached representation producer vs current consumer environment retained; no new encoding or equivalence test.
- Descriptive results only two seeds; reused Valid and prior selection, no significance test or posthoc mixed winner group.
- 22+64 new metrics computed once; two old H0 aggregates reused, no old metric reruns; no row truth/residual output.
