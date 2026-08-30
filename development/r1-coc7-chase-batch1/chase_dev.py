from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
TREATMENT_DIR = ROOT / 'development' / 'r1-coc7-sanity-treatment-batch2'
for path in (RULES_DIR, TREATMENT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import sanity_treatment_dev as treatment  # noqa: E402

MODULE_ID = 'COC7_CHASE_R1_BATCH1_DEV_V1'
PARENT_SANITY_TREATMENT_MODULE_ID = treatment.MODULE_ID
FROZEN_RULES_PACKAGE_ID = core_rules.PACKAGE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
MODES = {'FOOT', 'SELF_PROPELLED', 'VEHICLE'}
DIFFICULTIES = {'REGULAR', 'HARD', 'EXTREME'}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _roll(skill_value: int, units: int, tens: list[int], bonus_dice: int = 0) -> dict:
    if not _valid_int(skill_value, 1, 100):
        return {'status': 'BLOCKED', 'code': 'CHASE_SKILL_VALUE_INVALID'}
    if not _valid_int(bonus_dice, 0, 2):
        return {'status': 'BLOCKED', 'code': 'CHASE_BONUS_DICE_INVALID'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, bonus_dice)
        level = core_rules.success_level(skill_value, roll)
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}
    return {'status': 'RESOLVED', 'roll': roll, 'success_level': level, 'success': level not in {'FAILURE','FUMBLE'}}


def speed_roll(*, mode: str, base_mov: int, skill_value: int, units: int, tens: list[int]) -> dict:
    if mode not in MODES:
        return {'status': 'BLOCKED', 'code': 'CHASE_MODE_INVALID'}
    if not _valid_int(base_mov, 0, 30):
        return {'status': 'BLOCKED', 'code': 'BASE_MOV_INVALID'}
    check = _roll(skill_value, units, tens, 0)
    if check.get('status') != 'RESOLVED':
        return check
    if check['success_level'] in {'EXTREME','CRITICAL'}:
        delta = 1
    elif check['success']:
        delta = 0
    else:
        delta = -1
    adjusted = max(0, base_mov + delta)
    return {
        'status': 'RESOLVED', 'module_id': MODULE_ID, 'mode': mode,
        'required_skill_family': 'DRIVE_AUTO' if mode == 'VEHICLE' else 'CON',
        'roll': check['roll'], 'success_level': check['success_level'],
        'base_mov': base_mov, 'mov_delta': delta, 'adjusted_mov': adjusted,
        'duration': 'CHASE', 'randomness_generated': False,
    }


def establish_chase(*, fleeing_adjusted_mov: int, pursuer_adjusted_mov: int) -> dict:
    if not _valid_int(fleeing_adjusted_mov, 0, 30) or not _valid_int(pursuer_adjusted_mov, 0, 30):
        return {'status': 'BLOCKED', 'code': 'ADJUSTED_MOV_INVALID'}
    established = pursuer_adjusted_mov >= fleeing_adjusted_mov
    return {
        'status': 'RESOLVED',
        'outcome': 'CHASE_ESTABLISHED' if established else 'FLEEING_CHARACTER_ESCAPES',
        'chase_established': established,
    }


def starting_range(*, keeper_selected_locations: int = 2, exceptional_circumstances: bool = False) -> dict:
    if not isinstance(exceptional_circumstances, bool):
        return {'status': 'BLOCKED', 'code': 'EXCEPTIONAL_FLAG_INVALID'}
    if keeper_selected_locations not in {1,2}:
        return {'status': 'BLOCKED', 'code': 'STARTING_RANGE_OUTSIDE_BATCH1'}
    if keeper_selected_locations == 1 and not exceptional_circumstances:
        return {'status': 'BLOCKED', 'code': 'ONE_LOCATION_REQUIRES_EXCEPTIONAL_KEEPER_GATE'}
    return {'status': 'RESOLVED', 'starting_range_locations': keeper_selected_locations, 'keeper_selected': True}


def movement_actions(*, adjusted_mov: int, slowest_adjusted_mov: int) -> dict:
    if not _valid_int(adjusted_mov,0,30) or not _valid_int(slowest_adjusted_mov,0,30):
        return {'status': 'BLOCKED', 'code': 'MOVEMENT_ACTION_MOV_INVALID'}
    if adjusted_mov < slowest_adjusted_mov:
        return {'status': 'BLOCKED', 'code': 'PARTICIPANT_BELOW_DECLARED_SLOWEST_MOV'}
    actions = 1 + adjusted_mov - slowest_adjusted_mov
    return {'status': 'RESOLVED', 'movement_actions': actions, 'minimum_one': actions >= 1}


def dex_order(*, participants: list[dict]) -> dict:
    if not isinstance(participants, list) or not participants:
        return {'status': 'BLOCKED', 'code': 'CHASE_PARTICIPANTS_REQUIRED'}
    normalized=[]
    for p in participants:
        if not isinstance(p,dict) or not isinstance(p.get('id'),str) or not p.get('id') or not _valid_int(p.get('dex'),0,100):
            return {'status': 'BLOCKED', 'code': 'CHASE_PARTICIPANT_INVALID'}
        normalized.append({'id':p['id'],'dex':p['dex']})
    ordered=sorted(normalized,key=lambda p:(-p['dex'],p['id']))
    ties=[]
    by_dex={}
    for p in normalized:
        by_dex.setdefault(p['dex'],[]).append(p['id'])
    for dex, ids in by_dex.items():
        if len(ids)>1:
            ties.append({'dex':dex,'participants':sorted(ids),'opposed_dex_roll_required':True})
    return {'status':'RESOLVED','provisional_order':[p['id'] for p in ordered],'ties':ties,'ties_require_opposed_dex_roll':bool(ties)}


def clear_location_move(*, movement_actions_available: int) -> dict:
    if not _valid_int(movement_actions_available,0):
        return {'status':'BLOCKED','code':'MOVEMENT_ACTIONS_INVALID'}
    if movement_actions_available < 1:
        return {'status':'BLOCKED','code':'INSUFFICIENT_MOVEMENT_ACTIONS'}
    return {'status':'RESOLVED','advanced_locations':1,'movement_actions_spent':1,'movement_actions_remaining':movement_actions_available-1}


def hazard_plan(*, difficulty: str, cautious_actions_spent: int) -> dict:
    if difficulty not in DIFFICULTIES:
        return {'status':'BLOCKED','code':'HAZARD_DIFFICULTY_INVALID'}
    if not _valid_int(cautious_actions_spent,0,2):
        return {'status':'BLOCKED','code':'CAUTIOUS_ACTIONS_INVALID'}
    return {'status':'RESOLVED','difficulty':difficulty,'bonus_dice':cautious_actions_spent,'cautious_actions_spent':cautious_actions_spent}


def resolve_hazard(
    *,
    plan: dict,
    skill_value: int,
    units: int,
    tens: list[int],
    recorded_lost_actions_d3: int | None = None,
    keeper_selected_damage: int | None = None,
) -> dict:
    if not isinstance(plan,dict) or plan.get('status')!='RESOLVED':
        return {'status':'BLOCKED','code':'HAZARD_PLAN_REQUIRED'}
    check=_roll(skill_value,units,tens,plan['bonus_dice'])
    if check.get('status')!='RESOLVED':
        return check
    meets=core_rules.meets_difficulty(skill_value,check['roll'],plan['difficulty'])
    if meets['success']:
        if recorded_lost_actions_d3 is not None or keeper_selected_damage is not None:
            return {'status':'BLOCKED','code':'HAZARD_SUCCESS_MUST_NOT_CONSUME_FAILURE_OUTCOMES'}
        return {
            'status':'RESOLVED','success':True,'roll':check['roll'],'success_level':check['success_level'],
            'advanced_to_next_location':True,'lost_movement_actions':0,'damage':0,
            'randomness_generated':False,
        }
    if not _valid_int(recorded_lost_actions_d3,1,3):
        return {'status':'BLOCKED','code':'RECORDED_HAZARD_D3_REQUIRED'}
    if keeper_selected_damage is not None and not _valid_int(keeper_selected_damage,0):
        return {'status':'BLOCKED','code':'KEEPER_SELECTED_DAMAGE_INVALID'}
    return {
        'status':'RESOLVED','success':False,'roll':check['roll'],'success_level':check['success_level'],
        'advanced_to_next_location':True,'lost_movement_actions':recorded_lost_actions_d3,
        'damage':0 if keeper_selected_damage is None else keeper_selected_damage,
        'damage_selected_by_keeper':keeper_selected_damage is not None,
        'randomness_generated':False,
    }


def barrier_plan(*, difficulty: str, cautious_actions_spent: int = 0) -> dict:
    if difficulty not in DIFFICULTIES:
        return {'status':'BLOCKED','code':'BARRIER_DIFFICULTY_INVALID'}
    if not _valid_int(cautious_actions_spent,0,2):
        return {'status':'BLOCKED','code':'CAUTIOUS_ACTIONS_INVALID'}
    return {'status':'RESOLVED','difficulty':difficulty,'bonus_dice':cautious_actions_spent,'cautious_actions_spent':cautious_actions_spent}


def resolve_barrier(*, plan: dict, skill_value: int, units: int, tens: list[int]) -> dict:
    if not isinstance(plan,dict) or plan.get('status')!='RESOLVED':
        return {'status':'BLOCKED','code':'BARRIER_PLAN_REQUIRED'}
    check=_roll(skill_value,units,tens,plan['bonus_dice'])
    if check.get('status')!='RESOLVED':
        return check
    meets=core_rules.meets_difficulty(skill_value,check['roll'],plan['difficulty'])
    return {
        'status':'RESOLVED','success':meets['success'],'roll':check['roll'],'success_level':check['success_level'],
        'advanced_to_next_location':meets['success'],
        'keeper_may_select_damage_or_delay_on_failure':not meets['success'],
        'automatic_damage_or_delay':False,
        'randomness_generated':False,
    }


def chase_attack_gate(*, movement_actions_available: int, same_location: bool, firearm_attack: bool) -> dict:
    if not _valid_int(movement_actions_available,0) or not isinstance(same_location,bool) or not isinstance(firearm_attack,bool):
        return {'status':'BLOCKED','code':'CHASE_ATTACK_INPUT_INVALID'}
    if movement_actions_available < 1:
        return {'status':'BLOCKED','code':'ATTACK_REQUIRES_ONE_MOVEMENT_ACTION'}
    if not same_location and not firearm_attack:
        return {'status':'BLOCKED','code':'NON_FIREARM_ATTACK_REQUIRES_SAME_LOCATION'}
    return {
        'status':'RESOLVED','attack_allowed':True,'movement_actions_spent':1,
        'movement_actions_remaining':movement_actions_available-1,
        'defensive_response_allowed_even_if_defender_has_no_actions':True,
    }


def pushed_roll_policy() -> dict:
    return {'status':'RESOLVED','pushed_rolls_allowed':False}
