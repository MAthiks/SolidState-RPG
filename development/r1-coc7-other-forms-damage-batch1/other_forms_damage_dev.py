from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
WOUNDS_DIR = ROOT / 'development' / 'r1-coc7-wounds-healing-batch1'
for path in (RULES_DIR, WOUNDS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import wounds_healing_dev as wounds  # noqa: E402

MODULE_ID = 'COC7_OTHER_FORMS_DAMAGE_R1_BATCH1_DEV_V1'
PARENT_RANGED_THROWN_ARMOR_MODULE_ID = 'COC7_RANGED_THROWN_ARMOR_R1_BATCH1_DEV_V1'
WOUNDS_MODULE_ID = wounds.MODULE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'

SEVERITY_DICE = {
    'MINOR': (1, 3),
    'MODERATE': (1, 6),
    'SEVERE': (1, 10),
    'DEADLY': (2, 10),
    'TERMINAL': (4, 10),
    'SPLAT': (8, 10),
}
POISON_SYMPTOM_MODES = {
    'KEEP_ACTING',
    'PENALTY_DIE',
    'INCREASE_DIFFICULTY',
    'INCAPACITATED',
}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _severity(severity: str) -> dict:
    key = str(severity).upper().strip()
    profile = SEVERITY_DICE.get(key)
    if profile is None:
        return {'status': 'BLOCKED', 'code': 'DAMAGE_SEVERITY_UNMATERIALIZED'}
    return {
        'status': 'RESOLVED',
        'severity': key,
        'dice_count': profile[0],
        'die_sides': profile[1],
        'expression': f'{profile[0]}D{profile[1]}',
    }


def _recorded_damage(profile: dict, recorded_dice: list[int]) -> dict:
    if not isinstance(profile, dict) or profile.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'DAMAGE_PROFILE_UNRESOLVED'}
    if not isinstance(recorded_dice, list) or len(recorded_dice) != profile['dice_count']:
        return {'status': 'BLOCKED', 'code': 'RECORDED_DAMAGE_DICE_COUNT_MISMATCH'}
    if any(not _valid_int(v, 1, profile['die_sides']) for v in recorded_dice):
        return {'status': 'BLOCKED', 'code': 'RECORDED_DAMAGE_DIE_INVALID'}
    return {
        'status': 'RESOLVED',
        'recorded_dice': list(recorded_dice),
        'damage': sum(recorded_dice),
        'randomness_generated': False,
    }


def damage_profile(*, severity: str) -> dict:
    result = _severity(severity)
    if result.get('status') != 'RESOLVED':
        return result
    return {
        **result,
        'module_id': MODULE_ID,
        'severity_selected_automatically': False,
        'randomness_generated': False,
    }


def resolve_other_damage(
    *,
    severity: str,
    recorded_dice: list[int],
    max_hp: int,
    current_hp: int,
    had_major_wound: bool = False,
    exposure_continues: bool = False,
) -> dict:
    if not isinstance(exposure_continues, bool):
        return {'status': 'BLOCKED', 'code': 'EXPOSURE_CONTINUES_FLAG_INVALID'}
    profile = _severity(severity)
    if profile.get('status') != 'RESOLVED':
        return profile
    damage = _recorded_damage(profile, recorded_dice)
    if damage.get('status') != 'RESOLVED':
        return damage
    assessed = wounds.assess_damage(
        max_hp=max_hp,
        current_hp=current_hp,
        damage=damage['damage'],
        had_major_wound=had_major_wound,
    )
    if assessed.get('status') != 'RESOLVED':
        return assessed
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'wounds_module_id': WOUNDS_MODULE_ID,
        'severity': profile['severity'],
        'damage_expression': profile['expression'],
        'recorded_dice': damage['recorded_dice'],
        'damage': damage['damage'],
        'wound_state': assessed,
        'exposure_continues': exposure_continues,
        'damage_again_next_round_if_exposure_continues': exposure_continues,
        'severity_selected_automatically': False,
        'randomness_generated': False,
    }


def asphyxiation_con_check(
    *,
    con_value: int,
    units: int,
    tens: list[int],
    physically_exerting: bool,
    can_breathe: bool,
    failure_already_active: bool = False,
) -> dict:
    for flag in (physically_exerting, can_breathe, failure_already_active):
        if not isinstance(flag, bool):
            return {'status': 'BLOCKED', 'code': 'ASPHYXIATION_FLAG_INVALID'}
    if can_breathe:
        return {
            'status': 'RESOLVED',
            'asphyxiation_active': False,
            'con_check_required': False,
            'failure_active_after': False,
            'damage_on_subsequent_rounds': False,
            'randomness_generated': False,
        }
    if failure_already_active:
        return {
            'status': 'RESOLVED',
            'asphyxiation_active': True,
            'con_check_required': False,
            'failure_active_after': True,
            'damage_on_subsequent_rounds': True,
            'randomness_generated': False,
        }
    if not _valid_int(con_value, 0, 100):
        return {'status': 'BLOCKED', 'code': 'CON_VALUE_INVALID'}
    difficulty = 'HARD' if physically_exerting else 'REGULAR'
    try:
        roll = core_rules.percentile_from_digits(units, tens, 0)
        judged = core_rules.meets_difficulty(con_value, roll, difficulty)
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    failed = not judged['success']
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'asphyxiation_active': True,
        'con_check_required': True,
        'difficulty': difficulty,
        'roll': roll,
        'success_level': judged['level'],
        'success': judged['success'],
        'failure_active_after': failed,
        'damage_on_subsequent_rounds': failed,
        'first_failed_check_does_not_roll_damage_in_same_resolution': failed,
        'randomness_generated': False,
    }


def resolve_asphyxiation_damage_round(
    *,
    severity: str,
    recorded_dice: list[int],
    max_hp: int,
    current_hp: int,
    failure_active: bool,
    can_breathe: bool,
) -> dict:
    if not isinstance(failure_active, bool) or not isinstance(can_breathe, bool):
        return {'status': 'BLOCKED', 'code': 'ASPHYXIATION_FLAG_INVALID'}
    if not _valid_int(max_hp, 1) or not _valid_int(current_hp, 0, max_hp):
        return {'status': 'BLOCKED', 'code': 'HP_INPUT_INVALID'}
    if can_breathe:
        return {
            'status': 'RESOLVED',
            'damage': 0,
            'current_hp': current_hp,
            'dead': False,
            'failure_active_after': False,
            'major_wound_rule_ignored': True,
            'randomness_generated': False,
        }
    if not failure_active:
        return {'status': 'BLOCKED', 'code': 'ASPHYXIATION_DAMAGE_REQUIRES_ACTIVE_FAILED_CON'}
    profile = _severity(severity)
    if profile.get('status') != 'RESOLVED':
        return profile
    damage = _recorded_damage(profile, recorded_dice)
    if damage.get('status') != 'RESOLVED':
        return damage
    hp_after = max(0, current_hp - damage['damage'])
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'severity': profile['severity'],
        'damage_expression': profile['expression'],
        'recorded_dice': damage['recorded_dice'],
        'damage': damage['damage'],
        'current_hp': hp_after,
        'dead': hp_after == 0,
        'dying': False,
        'major_wound_rule_ignored': True,
        'failure_active_after': hp_after > 0,
        'next_damage_round_required_if_unable_to_breathe': hp_after > 0,
        'randomness_generated': False,
    }


def resolve_poison_con(
    *,
    con_value: int,
    units: int,
    tens: list[int],
    base_damage: int,
) -> dict:
    if not _valid_int(con_value, 0, 100):
        return {'status': 'BLOCKED', 'code': 'CON_VALUE_INVALID'}
    if not _valid_int(base_damage, 0):
        return {'status': 'BLOCKED', 'code': 'POISON_BASE_DAMAGE_INVALID'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, 0)
        level = core_rules.success_level(con_value, roll)
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    extreme_or_better = level in {'EXTREME', 'CRITICAL'}
    if extreme_or_better and base_damage % 2:
        return {
            'status': 'BLOCKED',
            'code': 'ODD_POISON_DAMAGE_HALVING_ROUNDING_UNMATERIALIZED',
            'base_damage': base_damage,
            'success_level': level,
            'critical_shakeoff_option_available': level == 'CRITICAL',
        }
    applied = base_damage // 2 if extreme_or_better else base_damage
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'roll': roll,
        'success_level': level,
        'extreme_con_halves_damage': extreme_or_better,
        'base_damage': base_damage,
        'applied_damage': applied,
        'critical_shakeoff_option_available': level == 'CRITICAL',
        'critical_shakeoff_applied_automatically': False,
        'poison_symptoms_selected_automatically': False,
        'randomness_generated': False,
    }


def poison_symptom_plan(*, mode: str) -> dict:
    key = str(mode).upper().strip()
    if key not in POISON_SYMPTOM_MODES:
        return {'status': 'BLOCKED', 'code': 'POISON_SYMPTOM_MODE_KEEPER_SELECTION_REQUIRED'}
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'mode': key,
        'keeper_selected': True,
        'automatic_symptom_selection': False,
        'penalty_dice': 1 if key == 'PENALTY_DIE' else 0,
        'increase_difficulty_one_step': key == 'INCREASE_DIFFICULTY',
        'can_act': key != 'INCAPACITATED',
        'randomness_generated': False,
    }
