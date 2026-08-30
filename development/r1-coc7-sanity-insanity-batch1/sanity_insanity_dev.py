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

MODULE_ID = 'COC7_SANITY_INSANITY_R1_BATCH1_DEV_V1'
PARENT_WOUNDS_MODULE_ID = wounds.MODULE_ID
FROZEN_RULES_PACKAGE_ID = core_rules.PACKAGE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
INSANITY_TYPES = {'TEMPORARY', 'INDEFINITE'}
BOUT_MODES = {'REAL_TIME', 'SUMMARY'}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _san_roll(current_san: int, units: int, tens: list[int]) -> dict:
    if not _valid_int(current_san, 1, 99):
        return {'status': 'BLOCKED', 'code': 'CURRENT_SAN_INVALID_OR_PERMANENTLY_INSANE'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, 0)
        level = core_rules.success_level(current_san, roll)
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    return {
        'status': 'RESOLVED',
        'roll': roll,
        'success_level': level,
        'success': level not in {'FAILURE', 'FUMBLE'},
    }


def maximum_sanity(*, cthulhu_mythos: int, current_san: int | None = None) -> dict:
    if not _valid_int(cthulhu_mythos, 0, 99):
        return {'status': 'BLOCKED', 'code': 'CTHULHU_MYTHOS_INVALID'}
    maximum = 99 - cthulhu_mythos
    result = {'status': 'RESOLVED', 'cthulhu_mythos': cthulhu_mythos, 'maximum_san': maximum}
    if current_san is not None:
        if not _valid_int(current_san, 0, 99):
            return {'status': 'BLOCKED', 'code': 'CURRENT_SAN_INVALID'}
        result['current_san'] = min(current_san, maximum)
        result['san_was_capped'] = current_san > maximum
    return result


def sanity_roll(
    *,
    current_san: int,
    units: int | None,
    tens: list[int] | None,
    recorded_success_loss: int,
    recorded_failure_loss: int,
    failure_loss_maximum: int,
    in_bout_of_madness: bool = False,
) -> dict:
    if not isinstance(in_bout_of_madness, bool):
        return {'status': 'BLOCKED', 'code': 'BOUT_FLAG_INVALID'}
    for value in (recorded_success_loss, recorded_failure_loss, failure_loss_maximum):
        if not _valid_int(value, 0):
            return {'status': 'BLOCKED', 'code': 'SAN_LOSS_VALUE_INVALID'}
    if recorded_failure_loss > failure_loss_maximum:
        return {'status': 'BLOCKED', 'code': 'RECORDED_FAILURE_LOSS_EXCEEDS_SOURCE_MAXIMUM'}
    if in_bout_of_madness:
        return {
            'status': 'RESOLVED',
            'immune_to_san_loss': True,
            'san_roll_required': False,
            'roll': None,
            'san_loss': 0,
            'failed_san_roll': False,
            'involuntary_action_keeper_choice_required': False,
            'randomness_generated': False,
        }
    if units is None or tens is None:
        return {'status': 'BLOCKED', 'code': 'SAN_ROLL_DIGITS_REQUIRED'}
    check = _san_roll(current_san, units, tens)
    if check.get('status') != 'RESOLVED':
        return check
    if check['success']:
        loss = recorded_success_loss
    elif check['success_level'] == 'FUMBLE':
        loss = failure_loss_maximum
    else:
        loss = recorded_failure_loss
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'immune_to_san_loss': False,
        'san_roll_required': True,
        'roll': check['roll'],
        'success_level': check['success_level'],
        'success': check['success'],
        'san_loss': loss,
        'failed_san_roll': not check['success'],
        'involuntary_action_keeper_choice_required': not check['success'],
        'luck_spend_allowed': False,
        'bonus_penalty_dice_allowed': False,
        'randomness_generated': False,
    }


def apply_sanity_loss(
    *,
    current_san: int,
    loss: int,
    sanity_start_of_day: int,
    daily_loss_before: int = 0,
    already_underlying_insanity: bool = False,
) -> dict:
    if not _valid_int(current_san, 0, 99) or not _valid_int(loss, 0) or not _valid_int(sanity_start_of_day, 1, 99) or not _valid_int(daily_loss_before, 0):
        return {'status': 'BLOCKED', 'code': 'SANITY_STATE_INPUT_INVALID'}
    if not isinstance(already_underlying_insanity, bool):
        return {'status': 'BLOCKED', 'code': 'UNDERLYING_INSANITY_FLAG_INVALID'}
    if current_san > sanity_start_of_day:
        return {'status': 'BLOCKED', 'code': 'CURRENT_SAN_EXCEEDS_DAY_START_SAN'}

    actual_loss = min(current_san, loss)
    new_san = current_san - actual_loss
    daily_loss_after = daily_loss_before + actual_loss
    daily_fifth_reached = daily_loss_after * 5 >= sanity_start_of_day

    if new_san == 0:
        state = 'PERMANENT_INSANITY'
        bout_required = False
        int_check_required = False
    elif already_underlying_insanity:
        state = 'UNDERLYING_INSANITY'
        bout_required = actual_loss > 0
        int_check_required = False
    elif daily_fifth_reached:
        state = 'INDEFINITE_INSANITY'
        bout_required = True
        int_check_required = False
    elif actual_loss >= 5:
        state = 'TEMPORARY_INSANITY_INT_CHECK_REQUIRED'
        bout_required = False
        int_check_required = True
    else:
        state = 'STABLE'
        bout_required = False
        int_check_required = False

    return {
        'status': 'RESOLVED',
        'previous_san': current_san,
        'requested_loss': loss,
        'actual_loss': actual_loss,
        'SAN': new_san,
        'sanity_start_of_day': sanity_start_of_day,
        'daily_loss_before': daily_loss_before,
        'daily_loss_after': daily_loss_after,
        'daily_fifth_reached': daily_fifth_reached,
        'state': state,
        'int_check_required': int_check_required,
        'bout_required': bout_required,
        'ceases_to_be_player_character': state == 'PERMANENT_INSANITY',
        'randomness_generated': False,
    }


def resolve_temporary_insanity_int(
    *,
    int_value: int,
    units: int,
    tens: list[int],
    recorded_duration_hours: int | None,
) -> dict:
    if not _valid_int(int_value, 1, 99):
        return {'status': 'BLOCKED', 'code': 'INT_INVALID'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, 0)
        level = core_rules.success_level(int_value, roll)
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    int_success = level not in {'FAILURE', 'FUMBLE'}
    if int_success:
        if not _valid_int(recorded_duration_hours, 1, 10):
            return {'status': 'BLOCKED', 'code': 'RECORDED_TEMPORARY_INSANITY_D10_REQUIRED'}
        return {
            'status': 'RESOLVED',
            'roll': roll,
            'success_level': level,
            'int_success': True,
            'state': 'TEMPORARY_INSANITY',
            'memory_repressed': False,
            'bout_required': True,
            'duration_hours': recorded_duration_hours,
            'randomness_generated': False,
        }
    if recorded_duration_hours is not None:
        return {'status': 'BLOCKED', 'code': 'TEMPORARY_DURATION_NOT_USED_WHEN_INT_FAILS'}
    return {
        'status': 'RESOLVED',
        'roll': roll,
        'success_level': level,
        'int_success': False,
        'state': 'NO_TEMPORARY_INSANITY',
        'memory_repressed': True,
        'bout_required': False,
        'duration_hours': None,
        'randomness_generated': False,
    }


def bout_of_madness_plan(*, insanity_type: str, mode: str, recorded_d10: int) -> dict:
    if insanity_type not in INSANITY_TYPES:
        return {'status': 'BLOCKED', 'code': 'INSANITY_TYPE_INVALID'}
    if mode not in BOUT_MODES:
        return {'status': 'BLOCKED', 'code': 'BOUT_MODE_INVALID'}
    if not _valid_int(recorded_d10, 1, 10):
        return {'status': 'BLOCKED', 'code': 'RECORDED_BOUT_D10_INVALID'}
    duration_unit = 'COMBAT_ROUNDS' if mode == 'REAL_TIME' else 'HOURS'
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'insanity_type': insanity_type,
        'mode': mode,
        'duration': recorded_d10,
        'duration_unit': duration_unit,
        'keeper_control': True,
        'player_control': False,
        'immune_to_further_san_loss': True,
        'automatic_bout_content_selection': False,
        'keeper_or_source_selection_required': True,
        'backstory_mutation_automatic': False,
        'randomness_generated': False,
    }


def end_bout(*, insanity_type: str) -> dict:
    if insanity_type not in INSANITY_TYPES:
        return {'status': 'BLOCKED', 'code': 'INSANITY_TYPE_INVALID'}
    return {
        'status': 'RESOLVED',
        'state': 'UNDERLYING_INSANITY',
        'insanity_type': insanity_type,
        'player_control': True,
        'keeper_control': False,
        'any_further_san_loss_triggers_bout': True,
    }


def reality_check(
    *,
    current_san: int,
    units: int,
    tens: list[int],
    underlying_insanity: bool,
    in_bout_of_madness: bool = False,
) -> dict:
    if not isinstance(underlying_insanity, bool) or not isinstance(in_bout_of_madness, bool):
        return {'status': 'BLOCKED', 'code': 'REALITY_CHECK_STATE_FLAG_INVALID'}
    if in_bout_of_madness:
        return {'status': 'BLOCKED', 'code': 'REALITY_CHECK_UNAVAILABLE_DURING_BOUT'}
    check = _san_roll(current_san, units, tens)
    if check.get('status') != 'RESOLVED':
        return check
    if check['success']:
        return {
            'status': 'RESOLVED',
            'roll': check['roll'],
            'success_level': check['success_level'],
            'success': True,
            'SAN': current_san,
            'san_loss': 0,
            'delusion_dispelled': True,
            'delusion_resistant_until_next_san_loss': True,
            'bout_required': False,
            'permanent_insanity': False,
            'randomness_generated': False,
        }
    new_san = max(0, current_san - 1)
    permanent = new_san == 0
    return {
        'status': 'RESOLVED',
        'roll': check['roll'],
        'success_level': check['success_level'],
        'success': False,
        'SAN': new_san,
        'san_loss': 1,
        'delusion_dispelled': False,
        'delusion_resistant_until_next_san_loss': False,
        'bout_required': underlying_insanity and not permanent,
        'permanent_insanity': permanent,
        'randomness_generated': False,
    }


def delusion_resistance_after_san_loss(*, resistant_before: bool, san_loss: int) -> dict:
    if not isinstance(resistant_before, bool) or not _valid_int(san_loss, 0):
        return {'status': 'BLOCKED', 'code': 'DELUSION_RESISTANCE_INPUT_INVALID'}
    return {
        'status': 'RESOLVED',
        'resistant': resistant_before and san_loss == 0,
        'cleared_by_san_loss': resistant_before and san_loss > 0,
    }


def mythos_related_insanity_update(
    *,
    cthulhu_mythos: int,
    current_san: int,
    first_mythos_related_insanity: bool,
) -> dict:
    if not _valid_int(cthulhu_mythos, 0, 99) or not _valid_int(current_san, 0, 99):
        return {'status': 'BLOCKED', 'code': 'MYTHOS_INSANITY_INPUT_INVALID'}
    if not isinstance(first_mythos_related_insanity, bool):
        return {'status': 'BLOCKED', 'code': 'FIRST_MYTHOS_INSANITY_FLAG_INVALID'}
    gain = 5 if first_mythos_related_insanity else 1
    new_mythos = cthulhu_mythos + gain
    if new_mythos > 99:
        return {'status': 'BLOCKED', 'code': 'CTHULHU_MYTHOS_RESULT_ABOVE_99_UNMATERIALIZED'}
    maximum = 99 - new_mythos
    capped_san = min(current_san, maximum)
    return {
        'status': 'RESOLVED',
        'cthulhu_mythos_gain': gain,
        'cthulhu_mythos': new_mythos,
        'maximum_san': maximum,
        'SAN': capped_san,
        'san_capped_by_new_maximum': capped_san < current_san,
    }


def temporary_insanity_recovery(
    *,
    elapsed_hours: float,
    duration_hours: int,
    good_night_sleep_completed: bool = False,
    safe_place: bool = False,
    heightened_tension: bool = False,
    keeper_allows_sleep_recovery: bool = False,
) -> dict:
    if not isinstance(elapsed_hours, (int, float)) or isinstance(elapsed_hours, bool) or elapsed_hours < 0:
        return {'status': 'BLOCKED', 'code': 'ELAPSED_HOURS_INVALID'}
    if not _valid_int(duration_hours, 1, 10):
        return {'status': 'BLOCKED', 'code': 'TEMPORARY_DURATION_INVALID'}
    for flag in (good_night_sleep_completed, safe_place, heightened_tension, keeper_allows_sleep_recovery):
        if not isinstance(flag, bool):
            return {'status': 'BLOCKED', 'code': 'TEMPORARY_RECOVERY_FLAG_INVALID'}
    duration_complete = elapsed_hours >= duration_hours
    sleep_recovery = (
        good_night_sleep_completed
        and safe_place
        and keeper_allows_sleep_recovery
        and not heightened_tension
    )
    recovered = duration_complete or sleep_recovery
    return {
        'status': 'RESOLVED',
        'recovered_from_temporary_insanity': recovered,
        'reason': 'DURATION_COMPLETE' if duration_complete else ('SAFE_GOOD_NIGHT_SLEEP' if sleep_recovery else None),
        'underlying_insanity_active': not recovered,
    }


def phobia_response_modifier(*, underlying_insanity: bool, direct_exposure: bool, action_category: str) -> dict:
    if not isinstance(underlying_insanity, bool) or not isinstance(direct_exposure, bool):
        return {'status': 'BLOCKED', 'code': 'PHOBIA_STATE_FLAG_INVALID'}
    if action_category not in {'FIGHT', 'FLEE', 'SANITY', 'REALITY_CHECK', 'OTHER'}:
        return {'status': 'BLOCKED', 'code': 'PHOBIA_ACTION_CATEGORY_INVALID'}
    penalty = 0
    if underlying_insanity and direct_exposure and action_category == 'OTHER':
        penalty = 1
    return {
        'status': 'RESOLVED',
        'penalty_dice': penalty,
        'fight_or_flee_exempt': action_category in {'FIGHT', 'FLEE'},
        'sanity_or_reality_exempt': action_category in {'SANITY', 'REALITY_CHECK'},
    }
