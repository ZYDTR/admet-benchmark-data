import concurrent.futures,json,sys
from pathlib import Path
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'source'))
from transport import remote
from fetch_host import fetch
s=(RUN/'source/audit_traces.py').read_text().split("if __name__=='__main__':")[0]
s+='\nimport os\nos.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])\nr=[]\nfor p in sorted(Path(ROOT).joinpath("raw").glob("*.strace")):\n    a=audit(p);a.pop("successful_inside_paths",None);r.append(a)\nprint(json.dumps(r))\n'
(RUN/'source/audit_final_remote.py').write_text(s)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    a=pool.submit(remote,s,'audit-final',timeout=100)
    b=pool.submit(remote,RUN/'source/final_inventory_remote.py','inventory-final',timeout=150)
    c=pool.submit(remote,RUN/'source/final_gpu_details_remote.py','gpu-final',timeout=60)
    audits=json.loads(a.result());inventory=json.loads(b.result());gpu=json.loads(c.result())
(RUN/'operator/final-write-audit.json').write_text(json.dumps(audits,indent=2)+'\n')
print('Final read-only checks collected',flush=True)
print(json.dumps({'gpu_modes':gpu['gpu_modes'],'devices':gpu['devices'],'own_jobs':inventory['jobs'],'tree_violations':inventory['tree_identity_violations'],'bytes_by_top_directory':inventory['bytes_by_top_directory'],'selected_gpu':[x for x in inventory['gpu']['stdout'].splitlines() if x.startswith('4,')],'audit_summary':[{'trace':Path(x['trace']).name,'verdict':x['verdict'],'outside_effect_count':len(x['successful_outside_file_effects']),'unknown_write_count':len(x['unknown_write_effects'])} for x in audits]},indent=2),flush=True)
path,manifest=fetch('final-fetch')
print('All evidence downloaded and SHA256 checked:',len(manifest),'files ->',path,flush=True)
(RUN/'operator/fetch-receipt.json').write_text(json.dumps({'path':str(path),'files':len(manifest),'all_sha256_verified':True,'manifest':str(path/'fetch-manifest.json')},indent=2)+'\n')
