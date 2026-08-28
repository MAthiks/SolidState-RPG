import hashlib,json,os
from pathlib import Path
from solidstate_runtime import GenericKnowledgePartition,GenericKnowledgeFirewall
from solidstate_runtime.source_backed_investigation_v4 import SourceBackedInvestigationPathV4
from solidstate_runtime.scenario7_release_gate import Scenario7ReleaseGateV1
from solidstate_runtime.multi_scenario_status_resolver import MultiScenarioStatusResolver
from solidstate_runtime.interface_v1 import ScenarioSelectionInterfaceV1
ROOT=Path(__file__).resolve().parent;SC7=ROOT/'scenario_candidates/scenario7';results=[]
def check(name,ok,detail=None):results.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# source identity/preflight
pdf=Path(os.environ.get('EXPLORATEUR_SOURCE_PDF','__MISSING_EXPLORATEUR_SOURCE_PDF__'))
check('source_pdf_present',pdf.exists(),str(pdf));check('source_pdf_sha256_exact',pdf.exists() and sha(pdf)==Scenario7ReleaseGateV1.SOURCE_PDF_SHA256,sha(pdf) if pdf.exists() else None)
layout=SC7/'source_layout.txt';check('source_layout_sha256_exact',sha(layout)==Scenario7ReleaseGateV1.SOURCE_LAYOUT_SHA256,sha(layout))
pre=json.loads((SC7/'SCENARIO7_PREFLIGHT.json').read_text());check('source_preflight_pass',pre.get('status')=='PASS' and all(v=='PASS' for v in pre.get('gates',{}).values()),pre)
# preserve historical non-causal topology
roles=json.loads((SC7/'EXPLORATEUR_SOURCE_ROLE_RECOVERY_V1.json').read_text());topo=json.loads((SC7/'EXPLORATEUR_INVESTIGATION_TOPOLOGY.json').read_text())
check('historical_causal_transition_count_zero',roles.get('causal_transition_count')==0 and roles.get('pass_real') is False,roles)
check('all_107_clue_anchors_remain_noncausal',len(topo.get('clue_scene_anchors',[]))==107 and all(x.get('causal_edge') is False for x in topo['clue_scene_anchors']))
# independently re-prove 324 from source refs/hashes
path=json.loads((SC7/'EXPLORATEUR_PATH_CLOSURE_324.json').read_text());lines=layout.read_text(encoding='utf-8').split('\n')
def rh(ref):
 bits=ref.split('_');a=int(bits[1][1:]);b=int(bits[2][1:]);return hashlib.sha256('\n'.join(lines[a-1:b]).encode()).hexdigest()
def hashes_match(rec):return [rh(r) for r in rec['source_refs']]==rec['source_hashes']
check('checkpoint324_start_hash_exact',hashes_match(path['start']))
check('checkpoint324_transition_hashes_exact',all(hashes_match(t) for t in path['transitions']))
evidence={'start':{'source_refs':path['start']['source_refs'],'source_hashes':path['start']['source_hashes']},'transitions':[{'transition_id':t['transition_id'],'source_refs':t['source_refs'],'source_hashes':t['source_hashes']} for t in path['transitions']]}
digest=hashlib.sha256(json.dumps(evidence,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
check('source_evidence_digest_exact',digest==Scenario7ReleaseGateV1.SOURCE_EVIDENCE_DIGEST_SHA256,digest)
proof=SourceBackedInvestigationPathV4.prove(path['start'],path['transitions'],path['terminal_scene'])
check('checkpoint324_path_reproved',proof.get('status')=='PROVED' and len(proof.get('transition_ids',[]))==10 and proof.get('promotion_applied') is False,proof)
check('generic_execution_ledger_exact',proof.get('executed_state',{}).get('transition_ledger')==[t['transition_id'] for t in path['transitions']])
check('zero_clue_anchor_edges_used',proof.get('clue_anchor_edges_used')==0 and path['anti_false_causality']['clue_scene_anchors_promoted_to_edges']==0)
check('no_specific_clue_anchor_required',all(not t.get('requires_specific_clue_anchor') and not t.get('derived_from_clue_anchor') for t in path['transitions']))
check('alternative_investigation_routes_preserved',path['anti_false_causality'].get('alternative_investigation_routes_preserved') is True)
# player isolation/projection
kp=GenericKnowledgePartition();kp.reveal('P1','PUBLIC_INVESTIGATION');kp.reveal('P2','OTHER')
check('knowledge_partition_isolated',kp.knows('P1','PUBLIC_INVESTIGATION') and not kp.knows('P2','PUBLIC_INVESTIGATION'))
fw=GenericKnowledgeFirewall.project([{'id':'PUBLIC_INVESTIGATION','partition':'PLAYER','text':'public'},{'id':'KEEPER_SOLUTION','partition':'KEEPER','source_refs':path['transitions'][5]['source_refs'],'source_hashes':path['transitions'][5]['source_hashes']}],'PLAYER')
check('keeper_evidence_not_projected',fw.get('status')=='PASS' and [x.get('id') for x in fw.get('records',[])]==['PUBLIC_INVESTIGATION'],fw)
public=SourceBackedInvestigationPathV4.player_safe_summary(proof)
check('player_safe_path_summary_no_keeper_provenance',set(public)=={'status','pass_real_candidate','path_length','promotion_applied','clue_anchor_edges_used'} and public['path_length']==10 and public['clue_anchor_edges_used']==0,public)
# certificate + tamper
certp=SC7/'EXPLORATEUR_PASS_REAL_RELEASE_325.json';cert=json.loads(certp.read_text());g=Scenario7ReleaseGateV1.validate_certificate(cert);check('release_certificate_gate_pass',g.get('status')=='PASS',g)
for name,mut,code in [
 ('tampered_parent_identity_fails_closed',lambda c:c.__setitem__('parent_checkpoint_git_blob_sha1','0'*40),'PARENT_CHECKPOINT_IDENTITY_MISMATCH'),
 ('tampered_path_identity_fails_closed',lambda c:c.__setitem__('checkpoint324_path_artifact_git_blob_sha1','0'*40),'PATH_ARTIFACT_IDENTITY_MISMATCH'),
 ('tampered_source_digest_fails_closed',lambda c:c.__setitem__('source_evidence_digest_sha256','0'*64),'SOURCE_EVIDENCE_DIGEST_MISMATCH'),
 ('clue_anchor_causality_fails_closed',lambda c:c.__setitem__('clue_anchor_edges_used',1),'CLUE_ANCHOR_CAUSALITY_FORBIDDEN'),
 ('historical_causality_rewrite_fails_closed',lambda c:c.__setitem__('historical_causal_transition_count',1),'HISTORICAL_CAUSALITY_REWRITE_FORBIDDEN'),
 ('specific_clue_requirement_fails_closed',lambda c:c.__setitem__('specific_clue_anchor_required',True),'SPECIFIC_CLUE_ANCHOR_REQUIREMENT_FORBIDDEN'),
 ('alternative_routes_collapse_fails_closed',lambda c:c.__setitem__('alternative_investigation_routes_preserved',False),'ALTERNATIVE_INVESTIGATION_ROUTES_COLLAPSED'),
 ('knowledge_leak_fails_closed',lambda c:c.__setitem__('player_keeper_leaks',1),'KNOWLEDGE_LEAK_PRESENT')]:
 bad=json.loads(json.dumps(cert));mut(bad);check(name,Scenario7ReleaseGateV1.validate_certificate(bad).get('code')==code)
# resolver fail-closed without cert; promote only with cert
hold=certp.with_suffix('.hold');certp.rename(hold)
try:before=MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates','scenario7')
finally:hold.rename(certp)
after=MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates','scenario7')
check('resolver_fails_closed_without_325_certificate',before.get('pass_real') is False and before.get('authority')=='EXPLORATEUR_INVESTIGATION_TOPOLOGY.json',before)
check('resolver_promotes_only_with_325_certificate',after.get('pass_real') is True and after.get('authority')=='EXPLORATEUR_PASS_REAL_RELEASE_325.json',after)
statuses={k:MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates',k) for k in ('scenario3','scenario4','scenario5','scenario6','scenario7')}
check('all_five_scenarios_pass_real_after_release',all(statuses[k].get('pass_real') is True for k in statuses),statuses)
ui=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates');rows={r['scenario_key']:r for r in ui.list_scenarios()['scenarios']};sel=ui.select('scenario7')
check('scenario7_selectable_after_release',rows['scenario7']['selectable'] is True and sel.get('status')=='SELECTED' and sel.get('code')=='SCENARIO_CERTIFIED',{'row':rows['scenario7'],'selection':sel})
check('player_selection_surface_no_keeper_evidence',set(sel['selection'])=={'scenario_key','title','certification_status'} and not any(x in json.dumps(sel).lower() for x in ('source_refs','source_hashes','keeper','judicial_conclusion','janet','diana')),sel)
passed=sum(x['status']=='PASS' for x in results)
report={'schema':'NATIVE_RUNTIME_CHUNK325_REPORT_V1','checkpoint_parent':324,'milestone':'SCENARIO7_PASS_REAL_RELEASE_AUDIT_V1','tests_total':len(results),'tests_passed':passed,'tests_failed':len(results)-passed,'status':'PASS' if passed==len(results) else 'FAIL','scenario7_release_status':'PASS_REAL' if passed==len(results) else 'BLOCKED','player_keeper_leaks':0,'clue_anchor_edges_used':0,'alternative_investigation_routes_preserved':True,'all_five_scenarios_pass_real':all(statuses[k].get('pass_real') is True for k in statuses),'next_phase':'MULTIPLAYER_SAVE_REPLAY_CERTIFICATION_V1','results':[{'name':x['name'],'status':x['status']} for x in results]}
(ROOT/'NATIVE_RUNTIME_CHUNK325_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['status']=='PASS' else 1)
