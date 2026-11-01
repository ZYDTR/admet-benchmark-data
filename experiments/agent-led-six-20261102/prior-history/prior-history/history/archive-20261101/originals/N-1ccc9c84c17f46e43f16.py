"""只读核对已安全取回的研究文件；格式、引用、声明覆盖与科学实读分开。"""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath

FILES = {'analysis.md','review.json','issues.json','next_batch_guide.md','next_experiments.json','search_space.json'}

def parse(raw):
    def pairs(items):
        out = {}
        for k,v in items:
            if k in out: raise ValueError('duplicate key: '+k)
            out[k]=v
        return out
    def finite(s):
        x=float(s)
        if not math.isfinite(x): raise ValueError('nonfinite')
        return x
    return json.loads(raw, object_pairs_hook=pairs, parse_float=finite,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))

def inspect(root, binding, reading):
    root=Path(root); manifest=parse((root/'delivery-manifest.json').read_bytes())
    aliases=[manifest[k] for k in ('input_manifest_sha256','manifest_sha256') if k in manifest]
    if not aliases or any(x!=binding['manifest_sha256'] for x in aliases):
        raise ValueError('input manifest identity mismatch/conflicting aliases')
    for k in ('request_id','round_id'):
        if manifest.get(k)!=binding[k]: raise ValueError('delivery identity: '+k)
    seen=set()
    for e in manifest['files']:
        name=e['path'];rel=PurePosixPath(name);p=root/name
        if rel.is_absolute() or '..' in rel.parts or '\\' in name or name in seen:
            raise ValueError('unsafe/duplicate path')
        if not p.resolve().is_relative_to(root.resolve()) or any(x.is_symlink() for x in [p,*p.parents]):
            raise ValueError('outside root/symlink')
        data=p.read_bytes()
        if len(data)!=e['bytes'] or hashlib.sha256(data).hexdigest()!=e['sha256']:
            raise ValueError('file identity: '+name)
        seen.add(name)
    if not FILES<=seen: raise ValueError('missing required files')
    review=parse((root/'review.json').read_bytes())
    for k in ('request_id','round_id','manifest_sha256'):
        if review.get(k)!=binding[k]: raise ValueError('review identity: '+k)
    issues=parse((root/'issues.json').read_bytes())
    proposals=parse((root/'next_experiments.json').read_bytes())
    spaces=parse((root/'search_space.json').read_bytes())
    for collection,key in [(issues,'issue_id'),(proposals,'proposal_id'),(spaces,'direction_id')]:
        if not isinstance(collection,list): raise ValueError('expected array: '+key)
        ids=[x[key] for x in collection]
        if len(ids)!=len(set(ids)): raise ValueError('duplicate ID: '+key)
    issue_ids={x['issue_id'] for x in issues};proposal_ids={x['proposal_id'] for x in proposals}
    dangling_proposals=[{'issue_id':x['issue_id'],'proposal_id':p} for x in issues for p in x['related_proposal_ids'] if p not in proposal_ids]
    dangling_issues=[{'direction_id':x['direction_id'],'issue_id':i} for x in spaces for i in x['linked_issues'] if i not in issue_ids]
    receipts=review['read_receipt'];rows=[]
    for need in reading['requirements']:
        matches=[x for x in receipts if x.get('uri')==need['uri']]
        exact=[x for x in matches if all(x.get(k)==need[k] for k in ('entry_id','layer','source_version')) and x.get('read_mode')=='original']
        rows.append({'entry_id':need['entry_id'],'uri':need['uri'],'uri_matches':len(matches),'claimed_original':any(x.get('read_mode')=='original' for x in matches),'exact_declared_identity_and_mode':len(exact)==1})
    return {'files_integrity':'passed','manifest_identity_field_used':'input_manifest_sha256' if 'input_manifest_sha256' in manifest else 'manifest_sha256',
            'listed_files':len(seen),'required_files':6,'listed_extras':sorted(seen-FILES),
            'array_shape':'allowed by current Prompt; identity bound by delivery manifest and review',
            'dangling_proposal_references':dangling_proposals,'dangling_issue_references':dangling_issues,
            'reference_closure_passed':not dangling_proposals and not dangling_issues,
            'required_read_count':len(rows),'uri_matched':sum(bool(x['uri_matches']) for x in rows),
            'uri_matched_claimed_original':sum(x['claimed_original'] for x in rows),
            'declared_read_contract_passed':all(x['exact_declared_identity_and_mode'] for x in rows),
            'reading_comparison':rows,'scientific_status_from_source':review['status'],
            'fresh_chat_read_verified':False,'scientific_acceptance':False,
            'limitation':'Only file/identity/reference/declaration checks. Actual reading and scientific/admissibility judgments remain independent main review. Originals unchanged; aliases are interpreted, not rewritten.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--binding',type=Path,required=True);p.add_argument('--reading',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=inspect(a.root,parse(a.binding.read_bytes()),parse(a.reading.read_bytes()))
    with a.out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='reading_comparison'},ensure_ascii=False))
if __name__=='__main__':main()
