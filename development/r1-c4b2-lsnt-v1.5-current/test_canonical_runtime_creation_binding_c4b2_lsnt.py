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

import canonical_runtime_creation_binding_c4b2_lsnt as binding
import investigator_creation_batch3_dev as creation3
import investigator_creation_batch2_dev as creation2
from integrated_adjudication_r1_c4b2_lsnt import SourceBackedRuntimeR1C4B2LSNT
from runtime_r1.core import RecoveryRuntimeR1, sha


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


def prepared(name='C4B2 Canonical Test'):
    p1=creation2.batch1.creation_preflight(
        recorded_dice=dice(), age=37, physical_allocation=None,
        edu_checks=[{'percentile':80,'gain_d10':5}], occupation_id='ARCHAEOLOGIST',
        credit_rating=20, era='1920S')
    assert p1['status']=='READY_FOR_SKILL_ALLOCATION_BATCH2',p1
    p2=creation2.creation_batch2_preflight(
        batch1_preflight=p1, occupation_selections=choices(), personal_interest_allocations=personal(), era='1920S',
        identity={'name':name,'gender':'Male','birthplace':'Paris, France'}, backstory=story(),
        key_connection={'category':'TREASURED_POSSESSIONS','entry_index':0})
    assert p2['status']=='READY_FOR_EQUIPMENT_FINANCE_BATCH3',p2
    r=creation3.prepare_creation_commit(
        batch2_preflight=p2,
        finance_profile={'credit_rating':20,'spending_level_units':10,'cash_refresh_units':100,'asset_value_units':500,'living_standard_id':'SYNTHETIC_DEV_CR20','adapter_verified':True},
        possessions=[])
    assert r['status']=='READY_FOR_ATOMIC_COMMIT',r
    return r


def make_runtime(player_count=1, session='C4B2-BINDING-PUBLIC-TEST'):
    td=tempfile.TemporaryDirectory()
    rt=SourceBackedRuntimeR1C4B2LSNT(Path(td.name)/'runtime.sqlite', Path(td.name)/'missing-rules.zip', {}, secret=b'c4b2-public-binding-secret')
    r=rt.new_session([{'name':f'Placeholder {i+1}'} for i in range(player_count)],session)
    assert r['status']=='SESSION_READY',r
    rt._test_tmpdir=td
    return rt


def bind_lsnt_fixture(rt):
    route=binding.ROUTES['SOLEIL_NOIR']
    s=rt.state()
    s['scenario_runtime']={
        'router_id':binding.ROUTER_ID,
        'registry_id':binding.REGISTRY_ID,
        'scenario_key':route.scenario_key,
        'scenario_id':route.scenario_id,
        'title':route.title,
        'source_ids':list(route.source_ids),
        'source_hashes':{sid:binding.SOURCE_SPECS_C4B[sid].sha256 for sid in route.source_ids},
        'release_checkpoint':route.release_checkpoint,
        'release_class':route.release_class,
        'canonical_path':copy.deepcopy(route.canonical_path),
    }
    rt._commit_state(s)
    return sha(s['scenario_runtime'])


def commit_all(rt,count):
    return [binding.commit_canonical_investigator(runtime=rt,player_id=f'P{n}',ready=prepared(f'C4B2 P{n}')) for n in range(1,count+1)]


class C4B2CanonicalRuntimeCreationBindingTests(unittest.TestCase):
    def test_001_module_identity(self):
        self.assertEqual(binding.MODULE_ID,'COC7_CANONICAL_RUNTIME_CREATION_BINDING_R1_C4B2_LSNT_DEV_V1')
    def test_002_parent_identity(self):
        self.assertEqual(binding.PARENT_CREATION_MODULE_ID,'COC7_INVESTIGATOR_CREATION_R1_BATCH4_DEV_V1')
    def test_003_runtime_identity(self):
        self.assertEqual(binding.FROZEN_RUNTIME_INTEGRATION_ID,'SOLIDSTATE_RECOVERY_RUNTIME_R1_C4B2_LSNT_V1')
    def test_004_release_class_allowed(self):
        self.assertIn('RECOVERY_SOURCE_COMPILED_C4B2',binding.ALLOWED_RELEASE_CLASSES)
    def test_005_plain_runtime_rejected(self):
        td=tempfile.TemporaryDirectory(); rt=RecoveryRuntimeR1(Path(td.name)/'r.sqlite'); rt.new_session([{}])
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['code'],'C4B2_LSNT_SOURCE_BACKED_RUNTIME_REQUIRED'); rt.close(); td.cleanup()
    def test_006_missing_binding_rejected(self):
        rt=make_runtime(); self.assertEqual(binding.canonical_binding_status(runtime=rt)['code'],'C4B2_SCENARIO_BINDING_REQUIRED'); rt.close()
    def test_007_lsnt_binding_ready(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); self.assertEqual(binding.canonical_binding_status(runtime=rt)['status'],'READY'); rt.close()
    def test_008_exact_router_bound(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); self.assertEqual(rt.state()['scenario_runtime']['router_id'],binding.ROUTER_ID); rt.close()
    def test_009_exact_registry_bound(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); self.assertEqual(rt.state()['scenario_runtime']['registry_id'],binding.REGISTRY_ID); rt.close()
    def test_010_wrong_source_hash_rejected(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); s=rt.state(); s['scenario_runtime']['source_hashes']['SOLEIL_NOIR_KEEPER']='0'*64; rt._commit_state(s)
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['code'],'C4B2_SCENARIO_BINDING_MISMATCH'); rt.close()
    def test_011_wrong_path_rejected(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); s=rt.state(); s['scenario_runtime']['canonical_path']={'tampered':True}; rt._commit_state(s)
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['code'],'C4B2_SCENARIO_BINDING_MISMATCH'); rt.close()
    def test_012_wrong_registry_rejected(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); s=rt.state(); s['scenario_runtime']['registry_id']='OLD_REGISTRY'; rt._commit_state(s)
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['code'],'C4B2_SCENARIO_BINDING_MISMATCH'); rt.close()
    def test_013_wrong_router_rejected(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); s=rt.state(); s['scenario_runtime']['router_id']='OLD_ROUTER'; rt._commit_state(s)
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['code'],'C4B2_SCENARIO_BINDING_MISMATCH'); rt.close()
    def test_014_commit_preserves_scenario_binding(self):
        rt=make_runtime(); expected=bind_lsnt_fixture(rt); r=binding.commit_canonical_investigator(runtime=rt,player_id='P1',ready=prepared())
        self.assertEqual(r['status'],'COMMIT'); self.assertEqual(sha(rt.state()['scenario_runtime']),expected); rt.close()
    def test_015_commit_without_binding_zero_mutation(self):
        rt=make_runtime(); before=rt.state_digest(); r=binding.commit_canonical_investigator(runtime=rt,player_id='P1',ready=prepared())
        self.assertEqual(r['code'],'C4B2_SCENARIO_BINDING_REQUIRED'); self.assertEqual(before,rt.state_digest()); rt.close()
    def test_016_finalize_canonical_party(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); commit_all(rt,1); r=binding.finalize_canonical_party_creation(runtime=rt)
        self.assertEqual(r['status'],'COMMIT'); self.assertEqual(r['phase'],'PLAY_READY'); rt.close()
    def test_017_play_before_finalize_blocked(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); commit_all(rt,1); self.assertEqual(binding.canonical_play_gate(runtime=rt,player_id='P1',character_id='C1')['code'],'PARTY_NOT_PLAY_READY'); rt.close()
    def test_018_projection_spoiler_safe(self):
        rt=make_runtime(); bind_lsnt_fixture(rt); p=binding.player_creation_projection(runtime=rt,player_id='P1')
        self.assertFalse(p['canonical_path_exposed']); self.assertFalse(p['source_hashes_exposed']); self.assertNotIn('canonical_path',p['scenario']); rt.close()
    def test_019_wrong_actor_action_zero_mutation(self):
        rt=make_runtime(2); bind_lsnt_fixture(rt); commit_all(rt,2); binding.finalize_canonical_party_creation(runtime=rt); before=rt.state_digest()
        r=binding.append_canonical_basic_action(runtime=rt,player_id='P1',character_id='C2',action_id='NOPE',roll=50)
        self.assertEqual(r['code'],'ACTOR_CONTROL_MISMATCH'); self.assertEqual(before,rt.state_digest()); rt.close()
    def test_020_from_dice_payload_reaches_atomic_boundary(self):
        r=prepared('Dice Boundary')
        self.assertEqual(r['status'],'READY_FOR_ATOMIC_COMMIT'); self.assertEqual(len(r['payload_sha256']),64)


def _make_matrix_test(offset):
    player_count=(offset % 4)+1
    iteration=offset // 4
    def test(self):
        rt=make_runtime(player_count,session=f'C4B2-LSNT-BIND-{player_count}-{iteration}')
        expected=bind_lsnt_fixture(rt)
        self.assertEqual(binding.canonical_binding_status(runtime=rt)['status'],'READY')
        results=commit_all(rt,player_count)
        self.assertTrue(all(r['status']=='COMMIT' for r in results))
        self.assertEqual(sha(rt.state()['scenario_runtime']),expected)
        final=binding.finalize_canonical_party_creation(runtime=rt)
        self.assertEqual(final['status'],'COMMIT')
        self.assertEqual(sha(rt.state()['scenario_runtime']),expected)
        for n in range(1,player_count+1):
            gate=binding.canonical_play_gate(runtime=rt,player_id=f'P{n}',character_id=f'C{n}')
            self.assertEqual(gate['status'],'READY')
            projection=binding.player_creation_projection(runtime=rt,player_id=f'P{n}')
            self.assertEqual(projection['scenario']['scenario_key'],'SOLEIL_NOIR')
            self.assertFalse(projection['canonical_path_exposed'])
            self.assertFalse(projection['source_hashes_exposed'])
        action=binding.append_canonical_basic_action(runtime=rt,player_id='P1',character_id='C1',action_id='C4B2_PUBLIC_MOVE',roll=50,event_id=f'PUBLIC-{offset}')
        self.assertEqual(action['status'],'COMMIT')
        self.assertEqual(rt.verify_journal(rt.state())['status'],'REPLAY_MATCH')
        rt.close()
    return test


for _offset in range(32):
    setattr(C4B2CanonicalRuntimeCreationBindingTests,f'test_{21+_offset:03d}_matrix_{_offset:02d}',_make_matrix_test(_offset))


if __name__=='__main__':
    unittest.main()
