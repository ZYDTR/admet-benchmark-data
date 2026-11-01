from pathlib import Path
import hashlib,json
w=Path.cwd();r=w/'adhoc_jobs/admet_training';a=r/'audits/control-plane-20261101';changes=json.loads((a/'changes.json').read_text())
def save(p,s):
 old=p.read_bytes();new=s.encode() if isinstance(s,str) else s
 if old==new:return
 dst=a/'before'/p.relative_to(w);dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():dst.write_bytes(old)
 p.write_bytes(new)
 entry=next((x for x in changes if x['path']==str(p.relative_to(w))),None)
 if entry:entry['after_sha256']=hashlib.sha256(new).hexdigest()
 else:changes.append({'path':str(p.relative_to(w)),'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':hashlib.sha256(new).hexdigest()})
def repl(p,pairs):
 s=p.read_text()
 for old,new in pairs:assert old in s,(p,old);s=s.replace(old,new)
 save(p,s)
p=r/'design/chat_gateway_20261031/CHAT_PROMPT.md'
repl(p,[('revision7','revision8'),('取回的全部实验原件','相关的完整实验原件（全部原件可达，按问题下钻，不要求无差别遍历）'),('一条历史推翻事件链','一条与本批相关的历史推翻事件链（若不存在则明确不适用，不编造）')])
p=r/'design/chat_gateway_20261031/prompt_contract.json';d=json.loads(p.read_text());d['template_revision']=8;save(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=r/'design/chat_gateway_20261031/GATEWAY_PROMPT.md'
repl(p,[('revision12','revision13'),('当前证据Skill为v0.4.1','当前证据Skill为v0.4.2')])
p=r/'design/chat_gateway_20261031/contracts.json';d=json.loads(p.read_text())
d['revision']=15
d['status']='current_role_and_data_contract; execution state belongs to registered cycle'
d['scope_note']='Historical observations are scoped explicitly below. Neither a design default nor an unsupported implementation branch is a new user prohibition.'
d['current_cycle_entry']='../../cycles/monitor-mae-e2e-20261101/CONTINUE.md'
d['chat_target']['scope']='historical first trial only; NEVER fallback to this target for a new batch'
d['authorization_notes']='Current authorization is the registered per-cycle task under project AGENTS; historical first-trial facts remain under measured_trial and trial_entry. No unrestricted HPO or automatic official submission.'
d['future_analysis_sessions']['analysis_chat_created_and_registered_by']='Controller registers one target/request per batch; gateway may create/select Pro in Browser and send first formal message only if no real native-addressable ID; then native continuation. See current evidence Skill.'
d['future_analysis_sessions']['new_chat_does_not_bypass_unknown_request_lock']='unknown SEND must reconcile; accepted complete artifacts with only generation-terminal unknown do not prevent controller registering a distinct new-evidence batch'
d['scoring']['completed_for_current_hainan_runs']=None
d['scoring']['completion_source']='registered cycle/run scoring receipts; old two-run trial was completed, not all later runs'
d['validation_analysis_proposal']['raw_truth_permission_activated']='per-cycle evaluation_scope; no global yes/no'
d['tooling_strategy']['status']='partially_implemented; reusable capabilities and gaps are listed separately'
d['catalog_skill']['version']='0.4.2'
d['open_decisions']['current_turn_scope']='Read current project entry and registered cycle, never infer current authorization from this design file.'
d['chat_transport']['basis']='Human 2026-11-01 approved Browser creation/Pro selection and conditional first formal send; native continuation and Browser attachment download.'
d['chat_transport']['browser_scope'] += ['create registered ordinary Chat and verify Pro','one sealed first formal message only if no native-addressable server ID exists']
d['chat_transport']['latest_actual_file_recovery']='Historical request-002 recovery passed; current cycle status is separate.'
d['prompt_contract']['template_revision']=8
d['review_contract']['required'].append('read_checks')
d['review_contract']['progressive_read_required']['historical_refutation_check']='Required when applicable history exists; otherwise explicit not_applicable, never fabricated.'
d['handoff_consumption']['controller_personal_work_is_valid_consumption']=True
d['handoff_consumption']['checker_limitation']='check_handoff.py does not recognize processing yet; preserve actual current-turn evidence without fake dispatch.'
save(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=r/'design/chat_gateway_20261031/status.json';d=json.loads(p.read_text());d['scope']='historical design/first-trial record only; not current pipeline status';d['current_cycle_entry']='../../cycles/monitor-mae-e2e-20261101/CONTINUE.md';save(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=r/'design/chat_gateway_20261031/one-trigger-audit.json';d=json.loads(p.read_text());d['scope']='dated 2026-10-31 audit; not current task status';d['current_cycle_entry']='../../cycles/monitor-mae-e2e-20261101/CONTINUE.md';save(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=r/'skills/ml-preparation-only/SKILL.md';repl(p,[('name: ml-preparation-only\n','name: ml-preparation-only\nversion: 1.2.2\n')])
p=r/'skills/ml-preparation-only/scripts/preparation_packet.py';repl(p,[('import json\n','import json\nimport re\n'),('def local_file(root, relative):','''def skill_version(raw):
    text = raw.decode("utf-8")
    header = re.match(r"\\A---\\n(.*?)\\n---(?:\\n|$)", text, re.S)
    require(header is not None, "missing Skill frontmatter")
    versions = re.findall(r"(?m)^version:\\s*(v?\\d+(?:\\.\\d+){1,2})[ \\t]*$", header.group(1))
    require(len(versions) == 1, "missing or ambiguous Skill version")
    return "v" + versions[0].removeprefix("v")


def local_file(root, relative):'''),('    return {"state": "target_files_verified" if target else "local_packet_verified",','''    frozen_skill = local_file(task, "input/rules/PREPARATION_SKILL.md").read_bytes()
    require(packet["skill_version"] == skill_version(frozen_skill), "Skill version differs from frozen content")
    return {"state": "target_files_verified" if target else "local_packet_verified",'''),('    version = "v1.2"','    version = skill_version(content["input/rules/PREPARATION_SKILL.md"][1])')])
p=r/'skills/ml-preparation-only/scripts/test_preparation_packet.py';repl(p,[('from preparation_packet import prepare, verify','from preparation_packet import prepare, verify, skill_version'),('    def test_changed_skill_rejected(self):','''    def test_patch_version_is_from_actual_skill(self):
        receipt = self.stage()
        actual = skill_version((self.task / "input/rules/PREPARATION_SKILL.md").read_bytes())
        self.assertEqual(receipt["skill_version"], actual)
        self.assertIn(actual, (self.task / "dispatch-prompt.txt").read_text())
        self.assertEqual(skill_version(b"---\\nversion: 9.8.7\\n---\\nbody"), "v9.8.7")

    def test_version_metadata_mismatch_rejected(self):
        self.stage()
        p = self.task / "input/rules/PACKET.json"
        data = json.loads(p.read_text()); data["skill_version"] = "v0.0"
        p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "version differs"): verify(self.task, self.project)

    def test_missing_version_not_guessed(self):
        with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
            skill_version(b"---\\nname: example\\n---\\nWorkflow v8.1")

    def test_changed_skill_rejected(self):''')])
# Index references reflect current written capabilities, not future model behavior.
p=r/'skills/INDEX.md';repl(p,[('历史302文件完整取回、固定评分/发布已测','v0.4.1；历史302文件完整取回、固定评分/发布已测')])
(a/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n');print({'changed_files_total':len(changes)})
