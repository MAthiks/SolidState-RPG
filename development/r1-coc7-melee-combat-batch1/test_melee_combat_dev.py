from __future__ import annotations

import unittest

import melee_combat_dev as melee


class MeleeCombatBatch1Tests(unittest.TestCase):
    def exchange(self, *, a_skill=50, a_roll=30, d_skill=50, d_roll=30, mode='DODGE', a_bonus=0, d_bonus=0, actor_turn=True):
        def digits(roll, bonus):
            units = roll % 10
            tens = roll // 10
            count = 1 + abs(bonus)
            return units, [tens] * count
        au, at = digits(a_roll, a_bonus)
        du, dt = digits(d_roll, d_bonus)
        return melee.resolve_melee_exchange(
            attacker_skill=a_skill,
            attacker_units=au,
            attacker_tens=at,
            defender_skill=d_skill,
            defender_units=du,
            defender_tens=dt,
            defense_mode=mode,
            attacker_net_bonus=a_bonus,
            defender_net_bonus=d_bonus,
            attacker_is_actor_turn=actor_turn,
        )

    def maneuver(self, *, ab=0, db=0, goal_type='DISARM', goal='prendre le couteau', bonus=0):
        return melee.maneuver_plan(attacker_build=ab, defender_build=db, goal_type=goal_type, goal=goal, additional_net_bonus=bonus)

    def test_001_identity(self):
        self.assertEqual(melee.MODULE_ID, 'COC7_MELEE_COMBAT_R1_BATCH1_DEV_V1')
        self.assertEqual(melee.PARENT_FIREARMS_MODULE_ID, 'COC7_COMBAT_FIREARMS_R1_BATCH2_DEV_V1')
        self.assertEqual(melee.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_002_dodge_attacker_higher_hits(self):
        r = self.exchange(a_roll=20, d_roll=30, mode='DODGE')
        self.assertEqual(r['attacker']['level'], 'HARD')
        self.assertEqual(r['defender']['level'], 'REGULAR')
        self.assertEqual(r['outcome'], 'ATTACKER_HITS')

    def test_003_dodge_defender_higher_dodges(self):
        r = self.exchange(a_roll=30, d_roll=20, mode='DODGE')
        self.assertEqual(r['outcome'], 'DODGED')

    def test_004_dodge_tie_defender_wins(self):
        r = self.exchange(a_roll=30, d_roll=30, mode='DODGE')
        self.assertEqual(r['winner'], 'DEFENDER')
        self.assertEqual(r['outcome'], 'DODGED')

    def test_005_dodge_both_fail_no_damage(self):
        r = self.exchange(a_roll=80, d_roll=90, mode='DODGE')
        self.assertEqual(r['winner'], 'NONE')
        self.assertEqual(r['outcome'], 'NO_DAMAGE')

    def test_006_fight_back_attacker_higher_hits(self):
        r = self.exchange(a_roll=20, d_roll=30, mode='FIGHT_BACK')
        self.assertEqual(r['outcome'], 'ATTACKER_HITS')

    def test_007_fight_back_defender_higher_counterhits(self):
        r = self.exchange(a_roll=30, d_roll=20, mode='FIGHT_BACK')
        self.assertEqual(r['winner'], 'DEFENDER')
        self.assertEqual(r['outcome'], 'DEFENDER_COUNTERHITS')

    def test_008_fight_back_tie_attacker_wins(self):
        r = self.exchange(a_roll=30, d_roll=30, mode='FIGHT_BACK')
        self.assertEqual(r['winner'], 'ATTACKER')
        self.assertEqual(r['outcome'], 'ATTACKER_HITS')

    def test_009_fight_back_both_fail_no_damage(self):
        r = self.exchange(a_roll=80, d_roll=90, mode='FIGHT_BACK')
        self.assertEqual(r['outcome'], 'NO_DAMAGE')

    def test_010_invalid_defense_mode_blocks(self):
        self.assertEqual(self.exchange(mode='PARRY_ONLY')['code'], 'DEFENSE_MODE_INVALID')

    def test_011_attacker_extreme_on_actor_turn_is_extreme_damage_eligible(self):
        r = self.exchange(a_skill=50, a_roll=10, d_skill=50, d_roll=30, mode='DODGE', actor_turn=True)
        self.assertTrue(r['extreme_damage_eligible'])

    def test_012_attacker_extreme_when_not_actor_turn_not_extreme_damage(self):
        r = self.exchange(a_skill=50, a_roll=10, d_skill=50, d_roll=30, mode='FIGHT_BACK', actor_turn=False)
        self.assertFalse(r['extreme_damage_eligible'])

    def test_013_defender_counterhit_never_gets_extreme_damage_bonus_here(self):
        r = self.exchange(a_roll=30, d_skill=50, d_roll=10, mode='FIGHT_BACK')
        self.assertEqual(r['winner'], 'DEFENDER')
        self.assertFalse(r['defender_counterhit_extreme_bonus_allowed'])

    def test_014_bonus_die_is_consumed_from_recorded_digits(self):
        r = melee.resolve_melee_exchange(
            attacker_skill=50, attacker_units=5, attacker_tens=[7, 2],
            defender_skill=50, defender_units=0, defender_tens=[3],
            defense_mode='DODGE', attacker_net_bonus=1,
        )
        self.assertEqual(r['attacker']['roll'], 25)
        self.assertEqual(r['outcome'], 'ATTACKER_HITS')

    def test_015_penalty_die_is_consumed_from_recorded_digits(self):
        r = melee.resolve_melee_exchange(
            attacker_skill=50, attacker_units=5, attacker_tens=[2, 7],
            defender_skill=50, defender_units=0, defender_tens=[3],
            defense_mode='DODGE', attacker_net_bonus=-1,
        )
        self.assertEqual(r['attacker']['roll'], 75)
        self.assertEqual(r['outcome'], 'DODGED')

    def test_016_wrong_tens_count_blocks(self):
        r = melee.resolve_melee_exchange(
            attacker_skill=50, attacker_units=5, attacker_tens=[2],
            defender_skill=50, defender_units=0, defender_tens=[3],
            defense_mode='DODGE', attacker_net_bonus=1,
        )
        self.assertEqual(r['code'], 'TENS_DICE_COUNT_INVALID')

    def test_017_maneuver_same_build_no_penalty(self):
        p = self.maneuver(ab=0, db=0)
        self.assertEqual(p['net_bonus'], 0)

    def test_018_maneuver_attacker_bigger_no_penalty(self):
        p = self.maneuver(ab=2, db=0)
        self.assertEqual(p['net_bonus'], 0)

    def test_019_maneuver_one_build_lower_one_penalty(self):
        p = self.maneuver(ab=0, db=1)
        self.assertEqual(p['build_penalty'], -1)

    def test_020_maneuver_two_build_lower_two_penalties(self):
        p = self.maneuver(ab=0, db=2)
        self.assertEqual(p['build_penalty'], -2)

    def test_021_maneuver_three_build_lower_impossible(self):
        p = self.maneuver(ab=0, db=3)
        self.assertEqual(p['code'], 'MANEUVER_IMPOSSIBLE_BUILD_DIFFERENCE')

    def test_022_maneuver_definite_goal_required(self):
        self.assertEqual(self.maneuver(goal='  ')['code'], 'MANEUVER_DEFINITE_GOAL_REQUIRED')

    def test_023_maneuver_goal_type_required(self):
        self.assertEqual(self.maneuver(goal_type='HURT_MORE')['code'], 'MANEUVER_GOAL_TYPE_INVALID')

    def test_024_maneuver_surprise_bonus_can_cancel_build_penalty(self):
        p = self.maneuver(ab=0, db=1, bonus=1)
        self.assertEqual(p['net_bonus'], 0)

    def test_025_maneuver_modifier_overflow_fail_closed(self):
        p = self.maneuver(ab=0, db=2, bonus=-1)
        self.assertEqual(p['code'], 'MANEUVER_MODIFIER_STACK_UNMATERIALIZED')

    def test_026_maneuver_vs_dodge_attacker_higher_succeeds(self):
        p = self.maneuver()
        r = melee.resolve_maneuver(
            plan=p,
            attacker_skill=50, attacker_units=0, attacker_tens=[2],
            defender_skill=50, defender_units=0, defender_tens=[3],
            defense_mode='DODGE',
        )
        self.assertTrue(r['maneuver_success'])
        self.assertEqual(r['outcome'], 'MANEUVER_SUCCEEDS')

    def test_027_maneuver_vs_dodge_tie_target_dodges(self):
        p = self.maneuver()
        r = melee.resolve_maneuver(
            plan=p,
            attacker_skill=50, attacker_units=0, attacker_tens=[3],
            defender_skill=50, defender_units=0, defender_tens=[3],
            defense_mode='DODGE',
        )
        self.assertFalse(r['maneuver_success'])
        self.assertEqual(r['outcome'], 'TARGET_DODGES_MANEUVER')

    def test_028_maneuver_vs_fight_back_tie_succeeds(self):
        p = self.maneuver()
        r = melee.resolve_maneuver(
            plan=p,
            attacker_skill=50, attacker_units=0, attacker_tens=[3],
            defender_skill=50, defender_units=0, defender_tens=[3],
            defense_mode='FIGHT_BACK',
        )
        self.assertTrue(r['maneuver_success'])

    def test_029_maneuver_vs_fight_back_defender_higher_inflicts_damage(self):
        p = self.maneuver()
        r = melee.resolve_maneuver(
            plan=p,
            attacker_skill=50, attacker_units=0, attacker_tens=[3],
            defender_skill=50, defender_units=0, defender_tens=[2],
            defense_mode='FIGHT_BACK',
        )
        self.assertEqual(r['outcome'], 'DEFENDER_INFLICTS_DAMAGE')

    def test_030_defender_counter_maneuver_supported(self):
        p = self.maneuver()
        r = melee.resolve_maneuver(
            plan=p,
            attacker_skill=50, attacker_units=0, attacker_tens=[3],
            defender_skill=50, defender_units=0, defender_tens=[2],
            defense_mode='FIGHT_BACK', defender_counter_is_maneuver=True,
        )
        self.assertEqual(r['outcome'], 'DEFENDER_COUNTER_MANEUVER')

    def test_031_disarm_effect(self):
        self.assertEqual(melee.maneuver_effect_options('DISARM')['type'], 'DISARM_OR_WREST_ITEM')

    def test_032_restrain_effect(self):
        r = melee.maneuver_effect_options('RESTRAIN')
        self.assertEqual(r['type'], 'RESTRAINT')
        self.assertIn('TARGET_SUCCESSFUL_ESCAPE_MANEUVER', r['persists_until'])

    def test_033_knockdown_effect_offers_disadvantage(self):
        r = melee.maneuver_effect_options('KNOCK_DOWN')
        self.assertEqual(r['type'], 'ONGOING_DISADVANTAGE')
        self.assertEqual(len(r['options']), 2)

    def test_034_escape_restraint_effect(self):
        self.assertEqual(melee.maneuver_effect_options('ESCAPE_RESTRAINT')['type'], 'BREAK_RESTRAINT')

    def test_035_keeper_defined_goal_does_not_infer_narrative(self):
        r = melee.maneuver_effect_options('OTHER_KEEPER_DEFINED')
        self.assertTrue(r['narrative_effect_not_inferred'])

    def test_036_outnumbered_first_defense_no_bonus_yet(self):
        self.assertEqual(melee.outnumbered_attack_modifier(defenses_already_used=0)['bonus_die'], 0)

    def test_037_outnumbered_after_first_defense_bonus(self):
        self.assertEqual(melee.outnumbered_attack_modifier(defenses_already_used=1)['bonus_die'], 1)

    def test_038_outnumbered_multiattack_capacity_three(self):
        self.assertEqual(melee.outnumbered_attack_modifier(defenses_already_used=2, defensive_capacity=3)['bonus_die'], 0)
        self.assertEqual(melee.outnumbered_attack_modifier(defenses_already_used=3, defensive_capacity=3)['bonus_die'], 1)

    def test_039_outnumbered_never_applies_to_firearm(self):
        r = melee.outnumbered_attack_modifier(defenses_already_used=5, attack_is_firearm=True)
        self.assertEqual(r['bonus_die'], 0)
        self.assertTrue(r['firearms_excluded'])

    def test_040_outnumbered_invalid_capacity_blocks(self):
        self.assertEqual(melee.outnumbered_attack_modifier(defenses_already_used=0, defensive_capacity=0)['code'], 'OUTNUMBERED_INPUT_INVALID')

    def test_041_surprise_anticipated_allows_defense(self):
        r = melee.surprise_plan(anticipated=True, attack_type='MELEE')
        self.assertTrue(r['defense_allowed'])
        self.assertEqual(r['mode'], 'NORMAL_DEFENDED_ATTACK')

    def test_042_surprise_unanticipated_requires_keeper_choice(self):
        r = melee.surprise_plan(anticipated=False, attack_type='MELEE')
        self.assertEqual(r['code'], 'SURPRISE_KEEPER_CHOICE_REQUIRED')

    def test_043_surprise_melee_auto_success_except_fumble(self):
        r = melee.surprise_plan(anticipated=False, attack_type='MELEE', keeper_choice='AUTO_SUCCESS_EXCEPT_FUMBLE')
        self.assertFalse(r['defense_allowed'])
        self.assertEqual(r['mode'], 'AUTO_SUCCESS_EXCEPT_FUMBLE')

    def test_044_surprise_melee_bonus_die(self):
        r = melee.surprise_plan(anticipated=False, attack_type='MELEE', keeper_choice='BONUS_DIE')
        self.assertEqual(r['net_bonus'], 1)

    def test_045_ranged_surprise_cannot_use_auto_success(self):
        r = melee.surprise_plan(anticipated=False, attack_type='RANGED', keeper_choice='AUTO_SUCCESS_EXCEPT_FUMBLE')
        self.assertEqual(r['code'], 'RANGED_SURPRISE_ROLL_ALWAYS_REQUIRED')

    def test_046_ranged_surprise_bonus_die_still_requires_roll(self):
        r = melee.surprise_plan(anticipated=False, attack_type='RANGED', keeper_choice='BONUS_DIE')
        self.assertTrue(r['roll_required'])
        self.assertEqual(r['net_bonus'], 1)

    def test_047_unopposed_auto_mode_normal_failure_still_hits(self):
        p = melee.surprise_plan(anticipated=False, attack_type='MELEE', keeper_choice='AUTO_SUCCESS_EXCEPT_FUMBLE')
        r = melee.resolve_unopposed_attack(skill_value=20, units=0, tens=[8], plan=p)
        self.assertEqual(r['success_level'], 'FAILURE')
        self.assertTrue(r['hit'])

    def test_048_unopposed_bonus_mode_normal_failure_still_hits_because_no_defense(self):
        p = melee.surprise_plan(anticipated=False, attack_type='MELEE', keeper_choice='BONUS_DIE')
        r = melee.resolve_unopposed_attack(skill_value=20, units=0, tens=[8, 7], plan=p)
        self.assertEqual(r['success_level'], 'FAILURE')
        self.assertTrue(r['hit'])

    def test_049_unopposed_fumble_fails(self):
        p = melee.surprise_plan(anticipated=False, attack_type='MELEE', keeper_choice='AUTO_SUCCESS_EXCEPT_FUMBLE')
        r = melee.resolve_unopposed_attack(skill_value=20, units=0, tens=[0], plan=p)
        self.assertEqual(r['roll'], 100)
        self.assertFalse(r['hit'])

    def test_050_unopposed_requires_unopposed_plan(self):
        p = melee.surprise_plan(anticipated=True, attack_type='MELEE')
        self.assertEqual(melee.resolve_unopposed_attack(skill_value=50, units=0, tens=[3], plan=p)['code'], 'UNOPPOSED_PLAN_REQUIRED')

    def test_051_escape_close_combat_allowed(self):
        r = melee.escape_close_combat(has_escape_route=True, physically_restrained=False)
        self.assertTrue(r['escape_allowed'])
        self.assertTrue(r['uses_action'])

    def test_052_escape_close_combat_blocked_by_restraint(self):
        r = melee.escape_close_combat(has_escape_route=True, physically_restrained=True)
        self.assertFalse(r['escape_allowed'])
        self.assertEqual(r['reason'], 'PHYSICALLY_RESTRAINED')

    def test_053_escape_close_combat_requires_route(self):
        r = melee.escape_close_combat(has_escape_route=False, physically_restrained=False)
        self.assertFalse(r['escape_allowed'])
        self.assertEqual(r['reason'], 'NO_ESCAPE_ROUTE')

    def test_054_unarmed_extreme_maximum_damage(self):
        r = melee.extreme_damage_profile(success_level='EXTREME', on_actor_turn=True, weapon_id=None, damage_bonus_max=4)
        self.assertEqual(r['mode'], 'MAXIMUM_DAMAGE')
        self.assertEqual(r['fixed_damage'], 7)

    def test_055_unarmed_extreme_not_applied_when_fighting_back(self):
        r = melee.extreme_damage_profile(success_level='EXTREME', on_actor_turn=False, weapon_id=None, damage_bonus_max=4)
        self.assertEqual(r['mode'], 'NORMAL_DAMAGE_ROLL')
        self.assertFalse(r['extreme_bonus_applied'])

    def test_056_blackjack_extreme_maximum_damage(self):
        r = melee.extreme_damage_profile(success_level='EXTREME', on_actor_turn=True, weapon_id='BLACKJACK', damage_bonus_max=4)
        self.assertEqual(r['mode'], 'MAXIMUM_DAMAGE')
        self.assertEqual(r['fixed_damage'], 12)

    def test_057_sword_extreme_impale(self):
        r = melee.extreme_damage_profile(success_level='EXTREME', on_actor_turn=True, weapon_id='SWORD_LIGHT', damage_bonus_max=4)
        self.assertEqual(r['mode'], 'IMPALE')
        self.assertEqual(r['fixed_component'], 10)
        self.assertEqual(r['extra_weapon_roll_expression'], '1D6')
        self.assertFalse(r['damage_bonus_rolled_again'])

    def test_058_medium_knife_impale_includes_weapon_constant(self):
        r = melee.extreme_damage_profile(success_level='EXTREME', on_actor_turn=True, weapon_id='KNIFE_MEDIUM', damage_bonus_max=4)
        self.assertEqual(r['fixed_component'], 10)
        self.assertEqual(r['extra_weapon_roll_expression'], '1D4+2')

    def test_059_regular_success_uses_normal_damage(self):
        r = melee.extreme_damage_profile(success_level='REGULAR', on_actor_turn=True, weapon_id='SWORD_LIGHT', damage_bonus_max=4)
        self.assertEqual(r['mode'], 'NORMAL_DAMAGE_ROLL')

    def test_060_complex_damage_expression_fail_closed(self):
        r = melee.extreme_damage_profile(success_level='EXTREME', on_actor_turn=True, weapon_id='BURNING_TORCH', damage_bonus_max=4)
        self.assertEqual(r['code'], 'COMPLEX_DAMAGE_EXPRESSION_UNMATERIALIZED')

    def test_061_unknown_weapon_damage_blocks(self):
        r = melee.extreme_damage_profile(success_level='EXTREME', on_actor_turn=True, weapon_id='NOPE', damage_bonus_max=4)
        self.assertEqual(r['code'], 'WEAPON_UNRESOLVED')

    def test_062_no_pushed_combat_rolls_in_rules_core(self):
        self.assertFalse(melee.core_rules.pushed_roll_allowed('COMBAT'))

    def test_063_no_randomness_exchange(self):
        self.assertFalse(self.exchange()['randomness_generated'])

    def test_064_no_randomness_maneuver(self):
        p = self.maneuver()
        r = melee.resolve_maneuver(
            plan=p,
            attacker_skill=50, attacker_units=0, attacker_tens=[2],
            defender_skill=50, defender_units=0, defender_tens=[3],
            defense_mode='DODGE',
        )
        self.assertFalse(r['randomness_generated'])

    def test_065_parent_firearms_batch2_identity_survives(self):
        self.assertEqual(melee.firearms2.MODULE_ID, 'COC7_COMBAT_FIREARMS_R1_BATCH2_DEV_V1')


if __name__ == '__main__':
    unittest.main()
