from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[2]
CREATION2_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch2'
CREATION3_DIR = ROOT / 'development' / 'r1-coc7-investigator-creation-batch3'
RUNTIME_DIR = ROOT / 'recovery' / 'recertification-r1'
for p in (HERE, CREATION2_DIR, CREATION3_DIR, RUNTIME_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import canonical_creation_binding_v17_provider_dev as binding
import investigator_creation_batch2_dev as creation2
import investigator_creation_batch3_dev as creation3
import source_identity_proof_v2 as identity
from runtime_r1.core import RecoveryRuntimeR1, sha


def provider_proof():
    def att(role, token, pages, created):
        return {
            'provider': identity.PROVIDER,
            'role': role,
            'document_id': identity.KEEPER_ID if role == 'KEEPER' else identity.PLAYER_ID,
            'pair_id': identity.SCENARIO_ID,
            'page_count': pages,
            'provider_created_at': created,
            'provider_object_token_sha256': token,
            'full_document_retrieved': True,
            'identity_markers_verified': True,
        }
    return identity.build_provider_pair_proof(
        keeper=att('KEEPER', 'a'*64, 3, '2026-08-25T05:10:49Z'),
        player=att('PLAYER', 'b'*64, 1, '2026-08-25T05:10:50Z'),
    )


def dice():
    return {
        'STR':[3,3,3], 'CON':[4,4,4], 'DEX':[5,4,3], 'APP':[3,4,5],
        'POW':[4,4,4], 'LUCK':[3,3,3], 'SIZ':[4,4], 'INT':[5,5], 'EDU':[5,4],
    }


def choices():
    return [
        {'slot_index':0,'skill_id':'APPRAISE','points':20},
        {'slot_index':1,'skill_id':'ARCHAEOLOGY','points':20},
        {'slot_index':2,'skill_id':'HISTORY','points':20},
        {'slot_index':3,'skill_id':'LANGUAGE_OTHER','specialization':'FRENCH','points':20},
        {'slot_index':4,'skill_id':'LIBRARY_USE','points':20},
        {'slot_index':5,'skill_id':'SPOT_HIDDEN','points':20},
        {'slot_index':6,'skill_id':'MECHANICAL_REPAIR','points':20},
        {'slot_index':7,'skill_id':'NAVIGATE','points':20},
    ]


def personal():
    return [
        {'skill_id':'DODGE','points':40}, {'skill_id':'PSYCHOLOGY','points':40},
        {'skill_id':'SPOT_HIDDEN','points':20}, {'skill_id':'FIREARMS_HANDGUN','points':20},
        {'skill_id':'CHARM','points':40},
    ]


def story():
    return {
        'PERSONAL_DESCRIPTION':['Cultured and carefully dressed.'],
        'IDEOLOGY_BELIEFS':['Knowledge should be preserved.'],
        'SIGNIFICANT_PEOPLE':['A trusted former professor.'],
        'MEANINGFUL_LOCATIONS':['The reading room of an old library.'],
        'TREASURED_POSSESSIONS':['A family notebook.'],
        'TRAITS':['Curious and persistent.'],
    }


def prepared(name='V17 Canonical Test'):
    p1 = creation2.batch1.creation_preflight(
        recorded_dice=dice(),
        age=37,
        physical_allocation=None,
        edu_checks=[{'percentile':80,'gain_d10':5}],
        occupation_id='ARCHAEOLOGIST',
        credit_rating=20,
        era='1920S',
    )
    assert p1['status'] == 'READY_FOR_SKILL_ALLOCATION_BATCH2', p1
    p2 = creation2.creation_batch2_preflight(
        batch1_preflight=p1,
        occupation_selections=choices(),
        personal_interest_allocations=personal(),
        era='1920S',
        identity={'name':name,'gender':'Male','birthplace':'Paris, France'},
        backstory=story(),
        key_connection={'category':'TREASURED_POSSESSIONS','entry_index':0},
    )
    assert p2['status'] == 'READY_FOR_EQUIPMENT_FINANCE_BATCH3', p2
    r = creation3.prepare_creation_commit(
        batch2_preflight=p2,
        finance_profile={
            'credit_rating':20,
            'spending_level_units':10,
            'cash_refresh_units':100,
            'asset_value_units':500,
            'living_standard_id':'SYNTHETIC_DEV_CR20',
            'adapter_verified':True,
        },
        possessions=[],
    )
    assert r['status'] == 'READY_FOR_ATOMIC_COMMIT', r
    return r


def make_runtime(player_count=1, session='V17-CREATION-BINDING-PUBLIC'):
    td = tempfile.TemporaryDirectory()
    rt = binding.v17runtime.ProviderAttestedRuntimeV17(
        Path(td.name)/'runtime.sqlite',
        provider_proof(),
        secret=b'v17-creation-binding-public-secret',
    )
    players = [{'name':f'Placeholder {i+1}'} for i in range(player_count)]
    ready = rt.new_v17_session(players, session_id=session)
    assert ready['status'] == 'DEV_SCENARIO_SESSION_READY', ready
    rt._test_tmpdir = td
    return rt


def commit_all(rt, count):
    return [
        binding.commit_canonical_investigator(
            runtime=rt,
            player_id=f'P{n}',
            ready=prepared(f'V17 P{n}'),
        )
        for n in range(1, count+1)
    ]


class V17CanonicalCreationBindingTests(unittest.TestCase):
    def test_001_module_identity(self):
        self.assertEqual(binding.MODULE_ID, 'COC7_CANONICAL_CREATION_BINDING_LSNT_V1_7_PROVIDER_DEV_V1')

    def test_002_parent_creation_identity(self):
        self.assertEqual(binding.PARENT_CREATION_MODULE_ID, 'COC7_INVESTIGATOR_CREATION_R1_BATCH4_DEV_V1')

    def test_003_runtime_identity(self):
        self.assertEqual(binding.RUNTIME_MODULE_ID, 'LSNT_V1_7_PROVIDER_ATTESTED_DEV_RUNTIME_R1_C4B2_V1')

    def test_004_plain_runtime_rejected(self):
        td = tempfile.TemporaryDirectory()
        rt = RecoveryRuntimeR1(Path(td.name)/'runtime.sqlite')
        rt.new_session([{}])
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['code'], 'V17_PROVIDER_ATTESTED_RUNTIME_REQUIRED')
        rt.close()
        td.cleanup()

    def test_005_provider_runtime_binding_ready(self):
        rt = make_runtime()
        b = binding.canonical_binding_status(runtime=rt)
        self.assertEqual(b['status'], 'READY_DEV_ONLY')
        self.assertFalse(b['module_ready'])
        self.assertFalse(b['promotion_allowed'])
        rt.close()

    def test_006_module_ready_claim_rejected(self):
        rt = make_runtime()
        s = rt.state()
        s['scenario_runtime']['module_ready'] = True
        rt._commit_state(s)
        self.assertNotEqual(binding.canonical_binding_status(runtime=rt)['status'], 'READY_DEV_ONLY')
        rt.close()

    def test_007_promotion_claim_rejected(self):
        rt = make_runtime()
        s = rt.state()
        s['scenario_runtime']['promotion_allowed'] = True
        rt._commit_state(s)
        self.assertNotEqual(binding.canonical_binding_status(runtime=rt)['status'], 'READY_DEV_ONLY')
        rt.close()

    def test_008_from_recorded_dice_reaches_atomic_boundary(self):
        ready = prepared('Recorded Dice Boundary')
        self.assertEqual(ready['status'], 'READY_FOR_ATOMIC_COMMIT')
        self.assertEqual(len(ready['payload_sha256']), 64)

    def test_009_commit_preserves_scenario_contract(self):
        rt = make_runtime()
        before = binding.canonical_binding_status(runtime=rt)['scenario_contract_sha256']
        r = binding.commit_canonical_investigator(runtime=rt, player_id='P1', ready=prepared())
        self.assertEqual(r['status'], 'COMMIT')
        after = binding.canonical_binding_status(runtime=rt)['scenario_contract_sha256']
        self.assertEqual(before, after)
        rt.close()

    def test_010_nonexistent_player_commit_zero_mutation(self):
        rt = make_runtime()
        before = rt.state_digest()
        r = binding.commit_canonical_investigator(runtime=rt, player_id='P9', ready=prepared())
        self.assertEqual(r['code'], 'PLAYER_NOT_IN_CANONICAL_SESSION')
        self.assertEqual(before, rt.state_digest())
        rt.close()

    def test_011_duplicate_creation_commit_blocked(self):
        rt = make_runtime()
        self.assertEqual(binding.commit_canonical_investigator(runtime=rt, player_id='P1', ready=prepared())['status'], 'COMMIT')
        before = rt.state_digest()
        r = binding.commit_canonical_investigator(runtime=rt, player_id='P1', ready=prepared())
        self.assertEqual(r['code'], 'CHARACTER_CREATION_ALREADY_COMMITTED')
        self.assertEqual(before, rt.state_digest())
        rt.close()

    def test_012_finalize_canonical_party(self):
        rt = make_runtime()
        commit_all(rt, 1)
        r = binding.finalize_canonical_party_creation(runtime=rt)
        self.assertEqual(r['status'], 'COMMIT')
        self.assertEqual(r['phase'], 'PLAY_READY')
        self.assertFalse(r['module_ready'])
        rt.close()

    def test_013_play_before_finalize_blocked(self):
        rt = make_runtime()
        commit_all(rt, 1)
        self.assertEqual(
            binding.canonical_play_gate(runtime=rt, player_id='P1', character_id='C1')['code'],
            'PARTY_NOT_PLAY_READY',
        )
        rt.close()

    def test_014_projection_spoiler_safe(self):
        rt = make_runtime()
        p = binding.player_creation_projection(runtime=rt, player_id='P1')
        raw = repr(p)
        self.assertFalse(p['guardian_truth_exposed'])
        self.assertFalse(p['source_hashes_exposed'])
        self.assertFalse(p['provider_identity_exposed'])
        self.assertFalse(p['canonical_graph_exposed'])
        self.assertFalse(p['scenario_contract_exposed'])
        self.assertNotIn('provider_pair_digest', raw)
        self.assertNotIn('graph_digest', raw)
        rt.close()

    def test_015_projection_after_creation_reports_complete(self):
        rt = make_runtime()
        commit_all(rt, 1)
        p = binding.player_creation_projection(runtime=rt, player_id='P1')
        self.assertTrue(p['creation']['complete'])
        self.assertEqual(p['creation']['party_status'], 'READY_TO_FINALIZE')
        rt.close()

    def test_016_wrong_actor_action_zero_mutation(self):
        rt = make_runtime(2)
        commit_all(rt, 2)
        binding.finalize_canonical_party_creation(runtime=rt)
        before = rt.state_digest()
        r = binding.append_canonical_basic_action(
            runtime=rt,
            player_id='P1',
            character_id='C2',
            action_id='NOPE',
            roll=50,
        )
        self.assertEqual(r['code'], 'ACTOR_CONTROL_MISMATCH')
        self.assertEqual(before, rt.state_digest())
        rt.close()

    def test_017_action_and_strict_replay(self):
        rt = make_runtime()
        commit_all(rt, 1)
        binding.finalize_canonical_party_creation(runtime=rt)
        r = binding.append_canonical_basic_action(
            runtime=rt,
            player_id='P1',
            character_id='C1',
            action_id='OBSERVE_CONVOY',
            roll=37,
            delta=-1,
            event_id='V17-CREATE-PLAY-1',
        )
        self.assertEqual(r['status'], 'COMMIT')
        self.assertEqual(rt.verify_journal(rt.state())['status'], 'REPLAY_MATCH')
        rt.close()

    def test_018_save_mutate_restore_after_creation(self):
        rt = make_runtime()
        commit_all(rt, 1)
        binding.finalize_canonical_party_creation(runtime=rt)
        binding.append_canonical_basic_action(
            runtime=rt, player_id='P1', character_id='C1',
            action_id='FIRST', roll=37, delta=-1, event_id='FIRST'
        )
        saved_digest = rt.state_digest()
        bundle = rt.save_v17_bundle()
        binding.append_canonical_basic_action(
            runtime=rt, player_id='P1', character_id='C1',
            action_id='SECOND', roll=55, delta=-1, event_id='SECOND'
        )
        self.assertNotEqual(saved_digest, rt.state_digest())
        restored = rt.restore_v17_bundle(bundle)
        self.assertEqual(restored['status'], 'RESTORED_STRICT_DEV_ONLY')
        self.assertEqual(saved_digest, rt.state_digest())
        self.assertEqual(rt.verify_journal(rt.state())['status'], 'REPLAY_MATCH')
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['status'], 'READY_DEV_ONLY')
        rt.close()

    def test_019_party_status_matrix_boundary(self):
        for count in range(1, 5):
            with self.subTest(players=count):
                rt = make_runtime(count, session=f'PARTY-STATUS-{count}')
                self.assertEqual(binding.canonical_party_creation_status(runtime=rt)['status'], 'PENDING_CREATION')
                commit_all(rt, count)
                self.assertEqual(binding.canonical_party_creation_status(runtime=rt)['status'], 'READY_TO_FINALIZE')
                binding.finalize_canonical_party_creation(runtime=rt)
                self.assertEqual(binding.canonical_party_creation_status(runtime=rt)['status'], 'FINALIZED')
                rt.close()

    def test_020_never_promotable_under_provider_attested(self):
        rt = make_runtime(4)
        commit_all(rt, 4)
        binding.finalize_canonical_party_creation(runtime=rt)
        b = binding.canonical_binding_status(runtime=rt)
        self.assertEqual(b['verification_level'], 'PROVIDER_ATTESTED')
        self.assertFalse(b['portable_byte_identity'])
        self.assertFalse(b['module_ready'])
        self.assertFalse(b['promotion_allowed'])
        rt.close()


def _make_matrix_test(offset):
    player_count = (offset % 4) + 1
    iteration = offset // 4

    def test(self):
        rt = make_runtime(player_count, session=f'V17-CREATE-MATRIX-{player_count}-{iteration}')
        contract_before = binding.canonical_binding_status(runtime=rt)['scenario_contract_sha256']
        results = commit_all(rt, player_count)
        self.assertTrue(all(r['status'] == 'COMMIT' for r in results))
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['scenario_contract_sha256'], contract_before)

        final = binding.finalize_canonical_party_creation(runtime=rt)
        self.assertEqual(final['status'], 'COMMIT')
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['scenario_contract_sha256'], contract_before)

        for n in range(1, player_count + 1):
            gate = binding.canonical_play_gate(runtime=rt, player_id=f'P{n}', character_id=f'C{n}')
            self.assertEqual(gate['status'], 'READY')
            projection = binding.player_creation_projection(runtime=rt, player_id=f'P{n}')
            self.assertTrue(projection['creation']['complete'])
            self.assertEqual(projection['creation']['party_status'], 'FINALIZED')
            self.assertFalse(projection['provider_identity_exposed'])
            self.assertFalse(projection['canonical_graph_exposed'])

        action = binding.append_canonical_basic_action(
            runtime=rt,
            player_id='P1',
            character_id='C1',
            action_id='V17_PUBLIC_MOVE',
            roll=50,
            event_id=f'PUBLIC-{offset}',
        )
        self.assertEqual(action['status'], 'COMMIT')
        self.assertEqual(rt.verify_journal(rt.state())['status'], 'REPLAY_MATCH')

        saved = rt.save_v17_bundle()
        saved_digest = rt.state_digest()
        action2 = binding.append_canonical_basic_action(
            runtime=rt,
            player_id='P1',
            character_id='C1',
            action_id='V17_PUBLIC_MOVE_2',
            roll=40,
            event_id=f'PUBLIC-2-{offset}',
        )
        self.assertEqual(action2['status'], 'COMMIT')
        self.assertNotEqual(rt.state_digest(), saved_digest)
        self.assertEqual(rt.restore_v17_bundle(saved)['status'], 'RESTORED_STRICT_DEV_ONLY')
        self.assertEqual(rt.state_digest(), saved_digest)
        self.assertEqual(rt.verify_journal(rt.state())['status'], 'REPLAY_MATCH')
        rt.close()

    return test


for _offset in range(32):
    setattr(
        V17CanonicalCreationBindingTests,
        f'test_{21+_offset:03d}_matrix_{_offset:02d}',
        _make_matrix_test(_offset),
    )


if __name__ == '__main__':
    unittest.main()
