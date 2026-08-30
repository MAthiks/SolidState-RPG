from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
CHASE2_DIR = ROOT / 'development' / 'r1-coc7-chase-batch2'
WOUNDS_DIR = ROOT / 'development' / 'r1-coc7-wounds-healing-batch1'
for path in (RULES_DIR, CHASE2_DIR, WOUNDS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import chase_batch2_dev as chase2  # noqa: E402
import wounds_healing_dev as wounds  # noqa: E402

MODULE_ID = 'COC7_MAGIC_CORE_R1_BATCH1_DEV_V1'
PARENT_CHASE_MODULE_ID = chase2.MODULE_ID
FROZEN_RULES_PACKAGE_ID = core_rules.PACKAGE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
DIFFICULTIES = {'REGULAR', 'HARD', 'EXTREME'}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _percentile(*, value: int, units: int, tens: list[int], difficulty: str) -> dict:
    if not _valid_int(value, 0, 100) or difficulty not in DIFFICULTIES:
        return {'status': 'BLOCKED', 'code': 'PERCENTILE_INPUT_INVALID'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, 0)
        judged = core_rules.meets_difficulty(value, roll, difficulty)
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    return {
        'status': 'RESOLVED',
        'roll': roll,
        'success_level': judged['level'],
        'success': judged['success'],
        'difficulty': difficulty,
    }


def magic_point_profile(*, pow_value: int, current_mp: int | None = None) -> dict:
    if not _valid_int(pow_value, 0):
        return {'status': 'BLOCKED', 'code': 'POW_INVALID'}
    natural_max = pow_value // 5
    regen_per_hour = 0 if pow_value == 0 else 1 + ((pow_value - 1) // 100)
    result = {
        'status': 'RESOLVED',
        'natural_max_mp': natural_max,
        'initial_mp': natural_max,
        'regen_per_completed_hour': regen_per_hour,
    }
    if current_mp is not None:
        if not _valid_int(current_mp, 0):
            return {'status': 'BLOCKED', 'code': 'CURRENT_MP_INVALID'}
        result['current_mp'] = current_mp
        result['excess_above_natural_max'] = max(0, current_mp - natural_max)
        result['excess_can_be_spent'] = current_mp > natural_max
        result['excess_can_be_regenerated'] = False
    return result


def regenerate_magic_points(*, pow_value: int, current_mp: int, completed_hours: int) -> dict:
    profile = magic_point_profile(pow_value=pow_value, current_mp=current_mp)
    if profile.get('status') != 'RESOLVED' or not _valid_int(completed_hours, 0):
        return profile if profile.get('status') != 'RESOLVED' else {'status': 'BLOCKED', 'code': 'COMPLETED_HOURS_INVALID'}
    natural_max = profile['natural_max_mp']
    if current_mp >= natural_max:
        regenerated = 0
        new_mp = current_mp
    else:
        regenerated = min(natural_max - current_mp, profile['regen_per_completed_hour'] * completed_hours)
        new_mp = current_mp + regenerated
    return {
        'status': 'RESOLVED',
        'previous_mp': current_mp,
        'MP': new_mp,
        'regenerated_mp': regenerated,
        'natural_max_mp': natural_max,
        'regen_per_completed_hour': profile['regen_per_completed_hour'],
        'randomness_generated': False,
    }


def spend_magic_points(*, current_mp: int, current_hp: int, max_hp: int, cost: int, had_major_wound: bool = False) -> dict:
    if not _valid_int(current_mp, 0) or not _valid_int(cost, 0) or not isinstance(had_major_wound, bool):
        return {'status': 'BLOCKED', 'code': 'MAGIC_POINT_SPEND_INPUT_INVALID'}
    if not _valid_int(max_hp, 1) or not _valid_int(current_hp, 0, max_hp):
        return {'status': 'BLOCKED', 'code': 'HP_INPUT_INVALID'}
    mp_spent = min(current_mp, cost)
    hp_cost = cost - mp_spent
    damage = wounds.assess_damage(max_hp=max_hp, current_hp=current_hp, damage=hp_cost, had_major_wound=had_major_wound)
    if damage.get('status') != 'RESOLVED':
        return damage
    return {
        'status': 'RESOLVED',
        'previous_mp': current_mp,
        'MP': current_mp - mp_spent,
        'magic_point_cost': cost,
        'mp_spent': mp_spent,
        'hp_cost_after_mp_exhausted': hp_cost,
        'hp_state': damage,
        'physical_harm_narration_keeper_selected': hp_cost > 0,
        'randomness_generated': False,
    }


def initial_tome_reading(
    *,
    language_value: int,
    difficulty: str,
    units: int | None,
    tens: list[int] | None,
    keeper_auto_success: bool,
    current_mythos: int,
    current_san: int,
    cmi: int,
    recorded_tome_san_loss: int | None,
    believer: bool,
) -> dict:
    if difficulty not in DIFFICULTIES or not isinstance(keeper_auto_success, bool) or not isinstance(believer, bool):
        return {'status': 'BLOCKED', 'code': 'INITIAL_READING_GATE_INVALID'}
    if not _valid_int(current_mythos, 0, 99) or not _valid_int(current_san, 0, 99) or not _valid_int(cmi, 0):
        return {'status': 'BLOCKED', 'code': 'INITIAL_READING_STATE_INVALID'}
    if keeper_auto_success:
        success = True
        roll = None
        level = 'KEEPER_AUTO_SUCCESS'
    else:
        if units is None or tens is None:
            return {'status': 'BLOCKED', 'code': 'LANGUAGE_READING_ROLL_REQUIRED'}
        check = _percentile(value=language_value, units=units, tens=tens, difficulty=difficulty)
        if check.get('status') != 'RESOLVED':
            return check
        success = check['success']; roll = check['roll']; level = check['success_level']
    if not success:
        if recorded_tome_san_loss is not None:
            return {'status': 'BLOCKED', 'code': 'FAILED_INITIAL_READING_MUST_NOT_CONSUME_TOME_SAN_LOSS'}
        return {
            'status': 'RESOLVED',
            'success': False,
            'roll': roll,
            'success_level': level,
            'cthulhu_mythos_gain': 0,
            'SAN': current_san,
            'san_loss': 0,
            'push_allowed': True,
            'automatic_pushed_failure_consequence': False,
            'randomness_generated': False,
        }
    if believer:
        if not _valid_int(recorded_tome_san_loss, 0):
            return {'status': 'BLOCKED', 'code': 'RECORDED_TOME_SAN_LOSS_REQUIRED'}
        tome_loss = recorded_tome_san_loss
    else:
        if recorded_tome_san_loss not in {None, 0}:
            return {'status': 'BLOCKED', 'code': 'NON_BELIEVER_INITIAL_READING_MUST_NOT_APPLY_SAN_LOSS'}
        tome_loss = 0
    new_mythos = min(99, current_mythos + cmi)
    maximum_san = 99 - new_mythos
    san_after_new_max = min(current_san, maximum_san)
    new_san = max(0, san_after_new_max - tome_loss)
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'success': True,
        'roll': roll,
        'success_level': level,
        'cthulhu_mythos_gain': new_mythos - current_mythos,
        'cthulhu_mythos': new_mythos,
        'maximum_san': maximum_san,
        'san_capped_by_new_mythos_maximum': san_after_new_max < current_san,
        'san_loss': san_after_new_max - new_san,
        'SAN': new_san,
        'believer': believer,
        'full_study_time_becomes_known': True,
        'spell_presence_summary_keeper_supplied': True,
        'randomness_generated': False,
    }


def full_tome_study(
    *,
    initial_reading_completed: bool,
    current_mythos: int,
    current_san: int,
    tome_rating: int,
    cmi: int,
    cmf: int,
    believer: bool,
    recorded_tome_san_loss: int | None,
    base_full_study_weeks: int,
    previous_full_studies: int,
    elapsed_study_weeks: int,
    other_tome_study_active: bool = False,
) -> dict:
    for flag in (initial_reading_completed, believer, other_tome_study_active):
        if not isinstance(flag, bool):
            return {'status': 'BLOCKED', 'code': 'FULL_STUDY_FLAG_INVALID'}
    if not initial_reading_completed:
        return {'status': 'BLOCKED', 'code': 'INITIAL_READING_REQUIRED'}
    if other_tome_study_active:
        return {'status': 'BLOCKED', 'code': 'ONLY_ONE_TOME_MAY_BE_STUDIED_AT_A_TIME'}
    values=(current_mythos,current_san,tome_rating,cmi,cmf,base_full_study_weeks,previous_full_studies,elapsed_study_weeks)
    if (not _valid_int(current_mythos,0,99) or not _valid_int(current_san,0,99) or not _valid_int(tome_rating,0,100)
        or not _valid_int(cmi,0) or not _valid_int(cmf,0) or not _valid_int(base_full_study_weeks,1)
        or not _valid_int(previous_full_studies,0) or not _valid_int(elapsed_study_weeks,0)):
        return {'status': 'BLOCKED', 'code': 'FULL_STUDY_INPUT_INVALID'}
    required_weeks = base_full_study_weeks * (2 ** previous_full_studies)
    if elapsed_study_weeks < required_weeks:
        return {
            'status': 'RESOLVED',
            'study_complete': False,
            'required_weeks': required_weeks,
            'elapsed_study_weeks': elapsed_study_weeks,
            'remaining_weeks': required_weeks - elapsed_study_weeks,
            'reading_roll_required': False,
        }
    if believer:
        if not _valid_int(recorded_tome_san_loss,0):
            return {'status':'BLOCKED','code':'RECORDED_TOME_SAN_LOSS_REQUIRED'}
        tome_loss=recorded_tome_san_loss
    else:
        if recorded_tome_san_loss not in {None,0}:
            return {'status':'BLOCKED','code':'NON_BELIEVER_FULL_STUDY_MUST_NOT_APPLY_SAN_LOSS'}
        tome_loss=0
    gain_requested = cmf if current_mythos < tome_rating else cmi
    new_mythos=min(99,current_mythos+gain_requested)
    max_san=99-new_mythos
    san_after_cap=min(current_san,max_san)
    new_san=max(0,san_after_cap-tome_loss)
    return {
        'status':'RESOLVED','study_complete':True,'reading_roll_required':False,
        'required_weeks':required_weeks,'elapsed_study_weeks':elapsed_study_weeks,
        'mythos_gain_basis':'CMF' if current_mythos < tome_rating else 'CMI',
        'cthulhu_mythos_gain':new_mythos-current_mythos,'cthulhu_mythos':new_mythos,
        'maximum_san':max_san,'SAN':new_san,'san_loss':san_after_cap-new_san,
        'language_skill_tick_granted':True,'automatic_other_skill_increase':False,
        'next_full_study_weeks':required_weeks*2,'randomness_generated':False,
    }


def tome_reference_search(*, full_study_completed: bool, tome_rating: int, recorded_search_hours_d4: int, roll: int) -> dict:
    if not isinstance(full_study_completed,bool):
        return {'status':'BLOCKED','code':'REFERENCE_STUDY_FLAG_INVALID'}
    if not full_study_completed:
        return {'status':'BLOCKED','code':'FULL_STUDY_REQUIRED_FOR_REFERENCE_USE'}
    if not _valid_int(tome_rating,0,100) or not _valid_int(recorded_search_hours_d4,1,4) or not _valid_int(roll,1,100):
        return {'status':'BLOCKED','code':'REFERENCE_SEARCH_INPUT_INVALID'}
    return {
        'status':'RESOLVED','search_hours':recorded_search_hours_d4,'roll':roll,
        'mythos_rating':tome_rating,'fact_or_allusion_found':roll <= tome_rating,
        'failed_result_ambiguous_between_absence_and_failed_search':roll > tome_rating,
        'randomness_generated':False,
    }


def spell_learning_plan(
    *,
    method: str,
    initial_reading_completed: bool = False,
    keeper_auto_success: bool = False,
    recorded_duration_dice: list[int] | None = None,
    keeper_override_duration: int | None = None,
) -> dict:
    if method not in {'BOOK','PERSON'} or not isinstance(initial_reading_completed,bool) or not isinstance(keeper_auto_success,bool):
        return {'status':'BLOCKED','code':'SPELL_LEARNING_PLAN_INPUT_INVALID'}
    if method=='BOOK' and not initial_reading_completed:
        return {'status':'BLOCKED','code':'INITIAL_READING_REQUIRED_TO_LEARN_BOOK_SPELL'}
    if keeper_override_duration is not None:
        if not _valid_int(keeper_override_duration,1):
            return {'status':'BLOCKED','code':'KEEPER_DURATION_OVERRIDE_INVALID'}
        duration=keeper_override_duration
        unit='KEEPER_DEFINED_TIME_UNIT'
        source='KEEPER_OVERRIDE'
        if recorded_duration_dice is not None:
            return {'status':'BLOCKED','code':'DURATION_DICE_AND_KEEPER_OVERRIDE_MUTUALLY_EXCLUSIVE'}
    elif method=='BOOK':
        if not isinstance(recorded_duration_dice,list) or len(recorded_duration_dice)!=2 or any(not _valid_int(v,1,6) for v in recorded_duration_dice):
            return {'status':'BLOCKED','code':'RECORDED_2D6_WEEKS_REQUIRED'}
        duration=sum(recorded_duration_dice); unit='WEEKS'; source='RECORDED_2D6'
    else:
        if not isinstance(recorded_duration_dice,list) or len(recorded_duration_dice)!=1 or not _valid_int(recorded_duration_dice[0],1,8):
            return {'status':'BLOCKED','code':'RECORDED_1D8_DAYS_REQUIRED'}
        duration=recorded_duration_dice[0]; unit='DAYS'; source='RECORDED_1D8'
    return {
        'status':'RESOLVED','method':method,'duration':duration,'duration_unit':unit,
        'duration_source':source,'keeper_auto_success':keeper_auto_success,
        'learning_san_cost':0,'randomness_generated':False,
    }


def resolve_spell_learning(*, plan: dict, int_value: int, units: int | None, tens: list[int] | None) -> dict:
    if not isinstance(plan,dict) or plan.get('status')!='RESOLVED':
        return {'status':'BLOCKED','code':'SPELL_LEARNING_PLAN_REQUIRED'}
    if plan['keeper_auto_success']:
        return {'status':'RESOLVED','learned':True,'roll':None,'success_level':'KEEPER_AUTO_SUCCESS','push_allowed':False,'randomness_generated':False}
    if units is None or tens is None:
        return {'status':'BLOCKED','code':'HARD_INT_ROLL_REQUIRED'}
    check=_percentile(value=int_value,units=units,tens=tens,difficulty='HARD')
    if check.get('status')!='RESOLVED':
        return check
    return {
        'status':'RESOLVED','learned':check['success'],'roll':check['roll'],'success_level':check['success_level'],
        'push_allowed':not check['success'],'automatic_pushed_failure_consequence':False,
        'retry_without_push_keeper_timing':not check['success'],'randomness_generated':False,
    }


def first_cast_roll(
    *,
    pow_value: int,
    units: int | None,
    tens: list[int] | None,
    previously_cast_successfully: bool,
    actor_is_npc_or_monster: bool = False,
) -> dict:
    if not isinstance(previously_cast_successfully,bool) or not isinstance(actor_is_npc_or_monster,bool):
        return {'status':'BLOCKED','code':'CASTING_STATE_FLAG_INVALID'}
    if previously_cast_successfully or actor_is_npc_or_monster:
        return {
            'status':'RESOLVED','casting_roll_required':False,'spell_effect_proceeds':True,
            'mastered_after_cast':previously_cast_successfully,'push_allowed':False,
            'randomness_generated':False,
        }
    if units is None or tens is None:
        return {'status':'BLOCKED','code':'FIRST_CAST_HARD_POW_ROLL_REQUIRED'}
    check=_percentile(value=pow_value,units=units,tens=tens,difficulty='HARD')
    if check.get('status')!='RESOLVED':
        return check
    return {
        'status':'RESOLVED','casting_roll_required':True,'roll':check['roll'],'success_level':check['success_level'],
        'spell_effect_proceeds':check['success'],'mastered_after_cast':check['success'],
        'push_allowed':not check['success'],'normal_cost_must_be_paid_for_this_attempt':True,
        'randomness_generated':False,
    }


def apply_fixed_spell_cost(
    *,
    current_mp: int,
    current_hp: int,
    max_hp: int,
    current_san: int,
    current_pow: int,
    mp_cost: int,
    san_cost: int,
    pow_cost: int,
    had_major_wound: bool = False,
) -> dict:
    for value in (current_san,current_pow,mp_cost,san_cost,pow_cost):
        if not _valid_int(value,0):
            return {'status':'BLOCKED','code':'SPELL_COST_INPUT_INVALID'}
    if san_cost > current_san or pow_cost > current_pow:
        return {'status':'BLOCKED','code':'SPELL_COST_EXCEEDS_SAN_OR_POW_AVAILABLE'}
    mp_result=spend_magic_points(current_mp=current_mp,current_hp=current_hp,max_hp=max_hp,cost=mp_cost,had_major_wound=had_major_wound)
    if mp_result.get('status')!='RESOLVED':
        return mp_result
    new_pow=current_pow-pow_cost
    natural_mp_max_after_pow=new_pow//5
    return {
        'status':'RESOLVED','MP':mp_result['MP'],'hp_state':mp_result['hp_state'],
        'SAN':current_san-san_cost,'POW':new_pow,'mp_cost':mp_cost,'san_cost':san_cost,'pow_cost':pow_cost,
        'natural_mp_max_after_pow_cost':natural_mp_max_after_pow,
        'current_mp_above_new_natural_max_can_be_spent_not_regenerated':mp_result['MP']>natural_mp_max_after_pow,
        'randomness_generated':False,
    }


def pushed_cast_failure_cost_plan(
    *,
    recorded_multiplier_d6: int,
    fixed_mp_cost: int = 0,
    fixed_pow_cost: int = 0,
    fixed_san_cost: int = 0,
    san_die_count: int = 0,
    san_die_sides: int | None = None,
    recorded_san_dice: list[int] | None = None,
) -> dict:
    if not _valid_int(recorded_multiplier_d6,1,6):
        return {'status':'BLOCKED','code':'RECORDED_PUSHED_CAST_D6_MULTIPLIER_REQUIRED'}
    for value in (fixed_mp_cost,fixed_pow_cost,fixed_san_cost,san_die_count):
        if not _valid_int(value,0):
            return {'status':'BLOCKED','code':'PUSHED_CAST_COST_PROFILE_INVALID'}
    if san_die_count > 0:
        if not _valid_int(san_die_sides,2):
            return {'status':'BLOCKED','code':'SAN_DIE_SIDES_REQUIRED'}
        required=san_die_count*recorded_multiplier_d6
        if not isinstance(recorded_san_dice,list) or len(recorded_san_dice)!=required or any(not _valid_int(v,1,san_die_sides) for v in recorded_san_dice):
            return {'status':'BLOCKED','code':'RECORDED_AMPLIFIED_SAN_DICE_INVALID'}
        san_total=sum(recorded_san_dice)+(fixed_san_cost*recorded_multiplier_d6)
    else:
        if recorded_san_dice not in {None, ()} and recorded_san_dice != []:
            return {'status':'BLOCKED','code':'UNUSED_SAN_DICE_SUPPLIED'}
        san_total=fixed_san_cost*recorded_multiplier_d6
    return {
        'status':'RESOLVED','multiplier':recorded_multiplier_d6,
        'additional_mp_cost':fixed_mp_cost*recorded_multiplier_d6,
        'additional_pow_cost':fixed_pow_cost*recorded_multiplier_d6,
        'additional_san_cost':san_total,
        'recorded_san_dice':[] if recorded_san_dice is None else list(recorded_san_dice),
        'spell_still_works':True,'keeper_side_effect_selection_required':True,
        'automatic_side_effect_selection':False,'randomness_generated':False,
    }
