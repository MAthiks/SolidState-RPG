from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
EQWP_DIR = ROOT / 'development' / 'r1-coc7-equipment-weapons-batch1'
FIREARMS2_DIR = ROOT / 'development' / 'r1-coc7-combat-firearms-batch2'
for path in (RULES_DIR, EQWP_DIR, FIREARMS2_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import registry_eqwp_batch1_dev as registry  # noqa: E402
import combat_firearms_batch2_dev as firearms2  # noqa: E402

MODULE_ID = 'COC7_MELEE_COMBAT_R1_BATCH1_DEV_V1'
PARENT_FIREARMS_MODULE_ID = firearms2.MODULE_ID
PARENT_REGISTRY_ID = registry.REGISTRY_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
DEFENSE_MODES = {'DODGE', 'FIGHT_BACK'}
GOAL_TYPES = {'DISARM', 'RESTRAIN', 'KNOCK_DOWN', 'ESCAPE_RESTRAINT', 'OTHER_KEEPER_DEFINED'}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _rank(level: str) -> int:
    return core_rules.LEVEL_RANK[level]


def _roll(skill_value: int, units: int, tens: list[int], net_bonus: int) -> dict:
    if not _valid_int(skill_value, 0, 100):
        return {'status': 'BLOCKED', 'code': 'SKILL_VALUE_INVALID'}
    if not _valid_int(net_bonus, -2, 2):
        return {'status': 'BLOCKED', 'code': 'MELEE_MODIFIER_OUT_OF_RANGE'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, net_bonus)
        level = core_rules.success_level(skill_value, roll)
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    return {'status': 'RESOLVED', 'roll': roll, 'level': level, 'skill_value': skill_value, 'net_bonus': net_bonus}


def resolve_melee_exchange(
    *,
    attacker_skill: int,
    attacker_units: int,
    attacker_tens: list[int],
    defender_skill: int,
    defender_units: int,
    defender_tens: list[int],
    defense_mode: str,
    attacker_net_bonus: int = 0,
    defender_net_bonus: int = 0,
    attacker_is_actor_turn: bool = True,
) -> dict:
    if defense_mode not in DEFENSE_MODES:
        return {'status': 'BLOCKED', 'code': 'DEFENSE_MODE_INVALID'}
    if not isinstance(attacker_is_actor_turn, bool):
        return {'status': 'BLOCKED', 'code': 'ACTOR_TURN_FLAG_INVALID'}

    attacker = _roll(attacker_skill, attacker_units, attacker_tens, attacker_net_bonus)
    if attacker.get('status') != 'RESOLVED':
        return attacker
    defender = _roll(defender_skill, defender_units, defender_tens, defender_net_bonus)
    if defender.get('status') != 'RESOLVED':
        return defender

    a_level = attacker['level']
    d_level = defender['level']
    a_rank = _rank(a_level)
    d_rank = _rank(d_level)
    both_fail = a_level in {'FAILURE', 'FUMBLE'} and d_level in {'FAILURE', 'FUMBLE'}

    if both_fail:
        winner = 'NONE'
        outcome = 'NO_DAMAGE'
    elif defense_mode == 'DODGE':
        if a_rank > d_rank:
            winner = 'ATTACKER'
            outcome = 'ATTACKER_HITS'
        else:
            winner = 'DEFENDER'
            outcome = 'DODGED'
    else:
        if a_rank > d_rank or a_rank == d_rank:
            winner = 'ATTACKER'
            outcome = 'ATTACKER_HITS'
        else:
            winner = 'DEFENDER'
            outcome = 'DEFENDER_COUNTERHITS'

    extreme_damage_eligible = (
        winner == 'ATTACKER'
        and attacker_is_actor_turn
        and a_level in {'EXTREME', 'CRITICAL'}
    )

    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'defense_mode': defense_mode,
        'attacker': attacker,
        'defender': defender,
        'winner': winner,
        'outcome': outcome,
        'extreme_damage_eligible': extreme_damage_eligible,
        'defender_counterhit_extreme_bonus_allowed': False,
        'randomness_generated': False,
    }


def maneuver_plan(
    *,
    attacker_build: int,
    defender_build: int,
    goal_type: str,
    goal: str,
    additional_net_bonus: int = 0,
) -> dict:
    if not _valid_int(attacker_build, -2, 20) or not _valid_int(defender_build, -2, 20):
        return {'status': 'BLOCKED', 'code': 'BUILD_INVALID'}
    if goal_type not in GOAL_TYPES:
        return {'status': 'BLOCKED', 'code': 'MANEUVER_GOAL_TYPE_INVALID'}
    if not isinstance(goal, str) or not goal.strip():
        return {'status': 'BLOCKED', 'code': 'MANEUVER_DEFINITE_GOAL_REQUIRED'}
    if not _valid_int(additional_net_bonus, -2, 2):
        return {'status': 'BLOCKED', 'code': 'MANEUVER_ADDITIONAL_MODIFIER_INVALID'}

    difference = defender_build - attacker_build
    if difference >= 3:
        return {
            'status': 'BLOCKED',
            'code': 'MANEUVER_IMPOSSIBLE_BUILD_DIFFERENCE',
            'build_difference': difference,
        }
    build_penalty = -2 if difference == 2 else (-1 if difference == 1 else 0)
    net = build_penalty + additional_net_bonus
    if net < -2 or net > 2:
        return {'status': 'BLOCKED', 'code': 'MANEUVER_MODIFIER_STACK_UNMATERIALIZED', 'raw_net_bonus': net}

    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'goal_type': goal_type,
        'goal': goal.strip(),
        'attacker_build': attacker_build,
        'defender_build': defender_build,
        'build_difference': difference,
        'build_penalty': build_penalty,
        'additional_net_bonus': additional_net_bonus,
        'net_bonus': net,
    }


def resolve_maneuver(
    *,
    plan: dict,
    attacker_skill: int,
    attacker_units: int,
    attacker_tens: list[int],
    defender_skill: int,
    defender_units: int,
    defender_tens: list[int],
    defense_mode: str,
    defender_counter_is_maneuver: bool = False,
) -> dict:
    if not isinstance(plan, dict) or plan.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'MANEUVER_PLAN_UNRESOLVED'}
    if not isinstance(defender_counter_is_maneuver, bool):
        return {'status': 'BLOCKED', 'code': 'COUNTER_MANEUVER_FLAG_INVALID'}

    exchange = resolve_melee_exchange(
        attacker_skill=attacker_skill,
        attacker_units=attacker_units,
        attacker_tens=attacker_tens,
        defender_skill=defender_skill,
        defender_units=defender_units,
        defender_tens=defender_tens,
        defense_mode=defense_mode,
        attacker_net_bonus=plan['net_bonus'],
        defender_net_bonus=0,
        attacker_is_actor_turn=True,
    )
    if exchange.get('status') != 'RESOLVED':
        return exchange

    if exchange['winner'] == 'ATTACKER':
        outcome = 'MANEUVER_SUCCEEDS'
    elif exchange['winner'] == 'DEFENDER' and defense_mode == 'FIGHT_BACK':
        outcome = 'DEFENDER_COUNTER_MANEUVER' if defender_counter_is_maneuver else 'DEFENDER_INFLICTS_DAMAGE'
    elif exchange['winner'] == 'DEFENDER':
        outcome = 'TARGET_DODGES_MANEUVER'
    else:
        outcome = 'MANEUVER_NO_EFFECT'

    return {
        'status': 'RESOLVED',
        'outcome': outcome,
        'maneuver_success': outcome == 'MANEUVER_SUCCEEDS',
        'goal_type': plan['goal_type'],
        'goal': plan['goal'],
        'exchange': exchange,
        'effect_options': maneuver_effect_options(plan['goal_type']) if outcome == 'MANEUVER_SUCCEEDS' else None,
        'randomness_generated': False,
    }


def maneuver_effect_options(goal_type: str) -> dict:
    if goal_type not in GOAL_TYPES:
        return {'status': 'BLOCKED', 'code': 'MANEUVER_GOAL_TYPE_INVALID'}
    if goal_type == 'DISARM':
        effect = {'type': 'DISARM_OR_WREST_ITEM'}
    elif goal_type == 'RESTRAIN':
        effect = {
            'type': 'RESTRAINT',
            'ongoing_disadvantage_options': ['TARGET_FUTURE_ACTIONS_ONE_PENALTY_DIE', 'ALLIES_AGAINST_TARGET_ONE_BONUS_DIE'],
            'persists_until': ['RELEASED', 'RESTRAINER_INCAPACITATED', 'RESTRAINER_MAJOR_WOUND', 'TARGET_SUCCESSFUL_ESCAPE_MANEUVER'],
        }
    elif goal_type == 'KNOCK_DOWN':
        effect = {
            'type': 'ONGOING_DISADVANTAGE',
            'options': ['TARGET_FUTURE_ACTIONS_ONE_PENALTY_DIE', 'ALLIES_AGAINST_TARGET_ONE_BONUS_DIE'],
        }
    elif goal_type == 'ESCAPE_RESTRAINT':
        effect = {'type': 'BREAK_RESTRAINT'}
    else:
        effect = {'type': 'KEEPER_DEFINED_STRUCTURED_GOAL', 'narrative_effect_not_inferred': True}
    return {'status': 'RESOLVED', **effect}


def outnumbered_attack_modifier(*, defenses_already_used: int, defensive_capacity: int = 1, attack_is_firearm: bool = False) -> dict:
    if not _valid_int(defenses_already_used, 0) or not _valid_int(defensive_capacity, 1):
        return {'status': 'BLOCKED', 'code': 'OUTNUMBERED_INPUT_INVALID'}
    if not isinstance(attack_is_firearm, bool):
        return {'status': 'BLOCKED', 'code': 'FIREARM_FLAG_INVALID'}
    bonus = 0 if attack_is_firearm else (1 if defenses_already_used >= defensive_capacity else 0)
    return {
        'status': 'RESOLVED',
        'bonus_die': bonus,
        'defensive_capacity': defensive_capacity,
        'defenses_already_used': defenses_already_used,
        'firearms_excluded': attack_is_firearm,
    }


def surprise_plan(*, anticipated: bool, attack_type: str, keeper_choice: str = 'NORMAL') -> dict:
    if not isinstance(anticipated, bool):
        return {'status': 'BLOCKED', 'code': 'SURPRISE_ANTICIPATED_FLAG_INVALID'}
    if attack_type not in {'MELEE', 'RANGED'}:
        return {'status': 'BLOCKED', 'code': 'SURPRISE_ATTACK_TYPE_INVALID'}

    if anticipated:
        return {
            'status': 'RESOLVED',
            'anticipated': True,
            'defense_allowed': True,
            'roll_required': True,
            'mode': 'NORMAL_DEFENDED_ATTACK',
            'net_bonus': 0,
        }

    if keeper_choice not in {'AUTO_SUCCESS_EXCEPT_FUMBLE', 'BONUS_DIE'}:
        return {'status': 'BLOCKED', 'code': 'SURPRISE_KEEPER_CHOICE_REQUIRED'}
    if attack_type == 'RANGED' and keeper_choice == 'AUTO_SUCCESS_EXCEPT_FUMBLE':
        return {'status': 'BLOCKED', 'code': 'RANGED_SURPRISE_ROLL_ALWAYS_REQUIRED'}

    return {
        'status': 'RESOLVED',
        'anticipated': False,
        'defense_allowed': False,
        'roll_required': True,
        'mode': keeper_choice,
        'net_bonus': 1 if keeper_choice == 'BONUS_DIE' else 0,
    }


def resolve_unopposed_attack(*, skill_value: int, units: int, tens: list[int], plan: dict) -> dict:
    if not isinstance(plan, dict) or plan.get('status') != 'RESOLVED' or plan.get('defense_allowed') is not False:
        return {'status': 'BLOCKED', 'code': 'UNOPPOSED_PLAN_REQUIRED'}
    rolled = _roll(skill_value, units, tens, plan.get('net_bonus', 0))
    if rolled.get('status') != 'RESOLVED':
        return rolled
    hit = rolled['level'] != 'FUMBLE'
    return {
        'status': 'RESOLVED',
        'roll': rolled['roll'],
        'success_level': rolled['level'],
        'hit': hit,
        'only_fumble_fails': plan['mode'] == 'AUTO_SUCCESS_EXCEPT_FUMBLE',
        'randomness_generated': False,
    }


def escape_close_combat(*, has_escape_route: bool, physically_restrained: bool) -> dict:
    if not isinstance(has_escape_route, bool) or not isinstance(physically_restrained, bool):
        return {'status': 'BLOCKED', 'code': 'ESCAPE_FLAG_INVALID'}
    allowed = has_escape_route and not physically_restrained
    return {
        'status': 'RESOLVED',
        'escape_allowed': allowed,
        'uses_action': allowed,
        'reason': None if allowed else ('PHYSICALLY_RESTRAINED' if physically_restrained else 'NO_ESCAPE_ROUTE'),
    }


def _parse_standard_melee_damage(expression: str) -> dict | None:
    text = expression.replace(' ', '')
    uses_db = text.endswith('+DB')
    if uses_db:
        text = text[:-3]
    if 'HALF_DB' in text or 'BURN' in text or '/' in text:
        return None
    match = re.fullmatch(r'(\d+)D(\d+)(?:\+(\d+))?', text)
    if not match:
        return None
    dice_count = int(match.group(1))
    die_size = int(match.group(2))
    constant = int(match.group(3) or 0)
    return {
        'weapon_roll_expression': text,
        'weapon_maximum': dice_count * die_size + constant,
        'uses_damage_bonus': uses_db,
    }


def extreme_damage_profile(
    *,
    success_level: str,
    on_actor_turn: bool,
    weapon_id: str | None = None,
    damage_bonus_max: int = 0,
) -> dict:
    if success_level not in core_rules.LEVEL_RANK:
        return {'status': 'BLOCKED', 'code': 'SUCCESS_LEVEL_INVALID'}
    if not isinstance(on_actor_turn, bool) or not _valid_int(damage_bonus_max, -20, 100):
        return {'status': 'BLOCKED', 'code': 'EXTREME_DAMAGE_INPUT_INVALID'}

    if weapon_id is None:
        record = {'weapon_id': 'UNARMED', 'damage': '1D3+DB', 'impale': False}
    else:
        resolved = registry.resolve_weapon(weapon_id)
        if resolved.get('status') != 'RESOLVED_MECHANICS':
            return {'status': 'BLOCKED', 'code': 'WEAPON_UNRESOLVED'}
        record = resolved['record']

    parsed = _parse_standard_melee_damage(record['damage'])
    if parsed is None:
        return {'status': 'BLOCKED', 'code': 'COMPLEX_DAMAGE_EXPRESSION_UNMATERIALIZED', 'weapon_id': record['weapon_id']}

    extreme = success_level in {'EXTREME', 'CRITICAL'} and on_actor_turn
    if not extreme:
        return {
            'status': 'RESOLVED',
            'mode': 'NORMAL_DAMAGE_ROLL',
            'weapon_roll_expression': parsed['weapon_roll_expression'],
            'damage_bonus_applies': parsed['uses_damage_bonus'],
            'extreme_bonus_applied': False,
        }

    db = damage_bonus_max if parsed['uses_damage_bonus'] else 0
    fixed = parsed['weapon_maximum'] + db
    if record.get('impale'):
        return {
            'status': 'RESOLVED',
            'mode': 'IMPALE',
            'fixed_component': fixed,
            'extra_weapon_roll_expression': parsed['weapon_roll_expression'],
            'damage_bonus_rolled_again': False,
            'extreme_bonus_applied': True,
        }
    return {
        'status': 'RESOLVED',
        'mode': 'MAXIMUM_DAMAGE',
        'fixed_damage': fixed,
        'extreme_bonus_applied': True,
    }
