from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
PARENT_DIR = ROOT / 'development' / 'r1-coc7-finance-credit-rating-batch1'
for path in (RULES_DIR, PARENT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import finance_credit_rating_dev as finance  # noqa: E402

MODULE_ID = 'COC7_GENERAL_SKILL_RESOLUTION_R1_BATCH1_DEV_V1'
PARENT_FINANCE_MODULE_ID = finance.MODULE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'

DIFFICULTIES = {'REGULAR', 'HARD', 'EXTREME'}
PUSHABLE_CATEGORIES = {'SKILL', 'CHARACTERISTIC'}
NON_PUSHABLE_CATEGORIES = {'LUCK', 'SANITY', 'COMBAT', 'CHASE', 'DAMAGE', 'SANITY_LOSS', 'OPPOSED'}


def _blocked(code: str, **extra) -> dict:
    return {'status': 'BLOCKED', 'code': code, **extra}


def _valid_int(value, minimum=None, maximum=None) -> bool:
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _valid_bool(value) -> bool:
    return isinstance(value, bool)


def _valid_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def living_opponent_difficulty(opponent_value: int) -> dict:
    if not _valid_int(opponent_value, 0):
        return _blocked('OPPONENT_VALUE_INVALID')
    if opponent_value < 50:
        difficulty = 'REGULAR'
    elif opponent_value < 90:
        difficulty = 'HARD'
    else:
        difficulty = 'EXTREME'
    return {
        'status': 'RESOLVED',
        'opponent_value': opponent_value,
        'difficulty': difficulty,
        'randomness_generated': False,
    }


def plan_pushed_roll(
    *,
    category: str,
    original_level: str,
    same_goal_confirmed: bool,
    justification: str,
    already_pushed: bool,
    original_fumble_consequence_applied: bool = False,
    situation_changed: bool = False,
    original_difficulty: str = 'REGULAR',
    keeper_new_difficulty: str | None = None,
) -> dict:
    if category not in PUSHABLE_CATEGORIES:
        if category in NON_PUSHABLE_CATEGORIES:
            return _blocked('ROLL_CATEGORY_NOT_PUSHABLE')
        return _blocked('ROLL_CATEGORY_UNMATERIALIZED')
    if original_level not in {'FAILURE', 'FUMBLE'}:
        return _blocked('PUSH_REQUIRES_FAILED_OR_FUMBLED_ORIGINAL_ROLL')
    if not _valid_bool(same_goal_confirmed) or not same_goal_confirmed:
        return _blocked('PUSH_REQUIRES_SAME_GOAL')
    if not _valid_text(justification):
        return _blocked('PUSH_JUSTIFICATION_REQUIRED')
    if not _valid_bool(already_pushed) or already_pushed:
        return _blocked('PUSH_IS_SECOND_AND_FINAL_ATTEMPT')
    if not _valid_bool(original_fumble_consequence_applied):
        return _blocked('FUMBLE_CONSEQUENCE_GATE_INVALID')
    if original_level == 'FUMBLE' and not original_fumble_consequence_applied:
        return _blocked('ORIGINAL_FUMBLE_CONSEQUENCE_MUST_ALREADY_APPLY')
    if original_level != 'FUMBLE' and original_fumble_consequence_applied:
        return _blocked('FUMBLE_CONSEQUENCE_GATE_UNUSED')
    if not _valid_bool(situation_changed):
        return _blocked('SITUATION_CHANGED_GATE_INVALID')
    if original_difficulty not in DIFFICULTIES:
        return _blocked('ORIGINAL_DIFFICULTY_INVALID')
    if situation_changed:
        if keeper_new_difficulty not in DIFFICULTIES:
            return _blocked('CHANGED_SITUATION_REQUIRES_KEEPER_DIFFICULTY')
        difficulty = keeper_new_difficulty
    else:
        if keeper_new_difficulty is not None:
            return _blocked('UNCHANGED_SITUATION_MUST_KEEP_DIFFICULTY')
        difficulty = original_difficulty
    return {
        'status': 'RESOLVED',
        'category': category,
        'original_level': original_level,
        'same_goal_confirmed': True,
        'justification': justification.strip(),
        'second_and_final_attempt': True,
        'difficulty': difficulty,
        'original_fumble_consequence_preserved': original_level == 'FUMBLE',
        'randomness_generated': False,
    }


def resolve_pushed_roll(
    *,
    value: int,
    recorded_roll: int,
    difficulty: str,
    keeper_failure_consequence_id: str | None = None,
) -> dict:
    if not _valid_int(value, 0, 100) or not _valid_int(recorded_roll, 1, 100):
        return _blocked('PUSHED_ROLL_INPUT_INVALID')
    if difficulty not in DIFFICULTIES:
        return _blocked('PUSHED_ROLL_DIFFICULTY_INVALID')
    result = core_rules.meets_difficulty(value, recorded_roll, difficulty)
    if result['success']:
        if keeper_failure_consequence_id is not None:
            return _blocked('SUCCESS_MUST_NOT_APPLY_PUSH_FAILURE_CONSEQUENCE')
        return {
            'status': 'RESOLVED',
            'success': True,
            'goal_achieved': True,
            'level': result['level'],
            'difficulty': difficulty,
            'second_and_final_attempt': True,
            'randomness_generated': False,
        }
    if not _valid_text(keeper_failure_consequence_id):
        return _blocked('FAILED_PUSH_REQUIRES_KEEPER_DEFINED_CONSEQUENCE')
    return {
        'status': 'RESOLVED',
        'success': False,
        'goal_achieved': False,
        'level': result['level'],
        'difficulty': difficulty,
        'keeper_failure_consequence_id': keeper_failure_consequence_id.strip(),
        'second_and_final_attempt': True,
        'randomness_generated': False,
    }


def resolve_group_skill_roll(*, participants: list[dict], difficulty: str, success_mode: str) -> dict:
    if difficulty not in DIFFICULTIES:
        return _blocked('GROUP_DIFFICULTY_INVALID')
    if success_mode not in {'ANY_SUCCESS', 'ALL_SUCCESS'}:
        return _blocked('GROUP_SUCCESS_MODE_INVALID')
    if not isinstance(participants, list) or not participants:
        return _blocked('GROUP_PARTICIPANTS_REQUIRED')
    seen = set()
    results = []
    for idx, participant in enumerate(participants):
        if not isinstance(participant, dict) or set(participant) != {'actor_id', 'value', 'recorded_roll'}:
            return _blocked('GROUP_PARTICIPANT_RECORD_INVALID', index=idx)
        actor_id = participant['actor_id']
        value = participant['value']
        roll = participant['recorded_roll']
        if not _valid_text(actor_id) or actor_id in seen:
            return _blocked('GROUP_PARTICIPANT_ID_INVALID_OR_DUPLICATE', index=idx)
        if not _valid_int(value, 0, 100) or not _valid_int(roll, 1, 100):
            return _blocked('GROUP_PARTICIPANT_ROLL_INVALID', index=idx)
        seen.add(actor_id)
        r = core_rules.meets_difficulty(value, roll, difficulty)
        results.append({'actor_id': actor_id, 'level': r['level'], 'success': r['success']})
    successes = sum(1 for r in results if r['success'])
    group_success = successes >= 1 if success_mode == 'ANY_SUCCESS' else successes == len(results)
    return {
        'status': 'RESOLVED',
        'success_mode': success_mode,
        'difficulty': difficulty,
        'participants': results,
        'successful_participants': successes,
        'group_success': group_success,
        'automatic_participant_selection': False,
        'randomness_generated': False,
    }


def subsequent_same_goal_attempt_gate(
    *,
    actor_already_rolled: bool,
    keeper_allows_attempt: bool,
    push_declared: bool,
) -> dict:
    if not all(_valid_bool(v) for v in (actor_already_rolled, keeper_allows_attempt, push_declared)):
        return _blocked('SUBSEQUENT_ATTEMPT_GATE_INVALID')
    if not keeper_allows_attempt:
        return _blocked('KEEPER_DOES_NOT_ALLOW_ADDITIONAL_ATTEMPT')
    if actor_already_rolled and not push_declared:
        return _blocked('SAME_INVESTIGATOR_RETRY_REQUIRES_PUSH')
    if not actor_already_rolled and push_declared:
        return _blocked('NEW_INVESTIGATOR_NORMAL_ATTEMPT_MUST_NOT_BE_MARKED_PUSHED')
    return {
        'status': 'RESOLVED',
        'attempt_type': 'PUSHED' if actor_already_rolled else 'NORMAL',
        'randomness_generated': False,
    }


def physical_human_limit_plan(*, opposition_value: int, investigators: list[dict]) -> dict:
    if not _valid_int(opposition_value, 1):
        return _blocked('PHYSICAL_OPPOSITION_INVALID')
    if not isinstance(investigators, list) or not investigators:
        return _blocked('PHYSICAL_INVESTIGATORS_REQUIRED')
    parsed = []
    seen = set()
    for idx, participant in enumerate(investigators):
        if not isinstance(participant, dict) or set(participant) != {'actor_id', 'characteristic'}:
            return _blocked('PHYSICAL_PARTICIPANT_RECORD_INVALID', index=idx)
        actor_id = participant['actor_id']
        characteristic = participant['characteristic']
        if not _valid_text(actor_id) or actor_id in seen:
            return _blocked('PHYSICAL_PARTICIPANT_ID_INVALID_OR_DUPLICATE', index=idx)
        if not _valid_int(characteristic, 0):
            return _blocked('PHYSICAL_CHARACTERISTIC_INVALID', index=idx)
        seen.add(actor_id)
        parsed.append({'actor_id': actor_id, 'characteristic': characteristic})

    remaining = sorted(parsed, key=lambda p: p['characteristic'])
    opposition = opposition_value
    reducers = []

    while remaining:
        capable = [p for p in remaining if opposition <= p['characteristic'] + 100]
        if capable:
            difficulty_record = living_opponent_difficulty(opposition)
            return {
                'status': 'RESOLVED',
                'opposition_before': opposition_value,
                'opposition_after_reductions': opposition,
                'difficulty': difficulty_record['difficulty'],
                'reducers': reducers,
                'eligible_rollers': [p['actor_id'] for p in remaining if opposition <= p['characteristic'] + 100],
                'a_roll_is_still_required': True,
                'automatic_helper_selection': False,
                'randomness_generated': False,
            }
        lowest = remaining[0]['characteristic']
        tied_lowest = [p['actor_id'] for p in remaining if p['characteristic'] == lowest]
        if len(tied_lowest) > 1:
            return _blocked(
                'LOWEST_CHARACTERISTIC_REDUCER_TIE_KEEPER_RESOLUTION_REQUIRED',
                characteristic=lowest,
                candidates=tied_lowest,
            )
        reducer = remaining.pop(0)
        next_opposition = opposition - reducer['characteristic']
        if next_opposition <= 0:
            return _blocked('PHYSICAL_OPPOSITION_MAY_NOT_BE_REDUCED_TO_ZERO_OR_BELOW')
        reducers.append(reducer['actor_id'])
        opposition = next_opposition

    return _blocked('NO_INVESTIGATOR_REMAINS_TO_MAKE_REQUIRED_ROLL')


def group_luck_selector(*, investigators: list[dict], mode: str) -> dict:
    if mode not in {'GROUP_LUCK_ROLL', 'LOWEST_LUCK_BAD_EVENT'}:
        return _blocked('GROUP_LUCK_MODE_INVALID')
    if not isinstance(investigators, list) or not investigators:
        return _blocked('GROUP_LUCK_INVESTIGATORS_REQUIRED')
    parsed = []
    seen = set()
    for idx, participant in enumerate(investigators):
        if not isinstance(participant, dict) or set(participant) != {'actor_id', 'luck'}:
            return _blocked('GROUP_LUCK_RECORD_INVALID', index=idx)
        actor_id = participant['actor_id']
        luck = participant['luck']
        if not _valid_text(actor_id) or actor_id in seen or not _valid_int(luck, 0, 99):
            return _blocked('GROUP_LUCK_PARTICIPANT_INVALID', index=idx)
        seen.add(actor_id)
        parsed.append({'actor_id': actor_id, 'luck': luck})
    lowest = min(p['luck'] for p in parsed)
    candidates = [p['actor_id'] for p in parsed if p['luck'] == lowest]
    if len(candidates) != 1:
        return _blocked('LOWEST_LUCK_TIE_KEEPER_RESOLUTION_REQUIRED', lowest_luck=lowest, candidates=candidates)
    return {
        'status': 'RESOLVED',
        'mode': mode,
        'actor_id': candidates[0],
        'luck': lowest,
        'roll_required': mode == 'GROUP_LUCK_ROLL',
        'randomness_generated': False,
    }


def resolve_group_luck_roll(*, investigators: list[dict], actor_id: str, recorded_roll: int) -> dict:
    selector = group_luck_selector(investigators=investigators, mode='GROUP_LUCK_ROLL')
    if selector['status'] != 'RESOLVED':
        return selector
    if actor_id != selector['actor_id']:
        return _blocked('GROUP_LUCK_WRONG_ACTOR', required_actor_id=selector['actor_id'])
    if not _valid_int(recorded_roll, 1, 100):
        return _blocked('GROUP_LUCK_ROLL_INVALID')
    result = core_rules.meets_difficulty(selector['luck'], recorded_roll, 'REGULAR')
    return {
        'status': 'RESOLVED',
        'actor_id': actor_id,
        'luck': selector['luck'],
        'recorded_roll': recorded_roll,
        'level': result['level'],
        'success': result['success'],
        'randomness_generated': False,
    }


def intelligence_or_idea_roll(*, INT: int, recorded_roll: int, roll_type: str) -> dict:
    if roll_type not in {'INTELLIGENCE', 'IDEA'}:
        return _blocked('INT_IDEA_ROLL_TYPE_INVALID')
    if not _valid_int(INT, 0, 100) or not _valid_int(recorded_roll, 1, 100):
        return _blocked('INT_IDEA_INPUT_INVALID')
    result = core_rules.meets_difficulty(INT, recorded_roll, 'REGULAR')
    return {
        'status': 'RESOLVED',
        'roll_type': roll_type,
        'level': result['level'],
        'success': result['success'],
        'automatic_solution_generated': False,
        'automatic_cost_generated': False,
        'randomness_generated': False,
    }


def know_roll(*, EDU: int, recorded_roll: int | None, specific_skill_applicable: bool, specific_skill_id: str | None = None) -> dict:
    if not _valid_bool(specific_skill_applicable):
        return _blocked('KNOW_SPECIFIC_SKILL_GATE_INVALID')
    if specific_skill_applicable:
        if not _valid_text(specific_skill_id):
            return _blocked('SPECIFIC_SKILL_ID_REQUIRED')
        if recorded_roll is not None:
            return _blocked('KNOW_ROLL_MUST_DEFER_BEFORE_CONSUMING_ROLL')
        return {
            'status': 'PENDING',
            'code': 'SPECIFIC_SKILL_PREFERRED_BY_KEEPER',
            'specific_skill_id': specific_skill_id.strip(),
            'randomness_generated': False,
        }
    if specific_skill_id is not None:
        return _blocked('SPECIFIC_SKILL_ID_UNUSED')
    if not _valid_int(EDU, 0, 100) or not _valid_int(recorded_roll, 1, 100):
        return _blocked('KNOW_ROLL_INPUT_INVALID')
    result = core_rules.meets_difficulty(EDU, recorded_roll, 'REGULAR')
    return {
        'status': 'RESOLVED',
        'level': result['level'],
        'success': result['success'],
        'automatic_information_generated': False,
        'randomness_generated': False,
    }
