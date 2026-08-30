from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REGISTRY_ID = "COC7_RECOVERY_REGISTRY_R1_C4_V1"
RULES_SOURCE = "COC7_INVESTIGATOR"


@dataclass(frozen=True)
class SkillRecord:
    skill_id: str
    name: str
    base: int | str
    specialization: bool = False
    source_page: int = 97


@dataclass(frozen=True)
class OccupationRecord:
    occupation_id: str
    name: str
    points_formula: str
    credit_min: int
    credit_max: int
    skill_slots: tuple[Any, ...]
    source_page: int


@dataclass(frozen=True)
class EquipmentRecord:
    equipment_id: str
    name: str
    era_scope: str
    source_page: int
    auto_possession: bool = False


@dataclass(frozen=True)
class WeaponRecord:
    weapon_id: str
    name: str
    skill_id: str
    damage: str
    base_range_yards: int
    uses_per_round: str
    capacity: str
    malfunction: int
    source_page: int
    availability_claim: str = "MECHANICS_ONLY_NOT_AUTOMATIC_POSSESSION"


SKILLS = {
    r.skill_id: r for r in (
        SkillRecord("ACCOUNTING", "Accounting", 5),
        SkillRecord("ANTHROPOLOGY", "Anthropology", 1),
        SkillRecord("APPRAISE", "Appraise", 5),
        SkillRecord("ARCHAEOLOGY", "Archaeology", 1),
        SkillRecord("CHARM", "Charm", 15),
        SkillRecord("CLIMB", "Climb", 20),
        SkillRecord("CREDIT_RATING", "Credit Rating", 0),
        SkillRecord("CTHULHU_MYTHOS", "Cthulhu Mythos", 0),
        SkillRecord("DISGUISE", "Disguise", 5),
        SkillRecord("DODGE", "Dodge", "HALF_DEX"),
        SkillRecord("DRIVE_AUTO", "Drive Auto", 20),
        SkillRecord("ELECTRICAL_REPAIR", "Electrical Repair", 10),
        SkillRecord("FAST_TALK", "Fast Talk", 5),
        SkillRecord("FIGHTING_BRAWL", "Fighting (Brawl)", 25, True),
        SkillRecord("FIREARMS_HANDGUN", "Firearms (Handgun)", 20, True),
        SkillRecord("FIREARMS_RIFLE", "Firearms (Rifle)", 25, True),
        SkillRecord("FIREARMS_SHOTGUN", "Firearms (Shotgun)", 25, True),
        SkillRecord("FIREARMS_SMG", "Firearms (Submachine Gun)", 15, True),
        SkillRecord("FIRST_AID", "First Aid", 30),
        SkillRecord("HISTORY", "History", 5),
        SkillRecord("INTIMIDATE", "Intimidate", 15),
        SkillRecord("JUMP", "Jump", 20),
        SkillRecord("LANGUAGE_OTHER", "Language (Other)", 1, True),
        SkillRecord("LAW", "Law", 5),
        SkillRecord("LIBRARY_USE", "Library Use", 20),
        SkillRecord("LISTEN", "Listen", 20),
        SkillRecord("LOCKSMITH", "Locksmith", 1),
        SkillRecord("MECHANICAL_REPAIR", "Mechanical Repair", 10),
        SkillRecord("MEDICINE", "Medicine", 1),
        SkillRecord("NATURAL_WORLD", "Natural World", 10),
        SkillRecord("NAVIGATE", "Navigate", 10),
        SkillRecord("OCCULT", "Occult", 5),
        SkillRecord("OPERATE_HEAVY_MACHINERY", "Operate Heavy Machinery", 1),
        SkillRecord("PERSUADE", "Persuade", 10),
        SkillRecord("PSYCHOANALYSIS", "Psychoanalysis", 1),
        SkillRecord("PSYCHOLOGY", "Psychology", 10),
        SkillRecord("RIDE", "Ride", 5),
        SkillRecord("SCIENCE", "Science", 1, True),
        SkillRecord("SPOT_HIDDEN", "Spot Hidden", 25),
        SkillRecord("STEALTH", "Stealth", 20),
        SkillRecord("SWIM", "Swim", 20),
        SkillRecord("THROW", "Throw", 20),
        SkillRecord("TRACK", "Track", 10),
    )
}

# Only mechanically verified occupations are materialized. Unknown occupations fail closed.
OCCUPATIONS = {
    "ARCHAEOLOGIST": OccupationRecord(
        "ARCHAEOLOGIST",
        "Archaeologist",
        "EDU_X4",
        10,
        40,
        (
            "APPRAISE",
            "ARCHAEOLOGY",
            "HISTORY",
            {"specialization": "LANGUAGE_OTHER", "choice": "ANY"},
            "LIBRARY_USE",
            "SPOT_HIDDEN",
            "MECHANICAL_REPAIR",
            {"choice_one_of": ("NAVIGATE", "SCIENCE")},
        ),
        71,
    ),
}

EQUIPMENT = {
    r.equipment_id: r for r in (
        EquipmentRecord("BINOCULARS_1920S_REFERENCE", "Binoculars", "1920S_REFERENCE", 242),
        EquipmentRecord("COMPASS_WITH_LID_1920S_REFERENCE", "Compass with Lid", "1920S_REFERENCE", 242),
        EquipmentRecord("ROPE_50FT_1920S_REFERENCE", "Rope (50 Feet)", "1920S_REFERENCE", 243),
        EquipmentRecord("POCKET_MAGNIFIER_1920S_REFERENCE", "3-Lens Pocket Magnifying Glass", "1920S_REFERENCE", 244),
    )
}

WEAPONS = {
    r.weapon_id: r for r in (
        WeaponRecord("REVOLVER_38_OR_9MM", ".38 or 9mm Revolver", "FIREARMS_HANDGUN", "1D10", 15, "1 (3)", "6", 100, 251),
        WeaponRecord("LEE_ENFIELD_303", ".303 Lee-Enfield", "FIREARMS_RIFLE", "2D6+4", 110, "1", "10", 100, 252),
        WeaponRecord("THOMPSON_SMG", "Thompson", "FIREARMS_SMG", "1D10+2", 20, "1 OR FULL_AUTO", "20/30/50", 96, 253),
    )
}


def _asdict(record):
    return dict(record.__dict__)


def resolve_skill(skill_id: str, *, dex: int | None = None) -> dict:
    record = SKILLS.get(str(skill_id).upper())
    if record is None:
        return {"status": "BLOCKED", "code": "SKILL_RECORD_UNMATERIALIZED", "skill_id": skill_id}
    result = _asdict(record)
    if record.base == "HALF_DEX":
        if not isinstance(dex, int) or isinstance(dex, bool) or not 0 <= dex <= 100:
            return {"status": "BLOCKED", "code": "DODGE_REQUIRES_VALID_DEX", "skill_id": record.skill_id}
        result["base"] = dex // 2
    return {"status": "RESOLVED", "registry_id": REGISTRY_ID, "record": result, "source_id": RULES_SOURCE}


def occupation_points(record: OccupationRecord, characteristics: dict) -> int:
    if record.points_formula == "EDU_X4":
        edu = characteristics.get("EDU")
        if not isinstance(edu, int) or isinstance(edu, bool) or not 0 <= edu <= 100:
            raise ValueError("EDU_INVALID")
        return edu * 4
    raise ValueError("OCCUPATION_FORMULA_UNMATERIALIZED")


def resolve_occupation(occupation_id: str, *, characteristics: dict | None = None) -> dict:
    record = OCCUPATIONS.get(str(occupation_id).upper())
    if record is None:
        return {"status": "BLOCKED", "code": "OCCUPATION_RECORD_UNMATERIALIZED", "occupation_id": occupation_id}
    result = _asdict(record)
    if characteristics is not None:
        try:
            result["occupation_skill_points"] = occupation_points(record, characteristics)
        except ValueError as error:
            return {"status": "BLOCKED", "code": str(error), "occupation_id": occupation_id}
    return {"status": "RESOLVED", "registry_id": REGISTRY_ID, "record": result, "source_id": RULES_SOURCE}


def validate_custom_occupation(*, authorized: bool, skill_ids: list[str], credit_min: int, credit_max: int) -> dict:
    if not authorized:
        return {"status": "BLOCKED", "code": "CUSTOM_OCCUPATION_NOT_AUTHORIZED"}
    if not isinstance(skill_ids, list) or not 1 <= len(skill_ids) <= 8:
        return {"status": "BLOCKED", "code": "CUSTOM_OCCUPATION_SKILL_COUNT_INVALID"}
    unresolved = [sid for sid in skill_ids if resolve_skill(sid).get("status") != "RESOLVED"]
    if unresolved:
        return {"status": "BLOCKED", "code": "CUSTOM_OCCUPATION_SKILL_UNRESOLVED", "unresolved": unresolved}
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (credit_min, credit_max)) or not 0 <= credit_min <= credit_max <= 100:
        return {"status": "BLOCKED", "code": "CUSTOM_OCCUPATION_CREDIT_RANGE_INVALID"}
    return {"status": "AUTHORIZED_CUSTOM", "skills": list(skill_ids), "credit_rating": [credit_min, credit_max]}


def resolve_equipment(equipment_id: str) -> dict:
    record = EQUIPMENT.get(str(equipment_id).upper())
    if record is None:
        return {"status": "BLOCKED", "code": "EQUIPMENT_RECORD_UNMATERIALIZED", "equipment_id": equipment_id}
    return {"status": "RESOLVED_REFERENCE", "registry_id": REGISTRY_ID, "record": _asdict(record), "source_id": RULES_SOURCE, "auto_possession": False}


def resolve_weapon(weapon_id: str) -> dict:
    record = WEAPONS.get(str(weapon_id).upper())
    if record is None:
        return {"status": "BLOCKED", "code": "WEAPON_RECORD_UNMATERIALIZED", "weapon_id": weapon_id}
    if record.skill_id not in SKILLS:
        return {"status": "BLOCKED", "code": "WEAPON_SKILL_RECORD_UNRESOLVED", "weapon_id": weapon_id}
    return {"status": "RESOLVED_MECHANICS", "registry_id": REGISTRY_ID, "record": _asdict(record), "source_id": RULES_SOURCE, "auto_possession": False}


def registry_summary() -> dict:
    return {
        "registry_id": REGISTRY_ID,
        "skills": len(SKILLS),
        "occupations": len(OCCUPATIONS),
        "equipment": len(EQUIPMENT),
        "weapons": len(WEAPONS),
        "scope": "source-grounded minimal registry; unknown records fail closed; not a substitute for the rulebooks",
    }
