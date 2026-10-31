# C-DOWNLOAD

历史命题和每次适用范围均保留，当前状态不能覆盖旧判断。

## CE-DOWNLOAD-01 · proposed

命题：下载事件超时说明本轮实际文件下载失败

理由：下载事件等待超时，原失败回执已保存；当时还没有系统文件的独立确认。

适用范围：本次原audit.zip请求

时间：历史顺序已知，精确时刻未知。审查者：controller_import_of_preserved_evidence。

证据：[download-timeout](../../evidence/98e23850926a19b81313ca994fc0460cd7b0414fbd9702104c5867ba2e71f3a7/download-timeout.json)

## CE-DOWNLOAD-02 · refuted

命题：下载事件超时说明本轮实际文件下载失败

理由：系统下载实际成功；文件身份、六件SHA和ZIP CRC通过。超时的是工具事件捕获，真实传输完成时间仍未知。

适用范围：本次原audit.zip，不推广为所有超时均成功

时间：历史顺序已知，精确时刻未知。审查者：controller_import_of_preserved_evidence。

证据：[download-correction](../../evidence/e5d180bfc471294f564920fc16c3613b99b97b6282be68185e4b655c1a9918ba/download-correction.json) · [round](../../evidence/bffbdbf1e51cc911c593cb78e1681aa32964dd58d725a4a0ca4ee3ec5b38f61f/round.md.txt)

