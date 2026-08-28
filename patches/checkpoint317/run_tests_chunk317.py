import hashlib, json, subprocess, sys
from pathlib import Path
from solidstate_runtime import SafeTransitionEvidenceGate, SafeTransitionRecoveryV1

ROOT=Path(__file__).resolve().parent
results=[]
def check(name, ok, detail=None):
    results.append({"name":name,"status":"PASS" if ok else "FAIL","detail":detail})

def rec(tid, frm, to, ref, h, relation, authority, predicate="SOURCE_CONDITION"):
    return {"transition_id":tid,"from_scene":frm,"to_scene":to,"predicate":predicate,
            "effects":[{"type":"UNLOCK_SCENE","scene":to}],"authority":authority,
            "relation":relation,"source_ref":ref,"source_sha256":h,"partition":"KEEPER",
            "target_binding_count":1,"explicit_source_language":True}

brume=[
 rec("BRUME_317_01","BRUME_NODE_MAISON_BELL","BRUME_NODE_EGLISE","KEEPER_P3_L27","c00f21fcc3e1ec36cea7213a5aa0204418e005f06b7a1b3471bba0bc7d938136","LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"),
 rec("BRUME_317_02","BRUME_NODE_MAISON_BELL","BRUME_NODE_CIMETIERE","KEEPER_P3_L27","c00f21fcc3e1ec36cea7213a5aa0204418e005f06b7a1b3471bba0bc7d938136","LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"),
 rec("BRUME_317_03","BRUME_NODE_MAIRIE","BRUME_NODE_BANQUE","KEEPER_P3_L29","6349fc2db6af38dc04f1f9aeeff0fd6977d30b4a47e79c636714c6379394b712","LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"),
 rec("BRUME_317_04","BRUME_NODE_MAIRIE","BRUME_NODE_DEPOT","KEEPER_P3_L29","6349fc2db6af38dc04f1f9aeeff0fd6977d30b4a47e79c636714c6379394b712","LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"),
 rec("BRUME_317_05","BRUME_NODE_MAIRIE","BRUME_NODE_GALERIE_WARD","KEEPER_P3_L29","6349fc2db6af38dc04f1f9aeeff0fd6977d30b4a47e79c636714c6379394b712","LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"),
 rec("BRUME_317_06","BRUME_NODE_EGLISE","BRUME_NODE_CIMETIERE","KEEPER_P3_L31","a790a40a51fc642fd541df9a5a6ae39e60af81903a7b862a2a48da61d3450d17","LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"),
 rec("BRUME_317_07","BRUME_NODE_DEPOT","BRUME_NODE_TRAIN","KEEPER_P3_L37","8835ab6969af36d086fc22d2d0afca7c162bff9b84b50c8fa586d8d7fbb4e792","LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"),
 rec("BRUME_317_08","BRUME_NODE_DEPOT","BRUME_NODE_GALERIE_WARD","KEEPER_P3_L37","8835ab6969af36d086fc22d2d0afca7c162bff9b84b50c8fa586d8d7fbb4e792","LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"),
]
r4=SafeTransitionRecoveryV1.recover(brume)
check("scenario4_explicit_leads_to_edges", r4["safe_transition_count"]==8 and not r4["pass_real_promotion"], r4)

antre=rec("ANTRE_TX_1","P11_L4","P19_L18","P11_L14","3f3c4b1fab575f4f6f1ed57256498a785459313a45cde8fd85485ff0916fae1e","CONDITIONAL_REDIRECT","EXPLICIT_CONDITION_PLUS_UNIQUE_TARGET")
r5=SafeTransitionRecoveryV1.recover([antre])
check("scenario5_existing_exact_transition_admitted", r5["safe_transition_count"]==1 and not r5["pass_real_promotion"], r5)

muse_text='\n'.join((ROOT/'scenario_candidates/scenario6/source_layout.txt').read_text(encoding='utf-8').splitlines()[581:590])
muse_hash=hashlib.sha256(muse_text.encode()).hexdigest()
muse=rec("MUSE_317_ACT1_TO_ACT2","MUSE_ROLE_ACT_I","MUSE_ROLE_ACT_II","SOURCE_LAYOUT_L582_L590",muse_hash,"SECTION_HANDOFF","EXPLICIT_SECTION_HANDOFF","JUSTINE_DELORME_LOCATED")
r6=SafeTransitionRecoveryV1.recover([muse])
check("scenario6_explicit_act_handoff", r6["safe_transition_count"]==1 and not r6["pass_real_promotion"], r6)

r7=SafeTransitionRecoveryV1.recover([])
check("scenario7_anchors_do_not_become_causal_edges", r7["safe_transition_count"]==0 and r7["status"]=="NO_SAFE_TRANSITIONS", r7)

bad=rec("BAD_REF","A","B","X","0"*64,"LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION")
bad["editorial_reference_only"]=True
check("editorial_reference_blocked", SafeTransitionEvidenceGate.validate(bad)["code"]=="EDITORIAL_REFERENCE_IS_NOT_CAUSALITY")
amb=rec("BAD_AMBIG","A","B","X","0"*64,"LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"); amb["target_binding_count"]=2
check("ambiguous_target_blocked", SafeTransitionEvidenceGate.validate(amb)["code"]=="TARGET_BINDING_NOT_UNIQUE")
implicit=rec("BAD_INFER","A","B","X","0"*64,"LEADS_TO","EXPLICIT_SOURCE_TABLE_RELATION"); implicit["explicit_source_language"]=False
check("inferred_transition_blocked", SafeTransitionEvidenceGate.validate(implicit)["code"]=="SOURCE_LANGUAGE_NOT_EXPLICIT")

pub=SafeTransitionRecoveryV1.player_safe_provenance(r4)
check("keeper_text_not_exposed", all(set(x)<= {"transition_id","source_ref","source_sha256","relation"} for x in pub["provenance"]), pub)

from solidstate_runtime import MultiScenarioStatusResolver
statuses={k:MultiScenarioStatusResolver.resolve(ROOT/'scenario_candidates',k) for k in ['scenario3','scenario4','scenario5','scenario6','scenario7']}
check("scenario_status_invariants", statuses['scenario3']['pass_real'] is True and all(not statuses[k]['pass_real'] for k in ['scenario4','scenario5','scenario6','scenario7']), statuses)

for script,name in [('run_tests_chunk316.py','checkpoint316_regression'),('run_tests_chunk315.py','checkpoint315_regression'),('run_tests.py','native_core_regression')]:
    p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True,text=True)
    check(name,p.returncode==0,{"returncode":p.returncode,"stdout_tail":p.stdout[-500:],"stderr_tail":p.stderr[-500:]})

passed=sum(x['status']=='PASS' for x in results)
report={"schema":"NATIVE_RUNTIME_CHUNK317_REPORT_V1","checkpoint_parent":316,
        "milestone":"SAFE_TRANSITION_RECOVERY_FROM_EXPLICIT_SOURCE_LANGUAGE_V1",
        "tests_total":len(results),"tests_passed":passed,"tests_failed":len(results)-passed,
        "status":"PASS" if passed==len(results) else "FAIL",
        "scenario_recovery":{"scenario4_safe_transitions":8,"scenario5_safe_transitions":1,"scenario6_safe_transitions":1,"scenario7_safe_transitions":0},
        "pass_real_promotions":0,"results":results}
(ROOT/'NATIVE_RUNTIME_CHUNK317_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
