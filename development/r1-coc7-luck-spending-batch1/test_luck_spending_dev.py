from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import luck_spending_dev as luck


def resolved(**overrides):
    args = dict(
        actor_id='P1',
        roll_owner_actor_id='P1',
        current_luck=50,
        roll_kind='SKILL',
        value=60,
        original_roll=70,
        spend_points=10,
        difficulty='REGULAR',
        pushed_roll=False,
        firearm_malfunction=False,
    )
    args.update(overrides)
    return luck.spend_luck_on_recorded_roll(**args)


class LuckSpendingBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(luck.MODULE_ID, 'COC7_LUCK_SPENDING_R1_BATCH1_DEV_V1')

    def test_002_parent_general_identity(self):
        self.assertEqual(luck.PARENT_GENERAL_SKILL_MODULE_ID, 'COC7_GENERAL_SKILL_RESOLUTION_R1_BATCH1_DEV_V1')

    def test_003_investigator_development_parent_identity(self):
        self.assertEqual(luck.INVESTIGATOR_DEVELOPMENT_MODULE_ID, 'COC7_INVESTIGATOR_DEVELOPMENT_R1_BATCH1_DEV_V1')

    def test_004_source_identity(self):
        self.assertEqual(luck.KEEPER_SOURCE_ID, 'COC7_KEEPER')
        self.assertEqual(luck.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_005_skill_roll_allowed(self):
        self.assertEqual(resolved()['status'], 'RESOLVED')

    def test_006_characteristic_roll_allowed(self):
        self.assertEqual(resolved(roll_kind='CHARACTERISTIC')['status'], 'RESOLVED')

    def test_007_luck_roll_excluded(self):
        self.assertEqual(resolved(roll_kind='LUCK')['code'], 'ROLL_KIND_EXCLUDED_FROM_LUCK_SPEND')

    def test_008_damage_roll_excluded(self):
        self.assertEqual(resolved(roll_kind='DAMAGE')['code'], 'ROLL_KIND_EXCLUDED_FROM_LUCK_SPEND')

    def test_009_sanity_roll_excluded(self):
        self.assertEqual(resolved(roll_kind='SANITY')['code'], 'ROLL_KIND_EXCLUDED_FROM_LUCK_SPEND')

    def test_010_sanity_loss_roll_excluded(self):
        self.assertEqual(resolved(roll_kind='SANITY_LOSS')['code'], 'ROLL_KIND_EXCLUDED_FROM_LUCK_SPEND')

    def test_011_unmaterialized_roll_kind_blocks(self):
        self.assertEqual(resolved(roll_kind='OTHER')['code'], 'ROLL_KIND_UNSUPPORTED_FOR_LUCK_SPEND')

    def test_012_wrong_actor_blocks(self):
        self.assertEqual(resolved(actor_id='P2')['code'], 'LUCK_MAY_ONLY_ALTER_OWN_ROLL')

    def test_013_actor_whitespace_normalizes(self):
        r = resolved(actor_id=' P1 ', roll_owner_actor_id='P1 ')
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertEqual(r['actor_id'], 'P1')

    def test_014_invalid_actor_blocks(self):
        self.assertEqual(resolved(actor_id='')['code'], 'ACTOR_ID_INVALID')

    def test_015_zero_luck_cannot_spend(self):
        self.assertEqual(resolved(current_luck=0, spend_points=1)['code'], 'LUCK_SPEND_EXCEEDS_CURRENT_LUCK')

    def test_016_luck_above_99_blocks(self):
        self.assertEqual(resolved(current_luck=100)['code'], 'CURRENT_LUCK_INVALID')

    def test_017_bool_luck_blocks(self):
        self.assertEqual(resolved(current_luck=True)['code'], 'CURRENT_LUCK_INVALID')

    def test_018_value_zero_is_valid_input(self):
        r = resolved(value=0, original_roll=50, spend_points=1)
        self.assertEqual(r['status'], 'RESOLVED')

    def test_019_value_100_is_valid_input(self):
        self.assertEqual(resolved(value=100, original_roll=70, spend_points=1)['status'], 'RESOLVED')

    def test_020_value_above_100_blocks(self):
        self.assertEqual(resolved(value=101)['code'], 'ROLL_VALUE_INVALID')

    def test_021_original_critical_blocks(self):
        self.assertEqual(resolved(original_roll=1, spend_points=1)['code'], 'ORIGINAL_CRITICAL_CANNOT_BE_ALTERED_WITH_LUCK')

    def test_022_roll_100_fumble_blocks(self):
        self.assertEqual(resolved(original_roll=100, spend_points=10)['code'], 'ORIGINAL_FUMBLE_CANNOT_BE_BOUGHT_OFF_WITH_LUCK')

    def test_023_low_skill_96_fumble_blocks(self):
        self.assertEqual(resolved(value=40, original_roll=96, spend_points=60)['code'], 'ORIGINAL_FUMBLE_CANNOT_BE_BOUGHT_OFF_WITH_LUCK')

    def test_024_value_50_roll_96_is_not_automatic_fumble(self):
        r = resolved(value=50, original_roll=96, spend_points=47)
        self.assertEqual(r['status'], 'RESOLVED')

    def test_025_firearm_malfunction_blocks(self):
        self.assertEqual(resolved(firearm_malfunction=True)['code'], 'FIREARM_MALFUNCTION_CANNOT_BE_BOUGHT_OFF_WITH_LUCK')

    def test_026_firearm_flag_must_be_boolean(self):
        self.assertEqual(resolved(firearm_malfunction=1)['code'], 'ROLL_STATE_FLAG_INVALID')

    def test_027_pushed_roll_blocks(self):
        self.assertEqual(resolved(pushed_roll=True)['code'], 'PUSHED_ROLL_CANNOT_BE_ALTERED_WITH_LUCK')

    def test_028_pushed_flag_must_be_boolean(self):
        self.assertEqual(resolved(pushed_roll='no')['code'], 'ROLL_STATE_FLAG_INVALID')

    def test_029_zero_spend_blocks(self):
        self.assertEqual(resolved(spend_points=0)['code'], 'LUCK_SPEND_POINTS_INVALID')

    def test_030_bool_spend_blocks(self):
        self.assertEqual(resolved(spend_points=True)['code'], 'LUCK_SPEND_POINTS_INVALID')

    def test_031_overspend_blocks(self):
        self.assertEqual(resolved(current_luck=10, spend_points=11)['code'], 'LUCK_SPEND_EXCEEDS_CURRENT_LUCK')

    def test_032_spending_all_current_luck_allowed(self):
        r = resolved(current_luck=10, spend_points=10)
        self.assertEqual(r['luck_after'], 0)

    def test_033_adjusted_roll_below_one_blocks(self):
        self.assertEqual(resolved(current_luck=99, original_roll=10, spend_points=10)['code'], 'LUCK_SPEND_WOULD_REDUCE_RECORDED_ROLL_BELOW_ONE')

    def test_034_adjusted_roll_exactly_one_is_preserved_as_critical(self):
        r = resolved(current_luck=99, original_roll=10, spend_points=9)
        self.assertEqual(r['adjusted_roll'], 1)
        self.assertEqual(r['adjusted_level'], 'CRITICAL')

    def test_035_one_for_one_roll_change(self):
        r = resolved(original_roll=70, spend_points=13)
        self.assertEqual(r['adjusted_roll'], 57)

    def test_036_regular_failure_can_become_regular_success(self):
        r = resolved(value=60, original_roll=70, spend_points=10)
        self.assertFalse(r['original_success'])
        self.assertTrue(r['adjusted_success'])
        self.assertEqual(r['adjusted_level'], 'REGULAR')

    def test_037_regular_failure_can_become_hard_success(self):
        r = resolved(value=60, original_roll=70, spend_points=40)
        self.assertEqual(r['adjusted_roll'], 30)
        self.assertEqual(r['adjusted_level'], 'HARD')

    def test_038_regular_failure_can_become_extreme_success(self):
        r = resolved(value=60, original_roll=70, spend_points=58)
        self.assertEqual(r['adjusted_roll'], 12)
        self.assertEqual(r['adjusted_level'], 'EXTREME')

    def test_039_success_can_be_improved_to_hard(self):
        r = resolved(value=60, original_roll=50, spend_points=20)
        self.assertTrue(r['original_success'])
        self.assertEqual(r['adjusted_level'], 'HARD')

    def test_040_hard_success_can_be_improved_to_extreme(self):
        r = resolved(value=80, original_roll=40, spend_points=24)
        self.assertEqual(r['original_level'], 'HARD')
        self.assertEqual(r['adjusted_level'], 'EXTREME')

    def test_041_invalid_difficulty_blocks(self):
        self.assertEqual(resolved(difficulty='IMPOSSIBLE')['code'], 'DIFFICULTY_INVALID')

    def test_042_luck_after_is_atomic_subtraction(self):
        r = resolved(current_luck=42, spend_points=17)
        self.assertEqual(r['luck_before'], 42)
        self.assertEqual(r['luck_after'], 25)

    def test_043_atomic_delta_matches_spend(self):
        self.assertEqual(resolved(spend_points=17)['atomic_luck_delta'], -17)

    def test_044_no_randomness_generated(self):
        self.assertFalse(resolved()['randomness_generated'])

    def test_045_no_automatic_spend_amount(self):
        self.assertFalse(resolved()['automatic_spend_amount_selection'])

    def test_046_spend_marks_experience_ineligible(self):
        self.assertFalse(resolved()['experience_check_eligible'])

    def test_047_successful_spend_marks_state_mutated(self):
        self.assertTrue(resolved()['state_mutated'])

    def test_048_wrong_actor_has_zero_mutation(self):
        self.assertFalse(resolved(actor_id='P2')['state_mutated'])

    def test_049_fumble_has_zero_mutation(self):
        self.assertFalse(resolved(original_roll=100)['state_mutated'])

    def test_050_replay_is_stable(self):
        a = resolved(current_luck=44, original_roll=63, spend_points=19)
        b = resolved(current_luck=44, original_roll=63, spend_points=19)
        self.assertEqual(a, b)

    def test_051_owner_binding_is_preserved(self):
        self.assertEqual(resolved()['roll_owner_actor_id'], 'P1')

    def test_052_owner_whitespace_normalizes(self):
        self.assertEqual(resolved(roll_owner_actor_id=' P1 ')['roll_owner_actor_id'], 'P1')

    def test_053_hard_difficulty_requires_hard_after_spend(self):
        r = resolved(value=60, original_roll=70, spend_points=10, difficulty='HARD')
        self.assertFalse(r['adjusted_success'])

    def test_054_hard_difficulty_succeeds_at_half(self):
        r = resolved(value=60, original_roll=70, spend_points=40, difficulty='HARD')
        self.assertTrue(r['adjusted_success'])

    def test_055_extreme_difficulty_requires_extreme_after_spend(self):
        r = resolved(value=60, original_roll=70, spend_points=40, difficulty='EXTREME')
        self.assertFalse(r['adjusted_success'])

    def test_056_extreme_difficulty_succeeds_at_fifth(self):
        r = resolved(value=60, original_roll=70, spend_points=58, difficulty='EXTREME')
        self.assertTrue(r['adjusted_success'])

    def test_057_regular_boundary_exact_skill(self):
        r = resolved(value=40, original_roll=41, spend_points=1)
        self.assertEqual(r['adjusted_roll'], 40)
        self.assertTrue(r['adjusted_success'])

    def test_058_hard_boundary_exact_half(self):
        r = resolved(value=80, original_roll=41, spend_points=1, difficulty='HARD')
        self.assertEqual(r['adjusted_roll'], 40)
        self.assertTrue(r['adjusted_success'])

    def test_059_extreme_boundary_exact_fifth(self):
        r = resolved(value=80, original_roll=17, spend_points=1, difficulty='EXTREME')
        self.assertEqual(r['adjusted_roll'], 16)
        self.assertTrue(r['adjusted_success'])

    def test_060_firearm_malfunction_blocks_even_if_spend_would_succeed(self):
        r = resolved(value=60, original_roll=70, spend_points=40, firearm_malfunction=True)
        self.assertEqual(r['code'], 'FIREARM_MALFUNCTION_CANNOT_BE_BOUGHT_OFF_WITH_LUCK')

    def test_061_experience_success_after_luck_gets_no_tick(self):
        r = luck.experience_tick_after_luck_spend(
            skill_id='SPOT_HIDDEN', adjusted_roll_success=True, used_bonus_die=False,
            opposed_roll=False, opposed_winner=None, already_checked=False)
        self.assertFalse(r['new_tick_granted'])
        self.assertEqual(r['reason'], 'LUCK_SPEND_BLOCKS_TICK')

    def test_062_experience_failure_after_luck_gets_no_tick(self):
        r = luck.experience_tick_after_luck_spend(
            skill_id='SPOT_HIDDEN', adjusted_roll_success=False, used_bonus_die=False,
            opposed_roll=False, opposed_winner=None, already_checked=False)
        self.assertFalse(r['new_tick_granted'])

    def test_063_experience_bonus_die_still_gets_no_tick(self):
        r = luck.experience_tick_after_luck_spend(
            skill_id='SPOT_HIDDEN', adjusted_roll_success=True, used_bonus_die=True,
            opposed_roll=False, opposed_winner=None, already_checked=False)
        self.assertFalse(r['new_tick_granted'])

    def test_064_experience_opposed_winner_still_gets_no_tick(self):
        r = luck.experience_tick_after_luck_spend(
            skill_id='SPOT_HIDDEN', adjusted_roll_success=True, used_bonus_die=False,
            opposed_roll=True, opposed_winner=True, already_checked=False)
        self.assertFalse(r['new_tick_granted'])
        self.assertEqual(r['reason'], 'LUCK_SPEND_BLOCKS_TICK')

    def test_065_experience_opposed_nonwinner_still_gets_no_tick(self):
        r = luck.experience_tick_after_luck_spend(
            skill_id='SPOT_HIDDEN', adjusted_roll_success=True, used_bonus_die=False,
            opposed_roll=True, opposed_winner=False, already_checked=False)
        self.assertFalse(r['new_tick_granted'])

    def test_066_experience_invalid_skill_fails_closed(self):
        r = luck.experience_tick_after_luck_spend(
            skill_id='', adjusted_roll_success=True, used_bonus_die=False,
            opposed_roll=False, opposed_winner=None, already_checked=False)
        self.assertEqual(r['status'], 'BLOCKED')

    def test_067_existing_experience_tick_is_preserved(self):
        r = luck.experience_tick_after_luck_spend(
            skill_id='SPOT_HIDDEN', adjusted_roll_success=True, used_bonus_die=False,
            opposed_roll=False, opposed_winner=None, already_checked=True)
        self.assertTrue(r['pending_check_after'])

    def test_068_credit_rating_remains_non_improvable(self):
        r = luck.experience_tick_after_luck_spend(
            skill_id='CREDIT_RATING', adjusted_roll_success=True, used_bonus_die=False,
            opposed_roll=False, opposed_winner=None, already_checked=False)
        self.assertFalse(r['new_tick_granted'])

    def test_069_cthulhu_mythos_remains_non_improvable(self):
        r = luck.experience_tick_after_luck_spend(
            skill_id='CTHULHU_MYTHOS', adjusted_roll_success=True, used_bonus_die=False,
            opposed_roll=False, opposed_winner=None, already_checked=False)
        self.assertFalse(r['new_tick_granted'])

    def test_070_spend_output_carries_module_identity(self):
        self.assertEqual(resolved()['module_id'], luck.MODULE_ID)


def _make_generated_spend_test(spend):
    def test(self):
        r = resolved(current_luck=50, original_roll=80, spend_points=spend)
        self.assertEqual(r['adjusted_roll'], 80 - spend)
        self.assertEqual(r['luck_after'], 50 - spend)
        self.assertEqual(r['atomic_luck_delta'], -spend)
    return test


for _i in range(1, 11):
    setattr(
        LuckSpendingBatch1Tests,
        f'test_generated_one_for_one_{_i:02d}',
        _make_generated_spend_test(_i),
    )


if __name__ == '__main__':
    unittest.main()
