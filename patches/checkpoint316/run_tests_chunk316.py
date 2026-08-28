import json, os, tempfile
from pathlib import Path
from solidstate_runtime import (
    SolidStateDB, SolidStateEngine,
    ScenarioSelectionInterfaceV1, PlayerInterfaceV1, LaunchChainV1,
)

ROOT = Path(__file__).resolve().parent
SCENARIO_ROOT = ROOT / "scenario_candidates"


def make_engine():
    td = tempfile.TemporaryDirectory()
    db = SolidStateDB(Path(td.name) / "test.sqlite")
    e = SolidStateEngine(db)
    return td, e


def create_pc(e, player_id, character_id, hp=12, san=70, mp=14, luck=55):
    assert e.set_character(character_id, player_id, {"name": character_id})["status"] == "COMMIT"
    assert e.attach_character(player_id, character_id)["status"] == "COMMIT"
    assert e.wounds.initialize(character_id, hp)["status"] == "COMMIT"
    assert e.mechanics.set_value(character_id, "SAN", san)["status"] == "COMMIT"
    assert e.mechanics.set_value(character_id, "MP", mp)["status"] == "COMMIT"
    assert e.mechanics.set_value(character_id, "Luck", luck)["status"] == "COMMIT"


def test_scenario_registry_statuses():
    ui = ScenarioSelectionInterfaceV1(SCENARIO_ROOT)
    rows = ui.list_scenarios()["scenarios"]
    by = {r["scenario_key"]: r for r in rows}
    assert by["scenario3"]["status"] == "PASS_REAL" and by["scenario3"]["selectable"] is True
    for key in ("scenario4", "scenario5", "scenario6", "scenario7"):
        assert by[key]["selectable"] is False
    return "PASS"


def test_noncertified_selection_blocked():
    ui = ScenarioSelectionInterfaceV1(SCENARIO_ROOT)
    for key in ("scenario4", "scenario5", "scenario6", "scenario7"):
        r = ui.select(key)
        assert r["status"] == "BLOCKED" and r["code"] == "SCENARIO_NOT_CERTIFIED"
    return "PASS"


def test_player_panel_real_inventory_and_stats():
    td, e = make_engine()
    try:
        create_pc(e, "P1", "C1")
        assert e.registry.register("NOTEBOOK", "equipment", "C1", {"label": "Notebook"}, "TEST_SOURCE")["status"] == "COMMIT"
        assert e.registry.register("OTHER_ITEM", "equipment", "OTHER", {"label": "Other"}, "TEST_SOURCE")["status"] == "COMMIT"
        p = PlayerInterfaceV1(e).status_panel("P1", "C1")
        assert (p["PV"], p["SAN"], p["PM"], p["Chance"]) == (12, 70, 14, 55)
        assert p["conditions"] == {"blessure_majeure": False, "mourant": False}
        assert p["inventory"] == [{"object_id": "NOTEBOOK", "object_type": "equipment", "quantity": 1}]
        return "PASS"
    finally:
        e.db.close(); td.cleanup()


def test_normal_mode_open_prompt_only():
    td, e = make_engine()
    try:
        create_pc(e, "P1", "C1")
        r = PlayerInterfaceV1(e).decision_prompt("P1", "C1", "NORMAL_LIBRE")
        assert r["status"] == "DECISION_READY" and r["menu"] is None and r["prompt"] == "Que fais-tu ?"
        return "PASS"
    finally:
        e.db.close(); td.cleanup()


def test_assisted_three_plus_free_and_knowledge_gate():
    td, e = make_engine()
    try:
        create_pc(e, "P1", "C1")
        assert e.knowledge.grant("C1", "K_PLAYER", "PLAYER", "TEST_SOURCE")["status"] == "COMMIT"
        assert e.knowledge.grant("C1", "K_KEEPER", "KEEPER", "TEST_SOURCE")["status"] == "COMMIT"
        good = [
            {"id": "A", "label": "A", "visibility": "PLAYER_SAFE", "requires_knowledge": ["K_PLAYER"]},
            {"id": "B", "label": "B", "visibility": "PLAYER_SAFE"},
            {"id": "C", "label": "C", "visibility": "PLAYER_SAFE"},
        ]
        r = PlayerInterfaceV1(e).decision_prompt("P1", "C1", "FACILE_ASSISTE", good)
        assert r["status"] == "DECISION_READY"
        assert len(r["menu"]["choices"]) == 3 and r["menu"]["free_action"]["id"] == "FREE_ACTION"
        bad = [dict(x) for x in good]
        bad[0] = {"id": "X", "label": "Secret", "visibility": "PLAYER_SAFE", "requires_knowledge": ["K_KEEPER"]}
        b = PlayerInterfaceV1(e).decision_prompt("P1", "C1", "FACILE_ASSISTE", bad)
        assert b["status"] == "BLOCKED" and b["code"] == "CHOICE_KNOWLEDGE_NOT_VISIBLE"
        return "PASS"
    finally:
        e.db.close(); td.cleanup()


def test_keeper_leakage_surface():
    td, e = make_engine()
    try:
        create_pc(e, "P1", "C1")
        # Deliberately seed Keeper-only data and a secret in raw character state.
        e.scenario.active_scenario_id = "SYNTH"
        e.db.conn.execute("INSERT INTO scenarios(scenario_id,title,version,authority_hash,runtime_registry_json,loaded_commit) VALUES(?,?,?,?,?,?)",
                          ("SYNTH", "Synthetic", "1", "h", "{}", 0))
        e.db.conn.commit()
        assert e.scenario.set_state("keeper_secret", "NEVER_SHOW", "KEEPER")["status"] == "COMMIT"
        assert e.scenario.set_state("public_fact", "SAFE", "PLAYER_SAFE")["status"] == "COMMIT"
        assert e.knowledge.grant("C1", "SECRET_KNOWLEDGE", "KEEPER", "TEST_SOURCE")["status"] == "COMMIT"
        p = PlayerInterfaceV1(e).status_panel("P1", "C1")
        blob = json.dumps(p, sort_keys=True)
        assert "NEVER_SHOW" not in blob and "SECRET_KNOWLEDGE" not in blob and "keeper_secret" not in blob
        return "PASS"
    finally:
        e.db.close(); td.cleanup()


def test_launch_chain_one_player():
    td, e = make_engine()
    try:
        create_pc(e, "P1", "C1")
        sel = ScenarioSelectionInterfaceV1(SCENARIO_ROOT)
        r = LaunchChainV1(e, sel).prepare_session("scenario3", ["P1"])
        assert r["status"] == "SESSION_READY"
        assert [x["gate"] for x in r["trace"]] == ["SCENARIO", "PLAYERS", "CHARACTERS", "SESSION"]
        state, _ = e.db.state()
        assert state["interface_session"]["scenario_key"] == "scenario3"
        return "PASS"
    finally:
        e.db.close(); td.cleanup()


def test_launch_chain_four_players():
    td, e = make_engine()
    try:
        for i in range(1, 5): create_pc(e, f"P{i}", f"C{i}")
        r = LaunchChainV1(e, ScenarioSelectionInterfaceV1(SCENARIO_ROOT)).prepare_session(
            "scenario3", ["P1", "P2", "P3", "P4"]
        )
        assert r["status"] == "SESSION_READY" and len(r["session"]["control_map"]) == 4
        return "PASS"
    finally:
        e.db.close(); td.cleanup()


def test_launch_chain_missing_character_fail_closed():
    td, e = make_engine()
    try:
        create_pc(e, "P1", "C1")
        r = LaunchChainV1(e, ScenarioSelectionInterfaceV1(SCENARIO_ROOT)).prepare_session(
            "scenario3", ["P1", "P2"]
        )
        assert r["status"] == "BLOCKED" and r["code"] == "PLAYER_CHARACTER_NOT_READY"
        return "PASS"
    finally:
        e.db.close(); td.cleanup()


def test_historical_statuses_unchanged():
    ui = ScenarioSelectionInterfaceV1(SCENARIO_ROOT)
    rows = {r["scenario_key"]: r for r in ui.list_scenarios()["scenarios"]}
    expected = {
        "scenario3": "PASS_REAL",
        "scenario4": "COMPILED_PROTECTED_NOT_PASS_REAL",
        "scenario5": "COMPILED_CANDIDATE_NOT_PATH_PROVEN",
        "scenario6": "COMPILED_CANDIDATE_NOT_PATH_PROVEN",
        "scenario7": "COMPILED_INVESTIGATION_GRAPH_NOT_PATH_PROVEN",
    }
    assert {k: rows[k]["status"] for k in expected} == expected
    return "PASS"


TESTS = [
    test_scenario_registry_statuses,
    test_noncertified_selection_blocked,
    test_player_panel_real_inventory_and_stats,
    test_normal_mode_open_prompt_only,
    test_assisted_three_plus_free_and_knowledge_gate,
    test_keeper_leakage_surface,
    test_launch_chain_one_player,
    test_launch_chain_four_players,
    test_launch_chain_missing_character_fail_closed,
    test_historical_statuses_unchanged,
]

if __name__ == "__main__":
    results = []
    for fn in TESTS:
        try:
            status = fn()
            results.append({"test": fn.__name__, "status": status})
        except Exception as exc:
            results.append({"test": fn.__name__, "status": "FAIL", "error": repr(exc)})
    passed = sum(r["status"] == "PASS" for r in results)
    report = {
        "chunk": 316,
        "checkpoint_parent": 315,
        "id": "PLAYER_AND_SCENARIO_INTERFACE_V1",
        "classification": "INTERFACE_V1_RUNTIME_MATERIALIZED",
        "passed": passed,
        "total": len(results),
        "status": "PASS" if passed == len(results) else "FAIL",
        "tasks": {"1": "PASS", "2": "PASS", "3": "PASS", "4": "PASS", "5": "PASS"} if passed == len(results) else {},
        "historical_scenario_promotions": 0,
        "results": results,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
