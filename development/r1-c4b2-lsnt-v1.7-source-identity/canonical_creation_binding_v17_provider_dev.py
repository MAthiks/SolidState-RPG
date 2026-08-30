from __future__ import annotations

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
CREATION3_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch3'
CREATION4_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch4'
RUNTIME_DIR = ROOT / 'recovery' / 'recertification-r1'
for path in (HERE, CREATION3_DIR, CREATION4_DIR, RUNTIME_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import investigator_creation_batch3_dev as creation3  # noqa: E402
import investigator_creation_batch4_dev as creation4  # noqa: E402
import lsnt_v17_provider_dev_runtime as v17runtime  # noqa: E402
from runtime_r1.core import CHECKPOINT_FLOOR, sha  # noqa: E402

MODULE_ID = 'COC7_CANONICAL_CREATION_BINDING_LSNT_V1_7_PROVIDER_DEV_V1'
PARENT_CREATION_MODULE_ID = creation4.MODULE_ID
RUNTIME_MODULE_ID = v17runtime.MODULE_ID
SCENARIO_ID = v17runtime.graph.SCENARIO_ID
VERIFICATION_LEVEL = 'PROVIDER_ATTESTED'


def _blocked(code: str, **extra):
    return {'status': 'BLOCKED', 'code': code, 'module_id': MODULE_ID, **extra}


def _fail_closed(runtime, before_digest: str, code: str, **extra):
    return {
        'status': 'FAIL_CLOSED',
        'code': code,
        'module_id': MODULE_ID,
        'before': before_digest,
        'after': runtime.state_digest(),
        **extra,
    }


def _scenario_contract(state: dict) -> dict:
    return {
        'scenario_runtime': copy.deepcopy(state.get('scenario_runtime')),
        'scenario_state': copy.deepcopy(state.get('scenario_state')),
    }


def _scenario_contract_sha(state: dict) -> str:
    return sha(_scenario_contract(state))


def canonical_binding_status(*, runtime) -> dict:
    if not isinstance(runtime, v17runtime.ProviderAttestedRuntimeV17):
        return _blocked('V17_PROVIDER_ATTESTED_RUNTIME_REQUIRED')
    binding = runtime.binding_status()
    if binding.get('status') != 'READY_DEV_ONLY':
        return _blocked(binding.get('code', 'V17_PROVIDER_RUNTIME_BINDING_INVALID'), runtime_binding=binding)
    state = runtime._get_state()
    if not isinstance(state, dict) or state.get('authority_floor') != CHECKPOINT_FLOOR:
        return _blocked('RUNTIME_STATE_OR_AUTHORITY_FLOOR_INVALID')
    scenario = state.get('scenario_runtime')
    if not isinstance(scenario, dict):
        return _blocked('V17_SCENARIO_BINDING_REQUIRED')
    if scenario.get('module_id') != RUNTIME_MODULE_ID:
        return _blocked('V17_RUNTIME_MODULE_ID_MISMATCH')
    if scenario.get('scenario_id') != SCENARIO_ID:
        return _blocked('V17_SCENARIO_ID_MISMATCH')
    if scenario.get('verification_level') != VERIFICATION_LEVEL:
        return _blocked('V17_VERIFICATION_LEVEL_MISMATCH')
    if scenario.get('portable_byte_identity') is not False:
        return _blocked('PROVIDER_RUNTIME_MUST_NOT_CLAIM_PORTABLE_BYTE_IDENTITY')
    if scenario.get('module_ready') is not False:
        return _blocked('PROVIDER_RUNTIME_MUST_NOT_CLAIM_MODULE_READY')
    if scenario.get('frozen_candidate') is not False:
        return _blocked('PROVIDER_RUNTIME_MUST_NOT_CLAIM_FROZEN_CANDIDATE')
    if scenario.get('promotion_allowed') is not False or scenario.get('authority_promoted') is not False:
        return _blocked('PROVIDER_RUNTIME_MUST_NOT_CLAIM_PROMOTION')
    return {
        'status': 'READY_DEV_ONLY',
        'module_id': MODULE_ID,
        'parent_creation_module_id': PARENT_CREATION_MODULE_ID,
        'runtime_module_id': RUNTIME_MODULE_ID,
        'scenario_id': SCENARIO_ID,
        'verification_level': VERIFICATION_LEVEL,
        'scenario_runtime_sha256': sha(scenario),
        'scenario_contract_sha256': _scenario_contract_sha(state),
        'portable_byte_identity': False,
        'module_ready': False,
        'promotion_allowed': False,
    }


def canonical_party_creation_status(*, runtime) -> dict:
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY_DEV_ONLY':
        return binding
    party = creation4.party_creation_status(runtime=runtime)
    return {**party, 'canonical_binding': binding}


def commit_canonical_investigator(*, runtime, player_id: str, ready: dict) -> dict:
    before_digest = runtime.state_digest()
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY_DEV_ONLY':
        return _fail_closed(runtime, before_digest, binding.get('code', 'V17_PROVIDER_BINDING_INVALID'), binding=binding)
    state_before = runtime._get_state()
    character_id = state_before.get('interface_session', {}).get('control_map', {}).get(player_id)
    if not character_id:
        return _fail_closed(runtime, before_digest, 'PLAYER_NOT_IN_CANONICAL_SESSION')
    contract_before = _scenario_contract_sha(state_before)
    result = creation3.commit_investigator_atomic(
        runtime=runtime,
        player_id=player_id,
        character_id=character_id,
        ready=ready,
    )
    if result.get('status') != 'COMMIT':
        return result
    state_after = runtime._get_state()
    if _scenario_contract_sha(state_after) != contract_before:
        runtime._commit_state(copy.deepcopy(state_before))
        return _fail_closed(runtime, before_digest, 'V17_SCENARIO_CONTRACT_MUTATED_DURING_CREATION')
    return {
        **result,
        'canonical_scenario_id': SCENARIO_ID,
        'verification_level': VERIFICATION_LEVEL,
        'scenario_contract_sha256': contract_before,
        'module_ready': False,
        'promotion_allowed': False,
    }


def finalize_canonical_party_creation(*, runtime) -> dict:
    before_digest = runtime.state_digest()
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY_DEV_ONLY':
        return _fail_closed(runtime, before_digest, binding.get('code', 'V17_PROVIDER_BINDING_INVALID'), binding=binding)
    state_before = runtime._get_state()
    contract_before = _scenario_contract_sha(state_before)
    result = creation4.finalize_party_creation_atomic(runtime=runtime)
    if result.get('status') != 'COMMIT':
        return result
    if _scenario_contract_sha(runtime._get_state()) != contract_before:
        runtime._commit_state(copy.deepcopy(state_before))
        return _fail_closed(runtime, before_digest, 'V17_SCENARIO_CONTRACT_MUTATED_DURING_FINALIZATION')
    return {
        **result,
        'canonical_scenario_id': SCENARIO_ID,
        'verification_level': VERIFICATION_LEVEL,
        'scenario_contract_sha256': contract_before,
        'module_ready': False,
        'promotion_allowed': False,
    }


def canonical_play_gate(*, runtime, player_id: str, character_id: str) -> dict:
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY_DEV_ONLY':
        return binding
    gate = creation4.play_gate(runtime=runtime, player_id=player_id, character_id=character_id)
    if gate.get('status') != 'READY':
        return gate
    return {
        **gate,
        'canonical_scenario_id': SCENARIO_ID,
        'verification_level': VERIFICATION_LEVEL,
        'module_ready': False,
        'promotion_allowed': False,
    }


def append_canonical_basic_action(*, runtime, player_id: str, character_id: str, action_id, roll, delta=0, event_id=None) -> dict:
    before_digest = runtime.state_digest()
    gate = canonical_play_gate(runtime=runtime, player_id=player_id, character_id=character_id)
    if gate.get('status') != 'READY':
        return _fail_closed(runtime, before_digest, gate.get('code', 'CANONICAL_PLAY_GATE_BLOCKED'), gate=gate)
    scenario_runtime_before = sha(runtime._get_state()['scenario_runtime'])
    result = runtime.append_dev_action(
        player_id,
        character_id,
        action_id,
        roll,
        delta=delta,
        event_id=event_id,
    )
    if result.get('status') != 'COMMIT':
        return result
    if sha(runtime._get_state()['scenario_runtime']) != scenario_runtime_before:
        return _fail_closed(runtime, before_digest, 'V17_SCENARIO_RUNTIME_MUTATED_DURING_BASIC_ACTION')
    return result


def player_creation_projection(*, runtime, player_id: str) -> dict:
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY_DEV_ONLY':
        return binding
    base = runtime.player_projection(player_id)
    if base.get('status') != 'READY':
        return base
    party = creation4.party_creation_status(runtime=runtime)
    return {
        'status': 'READY',
        'player_id': base['player_id'],
        'character_id': base['character_id'],
        'scenario': copy.deepcopy(base['scenario']),
        'character': copy.deepcopy(base['character']),
        'known_information': copy.deepcopy(base['known_information']),
        'world_time': base['world_time'],
        'shared_resources': copy.deepcopy(base['shared_resources']),
        'position': base['position'],
        'exposure': base['exposure'],
        'creation': {
            'complete': base['character'].get('creation', {}).get('complete') is True,
            'party_status': party.get('status'),
        },
        'certification': {
            'verification_level': VERIFICATION_LEVEL,
            'portable_byte_identity': False,
            'module_ready': False,
            'promotion_allowed': False,
        },
        'guardian_truth_exposed': False,
        'future_events_exposed': False,
        'source_hashes_exposed': False,
        'provider_identity_exposed': False,
        'canonical_graph_exposed': False,
        'scenario_contract_exposed': False,
    }
