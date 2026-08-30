from __future__ import annotations

import unittest

import wounds_healing_dev as healing


class WoundsHealingBatch1Tests(unittest.TestCase):
    def helper(self, skill=30, roll=20):
        return {'skill_value': skill, 'units': roll % 10, 'tens': [roll // 10]}

    def first_aid(self, **kwargs):
        defaults = dict(hours_since_damage=.5, previous_attempts=0, successful_treatment_already=False, dying=False)
        defaults.update(kwargs)
        return healing.first_aid_plan(**defaults)

    def medicine(self, **kwargs):
        defaults = dict(same_day=True, successful_treatment_already=False, dying=False, first_aid_stabilized=False, major_wound=False)
        defaults.update(kwargs)
        return healing.medicine_plan(**defaults)

    def major_plan(self, **kwargs):
        defaults = dict(max_hp=15, current_hp=4, major_wound=True, complete_rest=False, medical_care_modifier=0, poor_environment_and_insufficient_rest=False)
        defaults.update(kwargs)
        return healing.major_wound_recovery_plan(**defaults)

    def test_001_identity(self):
        self.assertEqual(healing.MODULE_ID, 'COC7_WOUNDS_HEALING_R1_BATCH1_DEV_V1')
        self.assertEqual(healing.PARENT_MELEE_MODULE_ID, 'COC7_MELEE_COMBAT_R1_BATCH1_DEV_V1')
        self.assertEqual(healing.FROZEN_RULES_PACKAGE_ID, 'COC7_RECOVERY_RULE_PACKAGE_R1_CORE_V1')
        self.assertEqual(healing.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_002_regular_damage_less_than_half(self):
        r = healing.assess_damage(max_hp=15, current_hp=15, damage=7)
        self.assertEqual(r['triage'], 'REGULAR_DAMAGE')
        self.assertFalse(r['major_wound'])

    def test_003_major_wound_at_half_or_more(self):
        r = healing.assess_damage(max_hp=15, current_hp=15, damage=8)
        self.assertEqual(r['triage'], 'MAJOR_WOUND')
        self.assertTrue(r['major_wound'])
        self.assertTrue(r['major_wound_inflicted_by_this_attack'])

    def test_004_more_than_max_hp_is_death(self):
        r = healing.assess_damage(max_hp=15, current_hp=15, damage=16)
        self.assertTrue(r['dead'])
        self.assertEqual(r['triage'], 'DEAD')
        self.assertEqual(r['current_hp'], 0)

    def test_005_equal_to_max_hp_is_major_wound_dying_not_instant_death(self):
        r = healing.assess_damage(max_hp=15, current_hp=15, damage=15)
        self.assertFalse(r['dead'])
        self.assertTrue(r['dying'])
        self.assertEqual(r['triage'], 'DYING')

    def test_006_regular_cumulative_damage_can_reach_zero_without_dying(self):
        r = healing.assess_damage(max_hp=15, current_hp=4, damage=4, had_major_wound=False)
        self.assertEqual(r['current_hp'], 0)
        self.assertTrue(r['unconscious'])
        self.assertFalse(r['dying'])
        self.assertEqual(r['triage'], 'UNCONSCIOUS_REGULAR_DAMAGE')

    def test_007_previous_major_wound_plus_regular_damage_to_zero_is_dying(self):
        r = healing.assess_damage(max_hp=15, current_hp=4, damage=4, had_major_wound=True)
        self.assertTrue(r['dying'])
        self.assertEqual(r['triage'], 'DYING')

    def test_008_major_wound_with_hp_remaining_requires_con(self):
        r = healing.assess_damage(max_hp=15, current_hp=15, damage=8)
        self.assertTrue(r['con_check_required_to_remain_conscious'])

    def test_009_major_wound_knocks_character_prone(self):
        r = healing.assess_damage(max_hp=15, current_hp=15, damage=8)
        self.assertTrue(r['prone'])

    def test_010_negative_hp_never_recorded(self):
        r = healing.assess_damage(max_hp=15, current_hp=3, damage=8)
        self.assertEqual(r['current_hp'], 0)
        self.assertFalse(r['negative_hp_recorded'])

    def test_011_invalid_damage_input_blocks(self):
        self.assertEqual(healing.assess_damage(max_hp=0, current_hp=0, damage=1)['code'], 'DAMAGE_INPUT_INVALID')

    def test_012_major_wound_con_success_remains_conscious(self):
        r = healing.resolve_major_wound_con(con_value=50, units=0, tens=[3])
        self.assertTrue(r['remains_conscious'])
        self.assertFalse(r['unconscious'])

    def test_013_major_wound_con_failure_falls_unconscious(self):
        r = healing.resolve_major_wound_con(con_value=50, units=0, tens=[8])
        self.assertFalse(r['remains_conscious'])
        self.assertTrue(r['unconscious'])

    def test_014_major_wound_con_critical_succeeds(self):
        r = healing.resolve_major_wound_con(con_value=50, units=1, tens=[0])
        self.assertEqual(r['success_level'], 'CRITICAL')
        self.assertTrue(r['remains_conscious'])

    def test_015_major_wound_con_invalid_value_blocks(self):
        self.assertEqual(healing.resolve_major_wound_con(con_value=101, units=0, tens=[3])['code'], 'SKILL_OR_CHARACTERISTIC_INVALID')

    def test_016_first_aid_within_hour_regular(self):
        p = self.first_aid(hours_since_damage=1)
        self.assertEqual(p['status'], 'RESOLVED')
        self.assertEqual(p['difficulty'], 'REGULAR')
        self.assertFalse(p['pushed_roll_required'])

    def test_017_first_aid_after_hour_blocks_normal_injury(self):
        self.assertEqual(self.first_aid(hours_since_damage=1.01)['code'], 'FIRST_AID_WINDOW_EXPIRED')

    def test_018_dying_first_aid_can_restabilize_after_original_hour(self):
        p = self.first_aid(hours_since_damage=3, dying=True, previous_attempts=2)
        self.assertEqual(p['status'], 'RESOLVED')
        self.assertFalse(p['pushed_roll_required'])
        self.assertTrue(p['pushed_roll_exempt_for_dying'])

    def test_019_second_normal_first_aid_attempt_is_pushed(self):
        self.assertTrue(self.first_aid(previous_attempts=1)['pushed_roll_required'])

    def test_020_dying_repeated_first_aid_is_not_pushed(self):
        self.assertFalse(self.first_aid(previous_attempts=4, dying=True)['pushed_roll_required'])

    def test_021_first_aid_success_already_used_blocks_normal_repeat(self):
        self.assertEqual(self.first_aid(successful_treatment_already=True)['code'], 'FIRST_AID_SUCCESS_ALREADY_USED_FOR_INJURY')

    def test_022_unfamiliar_physiology_fails_closed(self):
        self.assertEqual(self.first_aid(physiology='ALIEN')['code'], 'ALIEN_OR_UNFAMILIAR_PHYSIOLOGY_DIFFICULTY_UNMATERIALIZED')

    def test_023_first_aid_one_helper_success_recovers_one(self):
        p = self.first_aid()
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(skill=30, roll=20)])
        self.assertTrue(r['success'])
        self.assertEqual(r['hp_recovery'], 1)

    def test_024_two_helpers_either_success_is_success(self):
        p = self.first_aid()
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(skill=20, roll=80), self.helper(skill=40, roll=30)])
        self.assertTrue(r['success'])
        self.assertEqual(len(r['checks']), 2)

    def test_025_two_helpers_both_fail(self):
        p = self.first_aid()
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(skill=20, roll=80), self.helper(skill=30, roll=70)])
        self.assertFalse(r['success'])
        self.assertTrue(r['next_attempt_pushed'])

    def test_026_three_helpers_blocked(self):
        p = self.first_aid()
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(), self.helper(), self.helper()])
        self.assertEqual(r['code'], 'FIRST_AID_HELPER_COUNT_INVALID')

    def test_027_required_pushed_first_aid_cannot_be_silent_normal_retry(self):
        p = self.first_aid(previous_attempts=1)
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper()])
        self.assertEqual(r['code'], 'PUSHED_FIRST_AID_REQUIRED')

    def test_028_pushed_first_aid_can_succeed(self):
        p = self.first_aid(previous_attempts=1)
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(skill=40, roll=30)], pushed_roll=True)
        self.assertTrue(r['success'])
        self.assertFalse(r['pushed_failure_keeper_consequence_required'])

    def test_029_pushed_first_aid_failure_requires_keeper_consequence(self):
        p = self.first_aid(previous_attempts=1)
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(skill=30, roll=80)], pushed_roll=True)
        self.assertFalse(r['success'])
        self.assertTrue(r['pushed_failure_keeper_consequence_required'])

    def test_030_dying_first_aid_success_grants_one_temporary_hp(self):
        p = self.first_aid(dying=True)
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(skill=40, roll=20)])
        self.assertTrue(r['stabilized'])
        self.assertEqual(r['temporary_hp'], 1)
        self.assertEqual(r['next_con_check'], 'END_OF_EACH_HOUR')

    def test_031_dying_first_aid_failure_allows_retry_next_round_if_alive(self):
        p = self.first_aid(dying=True)
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(skill=30, roll=80)])
        self.assertFalse(r['stabilized'])
        self.assertTrue(r['repeat_first_aid_next_round_if_alive'])

    def test_032_dying_first_aid_must_not_be_marked_pushed(self):
        p = self.first_aid(dying=True, previous_attempts=2)
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper()], pushed_roll=True)
        self.assertEqual(r['code'], 'DYING_FIRST_AID_REPEAT_IS_NOT_PUSHED')

    def test_033_first_aid_success_can_rouse_unconscious(self):
        p = self.first_aid()
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(skill=40, roll=20)])
        self.assertTrue(r['rouse_unconscious_possible'])

    def test_034_first_aid_generates_no_randomness(self):
        p = self.first_aid()
        r = healing.resolve_first_aid(plan=p, helpers=[self.helper(skill=40, roll=20)])
        self.assertFalse(r['randomness_generated'])

    def test_035_first_aid_missing_helper_roll_blocks(self):
        p = self.first_aid()
        r = healing.resolve_first_aid(plan=p, helpers=[{'skill_value': 30}])
        self.assertEqual(r['code'], 'FIRST_AID_HELPER_ROLL_MISSING')

    def test_036_medicine_same_day_regular(self):
        p = self.medicine(same_day=True)
        self.assertEqual(p['difficulty'], 'REGULAR')
        self.assertEqual(p['minimum_treatment_hours'], 1)

    def test_037_medicine_later_is_hard(self):
        self.assertEqual(self.medicine(same_day=False)['difficulty'], 'HARD')

    def test_038_dying_medicine_requires_first_aid_stabilization(self):
        p = self.medicine(dying=True, first_aid_stabilized=False)
        self.assertEqual(p['code'], 'DYING_REQUIRES_FIRST_AID_STABILIZATION_BEFORE_MEDICINE')

    def test_039_dying_stabilized_allows_medicine_plan(self):
        p = self.medicine(dying=True, first_aid_stabilized=True, major_wound=True)
        self.assertEqual(p['status'], 'RESOLVED')
        self.assertTrue(p['dying'])

    def test_040_medicine_success_already_used_blocks_repeat(self):
        self.assertEqual(self.medicine(successful_treatment_already=True)['code'], 'MEDICINE_SUCCESS_ALREADY_USED_FOR_INJURY')

    def test_041_hospital_auto_success_requires_explicit_authorization(self):
        p = self.medicine(hospital_auto_success_authorized=True)
        self.assertTrue(p['automatic_success'])
        self.assertTrue(p['hospital_auto_success_explicitly_authorized'])

    def test_042_hospital_auto_success_still_requires_recorded_d3(self):
        p = self.medicine(hospital_auto_success_authorized=True)
        r = healing.resolve_medicine(plan=p, recovery_d3=None)
        self.assertEqual(r['code'], 'RECORDED_D3_REQUIRED_ON_MEDICINE_SUCCESS')

    def test_043_medicine_regular_success_recovers_recorded_d3(self):
        p = self.medicine()
        r = healing.resolve_medicine(plan=p, skill_value=60, units=0, tens=[4], recovery_d3=3)
        self.assertTrue(r['success'])
        self.assertEqual(r['hp_recovery'], 3)

    def test_044_late_medicine_regular_level_does_not_meet_hard(self):
        p = self.medicine(same_day=False)
        r = healing.resolve_medicine(plan=p, skill_value=60, units=0, tens=[4], recovery_d3=None)
        self.assertFalse(r['success'])
        self.assertEqual(r['success_level'], 'REGULAR')

    def test_045_late_medicine_hard_success_succeeds(self):
        p = self.medicine(same_day=False)
        r = healing.resolve_medicine(plan=p, skill_value=60, units=0, tens=[3], recovery_d3=2)
        self.assertTrue(r['success'])
        self.assertEqual(r['success_level'], 'HARD')

    def test_046_successful_medicine_on_major_wound_grants_weekly_bonus(self):
        p = self.medicine(major_wound=True)
        r = healing.resolve_medicine(plan=p, skill_value=60, units=0, tens=[4], recovery_d3=2)
        self.assertEqual(r['major_wound_weekly_bonus_die'], 1)

    def test_047_successful_medicine_after_first_aid_clears_dying(self):
        p = self.medicine(dying=True, first_aid_stabilized=True, major_wound=True)
        r = healing.resolve_medicine(plan=p, skill_value=60, units=0, tens=[4], recovery_d3=2)
        self.assertTrue(r['dying_cleared'])
        self.assertEqual(r['hp_recovery'], 2)

    def test_048_failed_medicine_can_be_pushed(self):
        p = self.medicine()
        r = healing.resolve_medicine(plan=p, skill_value=30, units=0, tens=[8], recovery_d3=None)
        self.assertFalse(r['success'])
        self.assertTrue(r['push_available'])

    def test_049_failed_pushed_medicine_requires_keeper_consequence(self):
        p = self.medicine()
        r = healing.resolve_medicine(plan=p, skill_value=30, units=0, tens=[8], recovery_d3=None, pushed_roll=True)
        self.assertTrue(r['pushed_failure_keeper_consequence_required'])

    def test_050_failed_pushed_medicine_on_dying_patient_is_death(self):
        p = self.medicine(dying=True, first_aid_stabilized=True, major_wound=True)
        r = healing.resolve_medicine(plan=p, skill_value=30, units=0, tens=[8], recovery_d3=None, pushed_roll=True)
        self.assertTrue(r['patient_dies_on_pushed_failure'])

    def test_051_medicine_success_invalid_d3_blocks(self):
        p = self.medicine()
        r = healing.resolve_medicine(plan=p, skill_value=60, units=0, tens=[4], recovery_d3=4)
        self.assertEqual(r['code'], 'RECORDED_D3_REQUIRED_ON_MEDICINE_SUCCESS')

    def test_052_medicine_roll_required_when_not_hospital_auto(self):
        p = self.medicine()
        self.assertEqual(healing.resolve_medicine(plan=p, recovery_d3=2)['code'], 'MEDICINE_ROLL_REQUIRED')

    def test_053_hospital_auto_success_uses_no_percentile_roll(self):
        p = self.medicine(hospital_auto_success_authorized=True)
        r = healing.resolve_medicine(plan=p, recovery_d3=2)
        self.assertTrue(r['success'])
        self.assertIsNone(r['roll'])

    def test_054_invalid_medicine_flag_blocks(self):
        self.assertEqual(healing.medicine_plan(same_day=1)['code'], 'MEDICINE_FLAG_INVALID')

    def test_055_dying_round_con_success_survives(self):
        r = healing.dying_con_check(phase='DYING_ROUNDLY', con_value=50, units=0, tens=[3])
        self.assertTrue(r['survives'])
        self.assertTrue(r['remains_dying'])
        self.assertEqual(r['next_check'], 'END_OF_NEXT_ROUND')

    def test_056_dying_round_con_failure_is_immediate_death(self):
        r = healing.dying_con_check(phase='DYING_ROUNDLY', con_value=50, units=0, tens=[8])
        self.assertFalse(r['survives'])
        self.assertTrue(r['dead'])

    def test_057_stabilized_hourly_con_success_remains_stable(self):
        r = healing.dying_con_check(phase='STABILIZED_HOURLY', con_value=50, units=0, tens=[3])
        self.assertTrue(r['stays_stabilized'])
        self.assertEqual(r['temporary_hp_lost'], 0)

    def test_058_stabilized_hourly_con_failure_loses_temp_hp_and_reverts(self):
        r = healing.dying_con_check(phase='STABILIZED_HOURLY', con_value=50, units=0, tens=[8])
        self.assertFalse(r['stays_stabilized'])
        self.assertEqual(r['temporary_hp_lost'], 1)
        self.assertTrue(r['returns_to_dying_roundly'])
        self.assertEqual(r['next_check'], 'END_OF_NEXT_ROUND')

    def test_059_invalid_dying_phase_blocks(self):
        self.assertEqual(healing.dying_con_check(phase='DAILY', con_value=50, units=0, tens=[3])['code'], 'DYING_CON_PHASE_INVALID')

    def test_060_dying_checks_generate_no_randomness(self):
        r = healing.dying_con_check(phase='DYING_ROUNDLY', con_value=50, units=0, tens=[3])
        self.assertFalse(r['randomness_generated'])

    def test_061_regular_recovery_one_hp_per_day(self):
        r = healing.regular_damage_recovery(max_hp=15, current_hp=10, days=3, major_wound=False)
        self.assertEqual(r['hp_recovered'], 3)
        self.assertEqual(r['current_hp'], 13)

    def test_062_regular_recovery_caps_at_max(self):
        r = healing.regular_damage_recovery(max_hp=15, current_hp=14, days=5, major_wound=False)
        self.assertEqual(r['current_hp'], 15)
        self.assertEqual(r['hp_recovered'], 1)

    def test_063_zero_hp_regular_damage_recovers_after_one_day(self):
        r = healing.regular_damage_recovery(max_hp=15, current_hp=0, days=1, major_wound=False)
        self.assertEqual(r['current_hp'], 1)
        self.assertFalse(r['unconscious_from_zero_hp'])

    def test_064_major_wound_does_not_use_daily_recovery(self):
        r = healing.regular_damage_recovery(max_hp=15, current_hp=5, days=1, major_wound=True)
        self.assertEqual(r['code'], 'MAJOR_WOUND_REQUIRES_WEEKLY_RECOVERY')

    def test_065_invalid_regular_recovery_input_blocks(self):
        self.assertEqual(healing.regular_damage_recovery(max_hp=15, current_hp=5, days=-1, major_wound=False)['code'], 'REGULAR_RECOVERY_INPUT_INVALID')

    def test_066_weekly_medicine_success_is_bonus_die(self):
        r = healing.weekly_medical_care_modifier(medicine_skill=60, units=0, tens=[4])
        self.assertEqual(r['modifier'], 1)
        self.assertTrue(r['care_effective'])

    def test_067_weekly_medicine_failure_is_no_modifier(self):
        r = healing.weekly_medical_care_modifier(medicine_skill=30, units=0, tens=[8])
        self.assertEqual(r['modifier'], 0)

    def test_068_weekly_medicine_fumble_is_penalty_die(self):
        r = healing.weekly_medical_care_modifier(medicine_skill=30, units=6, tens=[9])
        self.assertEqual(r['success_level'], 'FUMBLE')
        self.assertEqual(r['modifier'], -1)
        self.assertTrue(r['medicine_fumble'])

    def test_069_weekly_hospital_auto_care_is_bonus_if_explicit(self):
        r = healing.weekly_medical_care_modifier(hospital_auto_success_authorized=True)
        self.assertEqual(r['modifier'], 1)
        self.assertTrue(r['care_effective'])

    def test_070_weekly_medical_care_requires_roll_or_explicit_hospital(self):
        self.assertEqual(healing.weekly_medical_care_modifier()['code'], 'WEEKLY_MEDICINE_ROLL_REQUIRED')

    def test_071_complete_rest_adds_bonus(self):
        p = self.major_plan(complete_rest=True)
        self.assertEqual(p['net_bonus'], 1)

    def test_072_effective_medical_care_adds_bonus(self):
        p = self.major_plan(medical_care_modifier=1)
        self.assertEqual(p['net_bonus'], 1)

    def test_073_poor_environment_and_insufficient_rest_adds_penalty(self):
        p = self.major_plan(poor_environment_and_insufficient_rest=True)
        self.assertEqual(p['net_bonus'], -1)

    def test_074_rest_and_effective_care_produce_two_bonus_dice(self):
        p = self.major_plan(complete_rest=True, medical_care_modifier=1)
        self.assertEqual(p['net_bonus'], 2)

    def test_075_rest_can_cancel_poor_environment_penalty(self):
        p = self.major_plan(complete_rest=True, poor_environment_and_insufficient_rest=True)
        self.assertEqual(p['net_bonus'], 0)

    def test_076_medicine_fumble_plus_poor_environment_produce_two_penalties(self):
        p = self.major_plan(medical_care_modifier=-1, poor_environment_and_insufficient_rest=True)
        self.assertEqual(p['net_bonus'], -2)

    def test_077_invalid_medical_care_modifier_blocks(self):
        self.assertEqual(self.major_plan(medical_care_modifier=2)['code'], 'MEDICAL_CARE_MODIFIER_INVALID')

    def test_078_major_recovery_requires_marker(self):
        self.assertEqual(self.major_plan(major_wound=False)['code'], 'MAJOR_WOUND_MARKER_NOT_SET')

    def test_079_regular_weekly_con_success_recovers_one_d3(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[4], recorded_d3=[2])
        self.assertEqual(r['success_level'], 'REGULAR')
        self.assertEqual(r['hp_recovered'], 2)

    def test_080_hard_weekly_con_success_still_recovers_one_d3(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[3], recorded_d3=[3])
        self.assertEqual(r['success_level'], 'HARD')
        self.assertEqual(r['hp_recovered'], 3)

    def test_081_extreme_weekly_con_recovers_two_d3(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[1], recorded_d3=[2, 3])
        self.assertEqual(r['success_level'], 'EXTREME')
        self.assertEqual(r['hp_recovered'], 5)

    def test_082_critical_weekly_con_recovers_two_d3(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=1, tens=[0], recorded_d3=[1, 3])
        self.assertEqual(r['success_level'], 'CRITICAL')
        self.assertEqual(r['hp_recovered'], 4)

    def test_083_failed_weekly_con_recovers_nothing(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[8], recorded_d3=[])
        self.assertEqual(r['success_level'], 'FAILURE')
        self.assertEqual(r['hp_recovered'], 0)

    def test_084_failure_rejects_unearned_d3(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[8], recorded_d3=[2])
        self.assertEqual(r['code'], 'D3_NOT_USED_ON_RECOVERY_FAILURE')

    def test_085_fumble_requires_keeper_selected_complication(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=30, units=6, tens=[9], recorded_d3=[])
        self.assertEqual(r['success_level'], 'FUMBLE')
        self.assertTrue(r['complication_keeper_selection_required'])

    def test_086_fumble_rejects_d3(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=30, units=6, tens=[9], recorded_d3=[1])
        self.assertEqual(r['code'], 'D3_NOT_USED_ON_RECOVERY_FUMBLE')

    def test_087_regular_success_requires_exactly_one_recorded_d3(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[4], recorded_d3=[1, 2])
        self.assertEqual(r['code'], 'RECORDED_D3_COUNT_OR_VALUE_INVALID')

    def test_088_recorded_d3_value_must_be_one_to_three(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[4], recorded_d3=[4])
        self.assertEqual(r['code'], 'RECORDED_D3_COUNT_OR_VALUE_INVALID')

    def test_089_extreme_recovery_clears_major_wound_even_below_half_hp(self):
        p = self.major_plan(current_hp=1)
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[1], recorded_d3=[1, 1])
        self.assertTrue(r['major_wound_cleared'])
        self.assertEqual(r['clear_reason'], 'EXTREME_RECOVERY')

    def test_090_reaching_half_or_more_max_hp_clears_marker(self):
        p = self.major_plan(max_hp=15, current_hp=6)
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[4], recorded_d3=[2])
        self.assertEqual(r['current_hp'], 8)
        self.assertTrue(r['major_wound_cleared'])
        self.assertEqual(r['clear_reason'], 'HALF_OR_MORE_MAX_HP')

    def test_091_staying_below_half_keeps_marker(self):
        p = self.major_plan(max_hp=15, current_hp=5)
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[4], recorded_d3=[2])
        self.assertEqual(r['current_hp'], 7)
        self.assertFalse(r['major_wound_cleared'])

    def test_092_weekly_recovery_caps_at_max_hp(self):
        p = self.major_plan(max_hp=15, current_hp=14)
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[4], recorded_d3=[3])
        self.assertEqual(r['current_hp'], 15)
        self.assertEqual(r['hp_recovered'], 1)

    def test_093_bonus_die_uses_best_recorded_tens(self):
        p = self.major_plan(complete_rest=True)
        r = healing.resolve_major_wound_recovery(plan=p, con_value=50, units=5, tens=[7, 2], recorded_d3=[2])
        self.assertEqual(r['roll'], 25)
        self.assertEqual(r['success_level'], 'HARD')

    def test_094_penalty_die_uses_worst_recorded_tens(self):
        p = self.major_plan(poor_environment_and_insufficient_rest=True)
        r = healing.resolve_major_wound_recovery(plan=p, con_value=50, units=5, tens=[2, 7], recorded_d3=[])
        self.assertEqual(r['roll'], 75)
        self.assertEqual(r['success_level'], 'FAILURE')

    def test_095_two_bonus_dice_require_three_recorded_tens(self):
        p = self.major_plan(complete_rest=True, medical_care_modifier=1)
        r = healing.resolve_major_wound_recovery(plan=p, con_value=50, units=5, tens=[7, 4, 1], recorded_d3=[2])
        self.assertEqual(r['roll'], 15)
        self.assertEqual(r['success_level'], 'HARD')

    def test_096_wrong_tens_count_blocks_recovery(self):
        p = self.major_plan(complete_rest=True)
        r = healing.resolve_major_wound_recovery(plan=p, con_value=50, units=5, tens=[2], recorded_d3=[2])
        self.assertEqual(r['code'], 'TENS_DICE_COUNT_INVALID')

    def test_097_major_recovery_generates_no_randomness(self):
        p = self.major_plan()
        r = healing.resolve_major_wound_recovery(plan=p, con_value=60, units=0, tens=[4], recorded_d3=[2])
        self.assertFalse(r['randomness_generated'])

    def test_098_parent_melee_identity_survives(self):
        self.assertEqual(healing.melee.MODULE_ID, 'COC7_MELEE_COMBAT_R1_BATCH1_DEV_V1')


if __name__ == '__main__':
    unittest.main()
