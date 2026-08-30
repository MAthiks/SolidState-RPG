from __future__ import annotations

import unittest

import chase_dev as chase


class ChaseBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(chase.MODULE_ID,'COC7_CHASE_R1_BATCH1_DEV_V1')
        self.assertEqual(chase.PARENT_SANITY_TREATMENT_MODULE_ID,'COC7_SANITY_TREATMENT_R1_BATCH2_DEV_V1')
        self.assertEqual(chase.KEEPER_SHA256,'691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_002_foot_speed_success_no_change(self):
        r=chase.speed_roll(mode='FOOT',base_mov=7,skill_value=60,units=0,tens=[4])
        self.assertEqual(r['adjusted_mov'],7)
        self.assertEqual(r['required_skill_family'],'CON')

    def test_003_foot_speed_extreme_plus_one(self):
        r=chase.speed_roll(mode='FOOT',base_mov=7,skill_value=60,units=0,tens=[1])
        self.assertEqual(r['mov_delta'],1)
        self.assertEqual(r['adjusted_mov'],8)

    def test_004_speed_failure_minus_one(self):
        r=chase.speed_roll(mode='FOOT',base_mov=7,skill_value=60,units=0,tens=[7])
        self.assertEqual(r['mov_delta'],-1)
        self.assertEqual(r['adjusted_mov'],6)

    def test_005_vehicle_uses_drive_auto_family(self):
        r=chase.speed_roll(mode='VEHICLE',base_mov=8,skill_value=60,units=0,tens=[4])
        self.assertEqual(r['required_skill_family'],'DRIVE_AUTO')

    def test_006_self_propelled_uses_con(self):
        r=chase.speed_roll(mode='SELF_PROPELLED',base_mov=6,skill_value=50,units=0,tens=[4])
        self.assertEqual(r['required_skill_family'],'CON')

    def test_007_speed_result_lasts_chase(self):
        r=chase.speed_roll(mode='FOOT',base_mov=7,skill_value=60,units=0,tens=[4])
        self.assertEqual(r['duration'],'CHASE')

    def test_008_speed_no_randomness(self):
        r=chase.speed_roll(mode='FOOT',base_mov=7,skill_value=60,units=0,tens=[4])
        self.assertFalse(r['randomness_generated'])

    def test_009_invalid_mode_blocks(self):
        self.assertEqual(chase.speed_roll(mode='HORSE?',base_mov=7,skill_value=60,units=0,tens=[4])['code'],'CHASE_MODE_INVALID')

    def test_010_invalid_base_mov_blocks(self):
        self.assertEqual(chase.speed_roll(mode='FOOT',base_mov=-1,skill_value=60,units=0,tens=[4])['code'],'BASE_MOV_INVALID')

    def test_011_fleeing_faster_escapes(self):
        r=chase.establish_chase(fleeing_adjusted_mov=8,pursuer_adjusted_mov=7)
        self.assertFalse(r['chase_established'])
        self.assertEqual(r['outcome'],'FLEEING_CHARACTER_ESCAPES')

    def test_012_equal_speed_establishes_chase(self):
        r=chase.establish_chase(fleeing_adjusted_mov=7,pursuer_adjusted_mov=7)
        self.assertTrue(r['chase_established'])

    def test_013_pursuer_faster_establishes_chase(self):
        r=chase.establish_chase(fleeing_adjusted_mov=6,pursuer_adjusted_mov=7)
        self.assertTrue(r['chase_established'])

    def test_014_default_starting_range_two(self):
        r=chase.starting_range()
        self.assertEqual(r['starting_range_locations'],2)

    def test_015_one_location_requires_exceptional_gate(self):
        r=chase.starting_range(keeper_selected_locations=1,exceptional_circumstances=False)
        self.assertEqual(r['code'],'ONE_LOCATION_REQUIRES_EXCEPTIONAL_KEEPER_GATE')

    def test_016_one_location_allowed_exceptionally(self):
        r=chase.starting_range(keeper_selected_locations=1,exceptional_circumstances=True)
        self.assertEqual(r['starting_range_locations'],1)

    def test_017_three_locations_fail_closed(self):
        r=chase.starting_range(keeper_selected_locations=3,exceptional_circumstances=True)
        self.assertEqual(r['code'],'STARTING_RANGE_OUTSIDE_BATCH1')

    def test_018_slowest_gets_one_action(self):
        r=chase.movement_actions(adjusted_mov=5,slowest_adjusted_mov=5)
        self.assertEqual(r['movement_actions'],1)

    def test_019_one_faster_gets_two_actions(self):
        r=chase.movement_actions(adjusted_mov=6,slowest_adjusted_mov=5)
        self.assertEqual(r['movement_actions'],2)

    def test_020_two_faster_gets_three_actions(self):
        r=chase.movement_actions(adjusted_mov=7,slowest_adjusted_mov=5)
        self.assertEqual(r['movement_actions'],3)

    def test_021_declared_slowest_validation(self):
        r=chase.movement_actions(adjusted_mov=4,slowest_adjusted_mov=5)
        self.assertEqual(r['code'],'PARTICIPANT_BELOW_DECLARED_SLOWEST_MOV')

    def test_022_dex_order_high_to_low(self):
        r=chase.dex_order(participants=[{'id':'A','dex':40},{'id':'B','dex':70},{'id':'C','dex':55}])
        self.assertEqual(r['provisional_order'],['B','C','A'])

    def test_023_dex_tie_is_not_silently_resolved(self):
        r=chase.dex_order(participants=[{'id':'A','dex':50},{'id':'B','dex':50}])
        self.assertTrue(r['ties_require_opposed_dex_roll'])
        self.assertTrue(r['ties'][0]['opposed_dex_roll_required'])

    def test_024_dex_empty_blocks(self):
        self.assertEqual(chase.dex_order(participants=[])['code'],'CHASE_PARTICIPANTS_REQUIRED')

    def test_025_dex_invalid_participant_blocks(self):
        self.assertEqual(chase.dex_order(participants=[{'id':'A','dex':101}])['code'],'CHASE_PARTICIPANT_INVALID')

    def test_026_clear_move_costs_one(self):
        r=chase.clear_location_move(movement_actions_available=3)
        self.assertEqual(r['advanced_locations'],1)
        self.assertEqual(r['movement_actions_spent'],1)
        self.assertEqual(r['movement_actions_remaining'],2)

    def test_027_clear_move_requires_action(self):
        self.assertEqual(chase.clear_location_move(movement_actions_available=0)['code'],'INSUFFICIENT_MOVEMENT_ACTIONS')

    def test_028_hazard_no_caution_no_bonus(self):
        r=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        self.assertEqual(r['bonus_dice'],0)

    def test_029_hazard_one_caution_one_bonus(self):
        r=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=1)
        self.assertEqual(r['bonus_dice'],1)

    def test_030_hazard_two_caution_two_bonus(self):
        r=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=2)
        self.assertEqual(r['bonus_dice'],2)

    def test_031_hazard_more_than_two_caution_blocks(self):
        self.assertEqual(chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=3)['code'],'CAUTIOUS_ACTIONS_INVALID')

    def test_032_hazard_invalid_difficulty_blocks(self):
        self.assertEqual(chase.hazard_plan(difficulty='IMPOSSIBLE',cautious_actions_spent=0)['code'],'HAZARD_DIFFICULTY_INVALID')

    def test_033_hazard_success_advances(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[4])
        self.assertTrue(r['success'])
        self.assertTrue(r['advanced_to_next_location'])
        self.assertEqual(r['lost_movement_actions'],0)

    def test_034_hazard_failure_also_advances(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[8],recorded_lost_actions_d3=2)
        self.assertFalse(r['success'])
        self.assertTrue(r['advanced_to_next_location'])
        self.assertEqual(r['lost_movement_actions'],2)

    def test_035_hazard_failure_requires_recorded_d3(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[8])
        self.assertEqual(r['code'],'RECORDED_HAZARD_D3_REQUIRED')

    def test_036_hazard_failure_keeper_damage_optional(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[8],recorded_lost_actions_d3=2,keeper_selected_damage=3)
        self.assertEqual(r['damage'],3)
        self.assertTrue(r['damage_selected_by_keeper'])

    def test_037_hazard_failure_without_damage_is_zero(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[8],recorded_lost_actions_d3=1)
        self.assertEqual(r['damage'],0)
        self.assertFalse(r['damage_selected_by_keeper'])

    def test_038_hazard_success_rejects_failure_outcome_values(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[4],recorded_lost_actions_d3=1)
        self.assertEqual(r['code'],'HAZARD_SUCCESS_MUST_NOT_CONSUME_FAILURE_OUTCOMES')

    def test_039_hazard_hard_requires_hard(self):
        p=chase.hazard_plan(difficulty='HARD',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[4],recorded_lost_actions_d3=1)
        self.assertFalse(r['success'])

    def test_040_hazard_hard_success(self):
        p=chase.hazard_plan(difficulty='HARD',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[3])
        self.assertTrue(r['success'])

    def test_041_hazard_bonus_die_uses_recorded_digits(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=1)
        r=chase.resolve_hazard(plan=p,skill_value=50,units=5,tens=[7,2])
        self.assertEqual(r['roll'],25)
        self.assertTrue(r['success'])

    def test_042_hazard_two_bonus_dice(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=2)
        r=chase.resolve_hazard(plan=p,skill_value=50,units=5,tens=[7,4,1])
        self.assertEqual(r['roll'],15)

    def test_043_hazard_no_randomness_success(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        self.assertFalse(chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[4])['randomness_generated'])

    def test_044_hazard_no_randomness_failure(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        self.assertFalse(chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[8],recorded_lost_actions_d3=1)['randomness_generated'])

    def test_045_barrier_success_advances(self):
        p=chase.barrier_plan(difficulty='REGULAR')
        r=chase.resolve_barrier(plan=p,skill_value=60,units=0,tens=[4])
        self.assertTrue(r['success'])
        self.assertTrue(r['advanced_to_next_location'])

    def test_046_barrier_failure_does_not_advance(self):
        p=chase.barrier_plan(difficulty='REGULAR')
        r=chase.resolve_barrier(plan=p,skill_value=60,units=0,tens=[8])
        self.assertFalse(r['success'])
        self.assertFalse(r['advanced_to_next_location'])

    def test_047_barrier_failure_keeper_may_select_damage_or_delay(self):
        p=chase.barrier_plan(difficulty='REGULAR')
        r=chase.resolve_barrier(plan=p,skill_value=60,units=0,tens=[8])
        self.assertTrue(r['keeper_may_select_damage_or_delay_on_failure'])
        self.assertFalse(r['automatic_damage_or_delay'])

    def test_048_barrier_caution_bonus(self):
        p=chase.barrier_plan(difficulty='REGULAR',cautious_actions_spent=1)
        r=chase.resolve_barrier(plan=p,skill_value=50,units=5,tens=[7,2])
        self.assertEqual(r['roll'],25)
        self.assertTrue(r['success'])

    def test_049_barrier_two_bonus_max(self):
        p=chase.barrier_plan(difficulty='REGULAR',cautious_actions_spent=2)
        self.assertEqual(p['bonus_dice'],2)

    def test_050_barrier_three_caution_blocks(self):
        self.assertEqual(chase.barrier_plan(difficulty='REGULAR',cautious_actions_spent=3)['code'],'CAUTIOUS_ACTIONS_INVALID')

    def test_051_barrier_no_randomness(self):
        p=chase.barrier_plan(difficulty='REGULAR')
        self.assertFalse(chase.resolve_barrier(plan=p,skill_value=60,units=0,tens=[4])['randomness_generated'])

    def test_052_attack_costs_one_action(self):
        r=chase.chase_attack_gate(movement_actions_available=2,same_location=True,firearm_attack=False)
        self.assertEqual(r['movement_actions_spent'],1)
        self.assertEqual(r['movement_actions_remaining'],1)

    def test_053_attack_requires_action_available(self):
        r=chase.chase_attack_gate(movement_actions_available=0,same_location=True,firearm_attack=False)
        self.assertEqual(r['code'],'ATTACK_REQUIRES_ONE_MOVEMENT_ACTION')

    def test_054_melee_requires_same_location(self):
        r=chase.chase_attack_gate(movement_actions_available=2,same_location=False,firearm_attack=False)
        self.assertEqual(r['code'],'NON_FIREARM_ATTACK_REQUIRES_SAME_LOCATION')

    def test_055_firearm_can_attack_across_locations_gate(self):
        r=chase.chase_attack_gate(movement_actions_available=2,same_location=False,firearm_attack=True)
        self.assertTrue(r['attack_allowed'])

    def test_056_defensive_response_even_without_defender_actions(self):
        r=chase.chase_attack_gate(movement_actions_available=1,same_location=True,firearm_attack=False)
        self.assertTrue(r['defensive_response_allowed_even_if_defender_has_no_actions'])

    def test_057_pushes_forbidden(self):
        self.assertFalse(chase.pushed_roll_policy()['pushed_rolls_allowed'])

    def test_058_speed_replay_stable(self):
        kwargs=dict(mode='FOOT',base_mov=7,skill_value=60,units=0,tens=[1])
        self.assertEqual(chase.speed_roll(**kwargs),chase.speed_roll(**kwargs))

    def test_059_hazard_replay_stable(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=1)
        kwargs=dict(plan=p,skill_value=50,units=5,tens=[7,2])
        self.assertEqual(chase.resolve_hazard(**kwargs),chase.resolve_hazard(**kwargs))

    def test_060_barrier_replay_stable(self):
        p=chase.barrier_plan(difficulty='REGULAR',cautious_actions_spent=1)
        kwargs=dict(plan=p,skill_value=50,units=5,tens=[7,2])
        self.assertEqual(chase.resolve_barrier(**kwargs),chase.resolve_barrier(**kwargs))

    def test_061_starting_range_replay_stable(self):
        self.assertEqual(chase.starting_range(),chase.starting_range())

    def test_062_mov_actions_replay_stable(self):
        self.assertEqual(chase.movement_actions(adjusted_mov=7,slowest_adjusted_mov=5),chase.movement_actions(adjusted_mov=7,slowest_adjusted_mov=5))

    def test_063_no_auto_location_generation_in_speed(self):
        r=chase.speed_roll(mode='FOOT',base_mov=7,skill_value=60,units=0,tens=[4])
        self.assertNotIn('locations',r)

    def test_064_no_auto_hazard_damage(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[8],recorded_lost_actions_d3=1)
        self.assertEqual(r['damage'],0)

    def test_065_no_auto_barrier_damage(self):
        p=chase.barrier_plan(difficulty='REGULAR')
        r=chase.resolve_barrier(plan=p,skill_value=60,units=0,tens=[8])
        self.assertFalse(r['automatic_damage_or_delay'])

    def test_066_parent_module_present(self):
        self.assertTrue(chase.PARENT_SANITY_TREATMENT_MODULE_ID.startswith('COC7_SANITY_TREATMENT'))

    def test_067_frozen_rules_parent_present(self):
        self.assertEqual(chase.FROZEN_RULES_PACKAGE_ID,'COC7_RECOVERY_RULE_PACKAGE_R1_CORE_V1')

    def test_068_source_identity_present(self):
        self.assertEqual(chase.KEEPER_SOURCE_ID,'COC7_KEEPER')

    def test_069_negative_attack_actions_block(self):
        r=chase.chase_attack_gate(movement_actions_available=-1,same_location=True,firearm_attack=False)
        self.assertEqual(r['code'],'CHASE_ATTACK_INPUT_INVALID')

    def test_070_invalid_hazard_damage_blocks(self):
        p=chase.hazard_plan(difficulty='REGULAR',cautious_actions_spent=0)
        r=chase.resolve_hazard(plan=p,skill_value=60,units=0,tens=[8],recorded_lost_actions_d3=1,keeper_selected_damage=-1)
        self.assertEqual(r['code'],'KEEPER_SELECTED_DAMAGE_INVALID')


if __name__ == '__main__':
    unittest.main()
