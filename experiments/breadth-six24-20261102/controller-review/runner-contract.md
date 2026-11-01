# 当前科学执行接口与准备度

本轮实际执行冻结CheMeleon2048维raw特征，内部raw Drug分组、split seed43/10% stop，fit-only float32逐维标准化（std<1e-8置1），回归fit-only Y标准化MSE，分类BCEWithLogits。MLP2048→256→1/ReLU、dropout0.1或0.3、AdamW lr0.0005/wd0.0001、batch128/max50/patience8/min_delta1e-7，模型seed44/45。best头预测，原Y尺度或连续概率。所有24配置已完成，不应再次列入新增fit。

实际源码：在上级evidence/source-index.json定位remote/source/src/admet_breadth/{trainer,cache,pipeline,heads,data_io,metrics,encoder}.py，以及各run/source/consumed-config和expanded-config；不能只根据本摘要判config_only。当前validate_config接受范围窄，新的缩放、低方差门槛、损失、头容量、学习率等建议须标明需要改哪些真实科学接口，不能凭含义相近字段当实现已支持。旧legacy_reference只作来源，运行版本有变更。

18份原特征缓存、全部fit划分与scalers已取得，身份见上级assets/cache-index.json；新头可复用原raw特征，预处理仍在对应fit重拟合。改变编码器/池化/输入等才可能需新编码，不能不查缓存身份就重做编码，也不能复用旧fit统计到新划分。现有10项科学资产准备度见上级assets/scientific-assets.json。现有可用环境不是所有底座就绪。

部署、监控、异常恢复由执行Agent按现场判断；不要求复建旧launcher/supervisor。只允许冻结外部参数/buffer，train.Y学习，不改原数据，不训练或安装用于本次研究。下一批方案全部proposal_only，由主控科学审读后逐项登记；推理/集成也须另有具体任务。
