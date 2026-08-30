from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
GENERAL_DIR = ROOT / 'development' / 'r1-coc7-general-skill-resolution-batch1'
INVESTIGATOR_DEV_DIR = ROOT / 'development' / 'r1-coc7-investigator-development-batch1'
for path in (RULES_DIR, GENERAL_DIR, INVESTIGATOR_DEV_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import general_skill_resolution_dev as general  # noqa: E402
import investigator_development_dev as investigator_development  # noqa: E402

MODULE_ID = 'COC7_LUCK_SPENDING_R1_BATCH1_DEV_V1'
PARENT_GENERAL_SKILL_MODULE_ID = general.MODULE_ID
INVESTIGATOR_DEVELOPMENT_MODULE_ID = investigator_development.MODULE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'

ALLOWED_ROLL_KINDS = {'SKILL', 'CHARACTERISTIC'}
EXCLUDED_ROLL_KINDS = {'LUCK', 'DAMAGE', 'SANITY', 'SANITY_LOSS'}
DIFFICULTIES = {'REGULAR', 'HARD', 'EXTREME'}


def _blocked(code: str, **extra) -> dict:
    return {
        'status': 'BLOCKED',
        'code': code,
        'state_mutated': False,
        'randomness_generated': False,
        **extra,
    }


def _valid_int(value, minimum=None, maximum=None) -> bool:
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _valid_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def spend_luck_on_recorded_roll(
    *,
    actor_id: str,
    roll_owner_actor_id: str,
    current_luck: int,
    roll_kind: str,
    value: int,
    original_roll: int,
    spend_points: int,
    difficulty: str = 'REGULAR',
    pushed_roll: bool = False,
    firearm_malfunction: bool = False,
) -> dict:
    """Apply an explicitly declared Luck spend to an already-recorded roll.

    This function never chooses a spend amount and never generates dice.
    The result is deterministic and actor-bound for replay.
    """
    if not _valid_text(actor_id) or not _valid_text(roll_owner_actor_id):
        return _blocked('ACTOR_ID_INVALID')
    actor_id = actor_id.strip()
    roll_owner_actor_id = roll_owner_actor_id.strip()
    if actor_id != roll_owner_actor_id:
        return _blocked('LUCK_MAY_ONLY_ALTER_OWN_ROLL', required_actor_id=roll_owner_actor_id)

    if roll_kind in EXCLUDED_ROLL_KINDS:
        return _blocked('ROLL_KIND_EXCLUDED_FROM_LUCK_SPEND', roll_kind=roll_kind)
    if roll_kind not in ALLOWED_ROLL_KINDS:
        return _blocked('ROLL_KIND_UNSUPPORTED_FOR_LUCK_SPEND', roll_kind=roll_kind)
    if difficulty not in DIFFICULTIES:
        return _blocked('DIFFICULTY_INVALID')
    if not isinstance(pushed_roll, bool) or not isinstance(firearm_malfunction, bool):
        return _blocked('ROLL_STATE_FLAG_INVALID')
    if pushed_roll:
        return _blocked('PUSHED_ROLL_CANNOT_BE_ALTERED_WITH_LUCK')

    if not _valid_int(current_luck, 0, 99):
        return _blocked('CURRENT_LUCK_INVALID')
    if not _valid_int(value, 0, 100):
        return _blocked('ROLL_VALUE_INVALID')
    if not _valid_int(original_roll, 1, 100):
        return _blocked('RECORDED_ROLL_INVALID')
    if not _valid_int(spend_points, 1):
        return _blocked('LUCK_SPEND_POINTS_INVALID')
    if spend_points > current_luck:
        return _blocked('LUCK_SPEND_EXCEEDS_CURRENT_LUCK')

    original_result = core_rules.meets_difficulty(value, original_roll, difficulty)
    if original_result['level'] == 'CRITICAL':
        return _blocked('ORIGINAL_CRITICAL_CANNOT_BE_ALTERED_WITH_LUCK')
    if original_result['level'] == 'FUMBLE':
        return _blocked('ORIGINAL_FUMBLE_CANNOT_BE_BOUGHT_OFF_WITH_LUCK')
    if firearm_malfunction:
        return _blocked('FIREARM_MALFUNCTION_CANNOT_BE_BOUGHT_OFF_WITH_LUCK')

    adjusted_roll = original_roll - spend_points
    if adjusted_roll < 1:
        return _blocked('LUCK_SPEND_WOULD_REDUCE_RECORDED_ROLL_BELOW_ONE')

    adjusted_result = core_rules.meets_difficulty(value, adjusted_roll, difficulty)
    luck_after = current_luck - spend_points
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'actor_id': actor_id,
        'roll_owner_actor_id': roll_owner_actor_id,
        'roll_kind': roll_kind,
        'difficulty': difficulty,
        'value': value,
        'original_roll': original_roll,
        'original_level': original_result['level'],
        'original_success': original_result['success'],
        'spend_points': spend_points,
        'adjusted_roll': adjusted_roll,
        'adjusted_level': adjusted_result['level'],
        'adjusted_success': adjusted_result['success'],
        'luck_before': current_luck,
        'luck_after': luck_after,
        'luck_spent_on_roll': True,
        'experience_check_eligible': False,
        'state_mutated': True,
        'atomic_luck_delta': -spend_points,
        'automatic_spend_amount_selection': False,
        'randomness_generated': False,
    }


def experience_tick_after_luck_spend(
    *,
    skill_id: str,
    adjusted_roll_success: bool,
    used_bonus_die: bool,
    opposed_roll: bool,
    opposed_winner: bool | None,
    already_checked: bool,
) -> dict:
    """Reuse the existing experience engine with the Luck-spent flag pinned true."""
    return investigator_development.experience_tick(
        skill_id=skill_id,
        roll_success=adjusted_roll_success,
        used_bonus_die=used_bonus_die,
        luck_spent_on_roll=True,
        opposed_roll=opposed_roll,
        opposed_winner=opposed_winner,
        already_checked=already_checked,
    )
