from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
MAGIC2_DIR = ROOT / 'development' / 'r1-coc7-magic-core-batch2'
for path in (RULES_DIR, MAGIC2_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import magic_core_batch2_dev as magic2  # noqa: E402

MODULE_ID = 'COC7_INVESTIGATOR_DEVELOPMENT_R1_BATCH1_DEV_V1'
PARENT_MAGIC_MODULE_ID = magic2.MODULE_ID
FROZEN_RULES_PACKAGE_ID = core_rules.PACKAGE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
NON_IMPROVABLE_SKILLS = {'CTHULHU_MYTHOS', 'CREDIT_RATING'}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _skill_id(value: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().upper().replace(' ', '_')


def _recorded_2d6(values) -> tuple[int, int] | None:
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        return None
    if not all(_valid_int(v, 1, 6) for v in values):
        return None
    return int(values[0]), int(values[1])


def experience_tick(
    *,
    skill_id: str,
    roll_success: bool,
    used_bonus_die: bool,
    luck_spent_on_roll: bool,
    opposed_roll: bool,
    opposed_winner: bool | None,
    already_checked: bool,
) -> dict:
    sid = _skill_id(skill_id)
    flags = (roll_success, used_bonus_die, luck_spent_on_roll, opposed_roll, already_checked)
    if sid is None or not all(isinstance(v, bool) for v in flags):
        return {'status': 'BLOCKED', 'code': 'EXPERIENCE_TICK_INPUT_INVALID'}
    if opposed_roll:
        if not isinstance(opposed_winner, bool):
            return {'status': 'BLOCKED', 'code': 'OPPOSED_WINNER_REQUIRED'}
    elif opposed_winner is not None:
        return {'status': 'BLOCKED', 'code': 'OPPOSED_WINNER_UNUSED'}

    if sid in NON_IMPROVABLE_SKILLS:
        return {
            'status': 'RESOLVED', 'skill_id': sid, 'new_tick_granted': False,
            'pending_check_after': already_checked, 'reason': 'SKILL_NEVER_RECEIVES_IMPROVEMENT_CHECK',
            'randomness_generated': False,
        }
    if not roll_success:
        return {
            'status': 'RESOLVED', 'skill_id': sid, 'new_tick_granted': False,
            'pending_check_after': already_checked, 'reason': 'SKILL_USE_NOT_SUCCESSFUL',
            'randomness_generated': False,
        }
    if used_bonus_die:
        return {
            'status': 'RESOLVED', 'skill_id': sid, 'new_tick_granted': False,
            'pending_check_after': already_checked, 'reason': 'BONUS_DIE_BLOCKS_TICK',
            'randomness_generated': False,
        }
    if luck_spent_on_roll:
        return {
            'status': 'RESOLVED', 'skill_id': sid, 'new_tick_granted': False,
            'pending_check_after': already_checked, 'reason': 'LUCK_SPEND_BLOCKS_TICK',
            'randomness_generated': False,
        }
    if opposed_roll and not opposed_winner:
        return {
            'status': 'RESOLVED', 'skill_id': sid, 'new_tick_granted': False,
            'pending_check_after': already_checked, 'reason': 'OPPOSED_ROLL_NONWINNER',
            'randomness_generated': False,
        }
    if already_checked:
        return {
            'status': 'RESOLVED', 'skill_id': sid, 'new_tick_granted': False,
            'pending_check_after': True, 'reason': 'ONE_PENDING_CHECK_PER_SKILL',
            'randomness_generated': False,
        }
    return {
        'status': 'RESOLVED', 'skill_id': sid, 'new_tick_granted': True,
        'pending_check_after': True, 'reason': 'ELIGIBLE_SUCCESSFUL_USE',
        'randomness_generated': False,
    }


def resolve_skill_improvement(
    *,
    skill_id: str,
    current_skill: int,
    pending_check: bool,
    recorded_percentile: int | None,
    recorded_gain_d10: int | None = None,
    recorded_sanity_2d6=None,
) -> dict:
    sid = _skill_id(skill_id)
    if sid is None or not _valid_int(current_skill, 0) or not isinstance(pending_check, bool):
        return {'status': 'BLOCKED', 'code': 'SKILL_IMPROVEMENT_INPUT_INVALID'}
    if sid in NON_IMPROVABLE_SKILLS:
        return {'status': 'BLOCKED', 'code': 'SKILL_NEVER_RECEIVES_IMPROVEMENT_CHECK'}
    if not pending_check:
        if recorded_percentile is not None or recorded_gain_d10 is not None or recorded_sanity_2d6 is not None:
            return {'status': 'BLOCKED', 'code': 'NO_PENDING_CHECK_MUST_NOT_CONSUME_DICE'}
        return {
            'status': 'RESOLVED', 'skill_id': sid, 'improvement_checked': False,
            'improved': False, 'skill_before': current_skill, 'skill_after': current_skill,
            'pending_check_after': False, 'randomness_generated': False,
        }
    if not _valid_int(recorded_percentile, 1, 100):
        return {'status': 'BLOCKED', 'code': 'RECORDED_IMPROVEMENT_PERCENTILE_REQUIRED'}

    improved = recorded_percentile > current_skill or recorded_percentile > 95
    if improved:
        if not _valid_int(recorded_gain_d10, 1, 10):
            return {'status': 'BLOCKED', 'code': 'RECORDED_IMPROVEMENT_D10_REQUIRED'}
        skill_after = current_skill + recorded_gain_d10
    else:
        if recorded_gain_d10 is not None:
            return {'status': 'BLOCKED', 'code': 'FAILED_IMPROVEMENT_MUST_NOT_CONSUME_D10'}
        skill_after = current_skill

    crossed_90 = current_skill < 90 <= skill_after
    if crossed_90:
        dice = _recorded_2d6(recorded_sanity_2d6)
        if dice is None:
            return {'status': 'BLOCKED', 'code': 'RECORDED_2D6_SANITY_REWARD_REQUIRED'}
        sanity_reward = sum(dice)
    else:
        if recorded_sanity_2d6 is not None:
            return {'status': 'BLOCKED', 'code': 'UNUSED_SANITY_REWARD_DICE'}
        dice = None
        sanity_reward = 0

    return {
        'status': 'RESOLVED', 'module_id': MODULE_ID, 'skill_id': sid,
        'improvement_checked': True, 'improvement_roll': recorded_percentile,
        'improved': improved, 'skill_before': current_skill, 'skill_gain': skill_after - current_skill,
        'skill_after': skill_after, 'skill_may_exceed_100': True,
        'crossed_90_threshold': crossed_90, 'recorded_sanity_2d6': list(dice) if dice else None,
        'sanity_reward_pending_application': sanity_reward,
        'sanity_reward_application_requires_existing_sanity_cap_rules': crossed_90,
        'pending_check_after': False, 'randomness_generated': False,
    }


def training_segment(
    *,
    campaign_context: bool,
    segment_months: int,
    keeper_confirms_completed: bool,
    keeper_confirms_valid: bool,
    renowned_teacher_shortening_authorized: bool = False,
) -> dict:
    flags = (campaign_context, keeper_confirms_completed, keeper_confirms_valid, renowned_teacher_shortening_authorized)
    if not all(isinstance(v, bool) for v in flags) or not _valid_int(segment_months, 1):
        return {'status': 'BLOCKED', 'code': 'TRAINING_INPUT_INVALID'}
    if not campaign_context:
        return {'status': 'BLOCKED', 'code': 'TRAINING_BATCH1_REQUIRES_CAMPAIGN_CONTEXT'}
    if segment_months < 4 and not renowned_teacher_shortening_authorized:
        return {'status': 'BLOCKED', 'code': 'TRAINING_SEGMENT_SHORTER_THAN_DEFAULT_REQUIRES_KEEPER_OVERRIDE'}
    if not keeper_confirms_completed:
        return {
            'status': 'RESOLVED', 'experience_check_granted': False,
            'reason': 'TRAINING_SEGMENT_NOT_COMPLETED', 'randomness_generated': False,
        }
    if not keeper_confirms_valid:
        return {
            'status': 'RESOLVED', 'experience_check_granted': False,
            'reason': 'KEEPER_INVALIDATED_TRAINING_SEGMENT', 'randomness_generated': False,
        }
    return {
        'status': 'RESOLVED', 'experience_check_granted': True,
        'segment_months': segment_months, 'renowned_teacher_shortening_authorized': renowned_teacher_shortening_authorized,
        'keeper_course_judgment_required': True, 'randomness_generated': False,
    }


def self_study_plan(
    *,
    academic_skill_id: str,
    study_months: int,
    keeper_agrees_academic_subject: bool,
    renowned_teacher_shortening_authorized: bool = False,
) -> dict:
    sid = _skill_id(academic_skill_id)
    if sid is None or not _valid_int(study_months, 1) or not isinstance(keeper_agrees_academic_subject, bool) or not isinstance(renowned_teacher_shortening_authorized, bool):
        return {'status': 'BLOCKED', 'code': 'SELF_STUDY_INPUT_INVALID'}
    if sid in NON_IMPROVABLE_SKILLS:
        return {'status': 'BLOCKED', 'code': 'SELF_STUDY_SKILL_NOT_ELIGIBLE'}
    if not keeper_agrees_academic_subject:
        return {'status': 'BLOCKED', 'code': 'KEEPER_ACADEMIC_SUBJECT_GATE_REQUIRED'}
    if study_months < 4 and not renowned_teacher_shortening_authorized:
        return {'status': 'BLOCKED', 'code': 'SELF_STUDY_SHORTER_THAN_DEFAULT_REQUIRES_KEEPER_OVERRIDE'}
    return {
        'status': 'RESOLVED', 'skill_id': sid, 'study_months': study_months,
        'improvement_check_required_after_study': True,
        'use_resolve_skill_improvement_procedure': True,
        'renowned_teacher_shortening_authorized': renowned_teacher_shortening_authorized,
        'randomness_generated': False,
    }


def recover_luck(
    *,
    optional_rule_enabled: bool,
    session_complete: bool,
    current_luck: int,
    recorded_percentile: int | None,
    recorded_gain_d10: int | None = None,
) -> dict:
    if not isinstance(optional_rule_enabled, bool) or not isinstance(session_complete, bool) or not _valid_int(current_luck, 0, 99):
        return {'status': 'BLOCKED', 'code': 'LUCK_RECOVERY_INPUT_INVALID'}
    if not optional_rule_enabled:
        return {'status': 'BLOCKED', 'code': 'LUCK_RECOVERY_OPTION_NOT_ENABLED'}
    if not session_complete:
        return {'status': 'BLOCKED', 'code': 'LUCK_RECOVERY_REQUIRES_SESSION_END'}
    if not _valid_int(recorded_percentile, 1, 100):
        return {'status': 'BLOCKED', 'code': 'RECORDED_LUCK_RECOVERY_PERCENTILE_REQUIRED'}

    recovery_success = recorded_percentile > current_luck
    if recovery_success:
        if not _valid_int(recorded_gain_d10, 1, 10):
            return {'status': 'BLOCKED', 'code': 'RECORDED_LUCK_RECOVERY_D10_REQUIRED'}
        uncapped = current_luck + recorded_gain_d10
        luck_after = min(99, uncapped)
    else:
        if recorded_gain_d10 is not None:
            return {'status': 'BLOCKED', 'code': 'FAILED_LUCK_RECOVERY_MUST_NOT_CONSUME_D10'}
        uncapped = current_luck
        luck_after = current_luck

    return {
        'status': 'RESOLVED', 'module_id': MODULE_ID,
        'luck_before': current_luck, 'recovery_roll': recorded_percentile,
        'recovery_success': recovery_success, 'recorded_gain_d10': recorded_gain_d10,
        'uncapped_luck_after': uncapped, 'luck_after': luck_after,
        'actual_luck_gain': luck_after - current_luck, 'luck_cap': 99,
        'starting_luck_reset_applied': False, 'randomness_generated': False,
    }
