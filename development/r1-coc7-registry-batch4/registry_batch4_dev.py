from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
BATCH3_DIR = ROOT / "development" / "r1-coc7-registry-batch3"
if str(BATCH3_DIR) not in sys.path:
    sys.path.insert(0, str(BATCH3_DIR))

import registry_batch3_dev as batch3  # noqa: E402

BATCH = json.loads((HERE / "occupations_batch4.json").read_text(encoding="utf-8"))
REGISTRY_ID = "COC7_RECOVERY_REGISTRY_R1_BATCH4_DEV_V1"
PARENT_REGISTRY_ID = batch3.REGISTRY_ID
FROZEN_ANCESTOR_REGISTRY_ID = batch3.FROZEN_ANCESTOR_REGISTRY_ID
SOURCE_ID = BATCH["source"]["source_id"]
SOURCE_SHA256 = BATCH["source"]["sha256"]
OCCUPATIONS = BATCH["occupations"]
SKILL_EXTENSIONS = BATCH["skill_extensions"]
INTERPERSONAL = batch3.INTERPERSONAL
CLASSIC_ERAS = batch3.CLASSIC_ERAS
MODERN_ERAS = batch3.MODERN_ERAS


def _valid_characteristic(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100


def _era_key(era: str | None) -> str:
    return str(era or "").upper()


def resolve_skill(
    skill_id: str,
    *,
    dex: int | None = None,
    edu: int | None = None,
    era: str | None = None,
) -> dict:
    key = str(skill_id).upper()
    record = SKILL_EXTENSIONS.get(key)
    if record is None:
        return batch3.resolve_skill(key, dex=dex, edu=edu, era=era)
    out = copy.deepcopy(record)
    out["skill_id"] = key
    return {"status": "RESOLVED", "registry_id": REGISTRY_ID, "record": out, "source_id": SOURCE_ID}


def occupation_slot_count(record: dict) -> int:
    return sum(int(slot.get("count", 1)) for slot in record["skill_slots"])


def _points_from_formula(formula: dict, characteristics: dict, *, choice_characteristic: str | None = None) -> int:
    total = 0
    choice_terms = 0
    for term in formula.get("terms", []):
        multiplier = term.get("multiplier")
        if not isinstance(multiplier, int) or isinstance(multiplier, bool) or multiplier <= 0:
            raise ValueError("OCCUPATION_FORMULA_INVALID")
        if "characteristic" in term:
            characteristic = str(term["characteristic"]).upper()
        elif "choice_one_of" in term:
            choice_terms += 1
            allowed = tuple(str(x).upper() for x in term["choice_one_of"])
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


def _era_block(record: dict, era: str | None) -> str | None:
    key = _era_key(era)
    scope = record.get("era_scope")
    if scope == "MODERN" and key in CLASSIC_ERAS:
        return "OCCUPATION_NOT_AVAILABLE_IN_ERA"
    if scope == "CLASSIC" and key in MODERN_ERAS:
        return "OCCUPATION_NOT_AVAILABLE_IN_ERA"
    return None


def resolve_occupation(
    occupation_id: str,
    *,
    characteristics: dict | None = None,
    choice_characteristic: str | None = None,
    era: str | None = None,
) -> dict:
    key = str(occupation_id).upper()
    record = OCCUPATIONS.get(key)
    if record is None:
        parent_result = batch3.resolve_occupation(
            key,
            characteristics=characteristics,
            choice_characteristic=choice_characteristic,
            era=era,
        )
        if parent_result.get("status") == "RESOLVED":
            parent_result = copy.deepcopy(parent_result)
            parent_result["delegated_through_registry_id"] = REGISTRY_ID
        return parent_result
    era_code = _era_block(record, era)
    if era_code:
        return {"status": "BLOCKED", "code": era_code, "occupation_id": key, "era": era}
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
        "frozen_ancestor_registry_id": FROZEN_ANCESTOR_REGISTRY_ID,
        "source_id": SOURCE_ID,
        "source_sha256": SOURCE_SHA256,
        "record": out,
    }


def _materialized_skill_ids() -> set[str]:
    return (
        set(batch3.batch2.batch1.parent.SKILLS)
        | set(batch3.batch2.batch1.SKILL_EXTENSIONS)
        | set(batch3.batch2.SKILL_EXTENSIONS)
        | set(batch3.SKILL_EXTENSIONS)
        | set(SKILL_EXTENSIONS)
    )


def _family_is_materialized(family: str) -> bool:
    key = str(family).upper()
    ids = _materialized_skill_ids()
    if key in ids:
        return True
    prefix = key + "_"
    return any(skill_id.startswith(prefix) for skill_id in ids)


def _requirements_from_choice(choice: dict):
    if not isinstance(choice, dict):
        return
    if "skill" in choice:
        yield ("SKILL", choice["skill"])
    if "skill_family" in choice:
        yield ("FAMILY", choice["skill_family"])


def _iter_reference_requirements(slot: dict):
    if "skill" in slot:
        yield ("SKILL", slot["skill"])
    if "skill_family" in slot:
        yield ("FAMILY", slot["skill_family"])
    for choice in slot.get("choice_one_of", []):
        yield from _requirements_from_choice(choice)
    choice_n = slot.get("choice_n_of")
    if isinstance(choice_n, dict):
        for choice in choice_n.get("choices", []):
            yield from _requirements_from_choice(choice)
    if slot.get("interpersonal_choice"):
        for skill_id in INTERPERSONAL:
            yield ("SKILL", skill_id)


def validate_record_references(occupation_id: str) -> dict:
    key = str(occupation_id).upper()
    record = OCCUPATIONS.get(key)
    if record is None:
        return batch3.validate_record_references(key)
    if occupation_slot_count(record) != 8:
        return {"status": "BLOCKED", "code": "OCCUPATION_SKILL_SLOT_COUNT_INVALID", "occupation_id": key}
    unresolved = []
    for slot in record["skill_slots"]:
        for kind, value in _iter_reference_requirements(slot):
            if kind == "FAMILY":
                if not _family_is_materialized(value):
                    unresolved.append(f"FAMILY:{value}")
            else:
                result = resolve_skill(value, dex=50, edu=50, era="MODERN")
                # A materialized modern-only skill is still a valid occupation choice
                # where an alternative classic-era skill is also supplied.
                if result.get("status") != "RESOLVED" and result.get("code") != "SKILL_NOT_AVAILABLE_IN_ERA":
                    unresolved.append(value)
    if unresolved:
        return {
            "status": "BLOCKED",
            "code": "OCCUPATION_SKILL_REFERENCE_UNRESOLVED",
            "occupation_id": key,
            "unresolved": sorted(set(unresolved)),
        }
    return {"status": "VALIDATED", "occupation_id": key, "slot_count": occupation_slot_count(record)}


def _parent_occupation_ids() -> set[str]:
    return (
        set(batch3.OCCUPATIONS)
        | set(batch3.batch2.OCCUPATIONS)
        | set(batch3.batch2.batch1.OCCUPATIONS)
    )


def batch3_compatibility() -> dict:
    checks = []
    for occupation_id in sorted(_parent_occupation_ids()):
        direct = batch3.resolve_occupation(occupation_id)
        through = resolve_occupation(occupation_id)
        checks.append(
            direct.get("status") == through.get("status") == "RESOLVED"
            and direct.get("record") == through.get("record")
        )
    return {
        "status": "PASS" if all(checks) else "FAIL",
        "checked": len(checks),
        "parent_registry_id": PARENT_REGISTRY_ID,
    }


def registry_summary() -> dict:
    parent_count = batch3.registry_summary()["cumulative_occupations"]
    return {
        "registry_id": REGISTRY_ID,
        "parent_registry_id": PARENT_REGISTRY_ID,
        "frozen_ancestor_registry_id": FROZEN_ANCESTOR_REGISTRY_ID,
        "source_sha256": SOURCE_SHA256,
        "parent_cumulative_occupations": parent_count,
        "batch4_occupations": len(OCCUPATIONS),
        "cumulative_occupations": parent_count + len(OCCUPATIONS),
        "batch4_skill_extensions": len(SKILL_EXTENSIONS),
        "authority_promoted": False,
        "frozen_parent_modified": False,
    }
