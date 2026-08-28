import hashlib, json, subprocess, sys
from pathlib import Path
from solidstate_runtime import (
    SourceStartEvidenceGateV2, ExplicitRouteTransitionGateV2, SourceBackedRouteProofV2,
    MultiScenarioStatusResolver, ScenarioSelectionInterfaceV1, PlayerInterfaceV1, LaunchChainV1,
)

ROOT=Path(__file__).resolve().parent
SC5=ROOT/'scenario_candidates/scenario5'
EVID=ROOT/'patches/checkpoint320/ANTRE_PATH_CLOSURE_320.json'
results=[]
def check(name, ok, detail=None):
    results.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})

evidence=json.loads(EVID.read_text(encoding='utf-8'))
layout=SC5/'source_layout.txt'
layout_sha=hashlib.sha256(layout.read_bytes()).hexdigest()
check('source_layout_identity_exact', layout_sha==evidence['source']['source_layout_sha256'], {'actual':layout_sha,'expected':evidence['source']['source_layout_sha256']})

validation=json.loads((SC5/'SCENARIO5_SOURCE_VALIDATION.json').read_text(encoding='utf-8'))
check('scenario5_source_validation_preserved', validation.get('status')=='PASS' and validation.get('source')=='antre.pdf', validation)
old=json.loads((SC5/'ANTRE_PATH_PROOF_V2.json').read_text(encoding='utf-8'))
check('historical_blocker_preserved_as_provenance', old.get('status')=='BLOCKED_NO_EXPLICIT_START_TO_TERMINAL_PATH' and old.get('explicit_starts')==[], old)

pages=layout.read_text(encoding='utf-8').split('\f')
def ref_hash(ref):
    # Pn_La_Lb
    p,a,b=[int(x) for x in ref.replace('P','').replace('L','').split('_') if x]
    text='\n'.join(pages[p-1].splitlines()[a-1:b])
    return hashlib.sha256(text.encode()).hexdigest()
def hashes_match(record):
    return [ref_hash(r) for r in record['source_refs']]==record['source_hashes']

start=evidence['start']
check('start_source_hashes_exact', hashes_match(start), start)
check('explicit_invitation_start_resolved', SourceStartEvidenceGateV2.validate(start).get('status')=='RESOLVED', start)
bad_start=json.loads(json.dumps(start)); bad_start['partition']='KEEPER'
check('keeper_only_start_fails_closed', SourceStartEvidenceGateV2.validate(bad_start).get('code')=='START_NOT_PLAYER_SAFE')

route=evidence['transitions']
check('all_route_source_hashes_exact', all(hashes_match(r) for r in route))
mat=[ExplicitRouteTransitionGateV2.materialize(x) for x in route]
check('all_ten_route_edges_source_admitted', all(x.get('status')=='MATERIALIZED' for x in mat) and len(mat)==10, mat)
proof=SourceBackedRouteProofV2.prove(start,route,evidence['terminal_scene'])
check('complete_invitation_to_epilogue_path_proved', proof.get('status')=='PROVED' and proof.get('pass_real_candidate') is True and len(proof.get('transition_ids',[]))==10, proof)
check('generic_execution_ledger_exact', proof.get('executed_state',{}).get('transition_ledger')==[x['transition_id'] for x in route], proof.get('executed_state'))
check('proof_does_not_self_promote', proof.get('promotion_applied') is False and evidence.get('pass_real') is False)
check('terminal_is_source_authorized_open_keeper_resolution', evidence['terminal_scene']=='ANTRE_EPILOGUE_OPEN_KEEPER_RESOLUTION' and route[-1]['relation']=='TERMINAL_HANDOFF' and route[-1]['authority']=='EXPLICIT_EPILOGUE_DEPENDENCY')

bad=json.loads(json.dumps(route[4])); bad['explicit_source_language']=False
check('inferred_event_fails_closed', ExplicitRouteTransitionGateV2.validate(bad).get('code')=='ROUTE_SOURCE_NOT_EXPLICIT')
amb=json.loads(json.dumps(route[7])); amb['target_binding_count']=2
check('ambiguous_capture_target_fails_closed', ExplicitRouteTransitionGateV2.validate(amb).get('code')=='ROUTE_TARGET_NOT_UNIQUE')
editorial=json.loads(json.dumps(route[9])); editorial['editorial_reference_only']=True
check('editorial_epilogue_reference_not_enough', ExplicitRouteTransitionGateV2.validate(editorial).get('code')=='EDITORIAL_REFERENCE_IS_NOT_ROUTE')
public=SourceBackedRouteProofV2.player_safe_summary(proof)
check('player_safe_summary_contains_no_keeper_provenance', set(public)=={'status','pass_real_candidate','path_length','promotion_applied'} and public['path_length']==10, public)

historical_cert=json.loads((ROOT/'ANTRE_PASS_REAL_CERTIFICATE.json').read_text(encoding='utf-8'))
resolved5=MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates','scenario5')
check('historical_pass_real_certificate_not_current_release_authority', historical_cert.get('qualification')=='PASS_REAL' and resolved5.get('pass_real') is False and resolved5.get('authority')=='ANTRE_PATH_PROOF_V2.json')
statuses={k:MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates',k) for k in ('scenario3','scenario4','scenario5','scenario6','scenario7')}
check('current_status_boundary_preserved', statuses['scenario3']['pass_real'] is True and statuses['scenario4']['pass_real'] is True and all(statuses[k]['pass_real'] is False for k in ('scenario5','scenario6','scenario7')), statuses)
check('checkpoint316_interface_exports_restored', all(x is not None for x in (ScenarioSelectionInterfaceV1,PlayerInterfaceV1,LaunchChainV1)))

for script,name in [
 ('run_tests_chunk319.py','checkpoint319_current_overlay_regression'),
 ('run_tests_chunk315.py','checkpoint315_core_regression'),
 ('run_tests.py','native_core_regression'),
]:
 p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True,text=True)
 check(name,p.returncode==0,{'returncode':p.returncode,'stdout_tail':p.stdout[-500:],'stderr_tail':p.stderr[-500:]})

passed=sum(x['status']=='PASS' for x in results)
report={
 'schema':'NATIVE_RUNTIME_CHUNK320_REPORT_V1','checkpoint_parent':319,
 'milestone':'SCENARIO5_SOURCE_BACKED_PATH_CLOSURE_V1',
 'tests_total':len(results),'tests_passed':passed,'tests_failed':len(results)-passed,
 'status':'PASS' if passed==len(results) else 'FAIL',
 'scenario5_path_status':'PASS_REAL_CANDIDATE' if passed==len(results) else 'BLOCKED',
 'path_nodes':proof.get('path_nodes',[]),'transition_ids':proof.get('transition_ids',[]),
 'pass_real_promotion':False,'historical_pass_real_certificate_reactivated':False,
 'source_pdf_sha256_expected':evidence['source']['pdf_sha256'],
 'next_gate':'SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1',
 'results':results,
}
(ROOT/'NATIVE_RUNTIME_CHUNK320_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
