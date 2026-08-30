from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH2_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch2'
FINANCE_DIR = ROOT / 'development' / 'r1-coc7-finance-credit-rating-batch1'
EQWP_DIR = ROOT / 'development' / 'r1-coc7-equipment-weapons-batch1'
RUNTIME_DIR = ROOT / 'recovery' / 'recertification-r1'
for path in (BATCH2_DIR, FINANCE_DIR, EQWP_DIR, RUNTIME_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import investigator_creation_batch2_dev as batch2  # noqa: E402
import finance_credit_rating_dev as finance  # noqa: E402
import registry_eqwp_batch1_dev as eqwp  # noqa: E402
from runtime_r1.core import CHECKPOINT_FLOOR, sha  # noqa: E402

MODULE_ID = 'COC7_INVESTIGATOR_CREATION_R1_BATCH3_DEV_V1'
PARENT_MODULE_ID = batch2.MODULE_ID
PARENT_HARDENED_PROOF = 2514
FINANCE_MODULE_ID = finance.MODULE_ID
EQUIPMENT_WEAPON_REGISTRY_ID = eqwp.REGISTRY_ID


def _valid_int(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def _blocked(code: str, **extra):
    return {'status': 'BLOCKED', 'code': code, **extra}


def _normalize_possessions(possessions: list[dict]) -> dict:
    if not isinstance(possessions, list):
        return _blocked('POSSESSIONS_LIST_REQUIRED')
    normalized = []
    seen = set()
    for index, item in enumerate(possessions):
        if not isinstance(item, dict) or set(item) != {'kind', 'record_id', 'quantity'}:
            return _blocked('POSSESSION_ENTRY_SHAPE_INVALID', entry_index=index)
        kind = str(item['kind']).upper()
        record_id = str(item['record_id']).upper()
        quantity = item['quantity']
        if kind not in {'EQUIPMENT', 'WEAPON'}:
            return _blocked('POSSESSION_KIND_INVALID', entry_index=index)
        if not record_id:
            return _blocked('POSSESSION_RECORD_ID_REQUIRED', entry_index=index)
        if not _valid_int(quantity, 1):
            return _blocked('POSSESSION_QUANTITY_INVALID', entry_index=index)
        key = (kind, record_id)
        if key in seen:
            return _blocked('DUPLICATE_POSSESSION_ENTRY', entry_index=index, kind=kind, record_id=record_id)
        seen.add(key)
        if kind == 'EQUIPMENT':
            resolved = eqwp.resolve_equipment(record_id)
            expected_status = 'RESOLVED_REFERENCE'
        else:
            resolved = eqwp.resolve_weapon(record_id)
            expected_status = 'RESOLVED_MECHANICS'
        if resolved.get('status') != expected_status:
            return _blocked(
                'POSSESSION_REGISTRY_RECORD_UNRESOLVED',
                entry_index=index,
                kind=kind,
                record_id=record_id,
                registry_result=resolved,
            )
        if resolved.get('auto_possession') is not False:
            return _blocked('REGISTRY_AUTO_POSSESSION_INVARIANT_VIOLATED', entry_index=index)
        normalized.append({
            'kind': kind,
            'record_id': record_id,
            'quantity': quantity,
            'registry_id': resolved['registry_id'],
            'source_id': resolved['source_id'],
            'source_sha256': resolved['source_sha256'],
        })
    return {
        'status': 'RESOLVED',
        'inventory': normalized,
        'automatic_equipment_selection': False,
        'automatic_weapon_selection': False,
    }


def prepare_creation_commit(
    *,
    batch2_preflight: dict,
    finance_profile: dict,
    possessions: list[dict],
) -> dict:
    if not isinstance(batch2_preflight, dict) or batch2_preflight.get('status') != 'READY_FOR_EQUIPMENT_FINANCE_BATCH3':
        return _blocked('BATCH2_PREFLIGHT_REQUIRED')
    if batch2_preflight.get('module_id') != PARENT_MODULE_ID:
        return _blocked('BATCH2_MODULE_ID_MISMATCH')
    if not isinstance(finance_profile, dict) or set(finance_profile) != {
        'credit_rating', 'spending_level_units', 'cash_refresh_units', 'asset_value_units',
        'living_standard_id', 'adapter_verified'
    }:
        return _blocked('FINANCE_PROFILE_SHAPE_INVALID')

    expected_cr = batch2_preflight.get('skill_allocation', {}).get('credit_rating')
    if not _valid_int(expected_cr, 0, 99):
        return _blocked('BATCH2_CREDIT_RATING_MISSING')
    if finance_profile.get('credit_rating') != expected_cr:
        return _blocked(
            'FINANCE_CREDIT_RATING_MISMATCH',
            expected_credit_rating=expected_cr,
            supplied_credit_rating=finance_profile.get('credit_rating'),
        )

    finance_result = finance.validate_private_finance_profile(**finance_profile)
    if finance_result.get('status') != 'RESOLVED':
        return _blocked('PRIVATE_FINANCE_PROFILE_UNRESOLVED', finance_result=finance_result)

    possession_result = _normalize_possessions(possessions)
    if possession_result.get('status') != 'RESOLVED':
        return possession_result

    payload = {
        'module_id': MODULE_ID,
        'parent_module_id': PARENT_MODULE_ID,
        'checkpoint_floor': CHECKPOINT_FLOOR,
        'creation': copy.deepcopy(batch2_preflight),
        'finance': copy.deepcopy(finance_result),
        'inventory': copy.deepcopy(possession_result['inventory']),
        'automatic_equipment_selection': False,
        'automatic_weapon_selection': False,
        'automatic_asset_conversion': False,
        'automatic_debt_creation': False,
        'randomness_generated': False,
    }
    return {
        'status': 'READY_FOR_ATOMIC_COMMIT',
        'module_id': MODULE_ID,
        'payload': payload,
        'payload_sha256': sha(payload),
    }


def _validate_ready_bundle(ready: dict) -> dict:
    if not isinstance(ready, dict) or set(ready) != {'status', 'module_id', 'payload', 'payload_sha256'}:
        return _blocked('CREATION_COMMIT_BUNDLE_SHAPE_INVALID')
    if ready.get('status') != 'READY_FOR_ATOMIC_COMMIT' or ready.get('module_id') != MODULE_ID:
        return _blocked('CREATION_COMMIT_BUNDLE_STATUS_INVALID')
    payload = ready.get('payload')
    if not isinstance(payload, dict) or payload.get('module_id') != MODULE_ID:
        return _blocked('CREATION_COMMIT_PAYLOAD_INVALID')
    if payload.get('checkpoint_floor') != CHECKPOINT_FLOOR:
        return _blocked('CREATION_COMMIT_CHECKPOINT_FLOOR_INVALID')
    if sha(payload) != ready.get('payload_sha256'):
        return _blocked('CREATION_COMMIT_PAYLOAD_HASH_MISMATCH')
    if payload.get('creation', {}).get('status') != 'READY_FOR_EQUIPMENT_FINANCE_BATCH3':
        return _blocked('BATCH2_PREFLIGHT_NOT_READY_AT_COMMIT')
    if payload.get('finance', {}).get('status') != 'RESOLVED' or payload.get('finance', {}).get('adapter_verified') is not True:
        return _blocked('FINANCE_PROFILE_NOT_VERIFIED_AT_COMMIT')
    return {'status': 'RESOLVED'}


def materialize_character_state(*, player_id: str, character_id: str, ready: dict) -> dict:
    checked = _validate_ready_bundle(ready)
    if checked['status'] != 'RESOLVED':
        return checked
    payload = ready['payload']
    creation = payload['creation']
    batch1_preflight = creation['batch1_preflight']
    aged = batch1_preflight['aged']
    budgets = batch1_preflight['budgets']
    allocation = creation['skill_allocation']
    story = creation['story']

    if allocation.get('credit_rating') != payload['finance'].get('credit_rating'):
        return _blocked('CREDIT_RATING_DIVERGED_INSIDE_COMMIT_PAYLOAD')

    characteristics = copy.deepcopy(aged['characteristics'])
    derived = copy.deepcopy(aged['derived'])
    stats = {
        **characteristics,
        'HP': derived['HP'],
        'SAN': derived['SAN'],
        'MP': derived['MP'],
        'MOV': derived['MOV'],
        'damage_bonus': derived['damage_bonus'],
        'build': derived['build'],
        'Luck': aged['luck'],
    }
    character = {
        'character_id': character_id,
        'owner_id': player_id,
        'name': story['identity']['name'],
        'age': aged['age'],
        'identity': copy.deepcopy(story['identity']),
        'stats': stats,
        'skills': copy.deepcopy(allocation['skills']),
        'occupation': {
            'occupation_id': budgets['occupation_id'],
            'occupation_name': budgets['occupation_name'],
            'credit_rating': allocation['credit_rating'],
            'registry_id': batch1_preflight['budgets']['occupation_registry_id'],
        },
        'finance': {
            'credit_rating': payload['finance']['credit_rating'],
            'spending_level_units': payload['finance']['spending_level_units'],
            'cash_units': payload['finance']['cash_refresh_units'],
            'cash_refresh_units': payload['finance']['cash_refresh_units'],
            'asset_value_units': payload['finance']['asset_value_units'],
            'living_standard_id': payload['finance']['living_standard_id'],
            'private_adapter_verified': True,
            'private_table_values_embedded': False,
        },
        'inventory': copy.deepcopy(payload['inventory']),
        'backstory': copy.deepcopy(story['backstory']),
        'key_connection': copy.deepcopy(story['key_connection']),
        'creation': {
            'complete': True,
            'module_id': MODULE_ID,
            'parent_module_id': PARENT_MODULE_ID,
            'checkpoint_floor': CHECKPOINT_FLOOR,
            'payload_sha256': ready['payload_sha256'],
            'automatic_equipment_selection': False,
            'automatic_weapon_selection': False,
            'randomness_generated': False,
        },
    }
    return {'status': 'RESOLVED', 'character': character}


def commit_investigator_atomic(*, runtime, player_id: str, character_id: str, ready: dict) -> dict:
    try:
        before = runtime.state_digest()
        state = runtime._get_state()
    except Exception:
        return _blocked('RUNTIME_INTERFACE_UNAVAILABLE')

    def fail(code, **extra):
        return {'status': 'FAIL_CLOSED', 'code': code, 'before': before, 'after': runtime.state_digest(), **extra}

    checked = _validate_ready_bundle(ready)
    if checked['status'] != 'RESOLVED':
        return fail(checked['code'])
    if not isinstance(state, dict) or state.get('authority_floor') != CHECKPOINT_FLOOR:
        return fail('RUNTIME_STATE_OR_AUTHORITY_FLOOR_INVALID')
    control_map = state.get('interface_session', {}).get('control_map', {})
    if control_map.get(player_id) != character_id:
        return fail('ACTOR_CONTROL_MISMATCH')
    character = state.get('characters', {}).get(character_id)
    if not isinstance(character, dict) or character.get('owner_id') != player_id:
        return fail('CHARACTER_OWNERSHIP_MISMATCH')
    if character.get('creation', {}).get('complete') is True:
        return fail('CHARACTER_CREATION_ALREADY_COMMITTED')
    if state.get('journal'):
        return fail('CREATION_AFTER_PLAY_STARTED_BLOCKED')

    materialized = materialize_character_state(player_id=player_id, character_id=character_id, ready=ready)
    if materialized.get('status') != 'RESOLVED':
        return fail(materialized.get('code', 'CHARACTER_MATERIALIZATION_FAILED'))

    new_state = copy.deepcopy(state)
    new_character = materialized['character']
    new_state['characters'][character_id] = copy.deepcopy(new_character)
    new_state['initial_characters'][character_id] = copy.deepcopy(new_character)
    commits = new_state.setdefault('creation_commits', [])
    if any(row.get('character_id') == character_id for row in commits):
        return fail('DUPLICATE_CREATION_COMMIT_RECORD')
    commit_sequence = new_state.get('commit_sequence')
    if not _valid_int(commit_sequence, 0):
        return fail('RUNTIME_COMMIT_SEQUENCE_INVALID')
    new_state['commit_sequence'] = commit_sequence + 1
    commits.append({
        'commit_sequence': new_state['commit_sequence'],
        'player_id': player_id,
        'character_id': character_id,
        'module_id': MODULE_ID,
        'creation_payload_sha256': ready['payload_sha256'],
        'character_baseline_sha256': sha(new_character),
    })

    try:
        runtime._commit_state(new_state)
    except Exception:
        return fail('ATOMIC_RUNTIME_COMMIT_FAILED')

    after = runtime.state_digest()
    return {
        'status': 'COMMIT',
        'module_id': MODULE_ID,
        'player_id': player_id,
        'character_id': character_id,
        'commit_sequence': new_state['commit_sequence'],
        'before': before,
        'after': after,
        'creation_payload_sha256': ready['payload_sha256'],
        'character_baseline_sha256': sha(new_character),
        'strict_replay_baseline_updated': True,
        'automatic_equipment_selection': False,
        'randomness_generated': False,
    }
