from __future__ import annotations

import json
import unittest
from pathlib import Path

import registry_batch5_dev as registry

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "occupations_batch5.json").read_text(encoding="utf-8"))
SAMPLE = {"EDU":50,"DEX":50,"STR":50,"APP":50,"POW":50}


class RegistryBatch5Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(registry.REGISTRY_ID,"COC7_RECOVERY_REGISTRY_R1_BATCH5_DEV_V1")
        self.assertEqual(registry.PARENT_REGISTRY_ID,"COC7_RECOVERY_REGISTRY_R1_BATCH4_DEV_V1")
        self.assertEqual(registry.FROZEN_ANCESTOR_REGISTRY_ID,"COC7_RECOVERY_REGISTRY_R1_C4_V1")

    def test_002_source_identity(self):
        self.assertEqual(registry.SOURCE_ID,"COC7_INVESTIGATOR")
        self.assertEqual(registry.SOURCE_SHA256,"de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17")

    def test_003_non_authoritative(self):
        self.assertEqual(MANIFEST["status"],"DEV_SOURCE_GROUNDED_NOT_FROZEN")
        self.assertFalse(MANIFEST["authority_promoted"])

    def test_004_batch_size(self):
        self.assertEqual(len(registry.OCCUPATIONS),17)

    def test_005_cumulative_size(self):
        self.assertEqual(registry.registry_summary()["cumulative_occupations"],114)

    def test_006_parent_compatibility(self):
        r=registry.batch4_compatibility()
        self.assertEqual(r["status"],"PASS")
        self.assertEqual(r["checked"],97)

    def test_007_hypnosis(self):
        r=registry.resolve_skill("HYPNOSIS")
        self.assertEqual(r["status"],"RESOLVED")
        self.assertEqual(r["record"]["base"],1)
        self.assertTrue(r["record"]["uncommon"])
        self.assertEqual(r["record"]["source_pages"],[107,108])

    def test_008_actor_requires_variant(self):
        r=registry.resolve_occupation("ACTOR")
        self.assertEqual(r["code"],"OCCUPATION_VARIANT_REQUIRED")
        self.assertEqual(r["options"],["STAGE_ACTOR","FILM_STAR"])

    def test_009_criminal_requires_variant(self):
        r=registry.resolve_occupation("CRIMINAL")
        self.assertEqual(r["code"],"OCCUPATION_VARIANT_REQUIRED")
        self.assertEqual(len(r["options"]),11)

    def test_010_gangster_requires_variant(self):
        r=registry.resolve_occupation("GANGSTER")
        self.assertEqual(r["code"],"OCCUPATION_VARIANT_REQUIRED")
        self.assertEqual(r["options"],["GANGSTER_BOSS","GANGSTER_UNDERLING"])

    def test_011_journalist_requires_variant(self):
        self.assertEqual(registry.resolve_occupation("JOURNALIST")["code"],"OCCUPATION_VARIANT_REQUIRED")

    def test_012_sailor_requires_variant(self):
        self.assertEqual(registry.resolve_occupation("SAILOR")["code"],"OCCUPATION_VARIANT_REQUIRED")

    def test_013_white_collar_requires_variant(self):
        self.assertEqual(registry.resolve_occupation("WHITE_COLLAR_WORKER")["code"],"OCCUPATION_VARIANT_REQUIRED")

    def test_014_police_combined_requires_variant(self):
        self.assertEqual(registry.resolve_occupation("POLICE_DETECTIVE_OFFICER")["code"],"OCCUPATION_VARIANT_REQUIRED")

    def test_015_all_groups_validate(self):
        for group_id in registry.OCCUPATION_GROUPS:
            with self.subTest(group_id=group_id):
                self.assertEqual(registry.validate_group(group_id)["status"],"VALIDATED")

    def test_016_unknown_group_fail_closed(self):
        self.assertEqual(registry.validate_group("NOPE")["code"],"OCCUPATION_GROUP_UNKNOWN")

    def test_017_bootlegger_alias(self):
        r=registry.resolve_occupation("BOOTLEGGER")
        self.assertEqual(r["status"],"RESOLVED")
        self.assertEqual(r["canonical_occupation_id"],"BOOTLEGGER_THUG")

    def test_018_thug_alias(self):
        r=registry.resolve_occupation("THUG")
        self.assertEqual(r["canonical_occupation_id"],"BOOTLEGGER_THUG")

    def test_019_forger_alias(self):
        self.assertEqual(registry.resolve_occupation("FORGER")["canonical_occupation_id"],"FORGER_COUNTERFEITER")

    def test_020_counterfeiter_alias(self):
        self.assertEqual(registry.resolve_occupation("COUNTERFEITER")["canonical_occupation_id"],"FORGER_COUNTERFEITER")

    def test_021_unknown_occupation_fail_closed(self):
        r=registry.resolve_occupation("NOT_A_REAL_OCCUPATION")
        self.assertEqual(r["status"],"BLOCKED")
        self.assertEqual(r["code"],"OCCUPATION_RECORD_UNMATERIALIZED")

    def test_022_accountant_credit(self):
        self.assertEqual(registry.OCCUPATIONS["ACCOUNTANT"]["credit_rating"],[30,70])

    def test_023_acrobat_formula(self):
        terms=registry.OCCUPATIONS["ACROBAT"]["points_formula"]["terms"]
        self.assertEqual(terms,[{"characteristic":"EDU","multiplier":2},{"characteristic":"DEX","multiplier":2}])

    def test_024_stage_actor_credit(self):
        self.assertEqual(registry.OCCUPATIONS["STAGE_ACTOR"]["credit_rating"],[9,40])

    def test_025_film_star_credit(self):
        self.assertEqual(registry.OCCUPATIONS["FILM_STAR"]["credit_rating"],[20,90])

    def test_026_agency_detective_credit(self):
        self.assertEqual(registry.OCCUPATIONS["AGENCY_DETECTIVE"]["credit_rating"],[20,45])

    def test_027_assassin_credit(self):
        self.assertEqual(registry.OCCUPATIONS["ASSASSIN"]["credit_rating"],[30,60])

    def test_028_bank_robber_credit(self):
        self.assertEqual(registry.OCCUPATIONS["BANK_ROBBER"]["credit_rating"],[5,75])

    def test_029_bootlegger_thug_credit(self):
        self.assertEqual(registry.OCCUPATIONS["BOOTLEGGER_THUG"]["credit_rating"],[5,30])

    def test_030_burglar_credit(self):
        self.assertEqual(registry.OCCUPATIONS["BURGLAR"]["credit_rating"],[5,40])

    def test_031_conman_credit(self):
        self.assertEqual(registry.OCCUPATIONS["CONMAN"]["credit_rating"],[10,65])

    def test_032_freelance_criminal_interpersonal_excludes_persuade(self):
        slot=[s for s in registry.OCCUPATIONS["CRIMINAL_FREELANCE_SOLO"]["skill_slots"] if s.get("interpersonal_choice")][0]
        self.assertEqual(slot["allowed"],["CHARM","FAST_TALK","INTIMIDATE"])

    def test_033_gun_moll_classic(self):
        self.assertEqual(registry.resolve_occupation("GUN_MOLL",era="CLASSIC")["status"],"RESOLVED")
        self.assertEqual(registry.resolve_occupation("GUN_MOLL",era="MODERN")["code"],"OCCUPATION_NOT_AVAILABLE_IN_ERA")

    def test_034_fence_credit(self):
        self.assertEqual(registry.OCCUPATIONS["FENCE"]["credit_rating"],[20,40])

    def test_035_forger_credit(self):
        self.assertEqual(registry.OCCUPATIONS["FORGER_COUNTERFEITER"]["credit_rating"],[20,60])

    def test_036_smuggler_credit(self):
        self.assertEqual(registry.OCCUPATIONS["SMUGGLER"]["credit_rating"],[20,60])

    def test_037_street_punk_credit(self):
        self.assertEqual(registry.OCCUPATIONS["STREET_PUNK"]["credit_rating"],[3,10])

    def test_038_deprogrammer_modern_only(self):
        self.assertEqual(registry.resolve_occupation("DEPROGRAMMER",era="MODERN")["status"],"RESOLVED")
        self.assertEqual(registry.resolve_occupation("DEPROGRAMMER",era="1920S")["code"],"OCCUPATION_NOT_AVAILABLE_IN_ERA")

    def test_039_deprogrammer_hypnosis_is_substitution_not_auto_skill(self):
        record=registry.OCCUPATIONS["DEPROGRAMMER"]
        self.assertEqual(record["keeper_authorized_substitution"]["skill"],"HYPNOSIS")
        self.assertTrue(record["keeper_authorized_substitution"]["may_replace_one_listed_skill"])
        self.assertNotIn("HYPNOSIS",[s.get("skill") for s in record["skill_slots"]])

    def test_040_bank_robber_repair_choice(self):
        choice=registry.OCCUPATIONS["BANK_ROBBER"]["skill_slots"][1]["choice_one_of"]
        self.assertEqual(choice,[{"skill":"ELECTRICAL_REPAIR"},{"skill":"MECHANICAL_REPAIR"}])

    def test_041_burglar_has_sleight(self):
        self.assertIn({"skill":"SLEIGHT_OF_HAND"},registry.OCCUPATIONS["BURGLAR"]["skill_slots"])

    def test_042_gun_moll_brawl_or_handgun(self):
        choice=registry.OCCUPATIONS["GUN_MOLL"]["skill_slots"][2]["choice_one_of"]
        self.assertEqual(choice,[{"skill":"FIGHTING_BRAWL"},{"skill":"FIREARMS_HANDGUN"}])

    def test_043_smuggler_transport_choice(self):
        slot=registry.OCCUPATIONS["SMUGGLER"]["skill_slots"][4]
        self.assertEqual(slot["choice_one_of"][0],{"skill":"DRIVE_AUTO"})
        self.assertEqual(slot["choice_one_of"][1]["skill"],"PILOT")

    def test_044_stage_actor_fighting_family(self):
        self.assertIn({"skill_family":"FIGHTING"},registry.OCCUPATIONS["STAGE_ACTOR"]["skill_slots"])

    def test_045_agency_detective_exact_eight(self):
        self.assertEqual(registry.occupation_slot_count(registry.OCCUPATIONS["AGENCY_DETECTIVE"]),8)

    def test_046_criminal_variants_all_exact_eight(self):
        for occupation_id in registry.OCCUPATION_GROUPS["CRIMINAL"]["options"]:
            with self.subTest(occupation_id=occupation_id):
                self.assertEqual(registry.occupation_slot_count(registry.OCCUPATIONS[occupation_id]),8)

    def test_047_aliases_do_not_create_new_records(self):
        self.assertFalse(set(registry.ALIASES) & set(registry.OCCUPATIONS))

    def test_048_groups_do_not_create_automatic_record(self):
        for group_id in registry.OCCUPATION_GROUPS:
            with self.subTest(group_id=group_id):
                self.assertNotIn(group_id,registry.OCCUPATIONS)

    def test_049_no_duplicate_parent_ids(self):
        self.assertFalse(set(registry.OCCUPATIONS) & registry._parent_occupation_ids())

    def test_050_source_pages(self):
        self.assertEqual(MANIFEST["source"]["source_pages"],[70,75,76,77])

    def test_051_no_commercial_prose_fields(self):
        serialized=json.dumps(MANIFEST).lower()
        self.assertNotIn("suggested_contacts",serialized)
        self.assertNotIn("occupation_description",serialized)
        self.assertIn("structured mechanics/provenance only",MANIFEST["copyright_boundary"].lower())

    def test_052_no_auto_possession_or_authority(self):
        serialized=json.dumps(MANIFEST).lower()
        self.assertNotIn("auto_possession",serialized)
        self.assertNotIn("inventory",serialized)
        self.assertFalse(registry.registry_summary()["authority_promoted"])
        self.assertFalse(registry.registry_summary()["frozen_parent_modified"])


# 17 records x 4 generated contract tests = 68; 52 static + 68 = 120.
def _choice_for(record):
    for term in record["points_formula"]["terms"]:
        if "choice_one_of" in term:
            return term["choice_one_of"][0]
    return None


def _era_for(record):
    if record.get("era_scope")=="CLASSIC": return "CLASSIC"
    if record.get("era_scope")=="MODERN": return "MODERN"
    return None


def _slot_test(oid):
    def test(self): self.assertEqual(registry.occupation_slot_count(registry.OCCUPATIONS[oid]),8)
    return test


def _ref_test(oid):
    def test(self):
        r=registry.validate_record_references(oid)
        self.assertEqual(r["status"],"VALIDATED",r)
        self.assertEqual(r["slot_count"],8)
    return test


def _credit_test(oid):
    def test(self):
        lo,hi=registry.OCCUPATIONS[oid]["credit_rating"]
        self.assertTrue(0<=lo<=hi<=99)
    return test


def _points_test(oid):
    def test(self):
        rec=registry.OCCUPATIONS[oid]
        r=registry.resolve_occupation(oid,characteristics=SAMPLE,choice_characteristic=_choice_for(rec),era=_era_for(rec))
        self.assertEqual(r["status"],"RESOLVED",r)
        self.assertEqual(r["record"]["occupation_skill_points"],200)
    return test


for _oid in sorted(registry.OCCUPATIONS):
    _safe=_oid.lower()
    setattr(RegistryBatch5Tests,f"test_slot_{_safe}",_slot_test(_oid))
    setattr(RegistryBatch5Tests,f"test_refs_{_safe}",_ref_test(_oid))
    setattr(RegistryBatch5Tests,f"test_credit_{_safe}",_credit_test(_oid))
    setattr(RegistryBatch5Tests,f"test_points_{_safe}",_points_test(_oid))

if __name__=="__main__": unittest.main(verbosity=2)
