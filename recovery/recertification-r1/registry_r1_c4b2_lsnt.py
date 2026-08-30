from __future__ import annotations

import copy

import registry_r1_c4 as parent

REGISTRY_ID = "COC7_RECOVERY_REGISTRY_R1_C4B2_LSNT_V1"
PARENT_REGISTRY_ID = parent.REGISTRY_ID
RULES_SOURCE = "COC7_INVESTIGATOR"
INVESTIGATOR_SHA256 = "de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17"

SKILL_EXTENSIONS = {
    "DEMOLITIONS": parent.SkillRecord("DEMOLITIONS", "Demolitions", 1, False, 104),
    "FIREARMS_MACHINE_GUN": parent.SkillRecord("FIREARMS_MACHINE_GUN", "Firearms (Machine Gun)", 10, True, 107),
}

SCENARIO_REFERENCE_REQUIREMENTS = {
    "MG34": {
        "scenario_id": "LSNT-V1.5-MULTI-1942",
        "kind": "WEAPON_REFERENCE",
        "required_skill_id": "FIREARMS_MACHINE_GUN",
        "mechanics_status": "UNMATERIALIZED_SPECIFIC_WEAPON",
        "substitution_allowed": False,
        "note": "The scenario names MG34, while the currently materialized official weapon table does not provide an MG34-specific record. No Bren/Vickers/generic machine-gun substitution is authorized.",
    },
    "EXPLOSIVES": {
        "scenario_id": "LSNT-V1.5-MULTI-1942",
        "kind": "EQUIPMENT_REFERENCE",
        "required_skill_id": "DEMOLITIONS",
        "mechanics_status": "TYPE_UNSPECIFIED_BY_SCENARIO",
        "substitution_allowed": False,
        "note": "The scenario requires explosives in some situations but does not authorize the engine to choose a specific explosive type automatically.",
    },
}


def _with_registry(result: dict) -> dict:
    if result.get("status", "").startswith("RESOLVED"):
        out = copy.deepcopy(result)
        out["parent_registry_id"] = out.get("registry_id")
        out["registry_id"] = REGISTRY_ID
        return out
    return result


def resolve_skill(skill_id: str, *, dex: int | None = None) -> dict:
    key = str(skill_id).upper()
    record = SKILL_EXTENSIONS.get(key)
    if record is not None:
        return {
            "status": "RESOLVED",
            "registry_id": REGISTRY_ID,
            "parent_registry_id": PARENT_REGISTRY_ID,
            "record": dict(record.__dict__),
            "source_id": RULES_SOURCE,
            "source_sha256": INVESTIGATOR_SHA256,
        }
    return _with_registry(parent.resolve_skill(key, dex=dex))


def resolve_occupation(occupation_id: str, *, characteristics: dict | None = None) -> dict:
    return _with_registry(parent.resolve_occupation(occupation_id, characteristics=characteristics))


def resolve_equipment(equipment_id: str) -> dict:
    return _with_registry(parent.resolve_equipment(equipment_id))


def resolve_weapon(weapon_id: str) -> dict:
    return _with_registry(parent.resolve_weapon(weapon_id))


def scenario_reference_status(reference_id: str) -> dict:
    key = str(reference_id).upper()
    record = SCENARIO_REFERENCE_REQUIREMENTS.get(key)
    if record is None:
        return {"status": "BLOCKED", "code": "SCENARIO_REFERENCE_UNKNOWN", "reference_id": reference_id}
    return {
        "status": "REFERENCE_ONLY",
        "registry_id": REGISTRY_ID,
        "reference_id": key,
        **copy.deepcopy(record),
    }


def registry_summary() -> dict:
    base = parent.registry_summary()
    return {
        "registry_id": REGISTRY_ID,
        "parent_registry_id": PARENT_REGISTRY_ID,
        "base_counts": base,
        "skill_extensions": len(SKILL_EXTENSIONS),
        "scenario_reference_requirements": len(SCENARIO_REFERENCE_REQUIREMENTS),
        "specific_mg34_mechanics_materialized": False,
        "automatic_explosive_type_selection": False,
        "scope": "C4 registry plus source-grounded LSNT v1.5 skill requirements; unresolved scenario-specific equipment remains fail-closed.",
    }
