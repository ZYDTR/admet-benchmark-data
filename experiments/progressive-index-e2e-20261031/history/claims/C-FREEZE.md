# C-FREEZE

历史命题和每次适用范围均保留，当前状态不能覆盖旧判断。

## CE-FREEZE-01 · proposed

命题：跨run wrapper总摘要不同足以证明冻结编码器被更新

理由：原issues中保留initial hypothesis：总摘要不同是否意味外部编码器变化。这里导入的是疑问，不称它曾被证实。

适用范围：两run已登记wrapper状态

时间：历史顺序已知，精确时刻未知。审查者：controller_import_of_preserved_evidence。

证据：[issues](../../evidence/5a6de3c181b2dab31189fa2ed175d9b3dc695a5c9c73bb4ee138fdc811ecdb93/issues.json)

## CE-FREEZE-02 · refuted

命题：跨run wrapper总摘要不同足以证明冻结编码器被更新

理由：跨run不同仅在未被fingerprint调用的随机predictor；各run登记参数及buffer前后相同。因此单凭总摘要不同不能推出冻结失效。

适用范围：仅两个run已登记状态与核验调用链；不代表未登记内存均已证明

时间：历史顺序已知，精确时刻未知。审查者：controller_import_of_preserved_evidence。

证据：[tensors](../../evidence/71eb2ee4e34b1b2671a071ed9679c6e10f60b95bd6dc2c087fe8a3322d2ab034/tensors.json) · [call-path](../../evidence/575dd14195e2b8f33995b30d8bf03998bbc0dbccedc6727714dba92e816cab29/call-path.json) · [disposition](../../evidence/3f596c0111f6f4d40b7826e29d8dfea3ba496fe4a0ec71180f3b93b08325fdc2/disposition.json)

