from __future__ import annotations

import unittest

import combat_firearms_dev as combat


class CombatFirearmsBatch1Tests(unittest.TestCase):
    def plan(self, weapon='REVOLVER_38_OR_9MM', distance=10, dex=60, **kwargs):
        return combat.attack_plan(weapon_id=weapon, distance_yards=distance, shooter_dex=dex, **kwargs)

    def test_001_identity(self):
        self.assertEqual(combat.MODULE_ID, 'COC7_COMBAT_FIREARMS_R1_BATCH1_DEV_V1')
        self.assertEqual(combat.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_002_parent_registry(self):
        self.assertEqual(combat.PARENT_REGISTRY_ID, 'COC7_RECOVERY_EQUIPMENT_WEAPONS_R1_BATCH1_DEV_V1')

    def test_003_regular_range(self):
        p=self.plan(distance=15)
        self.assertEqual(p['status'],'RESOLVED')
        self.assertEqual(p['difficulty'],'REGULAR')

    def test_004_hard_range(self):
        self.assertEqual(self.plan(distance=30)['difficulty'],'HARD')

    def test_005_extreme_range(self):
        self.assertEqual(self.plan(distance=60)['difficulty'],'EXTREME')

    def test_006_beyond_four_times_blocks(self):
        self.assertEqual(self.plan(distance=61)['code'],'BEYOND_FOUR_TIMES_BASE_RANGE_BATCH1')

    def test_007_point_blank_threshold(self):
        p=self.plan(distance=4,dex=60)
        self.assertTrue(p['point_blank'])
        self.assertEqual(p['net_bonus'],1)

    def test_008_beyond_point_blank(self):
        p=self.plan(distance=4.1,dex=60)
        self.assertFalse(p['point_blank'])
        self.assertEqual(p['net_bonus'],0)

    def test_009_aim_bonus(self):
        self.assertEqual(self.plan(aimed_prior_round=True)['net_bonus'],1)

    def test_010_broken_aim_no_bonus(self):
        self.assertEqual(self.plan(aimed_prior_round=True,aim_broken_by_move_or_damage=True)['net_bonus'],0)

    def test_011_dive_cover_penalty(self):
        self.assertEqual(self.plan(target_dived_cover_successfully=True)['net_bonus'],-1)

    def test_012_half_concealment_penalty(self):
        self.assertEqual(self.plan(concealment_fraction=.5)['net_bonus'],-1)

    def test_013_less_than_half_concealment_no_penalty(self):
        self.assertEqual(self.plan(concealment_fraction=.49)['net_bonus'],0)

    def test_014_fast_target_penalty(self):
        self.assertEqual(self.plan(target_mov=8,target_full_speed=True)['net_bonus'],-1)

    def test_015_mov_7_not_fast_target_modifier(self):
        self.assertEqual(self.plan(target_mov=7,target_full_speed=True)['net_bonus'],0)

    def test_016_not_full_speed_no_fast_modifier(self):
        self.assertEqual(self.plan(target_mov=9,target_full_speed=False)['net_bonus'],0)

    def test_017_small_target_penalty(self):
        self.assertEqual(self.plan(target_build=-2)['net_bonus'],-1)

    def test_018_large_target_bonus(self):
        self.assertEqual(self.plan(target_build=4)['net_bonus'],1)

    def test_019_normal_build_no_modifier(self):
        self.assertEqual(self.plan(target_build=0)['net_bonus'],0)

    def test_020_melee_penalty(self):
        self.assertEqual(self.plan(firing_into_melee=True)['net_bonus'],-1)

    def test_021_bonus_penalty_cancel(self):
        p=self.plan(distance=4,dex=60,concealment_fraction=.5)
        self.assertEqual(p['net_bonus'],0)

    def test_022_two_bonus_dice_supported(self):
        p=self.plan(distance=4,dex=60,aimed_prior_round=True)
        self.assertEqual(p['net_bonus'],2)

    def test_023_two_penalty_dice_supported(self):
        p=self.plan(concealment_fraction=.5,firing_into_melee=True)
        self.assertEqual(p['net_bonus'],-2)

    def test_024_three_penalty_stack_blocks(self):
        p=self.plan(concealment_fraction=.5,firing_into_melee=True,target_build=-2)
        self.assertEqual(p['code'],'MODIFIER_STACK_ABOVE_TWO_UNMATERIALIZED_BATCH1')

    def test_025_handgun_two_shots_penalty(self):
        p=self.plan(shot_count=2)
        self.assertEqual(p['status'],'RESOLVED')
        self.assertEqual(p['net_bonus'],-1)

    def test_026_handgun_three_shots_penalty(self):
        p=self.plan(shot_count=3)
        self.assertEqual(p['status'],'RESOLVED')
        self.assertEqual(p['net_bonus'],-1)

    def test_027_non_handgun_multi_shot_blocks(self):
        p=self.plan(weapon='THOMPSON_SMG',shot_count=2)
        self.assertEqual(p['code'],'MULTIPLE_SHOTS_UNMATERIALIZED_FOR_WEAPON_BATCH1')

    def test_028_simple_smg_single_shot_resolves(self):
        p=self.plan(weapon='THOMPSON_SMG',distance=20)
        self.assertEqual(p['status'],'RESOLVED')
        self.assertEqual(p['difficulty'],'REGULAR')

    def test_029_shotgun_multiband_range_blocks(self):
        p=self.plan(weapon='SHOTGUN_12GA_2B',distance=10)
        self.assertEqual(p['code'],'WEAPON_RANGE_FORM_UNMATERIALIZED_BATCH1')

    def test_030_throw_range_blocks(self):
        p=self.plan(weapon='MOLOTOV_COCKTAIL',distance=5)
        self.assertEqual(p['code'],'WEAPON_RANGE_FORM_UNMATERIALIZED_BATCH1')

    def test_031_unknown_weapon_blocks(self):
        self.assertEqual(self.plan(weapon='NOT_A_WEAPON')['code'],'WEAPON_UNRESOLVED')

    def test_032_invalid_distance_blocks(self):
        self.assertEqual(self.plan(distance=-1)['code'],'DISTANCE_INVALID')

    def test_033_invalid_dex_blocks(self):
        self.assertEqual(self.plan(dex=101)['code'],'SHOOTER_DEX_INVALID')

    def test_034_invalid_concealment_blocks(self):
        self.assertEqual(self.plan(concealment_fraction=1.1)['code'],'CONCEALMENT_INVALID')

    def test_035_invalid_build_blocks(self):
        self.assertEqual(self.plan(target_build=-3)['code'],'TARGET_BUILD_INVALID')

    def test_036_readied_firearm_dex_plus_50(self):
        r=combat.firearm_dex_order(55,firearm_readied=True)
        self.assertEqual(r['dex_order'],105)

    def test_037_unreadied_firearm_normal_dex(self):
        r=combat.firearm_dex_order(55,firearm_readied=False)
        self.assertEqual(r['dex_order'],55)

    def test_038_regular_hit(self):
        p=self.plan(distance=10)
        r=combat.resolve_attack(skill_value=60,units=0,tens=[4],plan=p)
        self.assertTrue(r['hit'])
        self.assertEqual(r['success_level'],'REGULAR')

    def test_039_regular_miss(self):
        p=self.plan(distance=10)
        r=combat.resolve_attack(skill_value=60,units=0,tens=[7],plan=p)
        self.assertFalse(r['hit'])
        self.assertIsNone(r['damage_expression'])

    def test_040_hard_range_requires_hard(self):
        p=self.plan(distance=20)
        r=combat.resolve_attack(skill_value=60,units=0,tens=[4],plan=p)
        self.assertFalse(r['hit'])
        self.assertEqual(r['success_level'],'REGULAR')

    def test_041_hard_range_hard_hit(self):
        p=self.plan(distance=20)
        r=combat.resolve_attack(skill_value=60,units=0,tens=[3],plan=p)
        self.assertTrue(r['hit'])
        self.assertEqual(r['success_level'],'HARD')

    def test_042_bonus_die_uses_best_tens(self):
        p=self.plan(distance=4,dex=60)
        r=combat.resolve_attack(skill_value=50,units=5,tens=[7,2],plan=p)
        self.assertEqual(r['roll'],25)
        self.assertTrue(r['hit'])

    def test_043_penalty_die_uses_worst_tens(self):
        p=self.plan(concealment_fraction=.5)
        r=combat.resolve_attack(skill_value=50,units=5,tens=[2,7],plan=p)
        self.assertEqual(r['roll'],75)
        self.assertFalse(r['hit'])

    def test_044_two_bonus_requires_three_tens(self):
        p=self.plan(distance=4,dex=60,aimed_prior_round=True)
        r=combat.resolve_attack(skill_value=50,units=5,tens=[7,4,1],plan=p)
        self.assertEqual(r['roll'],15)

    def test_045_wrong_tens_count_blocks(self):
        p=self.plan(distance=4,dex=60)
        r=combat.resolve_attack(skill_value=50,units=5,tens=[2],plan=p)
        self.assertEqual(r['code'],'TENS_DICE_COUNT_INVALID')

    def test_046_impale_at_regular_range_on_extreme_result(self):
        p=self.plan(distance=10)
        r=combat.resolve_attack(skill_value=80,units=5,tens=[0],plan=p)
        self.assertTrue(r['hit'])
        self.assertTrue(r['impale'])

    def test_047_no_impale_at_very_long_without_critical(self):
        p=self.plan(distance=50)
        r=combat.resolve_attack(skill_value=80,units=5,tens=[0],plan=p)
        self.assertTrue(r['hit'])
        self.assertEqual(r['success_level'],'EXTREME')
        self.assertFalse(r['impale'])

    def test_048_critical_impales_at_very_long(self):
        p=self.plan(distance=50)
        r=combat.resolve_attack(skill_value=80,units=1,tens=[0],plan=p)
        self.assertTrue(r['hit'])
        self.assertEqual(r['success_level'],'CRITICAL')
        self.assertTrue(r['impale'])

    def test_049_non_impale_weapon_never_impales(self):
        p=self.plan(weapon='FLAMETHROWER',distance=20)
        r=combat.resolve_attack(skill_value=80,units=5,tens=[0],plan=p)
        self.assertTrue(r['hit'])
        self.assertFalse(r['impale'])

    def test_050_full_auto_explicitly_fail_closed(self):
        r=combat.unsupported_full_auto(weapon_id='THOMPSON_SMG')
        self.assertEqual(r['code'],'FULL_AUTO_UNMATERIALIZED_BATCH1')

    def test_051_no_randomness_generated(self):
        p=self.plan()
        r=combat.resolve_attack(skill_value=60,units=0,tens=[3],plan=p)
        self.assertFalse(r['randomness_generated'])

    def test_052_damage_expression_from_weapon_only_on_hit(self):
        p=self.plan(weapon='LEE_ENFIELD_303',distance=50)
        r=combat.resolve_attack(skill_value=80,units=0,tens=[3],plan=p)
        self.assertTrue(r['hit'])
        self.assertEqual(r['damage_expression'],'2D6+4')

    def test_053_attack_plan_carries_source_hash(self):
        p=self.plan()
        self.assertEqual(p['keeper_source_sha256'],combat.KEEPER_SHA256)

    def test_054_boolean_flag_validation(self):
        p=self.plan(aimed_prior_round=1)
        self.assertEqual(p['code'],'MODIFIER_FLAG_INVALID')

    def test_055_shot_count_zero_blocks(self):
        p=self.plan(shot_count=0)
        self.assertEqual(p['code'],'SHOT_COUNT_UNSUPPORTED_BATCH1')


if __name__ == '__main__':
    unittest.main()
