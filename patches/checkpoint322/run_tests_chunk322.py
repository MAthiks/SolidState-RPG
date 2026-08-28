import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from solidstate_runtime import (
    SourceStartEvidenceGateV3,ExplicitNarrativeTransitionGateV3,SourceBackedNarrativePathV3,
    MultiScenarioStatusResolver,ScenarioSelectionInterfaceV1,GenericKnowledgeFirewall,GenericKnowledgePartition,
)
ROOT=Path(__file__).resolve().parent
SC6=ROOT/'scenario_candidates/scenario6'
EVID=SC6/'MUSE_PATH_CLOSURE_322.json'
results=[]
def check(name,ok,detail=None):results.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

evidence=json.loads(EVID.read_text(encoding='utf-8'))
pdf_env=os.environ.get('MUSE_SOURCE_PDF')
pdf=Path(pdf_env) if pdf_env else Path('__MISSING_MUSE_SOURCE_PDF__')
check('source_pdf_present',pdf.exists(),str(pdf))
check('source_pdf_sha256_exact',pdf.exists() and sha(pdf)==evidence['source']['pdf_sha256'],sha(pdf) if pdf.exists() else None)
layout=SC6/'source_layout.txt'
check('source_layout_sha256_exact',sha(layout)==evidence['source']['source_layout_sha256'],sha(layout))
pre=json.loads((SC6/'SCENARIO6_MUSE_PREFLIGHT.json').read_text())
check('scenario6_preflight_pass',pre.get('status')=='PASS' and pre.get('physical_pages')==[42,56],pre)
roles=json.loads((SC6/'MUSE_SOURCE_ROLE_RECOVERY_V1.json').read_text())
check('historical_endpoints_recovered',roles.get('result')=='START_AND_TERMINAL_ROLES_RECOVERED_GRAPH_STILL_UNPROVEN' and roles.get('safe_transition_count')==0,roles)
freeze=json.loads((SC6/'MUSE_FREEZE_125.json').read_text())
check('historical_blocker_preserved',freeze.get('path_status')=='BLOCKED_NO_EXPLICIT_START_TO_TERMINAL_PATH' and freeze.get('pass_real') is False,freeze)
readiness=json.loads((SC6/'MUSE_RELEASE_READINESS.json').read_text())
check('historical_release_readiness_preserved',all(v=='PASS' for v in readiness.get('checks',{}).values()) and readiness.get('typed_transitions')==0 and readiness.get('pass_real') is False,readiness)

pages=layout.read_text(encoding='utf-8').split('\f')
def rh(ref):
 m=re.fullmatch(r'P(\d+)_L(\d+)_L(\d+)',ref)
 p,a,b=map(int,m.groups());text='\n'.join(pages[p-42].splitlines()[a-1:b]);return hashlib.sha256(text.encode()).hexdigest()
def hashes_match(rec):return all(rh(r)==h for r,h in zip(rec['source_refs'],rec['source_hashes']))
start=evidence['start'];route=evidence['transitions']
check('start_source_hashes_exact',hashes_match(start),start)
check('explicit_player_start_resolved',SourceStartEvidenceGateV3.validate(start).get('status')=='RESOLVED')
bad_start=json.loads(json.dumps(start));bad_start['partition']='KEEPER'
check('keeper_start_fails_closed',SourceStartEvidenceGateV3.validate(bad_start).get('code')=='START_NOT_PLAYER_SAFE')
check('all_route_source_hashes_exact',all(hashes_match(t) for t in route))
check('source_language_audit_attested',start.get('source_language_audit')=='MANUALLY_VERIFIED_EXPLICIT' and all(t.get('source_language_audit')=='MANUALLY_VERIFIED_EXPLICIT' for t in route))
missing_audit=json.loads(json.dumps(route[0]));missing_audit.pop('source_language_audit',None)
check('missing_language_audit_fails_closed',ExplicitNarrativeTransitionGateV3.validate(missing_audit).get('code')=='ROUTE_EVIDENCE_INCOMPLETE')
mat=[ExplicitNarrativeTransitionGateV3.materialize(t) for t in route]
check('all_six_transitions_materialized',len(mat)==6 and all(x.get('status')=='MATERIALIZED' for x in mat),mat)
proof=SourceBackedNarrativePathV3.prove(start,route,evidence['terminal_scene'])
check('complete_acti_to_conclusion_path_proved',proof.get('status')=='PROVED' and proof.get('pass_real_candidate') is True and len(proof.get('transition_ids',[]))==6,proof)
check('generic_execution_ledger_exact',proof.get('executed_state',{}).get('transition_ledger')==[t['transition_id'] for t in route],proof.get('executed_state'))
check('proof_does_not_self_promote',proof.get('promotion_applied') is False and evidence.get('pass_real') is False)
check('terminal_is_explicit_conditional_conclusion',route[-1]['relation']=='TERMINAL_CONSEQUENCE' and route[-1]['authority']=='EXPLICIT_CONCLUSION_CONDITION' and evidence['terminal_scene']=='MUSE_TERMINAL_ENMOUTEF_BODY_FUTURE')
bad=json.loads(json.dumps(route[0]));bad['explicit_source_language']=False
check('inferred_transition_fails_closed',ExplicitNarrativeTransitionGateV3.validate(bad).get('code')=='ROUTE_SOURCE_NOT_EXPLICIT')
amb=json.loads(json.dumps(route[3]));amb['target_binding_count']=2
check('ambiguous_target_fails_closed',ExplicitNarrativeTransitionGateV3.validate(amb).get('code')=='ROUTE_TARGET_NOT_UNIQUE')
editorial=json.loads(json.dumps(route[-1]));editorial['editorial_reference_only']=True
check('editorial_heading_alone_fails_closed',ExplicitNarrativeTransitionGateV3.validate(editorial).get('code')=='EDITORIAL_REFERENCE_IS_NOT_ROUTE')
public=SourceBackedNarrativePathV3.player_safe_summary(proof)
check('player_safe_summary_no_keeper_provenance',set(public)=={'status','pass_real_candidate','path_length','promotion_applied'} and public['path_length']==6,public)
kp=GenericKnowledgePartition();kp.reveal('P1','JUSTINE_LEAD');kp.reveal('P2','OTHER')
check('knowledge_partition_isolated',kp.knows('P1','JUSTINE_LEAD') and not kp.knows('P2','JUSTINE_LEAD'))
fw=GenericKnowledgeFirewall.project([
 {'id':'PUBLIC_START','partition':'PLAYER','text':'public'},
 {'id':'KEEPER_ACTIII','partition':'KEEPER','source_refs':['P54_L31_L38'],'source_hashes':[route[2]['source_hashes'][0]]}
],'PLAYER')
check('keeper_route_evidence_not_projected',fw.get('status')=='PASS' and [x.get('id') for x in fw.get('records',[])]==['PUBLIC_START'],fw)
statuses={k:MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates',k) for k in ('scenario3','scenario4','scenario5','scenario6','scenario7')}
check('status_boundary_3_4_5_pass_6_7_blocked',all(statuses[k]['pass_real'] for k in ('scenario3','scenario4','scenario5')) and all(not statuses[k]['pass_real'] for k in ('scenario6','scenario7')),statuses)
ui=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates')
rows={r['scenario_key']:r for r in ui.list_scenarios()['scenarios']}
sel=ui.select('scenario6')
check('scenario6_still_blocked_in_player_interface',rows['scenario6']['selectable'] is False and sel.get('status')=='BLOCKED' and sel.get('code')=='SCENARIO_NOT_CERTIFIED',{'row':rows['scenario6'],'selection':sel})
for script,name,extra in [
 ('run_tests_chunk321.py','checkpoint321_regression',{'ANTRE_SOURCE_PDF':"/mnt/data/antre.pdf"}),
 ('run_tests_chunk315.py','checkpoint315_regression',{}),
 ('run_tests.py','native_core_regression',{}),
]:
 env=os.environ.copy();env.update(extra)
 p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True,text=True,env=env)
 check(name,p.returncode==0,{'stdout':p.stdout[-800:],'stderr':p.stderr[-800:]})
passed=sum(x['status']=='PASS' for x in results)
report={'schema':'NATIVE_RUNTIME_CHUNK322_REPORT_V1','checkpoint_parent':321,'milestone':'SCENARIO6_SOURCE_BACKED_PATH_CLOSURE_V1','tests_total':len(results),'tests_passed':passed,'tests_failed':len(results)-passed,'status':'PASS' if passed==len(results) else 'FAIL','scenario6_path_status':'PASS_REAL_CANDIDATE' if passed==len(results) else 'BLOCKED','path_nodes':proof.get('path_nodes',[]),'transition_ids':proof.get('transition_ids',[]),'pass_real_promotion':False,'source_pdf_sha256_expected':evidence['source']['pdf_sha256'],'next_gate':'SCENARIO6_PASS_REAL_RELEASE_AUDIT_V1','results':[{'name':x['name'],'status':x['status']} for x in results]}
(ROOT/'NATIVE_RUNTIME_CHUNK322_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
