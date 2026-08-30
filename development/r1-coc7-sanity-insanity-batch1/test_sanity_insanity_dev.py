from __future__ import annotations

import unittest

import sanity_insanity_dev as sanity


class SanityInsanityBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(sanity.MODULE_ID, 'COC7_SANITY_INSANITY_R1_BATCH1_DEV_V1')
        self.assertEqual(sanity.PARENT_WOUNDS_MODULE_ID, 'COC7_WOUNDS_HEALING_R1_BATCH1_DEV_V1')
        self.assertEqual(sanity.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_002_maximum_sanity(self):
        r=sanity.maximum_sanity(cthulhu_mythos=17)
        self.assertEqual(r['maximum_san'],82)

    def test_003_maximum_sanity_caps_current(self):
        r=sanity.maximum_sanity(cthulhu_mythos=20,current_san=90)
        self.assertEqual(r['current_san'],79)
        self.assertTrue(r['san_was_capped'])

    def test_004_maximum_sanity_no_cap(self):
        r=sanity.maximum_sanity(cthulhu_mythos=20,current_san=70)
        self.assertEqual(r['current_san'],70)
        self.assertFalse(r['san_was_capped'])

    def test_005_invalid_mythos_blocks(self):
        self.assertEqual(sanity.maximum_sanity(cthulhu_mythos=100)['code'],'CTHULHU_MYTHOS_INVALID')

    def test_006_san_roll_success_uses_recorded_success_loss(self):
        r=sanity.sanity_roll(current_san=60,units=0,tens=[4],recorded_success_loss=1,recorded_failure_loss=5,failure_loss_maximum=6)
        self.assertTrue(r['success'])
        self.assertEqual(r['san_loss'],1)

    def test_007_san_roll_failure_uses_recorded_failure_loss(self):
        r=sanity.sanity_roll(current_san=60,units=0,tens=[7],recorded_success_loss=1,recorded_failure_loss=5,failure_loss_maximum=6)
        self.assertFalse(r['success'])
        self.assertEqual(r['san_loss'],5)

    def test_008_san_roll_failure_requires_keeper_involuntary_choice(self):
        r=sanity.sanity_roll(current_san=60,units=0,tens=[7],recorded_success_loss=0,recorded_failure_loss=1,failure_loss_maximum=3)
        self.assertTrue(r['involuntary_action_keeper_choice_required'])

    def test_009_san_roll_success_no_involuntary_choice(self):
        r=sanity.sanity_roll(current_san=60,units=0,tens=[4],recorded_success_loss=0,recorded_failure_loss=1,failure_loss_maximum=3)
        self.assertFalse(r['involuntary_action_keeper_choice_required'])

    def test_010_san_roll_no_luck(self):
        r=sanity.sanity_roll(current_san=60,units=0,tens=[4],recorded_success_loss=0,recorded_failure_loss=1,failure_loss_maximum=3)
        self.assertFalse(r['luck_spend_allowed'])
        self.assertFalse(r['bonus_penalty_dice_allowed'])

    def test_011_san_roll_does_not_generate_randomness(self):
        r=sanity.sanity_roll(current_san=60,units=0,tens=[4],recorded_success_loss=0,recorded_failure_loss=1,failure_loss_maximum=3)
        self.assertFalse(r['randomness_generated'])

    def test_012_san_roll_digits_required(self):
        r=sanity.sanity_roll(current_san=60,units=None,tens=None,recorded_success_loss=0,recorded_failure_loss=1,failure_loss_maximum=3)
        self.assertEqual(r['code'],'SAN_ROLL_DIGITS_REQUIRED')

    def test_013_failure_loss_cannot_exceed_source_maximum(self):
        r=sanity.sanity_roll(current_san=60,units=0,tens=[7],recorded_success_loss=0,recorded_failure_loss=7,failure_loss_maximum=6)
        self.assertEqual(r['code'],'RECORDED_FAILURE_LOSS_EXCEEDS_SOURCE_MAXIMUM')

    def test_014_bout_grants_san_immunity(self):
        r=sanity.sanity_roll(current_san=60,units=None,tens=None,recorded_success_loss=3,recorded_failure_loss=7,failure_loss_maximum=8,in_bout_of_madness=True)
        self.assertTrue(r['immune_to_san_loss'])
        self.assertFalse(r['san_roll_required'])
        self.assertEqual(r['san_loss'],0)

    def test_015_bout_immunity_no_randomness(self):
        r=sanity.sanity_roll(current_san=60,units=None,tens=None,recorded_success_loss=0,recorded_failure_loss=1,failure_loss_maximum=1,in_bout_of_madness=True)
        self.assertFalse(r['randomness_generated'])

    def test_016_san_zero_cannot_make_san_roll(self):
        r=sanity.sanity_roll(current_san=0,units=0,tens=[1],recorded_success_loss=0,recorded_failure_loss=1,failure_loss_maximum=1)
        self.assertEqual(r['code'],'CURRENT_SAN_INVALID_OR_PERMANENTLY_INSANE')

    def test_017_apply_small_loss_stable(self):
        r=sanity.apply_sanity_loss(current_san=60,loss=2,sanity_start_of_day=60)
        self.assertEqual(r['SAN'],58)
        self.assertEqual(r['state'],'STABLE')

    def test_018_apply_five_loss_requests_int_check(self):
        r=sanity.apply_sanity_loss(current_san=60,loss=5,sanity_start_of_day=60)
        self.assertEqual(r['state'],'TEMPORARY_INSANITY_INT_CHECK_REQUIRED')
        self.assertTrue(r['int_check_required'])

    def test_019_exact_daily_fifth_causes_indefinite(self):
        r=sanity.apply_sanity_loss(current_san=60,loss=12,sanity_start_of_day=60)
        self.assertEqual(r['state'],'INDEFINITE_INSANITY')
        self.assertTrue(r['bout_required'])
        self.assertFalse(r['int_check_required'])

    def test_020_daily_losses_accumulate(self):
        r=sanity.apply_sanity_loss(current_san=55,loss=7,sanity_start_of_day=60,daily_loss_before=5)
        self.assertEqual(r['daily_loss_after'],12)
        self.assertEqual(r['state'],'INDEFINITE_INSANITY')

    def test_021_loss_cannot_make_negative_san(self):
        r=sanity.apply_sanity_loss(current_san=3,loss=9,sanity_start_of_day=60)
        self.assertEqual(r['SAN'],0)
        self.assertEqual(r['actual_loss'],3)

    def test_022_zero_san_permanent(self):
        r=sanity.apply_sanity_loss(current_san=3,loss=3,sanity_start_of_day=60)
        self.assertEqual(r['state'],'PERMANENT_INSANITY')
        self.assertTrue(r['ceases_to_be_player_character'])

    def test_023_underlying_insanity_any_loss_triggers_bout(self):
        r=sanity.apply_sanity_loss(current_san=50,loss=1,sanity_start_of_day=60,already_underlying_insanity=True)
        self.assertEqual(r['state'],'UNDERLYING_INSANITY')
        self.assertTrue(r['bout_required'])

    def test_024_underlying_insanity_zero_loss_no_bout(self):
        r=sanity.apply_sanity_loss(current_san=50,loss=0,sanity_start_of_day=60,already_underlying_insanity=True)
        self.assertFalse(r['bout_required'])

    def test_025_apply_loss_no_randomness(self):
        r=sanity.apply_sanity_loss(current_san=60,loss=2,sanity_start_of_day=60)
        self.assertFalse(r['randomness_generated'])

    def test_026_current_san_over_day_start_fail_closed(self):
        r=sanity.apply_sanity_loss(current_san=61,loss=1,sanity_start_of_day=60)
        self.assertEqual(r['code'],'CURRENT_SAN_EXCEEDS_DAY_START_SAN')

    def test_027_temp_insanity_int_success(self):
        r=sanity.resolve_temporary_insanity_int(int_value=70,units=0,tens=[4],recorded_duration_hours=6)
        self.assertTrue(r['int_success'])
        self.assertEqual(r['state'],'TEMPORARY_INSANITY')
        self.assertEqual(r['duration_hours'],6)
        self.assertTrue(r['bout_required'])

    def test_028_temp_insanity_int_fail_represses_memory(self):
        r=sanity.resolve_temporary_insanity_int(int_value=40,units=0,tens=[7],recorded_duration_hours=None)
        self.assertFalse(r['int_success'])
        self.assertEqual(r['state'],'NO_TEMPORARY_INSANITY')
        self.assertTrue(r['memory_repressed'])

    def test_029_temp_duration_required_only_on_int_success(self):
        r=sanity.resolve_temporary_insanity_int(int_value=70,units=0,tens=[4],recorded_duration_hours=None)
        self.assertEqual(r['code'],'RECORDED_TEMPORARY_INSANITY_D10_REQUIRED')

    def test_030_temp_duration_rejected_on_int_failure(self):
        r=sanity.resolve_temporary_insanity_int(int_value=40,units=0,tens=[7],recorded_duration_hours=3)
        self.assertEqual(r['code'],'TEMPORARY_DURATION_NOT_USED_WHEN_INT_FAILS')

    def test_031_temp_duration_bounds(self):
        r=sanity.resolve_temporary_insanity_int(int_value=70,units=0,tens=[4],recorded_duration_hours=11)
        self.assertEqual(r['code'],'RECORDED_TEMPORARY_INSANITY_D10_REQUIRED')

    def test_032_real_time_bout_duration_rounds(self):
        r=sanity.bout_of_madness_plan(insanity_type='TEMPORARY',mode='REAL_TIME',recorded_d10=7)
        self.assertEqual(r['duration'],7)
        self.assertEqual(r['duration_unit'],'COMBAT_ROUNDS')

    def test_033_summary_bout_duration_hours(self):
        r=sanity.bout_of_madness_plan(insanity_type='INDEFINITE',mode='SUMMARY',recorded_d10=4)
        self.assertEqual(r['duration_unit'],'HOURS')

    def test_034_bout_keeper_control(self):
        r=sanity.bout_of_madness_plan(insanity_type='TEMPORARY',mode='REAL_TIME',recorded_d10=5)
        self.assertTrue(r['keeper_control'])
        self.assertFalse(r['player_control'])

    def test_035_bout_content_not_auto_selected(self):
        r=sanity.bout_of_madness_plan(insanity_type='TEMPORARY',mode='REAL_TIME',recorded_d10=5)
        self.assertFalse(r['automatic_bout_content_selection'])
        self.assertTrue(r['keeper_or_source_selection_required'])

    def test_036_bout_backstory_not_auto_mutated(self):
        r=sanity.bout_of_madness_plan(insanity_type='TEMPORARY',mode='REAL_TIME',recorded_d10=5)
        self.assertFalse(r['backstory_mutation_automatic'])

    def test_037_invalid_bout_d10_blocks(self):
        r=sanity.bout_of_madness_plan(insanity_type='TEMPORARY',mode='REAL_TIME',recorded_d10=0)
        self.assertEqual(r['code'],'RECORDED_BOUT_D10_INVALID')

    def test_038_end_bout_restores_player_control(self):
        r=sanity.end_bout(insanity_type='TEMPORARY')
        self.assertEqual(r['state'],'UNDERLYING_INSANITY')
        self.assertTrue(r['player_control'])
        self.assertFalse(r['keeper_control'])

    def test_039_end_bout_marks_any_san_loss_trigger(self):
        r=sanity.end_bout(insanity_type='INDEFINITE')
        self.assertTrue(r['any_further_san_loss_triggers_bout'])

    def test_040_invalid_insanity_type_blocks(self):
        self.assertEqual(sanity.end_bout(insanity_type='UNKNOWN')['code'],'INSANITY_TYPE_INVALID')

    def test_041_reality_check_success_dispels_delusion(self):
        r=sanity.reality_check(current_san=60,units=0,tens=[4],underlying_insanity=True)
        self.assertTrue(r['success'])
        self.assertTrue(r['delusion_dispelled'])
        self.assertEqual(r['san_loss'],0)

    def test_042_reality_check_success_resists_until_next_san_loss(self):
        r=sanity.reality_check(current_san=60,units=0,tens=[4],underlying_insanity=True)
        self.assertTrue(r['delusion_resistant_until_next_san_loss'])

    def test_043_reality_check_failure_costs_one_san(self):
        r=sanity.reality_check(current_san=60,units=0,tens=[7],underlying_insanity=False)
        self.assertFalse(r['success'])
        self.assertEqual(r['SAN'],59)
        self.assertEqual(r['san_loss'],1)

    def test_044_reality_check_failure_under_insanity_triggers_bout(self):
        r=sanity.reality_check(current_san=60,units=0,tens=[7],underlying_insanity=True)
        self.assertTrue(r['bout_required'])

    def test_045_reality_check_unavailable_during_bout(self):
        r=sanity.reality_check(current_san=60,units=0,tens=[4],underlying_insanity=True,in_bout_of_madness=True)
        self.assertEqual(r['code'],'REALITY_CHECK_UNAVAILABLE_DURING_BOUT')

    def test_046_reality_check_can_reach_permanent_insanity(self):
        r=sanity.reality_check(current_san=1,units=0,tens=[9],underlying_insanity=True)
        self.assertEqual(r['SAN'],0)
        self.assertTrue(r['permanent_insanity'])
        self.assertFalse(r['bout_required'])

    def test_047_reality_check_no_randomness(self):
        r=sanity.reality_check(current_san=60,units=0,tens=[4],underlying_insanity=True)
        self.assertFalse(r['randomness_generated'])

    def test_048_delusion_resistance_survives_zero_loss(self):
        r=sanity.delusion_resistance_after_san_loss(resistant_before=True,san_loss=0)
        self.assertTrue(r['resistant'])
        self.assertFalse(r['cleared_by_san_loss'])

    def test_049_delusion_resistance_cleared_by_loss(self):
        r=sanity.delusion_resistance_after_san_loss(resistant_before=True,san_loss=1)
        self.assertFalse(r['resistant'])
        self.assertTrue(r['cleared_by_san_loss'])

    def test_050_first_mythos_insanity_gain_five(self):
        r=sanity.mythos_related_insanity_update(cthulhu_mythos=10,current_san=70,first_mythos_related_insanity=True)
        self.assertEqual(r['cthulhu_mythos_gain'],5)
        self.assertEqual(r['cthulhu_mythos'],15)

    def test_051_later_mythos_insanity_gain_one(self):
        r=sanity.mythos_related_insanity_update(cthulhu_mythos=10,current_san=70,first_mythos_related_insanity=False)
        self.assertEqual(r['cthulhu_mythos_gain'],1)

    def test_052_mythos_gain_updates_max_san(self):
        r=sanity.mythos_related_insanity_update(cthulhu_mythos=20,current_san=90,first_mythos_related_insanity=False)
        self.assertEqual(r['maximum_san'],78)
        self.assertEqual(r['SAN'],78)
        self.assertTrue(r['san_capped_by_new_maximum'])

    def test_053_mythos_above_99_fail_closed(self):
        r=sanity.mythos_related_insanity_update(cthulhu_mythos=99,current_san=0,first_mythos_related_insanity=False)
        self.assertEqual(r['code'],'CTHULHU_MYTHOS_RESULT_ABOVE_99_UNMATERIALIZED')

    def test_054_temp_recovery_by_duration(self):
        r=sanity.temporary_insanity_recovery(elapsed_hours=6,duration_hours=6)
        self.assertTrue(r['recovered_from_temporary_insanity'])
        self.assertEqual(r['reason'],'DURATION_COMPLETE')

    def test_055_temp_not_recovered_before_duration(self):
        r=sanity.temporary_insanity_recovery(elapsed_hours=5.9,duration_hours=6)
        self.assertFalse(r['recovered_from_temporary_insanity'])
        self.assertTrue(r['underlying_insanity_active'])

    def test_056_safe_sleep_can_recover_with_keeper_gate(self):
        r=sanity.temporary_insanity_recovery(elapsed_hours=1,duration_hours=8,good_night_sleep_completed=True,safe_place=True,keeper_allows_sleep_recovery=True)
        self.assertTrue(r['recovered_from_temporary_insanity'])
        self.assertEqual(r['reason'],'SAFE_GOOD_NIGHT_SLEEP')

    def test_057_sleep_recovery_blocked_by_tension(self):
        r=sanity.temporary_insanity_recovery(elapsed_hours=1,duration_hours=8,good_night_sleep_completed=True,safe_place=True,heightened_tension=True,keeper_allows_sleep_recovery=True)
        self.assertFalse(r['recovered_from_temporary_insanity'])

    def test_058_sleep_recovery_requires_keeper_gate(self):
        r=sanity.temporary_insanity_recovery(elapsed_hours=1,duration_hours=8,good_night_sleep_completed=True,safe_place=True,keeper_allows_sleep_recovery=False)
        self.assertFalse(r['recovered_from_temporary_insanity'])

    def test_059_invalid_elapsed_hours_blocks(self):
        r=sanity.temporary_insanity_recovery(elapsed_hours=-1,duration_hours=8)
        self.assertEqual(r['code'],'ELAPSED_HOURS_INVALID')

    def test_060_recorded_duration_replay_stable(self):
        a=sanity.resolve_temporary_insanity_int(int_value=70,units=0,tens=[4],recorded_duration_hours=8)
        b=sanity.resolve_temporary_insanity_int(int_value=70,units=0,tens=[4],recorded_duration_hours=8)
        self.assertEqual(a,b)

    def test_061_sanity_roll_replay_stable(self):
        kwargs=dict(current_san=55,units=7,tens=[6],recorded_success_loss=1,recorded_failure_loss=4,failure_loss_maximum=6)
        self.assertEqual(sanity.sanity_roll(**kwargs),sanity.sanity_roll(**kwargs))

    def test_062_apply_loss_replay_stable(self):
        kwargs=dict(current_san=55,loss=6,sanity_start_of_day=60,daily_loss_before=2)
        self.assertEqual(sanity.apply_sanity_loss(**kwargs),sanity.apply_sanity_loss(**kwargs))

    def test_063_bout_replay_stable(self):
        kwargs=dict(insanity_type='INDEFINITE',mode='SUMMARY',recorded_d10=9)
        self.assertEqual(sanity.bout_of_madness_plan(**kwargs),sanity.bout_of_madness_plan(**kwargs))

    def test_064_no_automatic_bout_selection_field(self):
        r=sanity.bout_of_madness_plan(insanity_type='INDEFINITE',mode='SUMMARY',recorded_d10=9)
        self.assertNotIn('selected_bout',r)

    def test_065_no_automatic_phobia_mania_field(self):
        r=sanity.bout_of_madness_plan(insanity_type='INDEFINITE',mode='SUMMARY',recorded_d10=9)
        self.assertNotIn('phobia',r)
        self.assertNotIn('mania',r)

    def test_066_no_automatic_game_day_end(self):
        r=sanity.apply_sanity_loss(current_san=50,loss=1,sanity_start_of_day=60,daily_loss_before=2)
        self.assertNotIn('game_day_ended',r)

    def test_067_parent_wounds_module_present(self):
        self.assertTrue(sanity.PARENT_WOUNDS_MODULE_ID.startswith('COC7_WOUNDS_HEALING'))

    def test_068_frozen_rules_parent_present(self):
        self.assertEqual(sanity.FROZEN_RULES_PACKAGE_ID,'COC7_RECOVERY_RULE_PACKAGE_R1_CORE_V1')

    def test_069_source_identity_present(self):
        self.assertEqual(sanity.KEEPER_SOURCE_ID,'COC7_KEEPER')

    def test_070_san_roll_current_above_99_blocks(self):
        r=sanity.sanity_roll(current_san=100,units=0,tens=[4],recorded_success_loss=0,recorded_failure_loss=1,failure_loss_maximum=1)
        self.assertEqual(r['code'],'CURRENT_SAN_INVALID_OR_PERMANENTLY_INSANE')

    def test_071_apply_loss_invalid_underlying_flag(self):
        r=sanity.apply_sanity_loss(current_san=50,loss=1,sanity_start_of_day=60,already_underlying_insanity=1)
        self.assertEqual(r['code'],'UNDERLYING_INSANITY_FLAG_INVALID')

    def test_072_bout_invalid_mode(self):
        r=sanity.bout_of_madness_plan(insanity_type='TEMPORARY',mode='UNKNOWN',recorded_d10=5)
        self.assertEqual(r['code'],'BOUT_MODE_INVALID')

    def test_073_reality_invalid_state_flag(self):
        r=sanity.reality_check(current_san=50,units=0,tens=[4],underlying_insanity=1)
        self.assertEqual(r['code'],'REALITY_CHECK_STATE_FLAG_INVALID')

    def test_074_mythos_first_flag_validation(self):
        r=sanity.mythos_related_insanity_update(cthulhu_mythos=1,current_san=50,first_mythos_related_insanity=1)
        self.assertEqual(r['code'],'FIRST_MYTHOS_INSANITY_FLAG_INVALID')

    def test_075_temp_recovery_flag_validation(self):
        r=sanity.temporary_insanity_recovery(elapsed_hours=1,duration_hours=4,safe_place=1)
        self.assertEqual(r['code'],'TEMPORARY_RECOVERY_FLAG_INVALID')

    def test_076_day_fifth_precedes_temp_threshold(self):
        r=sanity.apply_sanity_loss(current_san=51,loss=3,sanity_start_of_day=60,daily_loss_before=9)
        self.assertEqual(r['state'],'INDEFINITE_INSANITY')
        self.assertFalse(r['int_check_required'])

    def test_077_permanent_precedes_underlying_bout(self):
        r=sanity.apply_sanity_loss(current_san=1,loss=1,sanity_start_of_day=60,already_underlying_insanity=True)
        self.assertEqual(r['state'],'PERMANENT_INSANITY')
        self.assertFalse(r['bout_required'])

    def test_078_zero_loss_does_not_trigger_temp(self):
        r=sanity.apply_sanity_loss(current_san=60,loss=0,sanity_start_of_day=60)
        self.assertEqual(r['state'],'STABLE')

    def test_079_temp_int_result_no_randomness(self):
        r=sanity.resolve_temporary_insanity_int(int_value=70,units=0,tens=[4],recorded_duration_hours=5)
        self.assertFalse(r['randomness_generated'])

    def test_080_bout_plan_no_randomness(self):
        r=sanity.bout_of_madness_plan(insanity_type='TEMPORARY',mode='REAL_TIME',recorded_d10=5)
        self.assertFalse(r['randomness_generated'])


if __name__ == '__main__':
    unittest.main()
