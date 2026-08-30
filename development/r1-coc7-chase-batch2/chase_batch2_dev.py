from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
CHASE1_DIR = ROOT / 'development' / 'r1-coc7-chase-batch1'
for path in (RULES_DIR, CHASE1_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import chase_dev as chase1  # noqa: E402

MODULE_ID = 'COC7_CHASE_R1_BATCH2_DEV_V1'
PARENT_CHASE_MODULE_ID = chase1.MODULE_ID
FROZEN_RULES_PACKAGE_ID = core_rules.PACKAGE_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'

COLLISION_DICE = {
    'MINOR': (1, 3, -1),
    'MODERATE': (1, 6, 0),
    'SEVERE': (1, 10, 0),
    'MAYHEM': (2, 10, 0),
    'ROAD_KILL': (5, 10, 0),
}


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _recorded_dice(values, *, count: int, sides: int, code: str):
    if not isinstance(values, list) or len(values) != count:
        return {'status': 'BLOCKED', 'code': code}
    if any(not _valid_int(v, 1, sides) for v in values):
        return {'status': 'BLOCKED', 'code': code}
    return {'status': 'RESOLVED', 'values': list(values), 'total': sum(values)}


def acceleration_plan(*, locations: int, navigation_assist_success: bool = False) -> dict:
    if not _valid_int(locations, 1, 5) or not isinstance(navigation_assist_success, bool):
        return {'status': 'BLOCKED', 'code': 'ACCELERATION_INPUT_INVALID'}
    if locations == 1:
        base_penalty = 0
        accelerated = False
    elif locations <= 3:
        base_penalty = 1
        accelerated = True
    else:
        base_penalty = 2
        accelerated = True
    applied = max(0, base_penalty - (1 if navigation_assist_success and accelerated else 0))
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'declared_locations': locations,
        'accelerated': accelerated,
        'base_hazard_penalty_dice': base_penalty,
        'navigation_assist_applied': navigation_assist_success and accelerated,
        'hazard_penalty_dice': applied,
        'movement_actions_spent': 1,
        'declaration_irrevocable_until_hazard_failure': accelerated,
    }


def acceleration_progress(*, declared_locations: int, completed_locations: int, hazard_failed: bool) -> dict:
    if not _valid_int(declared_locations, 1, 5) or not _valid_int(completed_locations, 0, declared_locations) or not isinstance(hazard_failed, bool):
        return {'status': 'BLOCKED', 'code': 'ACCELERATION_PROGRESS_INPUT_INVALID'}
    if hazard_failed and completed_locations >= declared_locations:
        return {'status': 'BLOCKED', 'code': 'HAZARD_FAILURE_REQUIRES_UNFINISHED_DECLARED_MOVE'}
    remaining = 0 if hazard_failed else declared_locations - completed_locations
    return {
        'status': 'RESOLVED',
        'hazard_failed': hazard_failed,
        'declared_locations': declared_locations,
        'completed_locations': completed_locations,
        'remaining_locations_in_same_action': remaining,
        'must_pay_new_movement_action_to_continue': hazard_failed,
    }


def vehicle_state_after_build_damage(*, starting_build: int, current_build: int, incident_build_damage: int) -> dict:
    if not _valid_int(starting_build, 1) or not _valid_int(current_build, 0, starting_build) or not _valid_int(incident_build_damage, 0):
        return {'status': 'BLOCKED', 'code': 'VEHICLE_BUILD_STATE_INPUT_INVALID'}
    complete_wreck = incident_build_damage >= starting_build
    new_build = 0 if complete_wreck else max(0, current_build - incident_build_damage)
    cumulative_zero = new_build == 0 and not complete_wreck
    impaired_threshold = starting_build // 2
    impaired = new_build > 0 and new_build <= impaired_threshold
    return {
        'status': 'RESOLVED',
        'starting_build': starting_build,
        'previous_build': current_build,
        'incident_build_damage': incident_build_damage,
        'build': new_build,
        'complete_wreck_single_incident': complete_wreck,
        'undriveable_cumulative_zero': cumulative_zero,
        'out_of_action': new_build == 0,
        'impaired': impaired,
        'drive_penalty_dice': 1 if impaired else 0,
        'keeper_survival_gate_required': complete_wreck,
    }


def collision_damage(*, incident: str, recorded_dice: list[int]) -> dict:
    spec = COLLISION_DICE.get(incident)
    if spec is None:
        return {'status': 'BLOCKED', 'code': 'COLLISION_INCIDENT_INVALID'}
    count, sides, modifier = spec
    checked = _recorded_dice(recorded_dice, count=count, sides=sides, code='RECORDED_COLLISION_DICE_INVALID')
    if checked['status'] != 'RESOLVED':
        return checked
    total = max(0, checked['total'] + modifier)
    return {
        'status': 'RESOLVED',
        'incident': incident,
        'recorded_dice': checked['values'],
        'modifier': modifier,
        'damage': total,
        'damage_unit_context_required': True,
        'randomness_generated': False,
    }


def resolve_vehicle_collision(
    *,
    incident: str,
    starting_build: int,
    current_build: int,
    recorded_vehicle_dice: list[int],
    recorded_delay_d3: int,
) -> dict:
    damage = collision_damage(incident=incident, recorded_dice=recorded_vehicle_dice)
    if damage.get('status') != 'RESOLVED':
        return damage
    if not _valid_int(recorded_delay_d3, 1, 3):
        return {'status': 'BLOCKED', 'code': 'RECORDED_COLLISION_DELAY_D3_INVALID'}
    state = vehicle_state_after_build_damage(
        starting_build=starting_build,
        current_build=current_build,
        incident_build_damage=damage['damage'],
    )
    if state.get('status') != 'RESOLVED':
        return state
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'incident': incident,
        'vehicle_build_damage': damage['damage'],
        'vehicle_state': state,
        'lost_movement_actions': recorded_delay_d3,
        'occupant_damage_roll_required_per_occupant': True,
        'occupant_damage_uses_same_collision_dice_expression': True,
        'randomness_generated': False,
    }


def resolve_collision_occupant_damage(*, incident: str, recorded_dice: list[int], armor: int = 0) -> dict:
    if not _valid_int(armor, 0):
        return {'status': 'BLOCKED', 'code': 'OCCUPANT_ARMOR_INVALID'}
    damage = collision_damage(incident=incident, recorded_dice=recorded_dice)
    if damage.get('status') != 'RESOLVED':
        return damage
    hp_damage = max(0, damage['damage'] - armor)
    return {
        'status': 'RESOLVED',
        'incident': incident,
        'raw_hit_point_damage': damage['damage'],
        'armor': armor,
        'hit_point_damage': hp_damage,
        'randomness_generated': False,
    }


def barrier_ram(*, vehicle_build: int, barrier_hp_before: int, recorded_d10: list[int]) -> dict:
    if not _valid_int(vehicle_build, 1) or not _valid_int(barrier_hp_before, 1):
        return {'status': 'BLOCKED', 'code': 'BARRIER_RAM_INPUT_INVALID'}
    checked = _recorded_dice(recorded_d10, count=vehicle_build, sides=10, code='RECORDED_BARRIER_RAM_D10_INVALID')
    if checked['status'] != 'RESOLVED':
        return checked
    inflicted = checked['total']
    destroyed = inflicted >= barrier_hp_before
    if not destroyed:
        return {
            'status': 'RESOLVED',
            'barrier_damage': inflicted,
            'barrier_hp_after': barrier_hp_before - inflicted,
            'barrier_destroyed': False,
            'vehicle_wrecked': True,
            'vehicle_self_hit_point_damage': None,
            'randomness_generated': False,
        }
    self_hp = barrier_hp_before // 2
    self_build_loss = self_hp // 10
    return {
        'status': 'RESOLVED',
        'barrier_damage': inflicted,
        'barrier_hp_after': 0,
        'barrier_destroyed': True,
        'vehicle_wrecked': False,
        'vehicle_self_hit_point_damage': self_hp,
        'vehicle_self_build_loss_from_hit_points': self_build_loss,
        'vehicle_build_after': max(0, vehicle_build - self_build_loss),
        'debris_may_become_hazard_keeper_gate': True,
        'randomness_generated': False,
    }


def vehicle_conflict_attack(*, attacker_build: int, target_build: int, recorded_d10: list[int]) -> dict:
    if not _valid_int(attacker_build, 1) or not _valid_int(target_build, 1):
        return {'status': 'BLOCKED', 'code': 'VEHICLE_CONFLICT_BUILD_INVALID'}
    checked = _recorded_dice(recorded_d10, count=attacker_build, sides=10, code='RECORDED_VEHICLE_ATTACK_D10_INVALID')
    if checked['status'] != 'RESOLVED':
        return checked
    delivered_hp = checked['total']
    target_build_loss = min(target_build, delivered_hp // 10)
    self_hp = delivered_hp // 2
    raw_self_build_loss = self_hp // 10
    self_build_loss = min(raw_self_build_loss, target_build)
    return {
        'status': 'RESOLVED',
        'delivered_hit_point_damage': delivered_hp,
        'target_build_loss': target_build_loss,
        'target_build_after': max(0, target_build - target_build_loss),
        'attacker_self_hit_point_damage': self_hp,
        'attacker_self_build_loss_uncapped': raw_self_build_loss,
        'attacker_self_build_loss': self_build_loss,
        'attacker_build_after': max(0, attacker_build - self_build_loss),
        'self_build_loss_capped_by_target_original_build': self_build_loss < raw_self_build_loss,
        'randomness_generated': False,
    }


def vehicle_maneuver_plan(*, attacker_build: int, target_build: int) -> dict:
    if not _valid_int(attacker_build, 0) or not _valid_int(target_build, 0):
        return {'status': 'BLOCKED', 'code': 'VEHICLE_MANEUVER_BUILD_INVALID'}
    difference = target_build - attacker_build
    if difference >= 3:
        return {'status': 'BLOCKED', 'code': 'VEHICLE_MANEUVER_IMPOSSIBLE_BUILD_DIFFERENCE', 'build_difference': difference}
    penalty = 2 if difference == 2 else (1 if difference == 1 else 0)
    return {
        'status': 'RESOLVED',
        'build_difference': difference,
        'penalty_dice': penalty,
        'successful_maneuver_uses_hazard_failure_outcome': True,
    }


def vehicle_maneuver_success(*, recorded_lost_actions_d3: int, collision_incident: str | None = None) -> dict:
    if not _valid_int(recorded_lost_actions_d3, 1, 3):
        return {'status': 'BLOCKED', 'code': 'RECORDED_MANEUVER_LOST_ACTIONS_D3_INVALID'}
    if collision_incident is not None and collision_incident not in COLLISION_DICE:
        return {'status': 'BLOCKED', 'code': 'MANEUVER_COLLISION_INCIDENT_INVALID'}
    return {
        'status': 'RESOLVED',
        'lost_movement_actions': recorded_lost_actions_d3,
        'collision_damage_required': collision_incident is not None,
        'collision_incident': collision_incident,
        'specific_regular_combat_goal_may_replace_default': True,
    }


def driver_major_wound_control(*, conscious: bool) -> dict:
    if not isinstance(conscious, bool):
        return {'status': 'BLOCKED', 'code': 'DRIVER_CONSCIOUS_FLAG_INVALID'}
    return {
        'status': 'RESOLVED',
        'automatic_loss_of_control': not conscious,
        'immediate_hazard_roll_required': conscious,
        'hazard_difficulty': 'HARD' if conscious else None,
    }


def chase_ranged_attack_plan(*, moving: bool, on_foot: bool, movement_actions_available: int) -> dict:
    if not isinstance(moving, bool) or not isinstance(on_foot, bool) or not _valid_int(movement_actions_available, 0):
        return {'status': 'BLOCKED', 'code': 'CHASE_RANGED_INPUT_INVALID'}
    if not moving and on_foot:
        if movement_actions_available < 1:
            return {'status': 'BLOCKED', 'code': 'STATIONARY_FOOT_FIRE_REQUIRES_MOVEMENT_ACTION'}
        return {
            'status': 'RESOLVED',
            'extra_penalty_dice': 0,
            'movement_actions_spent': 1,
            'movement_actions_remaining': movement_actions_available - 1,
            'movement_made': False,
        }
    return {
        'status': 'RESOLVED',
        'extra_penalty_dice': 1 if moving else 0,
        'movement_actions_spent': 0,
        'movement_actions_remaining': movement_actions_available,
        'movement_made': moving,
    }


def tire_damage(*, raw_damage: int, impaling_weapon: bool, already_burst: bool = False) -> dict:
    if not _valid_int(raw_damage, 0) or not isinstance(impaling_weapon, bool) or not isinstance(already_burst, bool):
        return {'status': 'BLOCKED', 'code': 'TIRE_DAMAGE_INPUT_INVALID'}
    if already_burst:
        return {'status': 'RESOLVED', 'already_burst': True, 'new_burst': False, 'vehicle_build_loss': 0, 'damage_after_armor': 0}
    if not impaling_weapon:
        return {'status': 'RESOLVED', 'already_burst': False, 'new_burst': False, 'vehicle_build_loss': 0, 'damage_after_armor': 0, 'ignored_non_impaling': True}
    after_armor = max(0, raw_damage - 3)
    burst = after_armor >= 2
    return {
        'status': 'RESOLVED',
        'already_burst': False,
        'new_burst': burst,
        'vehicle_build_loss': 1 if burst else 0,
        'damage_after_armor': after_armor,
        'extra_targeting_penalty_dice': 1,
    }


def multiple_participant_layout(*, pursuers: list[dict], fleeing: list[dict], fleeing_choose_escape_ids: list[str] | None = None) -> dict:
    if not isinstance(pursuers, list) or not pursuers or not isinstance(fleeing, list) or not fleeing:
        return {'status': 'BLOCKED', 'code': 'MULTI_CHASE_GROUPS_REQUIRED'}
    fleeing_choose_escape_ids = [] if fleeing_choose_escape_ids is None else fleeing_choose_escape_ids
    if not isinstance(fleeing_choose_escape_ids, list) or any(not isinstance(x, str) for x in fleeing_choose_escape_ids):
        return {'status': 'BLOCKED', 'code': 'FLEEING_ESCAPE_SELECTION_INVALID'}

    def normalize(group):
        result=[]
        seen=set()
        for p in group:
            if not isinstance(p, dict) or not isinstance(p.get('id'), str) or not p.get('id') or not _valid_int(p.get('mov'), 0, 30) or p['id'] in seen:
                return None
            seen.add(p['id'])
            result.append({'id': p['id'], 'mov': p['mov']})
        return result

    p = normalize(pursuers)
    f = normalize(fleeing)
    if p is None or f is None:
        return {'status': 'BLOCKED', 'code': 'MULTI_CHASE_PARTICIPANT_INVALID'}

    fastest_pursuer = max(x['mov'] for x in p)
    slowest_fleeing = min(x['mov'] for x in f)
    escape_eligible = sorted(x['id'] for x in f if x['mov'] > fastest_pursuer)
    invalid_escape = sorted(set(fleeing_choose_escape_ids) - set(escape_eligible))
    if invalid_escape:
        return {'status': 'BLOCKED', 'code': 'FLEEING_ESCAPE_SELECTION_NOT_ELIGIBLE', 'ids': invalid_escape}

    active_f = [x for x in f if x['id'] not in set(fleeing_choose_escape_ids)]
    if not active_f:
        return {
            'status': 'RESOLVED',
            'chase_continues': False,
            'escape_eligible': escape_eligible,
            'escaped_by_choice': sorted(fleeing_choose_escape_ids),
            'positions': {},
        }
    new_slowest_fleeing = min(x['mov'] for x in active_f)
    active_p = [x for x in p if x['mov'] >= new_slowest_fleeing]
    left_behind = sorted(x['id'] for x in p if x['mov'] < new_slowest_fleeing)
    if not active_p:
        return {
            'status': 'RESOLVED',
            'chase_continues': False,
            'escape_eligible': escape_eligible,
            'escaped_by_choice': sorted(fleeing_choose_escape_ids),
            'pursuers_left_behind': left_behind,
            'positions': {},
        }

    slowest_pursuer_mov = min(x['mov'] for x in active_p)
    positions = {x['id']: x['mov'] - slowest_pursuer_mov for x in active_p}
    foremost_pursuer = max(positions.values())
    slowest_active_fleeing = min(x['mov'] for x in active_f)
    fleeing_base = foremost_pursuer + 2
    for x in active_f:
        positions[x['id']] = fleeing_base + (x['mov'] - slowest_active_fleeing)

    slowest_all = min([x['mov'] for x in active_p] + [x['mov'] for x in active_f])
    movement = {x['id']: 1 + x['mov'] - slowest_all for x in active_p + active_f}
    return {
        'status': 'RESOLVED',
        'chase_continues': True,
        'escape_eligible': escape_eligible,
        'escaped_by_choice': sorted(fleeing_choose_escape_ids),
        'pursuers_left_behind': left_behind,
        'active_pursuers': sorted(x['id'] for x in active_p),
        'active_fleeing': sorted(x['id'] for x in active_f),
        'positions': positions,
        'movement_actions': movement,
        'automatic_escape_choice_made': False,
    }
