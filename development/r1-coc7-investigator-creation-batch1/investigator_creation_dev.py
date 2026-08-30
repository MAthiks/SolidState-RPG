from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
AGING_DIR = ROOT / 'development' / 'r1-coc7-investigator-aging-batch2'
REGISTRY_DIR = ROOT / 'development' / 'r1-coc7-registry-batch5'
for path in (RULES_DIR, AGING_DIR, REGISTRY_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import investigator_aging_dev as aging  # noqa: E402
import registry_batch5_dev as registry  # noqa: E402

MODULE_ID = 'COC7_INVESTIGATOR_CREATION_R1_BATCH1_DEV_V1'
PARENT_RULES_TEST_CHAIN = 1688
OCCUPATION_REGISTRY_TEST_CHAIN = 626
INVESTIGATOR_SOURCE_ID = 'COC7_INVESTIGATOR'
INVESTIGATOR_SHA256 = 'de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
OCCUPATION_REGISTRY_ID = registry.REGISTRY_ID
AGING_MODULE_ID = aging.MODULE_ID

THREE_D6_KEYS = ('STR', 'CON', 'DEX', 'APP', 'POW', 'LUCK')
TWO_D6_PLUS_6_KEYS = ('SIZ', 'INT', 'EDU')
CHARACTERISTIC_KEYS = ('STR', 'CON', 'SIZ', 'DEX', 'APP', 'INT', 'POW', 'EDU')
ALL_GENERATION_KEYS = set(THREE_D6_KEYS) | set(TWO_D6_PLUS_6_KEYS)


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _roll_d6_values(values, count: int) -> dict:
    if not isinstance(values, list) or len(values) != count:
        return {'status': 'BLOCKED', 'code': 'RECORDED_D6_COUNT_INVALID'}
    if any(not _valid_int(v, 1, 6) for v in values):
        return {'status': 'BLOCKED', 'code': 'RECORDED_D6_VALUE_INVALID'}
    return {'status': 'RESOLVED', 'values': list(values), 'sum': sum(values)}


def generate_raw_characteristics(*, recorded_dice: dict) -> dict:
    if not isinstance(recorded_dice, dict) or set(recorded_dice) != ALL_GENERATION_KEYS:
        return {
            'status': 'BLOCKED',
            'code': 'CHARACTERISTIC_DICE_MAP_INCOMPLETE_OR_EXTRA',
            'required_keys': sorted(ALL_GENERATION_KEYS),
        }
    characteristics = {}
    audit = {}
    for key in THREE_D6_KEYS:
        checked = _roll_d6_values(recorded_dice[key], 3)
        if checked['status'] != 'RESOLVED':
            return {**checked, 'characteristic': key}
        characteristics[key] = checked['sum'] * 5
        audit[key] = {'recorded_dice': checked['values'], 'formula': '3D6_X5'}
    for key in TWO_D6_PLUS_6_KEYS:
        checked = _roll_d6_values(recorded_dice[key], 2)
        if checked['status'] != 'RESOLVED':
            return {**checked, 'characteristic': key}
        characteristics[key] = (checked['sum'] + 6) * 5
        audit[key] = {'recorded_dice': checked['values'], 'formula': '2D6_PLUS_6_X5'}
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'characteristics': {k: characteristics[k] for k in CHARACTERISTIC_KEYS},
        'luck': characteristics['LUCK'],
        'generation_audit': audit,
        'automatic_reroll': False,
        'randomness_generated': False,
    }


def _normalize_allocation(allocation, allowed_keys, exact_total: int) -> dict | None:
    if exact_total == 0:
        if allocation in (None, {}):
            return {k: 0 for k in allowed_keys}
        return None
    if not isinstance(allocation, dict):
        return None
    normalized = {str(k).upper(): v for k, v in allocation.items()}
    if set(normalized) - set(allowed_keys):
        return None
    if not all(_valid_int(v, 0) for v in normalized.values()):
        return None
    for key in allowed_keys:
        normalized.setdefault(key, 0)
    if sum(normalized.values()) != exact_total:
        return None
    return normalized


def _creation_age_profile(age: int) -> dict:
    if not _valid_int(age, 15, 90):
        return {'status': 'BLOCKED', 'code': 'CREATION_AGE_INVALID'}
    if age == 90:
        return {'status': 'BLOCKED', 'code': 'AGE_90_CREATION_MODIFIER_UNMATERIALIZED'}
    if age <= 19:
        return {'status': 'RESOLVED', 'edu_checks': 0, 'physical_loss': 5, 'physical_keys': ('STR', 'SIZ'), 'edu_loss': 5, 'app_loss': 0, 'double_luck': True}
    if age <= 39:
        return {'status': 'RESOLVED', 'edu_checks': 1, 'physical_loss': 0, 'physical_keys': ('STR', 'CON', 'DEX'), 'edu_loss': 0, 'app_loss': 0, 'double_luck': False}
    if age <= 49:
        return {'status': 'RESOLVED', 'edu_checks': 2, 'physical_loss': 5, 'physical_keys': ('STR', 'CON', 'DEX'), 'edu_loss': 0, 'app_loss': 5, 'double_luck': False}
    if age <= 59:
        return {'status': 'RESOLVED', 'edu_checks': 3, 'physical_loss': 10, 'physical_keys': ('STR', 'CON', 'DEX'), 'edu_loss': 0, 'app_loss': 10, 'double_luck': False}
    if age <= 69:
        return {'status': 'RESOLVED', 'edu_checks': 4, 'physical_loss': 20, 'physical_keys': ('STR', 'CON', 'DEX'), 'edu_loss': 0, 'app_loss': 15, 'double_luck': False}
    if age <= 79:
        return {'status': 'RESOLVED', 'edu_checks': 4, 'physical_loss': 40, 'physical_keys': ('STR', 'CON', 'DEX'), 'edu_loss': 0, 'app_loss': 20, 'double_luck': False}
    return {'status': 'RESOLVED', 'edu_checks': 4, 'physical_loss': 80, 'physical_keys': ('STR', 'CON', 'DEX'), 'edu_loss': 0, 'app_loss': 25, 'double_luck': False}


def apply_creation_age(
    *,
    raw_characteristics: dict,
    raw_luck: int,
    age: int,
    physical_allocation: dict | None,
    edu_checks: list[dict],
    second_luck_dice: list[int] | None = None,
) -> dict:
    profile = _creation_age_profile(age)
    if profile['status'] != 'RESOLVED':
        return profile
    if not isinstance(raw_characteristics, dict) or set(raw_characteristics) != set(CHARACTERISTIC_KEYS):
        return {'status': 'BLOCKED', 'code': 'RAW_CHARACTERISTICS_INVALID'}
    state = {}
    for key in CHARACTERISTIC_KEYS:
        value = raw_characteristics[key]
        if not _valid_int(value, 0, 100):
            return {'status': 'BLOCKED', 'code': 'RAW_CHARACTERISTIC_VALUE_INVALID', 'characteristic': key}
        state[key] = value
    if not _valid_int(raw_luck, 0, 100):
        return {'status': 'BLOCKED', 'code': 'RAW_LUCK_INVALID'}
    if not isinstance(edu_checks, list) or len(edu_checks) != profile['edu_checks']:
        return {'status': 'BLOCKED', 'code': 'CREATION_EDU_CHECK_COUNT_INVALID', 'required': profile['edu_checks']}

    allocation = _normalize_allocation(physical_allocation, profile['physical_keys'], profile['physical_loss'])
    if allocation is None:
        return {'status': 'BLOCKED', 'code': 'CREATION_AGE_PHYSICAL_ALLOCATION_INVALID'}
    for key, amount in allocation.items():
        if amount > state[key]:
            return {'status': 'BLOCKED', 'code': 'CREATION_AGE_NEGATIVE_CHARACTERISTIC_WOULD_RESULT', 'characteristic': key}
        state[key] -= amount

    if profile['edu_loss']:
        if profile['edu_loss'] > state['EDU']:
            return {'status': 'BLOCKED', 'code': 'CREATION_AGE_EDU_BELOW_ZERO'}
        state['EDU'] -= profile['edu_loss']
    if profile['app_loss']:
        if profile['app_loss'] > state['APP']:
            return {'status': 'BLOCKED', 'code': 'CREATION_AGE_APP_BELOW_ZERO'}
        state['APP'] -= profile['app_loss']

    edu_audit = []
    for index, record in enumerate(edu_checks, start=1):
        if not isinstance(record, dict) or 'percentile' not in record or set(record) - {'percentile', 'gain_d10'}:
            return {'status': 'BLOCKED', 'code': 'CREATION_EDU_CHECK_RECORD_INVALID', 'check_index': index}
        result = aging.edu_age_improvement(
            current_edu=state['EDU'],
            recorded_percentile=record['percentile'],
            recorded_gain_d10=record.get('gain_d10'),
        )
        if result['status'] != 'RESOLVED':
            return {**result, 'check_index': index}
        state['EDU'] = result['EDU_after']
        edu_audit.append(result)

    luck = raw_luck
    second_luck = None
    if profile['double_luck']:
        second = _roll_d6_values(second_luck_dice, 3)
        if second['status'] != 'RESOLVED':
            return {**second, 'code': 'SECOND_LUCK_RECORDED_DICE_INVALID'}
        second_luck = second['sum'] * 5
        luck = max(raw_luck, second_luck)
    elif second_luck_dice is not None:
        return {'status': 'BLOCKED', 'code': 'SECOND_LUCK_ROLL_ONLY_FOR_AGE_15_19'}

    try:
        derived = core_rules.derived_stats(
            STR=state['STR'], CON=state['CON'], SIZ=state['SIZ'], DEX=state['DEX'], POW=state['POW'], age=age,
        )
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}

    half_fifth = {
        key: {'full': value, 'half': value // 2, 'fifth': value // 5}
        for key, value in state.items()
    }
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'age': age,
        'characteristics': state,
        'luck': luck,
        'second_luck': second_luck,
        'age_profile': profile,
        'physical_allocation': allocation,
        'edu_checks': edu_audit,
        'derived': derived,
        'half_fifth': half_fifth,
        'automatic_age_allocation': False,
        'randomness_generated': False,
    }


def creation_budgets(
    *,
    characteristics: dict,
    occupation_id: str,
    credit_rating: int,
    era: str,
    occupation_choice_characteristic: str | None = None,
) -> dict:
    if not isinstance(characteristics, dict):
        return {'status': 'BLOCKED', 'code': 'CHARACTERISTICS_REQUIRED'}
    if not _valid_int(credit_rating, 0, 99):
        return {'status': 'BLOCKED', 'code': 'CREDIT_RATING_INVALID'}
    result = registry.resolve_occupation(
        occupation_id,
        characteristics=characteristics,
        choice_characteristic=occupation_choice_characteristic,
        era=era,
    )
    if result.get('status') != 'RESOLVED':
        return {**result, 'creation_stage': 'OCCUPATION_RESOLUTION'}
    record = result['record']
    credit_range = record.get('credit_rating')
    if not isinstance(credit_range, list) or len(credit_range) != 2:
        return {'status': 'BLOCKED', 'code': 'OCCUPATION_CREDIT_RATING_RANGE_INVALID'}
    minimum, maximum = credit_range
    if not (_valid_int(minimum, 0, 99) and _valid_int(maximum, 0, 99) and minimum <= maximum):
        return {'status': 'BLOCKED', 'code': 'OCCUPATION_CREDIT_RATING_RANGE_INVALID'}
    if not minimum <= credit_rating <= maximum:
        return {
            'status': 'BLOCKED',
            'code': 'CREDIT_RATING_OUTSIDE_OCCUPATION_RANGE',
            'occupation_id': record['occupation_id'],
            'allowed_range': [minimum, maximum],
        }
    occupation_points = record.get('occupation_skill_points')
    if not _valid_int(occupation_points, 0):
        return {'status': 'BLOCKED', 'code': 'OCCUPATION_POINT_BUDGET_UNRESOLVED'}
    if credit_rating > occupation_points:
        return {'status': 'BLOCKED', 'code': 'CREDIT_RATING_EXCEEDS_OCCUPATION_POINT_BUDGET'}
    try:
        personal = core_rules.personal_interest_points(characteristics['INT'])
    except (KeyError, ValueError):
        return {'status': 'BLOCKED', 'code': 'PERSONAL_INTEREST_INT_INVALID'}
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'occupation_registry_id': OCCUPATION_REGISTRY_ID,
        'occupation_id': record['occupation_id'],
        'occupation_name': record['name'],
        'occupation_record': record,
        'occupation_skill_points_total': occupation_points,
        'credit_rating_selected': credit_rating,
        'credit_rating_range': [minimum, maximum],
        'occupation_points_remaining_after_credit_rating': occupation_points - credit_rating,
        'personal_interest_points_total': personal,
        'cthulhu_mythos_personal_interest_requires_keeper_exception': True,
        'automatic_occupation_selection': False,
        'automatic_credit_rating_selection': False,
    }


def creation_preflight(
    *,
    recorded_dice: dict,
    age: int,
    physical_allocation: dict | None,
    edu_checks: list[dict],
    occupation_id: str,
    credit_rating: int,
    era: str,
    second_luck_dice: list[int] | None = None,
    occupation_choice_characteristic: str | None = None,
) -> dict:
    generated = generate_raw_characteristics(recorded_dice=recorded_dice)
    if generated['status'] != 'RESOLVED':
        return {**generated, 'creation_stage': 'GENERATE_CHARACTERISTICS'}
    aged = apply_creation_age(
        raw_characteristics=generated['characteristics'],
        raw_luck=generated['luck'],
        age=age,
        physical_allocation=physical_allocation,
        edu_checks=edu_checks,
        second_luck_dice=second_luck_dice,
    )
    if aged['status'] != 'RESOLVED':
        return {**aged, 'creation_stage': 'APPLY_CREATION_AGE'}
    budgets = creation_budgets(
        characteristics=aged['characteristics'],
        occupation_id=occupation_id,
        credit_rating=credit_rating,
        era=era,
        occupation_choice_characteristic=occupation_choice_characteristic,
    )
    if budgets['status'] != 'RESOLVED':
        return {**budgets, 'creation_stage': budgets.get('creation_stage', 'CREATE_BUDGETS')}
    return {
        'status': 'READY_FOR_SKILL_ALLOCATION_BATCH2',
        'module_id': MODULE_ID,
        'generated': generated,
        'aged': aged,
        'budgets': budgets,
        'character_state_committed': False,
        'next_stage': 'OCCUPATION_AND_PERSONAL_INTEREST_SKILL_ALLOCATION_BATCH2',
        'randomness_generated': False,
        'authority_promoted': False,
    }
