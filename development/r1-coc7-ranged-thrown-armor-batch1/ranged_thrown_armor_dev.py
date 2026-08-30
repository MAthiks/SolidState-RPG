from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
EQWP_DIR = ROOT / 'development' / 'r1-coc7-equipment-weapons-batch1'
FIREARMS_DIR = ROOT / 'development' / 'r1-coc7-combat-firearms-batch1'
MELEE_DIR = ROOT / 'development' / 'r1-coc7-melee-combat-batch1'
ROUND_DIR = ROOT / 'development' / 'r1-coc7-combat-round-initiative-batch1'
for path in (RULES_DIR, EQWP_DIR, FIREARMS_DIR, MELEE_DIR, ROUND_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import registry_eqwp_batch1_dev as registry  # noqa: E402
import combat_firearms_dev as firearms1  # noqa: E402
import melee_combat_dev as melee  # noqa: E402
import combat_round_initiative_dev as combat_round  # noqa: E402

MODULE_ID = 'COC7_RANGED_THROWN_ARMOR_R1_BATCH1_DEV_V1'
PARENT_COMBAT_ROUND_MODULE_ID = combat_round.MODULE_ID
FIREARMS_MODULE_ID = firearms1.MODULE_ID
MELEE_MODULE_ID = melee.MODULE_ID
REGISTRY_ID = registry.REGISTRY_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
DEFENSE_MODES = {'NONE', 'DODGE', 'FIGHT_BACK'}
EXPLICIT_NON_ARMOR_DAMAGE_CATEGORIES = {'MAGICAL', 'POISON', 'DROWNING'}
SUPPORTED_ARMOR_DAMAGE_CATEGORIES = {'PHYSICAL'} | EXPLICIT_NON_ARMOR_DAMAGE_CATEGORIES


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _valid_distance_feet(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def _simple_yards(text: str) -> float | None:
    match = re.fullmatch(r'(\d+(?:\.\d+)?) yards', str(text).strip())
    return float(match.group(1)) if match else None


def weapon_ranged_profile(*, weapon_id: str, attacker_str: int) -> dict:
    if not _valid_int(attacker_str, 0, 100):
        return {'status': 'BLOCKED', 'code': 'ATTACKER_STR_INVALID'}
    resolved = registry.resolve_weapon(weapon_id)
    if resolved.get('status') != 'RESOLVED_MECHANICS':
        return {'status': 'BLOCKED', 'code': 'WEAPON_UNRESOLVED', 'weapon_id': weapon_id}
    record = resolved['record']
    skill_id = record.get('skill_id')
    range_text = str(record.get('base_range', ''))

    if skill_id == 'THROW':
        if range_text != 'STR/5 yards':
            return {'status': 'BLOCKED', 'code': 'THROWN_RANGE_FORM_UNMATERIALIZED', 'weapon_id': record['weapon_id']}
        base_range_yards = attacker_str / 5.0
        weapon_class = 'THROWN'
    elif skill_id == 'FIREARMS_BOW':
        base_range_yards = _simple_yards(range_text)
        if base_range_yards is None:
            return {'status': 'BLOCKED', 'code': 'MISSILE_RANGE_FORM_UNMATERIALIZED', 'weapon_id': record['weapon_id']}
        weapon_class = 'RANGED_MISSILE'
    else:
        return {'status': 'BLOCKED', 'code': 'WEAPON_NOT_RANGED_MISSILE_OR_THROWN', 'weapon_id': record['weapon_id']}

    damage_expression = str(record.get('damage', ''))
    half_db_applies = 'HALF_DB' in damage_expression
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'registry_id': REGISTRY_ID,
        'weapon': record,
        'weapon_class': weapon_class,
        'base_range_yards': base_range_yards,
        'half_damage_bonus_applies': half_db_applies,
        'damage_expression': damage_expression,
        'randomness_generated': False,
    }


def ranged_or_thrown_attack_plan(
    *,
    weapon_id: str,
    attacker_str: int,
    attacker_dex: int,
    distance_feet: float,
    defense_mode: str,
    target_dived_cover_successfully: bool = False,
) -> dict:
    if not _valid_int(attacker_dex, 0, 100):
        return {'status': 'BLOCKED', 'code': 'ATTACKER_DEX_INVALID'}
    if not _valid_distance_feet(distance_feet):
        return {'status': 'BLOCKED', 'code': 'DISTANCE_INVALID'}
    if defense_mode not in DEFENSE_MODES:
        return {'status': 'BLOCKED', 'code': 'DEFENSE_MODE_INVALID'}
    if not isinstance(target_dived_cover_successfully, bool):
        return {'status': 'BLOCKED', 'code': 'DIVE_FOR_COVER_FLAG_INVALID'}

    profile = weapon_ranged_profile(weapon_id=weapon_id, attacker_str=attacker_str)
    if profile.get('status') != 'RESOLVED':
        return profile

    distance_yards = float(distance_feet) / 3.0
    try:
        difficulty = core_rules.firearm_difficulty(distance_yards, profile['base_range_yards'])
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    if difficulty not in {'REGULAR', 'HARD', 'EXTREME'}:
        return {'status': 'BLOCKED', 'code': 'BEYOND_FOUR_TIMES_BASE_RANGE'}

    fight_back_limit_feet = attacker_dex / 5.0
    if defense_mode == 'FIGHT_BACK' and float(distance_feet) > fight_back_limit_feet:
        return {
            'status': 'BLOCKED',
            'code': 'FIGHT_BACK_OUTSIDE_DEX_OVER_5_FEET',
            'fight_back_limit_feet': fight_back_limit_feet,
        }
    if defense_mode == 'DODGE' and profile['weapon_class'] != 'THROWN':
        return {'status': 'BLOCKED', 'code': 'DODGE_OPPOSITION_ONLY_MATERIALIZED_FOR_THROWN_WEAPON'}

    if profile['weapon_class'] == 'RANGED_MISSILE':
        firearm_plan = firearms1.attack_plan(
            weapon_id=profile['weapon']['weapon_id'],
            distance_yards=distance_yards,
            shooter_dex=attacker_dex,
            shot_count=1,
            target_dived_cover_successfully=target_dived_cover_successfully,
        )
        if firearm_plan.get('status') != 'RESOLVED':
            return {'status': 'BLOCKED', 'code': 'RANGED_MISSILE_FIREARM_PLAN_UNRESOLVED', 'parent': firearm_plan}
    else:
        firearm_plan = None
        if target_dived_cover_successfully:
            return {'status': 'BLOCKED', 'code': 'DIVE_FOR_COVER_ROUTING_NOT_MATERIALIZED_FOR_THROWN_BATCH1'}

    opposed_route = None
    if defense_mode == 'DODGE':
        opposed_route = {
            'engine_module_id': MELEE_MODULE_ID,
            'engine_function': 'resolve_melee_exchange',
            'defense_mode': 'DODGE',
            'combined_range_and_opposition_resolution': 'FAIL_CLOSED_PENDING_EXPLICIT_CONTRACT',
        }
    elif defense_mode == 'FIGHT_BACK':
        opposed_route = {
            'engine_module_id': MELEE_MODULE_ID,
            'defense_mode': 'FIGHT_BACK',
            'combined_range_and_opposition_resolution': 'FAIL_CLOSED_PENDING_EXPLICIT_CONTRACT',
        }

    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'parent_combat_round_module_id': PARENT_COMBAT_ROUND_MODULE_ID,
        'weapon': profile['weapon'],
        'weapon_class': profile['weapon_class'],
        'distance_feet': float(distance_feet),
        'distance_yards': distance_yards,
        'base_range_yards': profile['base_range_yards'],
        'difficulty': difficulty,
        'defense_mode': defense_mode,
        'fight_back_limit_feet': fight_back_limit_feet,
        'half_damage_bonus_applies': profile['half_damage_bonus_applies'],
        'firearm_style_plan': firearm_plan,
        'opposed_route': opposed_route,
        'automatic_target_defense_selection': False,
        'randomness_generated': False,
    }


def resolve_ranged_missile_attack(*, plan: dict, skill_value: int, units: int, tens: list[int]) -> dict:
    if not isinstance(plan, dict) or plan.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'ATTACK_PLAN_UNRESOLVED'}
    if plan.get('weapon_class') != 'RANGED_MISSILE':
        return {'status': 'BLOCKED', 'code': 'RANGED_MISSILE_PLAN_REQUIRED'}
    if plan.get('defense_mode') in {'DODGE', 'FIGHT_BACK'}:
        return {'status': 'BLOCKED', 'code': 'OPPOSED_RANGED_RESOLUTION_UNMATERIALIZED_BATCH1'}
    parent = plan.get('firearm_style_plan')
    if not isinstance(parent, dict) or parent.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'FIREARM_STYLE_PLAN_REQUIRED'}
    result = firearms1.resolve_attack(skill_value=skill_value, units=units, tens=tens, plan=parent)
    if result.get('status') != 'RESOLVED':
        return result
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'weapon_id': plan['weapon']['weapon_id'],
        'weapon_class': plan['weapon_class'],
        'roll': result['roll'],
        'success_level': result['success_level'],
        'hit': result['hit'],
        'difficulty': result['difficulty'],
        'impale': result['impale'],
        'damage_expression': result['damage_expression'],
        'half_damage_bonus_applies': plan['half_damage_bonus_applies'],
        'randomness_generated': False,
    }


def resolve_unopposed_thrown_attack(*, plan: dict, skill_value: int, roll: int) -> dict:
    if not isinstance(plan, dict) or plan.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'ATTACK_PLAN_UNRESOLVED'}
    if plan.get('weapon_class') != 'THROWN':
        return {'status': 'BLOCKED', 'code': 'THROWN_PLAN_REQUIRED'}
    if plan.get('defense_mode') != 'NONE':
        return {'status': 'BLOCKED', 'code': 'OPPOSED_THROWN_RESOLUTION_UNMATERIALIZED_BATCH1'}
    if not _valid_int(skill_value, 0, 100) or not _valid_int(roll, 1, 100):
        return {'status': 'BLOCKED', 'code': 'THROWN_ROLL_INPUT_INVALID'}
    try:
        result = core_rules.meets_difficulty(skill_value, roll, plan['difficulty'])
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'weapon_id': plan['weapon']['weapon_id'],
        'roll': roll,
        'success_level': result['level'],
        'hit': result['success'],
        'difficulty': plan['difficulty'],
        'damage_expression': plan['weapon']['damage'] if result['success'] else None,
        'half_damage_bonus_applies': plan['half_damage_bonus_applies'],
        'randomness_generated': False,
    }


def apply_armor(
    *,
    incoming_damage: int,
    armor_points: int,
    damage_category: str,
    attack_passes_through_armor: bool,
) -> dict:
    if not _valid_int(incoming_damage, 0) or not _valid_int(armor_points, 0):
        return {'status': 'BLOCKED', 'code': 'ARMOR_NUMERIC_INPUT_INVALID', 'state_mutated': False}
    if not isinstance(damage_category, str):
        return {'status': 'BLOCKED', 'code': 'DAMAGE_CATEGORY_INVALID', 'state_mutated': False}
    category = damage_category.strip().upper()
    if category not in SUPPORTED_ARMOR_DAMAGE_CATEGORIES:
        return {'status': 'BLOCKED', 'code': 'DAMAGE_CATEGORY_UNMATERIALIZED_FOR_ARMOR', 'state_mutated': False}
    if not isinstance(attack_passes_through_armor, bool):
        return {'status': 'BLOCKED', 'code': 'ARMOR_PATH_FLAG_INVALID', 'state_mutated': False}

    if category in EXPLICIT_NON_ARMOR_DAMAGE_CATEGORIES:
        reduction = 0
        reason = 'SOURCE_EXPLICIT_ARMOR_EXCLUSION'
    elif not attack_passes_through_armor:
        reduction = 0
        reason = 'ATTACK_DID_NOT_PASS_THROUGH_ARMOR'
    else:
        reduction = min(incoming_damage, armor_points)
        reason = 'ARMOR_POINTS_DEDUCTED_FROM_PHYSICAL_DAMAGE'

    final_damage = incoming_damage - reduction
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'incoming_damage': incoming_damage,
        'armor_points': armor_points,
        'damage_category': category,
        'attack_passes_through_armor': attack_passes_through_armor,
        'armor_reduction': reduction,
        'final_damage': final_damage,
        'reason': reason,
        'automatic_armor_selection': False,
        'randomness_generated': False,
        'state_mutated': False,
    }
