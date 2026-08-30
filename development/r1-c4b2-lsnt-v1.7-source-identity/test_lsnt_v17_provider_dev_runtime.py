import copy
import hashlib
import hmac
import os
import tempfile
import unittest

import source_identity_proof_v2 as identity
import lsnt_v17_provider_dev_runtime as runtime_mod
from runtime_r1.core import canon


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


def proof():
    return identity.build_provider_pair_proof(
        keeper=att('KEEPER', 'a'*64, 3, '2026-08-25T05:10:49Z'),
        player=att('PLAYER', 'b'*64, 1, '2026-08-25T05:10:50Z'),
    )


def reauth(bundle, secret):
    raw = canon(bundle['payload']).encode('utf-8')
    bundle['auth']['payload_sha256'] = hashlib.sha256(raw).hexdigest()
    bundle['auth']['hmac_sha256'] = hmac.new(secret, raw, hashlib.sha256).hexdigest()


class V17ProviderDevRuntimeTests(unittest.TestCase):
    def make(self, count=1, p=None):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.close()
        self.addCleanup(lambda: os.path.exists(tmp.name) and os.unlink(tmp.name))
        rt = runtime_mod.ProviderAttestedRuntimeV17(tmp.name, p or proof())
        self.addCleanup(rt.close)
        players = [{'name': f'Investigator {i}', 'stats': {'HP': 10+i}} for i in range(1, count+1)]
        return rt, players

    def test_001_identity_dev_only(self):
        rt, _ = self.make()
        st = rt.identity_status()
        self.assertEqual(st['status'], 'READY_DEV_ONLY')
        self.assertFalse(st['module_ready'])
        self.assertFalse(st['promotion_allowed'])

    def test_002_to_005_player_matrix(self):
        for n in range(1, 5):
            with self.subTest(players=n):
                rt, players = self.make(n)
                result = rt.new_v17_session(players, session_id=f'V17-{n}')
                self.assertEqual(result['status'], 'DEV_SCENARIO_SESSION_READY')
                self.assertEqual(len(result['players']), n)

    def test_006_water_matrix(self):
        expected = {1: 32, 2: 48, 3: 64, 4: 80}
        for n, water in expected.items():
            with self.subTest(players=n):
                rt, players = self.make(n)
                rt.new_v17_session(players)
                self.assertEqual(rt.state()['scenario_state']['shared_resources']['water_liters'], water)

    def test_007_runtime_binding_has_no_v15_dependency(self):
        rt, players = self.make(2)
        rt.new_v17_session(players)
        binding = rt.binding_status()
        self.assertEqual(binding['status'], 'READY_DEV_ONLY')
        self.assertFalse(rt.state()['scenario_runtime']['runtime_dependency_on_v1_5'])

    def test_008_knowledge_partition(self):
        rt, players = self.make(2)
        result = rt.new_v17_session(players)
        c1, c2 = result['control_map']['P1'], result['control_map']['P2']
        rt.add_knowledge(c1, 'K1', 'PLAYER', {'clue': 'seen by P1'})
        p1 = rt.player_projection('P1')
        p2 = rt.player_projection('P2')
        self.assertEqual(len(p1['known_information']), 1)
        self.assertEqual(len(p2['known_information']), 0)
        self.assertEqual(rt.state()['knowledge'][c2], {})

    def test_009_keeper_knowledge_not_projected(self):
        rt, players = self.make(1)
        result = rt.new_v17_session(players)
        cid = result['control_map']['P1']
        rt.add_knowledge(cid, 'SECRET', 'KEEPER', {'truth': 'hidden'})
        projection = rt.player_projection('P1')
        self.assertEqual(projection['known_information'], [])

    def test_010_projection_has_no_source_or_graph_leaks(self):
        rt, players = self.make(1)
        rt.new_v17_session(players)
        projection = rt.player_projection('P1')
        raw = repr(projection)
        self.assertNotIn('provider_pair_digest', raw)
        self.assertNotIn('graph_digest', raw)
        self.assertFalse(projection['guardian_truth_exposed'])
        self.assertFalse(projection['provider_identity_exposed'])
        self.assertFalse(projection['canonical_graph_exposed'])

    def test_011_wrong_actor_zero_mutation(self):
        rt, players = self.make(2)
        result = rt.new_v17_session(players)
        before = rt.state_digest()
        blocked = rt.append_dev_action('P1', result['control_map']['P2'], 'WRONG', 42)
        self.assertEqual(blocked['status'], 'FAIL_CLOSED')
        self.assertEqual(blocked['code'], 'ACTOR_CONTROL_MISMATCH')
        self.assertEqual(rt.state_digest(), before)

    def test_012_action_and_strict_replay(self):
        rt, players = self.make(1)
        result = rt.new_v17_session(players)
        cid = result['control_map']['P1']
        action = rt.append_dev_action('P1', cid, 'OBSERVE_CONVOY', 37, delta=-1)
        self.assertEqual(action['status'], 'COMMIT')
        self.assertEqual(rt.verify_journal(rt.state())['status'], 'REPLAY_MATCH')
        self.assertEqual(rt.state()['characters'][cid]['stats']['HP'], 10)

    def test_013_save_mutate_restore_replay(self):
        rt, players = self.make(1)
        result = rt.new_v17_session(players)
        cid = result['control_map']['P1']
        rt.append_dev_action('P1', cid, 'FIRST', 37, delta=-1)
        saved_digest = rt.state_digest()
        bundle = rt.save_v17_bundle()
        rt.append_dev_action('P1', cid, 'SECOND', 55, delta=-1)
        self.assertNotEqual(rt.state_digest(), saved_digest)
        restored = rt.restore_v17_bundle(bundle)
        self.assertEqual(restored['status'], 'RESTORED_STRICT_DEV_ONLY')
        self.assertEqual(rt.state_digest(), saved_digest)
        self.assertEqual(rt.verify_journal(rt.state())['status'], 'REPLAY_MATCH')

    def test_014_tampered_pair_digest_reauthenticated_rejected(self):
        rt, players = self.make(1)
        rt.new_v17_session(players)
        bundle = rt.save_v17_bundle()
        bundle['payload']['provider_pair_digest'] = 'f'*64
        reauth(bundle, rt.secret)
        before = rt.state_digest()
        restored = rt.restore_v17_bundle(bundle)
        self.assertEqual(restored['status'], 'FAIL_CLOSED')
        self.assertEqual(restored['code'], 'V17_DEV_SAVE_BINDING_MISMATCH')
        self.assertEqual(rt.state_digest(), before)

    def test_015_tampered_graph_digest_reauthenticated_rejected(self):
        rt, players = self.make(1)
        rt.new_v17_session(players)
        bundle = rt.save_v17_bundle()
        bundle['payload']['graph_digest'] = 'e'*64
        reauth(bundle, rt.secret)
        before = rt.state_digest()
        restored = rt.restore_v17_bundle(bundle)
        self.assertEqual(restored['status'], 'FAIL_CLOSED')
        self.assertEqual(restored['code'], 'V17_DEV_SAVE_BINDING_MISMATCH')
        self.assertEqual(rt.state_digest(), before)

    def test_016_state_pair_tamper_reauthenticated_rejected(self):
        rt, players = self.make(1)
        rt.new_v17_session(players)
        bundle = rt.save_v17_bundle()
        bundle['payload']['state']['scenario_runtime']['provider_pair_digest'] = 'd'*64
        reauth(bundle, rt.secret)
        before = rt.state_digest()
        restored = rt.restore_v17_bundle(bundle)
        self.assertEqual(restored['status'], 'FAIL_CLOSED')
        self.assertEqual(restored['code'], 'V17_DEV_STATE_BINDING_MISMATCH')
        self.assertEqual(rt.state_digest(), before)

    def test_017_invalid_proof_blocks_session(self):
        bad = {'status': 'BLOCKED', 'verification_level': 'PROVIDER_ATTESTED'}
        rt, players = self.make(1, p=bad)
        result = rt.new_v17_session(players)
        self.assertEqual(result['status'], 'FAIL_CLOSED')

    def test_018_provider_runtime_never_claims_module_ready(self):
        rt, players = self.make(4)
        rt.new_v17_session(players)
        state = rt.state()['scenario_runtime']
        self.assertFalse(state['portable_byte_identity'])
        self.assertFalse(state['module_ready'])
        self.assertFalse(state['frozen_candidate'])
        self.assertFalse(state['promotion_allowed'])
        self.assertFalse(state['authority_promoted'])

    def test_019_saved_bundle_never_claims_promotion(self):
        rt, players = self.make(1)
        rt.new_v17_session(players)
        payload = rt.save_v17_bundle()['payload']
        self.assertFalse(payload['portable_byte_identity'])
        self.assertFalse(payload['module_ready'])
        self.assertFalse(payload['promotion_allowed'])

    def test_020_invalid_player_projection_blocked(self):
        rt, players = self.make(1)
        rt.new_v17_session(players)
        self.assertEqual(rt.player_projection('P9')['status'], 'BLOCKED')


if __name__ == '__main__':
    unittest.main()
