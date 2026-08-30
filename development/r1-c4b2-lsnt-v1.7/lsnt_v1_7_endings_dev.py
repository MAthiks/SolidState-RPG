from __future__ import annotations

import copy

ENDING_FAMILIES = {
    "LE_MIDI_REFERME": "Dispositif referme; menace locale contenue",
    "VICTOIRE_MILITAIRE": "Progetto Nero detruit; phenomene non resolu",
    "VICTOIRE_INCOMPLETE": "Fragment reenseveli; reveil futur possible",
    "CONVOI_DE_LOMBRE": "Voss transfere le fragment",
    "FRAGMENT_ALLIE": "Allies recuperent l'objet",
    "QASR_IREM_DETRUITE": "Site effondre; effets secondaires",
    "ZENITH_NOIR": "Expansion majeure Jour 4",
    "ALLIANCE_AMERE": "Cooperation ponctuelle",
    "ENQUETE_ABANDONNEE": "Tous les PJ actifs se retirent; horloge continue",
    "GAME_OVER": "Tous les PJ controlables morts/incapacites ou aucune poursuite jouable causalement possible",
}


def _controllable_rows(state: dict) -> list[dict]:
    return [copy.deepcopy(row) for row in state.get("party", {}).values()]


def _all_unable(rows: list[dict]) -> bool:
    if not rows:
        return False
    return all(bool(row.get("dead")) or bool(row.get("incapacitated")) for row in rows)


def _all_active_withdrawn(rows: list[dict]) -> bool:
    active = [row for row in rows if not row.get("dead") and not row.get("incapacitated")]
    return bool(active) and all(bool(row.get("withdrawn")) for row in active)


def evaluate_endings(state: dict, *, world_facts: dict[str, bool] | None = None) -> dict:
    facts = world_facts or {}
    rows = _controllable_rows(state)
    candidates = []

    def add(ending_id: str, evidence: list[str]):
        candidates.append({"ending_id": ending_id, "summary": ENDING_FAMILIES[ending_id], "evidence": evidence})

    if facts.get("DEVICE_CLOSED") is True and facts.get("LOCAL_THREAT_CONTAINED") is True:
        add("LE_MIDI_REFERME", ["DEVICE_CLOSED", "LOCAL_THREAT_CONTAINED"])
    if facts.get("PROGETTO_NERO_DESTROYED") is True and facts.get("PHENOMENON_UNRESOLVED") is True:
        add("VICTOIRE_MILITAIRE", ["PROGETTO_NERO_DESTROYED", "PHENOMENON_UNRESOLVED"])
    if facts.get("FRAGMENT_REBURIED") is True and facts.get("FUTURE_AWAKENING_POSSIBLE") is True:
        add("VICTOIRE_INCOMPLETE", ["FRAGMENT_REBURIED", "FUTURE_AWAKENING_POSSIBLE"])
    if facts.get("VOSS_TRANSFERRED_FRAGMENT") is True:
        add("CONVOI_DE_LOMBRE", ["VOSS_TRANSFERRED_FRAGMENT"])
    if facts.get("ALLIES_RECOVERED_FRAGMENT") is True:
        add("FRAGMENT_ALLIE", ["ALLIES_RECOVERED_FRAGMENT"])
    if facts.get("QASR_IREM_COLLAPSED") is True:
        add("QASR_IREM_DETRUITE", ["QASR_IREM_COLLAPSED"])
    if facts.get("MAJOR_EXPANSION_DAY4") is True:
        add("ZENITH_NOIR", ["MAJOR_EXPANSION_DAY4"])
    if facts.get("TEMPORARY_COOPERATION") is True:
        add("ALLIANCE_AMERE", ["TEMPORARY_COOPERATION"])
    if _all_active_withdrawn(rows):
        add("ENQUETE_ABANDONNEE", ["ALL_ACTIVE_CONTROLLABLE_PCS_WITHDRAWN", "WORLD_CLOCK_CONTINUES"])

    no_pursuit = facts.get("NO_CAUSAL_PLAYABLE_PURSUIT") is True
    all_unable = _all_unable(rows)
    if all_unable or no_pursuit:
        evidence = []
        if all_unable:
            evidence.append("ALL_CONTROLLABLE_PCS_DEAD_OR_INCAPACITATED")
        if no_pursuit:
            evidence.append("NO_CAUSAL_PLAYABLE_PURSUIT")
        add("GAME_OVER", evidence)

    return {
        "status": "EVALUATED",
        "party_state_verified": isinstance(state.get("party"), dict),
        "world_state_input_present": world_facts is not None,
        "eligible_endings": candidates,
        "automatic_selection": None,
        "single_forced_correct_ending": False,
    }


def finalize_ending(evaluation: dict, *, ending_id: str) -> dict:
    eligible = {row["ending_id"]: row for row in evaluation.get("eligible_endings", [])}
    if ending_id not in ENDING_FAMILIES:
        return {"status": "BLOCKED", "code": "ENDING_ID_UNKNOWN"}
    if ending_id not in eligible:
        return {"status": "BLOCKED", "code": "ENDING_CONDITIONS_NOT_VERIFIED", "ending_id": ending_id}
    return {"status": "FINALIZED", "ending": copy.deepcopy(eligible[ending_id])}
