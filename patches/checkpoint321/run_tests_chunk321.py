import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from solidstate_runtime import GenericCoverageGate, GenericKnowledgePartition, GenericKnowledgeFirewall
from solidstate_runtime.source_backed_route_v2 import SourceBackedRouteProofV2
from solidstate_runtime.scenario5_release_gate import Scenario5ReleaseGateV1
from solidstate_runtime.multi_scenario_status_resolver import MultiScenarioStatusResolver
from solidstate_runtime.interface_v1 import ScenarioSelectionInterfaceV1
ROOT=Path(__file__).resolve().parent
SC5=ROOT/'scenario_candidates/scenario5'
results=[]
def check(name,ok,detail=None):results.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
pdf_env=os.environ.get('ANTRE_SOURCE_PDF')
pdf=Path(pdf_env) if pdf_env else Path('__MISSING_ANTRE_SOURCE_PDF__')
check('source_pdf_present',pdf.exists(),str(pdf))
check('source_pdf_sha256_exact',pdf.exists() and sha(pdf)==Scenario5ReleaseGateV1.SOURCE_PDF_SHA256,sha(pdf) if pdf.exists() else None)
layout=SC5/'source_layout.txt'
check('source_layout_sha256_exact',sha(layout)==Scenario5ReleaseGateV1.SOURCE_LAYOUT_SHA256,sha(layout))
validation=json.loads((SC5/'SCENARIO5_SOURCE_VALIDATION.json').read_text())
check('source_validation_pass',validation.get('status')=='PASS' and validation.get('source')=='antre.pdf',validation)
ledger=json.loads((ROOT/'ANTRE_SOURCE_COVERAGE_LEDGER.json').read_text())
cov=GenericCoverageGate.evaluate(ledger)
check('coverage_zero_open',cov.get('code')=='PASS_REAL' and cov.get('open')==0,cov)
check('coverage_ledger_sha_exact',sha(ROOT/'ANTRE_SOURCE_COVERAGE_LEDGER.json')=='2d7cb929f3325f84e734194ae78150ac8cbf15049edb61a7c8945de209b00ba3')
oldcert=json.loads((ROOT/'ANTRE_PASS_REAL_CERTIFICATE.json').read_text())
check('historical_cert_sha_exact',sha(ROOT/'ANTRE_PASS_REAL_CERTIFICATE.json')=='a7828c9d498a879d669d0a35ca98b5300d4c1a123e30c3e5846f78d41a991d16')
check('historical_cert_provenance_only',oldcert.get('qualification')=='PASS_REAL')
check('historical_build_sha_exact',sha(ROOT/'builds/ANTRE_PASS_REAL.build.zip')=='3fbe28764c12d443744188b88f2e53354827d1a83de12e985b290d4306e2825e')
check('source_first_pass_zip_sha_exact',sha(ROOT/'scenario_candidates/antre_abomination/ANTRE_SOURCE_FIRST_PASS.zip')=='ef759f5108f3d0292a69dae82c65302334baa47f6f899bc7546044f3f9e6551a')
pages=layout.read_text(encoding='utf-8').split('\f')
def rh(ref):
 m=re.fullmatch(r'P(\d+)_L(\d+)_L(\d+)',ref);p,a,b=map(int,m.groups());text='\n'.join(pages[p-1].splitlines()[a-1:b]);return hashlib.sha256(text.encode()).hexdigest()
start={'scene_id':'ANTRE_START_INVITATION_RECEIVED','source_refs':['P2_L9_L22'],'source_hashes':['79e22cf80c7a8bab7e81bb47ef2b6fa46f5974f16eaf2390b33813df24a37292'],'partition':'PLAYER_SAFE','availability':'AT_SCENARIO_START','explicit_source_language':True}
rows=[
('ANTRE_320_01_INVITATION_TO_YACHT','ANTRE_START_INVITATION_RECEIVED','ANTRE_YACHT_DEPARTURE','REQUIRED_TRAVEL','EXPLICIT_REQUIRED_TRAVEL',['P2_L26_L31'],['8048d4fedf5102cfa58db42ccfa0cde4d2fe79d1f0c8b4f479c9883f8a5552bb'],'PLAYER_SAFE'),
('ANTRE_320_02_YACHT_TO_ISLAND','ANTRE_YACHT_DEPARTURE','ANTRE_ISLAND_ARRIVAL','REQUIRED_TRAVEL','EXPLICIT_REQUIRED_TRAVEL',['P2_L26_L30','P2_L62_L64'],['46e1482d6594946ef6b7ea01394133f77e91e54f4a19a314ef6a7dfa73c579fb','79133c9746701400115dfa23e8ec2b96c03f6f715049fb8df8bd54d9fbafc947'],'PLAYER_SAFE'),
('ANTRE_320_03_ISLAND_TO_HOTEL','ANTRE_ISLAND_ARRIVAL','ANTRE_GOLDEN_HOTEL','SCHEDULED_TRANSFER','EXPLICIT_SCHEDULED_EVENT',['P3_L9_L15','P3_L47_L60'],['c670083d942b9ad97e5ba984c2d677c292f3b7cb7d4702abd2055b3e96933f43','8339464fa8cb1a64eca9e18c5e828de054a44b31cdea393161b0ce881b64eb95'],'PLAYER_SAFE'),
('ANTRE_320_04_HOTEL_TO_CASINO','ANTRE_GOLDEN_HOTEL','ANTRE_CASINO_EVENING','SCHEDULED_TRANSFER','EXPLICIT_SCHEDULED_EVENT',['P13_L55_L60'],['2a9382b36c0c50e83f77609c39a8ba4e85da7c326af0e98587ac8d721b8ac59b'],'PLAYER_SAFE'),
('ANTRE_320_05_CASINO_TO_MASKS','ANTRE_CASINO_EVENING','ANTRE_MASKS_AVAILABLE','TIMED_EVENT','EXPLICIT_TIMED_EVENT',['P15_L33_L47'],['247199b2a1f3af4ba70935a0385449d1676d09a6a9505bc0f6327236da1ae9dc'],'KEEPER'),
('ANTRE_320_06_MASKS_TO_GAS_SURVIVAL','ANTRE_MASKS_AVAILABLE','ANTRE_GAS_EVENT_SURVIVED','TIMED_EVENT','EXPLICIT_TIMED_EVENT',['P15_L48_L63'],['0c9b08065762447d0cd963da12a08af53e86c750c66896f84fd3c1408e65b489'],'KEEPER'),
('ANTRE_320_07_GAS_TO_INTERVENTION','ANTRE_GAS_EVENT_SURVIVED','ANTRE_INTERVENE_PONCTION','PLAYER_OPTION','EXPLICIT_PLAYER_OPTION',['P15_L20_L30','P16_L1_L11'],['f78ab45294940e526441b48fcc8a7b5703fadae37fbbc83608a4443f2f43c733','9a98c0343662d0c045d317f5e4848d6a6ad399578082f771e0c4e15f1ae7261d'],'KEEPER'),
('ANTRE_320_08_INTERVENTION_TO_CAPTURE','ANTRE_INTERVENE_PONCTION','ANTRE_CAPTURED','CONDITIONAL_CAPTURE','EXPLICIT_CONDITIONAL_CONSEQUENCE',['P16_L1_L18'],['ce5340c61ed6c949fa5cda24cc913f94d05862aba33f0d8e299a1a68b2d4e403'],'KEEPER'),
('ANTRE_320_09_CAPTURE_TO_REVIVAL','ANTRE_CAPTURED','ANTRE_REANIMATED_SURVIVORS','CONDITIONAL_REVIVAL','EXPLICIT_CONDITIONAL_SEQUENCE',['P16_L8_L23'],['a176a69df2cc9d3362be093cad075a28fb8dfd9e697ce8b2a20c671743fd866e'],'KEEPER'),
('ANTRE_320_10_REVIVAL_TO_EPILOGUE','ANTRE_REANIMATED_SURVIVORS','ANTRE_EPILOGUE_OPEN_KEEPER_RESOLUTION','TERMINAL_HANDOFF','EXPLICIT_EPILOGUE_DEPENDENCY',['P16_L13_L28','P17_L17_L31'],['c352a7889ee28e4557cddc38dd63d22d63babe90dd6ee86f6ae8554b417c656c','e1366a4e82070b9f7751db7753ef91689b30eabef6acc971eb4e04299adfcfaf'],'KEEPER')]
trs=[]
for tid,fr,to,rel,auth,refs,hashes,part in rows:
 trs.append({'transition_id':tid,'from_scene':fr,'to_scene':to,'predicate':{'type':'SOURCE_CONDITION'},'effects':[{'type':'UNLOCK_SCENE','scene':to}],'relation':rel,'authority':auth,'source_refs':refs,'source_hashes':hashes,'partition':part,'target_binding_count':1,'explicit_source_language':True})
check('checkpoint320_start_hash_exact',all(rh(r)==h for r,h in zip(start['source_refs'],start['source_hashes'])))
check('checkpoint320_route_hashes_exact',all(all(rh(r)==h for r,h in zip(t['source_refs'],t['source_hashes'])) for t in trs))
proof=SourceBackedRouteProofV2.prove(start,trs,'ANTRE_EPILOGUE_OPEN_KEEPER_RESOLUTION')
check('checkpoint320_path_reproved',proof.get('status')=='PROVED' and len(proof.get('transition_ids',[]))==10 and proof.get('promotion_applied') is False,proof)
kp=GenericKnowledgePartition();kp.reveal('P1','PUBLIC_INVITATION');kp.reveal('P2','OTHER_FACT')
check('knowledge_partition_isolated',kp.knows('P1','PUBLIC_INVITATION') and not kp.knows('P2','PUBLIC_INVITATION'))
fw=GenericKnowledgeFirewall.project([{'id':'PUBLIC_INVITATION','partition':'PLAYER','text':'public'},{'id':'KEEPER_ROUTE','partition':'KEEPER','keeper_text_internal':'secret','source_refs':['P15_L33_L47']}],'PLAYER')
check('keeper_records_not_projected_to_player',fw.get('status')=='PASS' and [x.get('id') for x in fw.get('records',[])]==['PUBLIC_INVITATION'],fw)
certp=SC5/'ANTRE_PASS_REAL_RELEASE_321.json';cert=json.loads(certp.read_text())
g=Scenario5ReleaseGateV1.validate_certificate(cert)
check('release_certificate_gate_pass',g.get('status')=='PASS',g)
bad=json.loads(json.dumps(cert));bad['parent_checkpoint_record_sha256']='0'*64
check('tampered_parent_hash_fails_closed',Scenario5ReleaseGateV1.validate_certificate(bad).get('code')=='PARENT_CHECKPOINT_HASH_MISMATCH')
bad=json.loads(json.dumps(cert));bad['player_keeper_leaks']=1
check('knowledge_leak_fails_closed',Scenario5ReleaseGateV1.validate_certificate(bad).get('code')=='KNOWLEDGE_LEAK_PRESENT')
bad=json.loads(json.dumps(cert));bad['historical_pass_real_certificate_reactivated']=True
check('historical_cert_reactivation_fails_closed',Scenario5ReleaseGateV1.validate_certificate(bad).get('code')=='HISTORICAL_CERTIFICATE_REACTIVATION_FORBIDDEN')
hold=certp.with_suffix('.hold');certp.rename(hold)
try:before=MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates','scenario5')
finally:hold.rename(certp)
after=MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates','scenario5')
check('resolver_fails_closed_without_321_certificate',before.get('pass_real') is False and before.get('authority')=='ANTRE_PATH_PROOF_V2.json',before)
check('resolver_promotes_only_with_321_certificate',after.get('pass_real') is True and after.get('authority')=='ANTRE_PASS_REAL_RELEASE_321.json',after)
statuses={k:MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates',k) for k in ('scenario3','scenario4','scenario5','scenario6','scenario7')}
check('status_regression_3_4_5_pass_6_7_blocked',all(statuses[k]['pass_real'] for k in ('scenario3','scenario4','scenario5')) and all(not statuses[k]['pass_real'] for k in ('scenario6','scenario7')),statuses)
ui=ScenarioSelectionInterfaceV1(ROOT/'scenario_candidates')
rows={r['scenario_key']:r for r in ui.list_scenarios()['scenarios']};sel=ui.select('scenario5')
check('scenario5_selectable_after_release',rows['scenario5']['selectable'] is True and sel.get('status')=='SELECTED' and sel.get('code')=='SCENARIO_CERTIFIED',{'row':rows['scenario5'],'selection':sel})
check('player_selection_surface_no_keeper_evidence',set(sel['selection'])=={'scenario_key','title','certification_status'} and not any(x in json.dumps(sel).lower() for x in ('source_refs','source_hashes','keeper_route')),sel)
p=subprocess.run([sys.executable,str(ROOT/'run_pass_real_audit_antre.py')],cwd=ROOT,capture_output=True,text=True)
check('independent_antre_audit_15_15',p.returncode==0 and '15/15 PASS' in p.stdout,p.stdout[-800:])
for script,name in [('run_tests_chunk315.py','checkpoint315_regression'),('run_tests.py','native_core_regression')]:
 p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True,text=True);check(name,p.returncode==0,{'stdout':p.stdout[-500:],'stderr':p.stderr[-500:]})
passed=sum(x['status']=='PASS' for x in results)
report={'schema':'NATIVE_RUNTIME_CHUNK321_REPORT_V1','checkpoint_parent':320,'milestone':'SCENARIO5_PASS_REAL_RELEASE_AUDIT_V1','tests_total':len(results),'tests_passed':passed,'tests_failed':len(results)-passed,'status':'PASS' if passed==len(results) else 'FAIL','scenario5_release_status':'PASS_REAL' if passed==len(results) else 'BLOCKED','player_keeper_leaks':0,'historical_pass_real_certificate_reactivated':False,'next_phase':'SCENARIO6_SOURCE_BACKED_PATH_CLOSURE_V1','results':[{'name':x['name'],'status':x['status']} for x in results]}
(ROOT/'NATIVE_RUNTIME_CHUNK321_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
