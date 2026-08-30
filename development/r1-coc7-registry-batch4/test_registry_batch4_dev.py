from __future__ import annotations

import json
import unittest
from pathlib import Path

import registry_batch4_dev as registry

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "occupations_batch4.json").read_text(encoding="utf-8"))
SPANS = json.loads((HERE / "source_spans_batch4.json").read_text(encoding="utf-8"))
SAMPLE = {"EDU": 50, "DEX": 50, "STR": 50, "APP": 50, "POW": 50}


class RegistryBatch4StaticTests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(registry.REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_BATCH4_DEV_V1")
        self.assertEqual(registry.PARENT_REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_BATCH3_DEV_V1")
        self.assertEqual(registry.FROZEN_ANCESTOR_REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_C4_V1")

    def test_002_source_identity(self):
        self.assertEqual(registry.SOURCE_ID, "COC7_INVESTIGATOR")
        self.assertEqual(registry.SOURCE_SHA256, "de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17")

    def test_003_non_authoritative(self):
        self.assertEqual(MANIFEST["status"], "DEV_SOURCE_GROUNDED_NOT_FROZEN")
        self.assertFalse(MANIFEST["authority_promoted"])
        self.assertFalse(SPANS["authority_promoted"])

    def test_004_batch_size(self):
        self.assertEqual(len(registry.OCCUPATIONS), 39)

    def test_005_cumulative_size(self):
        self.assertEqual(registry.registry_summary()["cumulative_occupations"], 97)

    def test_006_parent_compatibility(self):
        result = registry.batch3_compatibility()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checked"], 58)

    def test_007_chainsaw_materialized(self):
        result = registry.resolve_skill("FIGHTING_CHAINSAW")
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["record"]["base"], 10)
        self.assertTrue(result["record"]["specialization"])

    def test_008_parent_sleight_resolves(self):
        self.assertEqual(registry.resolve_skill("SLEIGHT_OF_HAND")["record"]["base"], 10)

    def test_009_science_family_materialized(self):
        self.assertTrue(registry._family_is_materialized("SCIENCE"))

    def test_010_fighting_family_materialized(self):
        self.assertTrue(registry._family_is_materialized("FIGHTING"))

    def test_011_firearms_family_materialized(self):
        self.assertTrue(registry._family_is_materialized("FIREARMS"))

    def test_012_unknown_family_blocked(self):
        self.assertFalse(registry._family_is_materialized("IMAGINARY"))

    def test_013_parent_archaeologist_unchanged(self):
        direct = registry.batch3.resolve_occupation("ARCHAEOLOGIST")
        through = registry.resolve_occupation("ARCHAEOLOGIST")
        self.assertEqual(direct["record"], through["record"])
        self.assertEqual(through["delegated_through_registry_id"], registry.REGISTRY_ID)

    def test_014_parent_hacker_classic_gate_unchanged(self):
        result = registry.resolve_occupation("HACKER", era="CLASSIC")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "OCCUPATION_NOT_AVAILABLE_IN_ERA")

    def test_015_parent_explorer_modern_gate_unchanged(self):
        result = registry.resolve_occupation("EXPLORER", era="MODERN")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "OCCUPATION_NOT_AVAILABLE_IN_ERA")

    def test_016_unknown_occupation_fail_closed(self):
        result = registry.resolve_occupation("UNKNOWN_OCCUPATION")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "OCCUPATION_RECORD_UNMATERIALIZED")

    def test_017_unknown_skill_fail_closed(self):
        result = registry.resolve_skill("UNKNOWN_SKILL")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "SKILL_RECORD_UNMATERIALIZED")

    def test_018_source_pages_exact(self):
        self.assertEqual(MANIFEST["source"]["source_pages"], [83, 84, 85, 88, 89, 90, 91, 93])

    def test_019_source_spans_exact(self):
        self.assertEqual(SPANS["multi_page_records"]["MECHANIC_SKILLED_TRADES"], [83, 84])
        self.assertEqual(SPANS["multi_page_records"]["SPY"], [90, 91])

    def test_020_laboratory_assistant_three_science_slots(self):
        slots = registry.OCCUPATIONS["LABORATORY_ASSISTANT"]["skill_slots"]
        science_count = sum(s.get("count", 1) for s in slots if s.get("skill_family") == "SCIENCE")
        self.assertEqual(science_count, 3)

    def test_021_lumberjack_chainsaw(self):
        self.assertIn({"skill": "FIGHTING_CHAINSAW"}, registry.OCCUPATIONS["LUMBERJACK"]["skill_slots"])

    def test_022_miner_geology(self):
        self.assertIn({"skill": "SCIENCE", "specialization": "GEOLOGY"}, registry.OCCUPATIONS["MINER"]["skill_slots"])

    def test_023_lawyer_two_interpersonal(self):
        slots = registry.OCCUPATIONS["LAWYER"]["skill_slots"]
        self.assertIn({"interpersonal_choice": True, "count": 2}, slots)

    def test_024_librarian_four_specialties(self):
        slots = registry.OCCUPATIONS["LIBRARIAN"]["skill_slots"]
        self.assertEqual(slots[-1]["count"], 4)
        self.assertTrue(slots[-1]["specialist_reading_topic_allowed"])

    def test_025_military_officer_credit(self):
        self.assertEqual(registry.OCCUPATIONS["MILITARY_OFFICER"]["credit_rating"], [20, 70])

    def test_026_museum_curator_fixed_eight(self):
        self.assertEqual(registry.occupation_slot_count(registry.OCCUPATIONS["MUSEUM_CURATOR"]), 8)

    def test_027_occultist_mythos_is_keeper_authorized_only(self):
        slot = registry.OCCUPATIONS["OCCULTIST"]["skill_slots"][-1]
        self.assertTrue(slot["personal_or_era_specialty"])
        self.assertEqual(slot["keeper_authorized_option"]["skill"], "CTHULHU_MYTHOS")
        self.assertEqual(slot["keeper_authorized_option"]["advised_starting_max"], 10)
        self.assertNotIn("auto_grant", slot)

    def test_028_professor_four_academic_specialties(self):
        self.assertEqual(registry.OCCUPATIONS["PROFESSOR"]["skill_slots"][-1]["count"], 4)

    def test_029_psychiatrist_sciences(self):
        slots = registry.OCCUPATIONS["PSYCHIATRIST"]["skill_slots"]
        sciences = [x.get("specialization") for x in slots if x.get("skill") == "SCIENCE"]
        self.assertEqual(sciences, ["BIOLOGY", "CHEMISTRY"])

    def test_030_researcher_three_fields(self):
        slots = registry.OCCUPATIONS["RESEARCHER"]["skill_slots"]
        self.assertEqual([s for s in slots if s.get("field_of_study")][0]["count"], 3)

    def test_031_naval_sailor_repair_choice(self):
        choice = registry.OCCUPATIONS["SAILOR_NAVAL"]["skill_slots"][0]["choice_one_of"]
        self.assertEqual(choice, [{"skill": "ELECTRICAL_REPAIR"}, {"skill": "MECHANICAL_REPAIR"}])

    def test_032_scientist_three_sciences(self):
        first = registry.OCCUPATIONS["SCIENTIST"]["skill_slots"][0]
        self.assertEqual(first["skill_family"], "SCIENCE")
        self.assertEqual(first["count"], 3)

    def test_033_secretary_library_or_computer(self):
        slot = registry.OCCUPATIONS["SECRETARY"]["skill_slots"][4]
        self.assertEqual(slot["choice_one_of"], [{"skill": "LIBRARY_USE"}, {"skill": "COMPUTER_USE"}])

    def test_034_soldier_choose_two_of_three(self):
        slot = registry.OCCUPATIONS["SOLDIER_MARINE"]["skill_slots"][-1]
        self.assertEqual(slot["choice_n_of"]["n"], 2)
        self.assertEqual(slot["count"], 2)
        self.assertEqual(len(slot["choice_n_of"]["choices"]), 3)

    def test_035_spy_has_sleight_and_stealth(self):
        slots = registry.OCCUPATIONS["SPY"]["skill_slots"]
        self.assertIn({"skill": "SLEIGHT_OF_HAND"}, slots)
        self.assertIn({"skill": "STEALTH"}, slots)

    def test_036_student_three_fields_two_specialties(self):
        slots = registry.OCCUPATIONS["STUDENT_INTERN"]["skill_slots"]
        self.assertEqual([s for s in slots if s.get("field_of_study")][0]["count"], 3)
        self.assertEqual([s for s in slots if s.get("personal_or_era_specialty")][0]["count"], 2)

    def test_037_stuntman_final_choice(self):
        choices = registry.OCCUPATIONS["STUNTMAN"]["skill_slots"][-1]["choice_one_of"]
        skills = {x["skill"] for x in choices}
        self.assertEqual(skills, {"DIVING", "DRIVE_AUTO", "PILOT", "RIDE"})

    def test_038_undertaker_two_sciences(self):
        slots = registry.OCCUPATIONS["UNDERTAKER"]["skill_slots"]
        sciences = [x.get("specialization") for x in slots if x.get("skill") == "SCIENCE"]
        self.assertEqual(sciences, ["BIOLOGY", "CHEMISTRY"])

    def test_039_union_activist_brawl(self):
        self.assertIn({"skill": "FIGHTING_BRAWL"}, registry.OCCUPATIONS["UNION_ACTIVIST"]["skill_slots"])

    def test_040_white_collar_two_distinct_records(self):
        self.assertIn("WHITE_COLLAR_CLERK_EXECUTIVE", registry.OCCUPATIONS)
        self.assertIn("WHITE_COLLAR_MANAGER", registry.OCCUPATIONS)
        self.assertNotEqual(
            registry.OCCUPATIONS["WHITE_COLLAR_CLERK_EXECUTIVE"]["credit_rating"],
            registry.OCCUPATIONS["WHITE_COLLAR_MANAGER"]["credit_rating"],
        )

    def test_041_zealot_app_or_pow(self):
        terms = registry.OCCUPATIONS["ZEALOT"]["points_formula"]["terms"]
        self.assertEqual(terms[1]["choice_one_of"], ["APP", "POW"])

    def test_042_zookeeper_sciences(self):
        slots = registry.OCCUPATIONS["ZOOKEEPER"]["skill_slots"]
        sciences = [x.get("specialization") for x in slots if x.get("skill") == "SCIENCE"]
        self.assertEqual(sciences, ["PHARMACY", "ZOOLOGY"])

    def test_043_no_duplicate_parent_ids(self):
        self.assertFalse(set(registry.OCCUPATIONS) & registry._parent_occupation_ids())

    def test_044_copyright_and_no_auto_possession(self):
        serialized = json.dumps(MANIFEST).lower()
        self.assertNotIn("suggested_contacts", serialized)
        self.assertNotIn("occupation_description", serialized)
        self.assertNotIn("inventory", serialized)
        self.assertNotIn("auto_possession", serialized)
        self.assertIn("structured mechanics/provenance only", MANIFEST["copyright_boundary"].lower())


# 39 occupations x four generic contract tests = 156 generated tests.
# 44 static + 156 generated = exactly 200 Batch4 tests.
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
        result = registry.resolve_occupation(
            occupation_id,
            characteristics=SAMPLE,
            choice_characteristic=_choice_for(record),
        )
        self.assertEqual(result["status"], "RESOLVED", result)
        self.assertEqual(result["record"]["occupation_skill_points"], 200)
    return test


for _occupation_id in sorted(registry.OCCUPATIONS):
    _safe = _occupation_id.lower()
    setattr(RegistryBatch4StaticTests, f"test_slot_{_safe}", _make_slot_test(_occupation_id))
    setattr(RegistryBatch4StaticTests, f"test_refs_{_safe}", _make_reference_test(_occupation_id))
    setattr(RegistryBatch4StaticTests, f"test_credit_{_safe}", _make_credit_test(_occupation_id))
    setattr(RegistryBatch4StaticTests, f"test_points_{_safe}", _make_points_test(_occupation_id))


if __name__ == "__main__":
    unittest.main(verbosity=2)
