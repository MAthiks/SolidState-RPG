from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
EQWP_DIR = ROOT / 'development' / 'r1-coc7-equipment-weapons-batch1'
for path in (RULES_DIR, EQWP_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import registry_eqwp_batch1_dev as registry  # noqa: E402

MODULE_ID = 'COC7_COMBAT_FIREARMS_R1_BATCH1_DEV_V1'
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
PARENT_REGISTRY_ID = registry.REGISTRY_ID
SUPPORTED_DIFFICULTIES = {'REGULAR', 'HARD', 'EXTREME'}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _simple_base_range_yards(record: dict) -> float | None:
    text = str(record.get('base_range', '')).strip()
    match = re.fullmatch(r'(\d+(?:\.\d+)?) yards', text)
    if not match:
        return None
    return float(match.group(1))


def _handgun_max_shots(record: dict) -> int | None:
    if record.get('skill_id') != 'FIREARMS_HANDGUN':
        return None
    match = re.search(r'\((\d+)\)', str(record.get('uses_per_round', '')))
    return int(match.group(1)) if match else None


def firearm_dex_order(dex: int, *, firearm_readied: bool) -> dict:
    if not _valid_int(dex, 0, 100) or not isinstance(firearm_readied, bool):
        return {'status': 'BLOCKED', 'code': 'DEX_ORDER_INPUT_INVALID'}
    return {
        'status': 'RESOLVED',
        'dex_order': dex + 50 if firearm_readied else dex,
        'readied_firearm_bonus': 50 if firearm_readied else 0,
    }


def attack_plan(
    *,
    weapon_id: str,
    distance_yards: float,
    shooter_dex: int,
    shot_count: int = 1,
    aimed_prior_round: bool = False,
    aim_broken_by_move_or_damage: bool = False,
    target_dived_cover_successfully: bool = False,
    concealment_fraction: float = 0.0,
    target_mov: int = 0,
    target_full_speed: bool = False,
    target_build: int = 0,
    firing_into_melee: bool = False,
) -> dict:
    weapon = registry.resolve_weapon(weapon_id)
    if weapon.get('status') != 'RESOLVED_MECHANICS':
        return {'status': 'BLOCKED', 'code': 'WEAPON_UNRESOLVED', 'weapon_id': weapon_id}
    record = weapon['record']

    if not isinstance(distance_yards, (int, float)) or isinstance(distance_yards, bool) or distance_yards < 0:
        return {'status': 'BLOCKED', 'code': 'DISTANCE_INVALID'}
    if not _valid_int(shooter_dex, 0, 100):
        return {'status': 'BLOCKED', 'code': 'SHOOTER_DEX_INVALID'}
    if not _valid_int(shot_count, 1, 3):
        return {'status': 'BLOCKED', 'code': 'SHOT_COUNT_UNSUPPORTED_BATCH1'}
    if not isinstance(concealment_fraction, (int, float)) or isinstance(concealment_fraction, bool) or not 0 <= concealment_fraction <= 1:
        return {'status': 'BLOCKED', 'code': 'CONCEALMENT_INVALID'}
    if not _valid_int(target_mov, 0):
        return {'status': 'BLOCKED', 'code': 'TARGET_MOV_INVALID'}
    if not _valid_int(target_build, -2, 20):
        return {'status': 'BLOCKED', 'code': 'TARGET_BUILD_INVALID'}
    for flag in (aimed_prior_round, aim_broken_by_move_or_damage, target_dived_cover_successfully, target_full_speed, firing_into_melee):
        if not isinstance(flag, bool):
            return {'status': 'BLOCKED', 'code': 'MODIFIER_FLAG_INVALID'}

    base_range = _simple_base_range_yards(record)
    if base_range is None:
        return {'status': 'BLOCKED', 'code': 'WEAPON_RANGE_FORM_UNMATERIALIZED_BATCH1', 'weapon_id': weapon_id}
    difficulty = core_rules.firearm_difficulty(float(distance_yards), base_range)
    if difficulty not in SUPPORTED_DIFFICULTIES:
        return {'status': 'BLOCKED', 'code': 'BEYOND_FOUR_TIMES_BASE_RANGE_BATCH1', 'difficulty': difficulty}

    modifiers = []
    point_blank_limit_yards = shooter_dex / 15.0
    point_blank = float(distance_yards) <= point_blank_limit_yards
    if point_blank:
        modifiers.append(('POINT_BLANK', 1))

    if aimed_prior_round and not aim_broken_by_move_or_damage:
        modifiers.append(('AIMING', 1))

    if target_dived_cover_successfully:
        modifiers.append(('DIVE_FOR_COVER', -1))
    if concealment_fraction >= 0.5:
        modifiers.append(('HALF_OR_MORE_CONCEALMENT', -1))
    if target_full_speed and target_mov >= 8:
        modifiers.append(('FAST_MOVING_TARGET', -1))
    if target_build <= -2:
        modifiers.append(('SMALL_TARGET', -1))
    elif target_build >= 4:
        modifiers.append(('LARGE_TARGET', 1))
    if firing_into_melee:
        modifiers.append(('FIRING_INTO_MELEE', -1))

    if shot_count > 1:
        max_shots = _handgun_max_shots(record)
        if max_shots is None:
            return {'status': 'BLOCKED', 'code': 'MULTIPLE_SHOTS_UNMATERIALIZED_FOR_WEAPON_BATCH1', 'weapon_id': weapon_id}
        if shot_count > max_shots:
            return {'status': 'BLOCKED', 'code': 'SHOT_COUNT_EXCEEDS_WEAPON_RATE', 'max_shots': max_shots}
        modifiers.append(('HANDGUN_MULTIPLE_SHOTS', -1))

    net = sum(value for _, value in modifiers)
    if abs(net) > 2:
        return {
            'status': 'BLOCKED',
            'code': 'MODIFIER_STACK_ABOVE_TWO_UNMATERIALIZED_BATCH1',
            'raw_net_modifier': net,
            'modifiers': modifiers,
        }

    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'parent_registry_id': PARENT_REGISTRY_ID,
        'keeper_source_id': KEEPER_SOURCE_ID,
        'keeper_source_sha256': KEEPER_SHA256,
        'weapon': record,
        'distance_yards': float(distance_yards),
        'base_range_yards': base_range,
        'difficulty': difficulty,
        'point_blank': point_blank,
        'point_blank_limit_yards': point_blank_limit_yards,
        'modifiers': [{'id': key, 'delta': value} for key, value in modifiers],
        'net_bonus': net,
        'shot_count': shot_count,
    }


def resolve_attack(*, skill_value: int, units: int, tens: list[int], plan: dict) -> dict:
    if plan.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'ATTACK_PLAN_NOT_RESOLVED'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, plan['net_bonus'])
        result = core_rules.meets_difficulty(skill_value, roll, plan['difficulty'])
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}

    level = result['level']
    hit = result['success']
    impale = False
    if hit and plan['weapon'].get('impale'):
        very_long = plan['difficulty'] == 'EXTREME'
        if very_long:
            impale = level == 'CRITICAL'
        else:
            impale = level in {'EXTREME', 'CRITICAL'}

    return {
        'status': 'RESOLVED',
        'roll': roll,
        'skill_value': skill_value,
        'difficulty': plan['difficulty'],
        'success_level': level,
        'hit': hit,
        'impale': impale,
        'shot_count': plan['shot_count'],
        'damage_expression': plan['weapon']['damage'] if hit else None,
        'randomness_generated': False,
    }


def unsupported_full_auto(*, weapon_id: str) -> dict:
    weapon = registry.resolve_weapon(weapon_id)
    if weapon.get('status') != 'RESOLVED_MECHANICS':
        return {'status': 'BLOCKED', 'code': 'WEAPON_UNRESOLVED'}
    return {'status': 'BLOCKED', 'code': 'FULL_AUTO_UNMATERIALIZED_BATCH1', 'weapon_id': weapon_id}
