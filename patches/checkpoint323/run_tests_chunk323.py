import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from solidstate_runtime import GenericKnowledgePartition,GenericKnowledgeFirewall
from solidstate_runtime.source_backed_route_v3 import SourceBackedNarrativePathV3
from solidstate_runtime.scenario6_release_gate import Scenario6ReleaseGateV1
from solidstate_runtime.multi_scenario_status_resolver import MultiScenarioStatusResolver
from solidstate_runtime.interface_v1 import ScenarioSelectionInterfaceV1
ROOT=Path(__file__).resolve().parent;SC6=ROOT/'scenario_candidates/scenario6';results=[]
def check(name,ok,detail=None):results.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# exact external source identity
pdf=Path(os.environ.get('MUSE_SOURCE_PDF','__MISSING_MUSE_SOURCE_PDF__'))
check('source_pdf_present',pdf.exists(),str(pdf));check('source_pdf_sha256_exact',pdf.exists() and sha(pdf)==Scenario6ReleaseGateV1.SOURCE_PDF_SHA256,sha(pdf) if pdf.exists() else None)
layout=SC6/'source_layout.txt';check('source_layout_sha256_exact',sha(layout)==Scenario6ReleaseGateV1.SOURCE_LAYOUT_SHA256,sha(layout))
pre=json.loads((SC6/'SCENARIO6_MUSE_PREFLIGHT.json').read_text());check('source_preflight_pass',pre.get('status')=='PASS' and all(v=='PASS' for v in pre.get('gates',{}).values()),pre)
ready=json.loads((SC6/'MUSE_RELEASE_READINESS.json').read_text());check('historical_release_readiness_support_pass',all(v=='PASS' for v in ready.get('checks',{}).values()) and ready.get('pass_real') is False,ready)
freeze=json.loads((SC6/'MUSE_FREEZE_125.json').read_text());check('historical_freeze_preserved_as_provenance',freeze.get('pass_real') is False and freeze.get('path_status')=='BLOCKED_NO_EXPLICIT_START_TO_TERMINAL_PATH',freeze)
# independently re-prove checkpoint322 from stored source refs/hashes
path=json.loads((SC6/'MUSE_PATH_CLOSURE_322.json').read_text());pages=layout.read_text(encoding='utf-8').split('\f')
def rh(ref):
 m=re.fullmatch(r'P(\d+)_L(\d+)_L(\d+)',ref);p,a,b=map(int,m.groups());text='\n'.join(pages[p-42].splitlines()[a-1:b]);return hashlib.sha256(text.encode()).hexdigest()
def hashes_match(rec):return all(rh(r)==h for r,h in zip(rec['source_refs'],rec['source_hashes']))
check('checkpoint322_start_hashes_exact',hashes_match(path['start']))
check('checkpoint322_route_hashes_exact',all(hashes_match(t) for t in path['transitions']))
proof=SourceBackedNarrativePathV3.prove(path['start'],path['transitions'],path['terminal_scene'])
check('checkpoint322_path_reproved',proof.get('status')=='PROVED' and len(proof.get('transition_ids',[]))==6 and proof.get('promotion_applied') is False,proof)
check('generic_execution_ledger_exact',proof.get('executed_state',{}).get('transition_ledger')==[t['transition_id'] for t in path['transitions']],proof.get('executed_state'))
check('conditional_path_and_alternatives_preserved',path.get('policy','').startswith('One conditional') and path.get('pass_real') is False and path['transitions'][2]['relation']=='CONDITIONAL_ACT_HANDOFF' and path['transitions'][4]['relation']=='CONDITIONAL_OUTCOME')
# firewall / projection
kp=GenericKnowledgePartition();kp.reveal('P1','PUBLIC_START');kp.reveal('P2','OTHER');check('knowledge_partition_isolated',kp.knows('P1','PUBLIC_START') and not kp.knows('P2','PUBLIC_START'))
fw=GenericKnowledgeFirewall.project([{'id':'PUBLIC_START','partition':'PLAYER','text':'public'},{'id':'KEEPER_ACTIII','partition':'KEEPER','source_refs':path['transitions'][2]['source_refs'],'source_hashes':path['transitions'][2]['source_hashes']}],'PLAYER')
check('keeper_evidence_not_projected',fw.get('status')=='PASS' and [x.get('id') for x in fw.get('records',[])]==['PUBLIC_START'],fw)
public=SourceBackedNarrativePathV3.player_safe_summary(proof);check('player_safe_path_summary_no_keeper_provenance',set(public)=={'status','pass_real_candidate','path_length','promotion_applied'} and public['path_length']==6,public)
# certificate + tamper tests
certp=SC6/'MUSE_PASS_REAL_RELEASE_323.json';cert=json.loads(certp.read_text());g=Scenario6ReleaseGateV1.validate_certificate(cert);check('release_certificate_gate_pass',g.get('status')=='PASS',g)
for name,mut,code in [
 ('tampered_parent_identity_fails_closed',lambda c:c.__setitem__('parent_checkpoint_git_blob_sha1','0'*40),'PARENT_CHECKPOINT_IDENTITY_MISMATCH'),
 ('tampered_path_identity_fails_closed',lambda c:c.__setitem__('checkpoint322_path_artifact_git_blob_sha1','0'*40),'PATH_ARTIFACT_IDENTITY_MISMATCH'),
 ('knowledge_leak_fails_closed',lambda c:c.__setitem__('player_keeper_leaks',1),'KNOWLEDGE_LEAK_PRESENT'),
 ('collapsed_alternative_endings_fail_closed',lambda c:c.__setitem__('alternative_endings_preserved',False),'ALTERNATIVE_ENDINGS_COLLAPSED'),
 ('collapsed_open_conclusion_fails_closed',lambda c:c.__setitem__('open_conclusion_not_collapsed',False),'OPEN_CONCLUSION_COLLAPSED'),
 ('historical_freeze_reactivation_fails_closed',lambda c:c.__setitem__('historical_freeze_reactivated',True),'HISTORICAL_FREEZE_REACTIVATION_FORBIDDEN'),
 ('tampered_source_evidence_fails_closed',lambda c:c['source_evidence'].__setitem__('terminal_slice_sha256','0'*64),'SOURCE_EVIDENCE_HASH_MISMATCH')]:
 bad=json.loads(json.dumps(cert));mut(bad);check(name,Scenario6ReleaseGateV1.validate_certificate(bad).get('code')==code)
# resolver must fail closed without cert and promote only with 323 cert
hold=certp.with_suffix('.hold');certp.rename(hold)
try: before=MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates','scenario6')
finally: hold.rename(certp)
after=MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates','scenario6')
check('resolver_fails_closed_without_323_certificate',before.get('pass_real') is False and before.get('authority')=='MUSE_FREEZE_125.json',before)
check('resolver_promotes_only_with_323_certificate',after.get('pass_real') is True and after.get('authority')=='MUSE_PASS_REAL_RELEASE_323.json',after)
statuses={k:MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates',k) for k in ('scenario3','scenario4','scenario5','scenario6','scenario7')}
check('status_regression_3_4_5_6_pass_7_blocked',all(statuses[k]['pass_real'] for k in ('scenario3','scenario4','scenario5','scenario6')) and statuses['scenario7']['pass_real'] is False,statuses)
ui=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates');rows={r['scenario_key']:r for r in ui.list_scenarios()['scenarios']};sel=ui.select('scenario6')
check('scenario6_selectable_after_release',rows['scenario6']['selectable'] is True and sel.get('status')=='SELECTED' and sel.get('code')=='SCENARIO_CERTIFIED',{'row':rows['scenario6'],'selection':sel})
check('player_selection_surface_no_keeper_evidence',set(sel['selection'])=={'scenario_key','title','certification_status'} and not any(x in json.dumps(sel).lower() for x in ('source_refs','source_hashes','keeper','enmoutef_body_future')),sel)
# parent 322 is verified separately in frozen environment; current core regressions remain required
parent=Path('/mnt/data/ss322_parent_frozen')
for script,name,cwd,extra in [('run_tests_chunk321.py','checkpoint321_isolated_regression',parent,{'ANTRE_SOURCE_PDF':'/mnt/data/antre.pdf'}),('run_tests_chunk322.py','checkpoint322_isolated_regression',parent,{'MUSE_SOURCE_PDF':os.environ.get('MUSE_SOURCE_PDF','')}),('run_tests_chunk315.py','checkpoint315_regression',ROOT,{}),('run_tests.py','native_core_regression',ROOT,{})]:
 env=os.environ.copy();env.update(extra);p=subprocess.run([sys.executable,str(cwd/script)],cwd=cwd,capture_output=True,text=True,env=env);check(name,p.returncode==0,{'stdout':p.stdout[-500:],'stderr':p.stderr[-500:]})
passed=sum(x['status']=='PASS' for x in results)
report={'schema':'NATIVE_RUNTIME_CHUNK323_REPORT_V1','checkpoint_parent':322,'milestone':'SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1','tests_total':len(results),'tests_passed':passed,'tests_failed':len(results)-passed,'status':'PASS' if passed==len(results) else 'FAIL','scenario6_release_status':'PASS_REAL' if passed==len(results) else 'BLOCKED','player_keeper_leaks':0,'conditional_path_preserved':True,'alternative_endings_preserved':True,'open_conclusion_not_collapsed':True,'next_phase':'SCENARIO7_SOURCE_BACKED_PATH_CLOSURE_V1','results':[{'name':x['name'],'status':x['status']} for x in results]}
(ROOT/'NATIVE_RUNTIME_CHUNK323_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['status']=='PASS' else 1)
