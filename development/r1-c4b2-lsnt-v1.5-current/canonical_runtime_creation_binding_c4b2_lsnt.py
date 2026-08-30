from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CREATION3_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch3'
CREATION4_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch4'
RUNTIME_DIR = ROOT / 'recovery' / 'recertification-r1'
for path in (CREATION3_DIR, CREATION4_DIR, RUNTIME_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import investigator_creation_batch3_dev as creation3  # noqa: E402
import investigator_creation_batch4_dev as creation4  # noqa: E402
from integrated_adjudication_r1_c4b2_lsnt import SourceBackedRuntimeR1C4B2LSNT, INTEGRATION_ID as C4B2_INTEGRATION_ID  # noqa: E402
from scenario_router_r1_c4b2_lsnt import ROUTES, ROUTER_ID  # noqa: E402
from registry_r1_c4b2_lsnt import REGISTRY_ID  # noqa: E402
from source_adapter_r1_c4b import SOURCE_SPECS_C4B  # noqa: E402
from runtime_r1.core import CHECKPOINT_FLOOR, sha  # noqa: E402

MODULE_ID = 'COC7_CANONICAL_RUNTIME_CREATION_BINDING_R1_C4B2_LSNT_DEV_V1'
PARENT_CREATION_MODULE_ID = creation4.MODULE_ID
FROZEN_RUNTIME_INTEGRATION_ID = C4B2_INTEGRATION_ID
ALLOWED_RELEASE_CLASSES = {'PASS_REAL', 'RECOVERY_SOURCE_COMPILED_C4B', 'RECOVERY_SOURCE_COMPILED_C4B2'}

EXPECTED_SCENARIO_RUNTIME_KEYS = {
    'router_id', 'registry_id', 'scenario_key', 'scenario_id', 'title',
    'source_ids', 'source_hashes', 'release_checkpoint', 'release_class',
    'canonical_path',
}


def _blocked(code: str, **extra):
    return {'status': 'BLOCKED', 'code': code, **extra}


def _fail_closed(runtime, before, code: str, **extra):
    return {'status': 'FAIL_CLOSED', 'code': code, 'before': before, 'after': runtime.state_digest(), **extra}


def canonical_binding_status(*, runtime) -> dict:
    if not isinstance(runtime, SourceBackedRuntimeR1C4B2LSNT):
        return _blocked('C4B2_LSNT_SOURCE_BACKED_RUNTIME_REQUIRED')
    try:
        state = runtime._get_state()
    except Exception:
        return _blocked('RUNTIME_STATE_UNAVAILABLE')
    if not isinstance(state, dict):
        return _blocked('RUNTIME_STATE_UNAVAILABLE')
    if state.get('authority_floor') != CHECKPOINT_FLOOR:
        return _blocked('AUTHORITY_FLOOR_INVALID')

    scenario = state.get('scenario_runtime')
    if not isinstance(scenario, dict):
        return _blocked('C4B2_SCENARIO_BINDING_REQUIRED')
    if set(scenario) != EXPECTED_SCENARIO_RUNTIME_KEYS:
        return _blocked('C4B2_SCENARIO_BINDING_SHAPE_INVALID')

    key = str(scenario.get('scenario_key', '')).upper()
    route = ROUTES.get(key)
    if route is None:
        return _blocked('SCENARIO_NOT_REGISTERED', scenario_key=key)
    if route.canonical_path_ready is not True or route.release_class not in ALLOWED_RELEASE_CLASSES:
        return _blocked('C4B2_SCENARIO_ROUTE_NOT_PLAY_READY', scenario_key=key, release_class=route.release_class)

    expected_hashes = {}
    for source_id in route.source_ids:
        spec = SOURCE_SPECS_C4B.get(source_id)
        if spec is None:
            return _blocked('C4B2_EXPECTED_SOURCE_IDENTITY_MISSING', source_id=source_id)
        expected_hashes[source_id] = spec.sha256

    expected = {
        'router_id': ROUTER_ID,
        'registry_id': REGISTRY_ID,
        'scenario_key': route.scenario_key,
        'scenario_id': route.scenario_id,
        'title': route.title,
        'source_ids': list(route.source_ids),
        'source_hashes': expected_hashes,
        'release_checkpoint': route.release_checkpoint,
        'release_class': route.release_class,
        'canonical_path': copy.deepcopy(route.canonical_path),
    }
    if scenario != expected:
        mismatches = sorted(k for k in expected if scenario.get(k) != expected[k])
        return _blocked('C4B2_SCENARIO_BINDING_MISMATCH', scenario_key=key, mismatches=mismatches)

    return {
        'status': 'READY',
        'module_id': MODULE_ID,
        'runtime_integration_id': FROZEN_RUNTIME_INTEGRATION_ID,
        'scenario_key': key,
        'scenario_id': route.scenario_id,
        'scenario_binding_sha256': sha(scenario),
        'canonical_path_ready': True,
        'release_class': route.release_class,
        'source_hashes_match_expected': True,
        'source_files_reopened_by_binding_module': False,
    }


def canonical_party_creation_status(*, runtime) -> dict:
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY':
        return binding
    party = creation4.party_creation_status(runtime=runtime)
    return {**party, 'canonical_binding': binding}


def commit_canonical_investigator(*, runtime, player_id: str, ready: dict) -> dict:
    before = runtime.state_digest()
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY':
        return _fail_closed(runtime, before, binding.get('code', 'C4B2_SCENARIO_BINDING_INVALID'), binding=binding)
    state = runtime._get_state()
    character_id = state.get('interface_session', {}).get('control_map', {}).get(player_id)
    if not character_id:
        return _fail_closed(runtime, before, 'PLAYER_NOT_IN_CANONICAL_SESSION')
    scenario_before = sha(state['scenario_runtime'])
    result = creation3.commit_investigator_atomic(runtime=runtime, player_id=player_id, character_id=character_id, ready=ready)
    if result.get('status') != 'COMMIT':
        return result
    scenario_after = sha(runtime._get_state()['scenario_runtime'])
    if scenario_after != scenario_before:
        return _fail_closed(runtime, before, 'SCENARIO_BINDING_MUTATED_DURING_CREATION')
    return {**result, 'canonical_scenario_key': binding['scenario_key'], 'scenario_binding_sha256': binding['scenario_binding_sha256']}


def finalize_canonical_party_creation(*, runtime) -> dict:
    before = runtime.state_digest()
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY':
        return _fail_closed(runtime, before, binding.get('code', 'C4B2_SCENARIO_BINDING_INVALID'), binding=binding)
    scenario_before = sha(runtime._get_state()['scenario_runtime'])
    result = creation4.finalize_party_creation_atomic(runtime=runtime)
    if result.get('status') != 'COMMIT':
        return result
    scenario_after = sha(runtime._get_state()['scenario_runtime'])
    if scenario_after != scenario_before:
        return _fail_closed(runtime, before, 'SCENARIO_BINDING_MUTATED_DURING_PARTY_FINALIZATION')
    return {**result, 'canonical_scenario_key': binding['scenario_key'], 'scenario_binding_sha256': binding['scenario_binding_sha256']}


def canonical_play_gate(*, runtime, player_id: str, character_id: str) -> dict:
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY':
        return binding
    gate = creation4.play_gate(runtime=runtime, player_id=player_id, character_id=character_id)
    if gate.get('status') != 'READY':
        return gate
    return {**gate, 'canonical_scenario_key': binding['scenario_key'], 'scenario_id': binding['scenario_id'], 'scenario_binding_sha256': binding['scenario_binding_sha256']}


def append_canonical_basic_action(*, runtime, player_id: str, character_id: str, action_id, roll, delta=0, event_id=None) -> dict:
    before = runtime.state_digest()
    gate = canonical_play_gate(runtime=runtime, player_id=player_id, character_id=character_id)
    if gate.get('status') != 'READY':
        return _fail_closed(runtime, before, gate.get('code', 'CANONICAL_PLAY_GATE_BLOCKED'), gate=gate)
    return creation4.append_player_action_after_creation(runtime=runtime, player_id=player_id, character_id=character_id, action_id=action_id, roll=roll, delta=delta, event_id=event_id)


def player_creation_projection(*, runtime, player_id: str) -> dict:
    binding = canonical_binding_status(runtime=runtime)
    if binding.get('status') != 'READY':
        return binding
    state = runtime._get_state()
    character_id = state.get('party', {}).get(player_id)
    if not character_id:
        return _blocked('PLAYER_NOT_IN_CANONICAL_SESSION')
    character = state['characters'][character_id]
    party = creation4.party_creation_status(runtime=runtime)
    return {
        'status': 'READY',
        'player_id': player_id,
        'character_id': character_id,
        'scenario': {
            'scenario_key': binding['scenario_key'],
            'scenario_id': binding['scenario_id'],
            'title': state['scenario_runtime']['title'],
        },
        'creation': {
            'complete': character.get('creation', {}).get('complete') is True,
            'party_status': party.get('status'),
        },
        'canonical_path_exposed': False,
        'source_hashes_exposed': False,
    }
