from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT_DIR = ROOT / 'development' / 'r1-coc7-investigator-development-batch1'
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import investigator_development_dev as parent  # noqa: E402

MODULE_ID = 'COC7_INVESTIGATOR_AGING_R1_BATCH2_DEV_V1'
PARENT_DEVELOPMENT_MODULE_ID = parent.MODULE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'

PHYSICAL_KEYS = ('STR', 'CON', 'DEX')
TURNING_20_GAIN_KEYS = ('STR', 'SIZ')
REQUIRED_CHARACTERISTICS = ('STR', 'CON', 'DEX', 'SIZ', 'APP', 'EDU')


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _normalize_age_key(key):
    if isinstance(key, int) and not isinstance(key, bool):
        return key
    if isinstance(key, str) and key.isdigit():
        return int(key)
    return None


def crossed_aging_milestones(*, old_age: int, new_age: int, mode: str = 'NATURAL_OR_TIME_SKIP', keeper_confirms_magical: bool = False) -> dict:
    if not _valid_int(old_age, 0) or not _valid_int(new_age, 0) or new_age <= old_age:
        return {'status': 'BLOCKED', 'code': 'AGE_NOT_ADVANCING'}
    if mode not in {'NATURAL_OR_TIME_SKIP', 'SUDDEN_MAGICAL'}:
        return {'status': 'BLOCKED', 'code': 'AGING_MODE_INVALID'}
    if not isinstance(keeper_confirms_magical, bool):
        return {'status': 'BLOCKED', 'code': 'MAGICAL_GATE_FLAG_INVALID'}
    if mode == 'SUDDEN_MAGICAL' and not keeper_confirms_magical:
        return {'status': 'BLOCKED', 'code': 'MAGICAL_AGING_WITHOUT_KEEPER_CONFIRMATION'}
    if mode == 'NATURAL_OR_TIME_SKIP' and keeper_confirms_magical:
        return {'status': 'BLOCKED', 'code': 'MAGICAL_GATE_UNUSED'}

    milestones = []
    if mode == 'NATURAL_OR_TIME_SKIP' and old_age < 20 <= new_age:
        milestones.append(20)
    for age in (40, 50, 60, 70, 80):
        if old_age < age <= new_age:
            milestones.append(age)
    if new_age >= 90:
        first = max(90, ((old_age // 10) + 1) * 10)
        if first < 90:
            first = 90
        for age in range(first, new_age + 1, 10):
            if age >= 90 and old_age < age <= new_age:
                milestones.append(age)

    milestones = sorted(set(milestones))
    edu_milestones = [m for m in milestones if mode == 'NATURAL_OR_TIME_SKIP' and m in {20, 40, 50, 60}]
    allocation_milestones = list(milestones)
    if mode == 'SUDDEN_MAGICAL':
        allocation_milestones = [m for m in milestones if m >= 40]

    return {
        'status': 'RESOLVED',
        'mode': mode,
        'old_age': old_age,
        'new_age': new_age,
        'milestones': milestones,
        'edu_milestones': edu_milestones,
        'allocation_milestones': allocation_milestones,
        'cumulative': True,
        'randomness_generated': False,
    }


def edu_age_improvement(*, current_edu: int, recorded_percentile: int, recorded_gain_d10: int | None = None) -> dict:
    if not _valid_int(current_edu, 0, 99) or not _valid_int(recorded_percentile, 1, 100):
        return {'status': 'BLOCKED', 'code': 'EDU_IMPROVEMENT_INPUT_INVALID'}
    success = recorded_percentile > current_edu
    if success:
        if not _valid_int(recorded_gain_d10, 1, 10):
            return {'status': 'BLOCKED', 'code': 'UNRECORDED_EDU_GAIN_D10'}
        uncapped = current_edu + recorded_gain_d10
        edu_after = min(99, uncapped)
    else:
        if recorded_gain_d10 is not None:
            return {'status': 'BLOCKED', 'code': 'UNUSED_EDU_GAIN_D10'}
        uncapped = current_edu
        edu_after = current_edu
    return {
        'status': 'RESOLVED',
        'EDU_before': current_edu,
        'recorded_percentile': recorded_percentile,
        'improved': success,
        'recorded_gain_d10': recorded_gain_d10,
        'uncapped_EDU_after': uncapped,
        'EDU_after': edu_after,
        'EDU_cap': 99,
        'ordinary_skill_over_95_rule_imported': False,
        'randomness_generated': False,
    }


def _milestone_effect(age: int) -> dict:
    if age == 20:
        return {'kind': 'GAIN', 'points': 5, 'keys': TURNING_20_GAIN_KEYS, 'app_loss': 0, 'mov_loss': 0}
    if age == 40:
        return {'kind': 'LOSS', 'points': 5, 'keys': PHYSICAL_KEYS, 'app_loss': 5, 'mov_loss': 1}
    if age == 50:
        return {'kind': 'LOSS', 'points': 5, 'keys': PHYSICAL_KEYS, 'app_loss': 5, 'mov_loss': 1}
    if age == 60:
        return {'kind': 'LOSS', 'points': 10, 'keys': PHYSICAL_KEYS, 'app_loss': 5, 'mov_loss': 1}
    if age == 70:
        return {'kind': 'LOSS', 'points': 20, 'keys': PHYSICAL_KEYS, 'app_loss': 5, 'mov_loss': 1}
    if age == 80:
        return {'kind': 'LOSS', 'points': 40, 'keys': PHYSICAL_KEYS, 'app_loss': 5, 'mov_loss': 1}
    if age >= 90 and age % 10 == 0:
        return {'kind': 'LOSS', 'points': 80, 'keys': PHYSICAL_KEYS, 'app_loss': 0, 'mov_loss': 1}
    raise ValueError('AGING_MILESTONE_UNMATERIALIZED')


def _normalize_mapping_keys(mapping) -> dict | None:
    if not isinstance(mapping, dict):
        return None
    out = {}
    for key, value in mapping.items():
        normalized = _normalize_age_key(key)
        if normalized is None or normalized in out:
            return None
        out[normalized] = value
    return out


def _validate_allocation(*, allocation, allowed_keys, exact_total: int) -> dict | None:
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


def apply_aging(
    *,
    old_age: int,
    new_age: int,
    mode: str,
    current_characteristics: dict,
    current_mov: int,
    allocations: dict,
    edu_checks: dict,
    keeper_confirms_magical: bool = False,
) -> dict:
    milestone_plan = crossed_aging_milestones(
        old_age=old_age,
        new_age=new_age,
        mode=mode,
        keeper_confirms_magical=keeper_confirms_magical,
    )
    if milestone_plan['status'] != 'RESOLVED':
        return milestone_plan
    if not isinstance(current_characteristics, dict) or not _valid_int(current_mov, 0):
        return {'status': 'BLOCKED', 'code': 'AGING_STATE_INPUT_INVALID'}
    if any(key not in current_characteristics for key in REQUIRED_CHARACTERISTICS):
        return {'status': 'BLOCKED', 'code': 'AGING_CHARACTERISTICS_INCOMPLETE'}
    state = {}
    for key in REQUIRED_CHARACTERISTICS:
        value = current_characteristics[key]
        if not _valid_int(value, 0):
            return {'status': 'BLOCKED', 'code': 'AGING_CHARACTERISTIC_INVALID', 'characteristic': key}
        state[key] = value

    allocation_map = _normalize_mapping_keys(allocations)
    edu_map = _normalize_mapping_keys(edu_checks)
    if allocation_map is None or edu_map is None:
        return {'status': 'BLOCKED', 'code': 'AGING_MILESTONE_MAPPING_INVALID'}

    required_alloc = set(milestone_plan['allocation_milestones'])
    required_edu = set(milestone_plan['edu_milestones'])
    if set(allocation_map) != required_alloc:
        return {
            'status': 'BLOCKED', 'code': 'MISSING_OR_EXTRA_MILESTONE_ALLOCATION',
            'required': sorted(required_alloc), 'provided': sorted(allocation_map),
        }
    if set(edu_map) != required_edu:
        return {
            'status': 'BLOCKED', 'code': 'MISSING_OR_EXTRA_EDU_CHECK_RECORD',
            'required': sorted(required_edu), 'provided': sorted(edu_map),
        }

    mov = current_mov
    event_records = []
    any_con_or_siz_change = False
    any_str_or_siz_change = False

    for age in milestone_plan['milestones']:
        if mode == 'SUDDEN_MAGICAL' and age == 20:
            continue
        effect = _milestone_effect(age)
        allocation = _validate_allocation(
            allocation=allocation_map[age],
            allowed_keys=effect['keys'],
            exact_total=effect['points'],
        )
        if allocation is None:
            return {'status': 'BLOCKED', 'code': 'ALLOCATION_TOTAL_MISMATCH', 'milestone': age}

        before = dict(state)
        if effect['kind'] == 'GAIN':
            for key in effect['keys']:
                state[key] += allocation[key]
        else:
            for key in effect['keys']:
                if allocation[key] > state[key]:
                    return {
                        'status': 'BLOCKED', 'code': 'NEGATIVE_CHARACTERISTIC_WOULD_RESULT',
                        'milestone': age, 'characteristic': key,
                    }
                state[key] -= allocation[key]
            if effect['app_loss'] > state['APP']:
                return {'status': 'BLOCKED', 'code': 'APP_REDUCTION_BELOW_ZERO_UNMATERIALIZED', 'milestone': age}
            state['APP'] -= effect['app_loss']
            if effect['mov_loss'] > mov:
                return {'status': 'BLOCKED', 'code': 'MOV_REDUCTION_BELOW_ZERO_UNMATERIALIZED', 'milestone': age}
            mov -= effect['mov_loss']

        edu_result = None
        if age in required_edu:
            record = edu_map[age]
            if not isinstance(record, dict):
                return {'status': 'BLOCKED', 'code': 'EDU_CHECK_RECORD_INVALID', 'milestone': age}
            allowed_fields = {'percentile', 'gain_d10'}
            if set(record) - allowed_fields or 'percentile' not in record:
                return {'status': 'BLOCKED', 'code': 'EDU_CHECK_RECORD_INVALID', 'milestone': age}
            edu_result = edu_age_improvement(
                current_edu=state['EDU'],
                recorded_percentile=record['percentile'],
                recorded_gain_d10=record.get('gain_d10'),
            )
            if edu_result['status'] != 'RESOLVED':
                return {**edu_result, 'milestone': age}
            state['EDU'] = edu_result['EDU_after']

        if before['CON'] != state['CON'] or before['SIZ'] != state['SIZ']:
            any_con_or_siz_change = True
        if before['STR'] != state['STR'] or before['SIZ'] != state['SIZ']:
            any_str_or_siz_change = True

        event_records.append({
            'milestone': age,
            'effect_kind': effect['kind'],
            'allocation': allocation,
            'APP_loss': effect['app_loss'],
            'MOV_loss': effect['mov_loss'],
            'EDU_check': edu_result,
            'characteristics_after': dict(state),
            'MOV_after': mov,
        })

    derived_hp_after = (state['CON'] + state['SIZ']) // 10
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'parent_module_id': PARENT_DEVELOPMENT_MODULE_ID,
        'source_sha256': KEEPER_SHA256,
        'mode': mode,
        'old_age': old_age,
        'new_age': new_age,
        'applied_milestones': milestone_plan['milestones'],
        'events': event_records,
        'characteristics_before': {key: current_characteristics[key] for key in REQUIRED_CHARACTERISTICS},
        'characteristics_after': state,
        'MOV_before': current_mov,
        'MOV_after': mov,
        'derived_HP_after': derived_hp_after,
        'HP_recalculation_required': any_con_or_siz_change,
        'damage_bonus_build_recalculation_required': any_str_or_siz_change,
        'current_HP_reconciliation_not_automated': True,
        'automatic_stat_selection': False,
        'education_gain_suppressed_for_magical_aging': mode == 'SUDDEN_MAGICAL',
        'randomness_generated': False,
    }
