#!/usr/bin/env python3
"""生成本地完整历史导航；不搬运或公开原件，来源缺项由inventory拒绝。"""
from pathlib import Path
import argparse,json
from control_contract import inventory,read,ROOT,WORKSPACE,sha

def build(out):
    inv=inventory();out=Path(out);out.mkdir(parents=True,exist_ok=False)
    (out/'inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
    lines=['# ADMET 已知历史总览','', '本地登记视图。完整性指独立发现的实体与下列记录已对账，不等于全部原件已公开、已被Pro读取或已完成科学验收。','',
      '## 分层入口','', '[项目入口]('+str(ROOT/'AGENTS.md')+') → [控制合同]('+str(ROOT/'control/README.md')+') → 本页实验/失败总表 → 各记录原件；原始来源只读。', '',
      '## 全部实验、准备与研究','', '| ID / 类型 | 当前判定 | 范围与限制 | 证据 |','|---|---|---|---|']
    for row in inv['records']:
        links=' · '.join('[来源'+str(i+1)+']('+str(WORKSPACE/p)+')' for i,p in enumerate(row['sources']))
        lines.append('|'+row['id']+' / '+row['kind']+'|'+row['state']+'|'+row['summary']+'|'+links+'|')
    lines+=['','## 科学资产（与执行LLM分开）','','| 资产 / 类型 | 准备度 | 缺口 |','|---|---|---|']
    for x in read(ROOT/'control/scientific-assets.json')['assets']:
        lines.append('|'+x['name']+' / '+x['kind']+'|'+x['readiness']+'|'+'；'.join(x['blockers'])+'|')
    lines+=['','## 问题、推翻与评分使用','','[历史问题账](%s) · [旧结论事件](%s) · [评分使用账](%s)'%(ROOT/'exchange/issues/INDEX.json',ROOT/'exchange/catalog/inputs/20261031-v1.json',ROOT/'control/evaluation-use-ledger.json'),'',
      '公开材料下一版须为这些来源逐项生成批准的原件/衍生件映射及固定URI。已有未迁入项阻断普通研究发送；没有保存过的记录保留缺口，不用重新训练补造。',
      '最早Mini基线是22个任务各一头；后续4个已完成海南run均为Caco2，不是4组22任务。失败pilot单列。历史评分总访问次数未全部记录，账内null不能理解为0。','']
    (out/'README.md').write_text('\n'.join(lines))
    return {'records':len(inv['records']),'sources':len(inv['sources']),'runs':len(inv['discovered_run_roots']),'out':str(out)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.out),ensure_ascii=False))
