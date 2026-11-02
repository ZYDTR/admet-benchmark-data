# 28项固定Valid评分与对照

28/28项完成；37,494行预测，6个真值源共6,935独立原行；每项指标只调用一次。整批40份CSV已在首个指标调用前通过摘要、全行身份与数值校验。旧24项未重评分。主控已独立复算全部28项并验收，最大差8.8818e-16；正式评分与额外验证访问分列。

|任务|配置|种子|指标|原始Valid值|相同种子H0值|改进量（正为更好）|
|---|---|---:|---|---:|---:|---:|
|lipophilicity_astrazeneca|F001|44|MAE|0.561149395447|0.575065120095|0.0139157246481|
|lipophilicity_astrazeneca|F001|45|MAE|0.546414612215|0.566579750524|0.0201651383091|
|lipophilicity_astrazeneca|F010|44|MAE|0.537130001119|0.575065120095|0.0379351189765|
|lipophilicity_astrazeneca|F010|45|MAE|0.538007240921|0.566579750524|0.0285725096036|
|bbb_martins|F001|44|AUROC|0.89019388516|0.896905294556|-0.00671140939597|
|bbb_martins|F001|45|AUROC|0.892306736266|0.892306736266|0|
|bbb_martins|F010|44|AUROC|0.898521004226|0.896905294556|0.0016157096694|
|bbb_martins|F010|45|AUROC|0.909955257271|0.892306736266|0.0176485210042|
|cyp2d6_veith|F001|44|AUPRC|0.69960172354|0.698514342943|0.00108738059698|
|cyp2d6_veith|F001|45|AUPRC|0.663973250021|0.702340737577|-0.0383674875557|
|cyp2d6_veith|F010|44|AUPRC|0.694632048853|0.698514342943|-0.00388229408957|
|cyp2d6_veith|F010|45|AUPRC|0.709816508801|0.702340737577|0.0074757712247|
|clearance_hepatocyte_az|F001|44|Spearman|0.35554905867|0.324564196375|0.0309848622943|
|clearance_hepatocyte_az|F001|45|Spearman|0.355028944975|0.334062068737|0.0209668762387|
|clearance_hepatocyte_az|F010|44|Spearman|0.362313849518|0.324564196375|0.0377496531427|
|clearance_hepatocyte_az|F010|45|Spearman|0.368230556891|0.334062068737|0.0341684881539|
|ld50_zhu|F001|44|MAE|0.883628945905|0.881456127685|-0.00217281821976|
|ld50_zhu|F001|45|MAE|0.769535721172|2.27570581155|1.50617009038|
|ld50_zhu|F001|46|MAE|0.854094208949|2.03566691935|1.1815727104|
|ld50_zhu|F010|44|MAE|0.676217992508|0.881456127685|0.205238135177|
|ld50_zhu|F010|45|MAE|0.600210750984|2.27570581155|1.67549506056|
|solubility_aqsoldb|F001|44|MAE|2.2453231632|7.63972868366|5.39440552046|
|solubility_aqsoldb|F001|45|MAE|2.65220046263|8.77730875608|6.12510829345|
|solubility_aqsoldb|F001|46|MAE|2.08627167074|6.11704446918|4.03077279844|
|solubility_aqsoldb|F010|44|MAE|1.40941650251|7.63972868366|6.23031218115|
|solubility_aqsoldb|F010|45|MAE|1.52462373928|8.77730875608|7.2526850168|
|ld50_zhu|H0|46|MAE|2.03566691935|本批H0参照|—|
|solubility_aqsoldb|H0|46|MAE|6.11704446918|本批H0参照|—|

|配置|种子|推算Valid 22任务均分（其他16固定）|
|---|---:|---:|
|H0|44|43.819675388|
|H0|45|42.902648802|
|F001|44|44.588258810|
|F001|45|44.579486226|
|F010|44|45.382550059|
|F010|45|45.480340688|

原Mini22推算Valid均分：43.603216929。

H0：种子44/45均分 43.361162095。
F001：种子44/45均分 44.583872518。
F010：种子44/45均分 45.431445374。

本批逐任务事后最优推算：45.561743097；含旧24事后最优：45.577658617。

F010在lipophilicity、BBB、hepatocyte、LD50、solubility的两个配对种子均优于旧H0；CYP2D6两个种子方向不一致。F001对LD50种子44略退步，种子45/46改善；solubility三个配对种子均改善。以上是本地Valid比较，不能证明hidden test泛化。

- Formula inferred from retained 2026-11-01 website observations, not an explicitly published official formula.
- Local tied-group AP vs official AUPRC exact equivalence remains unconfirmed.
- Valid estimates only, not hidden-test forecasts; no official upload.
- Valid reused for comparisons and posthoc selection; best-case estimate is optimistic, no ensemble computed.
- Other16 held at original Mini22 baseline; newer Caco2 variants not substituted.
- Only two seeds for F010 and first four tasks; sample spread is descriptive, no significance claim.
