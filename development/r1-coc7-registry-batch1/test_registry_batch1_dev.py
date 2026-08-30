from __future__ import annotations

import json
import unittest
from pathlib import Path

import registry_batch1_dev as reg

HERE = Path(__file__).resolve().parent
RAW = json.loads((HERE / "occupations_batch1.json").read_text(encoding="utf-8"))


class RegistryBatch1DevTests(unittest.TestCase):
    def test_01_batch_has_eleven_occupations(self):
        self.assertEqual(len(reg.OCCUPATIONS), 11)

    def test_02_expected_ids(self):
        self.assertEqual(set(reg.OCCUPATIONS), {
            "ALIENIST", "ANIMAL_TRAINER", "ANTIQUARIAN", "ANTIQUE_DEALER", "ARCHAEOLOGIST",
            "ARCHITECT", "ARTIST", "ASYLUM_ATTENDANT", "ATHLETE", "AUTHOR", "BARTENDER",
        })

    def test_03_source_hash_is_exact_investigator_handbook(self):
        self.assertEqual(reg.SOURCE_SHA256, "de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17")

    def test_04_parent_registry_is_frozen_c4(self):
        self.assertEqual(reg.PARENT_REGISTRY_ID, "COC7_RECOVERY_REGISTRY_R1_C4_V1")
        self.assertFalse(reg.registry_summary()["frozen_parent_modified"])

    def test_05_four_skill_extensions_only(self):
        self.assertEqual(set(reg.SKILL_EXTENSIONS), {"ANIMAL_HANDLING", "ART_CRAFT", "COMPUTER_USE", "LANGUAGE_OWN"})

    def test_06_animal_handling_base(self):
        r = reg.resolve_skill("ANIMAL_HANDLING")
        self.assertEqual(r["status"], "RESOLVED")
        self.assertEqual(r["record"]["base"], 5)

    def test_07_art_craft_is_specialization(self):
        r = reg.resolve_skill("ART_CRAFT")
        self.assertEqual(r["record"]["base"], 5)
        self.assertTrue(r["record"]["specialization"])

    def test_08_own_language_equals_edu(self):
        r = reg.resolve_skill("LANGUAGE_OWN", edu=65)
        self.assertEqual(r["status"], "RESOLVED")
        self.assertEqual(r["record"]["base"], 65)

    def test_09_own_language_requires_valid_edu(self):
        r = reg.resolve_skill("LANGUAGE_OWN")
        self.assertEqual(r["code"], "OWN_LANGUAGE_REQUIRES_VALID_EDU")

    def test_10_computer_use_is_modern(self):
        self.assertEqual(reg.resolve_skill("COMPUTER_USE", era="MODERN")["status"], "RESOLVED")
        self.assertEqual(reg.resolve_skill("COMPUTER_USE", era="1920S")["code"], "SKILL_NOT_AVAILABLE_IN_ERA")

    def test_11_parent_skill_still_resolves(self):
        r = reg.resolve_skill("APPRAISE")
        self.assertEqual(r["status"], "RESOLVED")
        self.assertEqual(r["record"]["base"], 5)

    def test_12_unknown_skill_fails_closed(self):
        self.assertEqual(reg.resolve_skill("MADE_UP_SKILL")["code"], "SKILL_RECORD_UNMATERIALIZED")

    def test_13_all_occupations_have_eight_slots(self):
        for oid, record in reg.OCCUPATIONS.items():
            with self.subTest(occupation=oid):
                self.assertEqual(reg.occupation_slot_count(record), 8)

    def test_14_all_fixed_skill_references_resolve(self):
        for oid in reg.OCCUPATIONS:
            with self.subTest(occupation=oid):
                self.assertEqual(reg.validate_record_references(oid)["status"], "VALIDATED")

    def test_15_archaeologist_matches_frozen_parent_contract(self):
        self.assertEqual(reg.archaeology_parent_compatibility()["status"], "PASS")

    def test_16_alienist_formula(self):
        r = reg.resolve_occupation("ALIENIST", characteristics={"EDU": 60})
        self.assertEqual(r["record"]["occupation_skill_points"], 240)
        self.assertEqual(r["record"]["credit_rating"], [10, 60])

    def test_17_animal_trainer_app_formula(self):
        r = reg.resolve_occupation("ANIMAL_TRAINER", characteristics={"EDU": 60, "APP": 50, "POW": 70}, choice_characteristic="APP")
        self.assertEqual(r["record"]["occupation_skill_points"], 220)

    def test_18_animal_trainer_pow_formula(self):
        r = reg.resolve_occupation("ANIMAL_TRAINER", characteristics={"EDU": 60, "APP": 50, "POW": 70}, choice_characteristic="POW")
        self.assertEqual(r["record"]["occupation_skill_points"], 260)

    def test_19_animal_trainer_choice_required(self):
        r = reg.resolve_occupation("ANIMAL_TRAINER", characteristics={"EDU": 60, "APP": 50, "POW": 70})
        self.assertEqual(r["code"], "OCCUPATION_CHARACTERISTIC_CHOICE_REQUIRED")

    def test_20_animal_trainer_rejects_dex_choice(self):
        r = reg.resolve_occupation("ANIMAL_TRAINER", characteristics={"EDU": 60, "DEX": 50}, choice_characteristic="DEX")
        self.assertEqual(r["code"], "OCCUPATION_CHARACTERISTIC_CHOICE_REQUIRED")

    def test_21_antiquarian_formula_credit(self):
        r = reg.resolve_occupation("ANTIQUARIAN", characteristics={"EDU": 55})
        self.assertEqual(r["record"]["occupation_skill_points"], 220)
        self.assertEqual(r["record"]["credit_rating"], [30, 70])

    def test_22_antique_dealer_is_edu_x4(self):
        r = reg.resolve_occupation("ANTIQUE_DEALER", characteristics={"EDU": 60})
        self.assertEqual(r["record"]["occupation_skill_points"], 240)
        self.assertEqual(r["record"]["credit_rating"], [30, 50])

    def test_23_antique_dealer_contains_navigate(self):
        slots = reg.OCCUPATIONS["ANTIQUE_DEALER"]["skill_slots"]
        self.assertIn({"skill": "NAVIGATE"}, slots)

    def test_24_antique_dealer_has_two_interpersonal_slots(self):
        slots = reg.OCCUPATIONS["ANTIQUE_DEALER"]["skill_slots"]
        row = next(s for s in slots if s.get("interpersonal_choice"))
        self.assertEqual(row["count"], 2)

    def test_25_archaeologist_formula(self):
        r = reg.resolve_occupation("ARCHAEOLOGIST", characteristics={"EDU": 70})
        self.assertEqual(r["record"]["occupation_skill_points"], 280)
        self.assertEqual(r["record"]["credit_rating"], [10, 40])

    def test_26_archaeologist_last_slot_is_navigate_or_science(self):
        slot = reg.OCCUPATIONS["ARCHAEOLOGIST"]["skill_slots"][-1]
        self.assertEqual(slot["choice_one_of"], [{"skill": "NAVIGATE"}, {"skill": "SCIENCE", "specialization": "ANY"}])

    def test_27_architect_formula_credit(self):
        r = reg.resolve_occupation("ARCHITECT", characteristics={"EDU": 65})
        self.assertEqual(r["record"]["occupation_skill_points"], 260)
        self.assertEqual(r["record"]["credit_rating"], [30, 70])

    def test_28_architect_has_computer_or_library_choice(self):
        slots = reg.OCCUPATIONS["ARCHITECT"]["skill_slots"]
        self.assertIn({"choice_one_of": [{"skill": "COMPUTER_USE"}, {"skill": "LIBRARY_USE"}]}, slots)

    def test_29_artist_dex_formula(self):
        r = reg.resolve_occupation("ARTIST", characteristics={"EDU": 50, "DEX": 70, "POW": 60}, choice_characteristic="DEX")
        self.assertEqual(r["record"]["occupation_skill_points"], 240)

    def test_30_artist_pow_formula(self):
        r = reg.resolve_occupation("ARTIST", characteristics={"EDU": 50, "DEX": 70, "POW": 60}, choice_characteristic="POW")
        self.assertEqual(r["record"]["occupation_skill_points"], 220)

    def test_31_artist_has_two_personal_specialties(self):
        slots = reg.OCCUPATIONS["ARTIST"]["skill_slots"]
        row = next(s for s in slots if s.get("personal_or_era_specialty"))
        self.assertEqual(row["count"], 2)

    def test_32_asylum_attendant_str_formula(self):
        r = reg.resolve_occupation("ASYLUM_ATTENDANT", characteristics={"EDU": 50, "STR": 70, "DEX": 60}, choice_characteristic="STR")
        self.assertEqual(r["record"]["occupation_skill_points"], 240)

    def test_33_asylum_attendant_dex_formula(self):
        r = reg.resolve_occupation("ASYLUM_ATTENDANT", characteristics={"EDU": 50, "STR": 70, "DEX": 60}, choice_characteristic="DEX")
        self.assertEqual(r["record"]["occupation_skill_points"], 220)

    def test_34_asylum_attendant_contains_dodge_not_electrical_repair(self):
        slots = reg.OCCUPATIONS["ASYLUM_ATTENDANT"]["skill_slots"]
        self.assertIn({"skill": "DODGE"}, slots)
        self.assertNotIn({"skill": "ELECTRICAL_REPAIR"}, slots)

    def test_35_athlete_dex_formula(self):
        r = reg.resolve_occupation("ATHLETE", characteristics={"EDU": 55, "DEX": 65, "STR": 70}, choice_characteristic="DEX")
        self.assertEqual(r["record"]["occupation_skill_points"], 240)

    def test_36_athlete_str_formula(self):
        r = reg.resolve_occupation("ATHLETE", characteristics={"EDU": 55, "DEX": 65, "STR": 70}, choice_characteristic="STR")
        self.assertEqual(r["record"]["occupation_skill_points"], 250)

    def test_37_athlete_has_interpersonal_slot(self):
        self.assertTrue(any(s.get("interpersonal_choice") for s in reg.OCCUPATIONS["ATHLETE"]["skill_slots"]))

    def test_38_author_formula_credit(self):
        r = reg.resolve_occupation("AUTHOR", characteristics={"EDU": 70})
        self.assertEqual(r["record"]["occupation_skill_points"], 280)
        self.assertEqual(r["record"]["credit_rating"], [9, 30])

    def test_39_author_art_literature(self):
        self.assertEqual(reg.OCCUPATIONS["AUTHOR"]["skill_slots"][0], {"skill": "ART_CRAFT", "specialization": "LITERATURE"})

    def test_40_author_natural_world_or_occult(self):
        slot = reg.OCCUPATIONS["AUTHOR"]["skill_slots"][3]
        self.assertEqual(slot["choice_one_of"], [{"skill": "NATURAL_WORLD"}, {"skill": "OCCULT"}])

    def test_41_bartender_formula(self):
        r = reg.resolve_occupation("BARTENDER", characteristics={"EDU": 50, "APP": 60})
        self.assertEqual(r["record"]["occupation_skill_points"], 220)
        self.assertEqual(r["record"]["credit_rating"], [8, 25])

    def test_42_bartender_has_two_interpersonal_slots(self):
        row = next(s for s in reg.OCCUPATIONS["BARTENDER"]["skill_slots"] if s.get("interpersonal_choice"))
        self.assertEqual(row["count"], 2)

    def test_43_choice_not_used_rejected_for_edu_x4(self):
        r = reg.resolve_occupation("ALIENIST", characteristics={"EDU": 60}, choice_characteristic="APP")
        self.assertEqual(r["code"], "OCCUPATION_CHARACTERISTIC_CHOICE_NOT_USED")

    def test_44_invalid_characteristic_rejected(self):
        r = reg.resolve_occupation("ALIENIST", characteristics={"EDU": 101})
        self.assertEqual(r["code"], "EDU_INVALID")

    def test_45_bool_is_not_characteristic(self):
        r = reg.resolve_occupation("ALIENIST", characteristics={"EDU": True})
        self.assertEqual(r["code"], "EDU_INVALID")

    def test_46_unknown_occupation_fails_closed(self):
        r = reg.resolve_occupation("OCCULT_SUPERHERO", characteristics={"EDU": 60})
        self.assertEqual(r["code"], "OCCUPATION_RECORD_UNMATERIALIZED")

    def test_47_records_carry_source_pages(self):
        self.assertEqual(reg.OCCUPATIONS["ALIENIST"]["source_page"], 71)
        self.assertEqual(reg.OCCUPATIONS["ARCHITECT"]["source_page"], 72)
        self.assertIn(reg.OCCUPATIONS["BARTENDER"]["source_page"], (72, 73))

    def test_48_no_source_prose_fields_embedded(self):
        serialized = json.dumps(RAW, sort_keys=True)
        for forbidden_key in ('"description"', '"suggested_contacts"', '"source_text"', '"quote"'):
            self.assertNotIn(forbidden_key, serialized)

    def test_49_registry_summary_is_non_authoritative(self):
        s = reg.registry_summary()
        self.assertEqual(s["occupation_batch"], 11)
        self.assertEqual(s["skill_extensions"], 4)
        self.assertFalse(s["authority_promoted"])

    def test_50_raw_batch_is_not_frozen(self):
        self.assertEqual(RAW["status"], "DEV_SOURCE_GROUNDED_NOT_FROZEN")
        self.assertFalse(RAW["authority_promoted"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
