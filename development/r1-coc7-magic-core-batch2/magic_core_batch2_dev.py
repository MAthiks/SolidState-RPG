from __future__ import annotations

import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RULES_DIR=ROOT/'recovery'/'recertification-r1'
MAGIC1_DIR=ROOT/'development'/'r1-coc7-magic-core-batch1'
for path in (RULES_DIR,MAGIC1_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0,str(path))

from rules_r1 import core_rules  # noqa: E402
import magic_core_dev as magic1  # noqa: E402

MODULE_ID='COC7_MAGIC_CORE_R1_BATCH2_DEV_V1'
PARENT_MAGIC_MODULE_ID=magic1.MODULE_ID
FROZEN_RULES_PACKAGE_ID=core_rules.PACKAGE_ID
KEEPER_SOURCE_ID='COC7_KEEPER'
KEEPER_SHA256='691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
BELIEF_REASONS={'PLAYER_CHOICE','FIRSTHAND_MYTHOS_SAN_LOSS','CLEARLY_UNEARTHLY_KEEPER_GATE'}
POW_EXERCISE_SOURCES={'SPELL_OPPOSED_POW_WIN','LUCK_ROLL_01'}


def _valid_int(value,minimum=None,maximum=None):
    if not isinstance(value,int) or isinstance(value,bool): return False
    if minimum is not None and value<minimum: return False
    if maximum is not None and value>maximum: return False
    return True


def disrupted_casting(*,significant_distraction:bool,mp_cost:int,san_cost:int) -> dict:
    if not isinstance(significant_distraction,bool) or not _valid_int(mp_cost,0) or not _valid_int(san_cost,0):
        return {'status':'BLOCKED','code':'DISRUPTED_CAST_INPUT_INVALID'}
    return {
        'status':'RESOLVED','module_id':MODULE_ID,'disrupted':significant_distraction,
        'spell_effect_proceeds':not significant_distraction,
        'mp_cost_still_due':mp_cost if significant_distraction else 0,
        'san_cost_still_due':san_cost if significant_distraction else 0,
        'automatic_side_effect_selection':False,
        'keeper_may_use_pushed_failure_consequence_as_inspiration':significant_distraction,
        'randomness_generated':False,
    }


def believer_transition(*,believer_before:bool,current_san:int,current_mythos:int,reason:str,firsthand_mythos_san_loss:int=0,keeper_confirms_clearly_unearthly:bool=False) -> dict:
    if not isinstance(believer_before,bool) or not _valid_int(current_san,0,99) or not _valid_int(current_mythos,0,99):
        return {'status':'BLOCKED','code':'BELIEF_STATE_INVALID'}
    if current_san>99-current_mythos:
        return {'status':'BLOCKED','code':'CURRENT_SAN_EXCEEDS_MYTHOS_MAXIMUM'}
    if reason not in BELIEF_REASONS or not _valid_int(firsthand_mythos_san_loss,0) or not isinstance(keeper_confirms_clearly_unearthly,bool):
        return {'status':'BLOCKED','code':'BELIEF_TRIGGER_INVALID'}
    if believer_before:
        return {'status':'RESOLVED','believer':True,'changed':False,'additional_san_loss':0,'SAN':current_san,'feed_loss_into_sanity_state_machine':False}
    if reason=='FIRSTHAND_MYTHOS_SAN_LOSS' and firsthand_mythos_san_loss<1:
        return {'status':'BLOCKED','code':'FIRSTHAND_MYTHOS_BELIEF_REQUIRES_SAN_LOSS'}
    if reason=='CLEARLY_UNEARTHLY_KEEPER_GATE' and not keeper_confirms_clearly_unearthly:
        return {'status':'BLOCKED','code':'KEEPER_UNEARTHLY_GATE_REQUIRED'}
    additional_loss=min(current_san,current_mythos)
    return {
        'status':'RESOLVED','believer':True,'changed':True,'reason':reason,
        'firsthand_mythos_san_loss':firsthand_mythos_san_loss,
        'additional_san_loss':additional_loss,'SAN':current_san-additional_loss,
        'feed_loss_into_sanity_state_machine':additional_loss>0,
        'automatic_mythos_entity_classification':False,
        'randomness_generated':False,
    }


def human_horror_belief_gate(*,san_loss:int) -> dict:
    if not _valid_int(san_loss,0):
        return {'status':'BLOCKED','code':'HUMAN_HORROR_SAN_LOSS_INVALID'}
    return {'status':'RESOLVED','san_loss':san_loss,'forces_mythos_belief':False}


def nonbeliever_spell_access(*,believer:bool,spell_learned:bool) -> dict:
    if not isinstance(believer,bool) or not isinstance(spell_learned,bool):
        return {'status':'BLOCKED','code':'SPELL_ACCESS_FLAG_INVALID'}
    return {
        'status':'RESOLVED','may_learn_spell':True,'spell_learned':spell_learned,
        'may_cast_spell':believer and spell_learned,
        'blocked_reason':None if believer and spell_learned else ('NONBELIEVER_CANNOT_CAST' if spell_learned and not believer else 'SPELL_NOT_LEARNED'),
    }


def pow_exercise_chance(*,source:str,opposed_pow_won:bool=False,luck_roll:int|None=None) -> dict:
    if source not in POW_EXERCISE_SOURCES or not isinstance(opposed_pow_won,bool):
        return {'status':'BLOCKED','code':'POW_EXERCISE_SOURCE_INVALID'}
    if source=='SPELL_OPPOSED_POW_WIN':
        eligible=opposed_pow_won
        if luck_roll is not None:
            return {'status':'BLOCKED','code':'LUCK_ROLL_UNUSED_FOR_SPELL_EXERCISE'}
    else:
        if not _valid_int(luck_roll,1,100):
            return {'status':'BLOCKED','code':'LUCK_ROLL_REQUIRED'}
        eligible=luck_roll==1
        if opposed_pow_won:
            return {'status':'BLOCKED','code':'OPPOSED_POW_FLAG_UNUSED_FOR_LUCK_EXERCISE'}
    return {'status':'RESOLVED','source':source,'exercise_eligible':eligible}


def resolve_pow_exercise(*,current_pow:int,exercise_eligible:bool,recorded_percentile:int|None,recorded_gain_d10:int|None) -> dict:
    if not _valid_int(current_pow,0) or not isinstance(exercise_eligible,bool):
        return {'status':'BLOCKED','code':'POW_EXERCISE_INPUT_INVALID'}
    if not exercise_eligible:
        if recorded_percentile is not None or recorded_gain_d10 is not None:
            return {'status':'BLOCKED','code':'INELIGIBLE_POW_EXERCISE_MUST_NOT_CONSUME_DICE'}
        return {'status':'RESOLVED','exercise_eligible':False,'POW':current_pow,'pow_gain':0,'current_san_increase':0,'randomness_generated':False}
    if not _valid_int(recorded_percentile,1,100):
        return {'status':'BLOCKED','code':'RECORDED_POW_EXERCISE_PERCENTILE_REQUIRED'}
    success=recorded_percentile>current_pow or recorded_percentile>=96
    if success:
        if not _valid_int(recorded_gain_d10,1,10):
            return {'status':'BLOCKED','code':'RECORDED_POW_GAIN_D10_REQUIRED'}
        gain=recorded_gain_d10
    else:
        if recorded_gain_d10 is not None:
            return {'status':'BLOCKED','code':'FAILED_POW_EXERCISE_MUST_NOT_CONSUME_GAIN_D10'}
        gain=0
    return {
        'status':'RESOLVED','exercise_eligible':True,'exercise_roll':recorded_percentile,
        'exercise_success':success,'pow_gain':gain,'POW':current_pow+gain,
        'current_san_increase':0,'natural_mp_max_after_pow_gain':(current_pow+gain)//5,
        'randomness_generated':False,
    }


def non_mythos_magic_plan(*,keeper_enabled:bool,skill_id:str,effect_truth_status:str,horrific_deed:bool,keeper_san_cost:int|None) -> dict:
    if not isinstance(keeper_enabled,bool) or not isinstance(skill_id,str) or not skill_id or not isinstance(effect_truth_status,str) or not effect_truth_status or not isinstance(horrific_deed,bool):
        return {'status':'BLOCKED','code':'NON_MYTHOS_MAGIC_INPUT_INVALID'}
    if not keeper_enabled:
        return {'status':'BLOCKED','code':'NON_MYTHOS_MAGIC_NOT_ENABLED'}
    if skill_id!='OCCULT':
        return {'status':'BLOCKED','code':'NON_MYTHOS_MAGIC_SKILL_UNMATERIALIZED'}
    if horrific_deed:
        if not _valid_int(keeper_san_cost,0):
            return {'status':'BLOCKED','code':'KEEPER_SAN_COST_REQUIRED_FOR_HORRIFIC_MAGIC'}
    elif keeper_san_cost not in (None,0):
        return {'status':'BLOCKED','code':'UNNEEDED_NON_HORRIFIC_SAN_COST'}
    return {
        'status':'RESOLVED','skill_id':'OCCULT','effect_truth_status':effect_truth_status,
        'uses_mythos_magic_generic_procedure':True,'keeper_defined_effect':True,
        'horrific_deed':horrific_deed,'san_cost':0 if keeper_san_cost is None else keeper_san_cost,
        'automatic_effect_generation':False,
    }


def spontaneous_mythos_plan(*,optional_rule_enabled:bool,player_aim:str,keeper_accepts:bool,keeper_lesser_aim:str|None,target_resists:bool,mp_cost:int|None,san_cost:int|None) -> dict:
    if not isinstance(optional_rule_enabled,bool) or not isinstance(player_aim,str) or not player_aim.strip() or not isinstance(keeper_accepts,bool) or not isinstance(target_resists,bool):
        return {'status':'BLOCKED','code':'SPONTANEOUS_MYTHOS_INPUT_INVALID'}
    if not optional_rule_enabled:
        return {'status':'BLOCKED','code':'SPONTANEOUS_MYTHOS_OPTION_NOT_ENABLED'}
    if keeper_accepts:
        if keeper_lesser_aim is not None:
            return {'status':'BLOCKED','code':'LESSER_AIM_UNUSED_WHEN_ORIGINAL_ACCEPTED'}
        effective_aim=player_aim.strip()
    else:
        if not isinstance(keeper_lesser_aim,str) or not keeper_lesser_aim.strip():
            return {'status':'BLOCKED','code':'KEEPER_LESSER_AIM_REQUIRED'}
        effective_aim=keeper_lesser_aim.strip()
    if not _valid_int(mp_cost,0) or not _valid_int(san_cost,0):
        return {'status':'BLOCKED','code':'KEEPER_SPONTANEOUS_COSTS_REQUIRED'}
    return {
        'status':'RESOLVED','player_aim':player_aim.strip(),'effective_aim':effective_aim,
        'keeper_reduced_aim':not keeper_accepts,'target_resists':target_resists,
        'resolution':'OPPOSED_MYTHOS_VS_POW' if target_resists else 'REGULAR_MYTHOS',
        'difficulty':None if target_resists else 'REGULAR','mp_cost':mp_cost,'san_cost':san_cost,
        'roll_required_every_use':True,'automatic_aim_rewrite':False,'automatic_cost_selection':False,
    }


def resolve_spontaneous_mythos(*,plan:dict,mythos_value:int,mythos_roll:int,target_pow:int|None=None,target_pow_roll:int|None=None) -> dict:
    if not isinstance(plan,dict) or plan.get('status')!='RESOLVED':
        return {'status':'BLOCKED','code':'SPONTANEOUS_MYTHOS_PLAN_REQUIRED'}
    if not _valid_int(mythos_value,0,100) or not _valid_int(mythos_roll,1,100):
        return {'status':'BLOCKED','code':'SPONTANEOUS_MYTHOS_ROLL_INVALID'}
    if plan['target_resists']:
        if not _valid_int(target_pow,0,100) or not _valid_int(target_pow_roll,1,100):
            return {'status':'BLOCKED','code':'TARGET_POW_OPPOSED_ROLL_REQUIRED'}
        opposed=core_rules.opposed(mythos_value,mythos_roll,target_pow,target_pow_roll)
        success=opposed['winner']=='A'
        tie=opposed['winner']=='TIE_REROLL_OR_IMPASSE'
        return {
            'status':'RESOLVED','resolution':'OPPOSED_MYTHOS_VS_POW','mythos_roll':mythos_roll,
            'target_pow_roll':target_pow_roll,'opposed':opposed,'success':success,'tie_requires_keeper_resolution_or_reroll':tie,
            'no_second_pow_vs_pow_roll':True,'push_allowed':not success and not tie,
            'pushed_failure_aim_guaranteed':False,'randomness_generated':False,
        }
    if target_pow is not None or target_pow_roll is not None:
        return {'status':'BLOCKED','code':'TARGET_POW_UNUSED_FOR_UNRESISTED_MYTHOS_USE'}
    judged=core_rules.meets_difficulty(mythos_value,mythos_roll,'REGULAR')
    return {
        'status':'RESOLVED','resolution':'REGULAR_MYTHOS','mythos_roll':mythos_roll,
        'success_level':judged['level'],'success':judged['success'],'push_allowed':not judged['success'],
        'pushed_failure_aim_guaranteed':False,'randomness_generated':False,
    }


def spontaneous_push_framework(*,plan:dict,recorded_multiplier_d6:int,fixed_mp_cost:int|None=None,fixed_san_cost:int|None=None) -> dict:
    if not isinstance(plan,dict) or plan.get('status')!='RESOLVED':
        return {'status':'BLOCKED','code':'SPONTANEOUS_MYTHOS_PLAN_REQUIRED'}
    if fixed_mp_cost is not None or fixed_san_cost is not None:
        return {'status':'BLOCKED','code':'SPONTANEOUS_PUSH_MUST_USE_PLAN_COSTS'}
    pushed=magic1.pushed_cast_failure_cost_plan(recorded_multiplier_d6=recorded_multiplier_d6,fixed_mp_cost=plan['mp_cost'],fixed_san_cost=plan['san_cost'])
    if pushed.get('status')!='RESOLVED':
        return pushed
    return {
        'status':'RESOLVED','multiplier':pushed['multiplier'],'additional_mp_cost':pushed['additional_mp_cost'],
        'additional_san_cost':pushed['additional_san_cost'],'keeper_side_effect_selection_required':True,
        'aim_achieved_on_failed_push':'KEEPER_DECISION_NOT_GUARANTEED','automatic_aim_success':False,
        'randomness_generated':False,
    }
