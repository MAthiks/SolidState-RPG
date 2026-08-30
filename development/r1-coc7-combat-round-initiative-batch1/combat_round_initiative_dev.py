from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIREARMS_DIR = ROOT / 'development' / 'r1-coc7-combat-firearms-batch1'
LUCK_DIR = ROOT / 'development' / 'r1-coc7-luck-spending-batch1'
for path in (FIREARMS_DIR, LUCK_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import combat_firearms_dev as firearms  # noqa: E402
import luck_spending_dev as luck_spending  # noqa: E402

MODULE_ID = 'COC7_COMBAT_ROUND_INITIATIVE_R1_BATCH1_DEV_V1'
PARENT_LUCK_MODULE_ID = luck_spending.MODULE_ID
FIREARMS_MODULE_ID = firearms.MODULE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'

ACTION_KINDS = {
    'FIGHTING_ATTACK',
    'FIREARMS_ATTACK',
    'FIGHTING_MANEUVER',
    'FLEE',
    'CAST_SPELL',
    'OTHER_TIME_ACTION',
}
ROLES = {'INVESTIGATOR', 'NPC', 'MONSTER'}
ROUND_STATUSES = {'PENDING', 'ACTED', 'LOST_BY_MUTUAL_DELAY', 'INCAPABLE', 'DECLINED'}


def _blocked(code: str, **extra) -> dict:
    return {
        'status': 'BLOCKED',
        'code': code,
        'state_mutated': False,
        'randomness_generated': False,
        **extra,
    }


def _valid_int(value, minimum=None, maximum=None) -> bool:
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _valid_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _parse_combatant(record: dict, index: int) -> dict:
    expected = {
        'actor_id', 'dex', 'combat_skill', 'role',
        'action_kind', 'firearm_readied', 'attacks_on_turn',
    }
    if not isinstance(record, dict) or set(record) != expected:
        return _blocked('COMBATANT_RECORD_INVALID', index=index)
    actor_id = record['actor_id']
    dex = record['dex']
    combat_skill = record['combat_skill']
    role = record['role']
    action_kind = record['action_kind']
    firearm_readied = record['firearm_readied']
    attacks_on_turn = record['attacks_on_turn']
    if not _valid_text(actor_id):
        return _blocked('ACTOR_ID_INVALID', index=index)
    if not _valid_int(dex, 0, 100):
        return _blocked('DEX_INVALID', index=index)
    if not _valid_int(combat_skill, 0, 100):
        return _blocked('COMBAT_SKILL_INVALID', index=index)
    if role not in ROLES:
        return _blocked('COMBATANT_ROLE_INVALID', index=index)
    if action_kind not in ACTION_KINDS:
        return _blocked('ACTION_KIND_UNSUPPORTED', index=index)
    if not isinstance(firearm_readied, bool):
        return _blocked('FIREARM_READIED_FLAG_INVALID', index=index)
    if firearm_readied and action_kind != 'FIREARMS_ATTACK':
        return _blocked('READIED_FIREARM_BONUS_ONLY_APPLIES_TO_FIREARMS_ATTACK', index=index)
    if not _valid_int(attacks_on_turn, 1):
        return _blocked('ATTACKS_ON_TURN_INVALID', index=index)
    if role != 'MONSTER' and attacks_on_turn != 1:
        return _blocked('MULTIPLE_ATTACKS_ONLY_MATERIALIZED_FOR_MONSTERS', index=index)
    if attacks_on_turn > 1 and action_kind not in {'FIGHTING_ATTACK', 'FIREARMS_ATTACK'}:
        return _blocked('MONSTER_MULTIPLE_ATTACKS_REQUIRE_ATTACK_ACTION', index=index)

    if action_kind == 'FIREARMS_ATTACK':
        dex_record = firearms.firearm_dex_order(dex, firearm_readied=firearm_readied)
        if dex_record.get('status') != 'RESOLVED':
            return _blocked('FIREARM_DEX_ORDER_UNRESOLVED', index=index)
        order_score = dex_record['dex_order']
        readied_bonus = dex_record['readied_firearm_bonus']
    else:
        order_score = dex
        readied_bonus = 0

    return {
        'status': 'RESOLVED',
        'actor_id': actor_id.strip(),
        'dex': dex,
        'combat_skill': combat_skill,
        'role': role,
        'action_kind': action_kind,
        'firearm_readied': firearm_readied,
        'readied_firearm_bonus': readied_bonus,
        'dex_order_score': order_score,
        'attacks_on_turn': attacks_on_turn,
        'turn_count': 1,
    }


def build_initiative_order(*, combatants: list[dict]) -> dict:
    if not isinstance(combatants, list) or not combatants:
        return _blocked('COMBATANTS_REQUIRED')
    parsed = []
    seen = set()
    for index, record in enumerate(combatants):
        item = _parse_combatant(record, index)
        if item['status'] != 'RESOLVED':
            return item
        actor_id = item['actor_id']
        if actor_id in seen:
            return _blocked('DUPLICATE_ACTOR_ID', actor_id=actor_id)
        seen.add(actor_id)
        parsed.append(item)

    parsed.sort(key=lambda item: (item['dex_order_score'], item['combat_skill']), reverse=True)
    for first, second in zip(parsed, parsed[1:]):
        if (
            first['dex_order_score'] == second['dex_order_score']
            and first['combat_skill'] == second['combat_skill']
        ):
            return _blocked(
                'INITIATIVE_EXACT_TIE_KEEPER_RESOLUTION_REQUIRED',
                actor_ids=[first['actor_id'], second['actor_id']],
                dex_order_score=first['dex_order_score'],
                combat_skill=first['combat_skill'],
            )

    order = []
    for position, item in enumerate(parsed, start=1):
        order.append({
            'position': position,
            'actor_id': item['actor_id'],
            'raw_dex': item['dex'],
            'dex_order_score': item['dex_order_score'],
            'combat_skill': item['combat_skill'],
            'role': item['role'],
            'action_kind': item['action_kind'],
            'firearm_readied': item['firearm_readied'],
            'readied_firearm_bonus': item['readied_firearm_bonus'],
            'turn_count': 1,
            'attacks_on_turn': item['attacks_on_turn'],
        })
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'order': order,
        'actor_count': len(order),
        'one_turn_opportunity_each': True,
        'automatic_action_selection': False,
        'automatic_tie_break': False,
        'randomness_generated': False,
        'state_mutated': False,
    }


def plan_delay(
    *,
    actor_id: str,
    target_actor_id: str,
    round_actor_ids: list[str],
    actor_action_pending: bool,
    target_has_acted: bool,
) -> dict:
    if not _valid_text(actor_id) or not _valid_text(target_actor_id):
        return _blocked('DELAY_ACTOR_ID_INVALID')
    actor_id = actor_id.strip()
    target_actor_id = target_actor_id.strip()
    if actor_id == target_actor_id:
        return _blocked('DELAY_TARGET_MUST_BE_ANOTHER_CHARACTER')
    if not isinstance(round_actor_ids, list) or not round_actor_ids:
        return _blocked('ROUND_ACTOR_IDS_REQUIRED')
    normalized = []
    seen = set()
    for raw in round_actor_ids:
        if not _valid_text(raw):
            return _blocked('ROUND_ACTOR_ID_INVALID')
        value = raw.strip()
        if value in seen:
            return _blocked('ROUND_ACTOR_ID_DUPLICATE', actor_id=value)
        seen.add(value)
        normalized.append(value)
    if actor_id not in seen or target_actor_id not in seen:
        return _blocked('DELAY_ACTOR_OR_TARGET_NOT_IN_ROUND')
    if not isinstance(actor_action_pending, bool) or not isinstance(target_has_acted, bool):
        return _blocked('DELAY_STATE_FLAG_INVALID')
    if not actor_action_pending:
        return _blocked('ACTOR_HAS_NO_PENDING_ACTION_TO_DELAY')
    if target_has_acted:
        return _blocked('DELAY_TARGET_ALREADY_ACTED')
    return {
        'status': 'PENDING',
        'code': 'ACTION_DELAYED_UNTIL_TARGET_ACTS',
        'actor_id': actor_id,
        'target_actor_id': target_actor_id,
        'action_consumed': False,
        'state_mutated': True,
        'randomness_generated': False,
    }


def simultaneous_delayed_priority(*, waiting_combatants: list[dict]) -> dict:
    if not isinstance(waiting_combatants, list) or len(waiting_combatants) < 2:
        return _blocked('AT_LEAST_TWO_SIMULTANEOUS_WAITING_COMBATANTS_REQUIRED')
    parsed = []
    seen = set()
    for index, record in enumerate(waiting_combatants):
        if not isinstance(record, dict) or set(record) != {'actor_id', 'dex'}:
            return _blocked('SIMULTANEOUS_WAIT_RECORD_INVALID', index=index)
        actor_id = record['actor_id']
        dex = record['dex']
        if not _valid_text(actor_id) or not _valid_int(dex, 0, 100):
            return _blocked('SIMULTANEOUS_WAIT_INPUT_INVALID', index=index)
        actor_id = actor_id.strip()
        if actor_id in seen:
            return _blocked('SIMULTANEOUS_WAIT_DUPLICATE_ACTOR', actor_id=actor_id)
        seen.add(actor_id)
        parsed.append({'actor_id': actor_id, 'dex': dex})
    highest = max(item['dex'] for item in parsed)
    candidates = [item['actor_id'] for item in parsed if item['dex'] == highest]
    if len(candidates) != 1:
        return _blocked(
            'SIMULTANEOUS_DELAY_DEX_TIE_KEEPER_RESOLUTION_REQUIRED',
            highest_dex=highest,
            actor_ids=candidates,
        )
    return {
        'status': 'RESOLVED',
        'priority_actor_id': candidates[0],
        'highest_raw_dex': highest,
        'uses_raw_dex_not_firearm_adjusted_order': True,
        'automatic_tie_break': False,
        'state_mutated': False,
        'randomness_generated': False,
    }


def mutual_wait_resolution(
    *,
    actor_a: str,
    actor_b: str,
    both_insist_waiting: bool,
    keeper_ends_round_for_them: bool,
) -> dict:
    if not _valid_text(actor_a) or not _valid_text(actor_b):
        return _blocked('MUTUAL_WAIT_ACTOR_ID_INVALID')
    actor_a = actor_a.strip()
    actor_b = actor_b.strip()
    if actor_a == actor_b:
        return _blocked('MUTUAL_WAIT_REQUIRES_TWO_CHARACTERS')
    if not isinstance(both_insist_waiting, bool) or not isinstance(keeper_ends_round_for_them, bool):
        return _blocked('MUTUAL_WAIT_FLAG_INVALID')
    if not both_insist_waiting:
        return _blocked('MUTUAL_WAIT_NOT_ESTABLISHED')
    if not keeper_ends_round_for_them:
        return {
            'status': 'PENDING',
            'code': 'KEEPER_MAY_END_ROUND_FOR_MUTUAL_WAITERS',
            'actor_ids': [actor_a, actor_b],
            'actions_lost': False,
            'automatic_round_end': False,
            'state_mutated': False,
            'randomness_generated': False,
        }
    return {
        'status': 'RESOLVED',
        'actor_ids': [actor_a, actor_b],
        'resulting_status': 'LOST_BY_MUTUAL_DELAY',
        'actions_lost': True,
        'automatic_round_end': False,
        'keeper_resolution_required': True,
        'state_mutated': True,
        'randomness_generated': False,
    }


def round_completion_status(*, round_actor_ids: list[str], action_status_by_actor: dict[str, str]) -> dict:
    if not isinstance(round_actor_ids, list) or not round_actor_ids:
        return _blocked('ROUND_ACTOR_IDS_REQUIRED')
    normalized = []
    seen = set()
    for raw in round_actor_ids:
        if not _valid_text(raw):
            return _blocked('ROUND_ACTOR_ID_INVALID')
        actor_id = raw.strip()
        if actor_id in seen:
            return _blocked('ROUND_ACTOR_ID_DUPLICATE', actor_id=actor_id)
        seen.add(actor_id)
        normalized.append(actor_id)
    if not isinstance(action_status_by_actor, dict):
        return _blocked('ROUND_STATUS_MAP_INVALID')
    if set(action_status_by_actor) != set(normalized):
        return _blocked(
            'ROUND_STATUS_MAP_MUST_MATCH_ACTORS_EXACTLY',
            expected_actor_ids=sorted(normalized),
            actual_actor_ids=sorted(action_status_by_actor) if all(isinstance(k, str) for k in action_status_by_actor) else [],
        )
    for actor_id, status in action_status_by_actor.items():
        if status not in ROUND_STATUSES:
            return _blocked('ROUND_ACTOR_STATUS_INVALID', actor_id=actor_id)
    pending = [actor_id for actor_id in normalized if action_status_by_actor[actor_id] == 'PENDING']
    return {
        'status': 'RESOLVED',
        'round_complete': len(pending) == 0,
        'pending_actor_ids': pending,
        'next_round_may_begin': len(pending) == 0,
        'automatic_round_end': False,
        'randomness_generated': False,
        'state_mutated': False,
    }
