from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import investigator_creation_dev as creation


def base_dice():
    return {
        'STR': [3, 3, 3],
        'CON': [4, 4, 4],
        'DEX': [5, 4, 3],
        'APP': [3, 4, 5],
        'POW': [4, 4, 4],
        'LUCK': [3, 3, 3],
        'SIZ': [4, 4],
        'INT': [5, 5],
        'EDU': [5, 4],
    }


def raw():
    r = creation.generate_raw_characteristics(recorded_dice=base_dice())
    assert r['status'] == 'RESOLVED'
    return r


def aged37():
    r = raw()
    return creation.apply_creation_age(
        raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=37,
        physical_allocation=None, edu_checks=[{'percentile': 80, 'gain_d10': 5}],
    )


class InvestigatorCreationBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(creation.MODULE_ID, 'COC7_INVESTIGATOR_CREATION_R1_BATCH1_DEV_V1')

    def test_002_parent_rules_count(self):
        self.assertEqual(creation.PARENT_RULES_TEST_CHAIN, 1688)

    def test_003_registry_count(self):
        self.assertEqual(creation.OCCUPATION_REGISTRY_TEST_CHAIN, 626)

    def test_004_registry_identity(self):
        self.assertEqual(creation.OCCUPATION_REGISTRY_ID, 'COC7_RECOVERY_REGISTRY_R1_BATCH5_DEV_V1')

    def test_005_source_identity(self):
        self.assertEqual(creation.INVESTIGATOR_SOURCE_ID, 'COC7_INVESTIGATOR')
        self.assertEqual(creation.INVESTIGATOR_SHA256, 'de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17')

    def test_006_raw_str_formula(self):
        self.assertEqual(raw()['characteristics']['STR'], 45)

    def test_007_raw_con_formula(self):
        self.assertEqual(raw()['characteristics']['CON'], 60)

    def test_008_raw_dex_formula(self):
        self.assertEqual(raw()['characteristics']['DEX'], 60)

    def test_009_raw_app_formula(self):
        self.assertEqual(raw()['characteristics']['APP'], 60)

    def test_010_raw_pow_formula(self):
        self.assertEqual(raw()['characteristics']['POW'], 60)

    def test_011_raw_siz_formula(self):
        self.assertEqual(raw()['characteristics']['SIZ'], 70)

    def test_012_raw_int_formula(self):
        self.assertEqual(raw()['characteristics']['INT'], 80)

    def test_013_raw_edu_formula(self):
        self.assertEqual(raw()['characteristics']['EDU'], 75)

    def test_014_raw_luck_formula(self):
        self.assertEqual(raw()['luck'], 45)

    def test_015_raw_no_randomness(self):
        self.assertFalse(raw()['randomness_generated'])

    def test_016_raw_no_automatic_reroll(self):
        self.assertFalse(raw()['automatic_reroll'])

    def test_017_missing_dice_key_blocks(self):
        d = base_dice(); d.pop('STR')
        self.assertEqual(creation.generate_raw_characteristics(recorded_dice=d)['code'], 'CHARACTERISTIC_DICE_MAP_INCOMPLETE_OR_EXTRA')

    def test_018_extra_dice_key_blocks(self):
        d = base_dice(); d['X'] = [1, 1, 1]
        self.assertEqual(creation.generate_raw_characteristics(recorded_dice=d)['code'], 'CHARACTERISTIC_DICE_MAP_INCOMPLETE_OR_EXTRA')

    def test_019_three_d6_wrong_count_blocks(self):
        d = base_dice(); d['STR'] = [1, 2]
        self.assertEqual(creation.generate_raw_characteristics(recorded_dice=d)['code'], 'RECORDED_D6_COUNT_INVALID')

    def test_020_two_d6_wrong_count_blocks(self):
        d = base_dice(); d['SIZ'] = [1, 2, 3]
        self.assertEqual(creation.generate_raw_characteristics(recorded_dice=d)['code'], 'RECORDED_D6_COUNT_INVALID')

    def test_021_die_zero_blocks(self):
        d = base_dice(); d['STR'] = [0, 2, 3]
        self.assertEqual(creation.generate_raw_characteristics(recorded_dice=d)['code'], 'RECORDED_D6_VALUE_INVALID')

    def test_022_die_seven_blocks(self):
        d = base_dice(); d['INT'] = [7, 2]
        self.assertEqual(creation.generate_raw_characteristics(recorded_dice=d)['code'], 'RECORDED_D6_VALUE_INVALID')

    def test_023_bool_die_blocks(self):
        d = base_dice(); d['INT'] = [True, 2]
        self.assertEqual(creation.generate_raw_characteristics(recorded_dice=d)['code'], 'RECORDED_D6_VALUE_INVALID')

    def test_024_age_37_one_edu_check(self):
        a = aged37()
        self.assertEqual(a['characteristics']['EDU'], 80)
        self.assertEqual(len(a['edu_checks']), 1)

    def test_025_age_37_no_physical_loss(self):
        a = aged37()
        self.assertEqual(a['characteristics']['STR'], 45)
        self.assertEqual(a['characteristics']['DEX'], 60)

    def test_026_age_37_derived_hp(self):
        self.assertEqual(aged37()['derived']['HP'], 13)

    def test_027_age_37_derived_san_mp(self):
        a = aged37()
        self.assertEqual((a['derived']['SAN'], a['derived']['MP']), (60, 12))

    def test_028_age_37_mov(self):
        self.assertEqual(aged37()['derived']['MOV'], 7)

    def test_029_age_37_half_fifth(self):
        a = aged37()
        self.assertEqual(a['half_fifth']['INT'], {'full': 80, 'half': 40, 'fifth': 16})

    def test_030_age_37_no_second_luck_allowed(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=37,
            physical_allocation=None, edu_checks=[{'percentile': 80, 'gain_d10': 5}], second_luck_dice=[6,6,6])
        self.assertEqual(a['code'], 'SECOND_LUCK_ROLL_ONLY_FOR_AGE_15_19')

    def test_031_age_15_physical_and_edu_loss(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=18,
            physical_allocation={'STR': 5}, edu_checks=[], second_luck_dice=[6,6,6])
        self.assertEqual(a['characteristics']['STR'], 40)
        self.assertEqual(a['characteristics']['EDU'], 70)

    def test_032_age_15_higher_second_luck(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=18,
            physical_allocation={'SIZ': 5}, edu_checks=[], second_luck_dice=[6,6,6])
        self.assertEqual(a['luck'], 90)

    def test_033_age_15_lower_second_luck_keeps_first(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=18,
            physical_allocation={'SIZ': 5}, edu_checks=[], second_luck_dice=[1,1,1])
        self.assertEqual(a['luck'], 45)

    def test_034_age_15_second_luck_required(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=18,
            physical_allocation={'STR': 5}, edu_checks=[])
        self.assertEqual(a['code'], 'SECOND_LUCK_RECORDED_DICE_INVALID')

    def test_035_age_15_allocation_total_exact(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=18,
            physical_allocation={'STR': 4}, edu_checks=[], second_luck_dice=[6,6,6])
        self.assertEqual(a['code'], 'CREATION_AGE_PHYSICAL_ALLOCATION_INVALID')

    def test_036_age_40_two_edu_checks(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=45,
            physical_allocation={'DEX': 5}, edu_checks=[{'percentile': 50}, {'percentile': 80, 'gain_d10': 5}])
        self.assertEqual(a['characteristics']['EDU'], 80)
        self.assertEqual(len(a['edu_checks']), 2)

    def test_037_age_40_app_loss(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=45,
            physical_allocation={'DEX': 5}, edu_checks=[{'percentile': 50}, {'percentile': 50}])
        self.assertEqual(a['characteristics']['APP'], 55)

    def test_038_age_40_mov_penalty(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=45,
            physical_allocation={'DEX': 5}, edu_checks=[{'percentile': 50}, {'percentile': 50}])
        self.assertEqual(a['derived']['MOV'], 6)

    def test_039_age_50_profile(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=55,
            physical_allocation={'STR': 5, 'DEX': 5}, edu_checks=[{'percentile': 50}, {'percentile': 50}, {'percentile': 50}])
        self.assertEqual(a['characteristics']['APP'], 50)
        self.assertEqual(a['derived']['MOV'], 5)

    def test_040_age_60_profile(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=65,
            physical_allocation={'STR': 10, 'CON': 5, 'DEX': 5}, edu_checks=[{'percentile': 50}]*4)
        self.assertEqual(a['characteristics']['APP'], 45)
        self.assertEqual(a['derived']['MOV'], 4)

    def test_041_age_70_profile(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=75,
            physical_allocation={'STR': 15, 'CON': 10, 'DEX': 15}, edu_checks=[{'percentile': 50}]*4)
        self.assertEqual(a['characteristics']['APP'], 40)
        self.assertEqual(a['derived']['MOV'], 3)

    def test_042_age_80_profile(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=85,
            physical_allocation={'STR': 20, 'CON': 30, 'DEX': 30}, edu_checks=[{'percentile': 50}]*4)
        self.assertEqual(a['characteristics']['APP'], 35)
        self.assertEqual(a['derived']['MOV'], 2)

    def test_043_age_90_fails_closed(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=90,
            physical_allocation=None, edu_checks=[])
        self.assertEqual(a['code'], 'AGE_90_CREATION_MODIFIER_UNMATERIALIZED')

    def test_044_age_14_blocks(self):
        r = raw()
        self.assertEqual(creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=14,
            physical_allocation=None, edu_checks=[])['code'], 'CREATION_AGE_INVALID')

    def test_045_age_91_blocks(self):
        r = raw()
        self.assertEqual(creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=91,
            physical_allocation=None, edu_checks=[])['code'], 'CREATION_AGE_INVALID')

    def test_046_missing_edu_check_blocks(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=37,
            physical_allocation=None, edu_checks=[])
        self.assertEqual(a['code'], 'CREATION_EDU_CHECK_COUNT_INVALID')

    def test_047_extra_edu_check_blocks(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=37,
            physical_allocation=None, edu_checks=[{'percentile': 50}, {'percentile': 50}])
        self.assertEqual(a['code'], 'CREATION_EDU_CHECK_COUNT_INVALID')

    def test_048_successful_edu_check_requires_d10(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=37,
            physical_allocation=None, edu_checks=[{'percentile': 80}])
        self.assertEqual(a['code'], 'UNRECORDED_EDU_GAIN_D10')

    def test_049_failed_edu_check_rejects_unused_d10(self):
        r = raw()
        a = creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=37,
            physical_allocation=None, edu_checks=[{'percentile': 50, 'gain_d10': 5}])
        self.assertEqual(a['code'], 'UNUSED_EDU_GAIN_D10')

    def test_050_age_no_randomness(self):
        self.assertFalse(aged37()['randomness_generated'])

    def test_051_age_no_auto_allocation(self):
        self.assertFalse(aged37()['automatic_age_allocation'])

    def test_052_archaeologist_budget_resolves(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertEqual(b['status'], 'RESOLVED')
        self.assertEqual(b['occupation_skill_points_total'], 320)

    def test_053_archaeologist_credit_range(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertEqual(b['credit_rating_range'], [10, 40])

    def test_054_archaeologist_remaining_points(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertEqual(b['occupation_points_remaining_after_credit_rating'], 300)

    def test_055_personal_interest_int_x2(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertEqual(b['personal_interest_points_total'], 160)

    def test_056_credit_below_range_blocks(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ARCHAEOLOGIST', credit_rating=9, era='1920S')
        self.assertEqual(b['code'], 'CREDIT_RATING_OUTSIDE_OCCUPATION_RANGE')

    def test_057_credit_above_range_blocks(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ARCHAEOLOGIST', credit_rating=41, era='1920S')
        self.assertEqual(b['code'], 'CREDIT_RATING_OUTSIDE_OCCUPATION_RANGE')

    def test_058_animal_trainer_choice_required(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ANIMAL_TRAINER', credit_rating=20, era='1920S')
        self.assertEqual(b['code'], 'OCCUPATION_CHARACTERISTIC_CHOICE_REQUIRED')

    def test_059_animal_trainer_app_choice(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ANIMAL_TRAINER', credit_rating=20, era='1920S', occupation_choice_characteristic='APP')
        self.assertEqual(b['occupation_skill_points_total'], a['characteristics']['EDU']*2 + a['characteristics']['APP']*2)

    def test_060_ambiguous_actor_group_blocks(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ACTOR', credit_rating=20, era='1920S')
        self.assertEqual(b['code'], 'OCCUPATION_VARIANT_REQUIRED')

    def test_061_unknown_occupation_blocks(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='NOT_REAL', credit_rating=20, era='1920S')
        self.assertNotEqual(b['status'], 'RESOLVED')

    def test_062_no_auto_occupation(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertFalse(b['automatic_occupation_selection'])

    def test_063_no_auto_credit(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertFalse(b['automatic_credit_rating_selection'])

    def test_064_mythos_personal_interest_requires_exception(self):
        a = aged37()
        b = creation.creation_budgets(characteristics=a['characteristics'], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertTrue(b['cthulhu_mythos_personal_interest_requires_keeper_exception'])

    def test_065_preflight_archaeologist_ready_for_batch2(self):
        p = creation.creation_preflight(recorded_dice=base_dice(), age=37, physical_allocation=None,
            edu_checks=[{'percentile': 80, 'gain_d10': 5}], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertEqual(p['status'], 'READY_FOR_SKILL_ALLOCATION_BATCH2')

    def test_066_preflight_does_not_commit_character(self):
        p = creation.creation_preflight(recorded_dice=base_dice(), age=37, physical_allocation=None,
            edu_checks=[{'percentile': 80, 'gain_d10': 5}], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertFalse(p['character_state_committed'])

    def test_067_preflight_no_randomness(self):
        p = creation.creation_preflight(recorded_dice=base_dice(), age=37, physical_allocation=None,
            edu_checks=[{'percentile': 80, 'gain_d10': 5}], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertFalse(p['randomness_generated'])

    def test_068_preflight_invalid_dice_stage(self):
        d=base_dice(); d['STR']=[1]
        p=creation.creation_preflight(recorded_dice=d, age=37, physical_allocation=None,
            edu_checks=[{'percentile':80,'gain_d10':5}], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertEqual(p['creation_stage'], 'GENERATE_CHARACTERISTICS')

    def test_069_preflight_age_stage(self):
        p=creation.creation_preflight(recorded_dice=base_dice(), age=90, physical_allocation=None,
            edu_checks=[], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertEqual(p['creation_stage'], 'APPLY_CREATION_AGE')

    def test_070_preflight_occupation_stage(self):
        p=creation.creation_preflight(recorded_dice=base_dice(), age=37, physical_allocation=None,
            edu_checks=[{'percentile':80,'gain_d10':5}], occupation_id='ACTOR', credit_rating=20, era='1920S')
        self.assertEqual(p['creation_stage'], 'OCCUPATION_RESOLUTION')

    def test_071_preflight_credit_stage(self):
        p=creation.creation_preflight(recorded_dice=base_dice(), age=37, physical_allocation=None,
            edu_checks=[{'percentile':80,'gain_d10':5}], occupation_id='ARCHAEOLOGIST', credit_rating=99, era='1920S')
        self.assertEqual(p['creation_stage'], 'CREATE_BUDGETS')

    def test_072_preflight_replay_stable(self):
        kwargs=dict(recorded_dice=base_dice(), age=37, physical_allocation=None,
            edu_checks=[{'percentile':80,'gain_d10':5}], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertEqual(creation.creation_preflight(**copy.deepcopy(kwargs)), creation.creation_preflight(**copy.deepcopy(kwargs)))

    def test_073_preflight_next_stage_explicit(self):
        p=creation.creation_preflight(recorded_dice=base_dice(), age=37, physical_allocation=None,
            edu_checks=[{'percentile':80,'gain_d10':5}], occupation_id='ARCHAEOLOGIST', credit_rating=20, era='1920S')
        self.assertEqual(p['next_stage'], 'OCCUPATION_AND_PERSONAL_INTEREST_SKILL_ALLOCATION_BATCH2')

    def test_074_age_profile_no_auto_second_luck_outside_young(self):
        self.assertIsNone(aged37()['second_luck'])

    def test_075_edu_cap_99(self):
        d=base_dice(); d['EDU']=[6,6]
        r=creation.generate_raw_characteristics(recorded_dice=d)
        a=creation.apply_creation_age(raw_characteristics=r['characteristics'], raw_luck=r['luck'], age=37,
            physical_allocation=None, edu_checks=[{'percentile':100,'gain_d10':10}])
        self.assertEqual(a['characteristics']['EDU'], 99)


def _make_generated_raw_test(key, dice, expected):
    def test(self):
        d = base_dice()
        d[key] = list(dice)
        r = creation.generate_raw_characteristics(recorded_dice=d)
        self.assertEqual(r['status'], 'RESOLVED')
        actual = r['luck'] if key == 'LUCK' else r['characteristics'][key]
        self.assertEqual(actual, expected)
        self.assertFalse(r['randomness_generated'])
    return test


_GENERATED = [
    ('STR',[1,1,1],15), ('STR',[6,6,6],90),
    ('CON',[1,2,3],30), ('DEX',[6,5,4],75), ('APP',[2,2,2],30),
    ('POW',[5,5,5],75), ('LUCK',[1,1,1],15), ('LUCK',[6,6,6],90),
    ('SIZ',[1,1],40), ('SIZ',[6,6],90), ('INT',[1,1],40), ('INT',[6,6],90),
    ('EDU',[1,1],40), ('EDU',[6,6],90), ('STR',[2,3,4],45),
    ('CON',[3,3,3],45), ('DEX',[2,4,6],60), ('APP',[1,3,5],45),
    ('POW',[2,5,6],65), ('LUCK',[2,4,5],55), ('SIZ',[2,5],65),
    ('INT',[3,4],65), ('EDU',[4,5],75), ('STR',[4,4,4],60), ('CON',[6,6,5],85),
]

for i, (key, dice, expected) in enumerate(_GENERATED, start=76):
    setattr(InvestigatorCreationBatch1Tests, f'test_{i:03d}_generated_{key.lower()}', _make_generated_raw_test(key, dice, expected))


if __name__ == '__main__':
    unittest.main()
