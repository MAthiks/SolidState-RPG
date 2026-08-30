from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
SANITY1_DIR = ROOT / 'development' / 'r1-coc7-sanity-insanity-batch1'
for path in (RULES_DIR, SANITY1_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import sanity_insanity_dev as sanity1  # noqa: E402

MODULE_ID = 'COC7_SANITY_TREATMENT_R1_BATCH2_DEV_V1'
PARENT_SANITY_MODULE_ID = sanity1.MODULE_ID
FROZEN_RULES_PACKAGE_ID = core_rules.PACKAGE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
CARE_TYPES = {'PRIVATE', 'INSTITUTION'}
SELF_HELP_SUPPORT_TYPES = {'KEY_CONNECTION', 'OTHER_SUPPORT', 'PHOBIA', 'MANIA', 'WOUND', 'CTHULHU_MYTHOS'}
PHOBIA_MANIA_TYPES = {'PHOBIA', 'MANIA'}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _percentile(skill_value: int, units: int, tens: list[int], net_bonus: int = 0) -> dict:
    if not _valid_int(skill_value, 1, 99):
        return {'status': 'BLOCKED', 'code': 'SKILL_OR_SAN_VALUE_INVALID'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, net_bonus)
        level = core_rules.success_level(skill_value, roll)
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    return {
        'status': 'RESOLVED',
        'roll': roll,
        'success_level': level,
        'success': level not in {'FAILURE', 'FUMBLE'},
        'fumble': level == 'FUMBLE',
        'net_bonus': net_bonus,
    }


def _max_san(cthulhu_mythos: int) -> int | None:
    if not _valid_int(cthulhu_mythos, 0, 99):
        return None
    return 99 - cthulhu_mythos


def _apply_gain(current_san: int, cthulhu_mythos: int, gain: int) -> dict:
    maximum = _max_san(cthulhu_mythos)
    if maximum is None or not _valid_int(current_san, 1, 99) or not _valid_int(gain, 0):
        return {'status': 'BLOCKED', 'code': 'SAN_GAIN_INPUT_INVALID'}
    new_san = min(maximum, current_san + gain)
    return {
        'status': 'RESOLVED',
        'previous_san': current_san,
        'requested_gain': gain,
        'actual_gain': max(0, new_san - current_san),
        'SAN': new_san,
        'maximum_san': maximum,
        'capped_at_maximum': current_san + gain > maximum,
    }


def _apply_loss(current_san: int, loss: int) -> dict:
    if not _valid_int(current_san, 1, 99) or not _valid_int(loss, 0):
        return {'status': 'BLOCKED', 'code': 'SAN_LOSS_INPUT_INVALID'}
    actual = min(current_san, loss)
    new_san = current_san - actual
    return {
        'status': 'RESOLVED',
        'previous_san': current_san,
        'requested_loss': loss,
        'actual_loss': actual,
        'SAN': new_san,
        'permanent_insanity': new_san == 0,
    }


def monthly_indefinite_care(
    *,
    care_type: str,
    current_san: int,
    cthulhu_mythos: int,
    recorded_treatment_roll: int,
    recorded_gain_d3: int | None = None,
    recorded_loss_d6: int | None = None,
    san_units: int | None = None,
    san_tens: list[int] | None = None,
    institution_rating: int = 50,
    blocked_by_prior_rebellion: bool = False,
    indefinite_insanity_active: bool = True,
) -> dict:
    if care_type not in CARE_TYPES:
        return {'status': 'BLOCKED', 'code': 'CARE_TYPE_INVALID'}
    if not isinstance(blocked_by_prior_rebellion, bool) or not isinstance(indefinite_insanity_active, bool):
        return {'status': 'BLOCKED', 'code': 'CARE_STATE_FLAG_INVALID'}
    if not indefinite_insanity_active:
        return {'status': 'BLOCKED', 'code': 'INDEFINITE_INSANITY_REQUIRED'}
    if not _valid_int(current_san, 1, 99) or _max_san(cthulhu_mythos) is None:
        return {'status': 'BLOCKED', 'code': 'CARE_SAN_STATE_INVALID'}
    if not _valid_int(recorded_treatment_roll, 1, 100):
        return {'status': 'BLOCKED', 'code': 'RECORDED_TREATMENT_D100_INVALID'}
    if care_type == 'INSTITUTION' and not _valid_int(institution_rating, 5, 95):
        return {'status': 'BLOCKED', 'code': 'INSTITUTION_RATING_INVALID'}

    if blocked_by_prior_rebellion:
        return {
            'status': 'RESOLVED',
            'module_id': MODULE_ID,
            'care_type': care_type,
            'outcome': 'PRIOR_REBELLION_BLOCKS_PROGRESS_THIS_MONTH',
            'SAN': current_san,
            'cured': False,
            'next_month_blocked': False,
            'randomness_generated': False,
        }

    if recorded_treatment_roll >= 96:
        if not _valid_int(recorded_loss_d6, 1, 6):
            return {'status': 'BLOCKED', 'code': 'RECORDED_REBELLION_D6_REQUIRED'}
        loss = _apply_loss(current_san, recorded_loss_d6)
        return {
            'status': 'RESOLVED',
            'module_id': MODULE_ID,
            'care_type': care_type,
            'outcome': 'REBELLION_OR_SERIOUS_SETBACK',
            'treatment_roll': recorded_treatment_roll,
            'SAN': loss['SAN'],
            'san_loss': loss['actual_loss'],
            'permanent_insanity': loss['permanent_insanity'],
            'cured': False,
            'next_month_blocked': not loss['permanent_insanity'],
            'randomness_generated': False,
        }

    threshold = 95 if care_type == 'PRIVATE' else institution_rating
    if recorded_treatment_roll > threshold:
        return {
            'status': 'RESOLVED',
            'module_id': MODULE_ID,
            'care_type': care_type,
            'outcome': 'NO_PROGRESS',
            'treatment_roll': recorded_treatment_roll,
            'SAN': current_san,
            'cured': False,
            'next_month_blocked': False,
            'randomness_generated': False,
        }

    if not _valid_int(recorded_gain_d3, 1, 3):
        return {'status': 'BLOCKED', 'code': 'RECORDED_CARE_D3_REQUIRED'}
    if san_units is None or san_tens is None:
        return {'status': 'BLOCKED', 'code': 'POST_CARE_SAN_ROLL_REQUIRED'}
    gain = _apply_gain(current_san, cthulhu_mythos, recorded_gain_d3)
    if gain.get('status') != 'RESOLVED':
        return gain
    check = _percentile(gain['SAN'], san_units, san_tens, 0)
    if check.get('status') != 'RESOLVED':
        return check
    cured = check['success']
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'care_type': care_type,
        'outcome': 'TREATMENT_PROGRESS_CURED' if cured else 'TREATMENT_PROGRESS_NOT_YET_CURED',
        'treatment_roll': recorded_treatment_roll,
        'recorded_gain_d3': recorded_gain_d3,
        'SAN': gain['SAN'],
        'san_gain': gain['actual_gain'],
        'maximum_san': gain['maximum_san'],
        'post_care_san_roll': check['roll'],
        'post_care_san_level': check['success_level'],
        'cured': cured,
        'next_month_retry_allowed': not cured,
        'next_month_blocked': False,
        'randomness_generated': False,
    }


def keeper_development_phase_recovery(
    *,
    indefinite_insanity_active: bool,
    at_end_of_chapter_or_scenario: bool,
    keeper_ends_insanity: bool,
) -> dict:
    for flag in (indefinite_insanity_active, at_end_of_chapter_or_scenario, keeper_ends_insanity):
        if not isinstance(flag, bool):
            return {'status': 'BLOCKED', 'code': 'DEVELOPMENT_PHASE_FLAG_INVALID'}
    recovered = indefinite_insanity_active and at_end_of_chapter_or_scenario and keeper_ends_insanity
    return {
        'status': 'RESOLVED',
        'recovered_from_indefinite_insanity': recovered,
        'indefinite_insanity_active': indefinite_insanity_active and not recovered,
        'explicit_keeper_gate_used': keeper_ends_insanity,
        'randomness_generated': False,
    }


def keeper_award(*, current_san: int, cthulhu_mythos: int, recorded_gain: int) -> dict:
    if not _valid_int(recorded_gain, 0):
        return {'status': 'BLOCKED', 'code': 'RECORDED_KEEPER_AWARD_INVALID'}
    result = _apply_gain(current_san, cthulhu_mythos, recorded_gain)
    if result.get('status') != 'RESOLVED':
        return result
    return {'status': 'RESOLVED', 'source': 'KEEPER_AWARD', **{k:v for k,v in result.items() if k!='status'}, 'randomness_generated': False}


def skill_reaches_90_award(
    *,
    current_san: int,
    cthulhu_mythos: int,
    reached_90: bool,
    recorded_2d6_total: int | None,
) -> dict:
    if not isinstance(reached_90, bool):
        return {'status': 'BLOCKED', 'code': 'REACHED_90_FLAG_INVALID'}
    if not reached_90:
        if recorded_2d6_total is not None:
            return {'status': 'BLOCKED', 'code': 'SKILL_90_AWARD_NOT_APPLICABLE'}
        return {'status': 'RESOLVED', 'source': 'SKILL_90', 'SAN': current_san, 'san_gain': 0, 'randomness_generated': False}
    if not _valid_int(recorded_2d6_total, 2, 12):
        return {'status': 'BLOCKED', 'code': 'RECORDED_2D6_TOTAL_REQUIRED'}
    result = _apply_gain(current_san, cthulhu_mythos, recorded_2d6_total)
    if result.get('status') != 'RESOLVED':
        return result
    return {'status': 'RESOLVED', 'source': 'SKILL_90', **{k:v for k,v in result.items() if k!='status'}, 'randomness_generated': False}


def psychotherapy_month(
    *,
    current_san: int,
    cthulhu_mythos: int,
    analyst_skill: int,
    units: int,
    tens: list[int],
    recorded_gain_d3: int | None = None,
    recorded_loss_d6: int | None = None,
    permanent_insanity: bool = False,
) -> dict:
    if not isinstance(permanent_insanity, bool):
        return {'status': 'BLOCKED', 'code': 'PERMANENT_INSANITY_FLAG_INVALID'}
    if permanent_insanity or current_san == 0:
        return {'status': 'BLOCKED', 'code': 'PERMANENT_INSANITY_CANNOT_PARTICIPATE'}
    if _max_san(cthulhu_mythos) is None:
        return {'status': 'BLOCKED', 'code': 'CTHULHU_MYTHOS_INVALID'}
    check = _percentile(analyst_skill, units, tens, 0)
    if check.get('status') != 'RESOLVED':
        return check
    if check['fumble']:
        if not _valid_int(recorded_loss_d6, 1, 6):
            return {'status': 'BLOCKED', 'code': 'RECORDED_PSYCHOTHERAPY_FUMBLE_D6_REQUIRED'}
        loss = _apply_loss(current_san, recorded_loss_d6)
        return {
            'status': 'RESOLVED', 'module_id': MODULE_ID, 'outcome': 'FUMBLE_SETBACK',
            'roll': check['roll'], 'success_level': check['success_level'], 'SAN': loss['SAN'],
            'san_loss': loss['actual_loss'], 'san_gain': 0, 'analyst_relationship_terminated': True,
            'permanent_insanity': loss['permanent_insanity'], 'randomness_generated': False,
        }
    if not check['success']:
        return {
            'status': 'RESOLVED', 'module_id': MODULE_ID, 'outcome': 'NO_GAIN',
            'roll': check['roll'], 'success_level': check['success_level'], 'SAN': current_san,
            'san_gain': 0, 'san_loss': 0, 'analyst_relationship_terminated': False,
            'randomness_generated': False,
        }
    if not _valid_int(recorded_gain_d3, 1, 3):
        return {'status': 'BLOCKED', 'code': 'RECORDED_PSYCHOTHERAPY_D3_REQUIRED'}
    gain = _apply_gain(current_san, cthulhu_mythos, recorded_gain_d3)
    return {
        'status': 'RESOLVED', 'module_id': MODULE_ID, 'outcome': 'SAN_GAIN',
        'roll': check['roll'], 'success_level': check['success_level'], 'SAN': gain['SAN'],
        'san_gain': gain['actual_gain'], 'san_loss': 0, 'maximum_san': gain['maximum_san'],
        'analyst_relationship_terminated': False, 'randomness_generated': False,
    }


def phobia_mania_therapy_month(
    *,
    condition_type: str,
    current_san: int,
    analyst_skill: int,
    analyst_units: int,
    analyst_tens: list[int],
    patient_units: int | None = None,
    patient_tens: list[int] | None = None,
    recorded_loss_d6: int | None = None,
) -> dict:
    if condition_type not in PHOBIA_MANIA_TYPES:
        return {'status': 'BLOCKED', 'code': 'CONDITION_TYPE_INVALID'}
    if not _valid_int(current_san, 1, 99):
        return {'status': 'BLOCKED', 'code': 'CURRENT_SAN_INVALID'}
    analyst = _percentile(analyst_skill, analyst_units, analyst_tens, 0)
    if analyst.get('status') != 'RESOLVED':
        return analyst
    if analyst['fumble']:
        if not _valid_int(recorded_loss_d6, 1, 6):
            return {'status': 'BLOCKED', 'code': 'RECORDED_THERAPY_FUMBLE_D6_REQUIRED'}
        loss = _apply_loss(current_san, recorded_loss_d6)
        return {
            'status': 'RESOLVED', 'condition_type': condition_type, 'cured': False,
            'outcome': 'ANALYST_FUMBLE', 'SAN': loss['SAN'], 'san_loss': loss['actual_loss'],
            'analyst_relationship_terminated': True, 'backstory_edit_required': False,
            'randomness_generated': False,
        }
    if not analyst['success']:
        return {
            'status': 'RESOLVED', 'condition_type': condition_type, 'cured': False,
            'outcome': 'ANALYST_FAILURE_NO_BENEFIT', 'SAN': current_san, 'san_loss': 0,
            'analyst_relationship_terminated': False, 'backstory_edit_required': False,
            'randomness_generated': False,
        }
    if patient_units is None or patient_tens is None:
        return {'status': 'BLOCKED', 'code': 'PATIENT_SAN_ROLL_REQUIRED'}
    patient = _percentile(current_san, patient_units, patient_tens, 0)
    if patient.get('status') != 'RESOLVED':
        return patient
    if patient['fumble']:
        if not _valid_int(recorded_loss_d6, 1, 6):
            return {'status': 'BLOCKED', 'code': 'RECORDED_THERAPY_FUMBLE_D6_REQUIRED'}
        loss = _apply_loss(current_san, recorded_loss_d6)
        return {
            'status': 'RESOLVED', 'condition_type': condition_type, 'cured': False,
            'outcome': 'PATIENT_SAN_FUMBLE', 'SAN': loss['SAN'], 'san_loss': loss['actual_loss'],
            'analyst_relationship_terminated': False, 'relationship_effect_unmaterialized': True,
            'backstory_edit_required': False, 'randomness_generated': False,
        }
    cured = patient['success']
    return {
        'status': 'RESOLVED', 'condition_type': condition_type, 'cured': cured,
        'outcome': 'CURED' if cured else 'PATIENT_SAN_FAILURE_NO_BENEFIT',
        'SAN': current_san, 'san_gain': 0, 'san_loss': 0,
        'backstory_edit_required': cured, 'automatic_backstory_edit': False,
        'randomness_generated': False,
    }


def self_help(
    *,
    current_san: int,
    cthulhu_mythos: int,
    support_type: str,
    units: int,
    tens: list[int],
    recorded_gain_d6: int | None = None,
    indefinite_insanity_active: bool = False,
) -> dict:
    if support_type not in SELF_HELP_SUPPORT_TYPES:
        return {'status': 'BLOCKED', 'code': 'SELF_HELP_SUPPORT_TYPE_INVALID'}
    if not isinstance(indefinite_insanity_active, bool):
        return {'status': 'BLOCKED', 'code': 'INDEFINITE_INSANITY_FLAG_INVALID'}
    if support_type in {'PHOBIA', 'MANIA', 'WOUND', 'CTHULHU_MYTHOS'}:
        return {'status': 'BLOCKED', 'code': 'SELF_HELP_SUPPORT_INELIGIBLE'}
    if not _valid_int(current_san, 1, 99) or _max_san(cthulhu_mythos) is None:
        return {'status': 'BLOCKED', 'code': 'SELF_HELP_SAN_STATE_INVALID'}
    key = support_type == 'KEY_CONNECTION'
    check = _percentile(current_san, units, tens, 1 if key else 0)
    if check.get('status') != 'RESOLVED':
        return check
    if check['success']:
        if not _valid_int(recorded_gain_d6, 1, 6):
            return {'status': 'BLOCKED', 'code': 'RECORDED_SELF_HELP_D6_REQUIRED'}
        gain = _apply_gain(current_san, cthulhu_mythos, recorded_gain_d6)
        return {
            'status': 'RESOLVED', 'module_id': MODULE_ID, 'success': True,
            'roll': check['roll'], 'success_level': check['success_level'],
            'used_key_connection': key, 'bonus_die_used': 1 if key else 0,
            'SAN': gain['SAN'], 'san_gain': gain['actual_gain'], 'san_loss': 0,
            'recovered_from_indefinite_insanity': key and indefinite_insanity_active,
            'indefinite_insanity_active': indefinite_insanity_active and not key,
            'key_connection_lost': False,
            'new_key_connection_nomination_allowed': check['success_level'] == 'CRITICAL',
            'backstory_revision_required': False, 'automatic_backstory_edit': False,
            'randomness_generated': False,
        }
    loss = _apply_loss(current_san, 1)
    return {
        'status': 'RESOLVED', 'module_id': MODULE_ID, 'success': False,
        'roll': check['roll'], 'success_level': check['success_level'],
        'used_key_connection': key, 'bonus_die_used': 1 if key else 0,
        'SAN': loss['SAN'], 'san_gain': 0, 'san_loss': loss['actual_loss'],
        'permanent_insanity': loss['permanent_insanity'],
        'recovered_from_indefinite_insanity': False,
        'indefinite_insanity_active': indefinite_insanity_active and not loss['permanent_insanity'],
        'key_connection_lost': key,
        'new_key_connection_nomination_allowed': False,
        'backstory_revision_required': True, 'automatic_backstory_edit': False,
        'randomness_generated': False,
    }
