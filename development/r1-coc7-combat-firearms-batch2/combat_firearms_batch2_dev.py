from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = ROOT / 'recovery' / 'recertification-r1'
EQWP_DIR = ROOT / 'development' / 'r1-coc7-equipment-weapons-batch1'
BATCH1_DIR = ROOT / 'development' / 'r1-coc7-combat-firearms-batch1'
for path in (RULES_DIR, EQWP_DIR, BATCH1_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rules_r1 import core_rules  # noqa: E402
import registry_eqwp_batch1_dev as registry  # noqa: E402
import combat_firearms_dev as parent  # noqa: E402

MODULE_ID = 'COC7_COMBAT_FIREARMS_R1_BATCH2_DEV_V1'
PARENT_MODULE_ID = parent.MODULE_ID
PARENT_REGISTRY_ID = registry.REGISTRY_ID
KEEPER_SOURCE_ID = 'COC7_KEEPER'
KEEPER_SHA256 = '691cd2fe986a235a42b30646811210d442954801e068fc11cece869d928bd779'
INVESTIGATOR_SOURCE_ID = 'COC7_INVESTIGATOR'
INVESTIGATOR_SHA256 = 'de81a35ab5a466340c2c0d39d036d3f69b1d38dbcc0f546aa0db7526998bed17'
SUPPORTED_DIFFICULTIES = ('REGULAR', 'HARD', 'EXTREME')


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _weapon_record(weapon_id: str):
    resolved = registry.resolve_weapon(weapon_id)
    if resolved.get('status') != 'RESOLVED_MECHANICS':
        return None
    return resolved['record']


def _capacity_options(record: dict) -> list[int]:
    text = str(record.get('capacity', ''))
    return [int(x) for x in re.findall(r'\d+', text)]


def _full_auto_capable(record: dict) -> bool:
    return 'FULL_AUTO' in str(record.get('uses_per_round', '')).upper()


def full_auto_volley_size(skill_value: int) -> dict:
    if not _valid_int(skill_value, 0, 100):
        return {'status': 'BLOCKED', 'code': 'FIREARM_SKILL_INVALID'}
    return {'status': 'RESOLVED', 'volley_size': max(skill_value // 10, 3)}


def automatic_fire_capability(weapon_id: str) -> dict:
    record = _weapon_record(weapon_id)
    if record is None:
        return {'status': 'BLOCKED', 'code': 'WEAPON_UNRESOLVED', 'weapon_id': weapon_id}
    return {
        'status': 'RESOLVED',
        'weapon_id': weapon_id,
        'full_auto': _full_auto_capable(record),
        'uses_per_round': record.get('uses_per_round'),
        'capacity_options': _capacity_options(record),
    }


def make_auto_target(
    *,
    weapon_id: str,
    allocated_rounds: int,
    distance_yards: float,
    shooter_dex: int,
    target_id: str = 'TARGET',
    aimed_prior_round: bool = False,
    aim_broken_by_move_or_damage: bool = False,
    target_dived_cover_successfully: bool = False,
    concealment_fraction: float = 0.0,
    target_mov: int = 0,
    target_full_speed: bool = False,
    target_build: int = 0,
    firing_into_melee: bool = False,
) -> dict:
    if not _valid_int(allocated_rounds, 1):
        return {'status': 'BLOCKED', 'code': 'TARGET_ALLOCATION_INVALID'}
    base = parent.attack_plan(
        weapon_id=weapon_id,
        distance_yards=distance_yards,
        shooter_dex=shooter_dex,
        shot_count=1,
        aimed_prior_round=aimed_prior_round,
        aim_broken_by_move_or_damage=aim_broken_by_move_or_damage,
        target_dived_cover_successfully=target_dived_cover_successfully,
        concealment_fraction=concealment_fraction,
        target_mov=target_mov,
        target_full_speed=target_full_speed,
        target_build=target_build,
        firing_into_melee=firing_into_melee,
    )
    if base.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'BASE_TARGET_PLAN_BLOCKED', 'detail': base}
    return {
        'status': 'RESOLVED',
        'target_id': str(target_id),
        'weapon_id': weapon_id,
        'allocated_rounds': allocated_rounds,
        'base_difficulty': base['difficulty'],
        'base_net_bonus': base['net_bonus'],
        'base_modifiers': base['modifiers'],
        'distance_yards': base['distance_yards'],
    }


def _raise_difficulty(base: str, steps: int) -> str | None:
    if base not in SUPPORTED_DIFFICULTIES or not _valid_int(steps, 0):
        return None
    index = SUPPORTED_DIFFICULTIES.index(base) + steps
    if index >= len(SUPPORTED_DIFFICULTIES):
        return None
    return SUPPORTED_DIFFICULTIES[index]


def _automatic_roll_terms(*, base_difficulty: str, base_net_bonus: int, attack_index: int) -> dict:
    if base_difficulty not in SUPPORTED_DIFFICULTIES:
        return {'status': 'BLOCKED', 'code': 'BASE_DIFFICULTY_INVALID'}
    if not _valid_int(base_net_bonus, -2, 2):
        return {'status': 'BLOCKED', 'code': 'BASE_MODIFIER_INVALID'}
    if not _valid_int(attack_index, 1):
        return {'status': 'BLOCKED', 'code': 'ATTACK_INDEX_INVALID'}

    raw_net = base_net_bonus - (attack_index - 1)
    if raw_net >= -2:
        return {
            'status': 'RESOLVED',
            'net_bonus': min(raw_net, 2),
            'difficulty': base_difficulty,
            'overflow_penalty_steps': 0,
            'raw_net_bonus': raw_net,
        }

    overflow = (-raw_net) - 2
    difficulty = _raise_difficulty(base_difficulty, overflow)
    if difficulty is None:
        return {
            'status': 'BLOCKED',
            'code': 'AUTO_VOLLEY_REQUIRES_CRITICAL_OR_IMPOSSIBLE_DIFFICULTY',
            'overflow_penalty_steps': overflow,
            'raw_net_bonus': raw_net,
        }
    return {
        'status': 'RESOLVED',
        'net_bonus': -2,
        'difficulty': difficulty,
        'overflow_penalty_steps': overflow,
        'raw_net_bonus': raw_net,
    }


def full_auto_plan(
    *,
    weapon_id: str,
    skill_value: int,
    declared_rounds: int,
    available_ammo: int,
    targets: list[dict],
    transition_yards: list[int] | None = None,
) -> dict:
    record = _weapon_record(weapon_id)
    if record is None:
        return {'status': 'BLOCKED', 'code': 'WEAPON_UNRESOLVED'}
    if not _full_auto_capable(record):
        return {'status': 'BLOCKED', 'code': 'WEAPON_NOT_FULL_AUTO_CAPABLE'}
    if not _valid_int(skill_value, 0, 100):
        return {'status': 'BLOCKED', 'code': 'FIREARM_SKILL_INVALID'}
    if not _valid_int(declared_rounds, 1):
        return {'status': 'BLOCKED', 'code': 'DECLARED_ROUNDS_INVALID'}
    if not _valid_int(available_ammo, 0):
        return {'status': 'BLOCKED', 'code': 'AVAILABLE_AMMO_INVALID'}

    capacities = _capacity_options(record)
    if not capacities:
        return {'status': 'BLOCKED', 'code': 'WEAPON_CAPACITY_UNMATERIALIZED'}
    if available_ammo > max(capacities):
        return {'status': 'BLOCKED', 'code': 'AVAILABLE_AMMO_EXCEEDS_REGISTERED_CAPACITY', 'max_capacity': max(capacities)}
    if declared_rounds > available_ammo:
        return {'status': 'BLOCKED', 'code': 'DECLARED_ROUNDS_EXCEED_AVAILABLE_AMMO'}
    if not isinstance(targets, list) or not targets:
        return {'status': 'BLOCKED', 'code': 'TARGETS_REQUIRED'}

    for target in targets:
        if not isinstance(target, dict) or target.get('status') != 'RESOLVED':
            return {'status': 'BLOCKED', 'code': 'TARGET_PLAN_UNRESOLVED'}
        if target.get('weapon_id') != weapon_id:
            return {'status': 'BLOCKED', 'code': 'TARGET_WEAPON_MISMATCH'}

    allocated = sum(int(target['allocated_rounds']) for target in targets)
    if allocated != declared_rounds:
        return {'status': 'BLOCKED', 'code': 'DECLARED_ROUNDS_ALLOCATION_MISMATCH', 'allocated_rounds': allocated}

    transition_yards = [] if transition_yards is None else transition_yards
    if not isinstance(transition_yards, list) or len(transition_yards) != max(0, len(targets) - 1):
        return {'status': 'BLOCKED', 'code': 'TARGET_TRANSITION_COUNT_INVALID'}
    if not all(_valid_int(x, 0) for x in transition_yards):
        return {'status': 'BLOCKED', 'code': 'TARGET_TRANSITION_DISTANCE_INVALID'}

    transition_waste = sum(transition_yards)
    planned_ammo = declared_rounds + transition_waste
    if planned_ammo > available_ammo:
        return {
            'status': 'BLOCKED',
            'code': 'PLANNED_AMMO_WITH_TARGET_TRANSITIONS_EXCEEDS_AVAILABLE',
            'planned_ammo': planned_ammo,
        }

    volley_size = max(skill_value // 10, 3)
    volleys = []
    attack_index = 0
    for target_index, target in enumerate(targets):
        remaining = int(target['allocated_rounds'])
        first_for_target = True
        while remaining > 0:
            attack_index += 1
            shots = min(volley_size, remaining)
            terms = _automatic_roll_terms(
                base_difficulty=target['base_difficulty'],
                base_net_bonus=target['base_net_bonus'],
                attack_index=attack_index,
            )
            if terms.get('status') != 'RESOLVED':
                return {
                    'status': 'BLOCKED',
                    'code': terms['code'],
                    'attack_index': attack_index,
                    'target_id': target['target_id'],
                }
            waste_before = transition_yards[target_index - 1] if target_index > 0 and first_for_target else 0
            volleys.append({
                'status': 'RESOLVED',
                'attack_index': attack_index,
                'target_index': target_index,
                'target_id': target['target_id'],
                'shots': shots,
                'transition_waste_before': waste_before,
                'base_difficulty': target['base_difficulty'],
                'difficulty': terms['difficulty'],
                'base_net_bonus': target['base_net_bonus'],
                'net_bonus': terms['net_bonus'],
                'raw_net_bonus': terms['raw_net_bonus'],
                'overflow_penalty_steps': terms['overflow_penalty_steps'],
                'weapon': record,
            })
            remaining -= shots
            first_for_target = False

    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'parent_module_id': PARENT_MODULE_ID,
        'parent_registry_id': PARENT_REGISTRY_ID,
        'keeper_source_id': KEEPER_SOURCE_ID,
        'keeper_source_sha256': KEEPER_SHA256,
        'weapon_id': weapon_id,
        'weapon': record,
        'skill_value': skill_value,
        'volley_size': volley_size,
        'declared_rounds': declared_rounds,
        'available_ammo': available_ammo,
        'transition_waste': transition_waste,
        'planned_ammo': planned_ammo,
        'volleys': volleys,
        'randomness_generated': False,
    }


def check_malfunction(*, weapon_id: str, final_roll: int) -> dict:
    record = _weapon_record(weapon_id)
    if record is None:
        return {'status': 'BLOCKED', 'code': 'WEAPON_UNRESOLVED'}
    if not _valid_int(final_roll, 1, 100):
        return {'status': 'BLOCKED', 'code': 'ROLL_INVALID'}
    threshold = record.get('malfunction')
    if threshold is None:
        return {'status': 'RESOLVED', 'malfunction': False, 'threshold': None}
    return {
        'status': 'RESOLVED',
        'malfunction': final_roll >= int(threshold),
        'threshold': int(threshold),
        'weapon_does_not_fire': final_roll >= int(threshold),
        'recovery': 'FAIL_CLOSED_UNTIL_ACTION_TYPE_REGISTRY' if final_roll >= int(threshold) else None,
    }


def resolve_auto_volley(*, skill_value: int, units: int, tens: list[int], volley: dict) -> dict:
    if not isinstance(volley, dict) or volley.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'VOLLEY_PLAN_UNRESOLVED'}
    try:
        roll = core_rules.percentile_from_digits(units, tens, volley['net_bonus'])
        result = core_rules.meets_difficulty(skill_value, roll, volley['difficulty'])
    except ValueError as error:
        return {'status': 'BLOCKED', 'code': str(error)}

    malfunction = check_malfunction(weapon_id=volley['weapon']['weapon_id'], final_roll=roll)
    if malfunction.get('status') != 'RESOLVED':
        return malfunction
    if malfunction['malfunction']:
        return {
            'status': 'RESOLVED',
            'roll': roll,
            'difficulty': volley['difficulty'],
            'success_level': result['level'],
            'hit': False,
            'hits': 0,
            'impale_hits': 0,
            'shots_fired': 0,
            'malfunction': True,
            'sequence_stop': True,
            'damage_expression': volley['weapon']['damage'],
            'randomness_generated': False,
        }

    hit = bool(result['success'])
    hits = 0
    impale_hits = 0
    if hit:
        if result['level'] in {'EXTREME', 'CRITICAL'}:
            hits = volley['shots']
        else:
            hits = max(1, volley['shots'] // 2)

        if volley['weapon'].get('impale') and result['level'] in {'EXTREME', 'CRITICAL'}:
            if volley['difficulty'] != 'EXTREME' or result['level'] == 'CRITICAL':
                impale_hits = min(hits, max(1, volley['shots'] // 2))

    return {
        'status': 'RESOLVED',
        'roll': roll,
        'difficulty': volley['difficulty'],
        'success_level': result['level'],
        'hit': hit,
        'hits': hits,
        'impale_hits': impale_hits,
        'shots_fired': volley['shots'],
        'malfunction': False,
        'sequence_stop': False,
        'damage_expression': volley['weapon']['damage'] if hit else None,
        'randomness_generated': False,
    }


def resolve_full_auto_sequence(*, plan: dict, rolls: list[dict]) -> dict:
    if not isinstance(plan, dict) or plan.get('status') != 'RESOLVED':
        return {'status': 'BLOCKED', 'code': 'FULL_AUTO_PLAN_UNRESOLVED'}
    if not isinstance(rolls, list) or len(rolls) != len(plan['volleys']):
        return {'status': 'BLOCKED', 'code': 'VOLLEY_ROLL_COUNT_MISMATCH'}

    results = []
    ammo_expended = 0
    stopped = False
    for volley, supplied in zip(plan['volleys'], rolls):
        if stopped:
            break
        if not isinstance(supplied, dict) or 'units' not in supplied or 'tens' not in supplied:
            return {'status': 'BLOCKED', 'code': 'RECORDED_VOLLEY_DIGITS_MISSING'}
        ammo_expended += volley.get('transition_waste_before', 0)
        resolved = resolve_auto_volley(
            skill_value=plan['skill_value'],
            units=supplied['units'],
            tens=supplied['tens'],
            volley=volley,
        )
        if resolved.get('status') != 'RESOLVED':
            return resolved
        results.append(resolved)
        if resolved['malfunction']:
            stopped = True
        else:
            ammo_expended += volley['shots']

    return {
        'status': 'RESOLVED',
        'results': results,
        'malfunction_stopped_sequence': stopped,
        'ammo_expended': ammo_expended,
        'remaining_ammo': plan['available_ammo'] - ammo_expended,
        'randomness_generated': False,
    }


def resolve_parent_attack_with_malfunction(*, skill_value: int, units: int, tens: list[int], plan: dict) -> dict:
    resolved = parent.resolve_attack(skill_value=skill_value, units=units, tens=tens, plan=plan)
    if resolved.get('status') != 'RESOLVED':
        return resolved
    malfunction = check_malfunction(weapon_id=plan['weapon']['weapon_id'], final_roll=resolved['roll'])
    if malfunction.get('status') != 'RESOLVED':
        return malfunction
    if malfunction['malfunction']:
        resolved = dict(resolved)
        resolved.update({'hit': False, 'impale': False, 'damage_expression': None, 'malfunction': True, 'weapon_does_not_fire': True})
        return resolved
    resolved = dict(resolved)
    resolved.update({'malfunction': False, 'weapon_does_not_fire': False})
    return resolved


def reload_action(mode: str) -> dict:
    records = {
        'LOAD_TWO_LOOSE_ROUNDS': {'combat_rounds': 1, 'rounds_loaded': 2, 'fire_same_round': False, 'penalty_die': 0},
        'EXCHANGE_CLIP': {'combat_rounds': 1, 'rounds_loaded': 'CLIP_CAPACITY', 'fire_same_round': False, 'penalty_die': 0},
        'CHANGE_MACHINE_GUN_BELT': {'combat_rounds': 2, 'rounds_loaded': 'BELT_CAPACITY', 'fire_same_round': False, 'penalty_die': 0},
        'LOAD_ONE_AND_FIRE': {'combat_rounds': 1, 'rounds_loaded': 1, 'fire_same_round': True, 'penalty_die': 1},
    }
    if mode not in records:
        return {'status': 'BLOCKED', 'code': 'RELOAD_MODE_UNMATERIALIZED'}
    return {'status': 'RESOLVED', 'mode': mode, **records[mode]}


def shotgun_damage_band(*, weapon_id: str, distance_yards: float) -> dict:
    record = _weapon_record(weapon_id)
    if record is None:
        return {'status': 'BLOCKED', 'code': 'WEAPON_UNRESOLVED'}
    if record.get('skill_id') != 'FIREARMS_SHOTGUN':
        return {'status': 'BLOCKED', 'code': 'WEAPON_NOT_SHOTGUN'}
    if not isinstance(distance_yards, (int, float)) or isinstance(distance_yards, bool) or distance_yards < 0:
        return {'status': 'BLOCKED', 'code': 'DISTANCE_INVALID'}

    range_match = re.fullmatch(r'([0-9/]+) yards', str(record.get('base_range', '')).strip())
    if not range_match:
        return {'status': 'BLOCKED', 'code': 'SHOTGUN_RANGE_BANDS_UNMATERIALIZED'}
    ranges = [int(x) for x in range_match.group(1).split('/')]
    damages = str(record.get('damage', '')).split('/')
    if len(ranges) != len(damages):
        return {'status': 'BLOCKED', 'code': 'SHOTGUN_RANGE_DAMAGE_BAND_MISMATCH'}

    for index, upper in enumerate(ranges):
        if float(distance_yards) <= upper:
            return {
                'status': 'RESOLVED',
                'weapon_id': weapon_id,
                'band_index': index,
                'upper_range_yards': upper,
                'damage_expression': damages[index],
                'impale': False,
                'attack_difficulty_inferred': False,
            }
    return {'status': 'BLOCKED', 'code': 'SHOTGUN_BEYOND_LISTED_DAMAGE_BANDS', 'max_range_yards': ranges[-1]}


def burst_plan(*, weapon_id: str, burst_rounds: int, capability_binding: dict | None, base_plan: dict) -> dict:
    if burst_rounds not in (2, 3):
        return {'status': 'BLOCKED', 'code': 'BURST_ROUND_COUNT_INVALID'}
    if not isinstance(capability_binding, dict) or capability_binding.get('verified') is not True:
        return {'status': 'BLOCKED', 'code': 'BURST_CAPABILITY_BINDING_REQUIRED'}
    if capability_binding.get('weapon_id') != weapon_id or capability_binding.get('burst_rounds') != burst_rounds:
        return {'status': 'BLOCKED', 'code': 'BURST_CAPABILITY_BINDING_MISMATCH'}
    if not isinstance(base_plan, dict) or base_plan.get('status') != 'RESOLVED' or base_plan['weapon']['weapon_id'] != weapon_id:
        return {'status': 'BLOCKED', 'code': 'BURST_BASE_PLAN_UNRESOLVED'}
    return {
        'status': 'RESOLVED',
        'module_id': MODULE_ID,
        'weapon_id': weapon_id,
        'shots': burst_rounds,
        'difficulty': base_plan['difficulty'],
        'net_bonus': base_plan['net_bonus'],
        'weapon': base_plan['weapon'],
        'binding_id': capability_binding.get('binding_id'),
        'binding_source': capability_binding.get('source_id'),
    }
