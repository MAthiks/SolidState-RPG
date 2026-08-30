from __future__ import annotations

import json
import unittest
from pathlib import Path

import registry_batch3_dev as registry

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "occupations_batch3.json").read_text(encoding="utf-8"))
SPANS = json.loads((HERE / "source_spans_batch3.json").read_text(encoding="utf-8"))
SAMPLE = {"EDU": 50, "DEX": 50, "STR": 50, "APP": 50, "POW": 50}


class RegistryBatch3StaticTests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(registry.REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_BATCH3_DEV_V1")
        self.assertEqual(registry.PARENT_REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_BATCH2_DEV_V1")
        self.assertEqual(registry.FROZEN_ANCESTOR_REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_C4_V1")

    def test_002_source_identity(self):
        self.assertEqual(registry.SOURCE_ID, "COC7_INVESTIGATOR")
        self.assertEqual(
            registry.SOURCE_SHA256,
            "de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17",
        )

    def test_003_non_authoritative(self):
        self.assertEqual(MANIFEST["status"], "DEV_SOURCE_GROUNDED_NOT_FROZEN")
        self.assertFalse(MANIFEST["authority_promoted"])
        self.assertFalse(SPANS["authority_promoted"])

    def test_004_batch_size(self):
        self.assertEqual(len(registry.OCCUPATIONS), 24)

    def test_005_cumulative_size(self):
        self.assertEqual(registry.registry_summary()["cumulative_occupations"], 58)

    def test_006_parent_compatibility(self):
        result = registry.batch2_compatibility()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checked"], 34)

    def test_007_sleight_of_hand_materialized(self):
        result = registry.resolve_skill("SLEIGHT_OF_HAND")
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["record"]["base"], 10)

    def test_008_parent_survival_resolves(self):
        self.assertEqual(registry.resolve_skill("SURVIVAL")["record"]["base"], 10)

    def test_009_parent_pilot_resolves(self):
        self.assertEqual(registry.resolve_skill("PILOT")["record"]["base"], 1)

    def test_010_parent_computer_use_classic_block_still_active(self):
        result = registry.resolve_skill("COMPUTER_USE", era="1920S")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "SKILL_NOT_AVAILABLE_IN_ERA")

    def test_011_explorer_classic_only(self):
        self.assertEqual(registry.resolve_occupation("EXPLORER", era="CLASSIC")["status"], "RESOLVED")
        blocked = registry.resolve_occupation("EXPLORER", era="MODERN")
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["code"], "OCCUPATION_NOT_AVAILABLE_IN_ERA")

    def test_012_aviator_classic_only(self):
        self.assertEqual(registry.resolve_occupation("AVIATOR", era="1920S")["status"], "RESOLVED")
        self.assertEqual(registry.resolve_occupation("AVIATOR", era="MODERN")["status"], "BLOCKED")

    def test_013_parent_hacker_modern_gate_survives(self):
        blocked = registry.resolve_occupation("HACKER", era="CLASSIC")
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["code"], "OCCUPATION_NOT_AVAILABLE_IN_ERA")

    def test_014_parent_archaeologist_delegates_unchanged(self):
        direct = registry.batch2.resolve_occupation("ARCHAEOLOGIST")
        through = registry.resolve_occupation("ARCHAEOLOGIST")
        self.assertEqual(direct["record"], through["record"])
        self.assertEqual(through["delegated_through_registry_id"], registry.REGISTRY_ID)

    def test_015_unknown_occupation_fail_closed(self):
        result = registry.resolve_occupation("UNKNOWN_OCCUPATION")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "OCCUPATION_RECORD_UNMATERIALIZED")

    def test_016_unknown_skill_fail_closed(self):
        result = registry.resolve_skill("UNKNOWN_SKILL")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["code"], "SKILL_RECORD_UNMATERIALIZED")

    def test_017_firearms_family_materialized(self):
        self.assertTrue(registry._family_is_materialized("FIREARMS"))

    def test_018_fighting_family_materialized(self):
        self.assertTrue(registry._family_is_materialized("FIGHTING"))

    def test_019_source_spans_exact(self):
        self.assertEqual(SPANS["multi_page_records"]["FORENSIC_SURGEON"], [80, 81])
        self.assertEqual(SPANS["multi_page_records"]["PARAPSYCHOLOGIST"], [85, 86])
        self.assertEqual(SPANS["multi_page_records"]["PILOT"], [86, 87])
        self.assertEqual(SPANS["multi_page_records"]["AVIATOR"], [86, 87])

    def test_020_source_pages_cover_full_spans(self):
        self.assertEqual(SPANS["source_pages_used"], [80, 81, 82, 85, 86, 87])

    def test_021_forensic_surgeon_three_sciences(self):
        record = registry.OCCUPATIONS["FORENSIC_SURGEON"]
        sciences = [s.get("specialization") for s in record["skill_slots"] if s.get("skill") == "SCIENCE"]
        self.assertEqual(sciences, ["BIOLOGY", "FORENSICS", "PHARMACY"])

    def test_022_gambler_sleight_of_hand(self):
        skills = registry.OCCUPATIONS["GAMBLER"]["skill_slots"]
        self.assertIn({"skill": "SLEIGHT_OF_HAND"}, skills)

    def test_023_gangster_boss_credit(self):
        self.assertEqual(registry.OCCUPATIONS["GANGSTER_BOSS"]["credit_rating"], [60, 95])

    def test_024_gentleman_rifle_or_shotgun(self):
        record = registry.OCCUPATIONS["GENTLEMAN_LADY"]
        choice = record["skill_slots"][2]["choice_one_of"]
        self.assertEqual(choice, [{"skill": "FIREARMS_RIFLE"}, {"skill": "FIREARMS_SHOTGUN"}])

    def test_025_hobo_choice_is_app_or_dex(self):
        terms = registry.OCCUPATIONS["HOBO"]["points_formula"]["terms"]
        self.assertEqual(terms[1]["choice_one_of"], ["APP", "DEX"])

    def test_026_hospital_orderly_credit(self):
        self.assertEqual(registry.OCCUPATIONS["HOSPITAL_ORDERLY"]["credit_rating"], [6, 15])

    def test_027_judge_exact_eight_fixed_skills(self):
        record = registry.OCCUPATIONS["JUDGE"]
        self.assertEqual(registry.occupation_slot_count(record), 8)
        self.assertFalse(any(slot.get("personal_or_era_specialty") for slot in record["skill_slots"]))

    def test_028_pilot_aircraft_specialization(self):
        record = registry.OCCUPATIONS["PILOT"]
        self.assertIn({"skill": "PILOT", "specialization": "AIRCRAFT"}, record["skill_slots"])

    def test_029_police_credit_ranges(self):
        self.assertEqual(registry.OCCUPATIONS["POLICE_DETECTIVE"]["credit_rating"], [20, 50])
        self.assertEqual(registry.OCCUPATIONS["UNIFORMED_POLICE_OFFICER"]["credit_rating"], [9, 30])

    def test_030_private_investigator_credit(self):
        self.assertEqual(registry.OCCUPATIONS["PRIVATE_INVESTIGATOR"]["credit_rating"], [9, 30])

    def test_031_no_duplicate_parent_occupation_ids(self):
        parent_ids = registry._parent_occupation_ids()
        self.assertFalse(set(registry.OCCUPATIONS) & parent_ids)

    def test_032_copyright_and_no_auto_possession(self):
        serialized = json.dumps(MANIFEST).lower()
        self.assertNotIn("suggested_contacts", serialized)
        self.assertNotIn("inventory", serialized)
        self.assertNotIn("auto_possession", serialized)
        self.assertIn("structured mechanics/provenance only", MANIFEST["copyright_boundary"].lower())


# Four tests per occupation: slot count, references, credit range, points formula.
# 24 x 4 = 96 generated tests; with 32 static tests => 128 total.
def _choice_for(record: dict) -> str | None:
    for term in record["points_formula"]["terms"]:
        if "choice_one_of" in term:
            return term["choice_one_of"][0]
    return None


def _era_for(record: dict) -> str | None:
    if record.get("era_scope") == "CLASSIC":
        return "CLASSIC"
    if record.get("era_scope") == "MODERN":
        return "MODERN"
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
            era=_era_for(record),
        )
        self.assertEqual(result["status"], "RESOLVED", result)
        self.assertEqual(result["record"]["occupation_skill_points"], 200)
    return test


for _occupation_id in sorted(registry.OCCUPATIONS):
    _safe = _occupation_id.lower()
    setattr(RegistryBatch3StaticTests, f"test_slot_{_safe}", _make_slot_test(_occupation_id))
    setattr(RegistryBatch3StaticTests, f"test_refs_{_safe}", _make_reference_test(_occupation_id))
    setattr(RegistryBatch3StaticTests, f"test_credit_{_safe}", _make_credit_test(_occupation_id))
    setattr(RegistryBatch3StaticTests, f"test_points_{_safe}", _make_points_test(_occupation_id))


if __name__ == "__main__":
    unittest.main(verbosity=2)
