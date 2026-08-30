from __future__ import annotations

import copy
import hashlib
import hmac
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('SOLIDSTATE_REPO_ROOT', str(HERE.parents[1])))
RUNTIME_DIR = ROOT / 'recovery' / 'recertification-r1'
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import source_identity_proof_v2 as identity  # noqa: E402
import lsnt_v17_canonical_graph_candidate as graph  # noqa: E402
from runtime_r1.core import CHECKPOINT_FLOOR, RecoveryRuntimeR1, canon, sha  # noqa: E402

MODULE_ID = 'LSNT_V1_7_PROVIDER_ATTESTED_DEV_RUNTIME_R1_C4B2_V1'
SAVE_SCHEMA = 'SOLIDSTATE_LSNT_V1_7_PROVIDER_DEV_SAVE_V1'
AUTHORITY_ID = 'RECOVERY_R1_C4B2_LSNT_V1_7_DEV_PROVIDER_ATTESTED'
SCENARIO_KEY = 'SOLEIL_NOIR'
HEX64 = re.compile(r'^[0-9a-f]{64}$')


def _blocked(code: str, **extra):
    return {'status': 'BLOCKED', 'code': code, 'module_id': MODULE_ID, **extra}


class ProviderAttestedRuntimeV17(RecoveryRuntimeR1):
    def __init__(self, db_path, identity_proof: dict, secret=b'lsnt-v17-provider-dev-test-secret'):
        super().__init__(db_path, secret=secret)
        self.identity_proof = copy.deepcopy(identity_proof)
        self._proof_gate = self._validate_proof(self.identity_proof)

    @staticmethod
    def _validate_proof(proof: dict) -> dict:
        if not isinstance(proof, dict):
            return _blocked('SOURCE_IDENTITY_PROOF_INVALID')
        if proof.get('status') != 'SOURCE_IDENTITY_PROVIDER_ATTESTED':
            return _blocked('PROVIDER_ATTESTED_PROOF_REQUIRED')
        if proof.get('verification_level') != 'PROVIDER_ATTESTED':
            return _blocked('PROVIDER_ATTESTED_LEVEL_REQUIRED')
        if proof.get('module_id') != identity.MODULE_ID:
            return _blocked('SOURCE_IDENTITY_MODULE_MISMATCH')
        pair_digest = str(proof.get('pair_digest', '')).lower()
        if not HEX64.fullmatch(pair_digest):
            return _blocked('PROVIDER_PAIR_DIGEST_INVALID')
        permission = identity.permission_for(proof, target='DEV_RUNTIME')
        if permission.get('status') != 'ALLOWED_DEV_ONLY':
            return _blocked('DEV_RUNTIME_PERMISSION_DENIED', permission=permission)
        return {
            'status': 'READY_DEV_ONLY',
            'verification_level': 'PROVIDER_ATTESTED',
            'pair_digest': pair_digest,
            'portable_byte_identity': False,
            'module_ready': False,
            'promotion_allowed': False,
        }

    @staticmethod
    def current_graph_digest() -> str:
        return sha(graph.structural_graph())

    def identity_status(self) -> dict:
        return copy.deepcopy(self._proof_gate)

    def new_v17_session(self, players, session_id='LSNT-V1.7-PROVIDER-DEV') -> dict:
        before = self.state_digest()
        if self._proof_gate.get('status') != 'READY_DEV_ONLY':
            return {
                'status': 'FAIL_CLOSED',
                'code': self._proof_gate.get('code', 'SOURCE_IDENTITY_PROOF_INVALID'),
                'before': before,
                'after': before,
            }
        ready = self.new_session(players, session_id=session_id)
        if ready.get('status') != 'SESSION_READY':
            return ready

        state = self._get_state()
        count = len(ready['players'])
        water = graph.GRAPH['shared_resources']['water_liters_by_player_count'][count]
        positions = {cid: 'BIR_HALIM' for cid in state['characters']}
        exposure = {cid: 0 for cid in state['characters']}
        state['scenario_runtime'] = {
            'module_id': MODULE_ID,
            'scenario_key': SCENARIO_KEY,
            'scenario_id': graph.SCENARIO_ID,
            'source_ids': {'keeper': graph.KEEPER_ID, 'player': graph.PLAYER_ID},
            'verification_level': 'PROVIDER_ATTESTED',
            'provider_pair_digest': self._proof_gate['pair_digest'],
            'graph_digest': self.current_graph_digest(),
            'runtime_dependency_on_v1_5': False,
            'portable_byte_identity': False,
            'module_ready': False,
            'frozen_candidate': False,
            'promotion_allowed': False,
            'authority_promoted': False,
        }
        state['scenario_state'] = {
            'world_time': 'J1_0800',
            'party_split': False,
            'positions': positions,
            'romain_persy': {'position': 'BIR_HALIM', 'autonomous': True, 'replacement_pc': False},
            'exposure': exposure,
            'shared_resources': {
                'water_liters': water,
                'fuel': graph.GRAPH['shared_resources']['fuel'],
                'team_radio_batteries': 2,
                'vehicle': graph.GRAPH['shared_resources']['vehicle'],
                'vehicle_status': 'OPERATIONAL',
            },
            'front': 'RELATIVELY_STABLE',
            'shared_knowledge': [],
            'events': {},
            'consequences_pending': [],
        }
        self._commit_state(state)
        return {
            'status': 'DEV_SCENARIO_SESSION_READY',
            'module_id': MODULE_ID,
            'scenario_id': graph.SCENARIO_ID,
            'verification_level': 'PROVIDER_ATTESTED',
            'players': ready['players'],
            'control_map': ready['control_map'],
            'module_ready': False,
            'promotion_allowed': False,
        }

    def binding_status(self) -> dict:
        if self._proof_gate.get('status') != 'READY_DEV_ONLY':
            return copy.deepcopy(self._proof_gate)
        state = self._get_state()
        if not isinstance(state, dict):
            return _blocked('SESSION_NOT_READY')
        scenario = state.get('scenario_runtime')
        if not isinstance(scenario, dict):
            return _blocked('SCENARIO_BINDING_MISSING')
        expected = {
            'module_id': MODULE_ID,
            'scenario_key': SCENARIO_KEY,
            'scenario_id': graph.SCENARIO_ID,
            'source_ids': {'keeper': graph.KEEPER_ID, 'player': graph.PLAYER_ID},
            'verification_level': 'PROVIDER_ATTESTED',
            'provider_pair_digest': self._proof_gate['pair_digest'],
            'graph_digest': self.current_graph_digest(),
            'runtime_dependency_on_v1_5': False,
            'portable_byte_identity': False,
            'module_ready': False,
            'frozen_candidate': False,
            'promotion_allowed': False,
            'authority_promoted': False,
        }
        if scenario != expected:
            mismatches = sorted(k for k in expected if scenario.get(k) != expected[k])
            return _blocked('V17_DEV_SCENARIO_BINDING_MISMATCH', mismatches=mismatches)
        if state.get('authority_floor') != CHECKPOINT_FLOOR:
            return _blocked('AUTHORITY_FLOOR_INVALID')
        return {
            'status': 'READY_DEV_ONLY',
            'scenario_id': graph.SCENARIO_ID,
            'verification_level': 'PROVIDER_ATTESTED',
            'provider_pair_digest': self._proof_gate['pair_digest'],
            'graph_digest': expected['graph_digest'],
            'module_ready': False,
            'promotion_allowed': False,
        }

    def player_projection(self, player_id: str) -> dict:
        binding = self.binding_status()
        if binding.get('status') != 'READY_DEV_ONLY':
            return binding
        state = self._get_state()
        cid = state.get('party', {}).get(player_id)
        if not cid:
            return _blocked('PLAYER_NOT_IN_SESSION')
        base = self.player_view(player_id)
        scenario_state = state['scenario_state']
        return {
            'status': 'READY',
            'player_id': player_id,
            'character_id': cid,
            'scenario': {
                'scenario_key': SCENARIO_KEY,
                'scenario_id': graph.SCENARIO_ID,
                'title': 'Le Soleil Noir de Tobrouk',
                'era': '1942-06',
                'bcra_npc': 'Romain Persy',
                'bcra_autonomous': True,
            },
            'character': base['character'],
            'known_information': base['knowledge'],
            'world_time': scenario_state['world_time'],
            'shared_resources': copy.deepcopy(scenario_state['shared_resources']),
            'position': scenario_state['positions'][cid],
            'exposure': scenario_state['exposure'][cid],
            'guardian_truth_exposed': False,
            'future_events_exposed': False,
            'source_hashes_exposed': False,
            'provider_identity_exposed': False,
            'canonical_graph_exposed': False,
        }

    def append_dev_action(self, player_id: str, character_id: str, action_id, roll: int, delta: int = 0, event_id=None):
        before = self.state_digest()
        binding = self.binding_status()
        if binding.get('status') != 'READY_DEV_ONLY':
            return {
                'status': 'FAIL_CLOSED',
                'code': binding.get('code', 'V17_DEV_BINDING_INVALID'),
                'before': before,
                'after': before,
            }
        return self.append_player_action(player_id, character_id, action_id, roll, delta=delta, event_id=event_id)

    def save_v17_bundle(self) -> dict:
        binding = self.binding_status()
        if binding.get('status') != 'READY_DEV_ONLY':
            return binding
        payload = {
            'schema': SAVE_SCHEMA,
            'checkpoint_floor': CHECKPOINT_FLOOR,
            'authority_id': AUTHORITY_ID,
            'module_id': MODULE_ID,
            'scenario_id': graph.SCENARIO_ID,
            'verification_level': 'PROVIDER_ATTESTED',
            'provider_pair_digest': self._proof_gate['pair_digest'],
            'graph_digest': self.current_graph_digest(),
            'portable_byte_identity': False,
            'module_ready': False,
            'promotion_allowed': False,
            'state': self._get_state(),
        }
        raw = canon(payload).encode('utf-8')
        return {
            'payload': payload,
            'auth': {
                'algorithm': 'HMAC-SHA256',
                'payload_sha256': hashlib.sha256(raw).hexdigest(),
                'hmac_sha256': hmac.new(self.secret, raw, hashlib.sha256).hexdigest(),
            },
        }

    def restore_v17_bundle(self, bundle) -> dict:
        before = self.state_digest()
        try:
            if self._proof_gate.get('status') != 'READY_DEV_ONLY':
                raise ValueError('SOURCE_IDENTITY_PROOF_INVALID')
            if set(bundle) != {'payload', 'auth'}:
                raise ValueError('BUNDLE_SHAPE_INVALID')
            payload = bundle['payload']
            auth = bundle['auth']
            raw = canon(payload).encode('utf-8')
            if hashlib.sha256(raw).hexdigest() != auth.get('payload_sha256'):
                raise ValueError('PAYLOAD_HASH_MISMATCH')
            expected_hmac = hmac.new(self.secret, raw, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_hmac, str(auth.get('hmac_sha256', ''))):
                raise ValueError('SAVE_AUTHENTICATION_FAILED')
            if (
                payload.get('schema') != SAVE_SCHEMA
                or payload.get('checkpoint_floor') != CHECKPOINT_FLOOR
                or payload.get('authority_id') != AUTHORITY_ID
                or payload.get('module_id') != MODULE_ID
                or payload.get('scenario_id') != graph.SCENARIO_ID
                or payload.get('verification_level') != 'PROVIDER_ATTESTED'
                or payload.get('provider_pair_digest') != self._proof_gate['pair_digest']
                or payload.get('graph_digest') != self.current_graph_digest()
                or payload.get('portable_byte_identity') is not False
                or payload.get('module_ready') is not False
                or payload.get('promotion_allowed') is not False
            ):
                raise ValueError('V17_DEV_SAVE_BINDING_MISMATCH')
            state = copy.deepcopy(payload['state'])
            scenario = state.get('scenario_runtime', {})
            if (
                state.get('authority_floor') != CHECKPOINT_FLOOR
                or scenario.get('scenario_id') != graph.SCENARIO_ID
                or scenario.get('provider_pair_digest') != self._proof_gate['pair_digest']
                or scenario.get('graph_digest') != self.current_graph_digest()
                or scenario.get('verification_level') != 'PROVIDER_ATTESTED'
                or scenario.get('portable_byte_identity') is not False
                or scenario.get('module_ready') is not False
                or scenario.get('promotion_allowed') is not False
            ):
                raise ValueError('V17_DEV_STATE_BINDING_MISMATCH')
            if self.verify_journal(state).get('status') != 'REPLAY_MATCH':
                raise ValueError('STRICT_REPLAY_INVALID')
            self._commit_state(state)
            return {
                'status': 'RESTORED_STRICT_DEV_ONLY',
                'scenario_id': graph.SCENARIO_ID,
                'commit_sequence': state['commit_sequence'],
                'verification_level': 'PROVIDER_ATTESTED',
                'module_ready': False,
                'promotion_allowed': False,
            }
        except Exception as error:
            return {
                'status': 'FAIL_CLOSED',
                'code': str(error),
                'before': before,
                'after': self.state_digest(),
            }
