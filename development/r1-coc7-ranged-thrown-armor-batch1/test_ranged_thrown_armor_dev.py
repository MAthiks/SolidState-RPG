from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import ranged_thrown_armor_dev as rta


def plan(**overrides):
    args = dict(
        weapon_id='ROCK_THROWN',
        attacker_str=50,
        attacker_dex=60,
        distance_feet=30,
        defense_mode='NONE',
        target_dived_cover_successfully=False,
    )
    args.update(overrides)
    return rta.ranged_or_thrown_attack_plan(**args)


class RangedThrownArmorBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(rta.MODULE_ID, 'COC7_RANGED_THROWN_ARMOR_R1_BATCH1_DEV_V1')

    def test_002_parent_combat_round_identity(self):
        self.assertEqual(rta.PARENT_COMBAT_ROUND_MODULE_ID, 'COC7_COMBAT_ROUND_INITIATIVE_R1_BATCH1_DEV_V1')

    def test_003_firearms_parent_identity(self):
        self.assertEqual(rta.FIREARMS_MODULE_ID, 'COC7_COMBAT_FIREARMS_R1_BATCH1_DEV_V1')

    def test_004_melee_parent_identity(self):
        self.assertEqual(rta.MELEE_MODULE_ID, 'COC7_MELEE_COMBAT_R1_BATCH1_DEV_V1')

    def test_005_source_identity(self):
        self.assertEqual(rta.KEEPER_SOURCE_ID, 'COC7_KEEPER')
        self.assertEqual(rta.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_006_bow_profile(self):
        p = rta.weapon_ranged_profile(weapon_id='BOW_AND_ARROWS', attacker_str=50)
        self.assertEqual(p['weapon_class'], 'RANGED_MISSILE')
        self.assertEqual(p['base_range_yards'], 30.0)
        self.assertTrue(p['half_damage_bonus_applies'])

    def test_007_crossbow_profile(self):
        p = rta.weapon_ranged_profile(weapon_id='CROSSBOW', attacker_str=50)
        self.assertEqual(p['weapon_class'], 'RANGED_MISSILE')
        self.assertEqual(p['base_range_yards'], 50.0)
        self.assertFalse(p['half_damage_bonus_applies'])

    def test_008_rock_profile_str_over_5(self):
        p = rta.weapon_ranged_profile(weapon_id='ROCK_THROWN', attacker_str=50)
        self.assertEqual(p['weapon_class'], 'THROWN')
        self.assertEqual(p['base_range_yards'], 10.0)
        self.assertTrue(p['half_damage_bonus_applies'])

    def test_009_spear_thrown_profile(self):
        p = rta.weapon_ranged_profile(weapon_id='SPEAR_THROWN', attacker_str=75)
        self.assertEqual(p['base_range_yards'], 15.0)
        self.assertTrue(p['half_damage_bonus_applies'])

    def test_010_shuriken_profile(self):
        p = rta.weapon_ranged_profile(weapon_id='SHURIKEN', attacker_str=40)
        self.assertEqual(p['base_range_yards'], 8.0)
        self.assertTrue(p['half_damage_bonus_applies'])

    def test_011_unknown_weapon_blocks(self):
        self.assertEqual(rta.weapon_ranged_profile(weapon_id='NOPE', attacker_str=50)['code'], 'WEAPON_UNRESOLVED')

    def test_012_melee_weapon_blocks(self):
        self.assertEqual(rta.weapon_ranged_profile(weapon_id='SWORD_LIGHT', attacker_str=50)['code'], 'WEAPON_NOT_RANGED_MISSILE_OR_THROWN')

    def test_013_invalid_str_blocks(self):
        self.assertEqual(rta.weapon_ranged_profile(weapon_id='ROCK_THROWN', attacker_str=-1)['code'], 'ATTACKER_STR_INVALID')

    def test_014_bool_str_blocks(self):
        self.assertEqual(rta.weapon_ranged_profile(weapon_id='ROCK_THROWN', attacker_str=True)['code'], 'ATTACKER_STR_INVALID')

    def test_015_profile_no_randomness(self):
        self.assertFalse(rta.weapon_ranged_profile(weapon_id='ROCK_THROWN', attacker_str=50)['randomness_generated'])

    def test_016_thrown_regular_range(self):
        self.assertEqual(plan(distance_feet=30)['difficulty'], 'REGULAR')

    def test_017_thrown_hard_range(self):
        self.assertEqual(plan(distance_feet=60)['difficulty'], 'HARD')

    def test_018_thrown_extreme_range(self):
        self.assertEqual(plan(distance_feet=120)['difficulty'], 'EXTREME')

    def test_019_thrown_beyond_four_times_blocks(self):
        self.assertEqual(plan(distance_feet=150)['code'], 'BEYOND_FOUR_TIMES_BASE_RANGE')

    def test_020_bow_regular_range(self):
        p = plan(weapon_id='BOW_AND_ARROWS', distance_feet=90)
        self.assertEqual(p['difficulty'], 'REGULAR')
        self.assertEqual(p['weapon_class'], 'RANGED_MISSILE')

    def test_021_bow_hard_range(self):
        self.assertEqual(plan(weapon_id='BOW_AND_ARROWS', distance_feet=180)['difficulty'], 'HARD')

    def test_022_bow_extreme_range(self):
        self.assertEqual(plan(weapon_id='BOW_AND_ARROWS', distance_feet=360)['difficulty'], 'EXTREME')

    def test_023_crossbow_regular_range(self):
        self.assertEqual(plan(weapon_id='CROSSBOW', distance_feet=150)['difficulty'], 'REGULAR')

    def test_024_invalid_distance_blocks(self):
        self.assertEqual(plan(distance_feet=-1)['code'], 'DISTANCE_INVALID')

    def test_025_bool_distance_blocks(self):
        self.assertEqual(plan(distance_feet=True)['code'], 'DISTANCE_INVALID')

    def test_026_invalid_dex_blocks(self):
        self.assertEqual(plan(attacker_dex=101)['code'], 'ATTACKER_DEX_INVALID')

    def test_027_invalid_defense_mode_blocks(self):
        self.assertEqual(plan(defense_mode='PARRY')['code'], 'DEFENSE_MODE_INVALID')

    def test_028_thrown_dodge_is_routed(self):
        p = plan(defense_mode='DODGE')
        self.assertEqual(p['opposed_route']['engine_module_id'], rta.MELEE_MODULE_ID)
        self.assertEqual(p['opposed_route']['defense_mode'], 'DODGE')

    def test_029_missile_dodge_blocks(self):
        self.assertEqual(plan(weapon_id='BOW_AND_ARROWS', defense_mode='DODGE')['code'], 'DODGE_OPPOSITION_ONLY_MATERIALIZED_FOR_THROWN_WEAPON')

    def test_030_fight_back_exact_dex_over_5_allowed(self):
        p = plan(distance_feet=12, defense_mode='FIGHT_BACK', attacker_dex=60)
        self.assertEqual(p['status'], 'RESOLVED')
        self.assertEqual(p['fight_back_limit_feet'], 12.0)

    def test_031_fight_back_beyond_dex_over_5_blocks(self):
        self.assertEqual(plan(distance_feet=13, defense_mode='FIGHT_BACK', attacker_dex=60)['code'], 'FIGHT_BACK_OUTSIDE_DEX_OVER_5_FEET')

    def test_032_bow_close_fight_back_routed(self):
        p = plan(weapon_id='BOW_AND_ARROWS', distance_feet=10, defense_mode='FIGHT_BACK', attacker_dex=60)
        self.assertEqual(p['opposed_route']['defense_mode'], 'FIGHT_BACK')

    def test_033_bow_far_fight_back_blocks(self):
        self.assertEqual(plan(weapon_id='BOW_AND_ARROWS', distance_feet=13, defense_mode='FIGHT_BACK', attacker_dex=60)['code'], 'FIGHT_BACK_OUTSIDE_DEX_OVER_5_FEET')

    def test_034_bow_reuses_firearm_style_plan(self):
        p = plan(weapon_id='BOW_AND_ARROWS', distance_feet=90)
        self.assertEqual(p['firearm_style_plan']['status'], 'RESOLVED')
        self.assertEqual(p['firearm_style_plan']['module_id'], rta.FIREARMS_MODULE_ID)

    def test_035_crossbow_reuses_firearm_style_plan(self):
        p = plan(weapon_id='CROSSBOW', distance_feet=150)
        self.assertEqual(p['firearm_style_plan']['status'], 'RESOLVED')

    def test_036_missile_dive_for_cover_reuses_firearms_modifier(self):
        p = plan(weapon_id='BOW_AND_ARROWS', distance_feet=90, target_dived_cover_successfully=True)
        ids = [x['id'] for x in p['firearm_style_plan']['modifiers']]
        self.assertIn('DIVE_FOR_COVER', ids)

    def test_037_thrown_dive_for_cover_route_unmaterialized(self):
        self.assertEqual(plan(target_dived_cover_successfully=True)['code'], 'DIVE_FOR_COVER_ROUTING_NOT_MATERIALIZED_FOR_THROWN_BATCH1')

    def test_038_dive_flag_must_be_boolean(self):
        self.assertEqual(plan(target_dived_cover_successfully=1)['code'], 'DIVE_FOR_COVER_FLAG_INVALID')

    def test_039_no_automatic_defense_selection(self):
        self.assertFalse(plan()['automatic_target_defense_selection'])

    def test_040_plan_no_randomness(self):
        self.assertFalse(plan()['randomness_generated'])

    def test_041_bow_half_db_flag_in_plan(self):
        self.assertTrue(plan(weapon_id='BOW_AND_ARROWS', distance_feet=90)['half_damage_bonus_applies'])

    def test_042_crossbow_no_half_db_flag_in_plan(self):
        self.assertFalse(plan(weapon_id='CROSSBOW', distance_feet=150)['half_damage_bonus_applies'])

    def test_043_thrown_half_db_flag_in_plan(self):
        self.assertTrue(plan()['half_damage_bonus_applies'])

    def test_044_resolve_bow_hit_reuses_firearm_engine(self):
        p = plan(weapon_id='BOW_AND_ARROWS', distance_feet=90)
        r = rta.resolve_ranged_missile_attack(plan=p, skill_value=50, units=0, tens=[2])
        self.assertTrue(r['hit'])
        self.assertEqual(r['roll'], 20)

    def test_045_resolve_bow_miss(self):
        p = plan(weapon_id='BOW_AND_ARROWS', distance_feet=90)
        r = rta.resolve_ranged_missile_attack(plan=p, skill_value=50, units=0, tens=[8])
        self.assertFalse(r['hit'])

    def test_046_resolve_crossbow_hit(self):
        p = plan(weapon_id='CROSSBOW', distance_feet=150)
        r = rta.resolve_ranged_missile_attack(plan=p, skill_value=50, units=5, tens=[2])
        self.assertTrue(r['hit'])
        self.assertFalse(r['half_damage_bonus_applies'])

    def test_047_missile_resolver_rejects_thrown_plan(self):
        self.assertEqual(rta.resolve_ranged_missile_attack(plan=plan(), skill_value=50, units=0, tens=[2])['code'], 'RANGED_MISSILE_PLAN_REQUIRED')

    def test_048_opposed_missile_resolution_fails_closed(self):
        p = plan(weapon_id='BOW_AND_ARROWS', distance_feet=10, defense_mode='FIGHT_BACK')
        self.assertEqual(rta.resolve_ranged_missile_attack(plan=p, skill_value=50, units=0, tens=[2])['code'], 'OPPOSED_RANGED_RESOLUTION_UNMATERIALIZED_BATCH1')

    def test_049_unopposed_thrown_regular_hit(self):
        r = rta.resolve_unopposed_thrown_attack(plan=plan(), skill_value=50, roll=30)
        self.assertTrue(r['hit'])
        self.assertEqual(r['difficulty'], 'REGULAR')

    def test_050_unopposed_thrown_regular_miss(self):
        r = rta.resolve_unopposed_thrown_attack(plan=plan(), skill_value=50, roll=70)
        self.assertFalse(r['hit'])

    def test_051_unopposed_thrown_hard_requires_hard(self):
        p = plan(distance_feet=60)
        self.assertFalse(rta.resolve_unopposed_thrown_attack(plan=p, skill_value=50, roll=30)['hit'])
        self.assertTrue(rta.resolve_unopposed_thrown_attack(plan=p, skill_value=50, roll=25)['hit'])

    def test_052_unopposed_thrown_extreme_requires_extreme(self):
        p = plan(distance_feet=120)
        self.assertFalse(rta.resolve_unopposed_thrown_attack(plan=p, skill_value=50, roll=11)['hit'])
        self.assertTrue(rta.resolve_unopposed_thrown_attack(plan=p, skill_value=50, roll=10)['hit'])

    def test_053_opposed_thrown_resolution_fails_closed(self):
        p = plan(defense_mode='DODGE')
        self.assertEqual(rta.resolve_unopposed_thrown_attack(plan=p, skill_value=50, roll=20)['code'], 'OPPOSED_THROWN_RESOLUTION_UNMATERIALIZED_BATCH1')

    def test_054_thrown_roll_input_invalid(self):
        self.assertEqual(rta.resolve_unopposed_thrown_attack(plan=plan(), skill_value=50, roll=0)['code'], 'THROWN_ROLL_INPUT_INVALID')

    def test_055_thrown_resolution_no_randomness(self):
        self.assertFalse(rta.resolve_unopposed_thrown_attack(plan=plan(), skill_value=50, roll=20)['randomness_generated'])

    def test_056_armor_subtracts_points(self):
        r = rta.apply_armor(incoming_damage=10, armor_points=3, damage_category='PHYSICAL', attack_passes_through_armor=True)
        self.assertEqual(r['armor_reduction'], 3)
        self.assertEqual(r['final_damage'], 7)

    def test_057_armor_never_below_zero(self):
        r = rta.apply_armor(incoming_damage=4, armor_points=10, damage_category='PHYSICAL', attack_passes_through_armor=True)
        self.assertEqual(r['final_damage'], 0)
        self.assertEqual(r['armor_reduction'], 4)

    def test_058_zero_armor(self):
        r = rta.apply_armor(incoming_damage=10, armor_points=0, damage_category='PHYSICAL', attack_passes_through_armor=True)
        self.assertEqual(r['final_damage'], 10)

    def test_059_attack_not_through_armor_no_reduction(self):
        r = rta.apply_armor(incoming_damage=10, armor_points=5, damage_category='PHYSICAL', attack_passes_through_armor=False)
        self.assertEqual(r['final_damage'], 10)

    def test_060_magical_damage_ignores_armor(self):
        r = rta.apply_armor(incoming_damage=10, armor_points=5, damage_category='MAGICAL', attack_passes_through_armor=True)
        self.assertEqual(r['final_damage'], 10)
        self.assertEqual(r['reason'], 'SOURCE_EXPLICIT_ARMOR_EXCLUSION')

    def test_061_poison_damage_ignores_armor(self):
        self.assertEqual(rta.apply_armor(incoming_damage=10, armor_points=5, damage_category='POISON', attack_passes_through_armor=True)['final_damage'], 10)

    def test_062_drowning_damage_ignores_armor(self):
        self.assertEqual(rta.apply_armor(incoming_damage=10, armor_points=5, damage_category='DROWNING', attack_passes_through_armor=True)['final_damage'], 10)

    def test_063_unknown_damage_category_fails_closed(self):
        self.assertEqual(rta.apply_armor(incoming_damage=10, armor_points=5, damage_category='FIRE', attack_passes_through_armor=True)['code'], 'DAMAGE_CATEGORY_UNMATERIALIZED_FOR_ARMOR')

    def test_064_negative_armor_blocks(self):
        self.assertEqual(rta.apply_armor(incoming_damage=10, armor_points=-1, damage_category='PHYSICAL', attack_passes_through_armor=True)['code'], 'ARMOR_NUMERIC_INPUT_INVALID')

    def test_065_negative_damage_blocks(self):
        self.assertEqual(rta.apply_armor(incoming_damage=-1, armor_points=2, damage_category='PHYSICAL', attack_passes_through_armor=True)['code'], 'ARMOR_NUMERIC_INPUT_INVALID')

    def test_066_bool_damage_blocks(self):
        self.assertEqual(rta.apply_armor(incoming_damage=True, armor_points=2, damage_category='PHYSICAL', attack_passes_through_armor=True)['code'], 'ARMOR_NUMERIC_INPUT_INVALID')

    def test_067_path_flag_must_be_boolean(self):
        self.assertEqual(rta.apply_armor(incoming_damage=10, armor_points=2, damage_category='PHYSICAL', attack_passes_through_armor=1)['code'], 'ARMOR_PATH_FLAG_INVALID')

    def test_068_category_normalizes(self):
        self.assertEqual(rta.apply_armor(incoming_damage=10, armor_points=2, damage_category=' physical ', attack_passes_through_armor=True)['damage_category'], 'PHYSICAL')

    def test_069_armor_no_automatic_selection(self):
        self.assertFalse(rta.apply_armor(incoming_damage=10, armor_points=2, damage_category='PHYSICAL', attack_passes_through_armor=True)['automatic_armor_selection'])

    def test_070_armor_no_randomness(self):
        self.assertFalse(rta.apply_armor(incoming_damage=10, armor_points=2, damage_category='PHYSICAL', attack_passes_through_armor=True)['randomness_generated'])


def _make_generated_armor_test(damage: int):
    def test(self):
        r = rta.apply_armor(
            incoming_damage=damage,
            armor_points=3,
            damage_category='PHYSICAL',
            attack_passes_through_armor=True,
        )
        self.assertEqual(r['final_damage'], max(0, damage - 3))
        self.assertEqual(r['armor_reduction'], min(damage, 3))
    return test


for _i in range(1, 11):
    setattr(RangedThrownArmorBatch1Tests, f'test_generated_armor_{_i:02d}', _make_generated_armor_test(_i))


if __name__ == '__main__':
    unittest.main()
