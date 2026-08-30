from __future__ import annotations

import json
import unittest
from pathlib import Path

import registry_batch2_dev as registry

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "occupations_batch2.json").read_text(encoding="utf-8"))
SAMPLE = {"EDU": 50, "DEX": 50, "STR": 50, "APP": 50, "POW": 50}


class RegistryBatch2StaticTests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(registry.REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_BATCH2_DEV_V1")
        self.assertEqual(registry.PARENT_REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_BATCH1_DEV_V1")
        self.assertEqual(registry.FROZEN_ANCESTOR_REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_C4_V1")

    def test_002_source_identity(self):
        self.assertEqual(registry.SOURCE_ID, "COC7_INVESTIGATOR")
        self.assertEqual(
            registry.SOURCE_SHA256,
            "de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17",
        )

    def test_003_status_non_authoritative(self):
        self.assertEqual(MANIFEST["status"], "DEV_SOURCE_GROUNDED_NOT_FROZEN")
        self.assertFalse(MANIFEST["authority_promoted"])

    def test_004_batch_size(self):
        self.assertEqual(len(registry.OCCUPATIONS), 23)

    def test_005_cumulative_size(self):
        self.assertEqual(registry.registry_summary()["cumulative_occupations"], 34)

    def test_006_skill_extensions_exact(self):
        self.assertEqual(set(registry.SKILL_EXTENSIONS), {"DIVING", "ELECTRONICS", "PILOT", "SURVIVAL"})

    def test_007_skill_extension_bases(self):
        self.assertEqual(registry.resolve_skill("DIVING")["record"]["base"], 1)
        self.assertEqual(registry.resolve_skill("ELECTRONICS", era="MODERN")["record"]["base"], 1)
        self.assertEqual(registry.resolve_skill("PILOT")["record"]["base"], 1)
        self.assertEqual(registry.resolve_skill("SURVIVAL")["record"]["base"], 10)

    def test_008_electronics_classic_blocked(self):
        result = registry.resolve_skill("ELECTRONICS", era="1920S")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "SKILL_NOT_AVAILABLE_IN_ERA")

    def test_009_computer_use_classic_still_blocked_through_parent(self):
        result = registry.resolve_skill("COMPUTER_USE", era="CLASSIC")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "SKILL_NOT_AVAILABLE_IN_ERA")

    def test_010_modern_occupations_classic_blocked(self):
        for occupation_id in ("COMPUTER_PROGRAMMER_TECHNICIAN", "HACKER"):
            with self.subTest(occupation_id=occupation_id):
                result = registry.resolve_occupation(occupation_id, era="1920S")
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(result["code"], "OCCUPATION_NOT_AVAILABLE_IN_ERA")

    def test_011_modern_occupations_modern_resolve(self):
        for occupation_id in ("COMPUTER_PROGRAMMER_TECHNICIAN", "HACKER"):
            with self.subTest(occupation_id=occupation_id):
                self.assertEqual(registry.resolve_occupation(occupation_id, era="MODERN")["status"], "RESOLVED")

    def test_012_batch1_compatibility(self):
        result = registry.batch1_compatibility()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checked"], 11)

    def test_013_archaeologist_delegates_unchanged(self):
        direct = registry.batch1.resolve_occupation("ARCHAEOLOGIST")
        through = registry.resolve_occupation("ARCHAEOLOGIST")
        self.assertEqual(direct["record"], through["record"])
        self.assertEqual(through["delegated_through_registry_id"], registry.REGISTRY_ID)

    def test_014_unknown_occupation_fail_closed(self):
        result = registry.resolve_occupation("NOT_A_REAL_RECORD")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "OCCUPATION_RECORD_UNMATERIALIZED")

    def test_015_unknown_skill_fail_closed(self):
        result = registry.resolve_skill("NOT_A_REAL_SKILL")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "SKILL_RECORD_UNMATERIALIZED")

    def test_016_fighting_family_materialized(self):
        self.assertTrue(registry._family_is_materialized("FIGHTING"))

    def test_017_firearms_family_materialized(self):
        self.assertTrue(registry._family_is_materialized("FIREARMS"))

    def test_018_unknown_family_not_materialized(self):
        self.assertFalse(registry._family_is_materialized("IMAGINARY"))

    def test_019_source_pages_limited_to_verified_range(self):
        allowed = {73, 74, 75, 77, 78, 79}
        self.assertTrue(all(record["source_page"] in allowed for record in registry.OCCUPATIONS.values()))

    def test_020_copyright_boundary_has_no_source_descriptions(self):
        serialized = json.dumps(MANIFEST).lower()
        self.assertNotIn("suggested_contacts", serialized)
        self.assertNotIn("occupation_description", serialized)
        self.assertIn("structured mechanics/provenance only", MANIFEST["copyright_boundary"].lower())

    def test_021_big_game_hunter_structure(self):
        record = registry.OCCUPATIONS["BIG_GAME_HUNTER"]
        self.assertEqual(record["credit_rating"], [20, 50])
        self.assertEqual(record["skill_slots"][0]["skill_family"], "FIREARMS")
        self.assertEqual(record["skill_slots"][5]["specialization_choice"], ["BIOLOGY", "BOTANY", "ZOOLOGY"])

    def test_022_bounty_hunter_repair_choice(self):
        record = registry.OCCUPATIONS["BOUNTY_HUNTER"]
        self.assertEqual(
            record["skill_slots"][1]["choice_one_of"],
            [{"skill": "ELECTRONICS"}, {"skill": "ELECTRICAL_REPAIR"}],
        )

    def test_023_dilettante_credit(self):
        self.assertEqual(registry.OCCUPATIONS["DILETTANTE"]["credit_rating"], [50, 99])

    def test_024_doctor_sciences_are_two_slots(self):
        skills = registry.OCCUPATIONS["DOCTOR_MEDICINE"]["skill_slots"]
        sciences = [x.get("specialization") for x in skills if x.get("skill") == "SCIENCE"]
        self.assertEqual(sciences, ["BIOLOGY", "PHARMACY"])

    def test_025_engineer_sciences_are_two_slots(self):
        skills = registry.OCCUPATIONS["ENGINEER"]["skill_slots"]
        sciences = [x.get("specialization") for x in skills if x.get("skill") == "SCIENCE"]
        self.assertEqual(sciences, ["ENGINEERING", "PHYSICS"])

    def test_026_drifter_has_three_way_characteristic_choice(self):
        terms = registry.OCCUPATIONS["DRIFTER"]["points_formula"]["terms"]
        self.assertEqual(terms[1]["choice_one_of"], ["APP", "DEX", "STR"])

    def test_027_invalid_choice_characteristic_blocks(self):
        result = registry.resolve_occupation(
            "DRIFTER", characteristics=SAMPLE, choice_characteristic="POW"
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "OCCUPATION_CHARACTERISTIC_CHOICE_REQUIRED")

    def test_028_missing_choice_characteristic_blocks(self):
        result = registry.resolve_occupation("BIG_GAME_HUNTER", characteristics=SAMPLE)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "OCCUPATION_CHARACTERISTIC_CHOICE_REQUIRED")

    def test_029_spurious_choice_characteristic_blocks(self):
        result = registry.resolve_occupation("BOOK_DEALER", characteristics=SAMPLE, choice_characteristic="DEX")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "OCCUPATION_CHARACTERISTIC_CHOICE_NOT_USED")

    def test_030_invalid_characteristic_blocks(self):
        bad = dict(SAMPLE)
        bad["EDU"] = 101
        result = registry.resolve_occupation("BOOK_DEALER", characteristics=bad)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "EDU_INVALID")

    def test_031_all_records_have_valid_credit_ranges(self):
        for occupation_id, record in registry.OCCUPATIONS.items():
            with self.subTest(occupation_id=occupation_id):
                lo, hi = record["credit_rating"]
                self.assertTrue(0 <= lo <= hi <= 99)

    def test_032_no_duplicate_batch1_occupation_ids(self):
        self.assertFalse(set(registry.OCCUPATIONS) & set(registry.batch1.OCCUPATIONS))

    def test_033_registry_summary_non_authoritative(self):
        summary = registry.registry_summary()
        self.assertFalse(summary["authority_promoted"])
        self.assertFalse(summary["frozen_parent_modified"])

    def test_034_personal_slots_do_not_grant_any_skill(self):
        # Registry stores slot entitlement only; it does not auto-select or grant a skill.
        serialized = json.dumps(registry.OCCUPATIONS)
        self.assertNotIn('"auto_grant": true', serialized.lower())

    def test_035_no_equipment_or_weapon_possession_in_batch(self):
        serialized = json.dumps(MANIFEST).lower()
        self.assertNotIn("inventory", serialized)
        self.assertNotIn("auto_possession", serialized)

    def test_036_parent_frozen_registry_id_preserved(self):
        self.assertEqual(MANIFEST["frozen_ancestor_registry_id"], "COC7_RECOVERY_REGISTRY_R1_C4_V1")


# Generate four focused tests for every occupation: slot count, references,
# credit range, and occupation-point formula. 23 x 4 = 92 generated tests.
def _choice_for(record: dict) -> str | None:
    for term in record["points_formula"]["terms"]:
        if "choice_one_of" in term:
            return term["choice_one_of"][0]
    return None


def _make_slot_test(occupation_id: str):
    def test(self):
        self.assertEqual(registry.occupation_slot_count(registry.OCCUPATIONS[occupation_id]), 8)
    return test


def _make_reference_test(occupation_id: str):
    def test(self):
        result = registry.validate_record_references(occupation_id)
        self.assertEqual(result["status"], "VALIDATED", result)
        self.assertEqual(result["slot_count"], 8)
    return test


def _make_credit_test(occupation_id: str):
    def test(self):
        lo, hi = registry.OCCUPATIONS[occupation_id]["credit_rating"]
        self.assertTrue(0 <= lo <= hi <= 99)
    return test


def _make_points_test(occupation_id: str):
    def test(self):
        record = registry.OCCUPATIONS[occupation_id]
        choice = _choice_for(record)
        result = registry.resolve_occupation(
            occupation_id,
            characteristics=SAMPLE,
            choice_characteristic=choice,
            era="MODERN",
        )
        self.assertEqual(result["status"], "RESOLVED", result)
        self.assertEqual(result["record"]["occupation_skill_points"], 200)
    return test


for _occupation_id in sorted(registry.OCCUPATIONS):
    _safe = _occupation_id.lower()
    setattr(RegistryBatch2StaticTests, f"test_slot_{_safe}", _make_slot_test(_occupation_id))
    setattr(RegistryBatch2StaticTests, f"test_refs_{_safe}", _make_reference_test(_occupation_id))
    setattr(RegistryBatch2StaticTests, f"test_credit_{_safe}", _make_credit_test(_occupation_id))
    setattr(RegistryBatch2StaticTests, f"test_points_{_safe}", _make_points_test(_occupation_id))


if __name__ == "__main__":
    unittest.main(verbosity=2)
