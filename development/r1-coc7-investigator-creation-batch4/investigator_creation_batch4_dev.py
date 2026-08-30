from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH3_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch3'
RUNTIME_DIR = ROOT / 'recovery' / 'recertification-r1'
for path in (BATCH3_DIR, RUNTIME_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import investigator_creation_batch3_dev as batch3  # noqa: E402
from runtime_r1.core import CHECKPOINT_FLOOR, sha  # noqa: E402

MODULE_ID = 'COC7_INVESTIGATOR_CREATION_R1_BATCH4_DEV_V1'
PARENT_MODULE_ID = batch3.MODULE_ID
PARENT_HARDENED_PROOF = 2614
FINALIZATION_SCHEMA = 'COC7_PARTY_CREATION_FINALIZATION_R1_BATCH4_V1'


def _blocked(code: str, **extra):
    return {'status': 'BLOCKED', 'code': code, **extra}


def _state(runtime):
    try:
        return runtime._get_state()
    except Exception:
        return None


def _roster_from_state(state: dict) -> dict:
    roster = []
    party = state['party']
    for player_id in state['interface_session']['players']:
        character_id = party[player_id]
        character = state['initial_characters'][character_id]
        roster.append({
            'player_id': player_id,
            'character_id': character_id,
            'creation_payload_sha256': character['creation']['payload_sha256'],
            'character_baseline_sha256': sha(character),
        })
    return {
        'players': roster,
        'roster_sha256': sha(roster),
    }


def party_creation_status(*, runtime) -> dict:
    state = _state(runtime)
    if not isinstance(state, dict):
        return _blocked('RUNTIME_STATE_UNAVAILABLE')
    if state.get('authority_floor') != CHECKPOINT_FLOOR:
        return _blocked('AUTHORITY_FLOOR_INVALID')

    interface = state.get('interface_session')
    party = state.get('party')
    characters = state.get('characters')
    initial = state.get('initial_characters')
    commits = state.get('creation_commits', [])
    if not isinstance(interface, dict) or not isinstance(party, dict) or not isinstance(characters, dict) or not isinstance(initial, dict):
        return _blocked('RUNTIME_CREATION_STRUCTURES_INVALID')
    players = interface.get('players')
    control = interface.get('control_map')
    if not isinstance(players, list) or not 1 <= len(players) <= 4 or len(set(players)) != len(players):
        return _blocked('PLAYER_ROSTER_INVALID')
    if not isinstance(control, dict) or control != party or set(players) != set(party):
        return _blocked('CONTROL_MAP_PARTY_MISMATCH')
    if not isinstance(commits, list):
        return _blocked('CREATION_COMMITS_INVALID')

    phase = interface.get('phase')
    if phase not in {'SESSION_READY', 'PLAY_READY'}:
        return _blocked('INTERFACE_PHASE_INVALID', phase=phase)
    if phase == 'SESSION_READY' and state.get('journal'):
        return _blocked('PLAY_JOURNAL_EXISTS_BEFORE_PARTY_FINALIZATION')

    complete = []
    pending = []
    seen_commit_characters = set()
    for row in commits:
        if not isinstance(row, dict):
            return _blocked('CREATION_COMMIT_RECORD_INVALID')
        cid = row.get('character_id')
        if not cid or cid in seen_commit_characters:
            return _blocked('DUPLICATE_OR_MISSING_CREATION_COMMIT_CHARACTER')
        seen_commit_characters.add(cid)

    for player_id in players:
        character_id = party.get(player_id)
        character = characters.get(character_id)
        baseline = initial.get(character_id)
        if not isinstance(character, dict) or character.get('owner_id') != player_id:
            return _blocked('CHARACTER_OWNERSHIP_MISMATCH', player_id=player_id, character_id=character_id)
        if not isinstance(baseline, dict) or baseline.get('owner_id') != player_id:
            return _blocked('INITIAL_CHARACTER_OWNERSHIP_MISMATCH', player_id=player_id, character_id=character_id)
        creation = character.get('creation', {})
        if creation.get('complete') is True:
            if creation.get('module_id') != PARENT_MODULE_ID:
                return _blocked('CREATION_MODULE_ID_MISMATCH', character_id=character_id)
            if character != baseline and phase == 'SESSION_READY':
                return _blocked('CURRENT_INITIAL_BASELINE_MISMATCH_BEFORE_PLAY', character_id=character_id)
            matches = [row for row in commits if row.get('character_id') == character_id]
            if len(matches) != 1:
                return _blocked('CREATION_COMMIT_RECORD_MISSING_OR_DUPLICATE', character_id=character_id)
            row = matches[0]
            if (
                row.get('player_id') != player_id
                or row.get('module_id') != PARENT_MODULE_ID
                or row.get('creation_payload_sha256') != creation.get('payload_sha256')
                or row.get('character_baseline_sha256') != sha(baseline)
            ):
                return _blocked('CREATION_COMMIT_BINDING_MISMATCH', character_id=character_id)
            complete.append({'player_id': player_id, 'character_id': character_id})
        else:
            if any(row.get('character_id') == character_id for row in commits):
                return _blocked('COMMIT_RECORD_EXISTS_FOR_INCOMPLETE_CHARACTER', character_id=character_id)
            pending.append({'player_id': player_id, 'character_id': character_id})

    if phase == 'PLAY_READY':
        if pending:
            return _blocked('PLAY_READY_WITH_INCOMPLETE_CHARACTER', pending=pending)
        finalization = state.get('creation_finalization')
        if not isinstance(finalization, dict):
            return _blocked('CREATION_FINALIZATION_RECORD_MISSING')
        expected = _roster_from_state(state)
        if (
            finalization.get('schema') != FINALIZATION_SCHEMA
            or finalization.get('module_id') != MODULE_ID
            or finalization.get('parent_module_id') != PARENT_MODULE_ID
            or finalization.get('checkpoint_floor') != CHECKPOINT_FLOOR
            or finalization.get('players') != expected['players']
            or finalization.get('roster_sha256') != expected['roster_sha256']
        ):
            return _blocked('CREATION_FINALIZATION_BINDING_MISMATCH')
        return {
            'status': 'FINALIZED',
            'module_id': MODULE_ID,
            'phase': 'PLAY_READY',
            'completed': complete,
            'pending': [],
            'roster_sha256': expected['roster_sha256'],
        }

    return {
        'status': 'READY_TO_FINALIZE' if not pending else 'PENDING_CREATION',
        'module_id': MODULE_ID,
        'phase': 'SESSION_READY',
        'completed': complete,
        'pending': pending,
        'automatic_investigator_completion': False,
    }


def finalize_party_creation_atomic(*, runtime) -> dict:
    try:
        before = runtime.state_digest()
    except Exception:
        return _blocked('RUNTIME_INTERFACE_UNAVAILABLE')

    def fail(code, **extra):
        return {'status': 'FAIL_CLOSED', 'code': code, 'before': before, 'after': runtime.state_digest(), **extra}

    status = party_creation_status(runtime=runtime)
    if status.get('status') == 'FINALIZED':
        return fail('PARTY_CREATION_ALREADY_FINALIZED')
    if status.get('status') != 'READY_TO_FINALIZE':
        return fail(status.get('code', 'PARTY_CREATION_INCOMPLETE'), party_status=status)

    state = runtime._get_state()
    if state.get('journal'):
        return fail('PLAY_JOURNAL_EXISTS_BEFORE_PARTY_FINALIZATION')
    try:
        replay = runtime.verify_journal(state)
    except Exception:
        return fail('STRICT_REPLAY_INTERFACE_UNAVAILABLE')
    if replay.get('status') != 'REPLAY_MATCH':
        return fail('STRICT_REPLAY_BASELINE_INVALID', replay=replay)

    new_state = copy.deepcopy(state)
    roster = _roster_from_state(new_state)
    new_state['interface_session']['phase'] = 'PLAY_READY'
    new_state['creation_finalization'] = {
        'schema': FINALIZATION_SCHEMA,
        'module_id': MODULE_ID,
        'parent_module_id': PARENT_MODULE_ID,
        'checkpoint_floor': CHECKPOINT_FLOOR,
        'players': roster['players'],
        'roster_sha256': roster['roster_sha256'],
        'automatic_investigator_completion': False,
        'randomness_generated': False,
    }
    sequence = new_state.get('commit_sequence')
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        return fail('RUNTIME_COMMIT_SEQUENCE_INVALID')
    new_state['commit_sequence'] = sequence + 1
    new_state['creation_finalization']['commit_sequence'] = new_state['commit_sequence']

    try:
        runtime._commit_state(new_state)
    except Exception:
        return fail('ATOMIC_PARTY_FINALIZATION_COMMIT_FAILED')

    verified = party_creation_status(runtime=runtime)
    if verified.get('status') != 'FINALIZED':
        return fail('POST_COMMIT_PARTY_FINALIZATION_VERIFICATION_FAILED', verification=verified)
    return {
        'status': 'COMMIT',
        'module_id': MODULE_ID,
        'phase': 'PLAY_READY',
        'commit_sequence': new_state['commit_sequence'],
        'roster_sha256': roster['roster_sha256'],
        'before': before,
        'after': runtime.state_digest(),
        'automatic_investigator_completion': False,
        'randomness_generated': False,
    }


def play_gate(*, runtime, player_id: str, character_id: str) -> dict:
    status = party_creation_status(runtime=runtime)
    if status.get('status') != 'FINALIZED':
        return _blocked('PARTY_NOT_PLAY_READY', party_status=status)
    state = runtime._get_state()
    if state['interface_session']['control_map'].get(player_id) != character_id:
        return _blocked('ACTOR_CONTROL_MISMATCH')
    character = state['characters'].get(character_id)
    if not isinstance(character, dict) or character.get('owner_id') != player_id:
        return _blocked('CHARACTER_OWNERSHIP_MISMATCH')
    return {
        'status': 'READY',
        'player_id': player_id,
        'character_id': character_id,
        'phase': 'PLAY_READY',
        'roster_sha256': status['roster_sha256'],
    }


def append_player_action_after_creation(*, runtime, player_id: str, character_id: str, action_id, roll, delta=0, event_id=None) -> dict:
    before = runtime.state_digest()
    gate = play_gate(runtime=runtime, player_id=player_id, character_id=character_id)
    if gate.get('status') != 'READY':
        return {
            'status': 'FAIL_CLOSED',
            'code': gate.get('code', 'PARTY_NOT_PLAY_READY'),
            'before': before,
            'after': runtime.state_digest(),
            'gate': gate,
        }
    result = runtime.append_player_action(player_id, character_id, action_id, roll, delta=delta, event_id=event_id)
    return result
