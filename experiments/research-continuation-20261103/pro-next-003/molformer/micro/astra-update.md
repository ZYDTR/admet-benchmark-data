# MoLFormer微粒体结果

111行复用Valid：MLP46/47 Spearman为0.3923772173/0.4254760407，TabM为0.4322754114/0.4561373539。对旧CheM/Mini同head/seed八对全部负；MoL内部TabM两对胜MLP，但仍低于原两种表示。

与Caco结果一致地，当前冻结MoL配方在前两个任务没有收益。继续完成预注册DILI和CYP2D6，保留任务异质性检验；不为这两个负结果追加seed、epoch、池化或ensemble。原参数及所有buffer冻结、实际特征/行覆盖和CPU重载已证；维度/缩放/容量/设备及重复Valid限制仍保留。4新Spearman一次、8旧标量复用；无新增Astra真值/模型/指标调用。
