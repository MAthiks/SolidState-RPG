import json, subprocess, sys
from pathlib import Path
from solidstate_runtime import (
    SafeTransitionRecoveryV1, SourceBackedPathClosureV1,
    ScenarioSelectionInterfaceV1, Scenario4ReleaseGateV1,
    MultiScenarioStatusResolver, AntiFalsePromotionGate, CertificationEligibilityGate,
)

ROOT=Path(__file__).resolve().parent
SC4=ROOT/"scenario_candidates/scenario4"
results=[]
def check(name, ok, detail=None):
    results.append({"name":name,"status":"PASS" if ok else "FAIL","detail":detail})

pre=json.loads((SC4/"SCENARIO4_BRUME_PREFLIGHT.json").read_text(encoding="utf-8"))
check("dual_source_preflight_and_pair_identity",
      pre.get("status")=="PASS" and all(pre["gates"].get(k)=="PASS" for k in ("gardien_retrievable","joueur_retrievable","pair_identity","knowledge_partition")),
      pre.get("gates"))

fw=json.loads((SC4/"BRUME_KNOWLEDGE_FIREWALL_AUDIT.json").read_text(encoding="utf-8"))
check("knowledge_firewall_zero_leaks", fw.get("status")=="PASS" and fw.get("player_keeper_leaks")==0, fw)

rr=json.loads((SC4/"BRUME_RELEASE_READINESS.json").read_text(encoding="utf-8"))
check("protected_release_readiness_all_pass", all(v=="PASS" for v in rr.get("checks",{}).values()), rr.get("checks"))

start={
    "scene_id":"BRUME_NODE_MAIRIE",
    "source_ref":"PLAYER_P2_L8_L17",
    "source_sha256":"2beeb4fa844cfb34f4065660c6ef1547e6943e99e2cc0427b1ea96125733ae6e",
    "partition":"PLAYER_SAFE","availability":"AT_ARRIVAL","explicit_source_language":True,
}
edge={
    "transition_id":"BRUME_317_05","from_scene":"BRUME_NODE_MAIRIE","to_scene":"BRUME_NODE_GALERIE_WARD",
    "predicate":"SOURCE_CONDITION","effects":[{"type":"UNLOCK_SCENE","scene":"BRUME_NODE_GALERIE_WARD"}],
    "authority":"EXPLICIT_SOURCE_TABLE_RELATION","relation":"LEADS_TO",
    "source_ref":"KEEPER_P3_L43","source_sha256":"1453127d23b281a3948c209303d498361062d2a8804f64d3ae13a4b2f9952a95",
    "partition":"KEEPER","target_binding_count":1,"explicit_source_language":True,
}
safe=SafeTransitionRecoveryV1.recover([edge])
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
proof=SourceBackedPathClosureV1.prove(start,safe["transitions"],terminal)
check("source_backed_path_reproves", proof.get("status")=="PROVED" and proof.get("pass_real_candidate") is True, proof)
check("generic_execution_ledger_exact",
      proof.get("executed_state",{}).get("transition_ledger")==["BRUME_317_05","BRUME_318_GALLERY_TO_MAREE_REFERMEE"],
      proof.get("executed_state"))

cert=json.loads((SC4/"BRUME_PASS_REAL_RELEASE_319.json").read_text(encoding="utf-8"))
gate=Scenario4ReleaseGateV1.validate_certificate(cert)
check("release_certificate_gate", gate.get("status")=="PASS", gate)

tamper=json.loads(json.dumps(cert)); tamper["player_keeper_leaks"]=1
check("leak_tamper_fails_closed", Scenario4ReleaseGateV1.validate_certificate(tamper).get("code")=="KNOWLEDGE_LEAK_PRESENT")
tamper2=json.loads(json.dumps(cert)); tamper2["checks"]["source_backed_path_proof"]="FAIL"
check("missing_release_check_fails_closed", Scenario4ReleaseGateV1.validate_certificate(tamper2).get("code")=="RELEASE_CHECKS_INCOMPLETE")

resolved=MultiScenarioStatusResolver.resolve(ROOT/"scenario_candidates","scenario4")
check("scenario4_resolver_promoted_by_release_certificate",
      resolved.get("status")=="PASS_REAL" and resolved.get("pass_real") is True and resolved.get("authority")=="BRUME_PASS_REAL_RELEASE_319.json",
      resolved)

elig=CertificationEligibilityGate.evaluate(resolved)
check("certification_eligibility_now_true", elig.get("eligible") is True and elig.get("decision")=="CERTIFY", elig)
check("anti_false_promotion_gate_accepts_only_after_resolver_pass_real",
      AntiFalsePromotionGate.validate(resolved.get("status"),"PASS_REAL").get("valid") is True)

ui=ScenarioSelectionInterfaceV1(ROOT/"scenario_candidates")
listing=ui.list_scenarios()
row=next(x for x in listing["scenarios"] if x["scenario_key"]=="scenario4")
sel=ui.select("scenario4")
check("scenario_selection_interface_marks_brume_selectable", row.get("selectable") is True and row.get("status")=="PASS_REAL", row)
check("scenario_selection_selects_brume", sel.get("status")=="SELECTED" and sel.get("code")=="SCENARIO_CERTIFIED", sel)
check("player_selection_surface_has_no_keeper_evidence",
      set(sel["selection"])=={"scenario_key","title","certification_status"} and not any("KEEPER" in str(v) for v in sel["selection"].values()),
      sel["selection"])

old=json.loads((SC4/"BRUME_FINAL_CLASSIFICATION.json").read_text(encoding="utf-8"))
check("historical_classification_preserved_not_rewritten", old.get("pass_real") is False and old.get("classification")=="COMPILED_PROTECTED_NOT_PASS_REAL", old)

statuses={k:MultiScenarioStatusResolver.resolve(ROOT/"scenario_candidates",k) for k in ("scenario3","scenario4","scenario5","scenario6","scenario7")}
check("scenario_status_regression",
      statuses["scenario3"].get("pass_real") is True and statuses["scenario4"].get("pass_real") is True
      and all(statuses[k].get("pass_real") is False for k in ("scenario5","scenario6","scenario7")),
      statuses)

for script,name in [("run_tests_chunk315.py","checkpoint315_regression"),("run_tests.py","native_core_regression")]:
    p=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,capture_output=True,text=True)
    check(name,p.returncode==0,{"returncode":p.returncode,"stdout_tail":p.stdout[-600:],"stderr_tail":p.stderr[-600:]})

passed=sum(x["status"]=="PASS" for x in results)
report={
    "schema":"NATIVE_RUNTIME_CHUNK319_REPORT_V1",
    "checkpoint_parent":318,
    "milestone":"SCENARIO4_PASS_REAL_RELEASE_AUDIT_V1",
    "tests_total":len(results),
    "tests_passed":passed,
    "tests_failed":len(results)-passed,
    "status":"PASS" if passed==len(results) else "FAIL",
    "scenario4_release_status":"PASS_REAL" if passed==len(results) else "PASS_REAL_CANDIDATE",
    "pass_real_promotions":1 if passed==len(results) else 0,
    "promotion_target":"scenario4" if passed==len(results) else None,
    "results":results,
}
(ROOT/"NATIVE_RUNTIME_CHUNK319_REPORT.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report["status"]=="PASS" else 1)
