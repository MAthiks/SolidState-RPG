from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import other_forms_damage_dev as dmg


class OtherFormsDamageBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(dmg.MODULE_ID, 'COC7_OTHER_FORMS_DAMAGE_R1_BATCH1_DEV_V1')

    def test_002_parent_identity(self):
        self.assertEqual(dmg.PARENT_RANGED_THROWN_ARMOR_MODULE_ID, 'COC7_RANGED_THROWN_ARMOR_R1_BATCH1_DEV_V1')

    def test_003_wounds_parent_identity(self):
        self.assertEqual(dmg.WOUNDS_MODULE_ID, 'COC7_WOUNDS_HEALING_R1_BATCH1_DEV_V1')

    def test_004_source_identity(self):
        self.assertEqual(dmg.KEEPER_SOURCE_ID, 'COC7_KEEPER')
        self.assertEqual(dmg.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_005_minor_profile(self):
        r = dmg.damage_profile(severity='MINOR')
        self.assertEqual((r['dice_count'], r['die_sides'], r['expression']), (1, 3, '1D3'))

    def test_006_moderate_profile(self):
        self.assertEqual(dmg.damage_profile(severity='MODERATE')['expression'], '1D6')

    def test_007_severe_profile(self):
        self.assertEqual(dmg.damage_profile(severity='SEVERE')['expression'], '1D10')

    def test_008_deadly_profile(self):
        self.assertEqual(dmg.damage_profile(severity='DEADLY')['expression'], '2D10')

    def test_009_terminal_profile(self):
        self.assertEqual(dmg.damage_profile(severity='TERMINAL')['expression'], '4D10')

    def test_010_splat_profile(self):
        self.assertEqual(dmg.damage_profile(severity='SPLAT')['expression'], '8D10')

    def test_011_unknown_severity_blocks(self):
        self.assertEqual(dmg.damage_profile(severity='UNKNOWN')['code'], 'DAMAGE_SEVERITY_UNMATERIALIZED')

    def test_012_profile_normalizes_case(self):
        self.assertEqual(dmg.damage_profile(severity=' minor ')['severity'], 'MINOR')

    def test_013_profile_no_auto_selection(self):
        self.assertFalse(dmg.damage_profile(severity='MINOR')['severity_selected_automatically'])

    def test_014_profile_no_randomness(self):
        self.assertFalse(dmg.damage_profile(severity='MINOR')['randomness_generated'])

    def test_015_minor_damage_resolves(self):
        r = dmg.resolve_other_damage(severity='MINOR', recorded_dice=[3], max_hp=12, current_hp=12)
        self.assertEqual(r['damage'], 3)
        self.assertEqual(r['wound_state']['current_hp'], 9)

    def test_016_deadly_damage_sums_two_dice(self):
        r = dmg.resolve_other_damage(severity='DEADLY', recorded_dice=[8, 7], max_hp=20, current_hp=20)
        self.assertEqual(r['damage'], 15)

    def test_017_terminal_requires_four_dice(self):
        r = dmg.resolve_other_damage(severity='TERMINAL', recorded_dice=[1, 2, 3], max_hp=20, current_hp=20)
        self.assertEqual(r['code'], 'RECORDED_DAMAGE_DICE_COUNT_MISMATCH')

    def test_018_die_above_profile_blocks(self):
        r = dmg.resolve_other_damage(severity='MINOR', recorded_dice=[4], max_hp=12, current_hp=12)
        self.assertEqual(r['code'], 'RECORDED_DAMAGE_DIE_INVALID')

    def test_019_die_zero_blocks(self):
        r = dmg.resolve_other_damage(severity='MODERATE', recorded_dice=[0], max_hp=12, current_hp=12)
        self.assertEqual(r['code'], 'RECORDED_DAMAGE_DIE_INVALID')

    def test_020_bool_die_blocks(self):
        r = dmg.resolve_other_damage(severity='MODERATE', recorded_dice=[True], max_hp=12, current_hp=12)
        self.assertEqual(r['code'], 'RECORDED_DAMAGE_DIE_INVALID')

    def test_021_recorded_dice_required_as_list(self):
        r = dmg.resolve_other_damage(severity='MODERATE', recorded_dice=(3,), max_hp=12, current_hp=12)
        self.assertEqual(r['code'], 'RECORDED_DAMAGE_DICE_COUNT_MISMATCH')

    def test_022_exposure_flag_must_be_boolean(self):
        r = dmg.resolve_other_damage(severity='MINOR', recorded_dice=[1], max_hp=12, current_hp=12, exposure_continues=1)
        self.assertEqual(r['code'], 'EXPOSURE_CONTINUES_FLAG_INVALID')

    def test_023_continuing_exposure_marks_next_round(self):
        r = dmg.resolve_other_damage(severity='MINOR', recorded_dice=[1], max_hp=12, current_hp=12, exposure_continues=True)
        self.assertTrue(r['damage_again_next_round_if_exposure_continues'])

    def test_024_stopped_exposure_does_not_mark_next_round(self):
        r = dmg.resolve_other_damage(severity='MINOR', recorded_dice=[1], max_hp=12, current_hp=12, exposure_continues=False)
        self.assertFalse(r['damage_again_next_round_if_exposure_continues'])

    def test_025_other_damage_reuses_wounds(self):
        r = dmg.resolve_other_damage(severity='SEVERE', recorded_dice=[6], max_hp=10, current_hp=10)
        self.assertEqual(r['wounds_module_id'], dmg.WOUNDS_MODULE_ID)
        self.assertTrue(r['wound_state']['major_wound'])

    def test_026_other_damage_no_randomness(self):
        r = dmg.resolve_other_damage(severity='MINOR', recorded_dice=[2], max_hp=10, current_hp=10)
        self.assertFalse(r['randomness_generated'])

    def test_027_asphyxia_breathing_ends_state(self):
        r = dmg.asphyxiation_con_check(con_value=50, units=1, tens=[2], physically_exerting=False, can_breathe=True)
        self.assertFalse(r['asphyxiation_active'])
        self.assertFalse(r['failure_active_after'])

    def test_028_asphyxia_normal_is_regular_con(self):
        r = dmg.asphyxiation_con_check(con_value=50, units=0, tens=[4], physically_exerting=False, can_breathe=False)
        self.assertEqual(r['difficulty'], 'REGULAR')
        self.assertTrue(r['success'])

    def test_029_asphyxia_exertion_is_hard_con(self):
        r = dmg.asphyxiation_con_check(con_value=60, units=0, tens=[3], physically_exerting=True, can_breathe=False)
        self.assertEqual(r['difficulty'], 'HARD')
        self.assertTrue(r['success'])

    def test_030_asphyxia_hard_failure_activates_damage(self):
        r = dmg.asphyxiation_con_check(con_value=60, units=1, tens=[3], physically_exerting=True, can_breathe=False)
        self.assertFalse(r['success'])
        self.assertTrue(r['failure_active_after'])

    def test_031_first_failed_check_does_not_roll_damage_here(self):
        r = dmg.asphyxiation_con_check(con_value=40, units=9, tens=[8], physically_exerting=False, can_breathe=False)
        self.assertTrue(r['first_failed_check_does_not_roll_damage_in_same_resolution'])

    def test_032_active_failure_skips_new_con_check(self):
        r = dmg.asphyxiation_con_check(con_value=40, units=9, tens=[8], physically_exerting=False, can_breathe=False, failure_already_active=True)
        self.assertFalse(r['con_check_required'])
        self.assertTrue(r['damage_on_subsequent_rounds'])

    def test_033_asphyxia_flags_strict(self):
        r = dmg.asphyxiation_con_check(con_value=50, units=1, tens=[2], physically_exerting=1, can_breathe=False)
        self.assertEqual(r['code'], 'ASPHYXIATION_FLAG_INVALID')

    def test_034_asphyxia_invalid_con_blocks(self):
        r = dmg.asphyxiation_con_check(con_value=101, units=1, tens=[2], physically_exerting=False, can_breathe=False)
        self.assertEqual(r['code'], 'CON_VALUE_INVALID')

    def test_035_asphyxia_damage_requires_failed_con(self):
        r = dmg.resolve_asphyxiation_damage_round(severity='MODERATE', recorded_dice=[4], max_hp=10, current_hp=10, failure_active=False, can_breathe=False)
        self.assertEqual(r['code'], 'ASPHYXIATION_DAMAGE_REQUIRES_ACTIVE_FAILED_CON')

    def test_036_asphyxia_damage_resolves_after_failure(self):
        r = dmg.resolve_asphyxiation_damage_round(severity='MODERATE', recorded_dice=[4], max_hp=10, current_hp=10, failure_active=True, can_breathe=False)
        self.assertEqual(r['damage'], 4)
        self.assertEqual(r['current_hp'], 6)

    def test_037_asphyxia_zero_hp_is_dead(self):
        r = dmg.resolve_asphyxiation_damage_round(severity='MODERATE', recorded_dice=[6], max_hp=10, current_hp=5, failure_active=True, can_breathe=False)
        self.assertTrue(r['dead'])
        self.assertFalse(r['dying'])

    def test_038_asphyxia_ignores_major_wound_rule(self):
        r = dmg.resolve_asphyxiation_damage_round(severity='SEVERE', recorded_dice=[6], max_hp=10, current_hp=10, failure_active=True, can_breathe=False)
        self.assertTrue(r['major_wound_rule_ignored'])

    def test_039_asphyxia_breathing_prevents_damage(self):
        r = dmg.resolve_asphyxiation_damage_round(severity='MODERATE', recorded_dice=[6], max_hp=10, current_hp=5, failure_active=True, can_breathe=True)
        self.assertEqual(r['damage'], 0)
        self.assertEqual(r['current_hp'], 5)

    def test_040_asphyxia_bad_hp_blocks(self):
        r = dmg.resolve_asphyxiation_damage_round(severity='MODERATE', recorded_dice=[4], max_hp=10, current_hp=11, failure_active=True, can_breathe=False)
        self.assertEqual(r['code'], 'HP_INPUT_INVALID')

    def test_041_asphyxia_damage_no_randomness(self):
        r = dmg.resolve_asphyxiation_damage_round(severity='MINOR', recorded_dice=[2], max_hp=10, current_hp=10, failure_active=True, can_breathe=False)
        self.assertFalse(r['randomness_generated'])

    def test_042_poison_regular_con_does_not_halve(self):
        r = dmg.resolve_poison_con(con_value=60, units=0, tens=[4], base_damage=8)
        self.assertFalse(r['extreme_con_halves_damage'])
        self.assertEqual(r['applied_damage'], 8)

    def test_043_poison_extreme_con_halves_even_damage(self):
        r = dmg.resolve_poison_con(con_value=60, units=0, tens=[1], base_damage=8)
        self.assertTrue(r['extreme_con_halves_damage'])
        self.assertEqual(r['applied_damage'], 4)

    def test_044_poison_critical_halves_even_damage(self):
        r = dmg.resolve_poison_con(con_value=60, units=1, tens=[0], base_damage=10)
        self.assertEqual(r['success_level'], 'CRITICAL')
        self.assertEqual(r['applied_damage'], 5)

    def test_045_poison_critical_shakeoff_is_option_only(self):
        r = dmg.resolve_poison_con(con_value=60, units=1, tens=[0], base_damage=10)
        self.assertTrue(r['critical_shakeoff_option_available'])
        self.assertFalse(r['critical_shakeoff_applied_automatically'])

    def test_046_poison_extreme_odd_damage_blocks_rounding(self):
        r = dmg.resolve_poison_con(con_value=60, units=0, tens=[1], base_damage=7)
        self.assertEqual(r['code'], 'ODD_POISON_DAMAGE_HALVING_ROUNDING_UNMATERIALIZED')

    def test_047_poison_regular_odd_damage_is_unmodified(self):
        r = dmg.resolve_poison_con(con_value=60, units=0, tens=[4], base_damage=7)
        self.assertEqual(r['applied_damage'], 7)

    def test_048_poison_invalid_con_blocks(self):
        r = dmg.resolve_poison_con(con_value=101, units=0, tens=[4], base_damage=8)
        self.assertEqual(r['code'], 'CON_VALUE_INVALID')

    def test_049_poison_negative_damage_blocks(self):
        r = dmg.resolve_poison_con(con_value=60, units=0, tens=[4], base_damage=-1)
        self.assertEqual(r['code'], 'POISON_BASE_DAMAGE_INVALID')

    def test_050_poison_bool_damage_blocks(self):
        r = dmg.resolve_poison_con(con_value=60, units=0, tens=[4], base_damage=True)
        self.assertEqual(r['code'], 'POISON_BASE_DAMAGE_INVALID')

    def test_051_poison_no_auto_symptoms(self):
        r = dmg.resolve_poison_con(con_value=60, units=0, tens=[4], base_damage=8)
        self.assertFalse(r['poison_symptoms_selected_automatically'])

    def test_052_poison_no_randomness(self):
        r = dmg.resolve_poison_con(con_value=60, units=0, tens=[4], base_damage=8)
        self.assertFalse(r['randomness_generated'])

    def test_053_symptom_keep_acting(self):
        r = dmg.poison_symptom_plan(mode='KEEP_ACTING')
        self.assertTrue(r['can_act'])
        self.assertEqual(r['penalty_dice'], 0)

    def test_054_symptom_penalty_die(self):
        r = dmg.poison_symptom_plan(mode='PENALTY_DIE')
        self.assertEqual(r['penalty_dice'], 1)

    def test_055_symptom_increase_difficulty(self):
        r = dmg.poison_symptom_plan(mode='INCREASE_DIFFICULTY')
        self.assertTrue(r['increase_difficulty_one_step'])

    def test_056_symptom_incapacitated(self):
        r = dmg.poison_symptom_plan(mode='INCAPACITATED')
        self.assertFalse(r['can_act'])

    def test_057_unknown_symptom_mode_blocks(self):
        r = dmg.poison_symptom_plan(mode='VOMITING')
        self.assertEqual(r['code'], 'POISON_SYMPTOM_MODE_KEEPER_SELECTION_REQUIRED')

    def test_058_symptom_mode_normalizes(self):
        self.assertEqual(dmg.poison_symptom_plan(mode=' penalty_die ')['mode'], 'PENALTY_DIE')

    def test_059_symptom_is_keeper_selected(self):
        self.assertTrue(dmg.poison_symptom_plan(mode='KEEP_ACTING')['keeper_selected'])

    def test_060_symptom_no_auto_selection(self):
        self.assertFalse(dmg.poison_symptom_plan(mode='KEEP_ACTING')['automatic_symptom_selection'])


def _make_generated_damage_test(severity, dice):
    def test(self):
        max_hp = 100
        r = dmg.resolve_other_damage(
            severity=severity,
            recorded_dice=list(dice),
            max_hp=max_hp,
            current_hp=max_hp,
        )
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertEqual(r['damage'], sum(dice))
        self.assertEqual(r['wound_state']['current_hp'], max_hp - sum(dice))
        self.assertFalse(r['randomness_generated'])
    return test


_GENERATED = [
    ('MINOR', [1]), ('MINOR', [3]),
    ('MODERATE', [1]), ('MODERATE', [6]),
    ('SEVERE', [1]), ('SEVERE', [10]),
    ('DEADLY', [1, 1]), ('DEADLY', [10, 10]),
    ('TERMINAL', [1, 1, 1, 1]), ('TERMINAL', [10, 10, 10, 10]),
    ('SPLAT', [1, 1, 1, 1, 1, 1, 1, 1]), ('SPLAT', [10, 10, 10, 10, 10, 10, 10, 10]),
    ('DEADLY', [2, 3]), ('DEADLY', [4, 5]),
    ('TERMINAL', [2, 2, 2, 2]), ('TERMINAL', [3, 3, 3, 3]),
    ('SPLAT', [2, 2, 2, 2, 2, 2, 2, 2]), ('SPLAT', [3, 3, 3, 3, 3, 3, 3, 3]),
    ('MODERATE', [4]), ('SEVERE', [7]),
]

for i, (severity, dice) in enumerate(_GENERATED, start=61):
    setattr(OtherFormsDamageBatch1Tests, f'test_{i:03d}_generated_{severity.lower()}', _make_generated_damage_test(severity, dice))


if __name__ == '__main__':
    unittest.main()
