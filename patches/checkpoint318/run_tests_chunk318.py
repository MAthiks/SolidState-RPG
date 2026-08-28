import json, subprocess, sys
from pathlib import Path
from solidstate_runtime import (
    SafeTransitionRecoveryV1,
    StartCandidateEvidenceGate,
    TerminalOutcomeEvidenceGate,
    SourceBackedPathClosureV1,
)

ROOT = Path(__file__).resolve().parent
results=[]
def check(name, ok, detail=None):
    results.append({"name":name,"status":"PASS" if ok else "FAIL","detail":detail})

def rec(tid, frm, to, ref, h):
    return {
        "transition_id":tid,"from_scene":frm,"to_scene":to,
        "predicate":"SOURCE_CONDITION","effects":[{"type":"UNLOCK_SCENE","scene":to}],
        "authority":"EXPLICIT_SOURCE_TABLE_RELATION","relation":"LEADS_TO",
        "source_ref":ref,"source_sha256":h,"partition":"KEEPER",
        "target_binding_count":1,"explicit_source_language":True,
    }

start={
    "scene_id":"BRUME_NODE_MAIRIE",
    "source_ref":"PLAYER_P2_L8_L17",
    "source_sha256":"2beeb4fa844cfb34f4065660c6ef1547e6943e99e2cc0427b1ea96125733ae6e",
    "partition":"PLAYER_SAFE","availability":"AT_ARRIVAL","explicit_source_language":True,
}
check("defensible_player_start_candidate", StartCandidateEvidenceGate.validate(start)["status"]=="RESOLVED")
unsafe_start=dict(start); unsafe_start["partition"]="KEEPER"
check("keeper_only_start_rejected", StartCandidateEvidenceGate.validate(unsafe_start)["code"]=="START_NOT_PLAYER_SAFE")

mayor_to_gallery=rec(
    "BRUME_317_05","BRUME_NODE_MAIRIE","BRUME_NODE_GALERIE_WARD",
    "KEEPER_P3_L43","1453127d23b281a3948c209303d498361062d2a8804f64d3ae13a4b2f9952a95"
)
r=SafeTransitionRecoveryV1.recover([mayor_to_gallery])
check("mayor_to_gallery_safe_edge", r["safe_transition_count"]==1 and not r["pass_real_promotion"], r)

terminal={
    "transition_id":"BRUME_318_GALLERY_TO_MAREE_REFERMEE",
    "from_scene":"BRUME_NODE_GALERIE_WARD",
    "terminal_scene":"BRUME_TERMINAL_MAREE_REFERMEE",
    "predicate":{"type":"ALL","conditions":["GALLERY_FLOODED","BEFORE_19_OCT_05_17"]},
    "effects":[{"type":"SET_SCENARIO_OUTCOME","outcome":"TERMINAL_RESOLVED"}],
    "action_source_ref":"KEEPER_P5_L27",
    "action_source_sha256":"b1c7cc344852f4010180abb553e7de563fa06f2a6dba57e279a439d6a6d950c0",
    "outcome_source_ref":"KEEPER_P5_L42_L43",
    "outcome_source_sha256":"64128363d499419f33a4726fdfe660273a76f565ac214340a5f518e0ccd6ab86",
    "partition":"KEEPER","explicit_source_language":True,"target_binding_count":1,
}
check("explicit_gallery_action_terminal", TerminalOutcomeEvidenceGate.validate(terminal)["status"]=="RESOLVED")
bad_terminal=dict(terminal); bad_terminal["target_binding_count"]=2
check("ambiguous_terminal_rejected", TerminalOutcomeEvidenceGate.validate(bad_terminal)["code"]=="TERMINAL_TARGET_NOT_UNIQUE")

proof=SourceBackedPathClosureV1.prove(start, r["transitions"], terminal)
check("complete_start_to_terminal_path_proved", proof["status"]=="PROVED" and proof["pass_real_candidate"] and len(proof["transition_ids"])==2, proof)
check("path_executes_through_generic_transition_layer", proof.get("executed_state",{}).get("transition_ledger")==["BRUME_317_05","BRUME_318_GALLERY_TO_MAREE_REFERMEE"], proof.get("executed_state"))

no_edge=SourceBackedPathClosureV1.prove(start, [], terminal)
check("missing_middle_edge_fails_closed", no_edge["code"]=="NO_START_TO_TERMINAL_PATH")

public=SourceBackedPathClosureV1.player_safe_summary(proof)
check("player_safe_path_summary_has_no_keeper_graph", set(public)=={"status","pass_real_candidate","path_length","promotion_applied"} and public["path_length"]==2, public)

readiness=json.loads((ROOT/'scenario_candidates/scenario4/BRUME_RELEASE_READINESS.json').read_text(encoding='utf-8'))
check("preexisting_protected_release_checks_still_pass", all(v=="PASS" for v in readiness["checks"].values()), readiness["checks"])
check("path_proof_does_not_self_promote", proof["promotion_applied"] is False)

for script,name in [
    ('run_tests_chunk317.py','checkpoint317_regression'),
    ('run_tests_chunk316.py','checkpoint316_regression'),
    ('run_tests_chunk315.py','checkpoint315_regression'),
    ('run_tests.py','native_core_regression'),
]:
    p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True,text=True)
    check(name,p.returncode==0,{"returncode":p.returncode,"stdout_tail":p.stdout[-500:],"stderr_tail":p.stderr[-500:]})

passed=sum(x['status']=='PASS' for x in results)
report={
    "schema":"NATIVE_RUNTIME_CHUNK318_REPORT_V1",
    "checkpoint_parent":317,
    "milestone":"SCENARIO4_SOURCE_BACKED_PATH_CLOSURE_V1",
    "tests_total":len(results),"tests_passed":passed,"tests_failed":len(results)-passed,
    "status":"PASS" if passed==len(results) else "FAIL",
    "scenario4_path_status":"PASS_REAL_CANDIDATE" if passed==len(results) else "BLOCKED",
    "path_nodes": proof.get("path_nodes",[]),
    "transition_ids": proof.get("transition_ids",[]),
    "pass_real_promotion":False,
    "next_gate":"SCENARIO4_PASS_REAL_RELEASE_AUDIT_V1",
    "results":results,
}
(ROOT/'NATIVE_RUNTIME_CHUNK318_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['status']=='PASS' else 1)
