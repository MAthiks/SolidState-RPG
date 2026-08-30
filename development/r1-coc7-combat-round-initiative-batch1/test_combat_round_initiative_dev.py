from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import combat_round_initiative_dev as combat_round


def c(
    actor_id='A', dex=60, combat_skill=40, role='INVESTIGATOR',
    action_kind='FIGHTING_ATTACK', firearm_readied=False, attacks_on_turn=1,
):
    return {
        'actor_id': actor_id,
        'dex': dex,
        'combat_skill': combat_skill,
        'role': role,
        'action_kind': action_kind,
        'firearm_readied': firearm_readied,
        'attacks_on_turn': attacks_on_turn,
    }


class CombatRoundInitiativeBatch1Tests(unittest.TestCase):
    def test_001_identity(self):
        self.assertEqual(combat_round.MODULE_ID, 'COC7_COMBAT_ROUND_INITIATIVE_R1_BATCH1_DEV_V1')

    def test_002_parent_luck_identity(self):
        self.assertEqual(combat_round.PARENT_LUCK_MODULE_ID, 'COC7_LUCK_SPENDING_R1_BATCH1_DEV_V1')

    def test_003_firearms_parent_identity(self):
        self.assertEqual(combat_round.FIREARMS_MODULE_ID, 'COC7_COMBAT_FIREARMS_R1_BATCH1_DEV_V1')

    def test_004_source_identity(self):
        self.assertEqual(combat_round.KEEPER_SOURCE_ID, 'COC7_KEEPER')
        self.assertEqual(combat_round.KEEPER_SHA256, '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779')

    def test_005_combatants_required(self):
        self.assertEqual(combat_round.build_initiative_order(combatants=[])['code'], 'COMBATANTS_REQUIRED')

    def test_006_highest_dex_first(self):
        r = combat_round.build_initiative_order(combatants=[c('A', 40, 60), c('B', 80, 20)])
        self.assertEqual([x['actor_id'] for x in r['order']], ['B', 'A'])

    def test_007_dex_tie_higher_combat_skill_first(self):
        r = combat_round.build_initiative_order(combatants=[c('A', 60, 30), c('B', 60, 70)])
        self.assertEqual([x['actor_id'] for x in r['order']], ['B', 'A'])

    def test_008_exact_initiative_tie_fails_closed(self):
        r = combat_round.build_initiative_order(combatants=[c('A', 60, 40), c('B', 60, 40)])
        self.assertEqual(r['code'], 'INITIATIVE_EXACT_TIE_KEEPER_RESOLUTION_REQUIRED')

    def test_009_readied_firearm_reuses_dex_plus_50(self):
        r = combat_round.build_initiative_order(combatants=[
            c('A', 55, 40, action_kind='FIREARMS_ATTACK', firearm_readied=True),
        ])
        self.assertEqual(r['order'][0]['dex_order_score'], 105)
        self.assertEqual(r['order'][0]['readied_firearm_bonus'], 50)

    def test_010_unreadied_firearm_uses_raw_dex(self):
        r = combat_round.build_initiative_order(combatants=[
            c('A', 55, 40, action_kind='FIREARMS_ATTACK', firearm_readied=False),
        ])
        self.assertEqual(r['order'][0]['dex_order_score'], 55)
        self.assertEqual(r['order'][0]['readied_firearm_bonus'], 0)

    def test_011_readied_firearm_can_outorder_higher_raw_dex(self):
        r = combat_round.build_initiative_order(combatants=[
            c('Shooter', 40, 30, action_kind='FIREARMS_ATTACK', firearm_readied=True),
            c('Brawler', 80, 70),
        ])
        self.assertEqual(r['order'][0]['actor_id'], 'Shooter')

    def test_012_readied_flag_on_nonfirearms_action_blocks(self):
        r = combat_round.build_initiative_order(combatants=[c(firearm_readied=True)])
        self.assertEqual(r['code'], 'READIED_FIREARM_BONUS_ONLY_APPLIES_TO_FIREARMS_ATTACK')

    def test_013_readied_flag_must_be_boolean(self):
        r = combat_round.build_initiative_order(combatants=[c(firearm_readied=1)])
        self.assertEqual(r['code'], 'FIREARM_READIED_FLAG_INVALID')

    def test_014_duplicate_actor_blocks(self):
        r = combat_round.build_initiative_order(combatants=[c('A', 70), c('A', 50)])
        self.assertEqual(r['code'], 'DUPLICATE_ACTOR_ID')

    def test_015_invalid_dex_blocks(self):
        r = combat_round.build_initiative_order(combatants=[c(dex=101)])
        self.assertEqual(r['code'], 'DEX_INVALID')

    def test_016_bool_dex_blocks(self):
        r = combat_round.build_initiative_order(combatants=[c(dex=True)])
        self.assertEqual(r['code'], 'DEX_INVALID')

    def test_017_invalid_combat_skill_blocks(self):
        r = combat_round.build_initiative_order(combatants=[c(combat_skill=-1)])
        self.assertEqual(r['code'], 'COMBAT_SKILL_INVALID')

    def test_018_invalid_role_blocks(self):
        r = combat_round.build_initiative_order(combatants=[c(role='ALLY')])
        self.assertEqual(r['code'], 'COMBATANT_ROLE_INVALID')

    def test_019_invalid_action_kind_blocks(self):
        r = combat_round.build_initiative_order(combatants=[c(action_kind='WAIT')])
        self.assertEqual(r['code'], 'ACTION_KIND_UNSUPPORTED')

    def test_020_nonmonster_multiple_attacks_blocks(self):
        r = combat_round.build_initiative_order(combatants=[c(attacks_on_turn=2)])
        self.assertEqual(r['code'], 'MULTIPLE_ATTACKS_ONLY_MATERIALIZED_FOR_MONSTERS')

    def test_021_monster_multiple_attacks_share_one_turn(self):
        r = combat_round.build_initiative_order(combatants=[c(role='MONSTER', attacks_on_turn=3)])
        item = r['order'][0]
        self.assertEqual(item['turn_count'], 1)
        self.assertEqual(item['attacks_on_turn'], 3)

    def test_022_monster_multiple_attacks_require_attack_action(self):
        r = combat_round.build_initiative_order(combatants=[
            c(role='MONSTER', action_kind='FLEE', attacks_on_turn=2),
        ])
        self.assertEqual(r['code'], 'MONSTER_MULTIPLE_ATTACKS_REQUIRE_ATTACK_ACTION')

    def test_023_attacks_on_turn_zero_blocks(self):
        r = combat_round.build_initiative_order(combatants=[c(attacks_on_turn=0)])
        self.assertEqual(r['code'], 'ATTACKS_ON_TURN_INVALID')

    def test_024_one_turn_opportunity_each_flag(self):
        r = combat_round.build_initiative_order(combatants=[c('A', 80), c('B', 60)])
        self.assertTrue(r['one_turn_opportunity_each'])
        self.assertTrue(all(x['turn_count'] == 1 for x in r['order']))

    def test_025_no_automatic_action_selection(self):
        self.assertFalse(combat_round.build_initiative_order(combatants=[c()])['automatic_action_selection'])

    def test_026_no_automatic_tie_break(self):
        self.assertFalse(combat_round.build_initiative_order(combatants=[c()])['automatic_tie_break'])

    def test_027_initiative_no_randomness(self):
        self.assertFalse(combat_round.build_initiative_order(combatants=[c()])['randomness_generated'])

    def test_028_initiative_replay_stable(self):
        entries = [c('A', 80, 20), c('B', 50, 70)]
        self.assertEqual(
            combat_round.build_initiative_order(combatants=entries),
            combat_round.build_initiative_order(combatants=entries),
        )

    def test_029_valid_delay_is_pending(self):
        r = combat_round.plan_delay(
            actor_id='A', target_actor_id='B', round_actor_ids=['A', 'B'],
            actor_action_pending=True, target_has_acted=False,
        )
        self.assertEqual(r['status'], 'PENDING')
        self.assertFalse(r['action_consumed'])

    def test_030_delay_self_blocks(self):
        r = combat_round.plan_delay(
            actor_id='A', target_actor_id='A', round_actor_ids=['A', 'B'],
            actor_action_pending=True, target_has_acted=False,
        )
        self.assertEqual(r['code'], 'DELAY_TARGET_MUST_BE_ANOTHER_CHARACTER')

    def test_031_delay_actor_not_in_round_blocks(self):
        r = combat_round.plan_delay(
            actor_id='C', target_actor_id='B', round_actor_ids=['A', 'B'],
            actor_action_pending=True, target_has_acted=False,
        )
        self.assertEqual(r['code'], 'DELAY_ACTOR_OR_TARGET_NOT_IN_ROUND')

    def test_032_delay_target_not_in_round_blocks(self):
        r = combat_round.plan_delay(
            actor_id='A', target_actor_id='C', round_actor_ids=['A', 'B'],
            actor_action_pending=True, target_has_acted=False,
        )
        self.assertEqual(r['code'], 'DELAY_ACTOR_OR_TARGET_NOT_IN_ROUND')

    def test_033_delay_without_pending_action_blocks(self):
        r = combat_round.plan_delay(
            actor_id='A', target_actor_id='B', round_actor_ids=['A', 'B'],
            actor_action_pending=False, target_has_acted=False,
        )
        self.assertEqual(r['code'], 'ACTOR_HAS_NO_PENDING_ACTION_TO_DELAY')

    def test_034_delay_target_already_acted_blocks(self):
        r = combat_round.plan_delay(
            actor_id='A', target_actor_id='B', round_actor_ids=['A', 'B'],
            actor_action_pending=True, target_has_acted=True,
        )
        self.assertEqual(r['code'], 'DELAY_TARGET_ALREADY_ACTED')

    def test_035_delay_flags_must_be_boolean(self):
        r = combat_round.plan_delay(
            actor_id='A', target_actor_id='B', round_actor_ids=['A', 'B'],
            actor_action_pending=1, target_has_acted=False,
        )
        self.assertEqual(r['code'], 'DELAY_STATE_FLAG_INVALID')

    def test_036_delay_duplicate_round_actor_blocks(self):
        r = combat_round.plan_delay(
            actor_id='A', target_actor_id='B', round_actor_ids=['A', 'B', 'B'],
            actor_action_pending=True, target_has_acted=False,
        )
        self.assertEqual(r['code'], 'ROUND_ACTOR_ID_DUPLICATE')

    def test_037_delay_actor_ids_normalize_whitespace(self):
        r = combat_round.plan_delay(
            actor_id=' A ', target_actor_id=' B ', round_actor_ids=[' A ', 'B'],
            actor_action_pending=True, target_has_acted=False,
        )
        self.assertEqual(r['actor_id'], 'A')
        self.assertEqual(r['target_actor_id'], 'B')

    def test_038_delay_replay_stable(self):
        args = dict(
            actor_id='A', target_actor_id='B', round_actor_ids=['A', 'B'],
            actor_action_pending=True, target_has_acted=False,
        )
        self.assertEqual(combat_round.plan_delay(**args), combat_round.plan_delay(**args))

    def test_039_simultaneous_wait_highest_raw_dex_priority(self):
        r = combat_round.simultaneous_delayed_priority(waiting_combatants=[
            {'actor_id': 'A', 'dex': 40}, {'actor_id': 'B', 'dex': 80},
        ])
        self.assertEqual(r['priority_actor_id'], 'B')
        self.assertEqual(r['highest_raw_dex'], 80)

    def test_040_simultaneous_wait_three_characters(self):
        r = combat_round.simultaneous_delayed_priority(waiting_combatants=[
            {'actor_id': 'A', 'dex': 40}, {'actor_id': 'B', 'dex': 80}, {'actor_id': 'C', 'dex': 60},
        ])
        self.assertEqual(r['priority_actor_id'], 'B')

    def test_041_simultaneous_wait_uses_raw_dex(self):
        r = combat_round.simultaneous_delayed_priority(waiting_combatants=[
            {'actor_id': 'Shooter', 'dex': 40}, {'actor_id': 'Other', 'dex': 60},
        ])
        self.assertTrue(r['uses_raw_dex_not_firearm_adjusted_order'])
        self.assertEqual(r['priority_actor_id'], 'Other')

    def test_042_simultaneous_wait_dex_tie_fails_closed(self):
        r = combat_round.simultaneous_delayed_priority(waiting_combatants=[
            {'actor_id': 'A', 'dex': 60}, {'actor_id': 'B', 'dex': 60},
        ])
        self.assertEqual(r['code'], 'SIMULTANEOUS_DELAY_DEX_TIE_KEEPER_RESOLUTION_REQUIRED')

    def test_043_simultaneous_wait_duplicate_actor_blocks(self):
        r = combat_round.simultaneous_delayed_priority(waiting_combatants=[
            {'actor_id': 'A', 'dex': 60}, {'actor_id': 'A', 'dex': 50},
        ])
        self.assertEqual(r['code'], 'SIMULTANEOUS_WAIT_DUPLICATE_ACTOR')

    def test_044_simultaneous_wait_needs_two(self):
        r = combat_round.simultaneous_delayed_priority(waiting_combatants=[{'actor_id': 'A', 'dex': 60}])
        self.assertEqual(r['code'], 'AT_LEAST_TWO_SIMULTANEOUS_WAITING_COMBATANTS_REQUIRED')

    def test_045_simultaneous_wait_invalid_record_blocks(self):
        r = combat_round.simultaneous_delayed_priority(waiting_combatants=[
            {'actor_id': 'A', 'dex': 60, 'x': 1}, {'actor_id': 'B', 'dex': 50},
        ])
        self.assertEqual(r['code'], 'SIMULTANEOUS_WAIT_RECORD_INVALID')

    def test_046_simultaneous_wait_no_randomness(self):
        r = combat_round.simultaneous_delayed_priority(waiting_combatants=[
            {'actor_id': 'A', 'dex': 60}, {'actor_id': 'B', 'dex': 50},
        ])
        self.assertFalse(r['randomness_generated'])

    def test_047_mutual_wait_keeper_can_end_actions(self):
        r = combat_round.mutual_wait_resolution(
            actor_a='A', actor_b='B', both_insist_waiting=True, keeper_ends_round_for_them=True,
        )
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertTrue(r['actions_lost'])
        self.assertEqual(r['resulting_status'], 'LOST_BY_MUTUAL_DELAY')

    def test_048_mutual_wait_does_not_auto_end(self):
        r = combat_round.mutual_wait_resolution(
            actor_a='A', actor_b='B', both_insist_waiting=True, keeper_ends_round_for_them=False,
        )
        self.assertEqual(r['status'], 'PENDING')
        self.assertFalse(r['automatic_round_end'])

    def test_049_mutual_wait_not_established_blocks(self):
        r = combat_round.mutual_wait_resolution(
            actor_a='A', actor_b='B', both_insist_waiting=False, keeper_ends_round_for_them=False,
        )
        self.assertEqual(r['code'], 'MUTUAL_WAIT_NOT_ESTABLISHED')

    def test_050_mutual_wait_same_actor_blocks(self):
        r = combat_round.mutual_wait_resolution(
            actor_a='A', actor_b='A', both_insist_waiting=True, keeper_ends_round_for_them=True,
        )
        self.assertEqual(r['code'], 'MUTUAL_WAIT_REQUIRES_TWO_CHARACTERS')

    def test_051_mutual_wait_flags_must_be_boolean(self):
        r = combat_round.mutual_wait_resolution(
            actor_a='A', actor_b='B', both_insist_waiting=1, keeper_ends_round_for_them=True,
        )
        self.assertEqual(r['code'], 'MUTUAL_WAIT_FLAG_INVALID')

    def test_052_mutual_wait_replay_stable(self):
        args = dict(actor_a='A', actor_b='B', both_insist_waiting=True, keeper_ends_round_for_them=True)
        self.assertEqual(combat_round.mutual_wait_resolution(**args), combat_round.mutual_wait_resolution(**args))

    def test_053_round_all_acted_is_complete(self):
        r = combat_round.round_completion_status(
            round_actor_ids=['A', 'B'], action_status_by_actor={'A': 'ACTED', 'B': 'ACTED'},
        )
        self.assertTrue(r['round_complete'])
        self.assertTrue(r['next_round_may_begin'])

    def test_054_round_pending_actor_is_not_complete(self):
        r = combat_round.round_completion_status(
            round_actor_ids=['A', 'B'], action_status_by_actor={'A': 'ACTED', 'B': 'PENDING'},
        )
        self.assertFalse(r['round_complete'])
        self.assertEqual(r['pending_actor_ids'], ['B'])

    def test_055_incapable_actor_does_not_block_completion(self):
        r = combat_round.round_completion_status(
            round_actor_ids=['A', 'B'], action_status_by_actor={'A': 'ACTED', 'B': 'INCAPABLE'},
        )
        self.assertTrue(r['round_complete'])

    def test_056_declined_actor_does_not_block_completion(self):
        r = combat_round.round_completion_status(
            round_actor_ids=['A', 'B'], action_status_by_actor={'A': 'ACTED', 'B': 'DECLINED'},
        )
        self.assertTrue(r['round_complete'])

    def test_057_mutual_delay_lost_action_does_not_block_completion(self):
        r = combat_round.round_completion_status(
            round_actor_ids=['A', 'B'],
            action_status_by_actor={'A': 'LOST_BY_MUTUAL_DELAY', 'B': 'LOST_BY_MUTUAL_DELAY'},
        )
        self.assertTrue(r['round_complete'])

    def test_058_round_status_missing_actor_blocks(self):
        r = combat_round.round_completion_status(
            round_actor_ids=['A', 'B'], action_status_by_actor={'A': 'ACTED'},
        )
        self.assertEqual(r['code'], 'ROUND_STATUS_MAP_MUST_MATCH_ACTORS_EXACTLY')

    def test_059_round_status_extra_actor_blocks(self):
        r = combat_round.round_completion_status(
            round_actor_ids=['A'], action_status_by_actor={'A': 'ACTED', 'B': 'ACTED'},
        )
        self.assertEqual(r['code'], 'ROUND_STATUS_MAP_MUST_MATCH_ACTORS_EXACTLY')

    def test_060_round_invalid_status_blocks(self):
        r = combat_round.round_completion_status(
            round_actor_ids=['A'], action_status_by_actor={'A': 'WAITING'},
        )
        self.assertEqual(r['code'], 'ROUND_ACTOR_STATUS_INVALID')


def _make_action_kind_test(kind):
    def test(self):
        kwargs = {'action_kind': kind}
        if kind == 'FIREARMS_ATTACK':
            kwargs['firearm_readied'] = False
        r = combat_round.build_initiative_order(combatants=[c(**kwargs)])
        self.assertEqual(r['status'], 'RESOLVED')
        self.assertEqual(r['order'][0]['action_kind'], kind)
    return test


for _idx, _kind in enumerate(sorted(combat_round.ACTION_KINDS), start=1):
    setattr(
        CombatRoundInitiativeBatch1Tests,
        f'test_generated_action_kind_{_idx:02d}',
        _make_action_kind_test(_kind),
    )


def _make_dex_order_test(offset):
    def test(self):
        low = 20 + offset
        high = 70 + offset
        r = combat_round.build_initiative_order(combatants=[
            c('Low', low, 80), c('High', high, 10),
        ])
        self.assertEqual([x['actor_id'] for x in r['order']], ['High', 'Low'])
    return test


for _idx in range(1, 7):
    setattr(
        CombatRoundInitiativeBatch1Tests,
        f'test_generated_dex_order_{_idx:02d}',
        _make_dex_order_test(_idx),
    )


if __name__ == '__main__':
    unittest.main()
