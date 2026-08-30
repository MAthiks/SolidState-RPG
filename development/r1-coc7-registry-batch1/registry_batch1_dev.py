from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
RECOVERY = ROOT / "recovery" / "recertification-r1"
if str(RECOVERY) not in sys.path:
    sys.path.insert(0, str(RECOVERY))

import registry_r1_c4 as parent  # noqa: E402

BATCH = json.loads((HERE / "occupations_batch1.json").read_text(encoding="utf-8"))
REGISTRY_ID = "COC7_RECOVERY_REGISTRY_R1_BATCH1_DEV_V1"
PARENT_REGISTRY_ID = parent.REGISTRY_ID
SOURCE_ID = BATCH["source"]["source_id"]
SOURCE_SHA256 = BATCH["source"]["sha256"]
OCCUPATIONS = BATCH["occupations"]
SKILL_EXTENSIONS = BATCH["skill_extensions"]
INTERPERSONAL = ("CHARM", "FAST_TALK", "INTIMIDATE", "PERSUADE")
CLASSIC_ERAS = {"1920S", "CLASSIC", "1920S_CLASSIC"}


def _valid_characteristic(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100


def resolve_skill(skill_id: str, *, dex: int | None = None, edu: int | None = None, era: str | None = None) -> dict:
    key = str(skill_id).upper()
    if key in parent.SKILLS:
        return parent.resolve_skill(key, dex=dex)
    record = SKILL_EXTENSIONS.get(key)
    if record is None:
        return {"status": "BLOCKED", "code": "SKILL_RECORD_UNMATERIALIZED", "skill_id": skill_id}
    if record.get("era_scope") == "MODERN" and str(era or "").upper() in CLASSIC_ERAS:
        return {"status": "BLOCKED", "code": "SKILL_NOT_AVAILABLE_IN_ERA", "skill_id": key, "era": era}
    out = copy.deepcopy(record)
    out["skill_id"] = key
    if out["base"] == "EDU":
        if not _valid_characteristic(edu):
            return {"status": "BLOCKED", "code": "OWN_LANGUAGE_REQUIRES_VALID_EDU", "skill_id": key}
        out["base"] = edu
    return {"status": "RESOLVED", "registry_id": REGISTRY_ID, "record": out, "source_id": SOURCE_ID}


def occupation_slot_count(record: dict) -> int:
    return sum(int(slot.get("count", 1)) for slot in record["skill_slots"])


def _points_from_formula(formula: dict, characteristics: dict, *, choice_characteristic: str | None = None) -> int:
    total = 0
    choice_terms = 0
    for term in formula.get("terms", []):
        multiplier = term.get("multiplier")
        if not isinstance(multiplier, int) or multiplier <= 0:
            raise ValueError("OCCUPATION_FORMULA_INVALID")
        if "characteristic" in term:
            characteristic = term["characteristic"]
        elif "choice_one_of" in term:
            choice_terms += 1
            allowed = tuple(term["choice_one_of"])
            characteristic = str(choice_characteristic or "").upper()
            if characteristic not in allowed:
                raise ValueError("OCCUPATION_CHARACTERISTIC_CHOICE_REQUIRED")
        else:
            raise ValueError("OCCUPATION_FORMULA_INVALID")
        value = characteristics.get(characteristic)
        if not _valid_characteristic(value):
            raise ValueError(f"{characteristic}_INVALID")
        total += value * multiplier
    if choice_terms == 0 and choice_characteristic is not None:
        raise ValueError("OCCUPATION_CHARACTERISTIC_CHOICE_NOT_USED")
    if choice_terms > 1:
        raise ValueError("OCCUPATION_MULTIPLE_CHARACTERISTIC_CHOICES_UNSUPPORTED_DEV")
    return total


def resolve_occupation(
    occupation_id: str,
    *,
    characteristics: dict | None = None,
    choice_characteristic: str | None = None,
) -> dict:
    key = str(occupation_id).upper()
    record = OCCUPATIONS.get(key)
    if record is None:
        return {"status": "BLOCKED", "code": "OCCUPATION_RECORD_UNMATERIALIZED", "occupation_id": occupation_id}
    if occupation_slot_count(record) != 8:
        return {"status": "BLOCKED", "code": "OCCUPATION_SKILL_SLOT_COUNT_INVALID", "occupation_id": key}
    out = copy.deepcopy(record)
    out["occupation_id"] = key
    if characteristics is not None:
        try:
            out["occupation_skill_points"] = _points_from_formula(
                record["points_formula"], characteristics, choice_characteristic=choice_characteristic
            )
        except ValueError as error:
            return {"status": "BLOCKED", "code": str(error), "occupation_id": key}
    return {
        "status": "RESOLVED",
        "registry_id": REGISTRY_ID,
        "parent_registry_id": PARENT_REGISTRY_ID,
        "source_id": SOURCE_ID,
        "source_sha256": SOURCE_SHA256,
        "record": out,
    }


def _iter_explicit_skill_refs(slot: dict):
    if "skill" in slot:
        yield slot["skill"]
    for choice in slot.get("choice_one_of", []):
        if isinstance(choice, dict) and "skill" in choice:
            yield choice["skill"]
    if slot.get("interpersonal_choice"):
        yield from INTERPERSONAL


def validate_record_references(occupation_id: str) -> dict:
    resolved = resolve_occupation(occupation_id)
    if resolved["status"] != "RESOLVED":
        return resolved
    record = resolved["record"]
    unresolved = []
    for slot in record["skill_slots"]:
        for skill_id in _iter_explicit_skill_refs(slot):
            # Computer Use is a valid materialized record even though unavailable in classic eras.
            result = resolve_skill(skill_id, dex=50, edu=50, era="MODERN")
            if result.get("status") != "RESOLVED":
                unresolved.append(skill_id)
    if unresolved:
        return {"status": "BLOCKED", "code": "OCCUPATION_SKILL_REFERENCE_UNRESOLVED", "unresolved": sorted(set(unresolved))}
    return {"status": "VALIDATED", "occupation_id": occupation_id, "slot_count": occupation_slot_count(record)}


def archaeology_parent_compatibility() -> dict:
    child = OCCUPATIONS["ARCHAEOLOGIST"]
    p = parent.OCCUPATIONS["ARCHAEOLOGIST"]
    compatible = (
        child["points_formula"] == {"terms": [{"characteristic": "EDU", "multiplier": 4}]}
        and child["credit_rating"] == [p.credit_min, p.credit_max]
        and child["source_page"] == p.source_page
        and occupation_slot_count(child) == 8
    )
    return {"status": "PASS" if compatible else "FAIL", "parent_registry_id": parent.REGISTRY_ID}


def registry_summary() -> dict:
    return {
        "registry_id": REGISTRY_ID,
        "parent_registry_id": PARENT_REGISTRY_ID,
        "source_sha256": SOURCE_SHA256,
        "parent_skills": len(parent.SKILLS),
        "skill_extensions": len(SKILL_EXTENSIONS),
        "occupation_batch": len(OCCUPATIONS),
        "authority_promoted": False,
        "frozen_parent_modified": False,
    }
