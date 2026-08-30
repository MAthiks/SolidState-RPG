from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import chase_batch2_dev as c


class ChaseBatch2Tests(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(c.MODULE_ID, 'COC7_CHASE_R1_BATCH2_DEV_V1')
        self.assertEqual(c.PARENT_CHASE_MODULE_ID, 'COC7_CHASE_R1_BATCH1_DEV_V1')

    def test_acceleration_one_location(self):
        r=c.acceleration_plan(locations=1)
        self.assertFalse(r['accelerated']); self.assertEqual(r['hazard_penalty_dice'],0)

    def test_acceleration_two_locations(self):
        self.assertEqual(c.acceleration_plan(locations=2)['hazard_penalty_dice'],1)

    def test_acceleration_three_locations(self):
        self.assertEqual(c.acceleration_plan(locations=3)['hazard_penalty_dice'],1)

    def test_acceleration_four_locations(self):
        self.assertEqual(c.acceleration_plan(locations=4)['hazard_penalty_dice'],2)

    def test_acceleration_five_locations(self):
        self.assertEqual(c.acceleration_plan(locations=5)['hazard_penalty_dice'],2)

    def test_navigation_assist_reduces_once(self):
        self.assertEqual(c.acceleration_plan(locations=5,navigation_assist_success=True)['hazard_penalty_dice'],1)
        self.assertEqual(c.acceleration_plan(locations=2,navigation_assist_success=True)['hazard_penalty_dice'],0)

    def test_acceleration_invalid(self):
        self.assertEqual(c.acceleration_plan(locations=6)['status'],'BLOCKED')

    def test_acceleration_progress_clear(self):
        r=c.acceleration_progress(declared_locations=4,completed_locations=2,hazard_failed=False)
        self.assertEqual(r['remaining_locations_in_same_action'],2)

    def test_acceleration_progress_failure_stops(self):
        r=c.acceleration_progress(declared_locations=4,completed_locations=2,hazard_failed=True)
        self.assertEqual(r['remaining_locations_in_same_action'],0); self.assertTrue(r['must_pay_new_movement_action_to_continue'])

    def test_acceleration_failure_after_full_move_invalid(self):
        self.assertEqual(c.acceleration_progress(declared_locations=3,completed_locations=3,hazard_failed=True)['status'],'BLOCKED')

    def test_collision_minor_min_zero(self):
        self.assertEqual(c.collision_damage(incident='MINOR',recorded_dice=[1])['damage'],0)

    def test_collision_minor_max_two(self):
        self.assertEqual(c.collision_damage(incident='MINOR',recorded_dice=[3])['damage'],2)

    def test_collision_moderate(self):
        self.assertEqual(c.collision_damage(incident='MODERATE',recorded_dice=[6])['damage'],6)

    def test_collision_severe(self):
        self.assertEqual(c.collision_damage(incident='SEVERE',recorded_dice=[10])['damage'],10)

    def test_collision_mayhem(self):
        self.assertEqual(c.collision_damage(incident='MAYHEM',recorded_dice=[10,9])['damage'],19)

    def test_collision_road_kill(self):
        self.assertEqual(c.collision_damage(incident='ROAD_KILL',recorded_dice=[10,10,10,10,10])['damage'],50)

    def test_collision_invalid_incident(self):
        self.assertEqual(c.collision_damage(incident='NOPE',recorded_dice=[1])['status'],'BLOCKED')

    def test_collision_wrong_dice_count(self):
        self.assertEqual(c.collision_damage(incident='MAYHEM',recorded_dice=[5])['status'],'BLOCKED')

    def test_collision_invalid_die(self):
        self.assertEqual(c.collision_damage(incident='MODERATE',recorded_dice=[7])['status'],'BLOCKED')

    def test_vehicle_impaired_at_half(self):
        r=c.vehicle_state_after_build_damage(starting_build=6,current_build=4,incident_build_damage=1)
        self.assertEqual(r['build'],3); self.assertTrue(r['impaired']); self.assertEqual(r['drive_penalty_dice'],1)

    def test_vehicle_not_impaired_above_half(self):
        self.assertFalse(c.vehicle_state_after_build_damage(starting_build=6,current_build=5,incident_build_damage=1)['impaired'])

    def test_vehicle_complete_wreck_single_incident(self):
        r=c.vehicle_state_after_build_damage(starting_build=5,current_build=5,incident_build_damage=5)
        self.assertTrue(r['complete_wreck_single_incident']); self.assertTrue(r['keeper_survival_gate_required'])

    def test_vehicle_cumulative_zero(self):
        r=c.vehicle_state_after_build_damage(starting_build=5,current_build=2,incident_build_damage=2)
        self.assertTrue(r['undriveable_cumulative_zero']); self.assertFalse(r['complete_wreck_single_incident'])

    def test_vehicle_collision_applies_delay(self):
        r=c.resolve_vehicle_collision(incident='MODERATE',starting_build=6,current_build=6,recorded_vehicle_dice=[2],recorded_delay_d3=3)
        self.assertEqual(r['vehicle_build_damage'],2); self.assertEqual(r['lost_movement_actions'],3)

    def test_vehicle_collision_bad_delay(self):
        self.assertEqual(c.resolve_vehicle_collision(incident='MODERATE',starting_build=6,current_build=6,recorded_vehicle_dice=[2],recorded_delay_d3=4)['status'],'BLOCKED')

    def test_occupant_damage_same_expression(self):
        r=c.resolve_collision_occupant_damage(incident='SEVERE',recorded_dice=[7])
        self.assertEqual(r['hit_point_damage'],7)

    def test_barrier_ram_destroyed(self):
        r=c.barrier_ram(vehicle_build=3,barrier_hp_before=10,recorded_d10=[4,4,4])
        self.assertTrue(r['barrier_destroyed']); self.assertEqual(r['vehicle_self_hit_point_damage'],5)

    def test_barrier_ram_failed_wrecks_vehicle(self):
        r=c.barrier_ram(vehicle_build=2,barrier_hp_before=20,recorded_d10=[3,3])
        self.assertFalse(r['barrier_destroyed']); self.assertTrue(r['vehicle_wrecked'])

    def test_barrier_ram_requires_one_d10_per_build(self):
        self.assertEqual(c.barrier_ram(vehicle_build=3,barrier_hp_before=10,recorded_d10=[5,5])['status'],'BLOCKED')

    def test_vehicle_conflict_attack(self):
        r=c.vehicle_conflict_attack(attacker_build=5,target_build=4,recorded_d10=[10,10,10,10,10])
        self.assertEqual(r['delivered_hit_point_damage'],50); self.assertEqual(r['target_build_loss'],4)
        self.assertEqual(r['attacker_self_hit_point_damage'],25); self.assertEqual(r['attacker_self_build_loss'],2)

    def test_vehicle_conflict_self_build_cap(self):
        r=c.vehicle_conflict_attack(attacker_build=10,target_build=1,recorded_d10=[10]*10)
        self.assertEqual(r['attacker_self_build_loss'],1); self.assertTrue(r['self_build_loss_capped_by_target_original_build'])

    def test_vehicle_maneuver_equal_build(self):
        self.assertEqual(c.vehicle_maneuver_plan(attacker_build=5,target_build=5)['penalty_dice'],0)

    def test_vehicle_maneuver_one_larger(self):
        self.assertEqual(c.vehicle_maneuver_plan(attacker_build=5,target_build=6)['penalty_dice'],1)

    def test_vehicle_maneuver_two_larger(self):
        self.assertEqual(c.vehicle_maneuver_plan(attacker_build=5,target_build=7)['penalty_dice'],2)

    def test_vehicle_maneuver_three_larger_impossible(self):
        self.assertEqual(c.vehicle_maneuver_plan(attacker_build=5,target_build=8)['status'],'BLOCKED')

    def test_vehicle_maneuver_success_default(self):
        r=c.vehicle_maneuver_success(recorded_lost_actions_d3=2)
        self.assertEqual(r['lost_movement_actions'],2); self.assertFalse(r['collision_damage_required'])

    def test_vehicle_maneuver_success_collision(self):
        r=c.vehicle_maneuver_success(recorded_lost_actions_d3=1,collision_incident='SEVERE')
        self.assertTrue(r['collision_damage_required'])

    def test_driver_major_wound_conscious(self):
        r=c.driver_major_wound_control(conscious=True)
        self.assertEqual(r['hazard_difficulty'],'HARD'); self.assertTrue(r['immediate_hazard_roll_required'])

    def test_driver_major_wound_unconscious(self):
        self.assertTrue(c.driver_major_wound_control(conscious=False)['automatic_loss_of_control'])

    def test_ranged_attack_while_moving(self):
        r=c.chase_ranged_attack_plan(moving=True,on_foot=False,movement_actions_available=2)
        self.assertEqual(r['extra_penalty_dice'],1); self.assertEqual(r['movement_actions_spent'],0)

    def test_ranged_attack_stationary_on_foot(self):
        r=c.chase_ranged_attack_plan(moving=False,on_foot=True,movement_actions_available=2)
        self.assertEqual(r['movement_actions_spent'],1); self.assertEqual(r['extra_penalty_dice'],0)

    def test_ranged_attack_stationary_no_action(self):
        self.assertEqual(c.chase_ranged_attack_plan(moving=False,on_foot=True,movement_actions_available=0)['status'],'BLOCKED')

    def test_tire_ignores_non_impaling(self):
        r=c.tire_damage(raw_damage=20,impaling_weapon=False)
        self.assertFalse(r['new_burst']); self.assertTrue(r['ignored_non_impaling'])

    def test_tire_armor_prevents_burst(self):
        r=c.tire_damage(raw_damage=4,impaling_weapon=True)
        self.assertEqual(r['damage_after_armor'],1); self.assertFalse(r['new_burst'])

    def test_tire_bursts_at_two_after_armor(self):
        r=c.tire_damage(raw_damage=5,impaling_weapon=True)
        self.assertTrue(r['new_burst']); self.assertEqual(r['vehicle_build_loss'],1)

    def test_tire_already_burst_no_second_build_loss(self):
        self.assertEqual(c.tire_damage(raw_damage=20,impaling_weapon=True,already_burst=True)['vehicle_build_loss'],0)

    def test_multi_layout_basic(self):
        r=c.multiple_participant_layout(pursuers=[{'id':'P1','mov':8},{'id':'P2','mov':10}],fleeing=[{'id':'F1','mov':9},{'id':'F2','mov':10}])
        self.assertTrue(r['chase_continues']); self.assertEqual(r['positions']['P2'],1); self.assertEqual(r['positions']['F1'],3); self.assertEqual(r['positions']['F2'],4)

    def test_multi_escape_eligible_not_auto_selected(self):
        r=c.multiple_participant_layout(pursuers=[{'id':'P','mov':8}],fleeing=[{'id':'F','mov':9}])
        self.assertEqual(r['escape_eligible'],['F']); self.assertTrue(r['chase_continues']); self.assertFalse(r['automatic_escape_choice_made'])

    def test_multi_escape_by_explicit_choice(self):
        r=c.multiple_participant_layout(pursuers=[{'id':'P','mov':8}],fleeing=[{'id':'F','mov':9}],fleeing_choose_escape_ids=['F'])
        self.assertFalse(r['chase_continues']); self.assertEqual(r['escaped_by_choice'],['F'])

    def test_multi_invalid_escape_choice(self):
        r=c.multiple_participant_layout(pursuers=[{'id':'P','mov':9}],fleeing=[{'id':'F','mov':8}],fleeing_choose_escape_ids=['F'])
        self.assertEqual(r['status'],'BLOCKED')

    def test_multi_slow_pursuer_left_behind(self):
        r=c.multiple_participant_layout(pursuers=[{'id':'P1','mov':6},{'id':'P2','mov':9}],fleeing=[{'id':'F','mov':8}])
        self.assertEqual(r['pursuers_left_behind'],['P1']); self.assertIn('P2',r['active_pursuers'])

    def test_multi_all_pursuers_left_behind(self):
        r=c.multiple_participant_layout(pursuers=[{'id':'P','mov':6}],fleeing=[{'id':'F','mov':8}])
        self.assertFalse(r['chase_continues'])

    def test_multi_duplicate_id_blocked(self):
        r=c.multiple_participant_layout(pursuers=[{'id':'P','mov':8},{'id':'P','mov':9}],fleeing=[{'id':'F','mov':8}])
        self.assertEqual(r['status'],'BLOCKED')

    def test_multi_groups_required(self):
        self.assertEqual(c.multiple_participant_layout(pursuers=[],fleeing=[{'id':'F','mov':8}])['status'],'BLOCKED')

    def test_randomness_never_generated(self):
        self.assertFalse(c.collision_damage(incident='MODERATE',recorded_dice=[3])['randomness_generated'])
        self.assertFalse(c.barrier_ram(vehicle_build=1,barrier_hp_before=1,recorded_d10=[1])['randomness_generated'])


# Extra data-driven checks: each one is a distinct unittest, keeping CI counts visible.
def _add_generated_tests():
    cases=[]
    for locations,assist,expected in [(1,False,0),(2,False,1),(3,False,1),(4,False,2),(5,False,2),(2,True,0),(3,True,0),(4,True,1),(5,True,1)]:
        cases.append(('accel',locations,assist,expected))
    for incident,dice,expected in [
        ('MINOR',[2],1),('MODERATE',[4],4),('SEVERE',[8],8),('MAYHEM',[4,5],9),('ROAD_KILL',[1,2,3,4,5],15)
    ]:
        cases.append(('collision',incident,dice,expected))
    for attacker,target,expected in [(5,3,0),(5,4,0),(5,5,0),(5,6,1),(5,7,2)]:
        cases.append(('maneuver',attacker,target,expected))
    for raw,after,burst in [(0,0,False),(1,0,False),(2,0,False),(3,0,False),(4,1,False),(5,2,True),(6,3,True),(7,4,True),(8,5,True)]:
        cases.append(('tire',raw,after,burst))

    for index,case in enumerate(cases,1):
        def make_test(case):
            def test(self):
                kind=case[0]
                if kind=='accel':
                    _,locations,assist,expected=case
                    self.assertEqual(c.acceleration_plan(locations=locations,navigation_assist_success=assist)['hazard_penalty_dice'],expected)
                elif kind=='collision':
                    _,incident,dice,expected=case
                    self.assertEqual(c.collision_damage(incident=incident,recorded_dice=dice)['damage'],expected)
                elif kind=='maneuver':
                    _,attacker,target,expected=case
                    self.assertEqual(c.vehicle_maneuver_plan(attacker_build=attacker,target_build=target)['penalty_dice'],expected)
                else:
                    _,raw,after,burst=case
                    result=c.tire_damage(raw_damage=raw,impaling_weapon=True)
                    self.assertEqual(result['damage_after_armor'],after); self.assertEqual(result['new_burst'],burst)
            return test
        setattr(ChaseBatch2Tests,f'test_generated_{index:02d}',make_test(case))

_add_generated_tests()


if __name__ == '__main__':
    unittest.main()
