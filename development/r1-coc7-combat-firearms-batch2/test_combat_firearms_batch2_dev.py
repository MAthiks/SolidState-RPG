from __future__ import annotations

import unittest

import combat_firearms_batch2_dev as combat


AUTO_WEAPONS = [
    'BERGMANN_MP18_MP28',
    'THOMPSON_SMG',
    'GATLING_1882',
    'BROWNING_AUTO_RIFLE_M1918',
    'BROWNING_M1917A1',
    'BREN_GUN',
    'LEWIS_GUN',
    'VICKERS_303',
]

SHOTGUNS = {
    'SHOTGUN_20GA_2B': [(10, '2D6'), (20, '1D6'), (50, '1D3')],
    'SHOTGUN_16GA_2B': [(10, '2D6+2'), (20, '1D6+1'), (50, '1D4')],
    'SHOTGUN_12GA_2B': [(10, '4D6'), (20, '2D6'), (50, '1D6')],
    'SHOTGUN_12GA_SAWED': [(5, '4D6'), (10, '1D6')],
    'SHOTGUN_10GA_2B': [(10, '4D6+2'), (20, '2D6+1'), (50, '1D4')],
}


class CombatFirearmsBatch2Tests(unittest.TestCase):
    def target(self, *, weapon='THOMPSON_SMG', rounds=4, distance=20, dex=60, target_id='A', **kwargs):
        return combat.make_auto_target(
            weapon_id=weapon,
            allocated_rounds=rounds,
            distance_yards=distance,
            shooter_dex=dex,
            target_id=target_id,
            **kwargs,
        )

    def auto_plan(self, *, weapon='THOMPSON_SMG', skill=40, rounds=4, ammo=20, targets=None, transitions=None):
        if targets is None:
            targets = [self.target(weapon=weapon, rounds=rounds)]
        return combat.full_auto_plan(
            weapon_id=weapon,
            skill_value=skill,
            declared_rounds=rounds,
            available_ammo=ammo,
            targets=targets,
            transition_yards=transitions,
        )

    def test_001_identity(self):
        self.assertEqual(combat.MODULE_ID, 'COC7_COMBAT_FIREARMS_R1_BATCH2_DEV_V1')
        self.assertEqual(combat.PARENT_MODULE_ID, 'COC7_COMBAT_FIREARMS_R1_BATCH1_DEV_V1')
        self.assertEqual(combat.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_002_volley_size_63_is_6(self):
        self.assertEqual(combat.full_auto_volley_size(63)['volley_size'], 6)

    def test_003_volley_minimum_3(self):
        self.assertEqual(combat.full_auto_volley_size(10)['volley_size'], 3)

    def test_004_volley_zero_skill_still_minimum_3(self):
        self.assertEqual(combat.full_auto_volley_size(0)['volley_size'], 3)

    def test_005_invalid_skill_blocks(self):
        self.assertEqual(combat.full_auto_volley_size(101)['code'], 'FIREARM_SKILL_INVALID')

    def test_006_thompson_full_auto_capable(self):
        r = combat.automatic_fire_capability('THOMPSON_SMG')
        self.assertTrue(r['full_auto'])
        self.assertEqual(r['capacity_options'], [20, 30, 50])

    def test_007_revolver_not_full_auto(self):
        self.assertFalse(combat.automatic_fire_capability('REVOLVER_38_OR_9MM')['full_auto'])

    def test_008_unknown_capability_blocks(self):
        self.assertEqual(combat.automatic_fire_capability('NOPE')['code'], 'WEAPON_UNRESOLVED')

    def test_009_target_uses_parent_regular_range(self):
        t = self.target(distance=20)
        self.assertEqual(t['status'], 'RESOLVED')
        self.assertEqual(t['base_difficulty'], 'REGULAR')

    def test_010_target_preserves_point_blank_bonus(self):
        t = self.target(distance=4, dex=60)
        self.assertEqual(t['base_net_bonus'], 1)

    def test_011_target_preserves_cover_penalty(self):
        t = self.target(concealment_fraction=.5)
        self.assertEqual(t['base_net_bonus'], -1)

    def test_012_invalid_target_allocation_blocks(self):
        self.assertEqual(self.target(rounds=0)['code'], 'TARGET_ALLOCATION_INVALID')

    def test_013_non_auto_weapon_plan_blocks(self):
        t = combat.make_auto_target(weapon_id='REVOLVER_38_OR_9MM', allocated_rounds=3, distance_yards=10, shooter_dex=60)
        p = combat.full_auto_plan(weapon_id='REVOLVER_38_OR_9MM', skill_value=60, declared_rounds=3, available_ammo=6, targets=[t])
        self.assertEqual(p['code'], 'WEAPON_NOT_FULL_AUTO_CAPABLE')

    def test_014_declared_rounds_exceed_ammo_blocks(self):
        self.assertEqual(self.auto_plan(rounds=21, ammo=20, targets=[self.target(rounds=21)])['code'], 'DECLARED_ROUNDS_EXCEED_AVAILABLE_AMMO')

    def test_015_available_ammo_exceeds_registered_capacity_blocks(self):
        self.assertEqual(self.auto_plan(ammo=51)['code'], 'AVAILABLE_AMMO_EXCEEDS_REGISTERED_CAPACITY')

    def test_016_allocation_mismatch_blocks(self):
        p = self.auto_plan(rounds=8, targets=[self.target(rounds=4)])
        self.assertEqual(p['code'], 'DECLARED_ROUNDS_ALLOCATION_MISMATCH')

    def test_017_transition_count_blocks(self):
        a = self.target(rounds=4, target_id='A')
        b = self.target(rounds=4, target_id='B')
        p = self.auto_plan(rounds=8, targets=[a, b], transitions=[])
        self.assertEqual(p['code'], 'TARGET_TRANSITION_COUNT_INVALID')

    def test_018_transition_fraction_blocks(self):
        a = self.target(rounds=4, target_id='A')
        b = self.target(rounds=4, target_id='B')
        p = self.auto_plan(rounds=8, targets=[a, b], transitions=[1.5])
        self.assertEqual(p['code'], 'TARGET_TRANSITION_DISTANCE_INVALID')

    def test_019_transition_ammo_overflow_blocks(self):
        a = self.target(rounds=10, target_id='A')
        b = self.target(rounds=10, target_id='B')
        p = self.auto_plan(rounds=20, ammo=20, targets=[a, b], transitions=[1])
        self.assertEqual(p['code'], 'PLANNED_AMMO_WITH_TARGET_TRANSITIONS_EXCEEDS_AVAILABLE')

    def test_020_source_example_skill63_four_volleys(self):
        t = self.target(rounds=24)
        p = self.auto_plan(skill=63, rounds=24, ammo=30, targets=[t])
        self.assertEqual(p['status'], 'RESOLVED')
        self.assertEqual(p['volley_size'], 6)
        self.assertEqual([v['shots'] for v in p['volleys']], [6, 6, 6, 6])
        self.assertEqual([v['net_bonus'] for v in p['volleys']], [0, -1, -2, -2])
        self.assertEqual([v['difficulty'] for v in p['volleys']], ['REGULAR', 'REGULAR', 'REGULAR', 'HARD'])

    def test_021_partial_final_volley(self):
        p = self.auto_plan(skill=63, rounds=14, ammo=20, targets=[self.target(rounds=14)])
        self.assertEqual([v['shots'] for v in p['volleys']], [6, 6, 2])

    def test_022_source_example_three_targets_four_rounds_each(self):
        targets = [
            self.target(rounds=4, target_id='A'),
            self.target(rounds=4, target_id='B'),
            self.target(rounds=4, target_id='C'),
        ]
        p = self.auto_plan(rounds=12, ammo=20, targets=targets, transitions=[3, 3])
        self.assertEqual(p['planned_ammo'], 18)
        self.assertEqual([v['net_bonus'] for v in p['volleys']], [0, -1, -2])
        self.assertEqual([v['transition_waste_before'] for v in p['volleys']], [0, 3, 3])

    def test_023_cover_plus_third_attack_raises_difficulty(self):
        a = self.target(rounds=4, target_id='A')
        b = self.target(rounds=4, target_id='B')
        c = self.target(rounds=4, target_id='C', concealment_fraction=.5)
        p = self.auto_plan(rounds=12, ammo=20, targets=[a, b, c], transitions=[0, 0])
        third = p['volleys'][2]
        self.assertEqual(third['net_bonus'], -2)
        self.assertEqual(third['difficulty'], 'HARD')

    def test_024_fourth_attack_regular_base_becomes_hard(self):
        p = self.auto_plan(skill=40, rounds=16, ammo=20, targets=[self.target(rounds=16)])
        self.assertEqual(p['volleys'][3]['difficulty'], 'HARD')

    def test_025_fifth_attack_regular_base_becomes_extreme(self):
        p = self.auto_plan(skill=40, rounds=20, ammo=20, targets=[self.target(rounds=20)])
        self.assertEqual(p['volleys'][4]['difficulty'], 'EXTREME')

    def test_026_sixth_attack_requires_critical_and_blocks(self):
        cap = combat.registry.resolve_weapon('BREN_GUN')['record']
        self.assertEqual(max(combat._capacity_options(cap)), 100)
        p = self.auto_plan(weapon='BREN_GUN', skill=40, rounds=24, ammo=30, targets=[self.target(weapon='BREN_GUN', rounds=24, distance=50)])
        self.assertEqual(p['code'], 'AUTO_VOLLEY_REQUIRES_CRITICAL_OR_IMPOSSIBLE_DIFFICULTY')

    def test_027_bonus_die_consumed_by_second_volley(self):
        t = self.target(rounds=8, distance=4, dex=60)
        p = self.auto_plan(rounds=8, targets=[t])
        self.assertEqual([v['net_bonus'] for v in p['volleys']], [1, 0])

    def test_028_regular_success_hits_half(self):
        p = self.auto_plan(rounds=4)
        r = combat.resolve_auto_volley(skill_value=60, units=0, tens=[4], volley=p['volleys'][0])
        self.assertTrue(r['hit'])
        self.assertEqual(r['hits'], 2)
        self.assertEqual(r['impale_hits'], 0)

    def test_029_three_shot_regular_success_hits_one(self):
        p = self.auto_plan(skill=30, rounds=3, targets=[self.target(rounds=3)])
        r = combat.resolve_auto_volley(skill_value=60, units=0, tens=[4], volley=p['volleys'][0])
        self.assertEqual(r['hits'], 1)

    def test_030_extreme_success_hits_all_and_half_impale(self):
        p = self.auto_plan(rounds=4)
        r = combat.resolve_auto_volley(skill_value=80, units=5, tens=[0], volley=p['volleys'][0])
        self.assertEqual(r['success_level'], 'EXTREME')
        self.assertEqual(r['hits'], 4)
        self.assertEqual(r['impale_hits'], 2)

    def test_031_extreme_difficulty_extreme_success_no_impale(self):
        t = self.target(rounds=4, distance=70)
        p = self.auto_plan(rounds=4, targets=[t])
        self.assertEqual(p['volleys'][0]['difficulty'], 'EXTREME')
        r = combat.resolve_auto_volley(skill_value=80, units=5, tens=[0], volley=p['volleys'][0])
        self.assertTrue(r['hit'])
        self.assertEqual(r['impale_hits'], 0)

    def test_032_extreme_difficulty_critical_impales(self):
        t = self.target(rounds=4, distance=70)
        p = self.auto_plan(rounds=4, targets=[t])
        r = combat.resolve_auto_volley(skill_value=80, units=1, tens=[0], volley=p['volleys'][0])
        self.assertEqual(r['success_level'], 'CRITICAL')
        self.assertEqual(r['hits'], 4)
        self.assertEqual(r['impale_hits'], 2)

    def test_033_miss_still_fires_volley(self):
        p = self.auto_plan(rounds=4)
        r = combat.resolve_auto_volley(skill_value=40, units=0, tens=[8], volley=p['volleys'][0])
        self.assertFalse(r['hit'])
        self.assertEqual(r['shots_fired'], 4)

    def test_034_thompson_malfunction_at_96(self):
        r = combat.check_malfunction(weapon_id='THOMPSON_SMG', final_roll=96)
        self.assertTrue(r['malfunction'])
        self.assertTrue(r['weapon_does_not_fire'])

    def test_035_thompson_no_malfunction_at_95(self):
        self.assertFalse(combat.check_malfunction(weapon_id='THOMPSON_SMG', final_roll=95)['malfunction'])

    def test_036_bren_malfunction_at_96(self):
        self.assertTrue(combat.check_malfunction(weapon_id='BREN_GUN', final_roll=96)['malfunction'])

    def test_037_bar_threshold_100(self):
        self.assertFalse(combat.check_malfunction(weapon_id='BROWNING_AUTO_RIFLE_M1918', final_roll=99)['malfunction'])
        self.assertTrue(combat.check_malfunction(weapon_id='BROWNING_AUTO_RIFLE_M1918', final_roll=100)['malfunction'])

    def test_038_malfunction_volley_fires_zero(self):
        p = self.auto_plan(rounds=4)
        r = combat.resolve_auto_volley(skill_value=40, units=6, tens=[9], volley=p['volleys'][0])
        self.assertTrue(r['malfunction'])
        self.assertEqual(r['shots_fired'], 0)
        self.assertTrue(r['sequence_stop'])

    def test_039_sequence_stops_on_first_malfunction(self):
        p = self.auto_plan(rounds=8, targets=[self.target(rounds=8)])
        rolls = [{'units': 6, 'tens': [9]}, {'units': 0, 'tens': [2, 1]}]
        r = combat.resolve_full_auto_sequence(plan=p, rolls=rolls)
        self.assertTrue(r['malfunction_stopped_sequence'])
        self.assertEqual(len(r['results']), 1)
        self.assertEqual(r['ammo_expended'], 0)

    def test_040_sequence_second_volley_malfunction_preserves_first_ammo(self):
        p = self.auto_plan(rounds=8, targets=[self.target(rounds=8)])
        rolls = [{'units': 0, 'tens': [2]}, {'units': 6, 'tens': [1, 9]}]
        r = combat.resolve_full_auto_sequence(plan=p, rolls=rolls)
        self.assertTrue(r['malfunction_stopped_sequence'])
        self.assertEqual(r['ammo_expended'], 4)
        self.assertEqual(r['remaining_ammo'], 16)

    def test_041_sequence_transition_waste_counted_before_new_target(self):
        a = self.target(rounds=4, target_id='A')
        b = self.target(rounds=4, target_id='B')
        p = self.auto_plan(rounds=8, ammo=20, targets=[a, b], transitions=[3])
        rolls = [{'units': 0, 'tens': [2]}, {'units': 0, 'tens': [2, 1]}]
        r = combat.resolve_full_auto_sequence(plan=p, rolls=rolls)
        self.assertEqual(r['ammo_expended'], 11)

    def test_042_roll_count_mismatch_blocks(self):
        p = self.auto_plan(rounds=8, targets=[self.target(rounds=8)])
        self.assertEqual(combat.resolve_full_auto_sequence(plan=p, rolls=[{'units': 0, 'tens': [2]}])['code'], 'VOLLEY_ROLL_COUNT_MISMATCH')

    def test_043_no_randomness_generated(self):
        p = self.auto_plan(rounds=4)
        r = combat.resolve_full_auto_sequence(plan=p, rolls=[{'units': 0, 'tens': [2]}])
        self.assertFalse(p['randomness_generated'])
        self.assertFalse(r['randomness_generated'])

    def test_044_parent_attack_malfunction_added(self):
        p = combat.parent.attack_plan(weapon_id='THOMPSON_SMG', distance_yards=20, shooter_dex=60)
        r = combat.resolve_parent_attack_with_malfunction(skill_value=40, units=6, tens=[9], plan=p)
        self.assertTrue(r['malfunction'])
        self.assertFalse(r['hit'])
        self.assertIsNone(r['damage_expression'])

    def test_045_parent_attack_non_malfunction(self):
        p = combat.parent.attack_plan(weapon_id='THOMPSON_SMG', distance_yards=20, shooter_dex=60)
        r = combat.resolve_parent_attack_with_malfunction(skill_value=60, units=0, tens=[4], plan=p)
        self.assertFalse(r['malfunction'])
        self.assertTrue(r['hit'])

    def test_046_reload_two_loose_rounds(self):
        r = combat.reload_action('LOAD_TWO_LOOSE_ROUNDS')
        self.assertEqual((r['combat_rounds'], r['rounds_loaded']), (1, 2))

    def test_047_reload_clip_one_round(self):
        r = combat.reload_action('EXCHANGE_CLIP')
        self.assertEqual(r['combat_rounds'], 1)
        self.assertEqual(r['rounds_loaded'], 'CLIP_CAPACITY')

    def test_048_reload_machine_gun_belt_two_rounds(self):
        self.assertEqual(combat.reload_action('CHANGE_MACHINE_GUN_BELT')['combat_rounds'], 2)

    def test_049_load_one_and_fire_penalty(self):
        r = combat.reload_action('LOAD_ONE_AND_FIRE')
        self.assertTrue(r['fire_same_round'])
        self.assertEqual(r['penalty_die'], 1)

    def test_050_unknown_reload_mode_blocks(self):
        self.assertEqual(combat.reload_action('SPEED_RELOAD')['code'], 'RELOAD_MODE_UNMATERIALIZED')

    def test_051_non_shotgun_band_blocks(self):
        self.assertEqual(combat.shotgun_damage_band(weapon_id='THOMPSON_SMG', distance_yards=10)['code'], 'WEAPON_NOT_SHOTGUN')

    def test_052_shotgun_beyond_listed_bands_blocks(self):
        self.assertEqual(combat.shotgun_damage_band(weapon_id='SHOTGUN_12GA_2B', distance_yards=51)['code'], 'SHOTGUN_BEYOND_LISTED_DAMAGE_BANDS')

    def test_053_shotgun_does_not_infer_attack_difficulty(self):
        r = combat.shotgun_damage_band(weapon_id='SHOTGUN_12GA_2B', distance_yards=10)
        self.assertFalse(r['attack_difficulty_inferred'])
        self.assertFalse(r['impale'])

    def test_054_burst_without_binding_fails_closed(self):
        p = combat.parent.attack_plan(weapon_id='THOMPSON_SMG', distance_yards=20, shooter_dex=60)
        r = combat.burst_plan(weapon_id='THOMPSON_SMG', burst_rounds=3, capability_binding=None, base_plan=p)
        self.assertEqual(r['code'], 'BURST_CAPABILITY_BINDING_REQUIRED')

    def test_055_invalid_burst_round_count_blocks(self):
        p = combat.parent.attack_plan(weapon_id='THOMPSON_SMG', distance_yards=20, shooter_dex=60)
        binding = {'verified': True, 'weapon_id': 'THOMPSON_SMG', 'burst_rounds': 4}
        r = combat.burst_plan(weapon_id='THOMPSON_SMG', burst_rounds=4, capability_binding=binding, base_plan=p)
        self.assertEqual(r['code'], 'BURST_ROUND_COUNT_INVALID')

    def test_056_burst_binding_mismatch_blocks(self):
        p = combat.parent.attack_plan(weapon_id='THOMPSON_SMG', distance_yards=20, shooter_dex=60)
        binding = {'verified': True, 'weapon_id': 'BREN_GUN', 'burst_rounds': 3}
        r = combat.burst_plan(weapon_id='THOMPSON_SMG', burst_rounds=3, capability_binding=binding, base_plan=p)
        self.assertEqual(r['code'], 'BURST_CAPABILITY_BINDING_MISMATCH')

    def test_057_explicit_verified_burst_binding_resolves_generic_rule_only(self):
        p = combat.parent.attack_plan(weapon_id='THOMPSON_SMG', distance_yards=20, shooter_dex=60)
        binding = {
            'verified': True,
            'weapon_id': 'THOMPSON_SMG',
            'burst_rounds': 3,
            'binding_id': 'TEST_FIXTURE_ONLY',
            'source_id': 'EXPLICIT_EXTERNAL_BINDING',
        }
        r = combat.burst_plan(weapon_id='THOMPSON_SMG', burst_rounds=3, capability_binding=binding, base_plan=p)
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertEqual(r['shots'], 3)
        self.assertEqual(r['binding_id'], 'TEST_FIXTURE_ONLY')


def add_auto_capability_tests():
    for wid in AUTO_WEAPONS:
        def test(self, wid=wid):
            r = combat.automatic_fire_capability(wid)
            self.assertEqual(r['status'], 'RESOLVED', wid)
            self.assertTrue(r['full_auto'], wid)
            self.assertTrue(r['capacity_options'], wid)
        setattr(CombatFirearmsBatch2Tests, f'test_auto_capability_{wid.lower()}', test)


def add_shotgun_band_tests():
    for wid, bands in SHOTGUNS.items():
        for idx, (distance, damage) in enumerate(bands):
            def test(self, wid=wid, distance=distance, damage=damage, idx=idx):
                r = combat.shotgun_damage_band(weapon_id=wid, distance_yards=distance)
                self.assertEqual(r['status'], 'RESOLVED', wid)
                self.assertEqual(r['band_index'], idx)
                self.assertEqual(r['damage_expression'], damage)
                self.assertFalse(r['impale'])
            setattr(CombatFirearmsBatch2Tests, f'test_shotgun_{wid.lower()}_band_{idx}', test)


add_auto_capability_tests()
add_shotgun_band_tests()

if __name__ == '__main__':
    unittest.main()
