from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
MELEE_DIR = ROOT / 'development' / 'r1-coc7-melee-combat-batch1'
for path in (RULES_DIR, MELEE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import melee_combat_dev as melee  # noqa: E402

MODULE_ID = 'COC7_WOUNDS_HEALING_R1_BATCH1_DEV_V1'
PARENT_MELEE_MODULE_ID = melee.MODULE_ID
FROZEN_RULES_PACKAGE_ID = core_rules.PACKAGE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
SUCCESS_LEVELS = {'REGULAR', 'HARD', 'EXTREME', 'CRITICAL'}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _resolve_percentile(*, value: int, units: int, tens: list[int], difficulty: str = 'REGULAR', net_bonus: int = 0) -> dict:
    if not _valid_int(value, 0, 100):
        return {'status': 'BLOCKED', 'code': 'SKILL_OR_CHARACTERISTIC_INVALID'}
    if difficulty not in {'REGULAR', 'HARD', 'EXTREME'}:
        return {'status': 'BLOCKED', 'code': 'DIFFICULTY_INVALID'}
    if not _valid_int(net_bonus, -2, 2):
        return {'status': 'BLOCKED', 'code': 'BONUS_PENALTY_OUT_OF_RANGE'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, net_bonus)
        judged = core_rules.meets_difficulty(value, roll, difficulty)
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    return {
        'status': 'RESOLVED',
        'roll': roll,
        'level': judged['level'],
        'success': judged['success'],
        'difficulty': difficulty,
        'net_bonus': net_bonus,
    }


def assess_damage(*, max_hp: int, current_hp: int, damage: int, had_major_wound: bool = False) -> dict:
    if not isinstance(had_major_wound, bool):
        return {'status': 'BLOCKED', 'code': 'MAJOR_WOUND_FLAG_INVALID'}
    try:
        base = core_rules.classify_damage(
            max_hp=max_hp,
            current_hp=current_hp,
            damage=damage,
            had_major_wound=had_major_wound,
        )
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}

    newly_major_attack = damage * 2 >= max_hp
    instant_death = damage > max_hp
    result = {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'max_hp': max_hp,
        'previous_hp': current_hp,
        'damage': damage,
        'current_hp': base['current_hp'],
        'major_wound': base['major_wound'],
        'major_wound_inflicted_by_this_attack': newly_major_attack,
        'prone': newly_major_attack and not instant_death,
        'unconscious': base['unconscious'],
        'dying': base['dying'],
        'dead': base['status'] == 'DEAD',
        'con_check_required_to_remain_conscious': bool(base.get('requires_con_for_major_wound', False)),
        'negative_hp_recorded': False,
    }
    if result['dead']:
        result['triage'] = 'DEAD'
    elif result['dying']:
        result['triage'] = 'DYING'
    elif result['current_hp'] == 0:
        result['triage'] = 'UNCONSCIOUS_REGULAR_DAMAGE' if not result['major_wound'] else 'DYING'
    elif result['major_wound']:
        result['triage'] = 'MAJOR_WOUND'
    else:
        result['triage'] = 'REGULAR_DAMAGE'
    return result


def resolve_major_wound_con(*, con_value: int, units: int, tens: list[int]) -> dict:
    check = _resolve_percentile(value=con_value, units=units, tens=tens, difficulty='REGULAR')
    if check.get('status') != 'RESOLVED':
        return check
    return {
        'status': 'RESOLVED',
        'roll': check['roll'],
        'success_level': check['level'],
        'remains_conscious': check['success'],
        'unconscious': not check['success'],
        'randomness_generated': False,
    }


def first_aid_plan(
    *,
    hours_since_damage: float,
    previous_attempts: int = 0,
    successful_treatment_already: bool = False,
    dying: bool = False,
    physiology: str = 'HUMAN',
) -> dict:
    if not isinstance(hours_since_damage, (int, float)) or isinstance(hours_since_damage, bool) or hours_since_damage < 0:
        return {'status': 'BLOCKED', 'code': 'HOURS_SINCE_DAMAGE_INVALID'}
    if not _valid_int(previous_attempts, 0):
        return {'status': 'BLOCKED', 'code': 'PREVIOUS_ATTEMPTS_INVALID'}
    if not isinstance(successful_treatment_already, bool) or not isinstance(dying, bool):
        return {'status': 'BLOCKED', 'code': 'FIRST_AID_FLAG_INVALID'}
    if physiology != 'HUMAN':
        return {'status': 'BLOCKED', 'code': 'ALIEN_OR_UNFAMILIAR_PHYSIOLOGY_DIFFICULTY_UNMATERIALIZED'}
    if successful_treatment_already and not dying:
        return {'status': 'BLOCKED', 'code': 'FIRST_AID_SUCCESS_ALREADY_USED_FOR_INJURY'}
    if not dying and hours_since_damage > 1:
        return {'status': 'BLOCKED', 'code': 'FIRST_AID_WINDOW_EXPIRED'}

    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'difficulty': 'REGULAR',
        'dying': dying,
        'max_helpers': 2,
        'pushed_roll_required': previous_attempts >= 1 and not dying,
        'pushed_roll_exempt_for_dying': dying,
        'normal_recovery_hp': 0 if dying else 1,
        'temporary_stabilization_hp': 1 if dying else 0,
    }


def resolve_first_aid(*, plan: dict, helpers: list[dict], pushed_roll: bool = False) -> dict:
    if not isinstance(plan, dict) or plan.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'FIRST_AID_PLAN_UNRESOLVED'}
    if not isinstance(pushed_roll, bool):
        return {'status': 'BLOCKED', 'code': 'PUSHED_ROLL_FLAG_INVALID'}
    if plan['pushed_roll_required'] and not pushed_roll:
        return {'status': 'BLOCKED', 'code': 'PUSHED_FIRST_AID_REQUIRED'}
    if plan['dying'] and pushed_roll:
        return {'status': 'BLOCKED', 'code': 'DYING_FIRST_AID_REPEAT_IS_NOT_PUSHED'}
    if not isinstance(helpers, list) or not 1 <= len(helpers) <= plan['max_helpers']:
        return {'status': 'BLOCKED', 'code': 'FIRST_AID_HELPER_COUNT_INVALID'}

    checks = []
    for helper in helpers:
        if not isinstance(helper, dict) or not {'skill_value', 'units', 'tens'} <= set(helper):
            return {'status': 'BLOCKED', 'code': 'FIRST_AID_HELPER_ROLL_MISSING'}
        check = _resolve_percentile(
            value=helper['skill_value'],
            units=helper['units'],
            tens=helper['tens'],
            difficulty='REGULAR',
        )
        if check.get('status') != 'RESOLVED':
            return check
        checks.append(check)

    success = any(check['success'] for check in checks)
    pushed_failure = pushed_roll and not success
    if plan['dying']:
        return {
            'status': 'RESOLVED',
            'success': success,
            'checks': checks,
            'hp_recovery': 0,
            'temporary_hp': 1 if success else 0,
            'stabilized': success,
            'next_con_check': 'END_OF_EACH_HOUR' if success else 'END_OF_NEXT_ROUND_IF_SURVIVES',
            'repeat_first_aid_next_round_if_alive': not success,
            'pushed_failure_keeper_consequence_required': False,
            'randomness_generated': False,
        }
    return {
        'status': 'RESOLVED',
        'success': success,
        'checks': checks,
        'hp_recovery': 1 if success else 0,
        'rouse_unconscious_possible': success,
        'next_attempt_pushed': not success,
        'pushed_failure_keeper_consequence_required': pushed_failure,
        'randomness_generated': False,
    }


def medicine_plan(
    *,
    same_day: bool,
    successful_treatment_already: bool = False,
    dying: bool = False,
    first_aid_stabilized: bool = False,
    major_wound: bool = False,
    hospital_auto_success_authorized: bool = False,
) -> dict:
    for flag in (same_day, successful_treatment_already, dying, first_aid_stabilized, major_wound, hospital_auto_success_authorized):
        if not isinstance(flag, bool):
            return {'status': 'BLOCKED', 'code': 'MEDICINE_FLAG_INVALID'}
    if successful_treatment_already:
        return {'status': 'BLOCKED', 'code': 'MEDICINE_SUCCESS_ALREADY_USED_FOR_INJURY'}
    if dying and not first_aid_stabilized:
        return {'status': 'BLOCKED', 'code': 'DYING_REQUIRES_FIRST_AID_STABILIZATION_BEFORE_MEDICINE'}

    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'difficulty': 'REGULAR' if same_day else 'HARD',
        'minimum_treatment_hours': 1,
        'dying': dying,
        'major_wound': major_wound,
        'automatic_success': hospital_auto_success_authorized,
        'hospital_auto_success_explicitly_authorized': hospital_auto_success_authorized,
        'recovery_die': '1D3',
    }


def resolve_medicine(
    *,
    plan: dict,
    recovery_d3: int | None,
    skill_value: int | None = None,
    units: int | None = None,
    tens: list[int] | None = None,
    pushed_roll: bool = False,
) -> dict:
    if not isinstance(plan, dict) or plan.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'MEDICINE_PLAN_UNRESOLVED'}
    if not isinstance(pushed_roll, bool):
        return {'status': 'BLOCKED', 'code': 'PUSHED_ROLL_FLAG_INVALID'}

    if plan['automatic_success']:
        success = True
        level = 'AUTO_SUCCESS_KEEPER_AUTHORIZED'
        roll = None
    else:
        if skill_value is None or units is None or tens is None:
            return {'status': 'BLOCKED', 'code': 'MEDICINE_ROLL_REQUIRED'}
        check = _resolve_percentile(
            value=skill_value,
            units=units,
            tens=tens,
            difficulty=plan['difficulty'],
        )
        if check.get('status') != 'RESOLVED':
            return check
        success = check['success']
        level = check['level']
        roll = check['roll']

    if success:
        if not _valid_int(recovery_d3, 1, 3):
            return {'status': 'BLOCKED', 'code': 'RECORDED_D3_REQUIRED_ON_MEDICINE_SUCCESS'}
        return {
            'status': 'RESOLVED',
            'success': True,
            'roll': roll,
            'success_level': level,
            'hp_recovery': recovery_d3,
            'dying_cleared': plan['dying'],
            'major_wound_weekly_bonus_die': 1 if plan['major_wound'] else 0,
            'pushed_failure_keeper_consequence_required': False,
            'patient_dies_on_pushed_failure': False,
            'randomness_generated': False,
        }

    pushed_failure = pushed_roll
    return {
        'status': 'RESOLVED',
        'success': False,
        'roll': roll,
        'success_level': level,
        'hp_recovery': 0,
        'dying_cleared': False,
        'major_wound_weekly_bonus_die': 0,
        'push_available': not pushed_roll,
        'pushed_failure_keeper_consequence_required': pushed_failure,
        'patient_dies_on_pushed_failure': pushed_failure and plan['dying'],
        'randomness_generated': False,
    }


def dying_con_check(*, phase: str, con_value: int, units: int, tens: list[int]) -> dict:
    if phase not in {'DYING_ROUNDLY', 'STABILIZED_HOURLY'}:
        return {'status': 'BLOCKED', 'code': 'DYING_CON_PHASE_INVALID'}
    check = _resolve_percentile(value=con_value, units=units, tens=tens, difficulty='REGULAR')
    if check.get('status') != 'RESOLVED':
        return check
    if phase == 'DYING_ROUNDLY':
        return {
            'status': 'RESOLVED',
            'phase': phase,
            'roll': check['roll'],
            'success_level': check['level'],
            'survives': check['success'],
            'dead': not check['success'],
            'remains_dying': check['success'],
            'next_check': 'END_OF_NEXT_ROUND' if check['success'] else None,
            'randomness_generated': False,
        }
    return {
        'status': 'RESOLVED',
        'phase': phase,
        'roll': check['roll'],
        'success_level': check['level'],
        'stays_stabilized': check['success'],
        'temporary_hp_lost': 0 if check['success'] else 1,
        'returns_to_dying_roundly': not check['success'],
        'next_check': 'END_OF_NEXT_HOUR' if check['success'] else 'END_OF_NEXT_ROUND',
        'randomness_generated': False,
    }


def regular_damage_recovery(*, max_hp: int, current_hp: int, days: int, major_wound: bool) -> dict:
    if not _valid_int(max_hp, 1) or not _valid_int(current_hp, 0, max_hp) or not _valid_int(days, 0) or not isinstance(major_wound, bool):
        return {'status': 'BLOCKED', 'code': 'REGULAR_RECOVERY_INPUT_INVALID'}
    if major_wound:
        return {'status': 'BLOCKED', 'code': 'MAJOR_WOUND_REQUIRES_WEEKLY_RECOVERY'}
    new_hp = min(max_hp, current_hp + days)
    return {
        'status': 'RESOLVED',
        'hp_recovered': new_hp - current_hp,
        'current_hp': new_hp,
        'fully_healed': new_hp == max_hp,
        'unconscious_from_zero_hp': new_hp == 0,
        'randomness_generated': False,
    }


def weekly_medical_care_modifier(
    *,
    medicine_skill: int | None = None,
    units: int | None = None,
    tens: list[int] | None = None,
    hospital_auto_success_authorized: bool = False,
) -> dict:
    if not isinstance(hospital_auto_success_authorized, bool):
        return {'status': 'BLOCKED', 'code': 'HOSPITAL_AUTO_FLAG_INVALID'}
    if hospital_auto_success_authorized:
        return {'status': 'RESOLVED', 'modifier': 1, 'care_effective': True, 'medicine_fumble': False, 'roll': None}
    if medicine_skill is None or units is None or tens is None:
        return {'status': 'BLOCKED', 'code': 'WEEKLY_MEDICINE_ROLL_REQUIRED'}
    check = _resolve_percentile(value=medicine_skill, units=units, tens=tens, difficulty='REGULAR')
    if check.get('status') != 'RESOLVED':
        return check
    fumble = check['level'] == 'FUMBLE'
    modifier = 1 if check['success'] else (-1 if fumble else 0)
    return {
        'status': 'RESOLVED',
        'modifier': modifier,
        'care_effective': check['success'],
        'medicine_fumble': fumble,
        'roll': check['roll'],
        'success_level': check['level'],
    }


def major_wound_recovery_plan(
    *,
    max_hp: int,
    current_hp: int,
    major_wound: bool,
    complete_rest: bool,
    medical_care_modifier: int = 0,
    poor_environment_and_insufficient_rest: bool = False,
) -> dict:
    if not _valid_int(max_hp, 1) or not _valid_int(current_hp, 0, max_hp) or not isinstance(major_wound, bool):
        return {'status': 'BLOCKED', 'code': 'MAJOR_RECOVERY_INPUT_INVALID'}
    if not isinstance(complete_rest, bool) or not isinstance(poor_environment_and_insufficient_rest, bool):
        return {'status': 'BLOCKED', 'code': 'MAJOR_RECOVERY_FLAG_INVALID'}
    if medical_care_modifier not in {-1, 0, 1}:
        return {'status': 'BLOCKED', 'code': 'MEDICAL_CARE_MODIFIER_INVALID'}
    if not major_wound:
        return {'status': 'BLOCKED', 'code': 'MAJOR_WOUND_MARKER_NOT_SET'}

    raw = (1 if complete_rest else 0) + medical_care_modifier - (1 if poor_environment_and_insufficient_rest else 0)
    if raw < -2 or raw > 2:
        return {'status': 'BLOCKED', 'code': 'RECOVERY_MODIFIER_OUT_OF_MATERIALIZED_RANGE', 'raw_net_bonus': raw}
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'max_hp': max_hp,
        'current_hp': current_hp,
        'frequency': 'WEEKLY',
        'net_bonus': raw,
        'complete_rest_bonus': 1 if complete_rest else 0,
        'medical_care_modifier': medical_care_modifier,
        'poor_environment_penalty': 1 if poor_environment_and_insufficient_rest else 0,
    }


def resolve_major_wound_recovery(
    *,
    plan: dict,
    con_value: int,
    units: int,
    tens: list[int],
    recorded_d3: list[int],
) -> dict:
    if not isinstance(plan, dict) or plan.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'MAJOR_WOUND_RECOVERY_PLAN_UNRESOLVED'}
    check = _resolve_percentile(
        value=con_value,
        units=units,
        tens=tens,
        difficulty='REGULAR',
        net_bonus=plan['net_bonus'],
    )
    if check.get('status') != 'RESOLVED':
        return check
    level = check['level']

    if level == 'FUMBLE':
        if recorded_d3:
            return {'status': 'BLOCKED', 'code': 'D3_NOT_USED_ON_RECOVERY_FUMBLE'}
        return {
            'status': 'RESOLVED',
            'roll': check['roll'],
            'success_level': level,
            'hp_recovered': 0,
            'current_hp': plan['current_hp'],
            'major_wound_cleared': False,
            'complication_keeper_selection_required': True,
            'randomness_generated': False,
        }
    if level == 'FAILURE':
        if recorded_d3:
            return {'status': 'BLOCKED', 'code': 'D3_NOT_USED_ON_RECOVERY_FAILURE'}
        return {
            'status': 'RESOLVED',
            'roll': check['roll'],
            'success_level': level,
            'hp_recovered': 0,
            'current_hp': plan['current_hp'],
            'major_wound_cleared': False,
            'complication_keeper_selection_required': False,
            'randomness_generated': False,
        }

    dice_needed = 2 if level in {'EXTREME', 'CRITICAL'} else 1
    if not isinstance(recorded_d3, list) or len(recorded_d3) != dice_needed or not all(_valid_int(x, 1, 3) for x in recorded_d3):
        return {'status': 'BLOCKED', 'code': 'RECORDED_D3_COUNT_OR_VALUE_INVALID', 'dice_needed': dice_needed}
    recovered = sum(recorded_d3)
    new_hp = min(plan['max_hp'], plan['current_hp'] + recovered)
    clear_by_extreme = level in {'EXTREME', 'CRITICAL'}
    clear_by_hp = new_hp * 2 >= plan['max_hp']
    return {
        'status': 'RESOLVED',
        'roll': check['roll'],
        'success_level': level,
        'hp_recovered': new_hp - plan['current_hp'],
        'current_hp': new_hp,
        'major_wound_cleared': clear_by_extreme or clear_by_hp,
        'clear_reason': 'EXTREME_RECOVERY' if clear_by_extreme else ('HALF_OR_MORE_MAX_HP' if clear_by_hp else None),
        'complication_keeper_selection_required': False,
        'randomness_generated': False,
    }
